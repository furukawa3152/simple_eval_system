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

## Batch Startup

`setup_and_run.bat` and `run_waitress.bat` start the app with `DEBUG=False`.
The batch startup uses plain HTTP on port `8000`, so secure cookies are disabled by default for this mode.
If you later place the app behind HTTPS, set `DJANGO_SECURE_COOKIES=True`.

This project is configured so the batch files can be used directly on the server at `172.16.70.20`.

```powershell
.\setup_and_run.bat
```

or

```powershell
.\run_waitress.bat
```

Access URLs:

- On the server itself: `http://127.0.0.1:8000/`
- From another PC on the network: `http://172.16.70.20:8000/`

## PostgreSQL Switch

If `POSTGRES_DB` is not set, the app uses SQLite:

- [db.sqlite3](/c:/Users/user/cursor_project/simple_eval_system/db.sqlite3)

If `POSTGRES_DB` is set, the app switches to PostgreSQL automatically.

### Recommended App Env

Copy `deploy/app.env.example` to `deploy/app.env` and update the values.
Both batch files now read `deploy/app.env` automatically if the file exists.

Example:

```env
DJANGO_SECRET_KEY=change-this-to-a-secure-random-string
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,172.16.70.20
DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000,http://172.16.70.20:8000
DJANGO_SECURE_COOKIES=False

POSTGRES_DB=simple_eval
POSTGRES_USER=simple_eval_user
POSTGRES_PASSWORD=change-this-password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_SSLMODE=require
```

### Local PostgreSQL On The Same Server

```env
POSTGRES_DB=simple_eval
POSTGRES_USER=simple_eval_user
POSTGRES_PASSWORD=change-this-password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

Then run:

```powershell
.\setup_postgres_and_run.bat
```

### Remote PostgreSQL Server

```env
POSTGRES_DB=simple_eval
POSTGRES_USER=simple_eval_user
POSTGRES_PASSWORD=change-this-password
POSTGRES_HOST=172.16.70.30
POSTGRES_PORT=5432
POSTGRES_SSLMODE=require
```

Operational recommendations:

- Restrict PostgreSQL to the app server only
- Do not use `trust`
- Prefer `scram-sha-256`

### PostgreSQL Install After-Step Batch

After PostgreSQL is installed and `deploy/app.env` is filled in, you can use this batch:

```powershell
.\setup_postgres_and_run.bat
```

What it does:

1. Checks that `deploy/app.env` exists
2. Checks that `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT` are set
3. Runs the normal setup flow
4. Runs `migrate`
5. Runs `import_users`
6. Starts Waitress

### Confirm Which DB Is In Use

```powershell
@'
from django.db import connection
print(connection.vendor)
print(connection.settings_dict["ENGINE"])
print(connection.settings_dict["NAME"])
print(connection.settings_dict["HOST"])
'@ | .\.venv\Scripts\python manage.py shell
```

If PostgreSQL is active, `connection.vendor` will be `postgresql`.

## SQLite To PostgreSQL Migration

1. Prepare PostgreSQL and create the database and user.
2. Create `deploy/app.env` with the `POSTGRES_*` settings.
3. Run migrations against PostgreSQL:

```powershell
.\.venv\Scripts\python manage.py migrate
```

4. Import users from CSV:

```powershell
.\.venv\Scripts\python manage.py import_users
```

5. If you need to copy existing evaluation data from SQLite, export and import it separately before switching users to the new DB.

Important:

- `migrate` only creates tables
- Existing SQLite data is not copied automatically
- `users.csv` can recreate accounts, but not historical goal/evaluation records

## Production Stack

This project is prepared for:

- Waitress
- PostgreSQL

### Windows Server Deployment Flow

1. Install Python and PostgreSQL on the Windows server.
2. Create the PostgreSQL database and user.
3. Place the project on the server.
4. Create a virtual environment and install requirements.
5. Create `deploy/app.env` based on `deploy/app.env.example`.
6. Run `python manage.py migrate`.
7. Run `python manage.py import_users`.
8. Run `python manage.py collectstatic`.
9. Start the app with `run_waitress.bat`.

## Sample Login

- Manager: `1 / itaru3150`
- Staff: `2 / itaru3150`
