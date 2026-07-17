@echo off
chcp 65001 >nul
title OrgMind v2.1 — Installer
setlocal enabledelayedexpansion

set "APP_NAME=OrgMind"
set "APP_VERSION=2.1.0"
set "PORT=8080"

:: Admin or user install
net session >nul 2>&1
if "!errorlevel!"=="0" (
    set "INSTALL_DIR=C:\Program Files\OrgMind"
    set "IS_ADMIN=1"
) else (
    set "INSTALL_DIR=%LOCALAPPDATA%\OrgMind"
    set "IS_ADMIN=0"
)

cls
echo.
echo   ==============================================
echo     OrgMind v%APP_VERSION% — Installation
echo     Organizational Memory System
echo   ==============================================
echo.
echo   Install to: !INSTALL_DIR!
echo   Port:       %PORT%
echo.

choice /c YN /m "Proceed with installation"
if errorlevel 2 exit /b 0

:: Step 1: Check Python
echo.
echo   [1/4] Python check...
set "PYTHON="
for %%p in ("C:\Program Files\Python310\python.exe" "C:\Python310\python.exe" "%LOCALAPPDATA%\Programs\Python\Python310\python.exe") do (
    if exist %%p set "PYTHON=%%~p"
)
if "!PYTHON!"=="" (
    python --version >nul 2>&1
    if !errorlevel! equ 0 for /f "tokens=*" %%i in ('where python 2^>nul') do set "PYTHON=%%i"
)
if "!PYTHON!"=="" (
    echo   Python 3.10+ not found!
    echo   Download: https://mirrors.tuna.tsinghua.edu.cn/python/3.10.11/python-3.10.11-amd64.exe
    echo   MUST check "Add Python to PATH" during install!
    start https://mirrors.tuna.tsinghua.edu.cn/python/3.10.11/python-3.10.11-amd64.exe
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('"!PYTHON!" --version 2^>^&1') do echo   Python %%v  ✓

:: Step 2: Copy files
echo.
echo   [2/4] Copying files...
set "SRC=%~dp0"
mkdir "!INSTALL_DIR!" 2>nul
xcopy "!SRC!\orgmind" "!INSTALL_DIR!\orgmind\" /E /I /Q /Y >nul
xcopy "!SRC!\frontend\dist" "!INSTALL_DIR!\frontend\dist\" /E /I /Q /Y >nul
copy "!SRC!\requirements.txt" "!INSTALL_DIR!\" /Y >nul
copy "!SRC!\README.md" "!INSTALL_DIR!\" /Y >nul
echo   Files copied  ✓

:: Step 3: Create venv + install deps
echo.
echo   [3/4] Installing dependencies (2-5 min)...
cd /d "!INSTALL_DIR!"
"!PYTHON!" -m venv venv 2>nul
venv\Scripts\pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi "uvicorn[standard]" numpy pyjwt python-multipart openai tenacity bcrypt jieba sentence-transformers 2>nul
echo   Dependencies  ✓

:: Step 4: Create launcher
echo.
echo   [4/4] Creating launcher...
(
echo @echo off
echo set "DATA_DIR=%%~dp0data"
echo if not exist "%%DATA_DIR%%" mkdir "%%DATA_DIR%%"
echo set "ORGMIND_DB_PATH=%%DATA_DIR%%\orgmind.db"
echo set "ORGMIND_CONFIG_DIR=%%DATA_DIR%%\config"
echo cd /d "%%~dp0"
echo echo Starting OrgMind on http://localhost:%PORT%
echo start "" "%%~dp0venv\Scripts\python" -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port %PORT%
echo start http://localhost:%PORT%
echo pause
) > "!INSTALL_DIR!\OrgMind.bat"

:: Desktop shortcut
powershell -c "$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut('!USERPROFILE!\Desktop\OrgMind.lnk');$s.TargetPath='!INSTALL_DIR!\OrgMind.bat';$s.Save()" 2>nul

:: Firewall
if "!IS_ADMIN!"=="1" netsh advfirewall firewall add rule name="OrgMind" dir=in action=allow protocol=TCP localport=%PORT% >nul 2>&1

echo.
echo   ==============================================
echo     Installation complete!
echo.
echo     Start: Desktop "OrgMind" shortcut
echo     URL:   http://localhost:%PORT%
echo     Login: admin@local / orgmind2026
echo   ==============================================
echo.
choice /c YN /m "Launch now"
if errorlevel 2 exit /b 0
start "" "!INSTALL_DIR!\OrgMind.bat"
