from datetime import datetime
from functools import wraps
from pathlib import Path

from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .ai_client import generate_evaluation_text
from .forms import (
    AchievementForm,
    AppSettingForm,
    DepartmentGoalForm,
    EvaluationForm,
    InitialPasswordChangeForm,
    LoginForm,
    PersonalGoalForm,
)
from .models import Achievement, AppSetting, DepartmentGoal, Evaluation, PersonalGoal, User
from .user_sync import update_user_password_in_csv


def get_app_setting():
    setting, _ = AppSetting.objects.get_or_create(pk=1, defaults={'current_year': datetime.now().year})
    return setting


AI_FIELD_CONFIG = {
    'philosophy': {
        'ai_field_name': 'philosophy_eval',
        'manager_field_name': 'philosophy_manager_eval',
        'score_field_name': 'philosophy_score',
        'label': '理念',
        'department_attr': 'philosophy',
        'personal_attr': 'philosophy_goal',
        'achievement_attr': 'philosophy_result',
    },
    'finance': {
        'ai_field_name': 'finance_eval',
        'manager_field_name': 'finance_manager_eval',
        'score_field_name': 'finance_score',
        'label': '経営',
        'department_attr': 'finance',
        'personal_attr': 'finance_goal',
        'achievement_attr': 'finance_result',
    },
    'safety': {
        'ai_field_name': 'safety_eval',
        'manager_field_name': 'safety_manager_eval',
        'score_field_name': 'safety_score',
        'label': '安全',
        'department_attr': 'safety',
        'personal_attr': 'safety_goal',
        'achievement_attr': 'safety_result',
    },
    'cooperation': {
        'ai_field_name': 'cooperation_eval',
        'manager_field_name': 'cooperation_manager_eval',
        'score_field_name': 'cooperation_score',
        'label': '連携',
        'department_attr': 'cooperation',
        'personal_attr': 'cooperation_goal',
        'achievement_attr': 'cooperation_result',
    },
}


def save_evaluation_form(form, target_user, current_year):
    return Evaluation.objects.update_or_create(
        user=target_user,
        year=current_year,
        defaults={
            'philosophy_eval': form.cleaned_data['philosophy_eval'],
            'finance_eval': form.cleaned_data['finance_eval'],
            'safety_eval': form.cleaned_data['safety_eval'],
            'cooperation_eval': form.cleaned_data['cooperation_eval'],
            'philosophy_manager_eval': form.cleaned_data['philosophy_manager_eval'],
            'finance_manager_eval': form.cleaned_data['finance_manager_eval'],
            'safety_manager_eval': form.cleaned_data['safety_manager_eval'],
            'cooperation_manager_eval': form.cleaned_data['cooperation_manager_eval'],
            'philosophy_score': form.cleaned_data['philosophy_score'],
            'finance_score': form.cleaned_data['finance_score'],
            'safety_score': form.cleaned_data['safety_score'],
            'cooperation_score': form.cleaned_data['cooperation_score'],
        },
    )


def render_prompt(app_setting, *, selected_user, category_key, department_goal, personal_goal, achievement):
    config = AI_FIELD_CONFIG[category_key]
    return app_setting.ai_prompt_template.format(
        year=app_setting.current_year,
        user_name=selected_user.first_name or selected_user.username,
        department=selected_user.department,
        category=config['label'],
        department_goal=getattr(department_goal, config['department_attr'], '') if department_goal else '',
        personal_goal=getattr(personal_goal, config['personal_attr'], '') if personal_goal else '',
        achievement=getattr(achievement, config['achievement_attr'], '') if achievement else '',
    )


def manager_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_manager:
            messages.error(request, 'この画面は上長のみ利用できます。')
            return redirect('menu')
        return view_func(request, *args, **kwargs)

    return login_required(_wrapped)


def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.require_password_change:
        return redirect('initial_password_change')
    return redirect('menu')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('initial_password_change' if request.user.require_password_change else 'menu')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('initial_password_change' if user.require_password_change else 'menu')
    return render(request, 'evaluation/login.html', {'form': form})


