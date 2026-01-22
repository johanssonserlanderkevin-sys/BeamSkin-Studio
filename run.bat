@echo off
cd /d "%~dp0"

echo ========================================
echo BeamSkin Studio Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo Checking Python installation...
python --version
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Virtual environment not found. Creating one...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
    echo.
)

REM Check if requirements.txt exists
if not exist requirements.txt (
    echo ERROR: requirements.txt not found!
    echo Please make sure you have all the files from the repository.
    echo.
    pause
    exit /b 1
)

echo Checking dependencies in virtual environment...
echo.

REM Check each package individually in the venv
".venv\Scripts\python.exe" -c "import customtkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [MISSING] customtkinter - Installing...
    ".venv\Scripts\pip.exe" install customtkinter
) else (
    echo [OK] customtkinter
)

".venv\Scripts\python.exe" -c "import PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo [MISSING] Pillow - Installing...
    ".venv\Scripts\pip.exe" install Pillow
) else (
    echo [OK] Pillow
)

".venv\Scripts\python.exe" -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo [MISSING] requests - Installing...
    ".venv\Scripts\pip.exe" install requests
) else (
    echo [OK] requests
)

echo.
echo All dependencies are installed!
echo.
echo Starting BeamSkin Studio...
echo ========================================
echo.

REM Run the main application
start "" ".venv\Scripts\python.exe" main.py

REM Keep window open briefly to show any startup messages
timeout /t 2 /nobreak >nul
