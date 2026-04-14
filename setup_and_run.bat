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
if "%DJANGO_SECRET_KEY%"=="" set "DJANGO_SECRET_KEY=local-dev-secret-key-change-me"
if "%DJANGO_ALLOWED_HOSTS%"=="" set "DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,172.16.70.20"
if "%DJANGO_CSRF_TRUSTED_ORIGINS%"=="" set "DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000,http://172.16.70.20:8000"
if "%APP_HOST%"=="" set "APP_HOST=0.0.0.0"
if "%APP_PORT%"=="" set "APP_PORT=8000"

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

if not exist "%WAITRESS_EXE%" (
    echo Waitress executable was not found.
    pause
    exit /b 1
)

echo.
echo Starting the app with Waitress.
echo Open http://127.0.0.1:%APP_PORT%/ on this PC.
echo From another PC, open http://172.16.70.20:%APP_PORT%/
echo Press Ctrl+C to stop the server.
echo.

"%WAITRESS_EXE%" --listen=%APP_HOST%:%APP_PORT% config.wsgi:application

endlocal
