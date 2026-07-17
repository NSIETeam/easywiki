@echo off
chcp 65001 >nul
title OrgMind Electron — Build
setlocal enabledelayedexpansion

cd /d "%~dp0..\electron"
set "ROOT=%~dp0.."

echo ============================================
echo   OrgMind v2.1 — Electron Desktop Build
echo ============================================
echo.

:: Check Node.js
node --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Node.js required. Install from https://nodejs.org
    pause
    exit /b 1
)
for /f "tokens=1" %%v in ('node --version 2^>^&1') do echo   Node %%v  OK

:: Check Python
set "PYTHON="
for %%p in ("C:\Program Files\Python310\python.exe" "C:\Python310\python.exe") do (
    if exist %%p set "PYTHON=%%~p"
)
if "!PYTHON!"=="" (
    python --version >nul 2>&1 && for /f %%i in ('where python') do set "PYTHON=%%i"
)
if "!PYTHON!"=="" (
    echo [WARN] Python not found - Electron will prompt user to install
) else (
    for /f "tokens=2" %%v in ('"!PYTHON!" --version 2^>^&1') do echo   Python %%v  OK
)

:: Install npm deps
echo.
echo [1/4] Installing npm dependencies...
if not exist "node_modules\electron" (
    call npm install
    if !errorlevel! neq 0 (
        echo [ERROR] npm install failed
        pause
        exit /b 1
    )
) else (
    echo   Already installed
)

:: Setup Python venv for bundling
echo.
echo [2/4] Setting up Python environment for bundling...
set "VENV_DIR=!ROOT!\venv"
if not exist "!VENV_DIR!\Scripts\python.exe" (
    if not "!PYTHON!"=="" (
        echo   Creating venv...
        "!PYTHON!" -m venv "!VENV_DIR!" 2>nul
        echo   Installing Python packages...
        "!VENV_DIR!\Scripts\pip" install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi "uvicorn[standard]" numpy pyjwt python-multipart openai tenacity bcrypt jieba sentence-transformers -q 2>nul
    )
)
echo   OK

:: Build Electron
echo.
echo [3/4] Building Electron app (3-5 minutes)...
echo   Target: Portable + NSIS Installer

call npx electron-builder --win portable nsis 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

:: Show result
echo.
echo [4/4] Build complete!
echo.
dir /b "!ROOT!\dist\electron\*.exe" 2>nul

echo.
echo ============================================
echo   Electron desktop app built successfully!
echo.
echo   Output: !ROOT!\dist\electron\
echo ============================================
pause
