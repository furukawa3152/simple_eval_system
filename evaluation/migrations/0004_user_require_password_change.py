from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0003_reintroduce_year_with_setting'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='require_password_change',
            field=models.BooleanField(default=True, verbose_name='初回パスワード変更'),
        ),
    ]
