from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Achievement, DepartmentGoal, Evaluation, PersonalGoal, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('追加情報', {'fields': ('department', 'is_manager')}),
    )
    list_display = ('username', 'first_name', 'last_name', 'department', 'is_manager', 'is_staff')
    list_filter = ('department', 'is_manager', 'is_staff')


@admin.register(DepartmentGoal)
class DepartmentGoalAdmin(admin.ModelAdmin):
    list_display = ('department',)
    list_filter = ('department',)


@admin.register(PersonalGoal)
class PersonalGoalAdmin(admin.ModelAdmin):
    list_display = ('user',)
    list_filter = ('user__department',)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('user',)
    list_filter = ('user__department',)


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('user',)
    list_filter = ('user__department',)
