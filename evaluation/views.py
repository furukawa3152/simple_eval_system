from datetime import datetime
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import (
    AchievementForm,
    AppSettingForm,
    DepartmentGoalForm,
    EvaluationForm,
    LoginForm,
    PersonalGoalForm,
)
from .models import Achievement, AppSetting, DepartmentGoal, Evaluation, PersonalGoal, User


def get_app_setting():
    setting, _ = AppSetting.objects.get_or_create(pk=1, defaults={'current_year': datetime.now().year})
    return setting


def manager_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_manager:
            messages.error(request, 'この画面は上長のみ利用できます。')
            return redirect('menu')
        return view_func(request, *args, **kwargs)

    return login_required(_wrapped)


def home(request):
    return redirect('menu' if request.user.is_authenticated else 'login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('menu')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('menu')
    return render(request, 'evaluation/login.html', {'form': form})


@login_required
def menu_view(request):
    return render(request, 'evaluation/menu.html', {'current_year': get_app_setting().current_year})


@manager_required
def year_setting_view(request):
    setting = get_app_setting()
    form = AppSettingForm(request.POST or None, instance=setting)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '現在年度を更新しました。')
        return redirect(request.path)

    context = {
        'title': '年度設定',
        'description': 'この画面で設定した年度が、すべての入力画面で使われます。',
        'form': form,
        'current_year': setting.current_year,
    }
    return render(request, 'evaluation/simple_form.html', context)


@manager_required
def dept_goal_view(request):
    current_year = get_app_setting().current_year
    instance = DepartmentGoal.objects.filter(department=request.user.department, year=current_year).first()
    form = DepartmentGoalForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        department_goal = form.save(commit=False)
        department_goal.department = request.user.department
        department_goal.year = current_year
        department_goal.save()
        messages.success(request, '部署目標を保存しました。')
        return redirect(request.path)

    context = {
        'title': '部署目標入力',
        'description': f'{request.user.department} の部署目標を管理します。',
        'form': form,
        'current_year': current_year,
    }
    return render(request, 'evaluation/simple_form.html', context)


@login_required
def my_goal_view(request):
    current_year = get_app_setting().current_year
    instance = PersonalGoal.objects.filter(user=request.user, year=current_year).first()
    department_goal = DepartmentGoal.objects.filter(department=request.user.department, year=current_year).first()
    form = PersonalGoalForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        personal_goal = form.save(commit=False)
        personal_goal.user = request.user
        personal_goal.year = current_year
        personal_goal.save()
        messages.success(request, '個人目標を保存しました。')
        return redirect(request.path)

    context = {
        'title': '個人目標入力',
        'description': '部署目標を参照しながら、自分の目標を入力します。',
        'form': form,
        'department_goal': department_goal,
        'show_goal_pairs': True,
        'current_year': current_year,
    }
    return render(request, 'evaluation/entry_form.html', context)


@login_required
def achievement_view(request):
    current_year = get_app_setting().current_year
    instance = Achievement.objects.filter(user=request.user, year=current_year).first()
    department_goal = DepartmentGoal.objects.filter(department=request.user.department, year=current_year).first()
    personal_goal = PersonalGoal.objects.filter(user=request.user, year=current_year).first()
    form = AchievementForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        achievement = form.save(commit=False)
        achievement.user = request.user
        achievement.year = current_year
        achievement.save()
        messages.success(request, '達成状況を保存しました。')
        return redirect(request.path)

    context = {
        'title': '達成状況入力',
        'description': '自分の目標に対する実績を入力します。',
        'form': form,
        'department_goal': department_goal,
        'personal_goal': personal_goal,
        'show_achievement_pairs': True,
        'current_year': current_year,
    }
    return render(request, 'evaluation/entry_form.html', context)


@manager_required
def evaluate_view(request):
    current_year = get_app_setting().current_year
    subordinates = User.objects.filter(department=request.user.department, is_manager=False).order_by('username')
    selected_user = None
    department_goal = None
    personal_goal = None
    achievement = None

    if request.method == 'POST':
        user_id = request.POST.get('user')
        if user_id:
            selected_user = subordinates.filter(pk=user_id).first()
    else:
        user_id = request.GET.get('user')
        if user_id:
            selected_user = subordinates.filter(pk=user_id).first()
        elif subordinates.exists():
            selected_user = subordinates.first()

    initial = {}
    if selected_user:
        department_goal = DepartmentGoal.objects.filter(
            department=selected_user.department,
            year=current_year,
        ).first()
        personal_goal = PersonalGoal.objects.filter(user=selected_user, year=current_year).first()
        achievement = Achievement.objects.filter(user=selected_user, year=current_year).first()
        evaluation = Evaluation.objects.filter(user=selected_user, year=current_year).first()
        if evaluation:
            initial.update(
                {
                    'user': selected_user,
                    'philosophy_eval': evaluation.philosophy_eval,
                    'finance_eval': evaluation.finance_eval,
                    'safety_eval': evaluation.safety_eval,
                    'cooperation_eval': evaluation.cooperation_eval,
                }
            )
        else:
            initial['user'] = selected_user

    form = EvaluationForm(request.POST or None, initial=initial, user_queryset=subordinates)

    if request.method == 'POST' and form.is_valid():
        evaluation_user = form.cleaned_data['user']
        Evaluation.objects.update_or_create(
            user=evaluation_user,
            year=current_year,
            defaults={
                'philosophy_eval': form.cleaned_data['philosophy_eval'],
                'finance_eval': form.cleaned_data['finance_eval'],
                'safety_eval': form.cleaned_data['safety_eval'],
                'cooperation_eval': form.cleaned_data['cooperation_eval'],
            },
        )
        messages.success(request, '評価を保存しました。')
        return redirect(f'{request.path}?user={evaluation_user.pk}')

    context = {
        'title': '評価入力',
        'description': f'{request.user.department} の部下を対象に評価を入力します。',
        'form': form,
        'no_targets': not subordinates.exists(),
        'current_year': current_year,
        'selected_user': selected_user,
        'department_goal': department_goal,
        'personal_goal': personal_goal,
        'achievement': achievement,
    }
    return render(request, 'evaluation/evaluate.html', context)
