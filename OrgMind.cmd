@echo off
title OrgMind
cd /d "c:\Users\T14\Downloads\OrgMind-Windows-x86\OrgMind"

:: Kill old instances silently
taskkill /f /im OrgMind.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
ping -n 2 127.0.0.1 >nul

:: Start OrgMind (pywebview opens its own native window, no browser)
start "" "dist\OrgMind\OrgMind.exe"
