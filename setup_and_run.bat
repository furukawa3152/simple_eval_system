@echo off
setlocal

cd /d "%~dp0"

set "VENV_PYTHON=.venv\Scripts\python.exe"

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Please install Python and run this file again.
    pause
    exit /b 1
)

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" --version >nul 2>nul
    if errorlevel 1 (
        echo Existing virtual environment is broken. Recreating...
        rmdir /s /q ".venv"
    )
)

if not exist "%VENV_PYTHON%" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo Upgrading pip...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

echo Installing requirements...
"%VENV_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements.txt.
    pause
    exit /b 1
)

echo Running migrations...
"%VENV_PYTHON%" manage.py migrate
if errorlevel 1 (
    echo Failed to run migrate.
    pause
    exit /b 1
)

echo Syncing users.csv...
"%VENV_PYTHON%" manage.py import_users
if errorlevel 1 (
    echo Failed to run import_users.
    pause
    exit /b 1
)

echo.
echo Starting the app.
echo Open http://127.0.0.1:8000/ on this PC.
echo From another PC, open http://THIS_PC_IP:8000/
echo Press Ctrl+C to stop the server.
echo.

"%VENV_PYTHON%" manage.py runserver 0.0.0.0:8000

endlocal
