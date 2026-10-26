"""Local studio routes and one bounded background render worker."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import uuid
from flask import Blueprint, jsonify, request, send_file
from io import BytesIO

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "outputs/studio"
UPLOADS = JOBS / "uploads"
executor = ThreadPoolExecutor(max_workers=1)
lock = threading.Lock()
active = None
studio = Blueprint("studio", __name__)
sys.path.insert(0, str(ROOT))
from story_schema import ACTIONS, SCENE_CHOICES, SCENE_DEFAULTS
from story_planner import draft_story, writer_available, local_outline

TEMPLATES = {
    "mystery": {
        "name": "จดหมายจากวันพรุ่งนี้",
        "palette": "mystery",
        "scenes": [
            {
                "header_title": "จดหมายจากวันพรุ่งนี้",
                "narration": "เมื่อคืน ผมเจอกล่องใบหนึ่ง มันเขียนว่า ห้ามเปิดก่อนเที่ยงคืน",
                "action": "discover",
            },
            {
                "header_title": "ข้างในมีจดหมาย",
                "narration": "พอเปิดออก ข้างในมีจดหมายจากตัวผมเอง เขียนว่า พรุ่งนี้ อย่าลืมโทรหาแม่",
                "action": "read",
            },
            {
                "header_title": "บางเรื่อง ไม่ควรรอ",
                "narration": "ผมไม่รอให้ถึงพรุ่งนี้ ผมหยิบโทรศัพท์ แล้วโทรหาแม่ทันที",
                "action": "celebrate",
            },
        ],
    },
    "motivation": {
        "name": "ห้านาทีที่เปลี่ยนวัน",
        "palette": "pop",
        "scenes": [
            {
                "header_title": "ห้านาทีที่เปลี่ยนวัน",
                "narration": "เขารอวันที่พร้อม จนผ่านไปอีกหนึ่งปี แต่รองเท้าวิ่งคู่นั้น ยังอยู่ในกล่อง",
                "action": "think",
            },
            {
                "header_title": "เริ่มเล็กกว่าที่คิด",
                "narration": "เช้าวันหนึ่ง เขาไม่ตั้งเป้าวิ่งสิบกิโล เขาแค่ใส่รองเท้า แล้วออกไปห้านาที",
                "action": "run",
            },
            {
                "header_title": "พร้อม เพราะได้เริ่ม",
                "narration": "เขาไม่ได้เปลี่ยนชีวิตในวันเดียว แต่วันนั้น คือวันที่เขาเริ่มเปลี่ยนมัน",
                "action": "celebrate",
            },
        ],
    },
    "brain": {
        "name": "สมองไม่ได้เก็บภาพทุกอย่าง",
        "palette": "warm",
        "scenes": [
            {
                "header_title": "ความจำไม่ใช่กล้อง",
                "narration": "ทำไมเราถึงจำเรื่องเดียวกัน ไม่เหมือนกัน ทั้งที่อยู่ตรงนั้นด้วยกัน",
                "action": "think",
            },
            {
                "header_title": "สมองประกอบเรื่องใหม่",
                "narration": "ความจำไม่ใช่วิดีโอ ทุกครั้งที่นึกถึง สมองกำลังประกอบรายละเอียดขึ้นใหม่",
                "action": "discover",
            },
            {
                "header_title": "จำชัด ก็คลาดเคลื่อนได้",
                "narration": "เพราะฉะนั้น จำได้ชัด ไม่ได้แปลว่าถูกทุกอย่าง ลองฟังอีกมุม ก่อนตัดสิน",
                "action": "read",
            },
        ],
    },
}

TEMPLATES["mystery"] = local_outline("เรื่องลึกลับในลิฟต์ มีจดหมายเตือนก่อนประตูเปิด")
for template in TEMPLATES.values():
    template.setdefault("visual_style", "cinematic")
    template.setdefault("caption_position", "middle")


def valid_id(value):
    return bool(re.fullmatch(r"[a-f0-9]{32}", value))


def validate_project(data):
    if not isinstance(data, dict):
        raise ValueError("ข้อมูลเรื่องไม่ถูกต้อง")
    palette = data.get("palette", "pop")
    if palette not in ("pop", "warm", "mystery"):
        raise ValueError("เลือกโทนสีใหม่")
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 6:
        raise ValueError("เพิ่มฉากตั้งแต่ 1 ถึง 6 ฉาก")
    cleaned = []
    for scene in scenes:
        if not isinstance(scene, dict):
            raise ValueError("ข้อมูลฉากไม่ถูกต้อง")
        title = scene.get("header_title", "")
        narration = scene.get("narration", "")
        action = scene.get("action", "think")
        if not isinstance(title, str) or not title.strip() or len(title) > 60:
            raise ValueError("หัวข้อฉากต้องมี 1–60 ตัวอักษร")
        if (
            not isinstance(narration, str)
            or not narration.strip()
            or len(narration) > 400
        ):
            raise ValueError("บทแต่ละฉากต้องมี 1–400 ตัวอักษร")
        if not isinstance(action, str) or action not in ACTIONS:
            raise ValueError("ท่าทางตัวละครไม่ถูกต้อง")
        item = {
            "header_title": title.strip(),
            "narration": narration.strip(),
            "action": action,
        }
        for field, allowed in SCENE_CHOICES.items():
            value = scene.get(field, SCENE_DEFAULTS[field])
            if not isinstance(value, str) or value not in allowed:
                raise ValueError("รายละเอียดฉากไม่ถูกต้อง: " + field)
            item[field] = value
        cleaned.append(item)
    if sum(len(s["narration"]) for s in cleaned) > 1200:
        raise ValueError("บททั้งหมดต้องไม่เกิน 1,200 ตัวอักษร")
    project = {"scenes": cleaned, "palette": palette}
    for field, default, allowed in [
        ("visual_style", "classic", {"classic", "cinematic"}),
        ("caption_position", "bottom", {"middle", "bottom"}),
    ]:
        value = data.get(field, default)
        if not isinstance(value, str) or value not in allowed:
            raise ValueError("รูปแบบคลิปไม่ถูกต้อง")
        project[field] = value
    for field, default in [("lead_name", "นที"), ("friend_name", "มีนา")]:
        value = data.get(field, default)
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 20:
            raise ValueError("ชื่อตัวละครต้องมี 1–20 ตัวอักษร")
        project[field] = value.strip()
    upload = data.get("background_id")
    if upload:
        if not isinstance(upload, str) or not valid_id(upload):
            raise ValueError("ไฟล์พื้นหลังไม่ถูกต้อง")
        matches = list(UPLOADS.glob(upload + ".*"))
        if len(matches) != 1:
            raise ValueError("ไม่พบไฟล์พื้นหลัง กรุณาอัปโหลดใหม่")
        project["background_path"] = str(matches[0])
    return project


def run_job(job_id):
    global active
    directory = JOBS / job_id
    try:
        with (directory / "render.log").open("w") as log:
            result = subprocess.run(
                [sys.executable, str(ROOT / "studio_render.py"), str(directory)],
                cwd=ROOT,
                stdout=log,
                stderr=log,
                timeout=1800,
            )
        if result.returncode and not (directory / "status.json").exists():
            raise RuntimeError("worker failed")
    except Exception:
        (directory / "status.json").write_text(
            json.dumps(
                {
                    "status": "failed",
                    "progress": 0,
                    "message": "การสร้างคลิปหยุดลง กรุณาลองใหม่อีกครั้ง",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    finally:
        with lock:
            active = None


@studio.get("/api/studio/capabilities")
def capabilities():
    return jsonify(
        ai_available=writer_available(),
        scene_choices={k: sorted(v) for k, v in SCENE_CHOICES.items()},
        actions=sorted(ACTIONS),
    )


@studio.post("/api/studio/preview")
def scene_preview():
    data = request.get_json(silent=True)
    try:
        project = validate_project(data)
        index = data.get("scene_index", 0)
        if (
            not isinstance(index, int)
            or isinstance(index, bool)
            or not 0 <= index < len(project["scenes"])
        ):
            raise ValueError("เลือกฉากที่ต้องการดูใหม่")
        if project["visual_style"] != "cinematic":
            raise ValueError("ภาพตัวอย่างฉากใช้กับรูปแบบเรื่องเล่า 2D")
        from auto_knowledge_shorts import ensure_font
        from story_art import StoryStage
        from PIL import Image, ImageOps

        font = ensure_font(ROOT / "assets/fonts/Kanit-Bold.ttf")
        background = None
        if project.get("background_path"):
            from moviepy import VideoFileClip

            with VideoFileClip(project["background_path"], audio=False) as clip:
                background = ImageOps.fit(
                    Image.fromarray(clip.get_frame(min(1, clip.duration / 2))),
                    (1080, 1920),
                )
        image = StoryStage(font, project).frame(
            project["scenes"][index], 1, 5, background=background
        )
        output = BytesIO()
        image.convert("RGB").save(output, format="JPEG", quality=88)
        output.seek(0)
        return send_file(output, mimetype="image/jpeg")
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except (OSError, RuntimeError):
        return (
            jsonify(error="สร้างภาพตัวอย่างไม่ได้ กรุณาตรวจฟอนต์หรือไฟล์พื้นหลัง"),
            500,
        )


@studio.post("/api/studio/draft")
def create_draft():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="ใส่ไอเดียของเรื่องก่อน"), 400
    idea = data.get("idea", "")
    genre = data.get("genre", "mystery")
    ending = data.get("ending", "twist")
    writer = data.get("writer", "auto")
    if not isinstance(idea, str) or not 5 <= len(idea.strip()) <= 1000:
        return jsonify(error="ไอเดียต้องมี 5–1,000 ตัวอักษร"), 400
    if (
        not isinstance(genre, str)
        or genre not in ("mystery", "motivation", "knowledge")
        or not isinstance(ending, str)
        or ending not in ("twist", "warm", "open")
        or not isinstance(writer, str)
        or writer not in ("auto", "outline", "ai")
    ):
        return jsonify(error="ตัวเลือกร่างเรื่องไม่ถูกต้อง"), 400
    try:
        draft = draft_story(idea.strip(), genre, ending, writer)
        project = validate_project(draft)
        project.update(
            writer_mode=draft["writer_mode"],
            writer_notice=draft["writer_notice"],
            brief=idea.strip(),
        )
        return jsonify(project)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except RuntimeError as error:
        return jsonify(error=str(error)), 502


@studio.get("/api/studio/templates")
def templates():
    return jsonify(TEMPLATES)


@studio.get("/api/studio/recent")
def recent_jobs():
    items = []
    if JOBS.exists():
        for directory in sorted(
            (p for p in JOBS.iterdir() if p.is_dir() and valid_id(p.name)),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            try:
                status = json.loads((directory / "status.json").read_text())
                if status.get("status") != "done":
                    continue
                project = json.loads((directory / "project.json").read_text())
                items.append(
                    {
                        "id": directory.name,
                        "title": project["scenes"][0]["header_title"],
                    }
                )
            except (OSError, ValueError, KeyError, IndexError):
                continue
            if len(items) == 5:
                break
    return jsonify(items)


@studio.post("/api/studio/jobs")
def create_job():
    global active
    try:
        project = validate_project(request.get_json(silent=True))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    with lock:
        if active:
            return (
                jsonify(error="กำลังสร้างคลิปอยู่หนึ่งงาน รอให้เสร็จก่อนเริ่มงานใหม่"),
                409,
            )
        job_id = uuid.uuid4().hex
        directory = JOBS / job_id
        directory.mkdir(parents=True)
        (directory / "project.json").write_text(
            json.dumps(project, ensure_ascii=False), encoding="utf-8"
        )
        (directory / "status.json").write_text(
            json.dumps(
                {"status": "queued", "progress": 0, "message": "เตรียมสร้างคลิป"}
            ),
            encoding="utf-8",
        )
        active = job_id
        executor.submit(run_job, job_id)
    return jsonify(id=job_id), 202


@studio.get("/api/studio/jobs/<job_id>")
def job_status(job_id):
    if not valid_id(job_id):
        return jsonify(error="ไม่พบงานนี้"), 404
    path = JOBS / job_id / "status.json"
    if not path.exists():
        return jsonify(error="ไม่พบงานนี้"), 404
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["status"] not in ("done", "failed") and active != job_id:
        data = {
            "status": "failed",
            "progress": 0,
            "message": "เซิร์ฟเวอร์เริ่มใหม่ กรุณาสร้างคลิปอีกครั้ง",
        }
    if data["status"] == "done":
        data.update(
            video_url=f"/api/studio/jobs/{job_id}/video",
            timeline_url=f"/api/studio/jobs/{job_id}/timeline",
        )
    return jsonify(data)


@studio.get("/api/studio/jobs/<job_id>/<kind>")
def result_file(job_id, kind):
    if not valid_id(job_id) or kind not in ("video", "timeline", "project"):
        return jsonify(error="ไม่พบไฟล์"), 404
    directory = JOBS / job_id
    try:
        status = json.loads((directory / "status.json").read_text())
    except (FileNotFoundError, ValueError):
        return jsonify(error="ไม่พบไฟล์"), 404
    if status["status"] != "done":
        return jsonify(error="คลิปยังไม่พร้อม"), 409
    if kind == "project":
        project = json.loads((directory / "project.json").read_text())
        return jsonify({k: v for k, v in project.items() if k != "background_path"})
    file = directory / ("video.mp4" if kind == "video" else "timeline.json")
    return send_file(
        file,
        mimetype="video/mp4" if kind == "video" else "application/json",
        conditional=True,
        as_attachment=request.args.get("download") == "1",
        download_name="shorts-" + job_id[:8] + file.suffix,
    )


@studio.post("/api/studio/background")
def upload_background():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify(error="เลือกไฟล์วิดีโอหรือ GIF ก่อน"), 400
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".mp4", ".mov", ".webm", ".gif"):
        return jsonify(error="รองรับ MP4, MOV, WebM และ GIF"), 400
    UPLOADS.mkdir(parents=True, exist_ok=True)
    identity = uuid.uuid4().hex
    path = UPLOADS / (identity + suffix)
    file.save(path)
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height:format=duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
        info = json.loads(result.stdout)
        video = info["streams"][0]
        if (
            not 0 < float(info["format"]["duration"]) <= 300
            or video["width"] * video["height"] > 3840 * 2160
        ):
            raise ValueError()
    except (subprocess.SubprocessError, ValueError, KeyError, IndexError):
        path.unlink(missing_ok=True)
        return (
            jsonify(
                error="อ่านคลิปไม่ได้ ใช้คลิปความยาวไม่เกิน 5 นาที และขนาดไม่เกิน 4K"
            ),
            400,
        )
    return jsonify(id=identity, name=file.filename), 201
