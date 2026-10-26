import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import auto_knowledge_shorts as factory


class FactoryTests(unittest.TestCase):
    def test_no_key_downloads_and_reuses_local_background(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            clips = work / 'backgrounds'

            def download(url, path):
                self.assertEqual(url, factory.SAMPLE_URL)
                path.write_bytes(b'sample-video')

            with patch.object(factory, 'download', side_effect=download) as fetch:
                credit = factory.background_video('brain', '', work / 'first.mp4', clips)
                factory.background_video('brain', '', work / 'second.mp4', clips)
                self.assertEqual(fetch.call_count, 1)
            self.assertEqual((work / 'second.mp4').read_bytes(), b'sample-video')
            self.assertEqual(credit['provider'], 'local')
            self.assertEqual(credit['license'], 'CC BY 3.0')

    def test_pixabay_selection_and_key_redaction(self):
        hit = {'id': 12, 'user': 'artist', 'pageURL': 'https://pixabay.com/videos/id-12/',
               'videos': {'medium': {'width': 1920, 'height': 1080, 'url': 'https://cdn.pixabay.com/test.mp4'}}}
        with patch.object(factory.requests, 'get') as get, patch.object(factory, 'download') as download:
            response = get.return_value.__enter__.return_value
            response.status_code = 200
            response.json.return_value = {'hits': [hit]}
            credit = factory.background_video('brain', 'private-test-key', Path('/tmp/test-video.mp4'))
            self.assertEqual(credit['video_id'], 12)
            self.assertEqual(get.call_args.kwargs['params']['q'], 'brain')
            download.assert_called_once_with('https://cdn.pixabay.com/test.mp4', Path('/tmp/test-video.mp4'))
            response.status_code = 403
            with self.assertRaises(RuntimeError) as error:
                factory.background_video('brain', 'private-test-key', Path('/tmp/test-video.mp4'))
            self.assertNotIn('private-test-key', str(error.exception))

    def test_topics_and_validation(self):
        for topic in ('space', 'brain', 'history'):
            self.assertEqual(len(factory.load_topic(factory.ROOT / 'topics' / f'{topic}.json')), 3)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            path.write_text('[{"narration": "only one field"}]')
            with self.assertRaises(ValueError):
                factory.load_topic(path)

    def test_real_render_with_local_media(self):
        font = Path('/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf')
        if not font.exists() or not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            self.skipTest('Local Thai font, ffmpeg and ffprobe required')
        factory.ensure_font(font)
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            # A landscape source shorter than the audio exercises both crop and loop.
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'color=c=navy:s=640x360:r=30', '-t', '0.1', '-c:v',
                            'libx264', str(work / 'source.mp4')], check=True)
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'sine=frequency=440:duration=0.3', str(work / 'speech.mp3')], check=True)

            async def speech(text, path):
                shutil.copyfile(work / 'speech.mp3', path)

            def video(keyword, key, path, backgrounds=None):
                shutil.copyfile(work / 'source.mp4', path)
                return {'keyword': keyword, 'video_id': 1}

            scenes = factory.load_topic(factory.ROOT / 'topics' / 'space.json')[:2]
            with patch.object(factory, 'speech', speech), patch.object(factory, 'background_video', video):
                factory.render(scenes, font, work / 'result.mp4', 'test-only', work)
            metadata = json.loads(subprocess.check_output([
                'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(work / 'result.mp4')]))
            stream = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
            self.assertEqual((stream['width'], stream['height'], stream['r_frame_rate']), (1080, 1920, '30/1'))
            self.assertTrue(any(s['codec_type'] == 'audio' for s in metadata['streams']))
            self.assertAlmostEqual(float(metadata['format']['duration']), 1.2, delta=0.15)
            credits = json.loads((work / 'result.credits.json').read_text())
            self.assertEqual(len(credits), 2)
            for credit in credits:
                self.assertAlmostEqual(credit['scene_seconds'] - credit['narration_seconds'], 0.3)


if __name__ == '__main__':
    unittest.main()
