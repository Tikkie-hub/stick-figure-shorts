"""Animated shorts renderer with real Edge word timings; used by the web worker."""

import os
from pathlib import Path
import sys

if __name__ == "__main__":
    import truststore

    truststore.inject_into_ssl()

import asyncio
import bisect
import json
import math
import time
import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, CompositeAudioClip, VideoClip, VideoFileClip
from proglog import ProgressBarLogger
from auto_knowledge_shorts import ensure_font, ROOT
from story_art import StoryStage

W, H = 1080, 1920
ACTIONS = {"discover", "think", "run", "celebrate", "space", "read"}
PALETTES = {
    "pop": ("#11172c", "#262153", "#bdff52"),
    "mystery": ("#101523", "#302342", "#d0a4ff"),
    "warm": ("#251726", "#61372f", "#ffd181"),
}


def save_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


async def narrate(text, path):
    words = []
    speaker = edge_tts.Communicate(
        text,
        voice="th-TH-NiwatNeural",
        boundary="WordBoundary",
        proxy=os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"),
    )

    async def receive():
        with path.open("wb") as output:
            async for event in speaker.stream():
                if event["type"] == "audio":
                    output.write(event["data"])
                elif event["type"] == "WordBoundary":
                    words.append(
                        {
                            "text": event["text"],
                            "start": event["offset"] / 10_000_000,
                            "end": (event["offset"] + event["duration"]) / 10_000_000,
                        }
                    )

    await asyncio.wait_for(receive(), timeout=180)
    if not words or not path.stat().st_size:
        raise RuntimeError("บริการเสียงไม่ได้ส่งเสียงหรือเวลาของคำกลับมา กรุณาลองใหม่")
    return words


def caption_groups(words):
    groups, group = [], []
    for word in words:
        if group and (
            len(group) >= 3
            or sum(len(w["text"]) for w in group) + len(word["text"]) > 18
            or word["start"] - group[-1]["end"] > 0.3
        ):
            groups.append(group)
            group = []
        group.append(word)
    if group:
        groups.append(group)
    return groups


class RenderProgress(ProgressBarLogger):
    def __init__(self, path):
        super().__init__()
        self.path, self.last = path, 0

    def bars_callback(self, bar, attr, value, old_value=None):
        if (
            bar == "frame_index"
            and attr == "index"
            and time.monotonic() - self.last > 0.8
        ):
            total = self.bars[bar].get("total") or 1
            save_json(
                self.path,
                {
                    "status": "rendering",
                    "progress": min(98, 25 + int(value / total * 73)),
                    "message": "กำลังตัดต่อภาพ เสียง และซับตามคำพูด",
                },
            )
            self.last = time.monotonic()


def hex_rgb(value):
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))


def background(palette):
    top, bottom, _ = PALETTES[palette]
    blend = np.linspace(0, 1, H)[:, None, None]
    pixels = (
        np.array(hex_rgb(top))[None, None, :] * (1 - blend)
        + np.array(hex_rgb(bottom))[None, None, :] * blend
    )
    return Image.fromarray(np.repeat(pixels.astype("uint8"), W, axis=1))


