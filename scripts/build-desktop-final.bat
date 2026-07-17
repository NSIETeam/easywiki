@echo off
REM ============================================================
REM OrgMind Desktop - Final Build Script
REM Builds the PyInstaller windowed exe and fixes the sqlite3
REM packaging gap (PyInstaller's fastapi/sqlite3 hooks miss the
REM pure-python sqlite3 stdlib package + native _sqlite3.pyd).
REM ============================================================
setlocal

set "PATH=C:\Program Files\Python310;C:\Program Files\Python310\Scripts;C:\Users\T14\AppData\Roaming\Python\Python310\Scripts;%PATH%"
cd /d "%~dp0.."

echo [1/4] Cleaning previous build...
rmdir /s /q build\OrgMindDesktop dist\OrgMindDesktop 2>nul
del /q OrgMindDesktop.spec 2>nul

echo [2/4] Running PyInstaller...
pyinstaller --name OrgMindDesktop --onedir --windowed ^
    --icon orgmind\assets\icon.ico ^
    --version-file scripts\version_info.txt ^
    --add-data "frontend/dist;frontend/dist" ^
    --add-data "orgmind;orgmind" ^
    --collect-submodules fastapi ^
    --collect-submodules starlette ^
    --collect-submodules uvicorn ^
    --hidden-import jieba ^
    --hidden-import bcrypt ^
    --hidden-import numpy ^
    --hidden-import openai ^
    --hidden-import jwt ^
    --hidden-import webview ^
    --exclude-module pkg_resources ^
    --exclude-module setuptools ^
    --exclude-module torch ^
    --exclude-module sentence_transformers ^
    --exclude-module transformers ^
    --exclude-module scipy ^
    --exclude-module redis ^
    --exclude-module sqlalchemy ^
    --clean --noconfirm ^
    orgmind\desktop_shell.py

if not exist "dist\OrgMindDesktop\OrgMindDesktop.exe" (
    echo BUILD FAILED - exe not found in dist
    exit /b 1
)

echo [3/4] Injecting sqlite3 (stdlib package + native extension)...
REM PyInstaller does not auto-detect sqlite3 because it's only
REM imported indirectly (orgmind.database_sqlite -> sqlite3).
mkdir "dist\OrgMindDesktop\_internal\sqlite3" 2>nul
xcopy "C:\Program Files\Python310\Lib\sqlite3\*" "dist\OrgMindDesktop\_internal\sqlite3\" /E /Y /Q >nul
copy "C:\Program Files\Python310\DLLs\_sqlite3.pyd" "dist\OrgMindDesktop\_internal\" /Y >nul
copy "C:\Program Files\Python310\DLLs\sqlite3.dll" "dist\OrgMindDesktop\_internal\" /Y >nul

echo [4/4] Build complete: dist\OrgMindDesktop\OrgMindDesktop.exe
endlocal
