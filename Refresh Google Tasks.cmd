@echo off
setlocal
cd /d "%~dp0"
title Refresh Google Tasks
echo Refreshing your Google Tasks...
echo.
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo The Python environment is missing. See README.md for setup.
    pause
    exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0tasks_to_notepad.py" %*
if errorlevel 1 (
    echo.
    echo Refresh failed. The previous task report has been kept.
    echo If Google needs you to sign in again, follow the instructions above.
    pause
    exit /b 1
)
endlocal