@login_required
def initial_password_change_view(request):
    if not request.user.require_password_change:
        return redirect('menu')

    form = InitialPasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        new_password = form.cleaned_data['new_password1']
        csv_path = Path(settings.BASE_DIR) / 'users.csv'
        update_user_password_in_csv(csv_path, request.user.username, new_password, require_password_change=False)
        request.user.set_password(new_password)
        request.user.require_password_change = False
        request.user.save(update_fields=['password', 'require_password_change'])
        update_session_auth_hash(request, request.user)
        messages.success(request, 'パスワードを変更しました。')
        return redirect('menu')

    context = {
        'title': '初回パスワード変更',
        'description': '初回ログインのため、新しいパスワードを設定してください。',
        'form': form,
    }
    return render(request, 'evaluation/simple_form.html', context)


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
    app_setting = get_app_setting()
    current_year = app_setting.current_year
    evaluation_targets = User.objects.filter(department=request.user.department).order_by('username')
    selected_user = None
    department_goal = None
    personal_goal = None
    achievement = None

    action = request.POST.get('action') if request.method == 'POST' else ''
    current_target_user = None

    if request.method == 'POST' and action == 'switch_user':
        current_target_id = request.POST.get('current_target_user')
        if current_target_id:
            current_target_user = evaluation_targets.filter(pk=current_target_id).first()
            selected_user = current_target_user
    elif request.method == 'POST':
        user_id = request.POST.get('user')
        if user_id:
            selected_user = evaluation_targets.filter(pk=user_id).first()
    else:
        user_id = request.GET.get('user')
        if user_id:
            selected_user = evaluation_targets.filter(pk=user_id).first()
        elif evaluation_targets.exists():
            selected_user = evaluation_targets.first()

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
                    'philosophy_manager_eval': evaluation.philosophy_manager_eval,
                    'finance_manager_eval': evaluation.finance_manager_eval,
                    'safety_manager_eval': evaluation.safety_manager_eval,
                    'cooperation_manager_eval': evaluation.cooperation_manager_eval,
                    'philosophy_score': evaluation.philosophy_score,
                    'finance_score': evaluation.finance_score,
                    'safety_score': evaluation.safety_score,
                    'cooperation_score': evaluation.cooperation_score,
                }
            )
        else:
            initial['user'] = selected_user

    form_data = request.POST.copy() if request.method == 'POST' else None

    if request.method == 'POST' and action == 'switch_user' and current_target_user:
        form_data = request.POST.copy()
        form_data['user'] = str(current_target_user.pk)

    if action.startswith('generate_ai_') and selected_user:
        category_key = action.removeprefix('generate_ai_')
        config = AI_FIELD_CONFIG.get(category_key)
        temp_form = EvaluationForm(form_data, initial=initial, user_queryset=evaluation_targets)
        if config and temp_form.is_valid():
            try:
                prompt = render_prompt(
                    app_setting,
                    selected_user=selected_user,
                    category_key=category_key,
                    department_goal=department_goal,
                    personal_goal=personal_goal,
                    achievement=achievement,
                )
                generated_text = generate_evaluation_text(
                    endpoint=app_setting.ai_endpoint,
                    model=app_setting.ai_model,
                    prompt=prompt,
                )
                form_data[config['ai_field_name']] = generated_text
                messages.success(request, f"{config['label']}のAI評価を生成しました。")
            except Exception as error:
                messages.error(request, str(error))

    form = EvaluationForm(form_data or request.POST or None, initial=initial, user_queryset=evaluation_targets)

    if request.method == 'POST' and action == 'switch_user' and current_target_user:
        if form.is_valid():
            save_evaluation_form(form, current_target_user, current_year)
            messages.success(request, '入力途中の評価を保存しました。')
            next_user_id = request.POST.get('user')
            if next_user_id:
                return redirect(f'{request.path}?user={next_user_id}')
        else:
            messages.error(request, '保存できない入力があります。内容を確認してください。')

    if request.method == 'POST' and action == 'save' and form.is_valid():
        evaluation_user = form.cleaned_data['user']
        save_evaluation_form(form, evaluation_user, current_year)
        messages.success(request, '評価を保存しました。')
        return redirect(f'{request.path}?user={evaluation_user.pk}')

    context = {
        'title': '評価入力',
        'description': f'{request.user.department} の対象者に評価を入力します。',
        'form': form,
        'no_targets': not evaluation_targets.exists(),
        'current_year': current_year,
        'selected_user': selected_user,
        'department_goal': department_goal,
        'personal_goal': personal_goal,
        'achievement': achievement,
        'ai_actions': AI_FIELD_CONFIG,
    }
    return render(request, 'evaluation/evaluate.html', context)
