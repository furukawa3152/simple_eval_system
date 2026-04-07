from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import SetPasswordForm

from .models import Achievement, AppSetting, DepartmentGoal, PersonalGoal, User


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='社員ID')
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput)


class InitialPasswordChangeForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label='新しいパスワード',
        widget=forms.PasswordInput,
    )
    new_password2 = forms.CharField(
        label='新しいパスワード（確認）',
        widget=forms.PasswordInput,
    )


class AppSettingForm(forms.ModelForm):
    class Meta:
        model = AppSetting
        fields = ['current_year']
        labels = {'current_year': '現在年度'}


class DepartmentGoalForm(forms.ModelForm):
    class Meta:
        model = DepartmentGoal
        fields = ['philosophy', 'finance', 'safety', 'cooperation']
        labels = {
            'philosophy': '理念',
            'finance': '経営',
            'safety': '安全',
            'cooperation': '連携',
        }
        widgets = {
            'philosophy': forms.Textarea(attrs={'rows': 4}),
            'finance': forms.Textarea(attrs={'rows': 4}),
            'safety': forms.Textarea(attrs={'rows': 4}),
            'cooperation': forms.Textarea(attrs={'rows': 4}),
        }


class PersonalGoalForm(forms.ModelForm):
    class Meta:
        model = PersonalGoal
        fields = ['philosophy_goal', 'finance_goal', 'safety_goal', 'cooperation_goal']
        labels = {
            'philosophy_goal': '理念目標',
            'finance_goal': '経営目標',
            'safety_goal': '安全目標',
            'cooperation_goal': '連携目標',
        }
        widgets = {
            'philosophy_goal': forms.Textarea(attrs={'rows': 6}),
            'finance_goal': forms.Textarea(attrs={'rows': 6}),
            'safety_goal': forms.Textarea(attrs={'rows': 6}),
            'cooperation_goal': forms.Textarea(attrs={'rows': 6}),
        }


class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ['philosophy_result', 'finance_result', 'safety_result', 'cooperation_result']
        labels = {
            'philosophy_result': '理念達成',
            'finance_result': '経営達成',
            'safety_result': '安全達成',
            'cooperation_result': '連携達成',
        }
        widgets = {
            'philosophy_result': forms.Textarea(attrs={'rows': 4}),
            'finance_result': forms.Textarea(attrs={'rows': 4}),
            'safety_result': forms.Textarea(attrs={'rows': 4}),
            'cooperation_result': forms.Textarea(attrs={'rows': 4}),
        }


class EvaluationForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.none(), label='評価対象')
    philosophy_eval = forms.CharField(label='理念評価', required=False, widget=forms.Textarea(attrs={'rows': 4}))
    finance_eval = forms.CharField(label='経営評価', required=False, widget=forms.Textarea(attrs={'rows': 4}))
    safety_eval = forms.CharField(label='安全評価', required=False, widget=forms.Textarea(attrs={'rows': 4}))
    cooperation_eval = forms.CharField(label='連携評価', required=False, widget=forms.Textarea(attrs={'rows': 4}))

    def __init__(self, *args, user_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = user_queryset if user_queryset is not None else User.objects.none()
