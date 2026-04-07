from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from evaluation.user_sync import sync_users_from_csv


class Command(BaseCommand):
    help = 'CSVからユーザーを作成・更新します。'

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

        result = sync_users_from_csv(csv_path)
        self.stdout.write(
            self.style.SUCCESS(
                'ユーザー取込完了: '
                f"作成 {result['created']}件 / "
                f"更新 {result['updated']}件 / "
                f"無効化 {result['deactivated']}件 / "
                f"encoding={result['encoding']}"
            )
        )
