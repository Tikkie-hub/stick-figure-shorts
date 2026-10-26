import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))
from app import app
import studio
from studio_render import caption_groups


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_templates_and_legacy(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertIn("สร้างคลิปของฉัน", self.client.get("/").text)
        self.assertEqual(len(self.client.get("/api/studio/templates").json), 3)
        self.assertEqual(self.client.get("/gemini").status_code, 200)

    def test_invalid_projects_and_paths(self):
        for data in (
            None,
            {},
            {"scenes": []},
            {
                "scenes": [
                    {"header_title": "title", "narration": "text", "action": "evil"}
                ]
            },
            {
                "scenes": studio.TEMPLATES["brain"]["scenes"],
                "background_id": "../../etc/passwd",
            },
        ):
            self.assertEqual(
                self.client.post("/api/studio/jobs", json=data).status_code, 400
            )
        self.assertEqual(self.client.get("/api/studio/jobs/not-a-job").status_code, 404)
        self.assertEqual(
            self.client.get("/api/studio/jobs/" + "a" * 32 + "/secrets").status_code,
            404,
        )

    def test_job_creation_busy_and_saved_progress(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            studio, "JOBS", Path(temporary)
        ), patch.object(studio, "active", None), patch.object(
            studio.executor, "submit"
        ) as submit:
            response = self.client.post(
                "/api/studio/jobs", json=studio.TEMPLATES["brain"]
            )
            self.assertEqual(response.status_code, 202)
            identity = response.json["id"]
            self.assertEqual(
                self.client.get("/api/studio/jobs/" + identity).json["status"], "queued"
            )
            self.assertEqual(
                self.client.post(
                    "/api/studio/jobs", json=studio.TEMPLATES["brain"]
                ).status_code,
                409,
            )
            submit.assert_called_once()
            status = Path(temporary) / identity / "status.json"
            status.write_text(
                json.dumps({"status": "done", "progress": 100, "message": "done"})
            )
            self.assertEqual(
                self.client.get("/api/studio/recent").json[0]["id"], identity
            )
            project = self.client.get("/api/studio/jobs/" + identity + "/project").json
            self.assertNotIn("background_path", project)

    def test_upload_rejects_fake_video(self):
        import io

        with tempfile.TemporaryDirectory() as temporary, patch.object(
            studio, "UPLOADS", Path(temporary)
        ):
            response = self.client.post(
                "/api/studio/background",
                data={"file": (io.BytesIO(b"not a video"), "test.mp4")},
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_short_captions_keep_real_word_times(self):
        words = [
            {"text": text, "start": index * 0.3, "end": index * 0.3 + 0.22}
            for index, text in enumerate(
                ["เมื่อ", "คืน", "ผม", "เปิด", "กล่อง", "ใบ", "หนึ่ง"]
            )
        ]
        groups = caption_groups(words)
        self.assertTrue(all(len(group) <= 3 for group in groups))
        self.assertEqual([word for group in groups for word in group], words)
        self.assertEqual(groups[1][0]["start"], words[3]["start"])


if __name__ == "__main__":
    unittest.main()
