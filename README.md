# Simple Evaluation System

## Development Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py import_users
python manage.py runserver
```

Windows on a local network can also use `setup_and_run.bat`.

## Production Stack

This project is now prepared for:

- Waitress
- PostgreSQL

### Environment Variables

Copy `deploy/app.env.example` to `deploy/app.env` and update the values.

Important variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

### Windows Server Deployment Flow

1. Install Python and PostgreSQL on the Windows server.
2. Create the PostgreSQL database and user.
3. Place the project on the server.
4. Create a virtual environment and install requirements.
5. Set environment variables based on `deploy/app.env.example`.
6. Run `python manage.py migrate`.
7. Run `python manage.py import_users`.
8. Run `python manage.py collectstatic`.
9. Start the app with `run_waitress.bat`.

### Waitress Start Example

```powershell
.\run_waitress.bat
```

## Sample Login

- Manager: `1 / itaru3150`
- Staff: `2 / itaru3150`
