import os
import asyncio
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# ==============================================================================
# 1. กำหนดเสียงพากย์ และฉากทั้งหมด
# ==============================================================================
# - "th-TH-NiwatNeural"    : เสียงผู้ชาย (ชัดเจน เป็นธรรมชาติ สไตล์เล่าเรื่อง)
# - "th-TH-PremwadeeNeural" : เสียงผู้หญิง (สดใส คลีน น่าฟัง)
VOICE_NAME = "th-TH-NiwatNeural"

SCENES_DATA = [
    {
        "image": "assets/ep1/scene1_color_1792868833768.jpg",
        "text": "ก้างปลาตัวนี้ ตั้งนาฬิกาปลุกยี่สิบครั้งทุกคืน แต่ก็ยังไม่เคยตื่นตรงเวลาสักที"
    },
    {
        "image": "assets/ep1/scene2_color_1792868852284.jpg",
        "text": "เพราะสมองมันชอบหลอกเราว่า อีกแค่ห้านาทีก็ทัน แล้วสุดท้าย ห้านาทีก็กลายเป็นสองชั่วโมง"
    },
    {
        "image": "assets/ep1/scene3_color_1792868868879.jpg",
        "text": "วิธีแก้ที่ง่ายที่สุดคือ เอามือถือไปวางไว้อีกห้อง พอต้องลุกเดินไปปิด ตัวเราก็จะตื่นอัตโนมัติ"
    }
]

OUTPUT_VIDEO_PATH = "final_video.mp4"

async def generate_speech(text: str, output_audio_path: str):
    communicate = edge_tts.Communicate(text=text, voice=VOICE_NAME, rate="+0%", pitch="+0Hz")
    await communicate.save(output_audio_path)

async def main():
    print("=" * 60)
    print("🎬 เริ่มต้นกระบวนการสร้างวิดีโอเล่าเรื่องอัตโนมัติ...")
    print("=" * 60)

    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    temp_audio_files = []
    video_clips = []

    try:
        for idx, scene in enumerate(SCENES_DATA, start=1):
            image_path = scene["image"]
            text       = scene["text"]
            audio_path = os.path.join(temp_dir, f"audio_scene_{idx}.mp3")

            if not os.path.exists(image_path):
                print(f"⚠️ [ข้าม] ไม่พบไฟล์ภาพ: {image_path}")
                continue

            print(f"\n[ฉากที่ {idx}] กำลังสร้างเสียงพากย์: {text[:30]}...")
            await generate_speech(text, audio_path)
            temp_audio_files.append(audio_path)

            audio_clip = AudioFileClip(audio_path)
            scene_duration = audio_clip.duration + 0.3

            img_clip = ImageClip(image_path).set_duration(scene_duration)
            img_clip = img_clip.set_audio(audio_clip)
            video_clips.append(img_clip)
            print(f"✅ ความยาวฉาก: {scene_duration:.2f} วินาที")

        if not video_clips:
            print("❌ ไม่พบภาพที่จะสร้างวิดีโอ")
            return

        print("\n🔗 กำลังรวมภาพและเสียงทุกฉากเข้าด้วยกัน...")
        final_video = concatenate_videoclips(video_clips, method="compose")

        print(f"💾 กำลัง Export วิดีโอไปที่: {OUTPUT_VIDEO_PATH}")
        final_video.write_videofile(
            OUTPUT_VIDEO_PATH,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp_audio/temp_final.m4a",
            remove_temp=True
        )
        print(f"\n🎉 สำเร็จแล้ว: {OUTPUT_VIDEO_PATH}")

    finally:
        for clip in video_clips: clip.close()
        for f in temp_audio_files:
            if os.path.exists(f): os.remove(f)
        if os.path.exists(temp_dir): os.rmdir(temp_dir)

if __name__ == "__main__":
    asyncio.run(main())