def actor(draw, center, t, action, accent):
    """Draw an articulated character, moving props and actions, not a static cutout."""
    x, y = center
    bounce = math.sin(t * (11 if action == "run" else 3)) * (
        24 if action == "run" else 10
    )
    y += bounce
    swing = math.sin(t * 10) * 90 if action == "run" else math.sin(t * 3) * 15
    ink = "#0b1021"
    # Ground shadow follows the action.
    draw.ellipse((x - 150, y + 435, x + 150, y + 473), fill="#080d1a")
    draw.line([(x, y + 255), (x - 85 - swing, y + 435)], fill="#e5eaf2", width=26)
    draw.line([(x, y + 255), (x + 85 + swing, y + 435)], fill="#e5eaf2", width=26)
    draw.rounded_rectangle((x - 75, y + 90, x + 75, y + 285), 44, fill=accent)
    left = (x - 150, y + 150 + swing)
    right = (x + 155, y + 150 - swing)
    if action == "think":
        right = (x + 88, y + 35 + math.sin(t * 4) * 10)
    if action in ("discover", "read"):
        left, right = (x - 130, y + 250), (x + 130, y + 250 + math.sin(t * 4) * 12)
    if action == "celebrate":
        left, right = (x - 160, y - 75 + swing), (x + 160, y - 75 - swing)
    draw.line([(x - 65, y + 125), left], fill="#e5eaf2", width=24)
    draw.line([(x + 65, y + 125), right], fill="#e5eaf2", width=24)
    draw.ellipse(
        (x - 108, y - 112, x + 108, y + 104), fill="#ffd454", outline=ink, width=12
    )
    blink = math.sin(t * 2.2) > 0.985
    for dx in (-39, 39):
        if blink:
            draw.line((x + dx - 10, y - 9, x + dx + 10, y - 9), fill=ink, width=9)
        else:
            draw.ellipse((x + dx - 10, y - 24, x + dx + 10, y + 1), fill=ink)
    if action == "discover":
        draw.ellipse((x - 17, y + 28, x + 17, y + 65), fill=ink)
        # Opening box lid and rising light rays.
        bx, by = x + 230, y + 310
        draw.rounded_rectangle(
            (bx - 90, by - 65, bx + 90, by + 80),
            12,
            fill="#c48755",
            outline=ink,
            width=8,
        )
        lift = (0.5 + 0.5 * math.sin(t * 2.3)) * 65
        draw.polygon(
            [
                (bx - 100, by - 75),
                (bx + 90, by - 75 - lift),
                (bx + 115, by - 112 - lift),
                (bx - 80, by - 112),
            ],
            fill="#e0ad75",
            outline=ink,
            width=7,
        )
        for k in range(4):
            sx = bx - 60 + k * 40
            draw.line(
                (sx, by - 140 - lift, sx + math.sin(t + k) * 12, by - 175 - lift),
                fill=accent,
                width=6,
            )
    else:
        draw.arc((x - 37, y + 10, x + 37, y + 62), 5, 175, fill=ink, width=8)
    if action == "read":
        px = x + math.sin(t * 2) * 12
        draw.rounded_rectangle(
            (px - 115, y + 180, px + 115, y + 345),
            12,
            fill="#fff1d5",
            outline=ink,
            width=7,
        )
        for dy in (220, 255, 290):
            draw.line((px - 75, y + dy, px + 75, y + dy), fill="#8b7c76", width=6)
    if action == "think":
        for k in range(3):
            radius = 12 + 9 * k
            cx, cy = x + 140 + k * 48, y - 80 - k * 56 + math.sin(t * 2 + k) * 10
            draw.ellipse(
                (cx - radius, cy - radius, cx + radius, cy + radius), fill=accent
            )
    if action == "run":
        for k in range(5):
            sy = y + 60 + k * 70
            sx = x - 220 - ((t * 250 + k * 40) % 170)
            draw.line((sx - 90, sy, sx, sy), fill=accent, width=5)


def caption_image(group, active, font_path, accent, boxed=True):
    """One short phrase, with the speaking token highlighted, fully shaped by RAQM."""
    canvas = Image.new("RGBA", (1000, 240))
    draw = ImageDraw.Draw(canvas)
    text = "".join(word["text"] for word in group)
    size = 88
    while size > 42:
        font = ImageFont.truetype(
            str(font_path), size, layout_engine=ImageFont.Layout.RAQM
        )
        if draw.textlength(text, font=font) < 880:
            break
        size -= 4
    width = int(draw.textlength(text, font=font))
    # Preserve Thai shaping by drawing the full phrase in both colors; mask a token region.
    if boxed:
        draw.rounded_rectangle(
            ((1000 - width) / 2 - 32, 35, (1000 + width) / 2 + 32, 195),
            28,
            fill=(7, 10, 20, 242),
        )
    x = (1000 - width) / 2
    draw.text(
        (500, 66),
        text,
        font=font,
        fill="white",
        anchor="mt",
        stroke_width=2,
        stroke_fill="#080c18",
    )
    colored = Image.new("RGBA", canvas.size)
    ImageDraw.Draw(colored).text(
        (500, 66),
        text,
        font=font,
        fill=accent,
        anchor="mt",
        stroke_width=2,
        stroke_fill="#080c18",
    )
    start = draw.textlength("".join(w["text"] for w in group[:active]), font=font)
    end = draw.textlength("".join(w["text"] for w in group[: active + 1]), font=font)
    mask = Image.new("L", canvas.size)
    ImageDraw.Draw(mask).rectangle(
        (int(x + start - 2), 0, int(x + end + 2), 239), fill=255
    )
    alpha = np.minimum(np.array(colored.getchannel("A")), np.array(mask))
    colored.putalpha(Image.fromarray(alpha))
    canvas.alpha_composite(colored)
    return canvas


