"""Safe, stage-aware errors; never expose credential-bearing network URLs."""

import re


def describe_error(error, stage):
    kind = type(error).__name__
    message = str(error)
    if "libraqm" in message or "uharfbuzz" in message or "freetype" in message.lower():
        code = "THAI_FONT_SETUP"
        public = "ระบบจัดรูปอักษรไทยยังไม่พร้อม ปิดเว็บแล้วเปิด start.bat รุ่นล่าสุดเพื่อติดตั้งไลบรารีฟอนต์"
    elif "ไม่ได้ส่งเสียงหรือเวลาของคำ" in message:
        code = "TTS_TIMING_MISSING"
        public = (
            "บริการ Edge TTS ไม่ส่งเวลาคำกลับมา กรุณาลองใหม่ หรือลองบทสั้นหนึ่งฉากก่อน"
        )
    elif stage == "font":
        code = "FONT_LOAD_FAILED"
        public = "เตรียมฟอนต์ไทยไม่สำเร็จ ตรวจอินเทอร์เน็ตสำหรับดาวน์โหลด Kanit หรือไฟล์ assets/fonts/Kanit-Bold.ttf"
    elif stage == "speech":
        code = "TTS_FAILED"
        public = "สร้างเสียง Edge TTS ไม่สำเร็จ ตรวจการเชื่อมต่อ speech.platform.bing.com แล้วลองใหม่"
    elif stage == "background":
        code = "BACKGROUND_FAILED"
        public = "อ่านคลิปพื้นหลังไม่ได้ ลองเลือกฉากและตัวละครของเรื่อง หรือเปลี่ยนไฟล์วิดีโอ"
    else:
        code = "RENDER_FAILED"
        public = "เรนเดอร์วิดีโอไม่สำเร็จ ดูรายละเอียดใน render.log และส่งรหัสข้อผิดพลาดให้ผู้ดูแล"
    # Record code frames, not exception URLs, credentials or process environment.
    frames = []
    trace = error.__traceback__
    while trace:
        frames.append(
            {
                "file": trace.tb_frame.f_code.co_filename.replace("\\", "/").split("/")[
                    -1
                ],
                "line": trace.tb_lineno,
                "function": trace.tb_frame.f_code.co_name,
            }
        )
        trace = trace.tb_next
    safe_detail = (
        message[:500]
        if kind == "RuntimeError"
        and not re.search(r"https?://|wss?://|key=|token=|password=", message, re.I)
        else ""
    )
    return {
        "status": "failed",
        "progress": 0,
        "message": f"{public} [{code}]",
        "error_code": code,
        "stage": stage,
        "error_type": kind,
        "detail": safe_detail,
        "frames": frames,
    }
