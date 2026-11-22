@echo off
title yt-dlp GUI Pro
cd /d "%~dp0"

echo ===================================================
echo             yt-dlp GUI Pro Launcher
echo ===================================================

:: Check for Python in PATH
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :FOUND_PYTHON
)

:: Check common Windows Python install locations
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    goto :FOUND_PYTHON
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :FOUND_PYTHON
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :FOUND_PYTHON
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto :FOUND_PYTHON
)

echo [ERROR] Python 3 was not found on your system!
echo Please download and install Python from https://www.python.org/downloads/
echo Make sure to check the box: "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:FOUND_PYTHON
echo [INFO] Using Python: %PY_CMD%

:: Verify dependencies
"%PY_CMD%" -c "import PySide6, yt_dlp" >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Installing required packages from requirements.txt...
    "%PY_CMD%" -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

:: Launch the application
echo [INFO] Launching yt-dlp GUI Pro...
start "" "%PY_CMD%" ytdlp_gui.py
