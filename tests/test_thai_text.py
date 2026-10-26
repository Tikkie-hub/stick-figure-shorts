from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, AsyncMock
import json
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont, features
from thai_text import HarfBuzzFont, load_font
from render_errors import describe_error

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "assets/fonts/Kanit-Bold.ttf"


class ThaiTextTests(unittest.TestCase):
    def setUp(self):
        if not FONT.exists():
            self.skipTest("Kanit font required")

    def test_harfbuzz_without_raqm_shapes_thai(self):
        with patch("thai_text.features.check_feature", return_value=False):
            font = load_font(FONT, 72)
            self.assertIsInstance(font, HarfBuzzFont)
            image = Image.new("RGB", (1000, 250), "black")
            draw = ImageDraw.Draw(image)
            draw.text(
                (500, 20),
                "น้ำขึ้นให้รีบตัก",
                font=font,
                anchor="mt",
                fill="white",
                stroke_width=2,
            )
            self.assertIsNotNone(image.getbbox())
        if features.check_feature("raqm"):
            native = ImageFont.truetype(
                str(FONT), 72, layout_engine=ImageFont.Layout.RAQM
            )
            self.assertAlmostEqual(
                font.getlength("น้ำขึ้นให้รีบตัก"),
                native.getlength("น้ำขึ้นให้รีบตัก"),
                delta=1,
            )

    def test_font_and_network_errors_are_actionable_and_redacted(self):
        result = describe_error(
            RuntimeError("Pillow needs libraqm for correctly shaped Thai text"), "font"
        )
        self.assertEqual(result["error_code"], "THAI_FONT_SETUP")
        self.assertIn("start.bat", result["message"])
        result = describe_error(
            RuntimeError("https://host.test/path?key=private-secret"), "speech"
        )
        self.assertNotIn("private-secret", json.dumps(result))
        self.assertEqual(result["error_code"], "TTS_FAILED")

    def test_real_mp4_with_forced_harfbuzz_backend(self):
        if not shutil.which("ffmpeg"):
            self.skipTest("ffmpeg required")
        import studio_render

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:duration=0.3",
                    str(work / "source.mp3"),
                ],
                check=True,
            )

            async def voice(text, path):
                shutil.copyfile(work / "source.mp3", path)
                return [
                    {"text": "น้ำขึ้น", "start": 0.02, "end": 0.12},
                    {"text": "ให้รีบตัก", "start": 0.13, "end": 0.28},
                ]

            project = {
                "visual_style": "cinematic",
                "palette": "mystery",
                "caption_position": "middle",
                "scenes": [
                    {
                        "header_title": "ผู้ที่อยู่หน้าประตู",
                        "narration": "น้ำขึ้นให้รีบตัก",
                        "action": "listen",
                        "setting": "room",
                        "cast": "pair",
                        "camera": "medium",
                        "prop": "letter",
                        "expression": "worried",
                        "graphic": "none",
                    }
                ],
            }
            with patch(
                "thai_text.features.check_feature", return_value=False
            ), patch.object(studio_render, "narrate", voice):
                studio_render.render_project(project, work)
            self.assertEqual(
                json.loads((work / "status.json").read_text())["status"], "done"
            )
            result = json.loads(
                subprocess.check_output(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-show_entries",
                        "stream=codec_type,width,height",
                        "-of",
                        "json",
                        str(work / "video.mp4"),
                    ]
                )
            )
            video = next(s for s in result["streams"] if s["codec_type"] == "video")
            self.assertEqual((video["width"], video["height"]), (1080, 1920))


if __name__ == "__main__":
    unittest.main()
