@echo off
setlocal
title Shorts Studio
echo ============================================
echo Shorts Studio - Windows setup
echo ============================================
echo If the title says Select, press Esc to resume.
echo.
cd /d "%~dp0.."
if errorlevel 1 goto :failed
echo [1/4] Looking for Python 3.12, 3.11 or 3.10...
set "SHORTS_PYTHON="
for %%V in (3.12 3.11 3.10) do (
if not defined SHORTS_PYTHON (
py -%%V -c "import sys; sys.exit(not ((3,10) <= sys.version_info[:2] <= (3,12)))" >nul 2>&1
if not errorlevel 1 set "SHORTS_PYTHON=py -%%V"
)
)
if defined SHORTS_PYTHON goto :python_found
echo Trying python on PATH...
python -c "import sys; sys.exit(not ((3,10) <= sys.version_info[:2] <= (3,12)))" >nul 2>&1
if not errorlevel 1 set "SHORTS_PYTHON=python"
if defined SHORTS_PYTHON goto :python_found
echo.
echo [ERROR] No compatible Python found.
echo Install Python 3.12 from https://www.python.org/downloads/windows/
echo Enable the Python launcher and Add Python to PATH during installation.
echo Then run this file again.
pause
exit /b 1
:python_found
echo Using: %SHORTS_PYTHON%
%SHORTS_PYTHON% --version
echo.
echo [2/4] Preparing the virtual environment...
if not exist ".venv\Scripts\python.exe" %SHORTS_PYTHON% -m venv .venv
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -c "import sys; sys.exit(not ((3,10) <= sys.version_info[:2] <= (3,12)))"
if errorlevel 1 (
echo [ERROR] Existing .venv uses an unsupported Python version.
echo Rename the .venv folder, then run this file again.
goto :failed
)
echo.
echo [3/4] Installing dependencies. First run may take several minutes...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r web\requirements.txt
if errorlevel 1 goto :failed
echo.
echo [4/4] Starting Shorts Studio...
echo Keep this window open. Press Ctrl+C to stop.
echo Website: http://localhost:5000
start "" /b ".venv\Scripts\python.exe" "web\open_browser.py"
".venv\Scripts\python.exe" web\app.py
if errorlevel 1 goto :failed
pause
exit /b 0
:failed
echo.
echo [ERROR] Setup or startup failed. Send a screenshot of the messages above.
pause
exit /b 1
