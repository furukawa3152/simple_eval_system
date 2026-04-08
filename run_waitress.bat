@echo off
setlocal

cd /d "%~dp0"

set "VENV_PYTHON=.venv\Scripts\python.exe"
set "WAITRESS_EXE=.venv\Scripts\waitress-serve.exe"

if not exist "%VENV_PYTHON%" (
    echo Virtual environment was not found. Run setup_and_run.bat first.
    pause
    exit /b 1
)

if not exist "%WAITRESS_EXE%" (
    echo Waitress was not found. Installing requirements...
    "%VENV_PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install requirements.
        pause
        exit /b 1
    )
)

echo Starting Waitress on http://0.0.0.0:8000/
echo Open http://THIS_PC_IP:8000/ from another PC.
echo Press Ctrl+C to stop the server.
echo.

"%WAITRESS_EXE%" --listen=0.0.0.0:8000 config.wsgi:application

endlocal
