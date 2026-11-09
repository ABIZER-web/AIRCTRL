@echo off
title AIRCTRL - AI Desktop Assistant
echo Starting AIRCTRL...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Application exited with an error code: %errorlevel%
    pause
)

