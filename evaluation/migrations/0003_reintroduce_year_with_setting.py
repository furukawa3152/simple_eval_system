from datetime import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def seed_year_and_setting(apps, schema_editor):
    AppSetting = apps.get_model('evaluation', 'AppSetting')
    DepartmentGoal = apps.get_model('evaluation', 'DepartmentGoal')
    PersonalGoal = apps.get_model('evaluation', 'PersonalGoal')
    Achievement = apps.get_model('evaluation', 'Achievement')
    Evaluation = apps.get_model('evaluation', 'Evaluation')

    current_year = datetime.now().year
    AppSetting.objects.update_or_create(pk=1, defaults={'current_year': current_year})

    DepartmentGoal.objects.filter(year__isnull=True).update(year=current_year)
    PersonalGoal.objects.filter(year__isnull=True).update(year=current_year)
    Achievement.objects.filter(year__isnull=True).update(year=current_year)
    Evaluation.objects.filter(year__isnull=True).update(year=current_year)


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0002_alter_achievement_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_year', models.IntegerField(verbose_name='現在年度')),
            ],
            options={
                'verbose_name': '年度設定',
                'verbose_name_plural': '年度設定',
            },
        ),
        migrations.AddField(
            model_name='achievement',
            name='year',
            field=models.IntegerField(blank=True, null=True, verbose_name='年度'),
        ),
        migrations.AddField(
            model_name='departmentgoal',
            name='year',
            field=models.IntegerField(blank=True, null=True, verbose_name='年度'),
        ),
        migrations.AddField(
            model_name='evaluation',
            name='year',
            field=models.IntegerField(blank=True, null=True, verbose_name='年度'),
        ),
        migrations.AddField(
            model_name='personalgoal',
            name='year',
            field=models.IntegerField(blank=True, null=True, verbose_name='年度'),
        ),
        migrations.RunPython(seed_year_and_setting, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name='achievement',
            options={'ordering': ['-year', 'user__username']},
        ),
        migrations.AlterModelOptions(
            name='departmentgoal',
            options={'ordering': ['-year', 'department']},
        ),
        migrations.AlterModelOptions(
            name='evaluation',
            options={'ordering': ['-year', 'user__username']},
        ),
        migrations.AlterModelOptions(
            name='personalgoal',
            options={'ordering': ['-year', 'user__username']},
        ),
        migrations.AlterField(
            model_name='achievement',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='achievements', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='achievement',
            name='year',
            field=models.IntegerField(verbose_name='年度'),
        ),
        migrations.AlterField(
            model_name='departmentgoal',
            name='department',
            field=models.CharField(max_length=100, verbose_name='部署'),
        ),
        migrations.AlterField(
            model_name='departmentgoal',
            name='year',
            field=models.IntegerField(verbose_name='年度'),
        ),
        migrations.AlterField(
            model_name='evaluation',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='evaluation',
            name='year',
            field=models.IntegerField(verbose_name='年度'),
        ),
        migrations.AlterField(
            model_name='personalgoal',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='personal_goals', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='personalgoal',
            name='year',
            field=models.IntegerField(verbose_name='年度'),
        ),
        migrations.AddConstraint(
            model_name='departmentgoal',
            constraint=models.UniqueConstraint(fields=('department', 'year'), name='unique_department_goal_again'),
        ),
        migrations.AddConstraint(
            model_name='personalgoal',
            constraint=models.UniqueConstraint(fields=('user', 'year'), name='unique_personal_goal_again'),
        ),
        migrations.AddConstraint(
            model_name='achievement',
            constraint=models.UniqueConstraint(fields=('user', 'year'), name='unique_achievement_again'),
        ),
        migrations.AddConstraint(
            model_name='evaluation',
            constraint=models.UniqueConstraint(fields=('user', 'year'), name='unique_evaluation_again'),
        ),
    ]
