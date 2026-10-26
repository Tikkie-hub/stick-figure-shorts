@echo off
setlocal
chcp 65001 >nul
title Shorts Studio
cd /d "%~dp0.."
python --version >nul 2>&1
if errorlevel 1 (
    echo Install Python 3.10 or later first.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 goto :failed
.venv\Scripts\python.exe -m pip install -r web\requirements.txt
if errorlevel 1 goto :failed
echo Shorts Studio: http://localhost:5000
start "" "http://localhost:5000"
.venv\Scripts\python.exe web\app.py
pause
exit /b
:failed
echo Setup failed. Check the error above and try again.
pause
exit /b 1
