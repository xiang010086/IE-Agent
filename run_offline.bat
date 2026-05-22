@echo off
REM Industrial IE Agent - Offline Startup Script
REM Version: v1.0
REM Date: 2025-05-21

echo ========================================
echo   Industrial IE Agent - Action Analysis
echo   Version: v1.0 (Day -3 Delivery)
echo ========================================
echo.

REM Switch to script directory
cd /d "%~dp0"

REM Check Python environment
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found, please install Python 3.9+
    pause
    exit /b 1
)

echo [CHECK] Python environment OK
echo.

REM Check dependencies
echo [CHECK] Verifying dependencies...
python -c "import cv2; print('OpenCV:', cv2.__version__)" 2>nul
if errorlevel 1 (
    echo [WARN] OpenCV not installed, installing...
    pip install opencv-python>=4.8.0
)

python -c "import mediapipe; print('MediaPipe OK')" 2>nul
if errorlevel 1 (
    echo [WARN] MediaPipe not installed, installing...
    pip install mediapipe>=0.10.0
)

python -c "import streamlit; print('Streamlit OK')" 2>nul
if errorlevel 1 (
    echo [WARN] Streamlit not installed, installing...
    pip install streamlit>=1.30.0
)

python -c "import yaml; print('PyYAML OK')" 2>nul
if errorlevel 1 (
    echo [WARN] PyYAML not installed, installing...
    pip install pyyaml>=6.0
)

echo.
echo [START] Starting Streamlit application...
echo.
echo ========================================
echo   Open browser: http://localhost:8501
echo   Press Ctrl+C to stop
echo ========================================
echo.

REM Start Streamlit
python -m streamlit run app/streamlit_app.py

pause