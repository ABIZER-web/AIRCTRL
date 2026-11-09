@echo off
title AIRCTRL - Environment Setup
echo ========================================================
echo       AIRCTRL - Automated Dependency Setup
echo   AI-Powered Virtual Mouse, Keyboard & Assistant
echo ========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/3] Upgrading pip...
python -m pip install --upgrade pip

echo [2/3] Installing AIRCTRL dependencies from requirements.txt...
pip install -r requirements.txt

echo [3/3] Checking MediaPipe model asset...
if not exist "assets\models\hand_landmarker.task" (
    echo Downloading hand_landmarker.task...
    python -c "import urllib.request, os; os.makedirs('assets/models', exist_ok=True); urllib.request.urlretrieve('https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task', 'assets/models/hand_landmarker.task')"
)

echo.
echo ========================================================
echo  [SUCCESS] All dependencies and models are ready!
echo  To run the application, double-click run_airctrl.bat
echo ========================================================
echo.
pause

