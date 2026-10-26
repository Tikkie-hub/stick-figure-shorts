"""Build a portable source ZIP from an explicit allowlist; never package secrets or jobs."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
SOURCE_FILES = (
    'README.md', 'CODEX.md', 'requirements.txt', 'auto_knowledge_shorts.py',
    'studio_render.py', 'story_art.py', 'story_planner.py', 'story_schema.py',
    'package_project.py', 'web/app.py', 'web/studio.py', 'web/requirements.txt',
    'web/start.bat', 'web/open_browser.py', 'web/🚀 เปิด Gemini Studio.bat',
    'web/templates/index.html', 'web/templates/studio.html',
    'assets/backgrounds/README.md',
)


def project_zip():
    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        files = [ROOT / name for name in SOURCE_FILES] + sorted((ROOT / 'topics').glob('*.json'))
        for path in files:
            archive.write(path, 'ShortsStudio/' + path.relative_to(ROOT).as_posix())
    output.seek(0)
    return output
