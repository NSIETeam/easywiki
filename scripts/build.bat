@echo off
chcp 65001 >nul
title OrgMind — Build Installer
setlocal enabledelayedexpansion

cd /d "%~dp0.."
set "ROOT=%CD%"

echo ============================================
echo   OrgMind v2.1 — Build Installer
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10+ required. Install from https://python.org
    echo         Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   Python %%v  ✓

:: Step 1: Install build dependencies
echo.
echo [1/4] Installing build dependencies...
python -m pip install --upgrade pip -q 2>nul
python -m pip install pyinstaller -q 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller
    pause
    exit /b 1
)
echo   PyInstaller  ✓

:: Step 2: Install project dependencies
echo.
echo [2/4] Installing project dependencies...
python -m pip install -r requirements.txt -q 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies may have failed, continuing...
)
echo   Dependencies  ✓

:: Step 3: Build with PyInstaller
echo.
echo [3/4] Building executable (this may take 2-5 minutes)...
set "PYTHONPATH=%ROOT%"

:: Use spec file if exists, otherwise auto-build
if exist "%ROOT%\scripts\orgmind.spec" (
    python -m PyInstaller "%ROOT%\scripts\orgmind.spec" --clean --noconfirm
) else (
    python -m PyInstaller ^
        --name OrgMind ^
        --onefile ^
        --console ^
        --add-data "frontend\dist;frontend\dist" ^
        --add-data "orgmind;orgmind" ^
        --add-data "README.md;." ^
        --hidden-import uvicorn ^
        --hidden-import fastapi ^
        --hidden-import sentence_transformers ^
        --hidden-import jieba ^
        --hidden-import bcrypt ^
        --hidden-import numpy ^
        --hidden-import openai ^
        --hidden-import tenacity ^
        --hidden-import pyjwt ^
        --collect-all uvicorn ^
        --collect-all fastapi ^
        --collect-all sentence_transformers ^
        --copy-metadata sentence-transformers ^
        --copy-metadata transformers ^
        --copy-metadata torch ^
        --copy-metadata numpy ^
        --clean ^
        --noconfirm ^
        -m orgmind.main_sqlite
)

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed
    pause
    exit /b 1
)
echo   Executable built  ✓

:: Step 4: Package distribution
echo.
echo [4/4] Creating distribution package...
set "DIST_DIR=%ROOT%\dist\OrgMind-Portable"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
mkdir "%DIST_DIR%"

:: Copy executable
copy "%ROOT%\dist\OrgMind.exe" "%DIST_DIR%\" >nul

:: Copy frontend
xcopy "%ROOT%\frontend\dist" "%DIST_DIR%\frontend\dist\" /E /I /Q >nul

:: Copy README
copy "%ROOT%\README.md" "%DIST_DIR%\" >nul

:: Create run script
echo @echo off > "%DIST_DIR%\OrgMind.bat"
echo start "" OrgMind.exe >> "%DIST_DIR%\OrgMind.bat"

echo.
echo ============================================
echo   Build Complete!
echo.
echo   Output: %DIST_DIR%
echo.
echo   Run OrgMind.bat to start
echo ============================================
echo.
pause
