@echo off
setlocal enabledelayedexpansion
REM License Management System - Build .exe on Windows
REM Run this script on a Windows machine with Python 3.8+ installed

color 0A
echo.
echo ==========================================
echo License Management System - Build Script
echo ==========================================
echo.

REM Check Python exists
echo Step 1: Checking Python installation...
set "PY_CMD=python"
py -3.8 --version >nul 2>&1
if %errorlevel%==0 (
    set "PY_CMD=py -3.8"
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python not found!
        echo Please install Python 3.8+ from https://www.python.org/downloads/
        echo On Windows 7, use Python 3.8.x.
        pause
        exit /b 1
    )
)
%PY_CMD% --version
echo OK - Python found (%PY_CMD%)
echo.

REM Install dependencies
echo Step 2: Installing/upgrading PyInstaller and PyQt5...
echo This may take 2-3 minutes...
%PY_CMD% -m pip install --upgrade pip >nul 2>&1
%PY_CMD% -m pip install pyinstaller PyQt5 2>nul

if errorlevel 1 (
    echo WARNING: pip install had issues, but continuing...
)
echo OK - Dependencies installed
echo.

REM Verify PyInstaller is installed
echo Step 3: Verifying PyInstaller installation...
%PY_CMD% -m PyInstaller --version
if errorlevel 1 (
    echo ERROR: PyInstaller failed to install!
    echo Try running: %PY_CMD% -m pip install --upgrade pyinstaller
    pause
    exit /b 1
)
echo OK - PyInstaller ready
echo.

REM Clean old builds
echo Step 4: Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
echo OK - Cleaned
echo.

REM Run PyInstaller
echo Step 5: Building executable...
echo (This may take 3-5 minutes, please wait...)
echo.
%PY_CMD% -m PyInstaller --clean build_exe.spec --distpath=dist --buildpath=build

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build FAILED!
    echo.
    echo Troubleshooting steps:
    echo 1. Make sure main.py exists in this folder
    echo 2. Make sure db\, ui\, and notifications\ folders exist
    echo 3. Try manually: %PY_CMD% -m PyInstaller --onedir --windowed main.py
    echo 4. Check WINDOWS_TROUBLESHOOTING.md for more help
    echo.
    pause
    exit /b 1
)

echo.
echo.
echo ==========================================
echo SUCCESS! Build complete!
echo ==========================================
echo.
echo Your executable is ready at:
echo   %CD%\dist\LicenseManager.exe
echo.
echo Next steps:
echo   1. Double-click dist\LicenseManager.exe to test it
echo   2. Copy dist\LicenseManager.exe to other Windows PCs to use it
echo   3. Share the dist\ folder with others via ZIP/folder share
echo.
pause
