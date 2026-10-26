# 🤖 CODEX & AI Agent Operational Manual

ไฟล์นี้สร้างขึ้นเพื่อให้ OpenAI Codex, Copilot หรือ AI Agent อ่านทำความเข้าใจเพื่อสร้างคอนเทนต์ตอนถัดไป (EP.2, EP.3, ...) ให้คงมาตรฐานและสไตล์เดิม 100%

---

## 📌 Role & Mission
คุณคือ Creative Director & AI Prompt Engineer สำหรับช่องคลิปสั้นอนิเมชั่น "ก้างปลา เปลี่ยนชีวิต" (TikTok / YouTube Shorts) 
เป้าหมายคือการสร้างเรื่องเล่าที่เข้าถึงง่าย (Relatable), ตลกร้ายแบบผู้ใหญ่ (Irony/Humor), และจบด้วยข้อคิดพัฒนาตัวเอง (Self-Improvement) ความยาวคลิปประมาณ 40-45 วินาที

---

## 🎨 Master Prompt Template (ห้ามเปลี่ยนโครงสร้างนี้)

เมื่อผู้ใช้สั่งให้คิด Prompt สำหรับแต่ละฉาก ต้องใช้ Template นี้เสมอ:

```text
Maintain the EXACT same character design, proportions, ink line art style, coloring technique, and aesthetic from the attached reference image. Generate in vertical 9:16 portrait format:
[SHOT TYPE: e.g. CLOSE-UP / WIDE SHOT / ACTION SHOT]
The same cute stick figure character with bright yellow round circle head and simple black stick limbs, [ACTION & EMOTION].
[ENVIRONMENT / BACKGROUND DETAILS - Dark navy blue theme with warm glowing lighting].
Bold crisp black ink outlines, identical comic cel-shading and colors to the reference image, authentic hand-drawn 2D animation style, NO text, NO numbers, NO floating icons.
```

---

## 📋 45-Second Narrative Formula
โครงสร้างบทพูดทุก EP ต้องดำเนินตาม 6 ขั้นตอนนี้:
1. **The Hook (0-8s):** เปิดด้วยพฤติกรรมสุดโต่งหรือความจริงตลกร้ายที่ทุกคนเป็น
2. **The Pain (8-15s):** ขยี้ผลลัพธ์พังๆ ของพฤติกรรมนั้น ให้คนดูสะดุ้ง
3. **The 3 Steps (15-37s):** วิธีแก้ปัญหา 3 ข้อ (ง่าย -> มีแอ็กชัน -> ปฏิบัติได้ทันที)
4. **The Twist (37-42s):** หักมุมสะกิดใจ ลึกซึ้ง ไม่โลกสวย
5. **The Open Loop CTA (42-45s):** สั่งให้เซฟคลิป และทิ้งปริศนาสำหรับ EP ถัดไป

---

## 🗂️ EP Roadmap
- [x] **EP.1:** ตื่นเช้าไม่ได้ ไม่ใช่เพราะขี้เกียจ (Waking Up Early)
- [ ] **EP.2:** ทำไมคนเราถึงชอบผัดวันประกันพรุ่ง ทั้งที่รู้ว่าพังชีวิต (Procrastination Loop)
- [ ] **EP.3:** ดักจับสมองติดโดพามีน (Dopamine Detox)
- [ ] **EP.4:** กฎ 1% ทุกวัน สู้ชีวิตแต่ชีวิตสู้กลับ (1% Better Every Day)

---

## Universal Knowledge Shorts Factory — แนวทางสำหรับ Agent

ภารกิจใหม่รองรับความรู้สารพัดแนว ไม่จำกัดตัวละครก้างปลา กฎภาพและ Master
Prompt ด้านบนยังใช้กับงานสร้างภาพก้างปลาเดิมเท่านั้น คลิปความรู้ใช้พื้นหลัง
Pixabay ตามบริบทของเนื้อหา พร้อมกราฟิกข้อความภาษาไทย

- ใช้ checkout ปัจจุบันในงานคลาวด์ ไม่สร้าง worktree เว้นแต่ผู้ใช้ร้องขอ
- ข้อมูลอยู่ใน `topics/*.json` เป็น array ของฉาก: `header_title`,
  `highlight_text`, `narration`, `search_keyword` ต้องเป็นสตริงที่ไม่ว่าง
- ตรวจข้อเท็จจริงและบริบท ระบุความไม่แน่นอน หลีกเลี่ยงคำกล่าวเกินหลักฐาน
- บทบรรยายเป็นภาษาไทย คีย์เวิร์ดค้นหาคลิปเป็นภาษาอังกฤษ
- CLI: `python auto_knowledge_shorts.py --topic space` (หรือ brain/history)
- ติดตั้ง `requirements.txt` ใน venv แยกจากสคริปต์ MoviePy 1 เดิม
- ใช้ `PIXABAY_API_KEY` จาก environment เท่านั้น ห้ามบันทึกคีย์ในไฟล์หรือ log
- เสียง Edge TTS: `th-TH-NiwatNeural`; ไม่ต้องใช้ Gemini/API Key สำหรับเสียง
- Kanit Bold ดาวน์โหลดด้วย HTTPS เมื่อยังไม่มี; Pillow ต้องรองรับ RAQM
- ผลลัพธ์ต้อง 1080×1920 ที่ 30 fps เสียงกำหนดความยาวฉาก ครอปกึ่งกลาง
  และวนคลิปพื้นหลังเมื่อจำเป็น ซับปัจจุบันประมาณเวลาตามความยาวข้อความ
