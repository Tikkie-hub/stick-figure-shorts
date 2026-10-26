from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import urllib.request
import json
import ssl
import base64
import os

app = Flask(__name__)
CORS(app, resources={r"/api/chat": {"origins": "*"}, r"/api/generate-image": {"origins": "*"}})
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024
from studio import studio
app.register_blueprint(studio)

@app.errorhandler(413)
def too_large(error):
    return jsonify(error="ไฟล์ใหญ่เกิน 80 MB กรุณาเลือกไฟล์ที่เล็กลง"), 413

# Verify HTTPS using the configured trust roots
def get_ssl_context():
    ctx = ssl.create_default_context()
    return ctx

@app.route('/')
def index():
    return render_template('studio.html')

@app.get('/download-project')
def download_project():
    from package_project import project_zip
    return send_file(project_zip(), mimetype='application/zip', as_attachment=True, download_name='ShortsStudio.zip')

@app.get('/studio-font')
def studio_font():
    from pathlib import Path
    font = Path(__file__).resolve().parents[1] / 'assets/fonts/Kanit-Bold.ttf'
    if not font.exists():
        return '', 404
    return send_file(font, mimetype='font/ttf')

@app.route('/gemini')
def gemini_legacy():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    api_key = data.get('api_key', '').strip()
    message  = data.get('message', '')
    history  = data.get('history', [])

    if not api_key:
        return jsonify({'error': 'กรุณาใส่ Gemini API Key ในการตั้งค่า ⚙️'}), 400

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
        
        system_prompt = (
            "คุณเป็น AI ผู้ช่วยสร้างคอนเทนต์ TikTok ภาษาไทย\n"
            "ช่วยเขียนบทคลิปสั้น, แนะนำ Prompt สไตล์การ์ตูนก้างปลา (Stick figure)\n"
            "และคอยแปลงข้อความภาษาไทยของผู้ใช้ให้เป็น Prompt ภาษาอังกฤษสไตล์ก้างปลา 9:16 ที่สวยงาม"
        )
        
        contents = []
        for msg in history[-10:]:
            role = 'user' if msg['role'] == 'user' else 'model'
            contents.append({'role': role, 'parts': [{'text': msg['content']}]})
            
        contents.append({'role': 'user', 'parts': [{'text': message}]})

        payload = {
            'system_instruction': {'parts': [{'text': system_prompt}]},
            'contents': contents
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, context=get_ssl_context()) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            candidates = res_data.get('candidates', [])
            if candidates:
                text = candidates[0]['content']['parts'][0]['text']
                return jsonify({'response': text})
            return jsonify({'error': 'ไม่มีข้อความตอบกลับจาก AI'}), 500

    except Exception as e:
        return jsonify({'error': f'Chat Error: {str(e)}'}), 500


@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    data         = request.json
    api_key      = data.get('api_key', '').strip()
    prompt       = data.get('prompt', '')
    aspect_ratio = data.get('aspect_ratio', '9:16')

    if not api_key:
        return jsonify({'error': 'กรุณาใส่ Gemini API Key ในการตั้งค่า ⚙️'}), 400
    if not prompt:
        return jsonify({'error': 'กรุณาใส่ Prompt'}), 400

    # Ensure 9:16 and stick figure styling keyword
    full_prompt = prompt
    if 'stick figure' not in prompt.lower():
        full_prompt = f"2D stick figure character, yellow round head, {prompt}, vertical 9:16 portrait format, clean line art, no text"

    # Models to attempt
    models = [
        'gemini-2.5-flash-image',
        'gemini-3.1-flash-image-preview',
        'gemini-3.1-flash-image',
        'gemini-3-pro-image-preview'
    ]

    last_error = ''

    for model_name in models:
        try:
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}'
            payload = {
                'contents': [{
                    'parts': [{'text': full_prompt}]
                }]
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, context=get_ssl_context()) as response:
                result = json.loads(response.read().decode('utf-8'))
                candidates = result.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    for p in parts:
                        if 'inlineData' in p:
                            return jsonify({
                                'image': p['inlineData']['data'],
                                'mime_type': p['inlineData'].get('mimeType', 'image/png'),
                                'model_used': model_name
                            })
        except Exception as e:
            last_error = str(e)
            continue

    # Friendly error translation
    if '429' in last_error or 'Too Many Requests' in last_error:
        return jsonify({'error': '⏳ โควต้าสร้างภาพของ API Key นี้ติดจำกัดชั่วคราว (Rate limit/Quota exhausted) กรุณารอสักครู่'}), 429

    return jsonify({'error': f'ไม่สามารถสร้างภาพได้: {last_error}'}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("Shorts Studio — Animated Story Factory")
    print("=" * 50)
    app.run(debug=False, port=5000, host='0.0.0.0')
