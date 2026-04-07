from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    department = models.CharField(max_length=100, verbose_name='部署')
    is_manager = models.BooleanField(default=False, verbose_name='上長フラグ')

    def __str__(self):
        return f'{self.username} {self.last_name}{self.first_name}'.strip()


class AppSetting(models.Model):
    current_year = models.IntegerField(verbose_name='現在年度')

    class Meta:
        verbose_name = '年度設定'
        verbose_name_plural = '年度設定'

    def __str__(self):
        return f'現在年度: {self.current_year}'


class DepartmentGoal(models.Model):
    department = models.CharField(max_length=100, verbose_name='部署')
    year = models.IntegerField(verbose_name='年度')
    philosophy = models.TextField(blank=True, verbose_name='理念')
    finance = models.TextField(blank=True, verbose_name='経営')
    safety = models.TextField(blank=True, verbose_name='安全')
    cooperation = models.TextField(blank=True, verbose_name='連携')

    class Meta:
        ordering = ['-year', 'department']
        constraints = [
            models.UniqueConstraint(fields=['department', 'year'], name='unique_department_goal_again')
        ]

    def __str__(self):
        return f'{self.department} / {self.year}'


class PersonalGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_goals')
    year = models.IntegerField(verbose_name='年度')
    philosophy_goal = models.TextField(blank=True, verbose_name='理念目標')
    finance_goal = models.TextField(blank=True, verbose_name='経営目標')
    safety_goal = models.TextField(blank=True, verbose_name='安全目標')
    cooperation_goal = models.TextField(blank=True, verbose_name='連携目標')

    class Meta:
        ordering = ['-year', 'user__username']
        constraints = [
            models.UniqueConstraint(fields=['user', 'year'], name='unique_personal_goal_again')
        ]

    def __str__(self):
        return f'{self.user} / {self.year}'


class Achievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    year = models.IntegerField(verbose_name='年度')
    philosophy_result = models.TextField(blank=True, verbose_name='理念達成')
    finance_result = models.TextField(blank=True, verbose_name='経営達成')
    safety_result = models.TextField(blank=True, verbose_name='安全達成')
    cooperation_result = models.TextField(blank=True, verbose_name='連携達成')

    class Meta:
        ordering = ['-year', 'user__username']
        constraints = [
            models.UniqueConstraint(fields=['user', 'year'], name='unique_achievement_again')
        ]

    def __str__(self):
        return f'{self.user} / {self.year}'


class Evaluation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluations')
    year = models.IntegerField(verbose_name='年度')
    philosophy_eval = models.TextField(blank=True, verbose_name='理念評価')
    finance_eval = models.TextField(blank=True, verbose_name='経営評価')
    safety_eval = models.TextField(blank=True, verbose_name='安全評価')
    cooperation_eval = models.TextField(blank=True, verbose_name='連携評価')

    class Meta:
        ordering = ['-year', 'user__username']
        constraints = [
            models.UniqueConstraint(fields=['user', 'year'], name='unique_evaluation_again')
        ]

    def __str__(self):
        return f'{self.user} / {self.year}'
