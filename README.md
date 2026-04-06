# Simple Evaluation System

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py import_users
python manage.py runserver
```

## Sample Login

- Manager: `001 / 1234`
- Staff: `002 / 1234`
