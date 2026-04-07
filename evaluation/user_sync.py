import csv
from pathlib import Path

from django.contrib.auth import get_user_model


ENCODINGS = ('utf-8-sig', 'cp932')


def load_user_rows(csv_path):
    csv_path = Path(csv_path)
    last_error = None

    for encoding in ENCODINGS:
        try:
            with csv_path.open(encoding=encoding, newline='') as file:
                return list(csv.DictReader(file)), encoding
        except UnicodeDecodeError as error:
            last_error = error

    if last_error is not None:
        raise last_error
    return [], None


def sync_users_from_csv(csv_path):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        return {
            'created': 0,
            'updated': 0,
            'deactivated': 0,
            'encoding': None,
            'path': str(csv_path),
            'missing': True,
        }

    rows, encoding = load_user_rows(csv_path)
    user_model = get_user_model()
    created_count = 0
    updated_count = 0
    csv_usernames = []

    for row in rows:
        username = row['id']
        csv_usernames.append(username)
        user, created = user_model.objects.get_or_create(username=username)
        changed = created
        is_manager = bool(int(row['上長フラグ']))

        if user.first_name != row['名前']:
            user.first_name = row['名前']
            changed = True
        if user.department != row['部署']:
            user.department = row['部署']
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
        if not user.check_password(row['パスワード']):
            user.set_password(row['パスワード'])
            changed = True

        if changed:
            user.save()

        if created:
            created_count += 1
        else:
            updated_count += 1

    deactivated_count = (
        user_model.objects.exclude(is_superuser=True)
        .exclude(username__in=csv_usernames)
        .filter(is_active=True)
        .update(is_active=False)
    )

    return {
        'created': created_count,
        'updated': updated_count,
        'deactivated': deactivated_count,
        'encoding': encoding,
        'path': str(csv_path),
        'missing': False,
    }
