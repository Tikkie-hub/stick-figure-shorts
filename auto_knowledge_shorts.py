"""Render Thai knowledge shorts. Requires FFmpeg, Pixabay or local backgrounds, and Edge TTS access."""
import argparse
import asyncio
import json
import math
import os
import random
import shutil
from pathlib import Path
import tempfile
import unicodedata

# Initialize system trust before networking libraries create cached SSL contexts.
if __name__ == '__main__':
    import truststore
    truststore.inject_into_ssl()

import edge_tts
import aiohttp
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont, features
from moviepy import CompositeAudioClip, AudioFileClip, VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, vfx

ROOT = Path(__file__).resolve().parent
SIZE = (1080, 1920)
FONT_URL = 'https://raw.githubusercontent.com/google/fonts/main/ofl/kanit/Kanit-Bold.ttf'


def download(url, destination, headers=None):
    """Verified HTTPS, bounded timeouts and atomic writes; never log auth headers."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + '.part')
    try:
        with requests.get(url, headers=headers, stream=True, timeout=(15, 120)) as response:
            response.raise_for_status()
            with temporary.open('wb') as output:
                for chunk in response.iter_content(1024 * 1024):
                    output.write(chunk)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_font(path):
    path = Path(path)
    if not path.exists():
        download(FONT_URL, path)
    # Validate existing and newly downloaded fonts before rendering.
    ImageFont.truetype(str(path), 40)
    if not features.check_feature('raqm'):
        raise RuntimeError('Pillow needs libraqm for correctly shaped Thai text. Install a Pillow wheel with RAQM support.')
    return path


def load_topic(path):
    scenes = json.loads(Path(path).read_text(encoding='utf-8'))
    keys = ('header_title', 'highlight_text', 'narration', 'search_keyword')
    if not isinstance(scenes, list) or not scenes:
        raise ValueError('Topic must be a nonempty JSON array of scenes')
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict) or any(not isinstance(scene.get(k), str) or not scene[k].strip() for k in keys):
            raise ValueError(f'Scene {index} requires nonempty strings: {keys}')
    return scenes


SAMPLE_URL = 'https://raw.githubusercontent.com/mediaelement/mediaelement-files/master/big_buck_bunny.mp4'


def background_video(keyword, api_key, destination, backgrounds=None):
    """Use Pixabay with a key; otherwise select a local clip (bootstrap a CC sample)."""
    if not api_key:
        directory = Path(backgrounds or ROOT / 'assets/backgrounds')
        directory.mkdir(parents=True, exist_ok=True)
        files = [p for p in sorted(directory.iterdir()) if p.suffix.lower() in ('.mp4', '.mov', '.webm') and p.is_file()]
        if not files:
            sample = directory / 'big_buck_bunny.mp4'
            download(SAMPLE_URL, sample)
            files = [sample]
        selected = random.choice(files)
        shutil.copyfile(selected, destination)
        credit = {'provider': 'local', 'keyword': keyword, 'file': selected.name,
                  'note': 'Generic fallback background; not matched to topic'}
        if selected.name == 'big_buck_bunny.mp4':
            credit.update(source=SAMPLE_URL, creator='Blender Foundation',
                          license='CC BY 3.0', license_url='https://creativecommons.org/licenses/by/3.0/')
        return credit
    # API key is a query parameter: never print response URLs or HTTP exceptions.
    try:
        with requests.get('https://pixabay.com/api/videos/',
                          params={'key': api_key, 'q': keyword, 'per_page': 10,
                                  'safesearch': 'true', 'video_type': 'film'},
                          timeout=(15, 45)) as response:
            if response.status_code != 200:
                raise RuntimeError(f'Pixabay API HTTP {response.status_code}; check key, quota and network settings')
            hits = response.json().get('hits', [])
    except requests.RequestException:
        raise RuntimeError('Pixabay API connection failed; check network settings') from None
    candidates = [(hit, file) for hit in hits for file in hit.get('videos', {}).values()
                  if file.get('width') and file.get('height') and file.get('url', '').startswith('https://')]
    if not candidates:
        raise RuntimeError(f'No usable Pixabay video for keyword: {keyword}')
    def rank(item):
        file = item[1]
        return (file['width'] < 1080 or file['height'] < 1920,
                abs(file['width'] / file['height'] - 9 / 16), file['width'] * file['height'])
    hit, file = min(candidates, key=rank)
    download(file['url'], destination)
    return {'provider': 'pixabay', 'keyword': keyword, 'video_id': hit['id'],
            'url': hit.get('pageURL'), 'creator': hit.get('user')}


def clusters(text):
    """Keep Thai combining marks attached when wrapping text without spaces."""
    result = []
    for char in text:
        if result and (unicodedata.category(char).startswith('M') or char == '\u0e33'):
            result[-1] += char
        else:
            result.append(char)
    return result


def wrap(text, font, width):
    draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for cluster in clusters(paragraph):
            if line and draw.textlength(line + cluster, font=font) > width:
                lines.append(line.strip())
                line = ''
            line += cluster
        lines.append(line.strip())
    return lines


def text_card(canvas, text, font_path, box, max_size, min_size=20):
    left, top, right, bottom = box
    for size in range(max_size, min_size - 1, -2):
        font = ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        lines = wrap(text, font, right - left - 64)
        line_height = sum(font.getmetrics()) + 10
        if len(lines) * line_height <= bottom - top - 48:
            break
    else:
        raise ValueError('Text is too long for its card; shorten the scene text')
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(box, radius=28, fill=(8, 16, 35, 220))
    y = top + (bottom - top - len(lines) * line_height) / 2
    for line in lines:
        # Ascender anchoring and font metrics leave room for Thai vowels and tone marks.
        draw.text(((left + right) / 2, y), line, font=font, anchor='mt', fill='white', stroke_width=1)
        y += line_height


def overlay(scene, font):
    image = Image.new('RGBA', SIZE)
    text_card(image, scene['header_title'], font, (60, 120, 1020, 360), 64)
    text_card(image, scene['highlight_text'], font, (80, 740, 1000, 1180), 76)
    return np.array(image)


def subtitle_segments(text, font):
    face = ImageFont.truetype(str(font), 48, layout_engine=ImageFont.Layout.RAQM)
    lines = wrap(text, face, 880)
    return ['\n'.join(lines[i:i + 2]) for i in range(0, len(lines), 2)]


async def speech(text, path):
    proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    try:
        await asyncio.wait_for(
            edge_tts.Communicate(text, voice='th-TH-NiwatNeural', proxy=proxy).save(str(path)),
            timeout=180,
        )
    except aiohttp.ClientResponseError as error:
        raise RuntimeError(f'Edge TTS HTTP {error.status}; allow HTTPS/WebSocket access to speech.platform.bing.com') from None
    except (aiohttp.ClientError, edge_tts.exceptions.EdgeTTSException, TimeoutError):
        raise RuntimeError('Edge TTS failed; check connectivity, system CA trust, and the installed edge-tts version') from None


def render(scenes, font, output, api_key, work, backgrounds=None):
    resources, composed, credits = [], [], []
    try:
        for index, scene in enumerate(scenes):
            print(f'Scene {index + 1}/{len(scenes)}: speech and background', flush=True)
            audio_path, video_path = work / f'{index}.mp3', work / f'{index}.mp4'
            asyncio.run(speech(scene['narration'], audio_path))
            credit = background_video(scene['search_keyword'], api_key, video_path, backgrounds)
            credits.append(credit)
            audio = AudioFileClip(str(audio_path))
            resources.append(audio)
            source = VideoFileClip(str(video_path), audio=False)
            resources.append(source)
            if source.duration <= 0 or audio.duration <= 0:
                raise ValueError('Media has no duration')
            duration = audio.duration + 0.3
            credit.update(narration_seconds=audio.duration, scene_seconds=duration)
            scale = max(SIZE[0] / source.w, SIZE[1] / source.h)
            background = source.resized((math.ceil(source.w * scale), math.ceil(source.h * scale)))
            background = background.cropped(x_center=background.w / 2, y_center=background.h / 2, width=1080, height=1920)
            background = background.with_effects([vfx.Loop(duration=duration)])
            layers = [background, ImageClip(overlay(scene, font)).with_duration(duration)]
            segments = subtitle_segments(scene['narration'], font)
            # Display short subtitle cards across the narration; timings are proportional,
            # not speech-aligned word timestamps.
            weights = [len(s.replace('\n', '')) for s in segments]
            elapsed = 0.0
            for segment, weight in zip(segments, weights):
                length = audio.duration * weight / sum(weights)
                image = Image.new('RGBA', SIZE)
                text_card(image, segment, font, (60, 1440, 1020, 1780), 48)
                layers.append(ImageClip(np.array(image)).with_start(elapsed).with_duration(length))
                elapsed += length
            padded_audio = CompositeAudioClip([audio]).with_duration(duration)
            resources.append(padded_audio)
            clip = CompositeVideoClip(layers, size=SIZE).with_duration(duration).with_audio(padded_audio)
            resources.extend(layers)
            resources.append(clip)
            composed.append(clip)
        final = concatenate_videoclips(composed, method='chain')
        resources.append(final)
        final.write_videofile(str(output), fps=30, codec='libx264', audio_codec='aac',
                              preset='medium', threads=2, temp_audiofile=str(work / 'sound.m4a'), logger='bar')
        output.with_suffix('.credits.json').write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding='utf-8')
    finally:
        for resource in reversed(resources):
            resource.close()


def main():
    parser = argparse.ArgumentParser(description='Universal Knowledge Shorts Factory — Thai 1080x1920')
    parser.add_argument('--topic', required=True, help='Topic name in topics/, e.g. space')
    parser.add_argument('--output', type=Path, help='Output MP4 path')
    parser.add_argument('--backgrounds', type=Path, default=ROOT / 'assets/backgrounds', help='Fallback clip directory when PIXABAY_API_KEY is unset')
    parser.add_argument('--font', type=Path, default=ROOT / 'assets/fonts/Kanit-Bold.ttf')
    args = parser.parse_args()
    if Path(args.topic).name != args.topic or args.topic in ('.', '..'):
        parser.error('--topic must be a topic name, not a path')
    try:
        scenes = load_topic(ROOT / 'topics' / f'{args.topic}.json')
        api_key = os.environ.get('PIXABAY_API_KEY', '').strip()
        font = ensure_font(args.font)
        output = (args.output or ROOT / 'outputs' / f'{args.topic}.mp4').resolve()
        if output.suffix.lower() != '.mp4':
            parser.error('--output must end with .mp4')
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='knowledge-shorts-') as temporary:
            render(scenes, font, output, api_key, Path(temporary), args.backgrounds)
    except (OSError, ValueError, RuntimeError, requests.RequestException, aiohttp.ClientError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