- ผลลัพธ์อยู่ `outputs/` พร้อมเครดิต Pixabay; ไฟล์กลางถูกลบอัตโนมัติ
- ตรวจวิดีโอจริงด้วย ffprobe: ขนาด, fps, เสียง และระยะเวลา ไม่ถือว่าการ
  import ผ่านเพียงอย่างเดียวคือการผลิตวิดีโอสำเร็จ
- หากไม่มีคีย์หรือบริการออนไลน์ใช้ไม่ได้ ให้ทดสอบ pipeline ด้วยสื่อจำลอง
  และรายงานแยกจากการเรียก Pixabay/Edge TTS จริง ห้ามอ้างว่าทดสอบออนไลน์แล้ว


### พื้นหลังเมื่อไม่มีคีย์ Pixabay

หากไม่ตั้ง `PIXABAY_API_KEY` ระบบสุ่มคลิปจาก `assets/backgrounds/`
ถ้าโฟลเดอร์ว่างจะดาวน์โหลดตัวอย่าง Big Buck Bunny (CC BY 3.0) อัตโนมัติ
ดูเครดิตและเงื่อนไขใน `assets/backgrounds/README.md` พื้นหลังตัวอย่างไม่ได้
ตรงกับเนื้อหาหัวข้อ เลือกโฟลเดอร์อื่นได้ด้วย `--backgrounds /path/to/clips`
เมื่อใช้ Pixabay ระบบค้นหาตาม `search_keyword`; คีย์ผิดหรือการค้นหาล้มเหลว
จะรายงานข้อผิดพลาดแทนการเปลี่ยนไปใช้คลิปอื่นเงียบ ๆ
เสียงแต่ละฉากเป็น Edge TTS จริง ตามด้วยช่วงเงียบ 0.3 วินาที
ต้องอนุญาต `speech.platform.bing.com` ผ่าน HTTPS/WebSocket จึงจะสร้างเสียงได้
การบันทึกเครือข่ายในฉบับร่างยังไม่ทำให้เครื่องที่กำลังรันเข้าถึงบริการได้ทันที


## Shorts Studio บนหน้าเว็บ

- หน้า `/` เป็น studio ใหม่; เครื่องมือ Gemini เดิมอยู่ `/gemini`
- รัน `python web/app.py` หลังติดตั้ง `web/requirements.txt` ซึ่งรวม root requirements
- ผู้ใช้แก้บท/แอ็กชัน/โทนสีบนเว็บ ไม่ต้องแก้ไฟล์ JSON เพื่อเปลี่ยนเรื่อง
- `web/studio.py` ตรวจข้อมูลและรัน subprocess `studio_render.py` ทีละงาน
- สร้างเสียงด้วย Edge TTS WordBoundary จริง เก็บเวลาแต่ละคำใน timeline.json
- ห้ามแทนซับที่ตรงเสียงด้วยการหารเวลาตามจำนวนตัวอักษรใน studio renderer
- ตัวละครเคลื่อนไหวพร้อมพร็อพตามแอ็กชัน กล่องข้อความเด้ง และไฮไลต์ตามคำ
- ตัวอย่างภาพ CSS บนเว็บต้องติดป้ายว่ายังไม่ใช่วิดีโอที่เรนเดอร์
- แม่แบบเรื่องเขียนไว้ล่วงหน้า ห้ามอ้างว่า AI แต่งเรื่องตามหัวข้ออิสระ
- อัปโหลด GIF/วิดีโอสูงสุด 80 MB / 5 นาที ตรวจด้วย ffprobe ก่อนใช้
- ไฟล์งานเก็บ outputs/studio/; ห้ามให้ client กำหนด filesystem path หรือคำสั่ง shell
- ทดสอบ API, browser flow, การดาวน์โหลด MP4 และ metadata/word timings ของไฟล์จริง
- เป็นเว็บพัฒนาแบบผู้ใช้เดียว ยังไม่มีระบบสมาชิกหรือการเผยแพร่เว็บไซต์สาธารณะ

## Cinematic 2D storyboards

- มี `visual_style=cinematic` และ `classic`; รองรับงานเดิมด้วยค่า default classic
- `story_schema.py` เป็นแหล่ง enum เดียวสำหรับ setting/camera/cast/prop/graphic/expression
- `story_art.py` วาดฉากและตัวละครมนุษย์ที่คงรูปลักษณ์ข้ามช็อต พร้อม camera push-in
- `story_planner.py` มี outline แบบไม่ใช้คีย์และ Gemini writer แบบ optional
- ห้ามเรียก outline ว่า AI หรืออ้างว่ารองรับทุกไอเดีย; แจ้งข้อจำกัดที่หน้าเว็บ
- AI ใช้ STORY_API_KEY จาก server environment เท่านั้น ตรวจ schema และทิ้ง
  filesystem paths/ตัวเลือกที่ไม่รู้จักก่อนเรียก renderer ห้าม log คีย์หรือ URL ที่มีคีย์
- งานที่ไม่มีคีย์ยังร่างและเรนเดอร์ได้; การแต่งเรื่องอิสระผ่านโมเดลต้องทดสอบแยก
- ตรวจฉากหลายคน พร็อพ กราฟิก ซับตรงเสียง และมุมกล้องใน MP4 จริง ไม่ใช่แค่ภาพนิ่ง
