"""Thai shaping on Pillow wheels with or without RAQM (including Windows)."""

from functools import lru_cache
from pathlib import Path
import math
from PIL import Image, ImageFilter, ImageFont, features


class HarfBuzzFont(ImageFont.ImageFont):
    """Pillow-compatible LTR font with HarfBuzz shaping and FreeType rasterization."""

    def __init__(self, path, size):
        import freetype
        import uharfbuzz as hb

        self.size = int(size)
        self._hb = hb
        self._ft = freetype
        data = Path(path).read_bytes()
        self._font = hb.Font(hb.Face(data))
        self._font.scale = (self.size * 64, self.size * 64)
        hb.ot_font_set_funcs(self._font)
        self._face = freetype.Face(str(path))
        self._face.set_pixel_sizes(0, self.size)

    def getmetrics(self):
        return (
            math.ceil(self._face.size.ascender / 64),
            math.ceil(-self._face.size.descender / 64),
        )

    @lru_cache(maxsize=256)
    def _shape(self, text):
        if not text:
            return ()
        buffer = self._hb.Buffer()
        buffer.add_str(str(text))
        buffer.guess_segment_properties()
        self._hb.shape(self._font, buffer)
        return tuple(
            (
                info.codepoint,
                pos.x_advance / 64,
                pos.y_advance / 64,
                pos.x_offset / 64,
                pos.y_offset / 64,
            )
            for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions)
        )

    def getlength(self, text, *args, **kwargs):
        return sum(glyph[1] for glyph in self._shape(text))

    @lru_cache(maxsize=128)
    def _raster(self, text):
        glyphs = []
        x = y = 0.0
        for identity, ax, ay, ox, oy in self._shape(text):
            self._face.load_glyph(
                identity, self._ft.FT_LOAD_RENDER | self._ft.FT_LOAD_TARGET_NORMAL
            )
            slot = self._face.glyph
            bitmap = slot.bitmap
            if bitmap.width and bitmap.rows:
                raw = bytes(bitmap.buffer)
                # FreeType bitmap rows may have padding.
                pitch = abs(bitmap.pitch)
                raw = b"".join(
                    raw[row * pitch : row * pitch + bitmap.width]
                    for row in range(bitmap.rows)
                )
                image = Image.frombytes("L", (bitmap.width, bitmap.rows), raw)
                left = round(x + ox + slot.bitmap_left)
                top = round(-y - oy - slot.bitmap_top)
                glyphs.append((left, top, image))
            x += ax
            y += ay
        if not glyphs:
            return Image.new("L", (max(1, math.ceil(x)), 1)), (0, 0)
        left = min(g[0] for g in glyphs)
        top = min(g[1] for g in glyphs)
        right = max(g[0] + g[2].width for g in glyphs)
        bottom = max(g[1] + g[2].height for g in glyphs)
        mask = Image.new("L", (right - left, bottom - top))
        # Max blending preserves antialiasing when Thai marks overlap base glyphs.
        from PIL import ImageChops

        for gx, gy, image in glyphs:
            layer = Image.new("L", mask.size)
            layer.paste(image, (gx - left, gy - top))
            mask = ImageChops.lighter(mask, layer)
        return mask, (left, top)

    def _anchor(self, text, anchor, mask, origin):
        anchor = anchor or "la"
        ascent, descent = self.getmetrics()
        horizontal = {
            "l": 0,
            "m": -self.getlength(text) / 2,
            "r": -self.getlength(text),
        }[anchor[0]]
        vertical = {
            "a": ascent,
            "t": -origin[1],
            "m": (ascent - descent) / 2,
            "s": 0,
            "b": -origin[1] - mask.height,
            "d": -descent,
        }[anchor[1]]
        return round(origin[0] + horizontal), round(origin[1] + vertical)

    def getmask2(self, text, mode="", *args, stroke_width=0, anchor=None, **kwargs):
        mask, origin = self._raster(str(text))
        offset = self._anchor(text, anchor, mask, origin)
        stroke = math.ceil(stroke_width)
        if stroke:
            expanded = Image.new(
                "L", (mask.width + 2 * stroke, mask.height + 2 * stroke)
            )
            expanded.paste(mask, (stroke, stroke))
            mask = expanded.filter(ImageFilter.MaxFilter(2 * stroke + 1))
            offset = (offset[0] - stroke, offset[1] - stroke)
        return mask.im, offset

    def getmask(self, text, mode="", *args, **kwargs):
        return self.getmask2(text, mode, *args, **kwargs)[0]

    def getbbox(self, text, *args, stroke_width=0, anchor=None, **kwargs):
        mask, origin = self._raster(str(text))
        x, y = self._anchor(text, anchor, mask, origin)
        return (
            x - stroke_width,
            y - stroke_width,
            x + mask.width + stroke_width,
            y + mask.height + stroke_width,
        )


def load_font(path, size, **kwargs):
    if features.check_feature("raqm"):
        return ImageFont.truetype(str(path), size, layout_engine=ImageFont.Layout.RAQM)
    return HarfBuzzFont(path, size)
