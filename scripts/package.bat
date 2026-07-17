@echo off
chcp 65001 >nul
title OrgMind Packager
setlocal enabledelayedexpansion

cd /d "%~dp0.."
set "ROOT=%CD%"
set "OUTPUT=%ROOT%\dist\OrgMind-Portable"

echo ============================================
echo   OrgMind v2.1 - Portable Package Builder
echo ============================================
echo.

:: Clean
if exist "%OUTPUT%" rmdir /s /q "%OUTPUT%"
if exist "%ROOT%\dist\OrgMind.zip" del "%ROOT%\dist\OrgMind.zip"

:: Create structure
mkdir "%OUTPUT%"
mkdir "%OUTPUT%\orgmind"
mkdir "%OUTPUT%\frontend\dist"
mkdir "%OUTPUT%\data"

:: Copy source
echo [1/4] Copying application source...
xcopy "%ROOT%\orgmind" "%OUTPUT%\orgmind\" /E /I /Q /Y >nul
xcopy "%ROOT%\frontend\dist" "%OUTPUT%\frontend\dist\" /E /I /Q /Y >nul
copy "%ROOT%\README.md" "%OUTPUT%\" /Y >nul
copy "%ROOT%\requirements.txt" "%OUTPUT%\" /Y >nul
echo   Done.

:: Create venv with all deps
echo [2/4] Creating Python virtual environment...
set "PYEXE="
for %%p in (
    "C:\Program Files\Python310\python.exe"
    "C:\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
) do if exist %%p set "PYEXE=%%p"
if "%PYEXE%"=="" (
    python --version >nul 2>&1 && for /f %%i in ('where python') do set "PYEXE=%%i"
)
if "%PYEXE%"=="" (
    echo [ERROR] Python not found
    exit /b 1
)

"%PYEXE%" -m venv "%OUTPUT%\venv" --copies
echo [3/4] Installing dependencies...
"%OUTPUT%\venv\Scripts\pip" install --upgrade pip -q 2>nul
"%OUTPUT%\venv\Scripts\pip" install fastapi "uvicorn[standard]" numpy pyjwt python-multipart openai tenacity bcrypt jieba sentence-transformers -q 2>nul
echo   Done.

:: Create launcher
echo [4/4] Creating launcher...
(
echo @echo off
echo set "APP_DIR=%%~dp0"
echo set "DATA_DIR=%%APP_DIR%%data"
echo set "PORT=8080"
echo if not exist "%%DATA_DIR%%" mkdir "%%DATA_DIR%%"
echo set "ORGMIND_DB_PATH=%%DATA_DIR%%\orgmind.db"
echo set "ORGMIND_CONFIG_DIR=%%DATA_DIR%%\config"
echo cd /d "%%APP_DIR%%"
echo echo Starting OrgMind...
echo start "" "%%APP_DIR%%venv\Scripts\python" -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080
echo start http://localhost:8080
echo echo OrgMind is running at http://localhost:8080
echo echo.
echo echo Login: admin@local / orgmind2026
echo echo Press any key to stop...
echo pause ^>nul
echo taskkill /f /im python.exe ^>nul 2^>^&1
) > "%OUTPUT%\启动OrgMind.bat"

:: Zip package
echo.
echo Creating archive...
cd "%ROOT%\dist"
powershell -Command "Compress-Archive -Path 'OrgMind-Portable\*' -DestinationPath 'OrgMind.zip' -Force" 2>nul
if exist "OrgMind.zip" (
    for %%f in ("OrgMind.zip") do (
        set /a "SIZE=%%~zf/1048576"
        echo   Package: OrgMind.zip ^(!SIZE! MB^)
    )
)

echo.
echo ============================================
echo   Portable package ready!
echo.
echo   Location: %OUTPUT%
echo   Archive:  %ROOT%\dist\OrgMind.zip
echo.
echo   To use: Extract archive, run "启动OrgMind.bat"
echo ============================================
pause
