from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Achievement, DepartmentGoal, Evaluation, PersonalGoal, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('追加情報', {'fields': ('department', 'is_manager')}),
    )
    list_display = ('username', 'first_name', 'last_name', 'department', 'is_manager', 'is_staff', 'is_active')
    list_filter = ('department', 'is_manager', 'is_staff', 'is_active')
    readonly_fields = ('username', 'first_name', 'last_name', 'department', 'is_manager', 'is_staff', 'is_active')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff


@admin.register(DepartmentGoal)
class DepartmentGoalAdmin(admin.ModelAdmin):
    list_display = ('department', 'year')
    list_filter = ('department', 'year')


@admin.register(PersonalGoal)
class PersonalGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'year')
    list_filter = ('user__department', 'year')


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'year')
    list_filter = ('user__department', 'year')


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('user', 'year')
    list_filter = ('user__department', 'year')
