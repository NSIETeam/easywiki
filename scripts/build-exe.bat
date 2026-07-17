@echo off
chcp 65001 >nul
title OrgMind — Build Final EXE
setlocal enabledelayedexpansion

cd /d "%~dp0.."
set "ROOT=%CD%"
set "PYTHON_DIR=C:\Program Files\Python310"

echo ============================================
echo   OrgMind v2.1 — Complete Build Pipeline
echo ============================================
echo.

:: Step 1: PyInstaller --windowed (no console)
echo [1/4] Building with PyInstaller (--windowed)...
set "PATH=%PYTHON_DIR%;%PYTHON_DIR%\Scripts;%PATH%"
pyinstaller --name OrgMind --onedir --windowed ^
    --icon orgmind\assets\icon.ico ^
    --version-file scripts\version_info.txt ^
    --add-data "frontend/dist;frontend/dist" ^
    --add-data "orgmind;orgmind" ^
    --hidden-import fastapi --hidden-import uvicorn ^
    --hidden-import jieba --hidden-import bcrypt ^
    --hidden-import numpy --hidden-import openai ^
    --hidden-import pyjwt --hidden-import webview ^
    --hidden-import pystray --hidden-import PIL ^
    --hidden-import requests ^
    --exclude-module pkg_resources --exclude-module setuptools ^
    --exclude-module torch --exclude-module sentence_transformers ^
    --exclude-module transformers --exclude-module scipy ^
    --exclude-module redis --exclude-module sqlalchemy ^
    --clean --noconfirm orgmind\desktop_shell.py
if !errorlevel! neq 0 (echo [ERROR] Build failed & pause & exit /b 1)
echo   PyInstaller done.

:: Step 2: Inject sqlite3 (PyInstaller 6.21 bug workaround)
echo [2/4] Injecting sqlite3 stdlib...
set "OUTDIR=dist\OrgMind\_internal"
rmdir /s /q "!OUTDIR!\sqlite3" 2>nul
mkdir "!OUTDIR!\sqlite3" 2>nul
xcopy "%PYTHON_DIR%\Lib\sqlite3\*" "!OUTDIR!\sqlite3\" /E /Q /Y >nul
copy "%PYTHON_DIR%\DLLs\_sqlite3.pyd" "!OUTDIR!\sqlite3\" /Y >nul
copy "%PYTHON_DIR%\DLLs\sqlite3.dll" "!OUTDIR!\sqlite3\" /Y >nul
echo   sqlite3 injected.

:: Step 3: Verify exe exists
echo [3/4] Verifying output...
if not exist "dist\OrgMind\OrgMind.exe" (
    echo [ERROR] OrgMind.exe not found!
    pause & exit /b 1
)
dir "dist\OrgMind\OrgMind.exe" | findstr OrgMind
echo   OrgMind.exe ready.

:: Step 4: Create distributable ZIP
echo [4/4] Creating OrgMind-2.1.0-windowed.zip...
cd dist
powershell -c "Compress-Archive -Path 'OrgMind\*' -DestinationPath 'OrgMind-2.1.0-windowed.zip' -Force" 2>nul
dir OrgMind-2.1.0-windowed.zip | findstr OrgMind
cd ..

echo.
echo ============================================
echo   BUILD COMPLETE
echo.
echo   Output: dist\OrgMind\OrgMind.exe
echo   ZIP:    dist\OrgMind-2.1.0-windowed.zip
echo.
echo   User: unzip -> double-click OrgMind.exe
echo ============================================
pause
