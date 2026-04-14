@echo off
setlocal

cd /d "%~dp0"

set "VENV_PYTHON=.venv\Scripts\python.exe"
set "WAITRESS_EXE=.venv\Scripts\waitress-serve.exe"

if exist "deploy\app.env" (
    for /f "usebackq tokens=1* delims==" %%A in ("deploy\app.env") do (
        if not "%%A"=="" (
            if /I not "%%A"=="REM" (
                set "%%A=%%B"
            )
        )
    )
)

if "%DJANGO_DEBUG%"=="" set "DJANGO_DEBUG=False"
if "%DJANGO_ALLOWED_HOSTS%"=="" set "DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,172.16.70.20"
if "%DJANGO_CSRF_TRUSTED_ORIGINS%"=="" set "DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000,http://172.16.70.20:8000"
if "%APP_HOST%"=="" set "APP_HOST=0.0.0.0"
if "%APP_PORT%"=="" set "APP_PORT=8000"

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

echo Starting Waitress on http://0.0.0.0:%APP_PORT%/
echo Open http://127.0.0.1:%APP_PORT%/ on this PC.
echo From another PC, open http://172.16.70.20:%APP_PORT%/
echo Press Ctrl+C to stop the server.
echo.

"%WAITRESS_EXE%" --listen=%APP_HOST%:%APP_PORT% config.wsgi:application

endlocal
