@echo off
setlocal

cd /d "%~dp0"

if not exist "deploy\app.env" (
    echo deploy\app.env was not found.
    echo Copy deploy\app.env.example to deploy\app.env and set POSTGRES_* values first.
    pause
    exit /b 1
)

for /f "usebackq tokens=1* delims==" %%A in ("deploy\app.env") do (
    if not "%%A"=="" (
        if /I not "%%A"=="REM" (
            set "%%A=%%B"
        )
    )
)

if "%POSTGRES_DB%"=="" (
    echo POSTGRES_DB is not set in deploy\app.env.
    pause
    exit /b 1
)

if "%POSTGRES_USER%"=="" (
    echo POSTGRES_USER is not set in deploy\app.env.
    pause
    exit /b 1
)

if "%POSTGRES_PASSWORD%"=="" (
    echo POSTGRES_PASSWORD is not set in deploy\app.env.
    pause
    exit /b 1
)

if "%POSTGRES_HOST%"=="" (
    echo POSTGRES_HOST is not set in deploy\app.env.
    pause
    exit /b 1
)

if "%POSTGRES_PORT%"=="" (
    echo POSTGRES_PORT is not set in deploy\app.env.
    pause
    exit /b 1
)

echo PostgreSQL settings detected:
echo   DB   : %POSTGRES_DB%
echo   USER : %POSTGRES_USER%
echo   HOST : %POSTGRES_HOST%
echo   PORT : %POSTGRES_PORT%
echo.
echo Starting setup and run with PostgreSQL...
echo.

call ".\setup_and_run.bat"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo setup_and_run.bat failed with exit code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
