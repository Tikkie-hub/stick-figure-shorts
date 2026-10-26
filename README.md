# 🐟 Stick Figure Shorts Studio (ก้างปลา เปลี่ยนชีวิต)

ระบบผลิตคอนเทนต์คลิปสั้นอนิเมชั่นก้างปลาไวรัล (TikTok / YouTube Shorts / Reels) ความยาว ~45 วินาที พร้อมคลัง Prompt และเครื่องมือช่วยสร้างภาพด้วย Gemini AI

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```
stick-figure-shorts/
├── CODEX.md                # 🤖 คู่มือคำสั่งและ System Prompt สำหรับ Codex / AI
├── README.md               # 📖 เอกสารภาพรวมโปรเจกต์
├── scripts/                # 📝 สคริปต์บทพูดและคำพากย์แยกตาม EP
│   └── ep1_waking_up.md    # EP.1 "ตื่นเช้าไม่ได้ ไม่ใช่เพราะขี้เกียจ"
├── prompts/                # 🎨 คลัง Prompt แต่ละฉากพร้อมการล็อกสไตล์
│   └── ep1_prompts.md      # ชุด Prompt ทุกช็อตของ EP.1
├── assets/                 # 🖼️ ไฟล์รูปภาพที่สร้างแล้ว
│   └── ep1/                # ช็อตทั้งหมดของ EP.1 ขนาด 9:16
└── web/                    # 🌐 เว็บแอป Gemini Studio (Flask + Gemini API)
    ├── app.py
    ├── requirements.txt
    ├── templates/
    └── start.bat
```

---

## 🎯 กฎเหล็กของตัวละครและสไตล์ภาพ (Character Bible)

1. **ตัวละคร (Character):**
   - ตัวการ์ตูนก้างปลา 2D (Stick Figure) สไตล์ Doodle มินิมอล
   - หัวกลมสีเหลืองสดใส (Solid Bright Yellow Head)
   - แขนขาเป็นเส้นก้างปลาสีดำธรรมดา (Simple Black Stick Limbs)
   - เส้นขอบหมึกดำหนา คมชัด (Bold Crisp Black Ink Outlines)
2. **โทนสีและแสงเงา (Color Palette & Lighting):**
   - ห้องนอน/ฉากโทนสีน้ำเงินเข้มยามค่ำคืน (Dark Navy Blue Atmosphere)
   - ตัดกับแสงไฟโคมไฟข้างเตียงสีส้มอุ่น (Warm Bedside Lamp Glow)
   - สไตล์การลงสีแบบ Graphic Novel / Comic Cel-Shading
3. **สัดส่วนภาพ (Aspect Ratio):**
   - แนวตั้ง **9:16** สำหรับ TikTok โดยเฉพาะ
4. **ข้อห้ามเด็ดขาด (Negative Constraints):**
   - ห้ามมีตัวหนังสือหรือตัวเลขลอย (NO text, NO artificial floating numbers)
   - ห้ามมีไอคอน AI แปลกปลอม (ให้ใช้วัตถุจริงหรือท่าทางตัวการ์ตูนแทน)

---

## 🚀 วิธีเปิดใช้งาน Gemini Studio Web App

```bash
cd web
pip install -r requirements.txt
python app.py
```
หรือดับเบิลคลิกไฟล์ `web/start.bat` แล้วเปิดเบราว์เซอร์ไปที่: `http://localhost:5000`

---

## 🎬 สูตรการตัดต่อ 45 วินาที (CapCut / Premiere Pro)

- **0:00 - 0:08 (Hook):** เปิดตัวปัญหา + ตั้งนาฬิกาปลุกหลายเรือน
- **0:08 - 0:15 (Pain Point):** เลื่อนปลุก (Snooze) 5 นาทีกลายเป็น 2 ชั่วโมง
- **0:15 - 0:22 (Method 1):** วางมือถือไว้อีกห้อง ลุกเดินไปปิด = ตื่นอัตโนมัติ
- **0:22 - 0:30 (Method 2):** กฎ 5 วินาที นับ 5-4-3-2-1 ดีดตัวลุกทันที
- **0:30 - 0:37 (Method 3):** ตั้งเป้าหมายเล็กที่สุด ดื่มน้ำ 1 แก้ว
- **0:37 - 0:42 (Twist):** หยุดคิดทวิสต์ "ถ้าไม่มีเป้าหมายในชีวิต วิธีไหนก็ไม่ช่วย"
- **0:42 - 0:45 (CTA):** ชวนกดเซฟและกดติดตามรอ EP.2
