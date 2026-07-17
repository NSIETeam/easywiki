@echo off
chcp 65001 >nul
title OrgMind v2.1 — Installer
setlocal enabledelayedexpansion

:: ============ CONFIG ============
set "APP_NAME=OrgMind"
set "APP_VERSION=2.1.0"
set "APP_DIR=%ProgramFiles%\OrgMind"
set "DATA_DIR=%ProgramData%\OrgMind"
set "START_MENU_DIR=%ProgramData%\Microsoft\Windows\Start Menu\Programs\OrgMind"
set "PORT=8080"

:: ============ ADMIN CHECK ============
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ================================================
    echo   OrgMind Installer needs Administrator rights
    echo   Right-click this file -> Run as Administrator
    echo ================================================
    pause
    exit /b 1
)

:: ============ UI ============
cls
echo.
echo   ================================================
echo     OrgMind v%APP_VERSION% — Installation Wizard
echo   ================================================
echo.
echo     Organizational Memory System
echo     AI-powered knowledge base for teams
echo.
echo   ================================================
echo.
echo   This will install OrgMind to:
echo     %APP_DIR%
echo.
echo   Data will be stored in:
echo     %DATA_DIR%
echo.
echo   ================================================
echo.
choice /c YN /m "Continue with installation"
if errorlevel 2 exit /b 0

:: ============ STEP 1: Check Python ============
cls
echo   [1/5] Checking Python...
echo   ================================================

set "PYTHON_EXE="
for %%p in (
    "C:\Program Files\Python310\python.exe"
    "C:\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) do (
    if exist %%p set "PYTHON_EXE=%%~p"
)
if "%PYTHON_EXE%"=="" (
    :: Try PATH
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "tokens=*" %%i in ('where python 2^>nul') do set "PYTHON_EXE=%%i"
    )
)

if "%PYTHON_EXE%"=="" (
    echo   Python 3.10+ is required but not found!
    echo.
    echo   Download from: https://mirrors.tuna.tsinghua.edu.cn/python/3.10.11/python-3.10.11-amd64.exe
    echo   Or from:     https://www.python.org/downloads/
    echo.
    echo   IMPORTANT: Check "Add Python to PATH" during install!
    echo.
    choice /c YN /m "Open download page now"
    if errorlevel 2 exit /b 1
    start https://mirrors.tuna.tsinghua.edu.cn/python/3.10.11/python-3.10.11-amd64.exe
    echo.
    echo   After installing Python, re-run this installer.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('"%PYTHON_EXE%" --version 2^>^&1') do echo   Found Python %%v  ✓
echo.

:: ============ STEP 2: Create directories ============
echo   [2/5] Creating directories...
echo   ================================================
if not exist "%APP_DIR%" mkdir "%APP_DIR%"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%START_MENU_DIR%" mkdir "%START_MENU_DIR%"
echo   Install dir:  %APP_DIR%
echo   Data dir:     %DATA_DIR%
echo.

:: ============ STEP 3: Copy files ============
echo   [3/5] Copying application files...
echo   ================================================
set "SRC_DIR=%~dp0.."
xcopy "%SRC_DIR%\orgmind" "%APP_DIR%\orgmind\" /E /I /Q /Y >nul
xcopy "%SRC_DIR%\frontend\dist" "%APP_DIR%\frontend\dist\" /E /I /Q /Y >nul
copy "%SRC_DIR%\requirements.txt" "%APP_DIR%\" /Y >nul
copy "%SRC_DIR%\README.md" "%APP_DIR%\" /Y >nul
echo   Files copied successfully  ✓
echo.

:: ============ STEP 4: Install dependencies ============
echo   [4/5] Installing Python dependencies (1-3 min)...
echo   ================================================

:: Create venv
if not exist "%APP_DIR%\venv\Scripts\python.exe" (
    echo   Creating virtual environment...
    "%PYTHON_EXE%" -m venv "%APP_DIR%\venv" 2>nul
)

:: Install via pip
echo   Installing packages...
"%APP_DIR%\venv\Scripts\pip" install --upgrade pip -q 2>nul
"%APP_DIR%\venv\Scripts\pip" install -r "%APP_DIR%\requirements.txt" -q 2>nul
if %errorlevel% neq 0 (
    echo   WARNING: Some packages failed. Trying direct install...
    "%APP_DIR%\venv\Scripts\pip" install fastapi "uvicorn[standard]" numpy pyjwt python-multipart openai tenacity bcrypt jieba sentence-transformers -q 2>nul
)
echo   Dependencies installed  ✓
echo.

:: ============ STEP 5: Create shortcuts ============
echo   [5/5] Creating shortcuts...
echo   ================================================

:: Start Menu shortcut
set "LAUNCHER=%APP_DIR%\OrgMind.launcher.bat"
(
echo @echo off
echo set "ORGMIND_DB_PATH=%DATA_DIR%\orgmind.db"
echo set "ORGMIND_CONFIG_DIR=%DATA_DIR%\config"
echo start "" "%APP_DIR%\venv\Scripts\python" -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port %PORT% --app-dir "%APP_DIR%"
) > "%LAUNCHER%"

:: Create shortcut in Start Menu
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%START_MENU_DIR%\OrgMind.lnk'); $SC.TargetPath = '%LAUNCHER%'; $SC.WorkingDirectory = '%APP_DIR%'; $SC.Description = 'OrgMind - Organizational Memory System'; $SC.Save()" 2>nul

:: Desktop shortcut
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%USERPROFILE%\Desktop\OrgMind.lnk'); $SC.TargetPath = '%LAUNCHER%'; $SC.WorkingDirectory = '%APP_DIR%'; $SC.Description = 'OrgMind - Organizational Memory System'; $SC.Save()" 2>nul

:: Firewall rule
netsh advfirewall firewall add rule name="OrgMind" dir=in action=allow protocol=TCP localport=%PORT% >nul 2>&1

echo   Shortcuts created  ✓
echo.

:: ============ COMPLETE ============
echo   ================================================
echo     Installation Complete!
echo   ================================================
echo.
echo     Start OrgMind from:
echo       - Desktop shortcut
echo       - Start Menu ^> OrgMind
echo.
echo     Then open:  http://localhost:%PORT%
echo.
echo     Default login:
echo       Email:    admin@local
echo       Password: orgmind2026
echo.
echo   ================================================
echo.

choice /c YN /m "Launch OrgMind now"
if errorlevel 2 goto :end

start "" "%LAUNCHER%"
echo   Waiting for server to start...
timeout /t 5 /nobreak >nul
start http://localhost:%PORT%

:end
exit /b 0