def render_project(project, directory):
    directory = Path(directory)
    status = directory / "status.json"
    font = ensure_font(ROOT / "assets/fonts/Kanit-Bold.ttf")
    palette = project.get("palette", "pop")
    accent = PALETTES[palette][2]
    base = background(palette)
    cinematic = project.get("visual_style") == "cinematic"
    stage = StoryStage(font, project) if cinematic else None
    heading_font = ImageFont.truetype(str(font), 45)
    tiny_font = ImageFont.truetype(str(font), 29)
    resources, timeline, audio_tracks = [], [], []
    source = None
    try:
        if project.get("background_path"):
            source = VideoFileClip(project["background_path"], audio=False)
            resources.append(source)
            if not source.duration:
                raise RuntimeError("คลิปพื้นหลังไม่มีความยาว")
        elapsed = 0
        for i, scene in enumerate(project["scenes"]):
            save_json(
                status,
                {
                    "status": "speech",
                    "progress": 3 + int(i / len(project["scenes"]) * 20),
                    "message": f'กำลังสร้างเสียงและจับเวลาคำ ฉาก {i + 1}/{len(project["scenes"])}',
                },
            )
            path = directory / f"voice-{i}.mp3"
            words = asyncio.run(narrate(scene["narration"], path))
            audio = AudioFileClip(str(path))
            resources.append(audio)
            track = audio.with_start(elapsed)
            resources.append(track)
            audio_tracks.append(track)
            duration = audio.duration + 0.3
            timeline.append(
                {
                    "start": elapsed,
                    "duration": duration,
                    "narration_seconds": audio.duration,
                    "scene": scene,
                    "words": words,
                    "groups": caption_groups(words),
                }
            )
            elapsed += duration
        starts = [entry["start"] for entry in timeline]
        # Cache small caption cards only; never store full-size frames per word.
        cache = {}

        def frame(t):
            index = min(len(timeline) - 1, bisect.bisect_right(starts, t) - 1)
            entry = timeline[index]
            local = t - entry["start"]
            scene = entry["scene"]
            if source:
                raw = Image.fromarray(source.get_frame(t % source.duration))
                scale = max(W / raw.width, H / raw.height) * (
                    1.04 + 0.035 * math.sin(local * 0.7)
                )
                raw = raw.resize(
                    (math.ceil(raw.width * scale), math.ceil(raw.height * scale)),
                    Image.Resampling.BILINEAR,
                )
                cx = (raw.width - W) / 2 + math.sin(local * 0.8) * min(
                    35, (raw.width - W) / 2
                )
                cy = (raw.height - H) / 2
                image = raw.crop((int(cx), int(cy), int(cx) + W, int(cy) + H)).convert(
                    "RGBA"
                )
                image.alpha_composite(Image.new("RGBA", (W, H), (8, 12, 24, 95)))
            else:
                image = base.copy().convert("RGBA")
            if not cinematic:
                draw = ImageDraw.Draw(image)
                # Scene-driven parallax, animated orbit particles and progress strip.
                for k in range(15):
                    px = (k * 193 + math.sin(local * 0.5 + k) * 75) % W
                    py = (k * 137 - local * (24 + k % 4 * 10)) % H
                    radius = 3 + k % 3 * 2
                    draw.ellipse(
                        (px - radius, py - radius, px + radius, py + radius),
                        fill=accent if k % 4 == 0 else "#69708d",
                    )
                draw.rounded_rectangle((65, 145, 1015, 245), 25, fill="#0c1225")
                title = scene["header_title"][:32]
                title_font = heading_font
                while draw.textlength(title, font=title_font) > 850:
                    title_font = ImageFont.truetype(str(font), title_font.size - 2)
                draw.text((540, 166), title, font=title_font, fill="white", anchor="mt")
                draw.text(
                    (75, 285),
                    f"{index + 1:02d} / {len(timeline):02d}",
                    font=tiny_font,
                    fill=accent,
                )
                action = scene.get("action", "think")
                # Change shot scale/position every ~2.6 seconds, with eased camera movement.
                shot = int(local / 2.6)
                center_x = 460 + math.sin(local * 0.7) * 36 + (35 if shot % 2 else -20)
                if action == "run":
                    center_x += math.sin(local * 1.5) * 95
                center_y = 710 + math.sin(local * 0.5) * 18
                if action == "space":
                    for k in range(3):
                        cx = 540 + math.cos(local * 0.6 + k * 2) * 290
                        cy = 850 + math.sin(local * 0.6 + k * 2) * 210
                        draw.ellipse((cx - 32, cy - 32, cx + 32, cy + 32), fill=accent)
                actor(draw, (center_x, center_y), local, action, accent)
                if action == "celebrate":
                    for k in range(24):
                        cx = (k * 113 + math.sin(local + k) * 50) % W
                        cy = (local * 180 + k * 83) % 1350
                        draw.rectangle(
                            (cx, cy, cx + 10, cy + 20),
                            fill=accent if k % 2 else "#ffa1d2",
                        )
                # Brief hook label; the long highlight paragraph from the old layout is gone.
                if local < 1.2:
                    label = {
                        "discover": "เจออะไรบางอย่าง",
                        "read": "ข้อความนี้…",
                        "run": "แล้วเขาก็เริ่ม",
                        "think": "เคยสงสัยไหม",
                        "celebrate": "คำตอบคือ…",
                        "space": "มองขึ้นไป",
                    }.get(action, "เรื่องกำลังเปลี่ยนไป")
                    label_font = ImageFont.truetype(str(font), 42)
                    width = draw.textlength(label, font=label_font) + 70
                    x = 540 - width / 2
                    y = 405 - int(18 * math.exp(-local * 8))
                    draw.rounded_rectangle((x, y, x + width, y + 95), 24, fill=accent)
                    draw.text(
                        (540, y + 16),
                        label,
                        font=label_font,
                        fill="#101526",
                        anchor="mt",
                    )
            else:
                speaking = any(
                    word["start"] <= local <= word["end"] for word in entry["words"]
                )
                image = stage.frame(
                    scene, local, entry["duration"], speaking, image if source else None
                )
                draw = ImageDraw.Draw(image)
                title = scene["header_title"]
                title_font = heading_font
                while draw.textlength(title, font=title_font) > 850:
                    title_font = ImageFont.truetype(str(font), title_font.size - 2)
                width = draw.textlength(title, font=title_font) + 80
                draw.rounded_rectangle(
                    ((1080 - width) / 2, 95, (1080 + width) / 2, 180),
                    22,
                    fill="#ede4d1",
                )
                draw.text(
                    (540, 113), title, font=title_font, fill="#242d37", anchor="mt"
                )
                draw.text(
                    (78, 220),
                    f"{index+1:02d} / {len(timeline):02d}",
                    font=tiny_font,
                    fill="#d8c79f",
                )
            for gi, group in enumerate(entry["groups"]):
                end = group[-1]["end"] + 0.06
                if group[0]["start"] <= local <= end:
                    active = max(i for i, w in enumerate(group) if w["start"] <= local)
                    key = (index, gi, active)
                    if key not in cache:
                        cache[key] = caption_image(
                            group,
                            active,
                            font,
                            "#ffd56b" if cinematic else accent,
                            boxed=not cinematic,
                        )
                    age = local - group[0]["start"]
                    # Pop-in movement on each phrase, without changing its speech timing.
                    y = (
                        1150 if project.get("caption_position") == "middle" else 1380
                    ) + int(20 * math.exp(-age * 18) * math.cos(age * 22))
                    image.alpha_composite(cache[key], (40, y))
                    break
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle((70, 1780, 1010, 1790), 5, fill="#41465b")
            draw.rounded_rectangle(
                (70, 1780, 70 + max(1, 940 * t / elapsed), 1790), 5, fill=accent
            )
            return np.array(image.convert("RGB"))

        audio = CompositeAudioClip(audio_tracks).with_duration(elapsed)
        resources.append(audio)
        clip = VideoClip(frame_function=frame, duration=elapsed).with_audio(audio)
        resources.append(clip)
        save_json(
            status,
            {
                "status": "rendering",
                "progress": 25,
                "message": "กำลังตัดต่อภาพและซับตามเสียง",
            },
        )
        clip.write_videofile(
            str(directory / "video.mp4"),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="veryfast",
            threads=2,
            temp_audiofile=str(directory / "mixed.m4a"),
            logger=RenderProgress(status),
        )
        save_json(
            directory / "timeline.json",
            {
                "voice": "th-TH-NiwatNeural",
                "duration": elapsed,
                "caption_timing": "Edge TTS WordBoundary",
                "scenes": timeline,
            },
        )
        save_json(
            status,
            {
                "status": "done",
                "progress": 100,
                "message": "คลิปพร้อมแล้ว ดูตัวอย่างและดาวน์โหลดได้เลย",
            },
        )
    finally:
        for resource in reversed(resources):
            resource.close()


if __name__ == "__main__":
    directory = Path(sys.argv[1]).resolve()
    try:
        project = json.loads((directory / "project.json").read_text(encoding="utf-8"))
        render_project(project, directory)
    except Exception as error:
        # Keep credential-bearing URLs out of the public job response.
        message = (
            "สร้างเสียงไม่ได้ ตรวจการเชื่อมต่อ Edge TTS แล้วลองใหม่"
            if isinstance(
                error, (edge_tts.exceptions.EdgeTTSException, asyncio.TimeoutError)
            )
            else "สร้างคลิปไม่สำเร็จ กรุณาตรวจไฟล์พื้นหลังหรือการเชื่อมต่อ แล้วลองอีกครั้ง"
        )
        save_json(
            directory / "status.json",
            {"status": "failed", "progress": 0, "message": message},
        )
        print(type(error).__name__, file=sys.stderr)
        sys.exit(1)
