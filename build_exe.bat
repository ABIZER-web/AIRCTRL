@echo off
title Build AIRCTRL Windows Executable
echo ========================================================
echo       Building AIRCTRL Windows Standalone Executable
echo ========================================================
echo.

pyinstaller --clean airctrl.spec

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo  [BUILD SUCCESSFUL]
    echo  The standalone application is located in: dist\AIRCTRL\
    echo  Run dist\AIRCTRL\AIRCTRL.exe
    echo ========================================================
) else (
    echo.
    echo [BUILD FAILED] PyInstaller encountered an error.
)
pause

