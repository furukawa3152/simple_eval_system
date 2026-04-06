import csv
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'CSVからユーザーを作成・更新します。'

    ENCODINGS = ('utf-8-sig', 'cp932')

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default='users.csv',
            help='ユーザーCSVのパス。デフォルトは users.csv',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['path'])
        if not csv_path.exists():
            raise CommandError(f'CSVファイルが見つかりません: {csv_path}')

        user_model = get_user_model()
        created_count = 0
        updated_count = 0

        reader = None
        last_error = None
        used_encoding = None

        for encoding in self.ENCODINGS:
            try:
                with csv_path.open(encoding=encoding, newline='') as file:
                    rows = list(csv.DictReader(file))
                reader = rows
                used_encoding = encoding
                break
            except UnicodeDecodeError as error:
                last_error = error

        if reader is None:
            raise CommandError(
                f'CSVファイルを読み込めませんでした。対応エンコーディング: {", ".join(self.ENCODINGS)}'
            ) from last_error

        for row in reader:
            user, created = user_model.objects.get_or_create(username=row['id'])
            user.first_name = row['名前']
            user.department = row['部署']
            user.is_manager = bool(int(row['上長フラグ']))
            user.is_staff = user.is_manager
            user.set_password(row['パスワード'])
            user.save()

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'ユーザー取込完了: 作成 {created_count}件 / 更新 {updated_count}件 / encoding={used_encoding}'
            )
        )
