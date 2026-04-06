from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    department = models.CharField(max_length=100, verbose_name='部署')
    is_manager = models.BooleanField(default=False, verbose_name='上長フラグ')

    def __str__(self):
        return f'{self.username} {self.last_name}{self.first_name}'.strip()


class DepartmentGoal(models.Model):
    department = models.CharField(max_length=100, unique=True, verbose_name='部署')
    philosophy = models.TextField(blank=True, verbose_name='理念')
    finance = models.TextField(blank=True, verbose_name='経営')
    safety = models.TextField(blank=True, verbose_name='安全')
    cooperation = models.TextField(blank=True, verbose_name='連携')

    class Meta:
        ordering = ['department']

    def __str__(self):
        return self.department


class PersonalGoal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personal_goal')
    philosophy_goal = models.TextField(blank=True, verbose_name='理念目標')
    finance_goal = models.TextField(blank=True, verbose_name='経営目標')
    safety_goal = models.TextField(blank=True, verbose_name='安全目標')
    cooperation_goal = models.TextField(blank=True, verbose_name='連携目標')

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return str(self.user)


class Achievement(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='achievement')
    philosophy_result = models.TextField(blank=True, verbose_name='理念達成')
    finance_result = models.TextField(blank=True, verbose_name='経営達成')
    safety_result = models.TextField(blank=True, verbose_name='安全達成')
    cooperation_result = models.TextField(blank=True, verbose_name='連携達成')

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return str(self.user)


class Evaluation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='evaluation')
    philosophy_eval = models.TextField(blank=True, verbose_name='理念評価')
    finance_eval = models.TextField(blank=True, verbose_name='経営評価')
    safety_eval = models.TextField(blank=True, verbose_name='安全評価')
    cooperation_eval = models.TextField(blank=True, verbose_name='連携評価')

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return str(self.user)
