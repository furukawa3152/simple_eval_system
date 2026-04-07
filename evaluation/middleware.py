from pathlib import Path

from django.conf import settings

from .user_sync import sync_users_from_csv


class UserCsvSyncMiddleware:
    last_signature = None

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        csv_path = Path(settings.BASE_DIR) / 'users.csv'
        if csv_path.exists():
            stat = csv_path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
            if signature != self.last_signature:
                sync_users_from_csv(csv_path)
                type(self).last_signature = signature

        return self.get_response(request)
