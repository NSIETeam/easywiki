@echo off
cd /d "c:\Users\T14\Downloads\OrgMind-Windows-x86\OrgMind\dist\OrgMindBackend"

:: Kill old backend
taskkill /f /im OrgMindBackend.exe >nul 2>&1

:: Start backend hidden
start "" /B OrgMindBackend.exe

:: Wait for ready
echo Starting OrgMind...
:wait
ping -n 2 127.0.0.1 >nul
curl -s http://127.0.0.1:8080/health >nul 2>&1
if errorlevel 1 goto wait

:: Open in default browser
start http://127.0.0.1:8080
exit
