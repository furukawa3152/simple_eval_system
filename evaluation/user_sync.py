import csv
from pathlib import Path

from django.contrib.auth import get_user_model


ENCODINGS = ("utf-8-sig", "cp932")
PASSWORD_CHANGE_FIELD = "要パスワード変更"
PASSWORD_FIELD = "パスワード"
USERNAME_FIELD = "id"
NAME_FIELD = "名前"
DEPARTMENT_FIELD = "部署"
MANAGER_FIELD = "上長フラグ"


def load_user_rows(csv_path):
    csv_path = Path(csv_path)
    last_error = None

    for encoding in ENCODINGS:
        try:
            with csv_path.open(encoding=encoding, newline="") as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                fieldnames = list(reader.fieldnames or [])
                return rows, encoding, fieldnames
        except UnicodeDecodeError as error:
            last_error = error

    if last_error is not None:
        raise last_error
    return [], None, []


def should_require_password_change(row):
    value = row.get(PASSWORD_CHANGE_FIELD)
    if value is None or value == "":
        return True
    return str(value).strip() in {"1", "true", "True", "yes", "YES"}


def write_user_rows(csv_path, rows, fieldnames, encoding):
    csv_path = Path(csv_path)
    normalized_fieldnames = list(fieldnames)
    if PASSWORD_CHANGE_FIELD not in normalized_fieldnames:
        normalized_fieldnames.append(PASSWORD_CHANGE_FIELD)

    for row in rows:
        if PASSWORD_CHANGE_FIELD not in row or row[PASSWORD_CHANGE_FIELD] == "":
            row[PASSWORD_CHANGE_FIELD] = "1"

    with csv_path.open("w", encoding=encoding or "utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=normalized_fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sync_users_from_csv(csv_path):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        return {
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "encoding": None,
            "path": str(csv_path),
            "missing": True,
        }

    rows, encoding, fieldnames = load_user_rows(csv_path)
    user_model = get_user_model()
    created_count = 0
    updated_count = 0
    csv_usernames = []
    csv_changed = PASSWORD_CHANGE_FIELD not in fieldnames

    for row in rows:
        username = row[USERNAME_FIELD]
        csv_usernames.append(username)
        user, created = user_model.objects.get_or_create(username=username)
        changed = created
        is_manager = bool(int(row[MANAGER_FIELD]))
        require_password_change = should_require_password_change(row)

        if user.first_name != row[NAME_FIELD]:
            user.first_name = row[NAME_FIELD]
            changed = True
        if user.department != row[DEPARTMENT_FIELD]:
            user.department = row[DEPARTMENT_FIELD]
            changed = True
        if user.is_manager != is_manager:
            user.is_manager = is_manager
            changed = True
        if user.is_staff != is_manager:
            user.is_staff = is_manager
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True

        # Existing users keep their current password and password-change state in the DB.
        if created:
            user.require_password_change = require_password_change
            user.set_password(row[PASSWORD_FIELD])
            changed = True

        if changed:
            user.save()

        if created:
            created_count += 1
        else:
            updated_count += 1

        if row.get(PASSWORD_CHANGE_FIELD) != ("1" if require_password_change else "0"):
            row[PASSWORD_CHANGE_FIELD] = "1" if require_password_change else "0"
            csv_changed = True

    deleted_count = (
        user_model.objects.exclude(is_superuser=True)
        .exclude(username__in=csv_usernames)
        .delete()[0]
    )

    if csv_changed:
        write_user_rows(csv_path, rows, fieldnames, encoding)

    return {
        "created": created_count,
        "updated": updated_count,
        "deleted": deleted_count,
        "encoding": encoding,
        "path": str(csv_path),
        "missing": False,
    }
