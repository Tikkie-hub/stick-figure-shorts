import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))
from app import app
from studio import validate_project
from story_planner import local_outline, draft_story
from story_art import StoryStage


class StoryTests(unittest.TestCase):
    def test_outline_is_valid_and_honestly_identified(self):
        for genre in ("mystery", "motivation", "knowledge"):
            draft = local_outline("เรื่องลิฟต์และจดหมายเตือนจากอนาคต", genre, "warm")
            project = validate_project(draft)
            self.assertEqual(project["visual_style"], "cinematic")
            self.assertEqual(len(project["scenes"]), 6)
            self.assertEqual(draft["writer_mode"], "outline")
            self.assertIn("ยังไม่ใช่ AI", draft["writer_notice"])
        self.assertNotEqual(
            local_outline("จดหมายในห้องพัก")["scenes"],
            local_outline("โทรศัพท์ในลิฟต์")["scenes"],
        )

    def test_model_response_is_validated_and_cannot_set_file_paths(self):
        draft = local_outline("จดหมายในห้องพัก")
        draft["background_path"] = "/etc/passwd"
        response = MagicMock(status_code=200)
        response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": json.dumps(draft, ensure_ascii=False)}]
                    }
                }
            ]
        }
        with patch.dict(os.environ, {"STORY_API_KEY": "secret-test-only"}), patch(
            "story_planner.requests.post", return_value=response
        ) as post:
            result = draft_story("จดหมายจากอนาคต", writer="ai")
            self.assertEqual(result["writer_mode"], "ai")
            self.assertNotIn("background_path", result)
            validate_project(result)
            self.assertEqual(
                post.call_args.kwargs["headers"]["x-goog-api-key"], "secret-test-only"
            )
            response.status_code = 429
            with self.assertRaises(RuntimeError) as error:
                draft_story("จดหมายจากอนาคต", writer="ai")
            self.assertNotIn("secret-test-only", str(error.exception))

    def test_draft_api_and_scene_enums(self):
        client = app.test_client()
        response = client.post(
            "/api/studio/draft",
            json={"idea": "ขึ้นลิฟต์แล้วพบจดหมายแปลก ๆ", "writer": "outline"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["scenes"][0]["setting"], "elevator")
        project = response.json
        project["scenes"][0]["camera"] = "../../etc/passwd"
        self.assertEqual(client.post("/api/studio/jobs", json=project).status_code, 400)
        self.assertEqual(
            client.post("/api/studio/draft", json={"idea": "สั้น"}).status_code, 400
        )
        with patch.dict(os.environ, {}, clear=True):
            response = client.post(
                "/api/studio/draft", json={"idea": "จดหมายจากอนาคต", "writer": "ai"}
            )
            self.assertEqual(response.status_code, 400)

    def test_scene_preview_and_ending_controls(self):
        client = app.test_client()
        project = local_outline("ลิฟต์กับจดหมายแปลก ๆ")
        response = client.post("/api/studio/preview", json=project | {"scene_index": 0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/jpeg")
        self.assertTrue(response.data.startswith(b"\xff\xd8"))
        self.assertEqual(
            client.post(
                "/api/studio/preview", json=project | {"scene_index": 99}
            ).status_code,
            400,
        )
        for genre in ("mystery", "motivation", "knowledge"):
            warm = local_outline("จดหมายในห้องพัก", genre, "warm")
            opened = local_outline("จดหมายในห้องพัก", genre, "open")
            self.assertNotEqual(
                warm["scenes"][-1]["narration"], opened["scenes"][-1]["narration"]
            )

    def test_every_set_and_action_renders_changing_frames(self):
        from story_schema import ACTIONS, SCENE_CHOICES

        font = Path(__file__).resolve().parents[1] / "assets/fonts/Kanit-Bold.ttf"
        if not font.exists():
            self.skipTest("Kanit font not downloaded")
        project = validate_project(local_outline("จดหมายในห้องพัก"))
        stage = StoryStage(font, project)
        for setting in SCENE_CHOICES["setting"]:
            scene = project["scenes"][0] | {
                "setting": setting,
                "cast": "pair",
                "camera": "wide",
                "graphic": "none",
            }
            a = np.asarray(stage.frame(scene, 0.2, 4, True))
            b = np.asarray(stage.frame(scene, 1.1, 4, True))
            self.assertEqual(a.shape, (1920, 1080, 4))
            self.assertGreater(np.mean(np.abs(a.astype(float) - b.astype(float))), 0.05)
        for action in ACTIONS:
            image = stage.frame(project["scenes"][0] | {"action": action}, 0.5, 4, True)
            self.assertEqual(image.size, (1080, 1920))
        for graphic in SCENE_CHOICES["graphic"]:
            stage.frame(project["scenes"][0] | {"graphic": graphic}, 1, 4, True)


if __name__ == "__main__":
    unittest.main()
