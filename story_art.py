"""Original layered 2D sets, articulated actors, camera moves and explanatory graphics."""

import math
import numpy as np
from thai_text import load_font
from PIL import Image, ImageDraw, ImageFont

SIZE = (1080, 1920)


class StoryStage:
    def __init__(self, font_path, project):
        self.font_path = str(font_path)
        self.project = project
        self.fonts = {}
        self.sets = {}
        yy, xx = np.ogrid[:1920, :1080]
        radius = ((xx - 540) / 780) ** 2 + ((yy - 950) / 1320) ** 2
        alpha = np.clip((radius - 0.15) * 95, 0, 155).astype("uint8")
        self.vignette = Image.new("RGBA", SIZE, (0, 0, 0, 0))
        self.vignette.putalpha(Image.fromarray(alpha))

    def font(self, size):
        if size not in self.fonts:
            self.fonts[size] = load_font(
                self.font_path, size, layout_engine=ImageFont.Layout.RAQM
            )
        return self.fonts[size]

    def label(self, d, xy, text, size=30, fill="#f3eedf", anchor="mm"):
        d.text(xy, text, font=self.font(size), fill=fill, anchor=anchor)

    def door(self, d, box, number="407", color="#725447"):
        x, y, r, b = box
        d.rectangle((x - 18, y - 18, r + 18, b + 12), fill="#30272b")
        d.rectangle(box, fill=color, outline="#3c302f", width=9)
        for yy in (y + 90, y + (b - y) * 0.47):
            d.rectangle(
                (x + 22, yy, r - 22, min(b - 30, yy + (b - y) * 0.33)),
                outline="#5a4338",
                width=6,
            )
        d.ellipse(
            (r - 46, y + (b - y) * 0.58, r - 20, y + (b - y) * 0.58 + 26),
            fill="#e0c88f",
        )
        d.rounded_rectangle(
            (x + (r - x) / 2 - 50, y + 25, x + (r - x) / 2 + 50, y + 75),
            8,
            fill="#332c2b",
        )
        self.label(d, ((x + r) / 2, y + 50), number, 25)

    def scenery(self, setting):
        if setting in self.sets:
            return self.sets[setting]
        image = Image.new("RGBA", SIZE, "#141c2b")
        d = ImageDraw.Draw(image)
        if setting == "city":
            d.rectangle((0, 0, 1080, 1920), fill="#111c37")
            d.ellipse((780, 170, 900, 290), fill="#ecdfb0")
            for k in range(8):
                x = k * 155 - 50
                top = 640 + (k * 137) % 370
                d.rectangle(
                    (x, top, x + 145, 1660), fill=("#25334a" if k % 2 else "#1b2940")
                )
                for row in range(13):
                    for col in range(4):
                        y = top + 35 + row * 59
                        if y < 1630:
                            color = (
                                "#c9ae69"
                                if (row * 7 + col * 3 + k) % 9 == 0
                                else "#3b4b65"
                            )
                            d.rectangle(
                                (x + 18 + col * 29, y, x + 31 + col * 29, y + 24),
                                fill=color,
                            )
            d.rectangle((0, 1660, 1080, 1920), fill="#1e2531")
            d.line((0, 1760, 1080, 1760), fill="#6c6670", width=4)
        elif setting == "corridor":
            d.rectangle((0, 0, 1080, 1920), fill="#172332")
            d.polygon([(0, 0), (420, 520), (420, 1320), (0, 1920)], fill="#263342")
            d.polygon(
                [(1080, 0), (660, 520), (660, 1320), (1080, 1920)], fill="#202c3a"
            )
            d.polygon(
                [(0, 1920), (420, 1320), (660, 1320), (1080, 1920)], fill="#333941"
            )
            d.rectangle((420, 520, 660, 1320), fill="#0c1725")
            self.door(d, (70, 500, 300, 1460), "407", "#4e4444")
            self.door(d, (790, 500, 1020, 1460), "408", "#494049")
            self.door(d, (455, 730, 625, 1280), "409", "#343c47")
            d.rounded_rectangle((435, 570, 645, 630), 8, fill="#275b48")
            self.label(d, (540, 600), "ทางออก", 26, fill="#9be6be")
            d.polygon([(420, 210), (660, 210), (585, 360), (495, 360)], fill="#c0bba0")
        elif setting == "elevator":
            d.rectangle((0, 0, 1080, 1920), fill="#9d8967")
            d.rectangle(
                (50, 80, 1030, 1600), fill="#b3a17f", outline="#64543f", width=14
            )
            d.rectangle(
                (180, 380, 900, 1510), fill="#746d65", outline="#473f3b", width=14
            )
            d.rectangle((200, 400, 535, 1490), fill="#a3a19b")
            d.rectangle((545, 400, 880, 1490), fill="#92908a")
            for x in range(210, 880, 45):
                d.line((x, 400, x, 1490), fill="#9a9790", width=2)
            d.rectangle((405, 210, 675, 300), fill="#262b2c")
            self.label(d, (540, 255), "07", 47, fill="#f0c575")
            d.rounded_rectangle((945, 650, 1000, 980), 10, fill="#6a6258")
            for y in range(690, 960, 75):
                d.ellipse((960, y, 985, y + 25), fill="#e3cf9e")
            d.polygon(
                [(0, 1920), (180, 1510), (900, 1510), (1080, 1920)], fill="#655d58"
            )
        elif setting == "diagram":
            d.rectangle((0, 0, 1080, 1920), fill="#172334")
            d.rounded_rectangle((60, 330, 1020, 1550), 35, fill="#ede8db")
            self.label(d, (540, 405), "มองภาพรวม", 40, fill="#243548")
        else:
            d.rectangle(
                (0, 0, 1080, 1470), fill="#a4917f" if setting == "room" else "#6e8291"
            )
            d.rectangle((0, 1470, 1080, 1920), fill="#534440")
            d.rectangle((0, 1450, 1080, 1490), fill="#3f3534")
            self.door(d, (700, 380, 1020, 1450), "407")
            d.rectangle(
                (95, 420, 480, 950), fill="#292e42", outline="#dac7a9", width=12
            )
            d.rectangle((115, 440, 460, 930), fill="#16283e")
            for x in range(135, 460, 60):
                d.rectangle((x, 680 + (x % 100), x + 48, 930), fill="#243d56")
            d.line((285, 430, 285, 940), fill="#b6a58c", width=12)
            d.rectangle((60, 1220, 590, 1470), fill="#4e5c69")
            d.rounded_rectangle((80, 1110, 570, 1300), 30, fill="#8b9290")
            d.rounded_rectangle((95, 1125, 260, 1250), 22, fill="#c4bcb1")
            d.rectangle((535, 1070, 650, 1460), fill="#624c3d")
            d.rectangle((585, 880, 605, 1080), fill="#3b332e")
            d.polygon([(530, 880), (660, 880), (630, 760), (560, 760)], fill="#d8b36e")
        self.sets[setting] = image
        return image

    def person(
        self,
        d,
        x,
        ground,
        scale,
        t,
        pose,
        friend=False,
        emotion="neutral",
        prop="none",
        speaking=False,
    ):
        def p(u, v):
            return (x + u * scale, ground + v * scale)

        def box(u, v, r, b):
            return (*p(u, v), *p(r, b))

        def line(points, color, width):
            d.line(
                [p(*pt) for pt in points],
                fill=color,
                width=max(1, int(width * scale)),
                joint="curve",
            )

        skin = "#dab397" if friend else "#d9ba9b"
        shirt = "#a26572" if friend else "#39566d"
        ink = "#262631"
        walking = pose in ("walk", "run")
        swing = (
            math.sin(t * (10 if pose == "run" else 5)) * 65
            if walking
            else math.sin(t * 2) * 8
        )
        # Hair silhouette behind the face, coherent costume and proportions per character.
        if friend:
            d.rounded_rectangle(
                box(-92, -800, 95, -475), radius=int(65 * scale), fill="#49352f"
            )
        d.ellipse(box(-120, -20, 120, 20), fill="#20222c")
        line(
            [(-38, -300), (-50 - swing * 0.4, -155), (-58 - swing, -15)], "#343b49", 29
        )
        line([(38, -300), (50 + swing * 0.4, -155), (58 + swing, -15)], "#343b49", 29)
        d.rounded_rectangle(
            box(-91 - swing, -24, -29 - swing, 4), int(12 * scale), fill="#c0c1bd"
        )
        d.rounded_rectangle(
            box(29 + swing, -24, 91 + swing, 4), int(12 * scale), fill="#c0c1bd"
        )
        d.rounded_rectangle(box(-85, -540, 85, -280), int(24 * scale), fill=shirt)
        line([(0, -520), (0, -300)], "#c8c8bc", 3)
        line([(-25, -510), (-25, -435)], "#c5c4b8", 3)
        line([(25, -510), (25, -435)], "#c5c4b8", 3)
        left = (-100 - swing * 0.25, -290 + swing * 0.2)
        right = (110 + swing * 0.25, -290 - swing * 0.2)
        if pose == "knock":
            right = (175 + math.sin(t * 8) * 14, -510)
        elif pose == "listen":
            right = (90, -650 + math.sin(t * 2) * 4)
        elif pose in ("offer", "open_door"):
            right = (200, -385 + math.sin(t * 2) * 10)
        elif pose == "phone":
            right = (110, -600)
        elif pose in ("read", "discover"):
            left, right = (-80, -390), (90, -390)
        elif pose == "celebrate":
            left, right = (-155, -650), (155, -650)
        elif pose == "think":
            right = (75, -625)
        for shoulder, hand in [((-77, -510), left), ((77, -510), right)]:
            elbow = ((shoulder[0] + hand[0]) * 0.5, (shoulder[1] + hand[1]) * 0.5 + 15)
            line([shoulder, elbow, hand], shirt, 30)
            d.ellipse(
                box(hand[0] - 15, hand[1] - 15, hand[0] + 15, hand[1] + 15), fill=skin
            )
        d.rectangle(box(-25, -580, 25, -520), fill=skin)
        d.ellipse(box(-78, -760, 78, -565), fill=skin)
        d.pieslice(box(-86, -793, 86, -635), 180, 360, fill="#3b302c")
        d.polygon(
            [
                p(-81, -710),
                p(-60, -775),
                p(37, -784),
                p(81, -720),
                p(28, -742),
                p(-29, -729),
            ],
            fill="#3b302c",
        )
        blink = math.sin(t * 2.3 + (1 if friend else 0)) > 0.99
        for xx in (-28, 28):
            if blink:
                line([(xx - 10, -668), (xx + 10, -668)], ink, 4)
            else:
                d.ellipse(box(xx - 7, -680, xx + 7, -660), fill=ink)
            brow = -700 + (5 if emotion == "worried" else 0)
            line(
                [
                    (xx - 13, brow - 4 if xx < 0 and emotion == "worried" else brow),
                    (xx + 13, brow),
                ],
                ink,
                4,
            )
        if emotion == "surprised" or (speaking and math.sin(t * 17) > 0.1):
            d.ellipse(box(-11, -631, 11, -602), fill="#6e4640")
        elif emotion == "happy":
            d.arc(
                box(-24, -645, 24, -606),
                0,
                180,
                fill="#77493f",
                width=max(2, int(4 * scale)),
            )
        else:
            line([(-16, -618), (15, -620)], "#86564b", 4)
        if prop == "phone" or pose == "phone":
            u, v = right
            d.rounded_rectangle(
                box(u - 24, v - 64, u + 22, v + 20),
                int(7 * scale),
                fill="#17212c",
                outline="#bec6ca",
                width=max(1, int(3 * scale)),
            )
            d.rectangle(box(u - 16, v - 53, u + 14, v + 4), fill="#6c9cbd")
        elif prop == "bottle":
            u, v = right
            d.rounded_rectangle(
                box(u - 22, v - 65, u + 23, v + 30),
                int(9 * scale),
                fill="#72afc4",
                outline="#bedbdb",
                width=max(1, int(2 * scale)),
            )
            d.rectangle(box(u - 12, v - 80, u + 12, v - 66), fill="#244c69")
            line([(u - 16, v - 15), (u + 17, v - 15)], "#d8e3d6", 18)
        elif prop == "letter" or pose == "read":
            d.rounded_rectangle(
                box(-75, -438, 105, -320), int(5 * scale), fill="#e9dcc3"
            )
            for yy in (-409, -385, -361):
                line([(-51, yy), (77, yy)], "#968d7f", 3)
        elif prop == "box" or pose == "discover":
            d.rectangle(
                box(-85, -413, 100, -285),
                fill="#a8784d",
                outline="#513b30",
                width=max(1, int(3 * scale)),
            )
            lift = (0.5 + 0.5 * math.sin(t * 2)) * 32
            d.polygon(
                [p(-95, -422), p(96, -422 - lift), p(107, -450 - lift), p(-80, -450)],
                fill="#d0a26b",
            )

    def graphic(self, image, scene, t, duration):
        kind = scene.get("graphic", "none")
        d = ImageDraw.Draw(image)
        if kind == "building":
            d.rounded_rectangle(
                (225, 480, 855, 1450), 20, fill="#f2ead9", outline="#6b665f", width=5
            )
            for row in range(9):
                y = 540 + row * 92
                d.line((270, y, 780, y), fill="#aea89d", width=3)
                self.label(d, (310, y + 38), f"{9-row:02d}", 25, fill="#5a6267")
                for col in range(5):
                    d.rectangle(
                        (370 + col * 75, y + 19, 414 + col * 75, y + 62),
                        outline="#9da3a0",
                        width=2,
                    )
            progress = min(1, t / max(1, duration - 0.5))
            cy = 1300 - progress * 670
            d.ellipse((495, cy - 18, 531, cy + 18), fill="#b54451")
            d.line((535, cy, 750, cy), fill="#b54451", width=4)
            self.label(d, (540, 1400), "เส้นทางที่ต้องตรวจสอบ", 27, fill="#394657")
        elif kind == "comparison":
            for x, title, color in [
                (90, "ตรวจสอบก่อน", "#3a8a73"),
                (570, "รีบตัดสินใจ", "#a65360"),
            ]:
                d.rounded_rectangle((x, 610, x + 420, 1170), 25, fill="#e9e4d8")
                d.rounded_rectangle((x, 610, x + 420, 710), 20, fill=color)
                self.label(d, (x + 210, 660), title, 32)
                for k in range(4):
                    yy = 780 + k * 80
                    d.ellipse((x + 55, yy, x + 80, yy + 25), fill=color)
                    d.line(
                        (x + 110, yy + 12, x + 330, yy + 12), fill="#adaaa0", width=8
                    )
        elif kind == "countdown":
            count = max(1, math.ceil(duration - t))
            d.rounded_rectangle((360, 365, 720, 545), 25, fill="#141c2b")
            self.label(d, (540, 450), str(count), 108, fill="#f5cc82")
        elif kind == "spotlight":
            mask = Image.new("RGBA", SIZE, (0, 0, 0, 150))
            md = ImageDraw.Draw(mask)
            cx = 610 + math.sin(t * 0.65) * 130
            md.ellipse((cx - 280, 500, cx + 280, 1320), fill=(0, 0, 0, 0))
            image.alpha_composite(mask)

    def frame(self, scene, t, duration, speaking=False, background=None):
        setting = scene.get("setting", "room")
        if setting == "studio":
            setting = "room"
        image = (
            background.copy().convert("RGBA")
            if background is not None
            else self.scenery(setting).copy()
        )
        d = ImageDraw.Draw(image)
        cast = scene.get("cast", "solo")
        pose = scene.get("action", "think")
        emotion = scene.get("expression", "neutral")
        prop = scene.get("prop", "none")
        if pose == "knock" and setting == "room":
            for k in range(3):
                x = 850 + k * 32
                y = 970 + math.sin(t * 8 + k) * 8
                d.arc(
                    (x - 20, y - 30, x + 20, y + 30), -70, 70, fill="#d8bd83", width=4
                )
        moving = pose in ("walk", "run")
        shift = math.sin(t * 0.9) * 50 if moving else math.sin(t * 1.4) * 4
        ground = 1530
        if cast == "pair":
            self.person(
                d, 335 + shift, ground, 0.86, t, pose, False, emotion, prop, speaking
            )
            self.person(
                d,
                745,
                ground,
                0.83,
                t + 0.35,
                "look",
                True,
                "worried" if emotion == "worried" else "neutral",
                "none",
                False,
            )
            self.label(d, (335, ground - 740), self.project.get("lead_name", "นที"), 26)
            self.label(
                d, (745, ground - 740), self.project.get("friend_name", "มีนา"), 26
            )
        elif cast in ("solo", "friend"):
            x = 535 + shift
            if setting == "room" and pose in ("knock", "open_door"):
                x = 590
            self.person(
                d, x, ground, 0.98, t, pose, cast == "friend", emotion, prop, speaking
            )
        if pose == "open_door" and setting in ("room", "corridor"):
            # Door panel reveals a moving wedge of light, independently of the actor.
            x = 910
            y = 420
            reveal = int(70 * (0.5 + 0.5 * math.sin(t * 1.7)))
            d.polygon(
                [(x, y), (x + reveal, y + 35), (x + reveal, 1430), (x, 1450)],
                fill="#d5bb82",
            )
        self.graphic(image, scene, t, duration)
        tint = {
            "mystery": (19, 27, 64, 20),
            "warm": (125, 65, 27, 18),
            "pop": (31, 84, 83, 12),
        }.get(self.project.get("palette"), (0, 0, 0, 0))
        image.alpha_composite(Image.new("RGBA", SIZE, tint))
        image.alpha_composite(self.vignette)
        camera = scene.get("camera", "medium")
        zoom = {"wide": 1, "medium": 1.08, "close": 1.38, "detail": 1.19}[camera] + min(
            0.05, t / max(duration, 1) * 0.05
        )
        # Slow push-in plus purposeful shot-size changes at scene boundaries.
        focus_x = 540 + math.sin(t * 0.35) * 18
        focus_y = 1040 if camera == "close" else 950
        width, height = 1080 / zoom, 1920 / zoom
        left = max(0, min(1080 - width, focus_x - width / 2))
        top = max(0, min(1920 - height, focus_y - height / 2))
        image = image.crop(
            (int(left), int(top), int(left + width), int(top + height))
        ).resize(SIZE, Image.Resampling.BILINEAR)
        return image
