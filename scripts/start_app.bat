@echo off
chcp 65001 >nul
title OrgMind Server
setlocal enabledelayedexpansion

set "APP_NAME=OrgMind"
set "APP_DIR=%USERPROFILE%\.orgmind"
set "VENV_DIR=%APP_DIR%\venv"
set "PORT=8080"

echo ============================================
echo   OrgMind v2.1 — Starting...
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 not found. Please install from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   Python %%v found.
echo.

:: Create APP_DIR
if not exist "%APP_DIR%" mkdir "%APP_DIR%"

:: Create venv
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [1/3] Creating virtual environment...
    python -m venv "%VENV_DIR%" 2>nul
)

:: Install dependencies
if not exist "%VENV_DIR%\.installed" (
    echo [2/3] Installing dependencies (1-2 minutes)...
    "%VENV_DIR%\Scripts\pip" install --upgrade pip -q 2>nul
    "%VENV_DIR%\Scripts\pip" install fastapi "uvicorn[standard]" numpy pyjwt python-multipart openai tenacity bcrypt jieba sentence-transformers -q 2>nul
    type nul > "%VENV_DIR%\.installed"
    echo   Dependencies installed.
)

:: Check port
netstat -ano | findstr ":%PORT% " >nul 2>&1
if %errorlevel% equ 0 (
    echo   Port %PORT% already in use. Opening browser...
    start http://localhost:%PORT%
    exit /b 0
)

:: Set environment
set "PYTHONPATH=%~dp0..;%PYTHONPATH%"
set "ORGMIND_DB_PATH=%APP_DIR%\orgmind.db"

:: Start server
echo [3/3] Starting server on port %PORT%...
start "" /B "%VENV_DIR%\Scripts\python" -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port %PORT% > "%APP_DIR%\server.log" 2>&1

:: Wait for ready
echo   Waiting for server to be ready...
for /L %%i in (1,1,30) do (
    timeout /t 1 /nobreak >nul
    curl -s http://localhost:%PORT%/health >nul 2>&1
    if !errorlevel! equ 0 goto :ready
)
echo [ERROR] Server failed to start. Check: %APP_DIR%\server.log
pause
exit /b 1

:ready
echo   Server is ready.
echo.
echo ============================================
echo   OrgMind is running!
echo.
echo   URL:      http://localhost:%PORT%
echo   Admin:    admin@local
echo   Password: orgmind2026
echo   Manager:  tech@local
echo   Employee: dev@local
echo ============================================
echo.
start http://localhost:%PORT%
pause
