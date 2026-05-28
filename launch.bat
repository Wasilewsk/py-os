@echo off
setlocal
cd /d "%~dp0"
:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)
:: Activate and run
call venv\Scripts\activate
start "" pythonw desktop.py
endlocal
