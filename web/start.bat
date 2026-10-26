@echo off
title Gemini Studio
color 0A
echo.
echo  ============================================
echo   GEMINI STUDIO - Image Generator
echo  ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] ไม่พบ Python!
    echo  กรุณาติดตั้ง Python จาก https://python.org
    echo.
    pause
    exit /b
)
echo  [OK] พบ Python แล้ว

:: Install dependencies
echo  [..] กำลังตรวจสอบ Dependencies...
pip install flask flask-cors google-genai pillow --quiet --disable-pip-version-check
echo  [OK] Dependencies พร้อมแล้ว

:: Go to project folder
cd /d "C:\Users\Administartor\.gemini\antigravity\scratch\gemini-studio"
echo.
echo  ============================================
echo   เปิดเว็บได้ที่ http://localhost:5000
echo   กด Ctrl+C เพื่อปิด Server
echo  ============================================
echo.

:: Open browser after 2 seconds
start "" timeout /t 2 /nobreak >nul
start "" "http://localhost:5000"

:: Start server
python app.py

echo.
echo  [Server ปิดแล้ว]
pause
