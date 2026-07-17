@echo off
chcp 65001 >nul
title OrgMind Server
setlocal

set "APP_DIR=%~dp0"
set "DATA_DIR=%APPDATA%\OrgMind"
set "PORT=8080"

if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

if not exist "%APP_DIR%venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

echo Starting OrgMind Server...
echo Data: %DATA_DIR%
echo Port: %PORT%
echo.

set "ORGMIND_DB_PATH=%DATA_DIR%\orgmind.db"
set "ORGMIND_CONFIG_DIR=%DATA_DIR%\config"

start "" "%APP_DIR%venv\Scripts\python" -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port %PORT% --app-dir "%APP_DIR%"

echo Waiting for server...
timeout /t 3 /nobreak >nul
start http://localhost:%PORT%
echo.
echo OrgMind is starting at http://localhost:%PORT%
echo Press any key to stop the server...
pause >nul
taskkill /f /im python.exe >nul 2>&1
