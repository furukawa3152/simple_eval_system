import csv
from datetime import datetime
from functools import wraps
from io import StringIO
import time
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
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
    SettingAccessForm,
)
from .models import Achievement, AppSetting, DepartmentGoal, Evaluation, PersonalGoal, User


SETTINGS_GATE_PASSWORD = "fuck"
SETTINGS_GATE_SESSION_KEY = "settings_access_granted"
BULK_AI_TIMEOUT_SECONDS = 90


def get_app_setting():
    setting, _ = AppSetting.objects.get_or_create(pk=1, defaults={"current_year": datetime.now().year})
    return setting


AI_FIELD_CONFIG = {
    "philosophy": {
        "ai_field_name": "philosophy_eval",
        "manager_field_name": "philosophy_manager_eval",
        "score_field_name": "philosophy_score",
        "label": "理念",
        "department_attr": "philosophy",
        "personal_attr": "philosophy_goal",
        "achievement_attr": "philosophy_result",
    },
    "finance": {
        "ai_field_name": "finance_eval",
        "manager_field_name": "finance_manager_eval",
        "score_field_name": "finance_score",
        "label": "経営",
        "department_attr": "finance",
        "personal_attr": "finance_goal",
        "achievement_attr": "finance_result",
    },
    "safety": {
        "ai_field_name": "safety_eval",
        "manager_field_name": "safety_manager_eval",
        "score_field_name": "safety_score",
        "label": "安全",
        "department_attr": "safety",
        "personal_attr": "safety_goal",
        "achievement_attr": "safety_result",
    },
    "cooperation": {
        "ai_field_name": "cooperation_eval",
        "manager_field_name": "cooperation_manager_eval",
        "score_field_name": "cooperation_score",
        "label": "連携",
        "department_attr": "cooperation",
        "personal_attr": "cooperation_goal",
        "achievement_attr": "cooperation_result",
    },
}


def manager_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_manager:
            messages.error(request, "この画面は上長のみ利用できます。")
            return redirect("menu")
        return view_func(request, *args, **kwargs)

    return login_required(_wrapped)


def save_evaluation_form(form, target_user, current_year):
    return Evaluation.objects.update_or_create(
        user=target_user,
        year=current_year,
        defaults={
            "manager_note": form.cleaned_data["manager_note"],
            "philosophy_eval": form.cleaned_data["philosophy_eval"],
            "finance_eval": form.cleaned_data["finance_eval"],
            "safety_eval": form.cleaned_data["safety_eval"],
            "cooperation_eval": form.cleaned_data["cooperation_eval"],
            "philosophy_manager_eval": form.cleaned_data["philosophy_manager_eval"],
            "finance_manager_eval": form.cleaned_data["finance_manager_eval"],
            "safety_manager_eval": form.cleaned_data["safety_manager_eval"],
            "cooperation_manager_eval": form.cleaned_data["cooperation_manager_eval"],
            "philosophy_score": form.cleaned_data["philosophy_score"],
            "finance_score": form.cleaned_data["finance_score"],
            "safety_score": form.cleaned_data["safety_score"],
            "cooperation_score": form.cleaned_data["cooperation_score"],
        },
    )


def render_prompt(app_setting, *, selected_user, category_key, department_goal, personal_goal, achievement):
    config = AI_FIELD_CONFIG[category_key]
    return app_setting.ai_prompt_template.format(
        year=app_setting.current_year,
        user_name=selected_user.first_name or selected_user.username,
        department=selected_user.department,
        category=config["label"],
        department_goal=getattr(department_goal, config["department_attr"], "") if department_goal else "",
        personal_goal=getattr(personal_goal, config["personal_attr"], "") if personal_goal else "",
        achievement=getattr(achievement, config["achievement_attr"], "") if achievement else "",
    )


def populate_ai_evaluation(form_data, *, app_setting, selected_user, category_key, department_goal, personal_goal, achievement):
    config = AI_FIELD_CONFIG[category_key]
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
    form_data[config["ai_field_name"]] = generated_text
    return config


def generate_ai_text_for_category(*, app_setting, selected_user, category_key, department_goal, personal_goal, achievement):
    config = AI_FIELD_CONFIG[category_key]
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
    return config, generated_text


def home(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if request.user.require_password_change:
        return redirect("initial_password_change")
    return redirect("menu")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("initial_password_change" if request.user.require_password_change else "menu")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect("initial_password_change" if user.require_password_change else "menu")
    return render(request, "evaluation/login.html", {"form": form})


@login_required
def initial_password_change_view(request):
    if not request.user.require_password_change:
        return redirect("menu")

    form = InitialPasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        new_password = form.cleaned_data["new_password1"]
        request.user.set_password(new_password)
        request.user.require_password_change = False
        request.user.save(update_fields=["password", "require_password_change"])
        update_session_auth_hash(request, request.user)
        messages.success(request, "パスワードを変更しました。")
        return redirect("menu")

    return render(
        request,
        "evaluation/simple_form.html",
        {
            "title": "初回パスワード変更",
            "description": "初回ログインのため、新しいパスワードを設定してください。",
            "form": form,
        },
    )


@login_required
def menu_view(request):
    return render(request, "evaluation/menu.html", {"current_year": get_app_setting().current_year})


@manager_required
def export_department_csv_view(request):
    current_year = get_app_setting().current_year
    users = list(
        User.objects.filter(department=request.user.department).order_by("username")
    )

    department_goal = DepartmentGoal.objects.filter(
        department=request.user.department,
        year=current_year,
    ).first()
    personal_goals = {
        item.user_id: item
        for item in PersonalGoal.objects.filter(user__in=users, year=current_year)
    }
    achievements = {
        item.user_id: item
        for item in Achievement.objects.filter(user__in=users, year=current_year)
    }
    evaluations = {
        item.user_id: item
        for item in Evaluation.objects.filter(user__in=users, year=current_year)
    }

    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        [
            "年度",
            "部署",
            "社員ID",
            "氏名",
            "権限",
            "部署目標_理念",
            "部署目標_経営",
            "部署目標_安全",
            "部署目標_連携",
            "自由記載",
            "個人目標_理念",
            "個人目標_経営",
            "個人目標_安全",
            "個人目標_連携",
            "達成状況_理念",
            "達成状況_経営",
            "達成状況_安全",
            "達成状況_連携",
            "評価自由記載",
            "上長評価_理念",
            "上長評価_経営",
            "上長評価_安全",
            "上長評価_連携",
            "AI評価_理念",
            "AI評価_経営",
            "AI評価_安全",
            "AI評価_連携",
            "点数_理念",
            "点数_経営",
            "点数_安全",
            "点数_連携",
        ]
    )

    for user in users:
        personal_goal = personal_goals.get(user.id)
        achievement = achievements.get(user.id)
        evaluation = evaluations.get(user.id)
        full_name = f"{user.last_name}{user.first_name}".strip() or user.username

        writer.writerow(
            [
                current_year,
                user.department,
                user.username,
                full_name,
                "上長" if user.is_manager else "部下",
                department_goal.philosophy if department_goal else "",
                department_goal.finance if department_goal else "",
                department_goal.safety if department_goal else "",
                department_goal.cooperation if department_goal else "",
                personal_goal.shared_note if personal_goal else "",
                personal_goal.philosophy_goal if personal_goal else "",
                personal_goal.finance_goal if personal_goal else "",
                personal_goal.safety_goal if personal_goal else "",
                personal_goal.cooperation_goal if personal_goal else "",
                achievement.philosophy_result if achievement else "",
                achievement.finance_result if achievement else "",
                achievement.safety_result if achievement else "",
                achievement.cooperation_result if achievement else "",
                evaluation.manager_note if evaluation else "",
                evaluation.philosophy_manager_eval if evaluation else "",
                evaluation.finance_manager_eval if evaluation else "",
                evaluation.safety_manager_eval if evaluation else "",
                evaluation.cooperation_manager_eval if evaluation else "",
                evaluation.philosophy_eval if evaluation else "",
                evaluation.finance_eval if evaluation else "",
                evaluation.safety_eval if evaluation else "",
                evaluation.cooperation_eval if evaluation else "",
                evaluation.philosophy_score if evaluation and evaluation.philosophy_score is not None else "",
                evaluation.finance_score if evaluation and evaluation.finance_score is not None else "",
                evaluation.safety_score if evaluation and evaluation.safety_score is not None else "",
                evaluation.cooperation_score if evaluation and evaluation.cooperation_score is not None else "",
            ]
        )

    filename = f"{request.user.department}_{current_year}_export.csv"
    csv_bytes = output.getvalue().encode("shift_jis", errors="replace")
    response = HttpResponse(csv_bytes, content_type="text/csv; charset=shift_jis")
    response["Content-Disposition"] = (
        f'attachment; filename="department_export_{current_year}.csv"; '
        f"filename*=UTF-8''{quote(filename)}"
    )
    return response


@manager_required
def year_setting_view(request):
    if not request.session.get(SETTINGS_GATE_SESSION_KEY):
        access_form = SettingAccessForm(request.POST or None)
        if request.method == "POST" and access_form.is_valid():
            if access_form.cleaned_data["password"] == SETTINGS_GATE_PASSWORD:
                request.session[SETTINGS_GATE_SESSION_KEY] = True
                messages.success(request, "設定画面に入りました。")
                return redirect(request.path)
            messages.error(request, "設定パスワードが違います。")

        return render(
            request,
            "evaluation/simple_form.html",
            {
                "title": "設定",
                "description": "設定画面に入るには専用パスワードが必要です。",
                "form": access_form,
            },
        )

    setting = get_app_setting()
    form = AppSettingForm(request.POST or None, instance=setting)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "設定を更新しました。")
        return redirect(request.path)

    return render(
        request,
        "evaluation/simple_form.html",
        {
            "title": "設定",
            "description": "この画面で現在年度と各種設定を変更できます。",
            "form": form,
            "current_year": setting.current_year,
        },
    )


@manager_required
def dept_goal_view(request):
    current_year = get_app_setting().current_year
    instance = DepartmentGoal.objects.filter(department=request.user.department, year=current_year).first()
    form = DepartmentGoalForm(request.POST or None, instance=instance)

    if request.method == "POST" and form.is_valid():
        department_goal = form.save(commit=False)
        department_goal.department = request.user.department
        department_goal.year = current_year
        department_goal.save()
        messages.success(request, "部署目標を保存しました。")
        return redirect(request.path)

    return render(
        request,
        "evaluation/entry_form.html",
        {
            "title": "部署目標入力",
            "description": f"{request.user.department} の部署目標を入力します。",
            "form": form,
            "current_year": current_year,
            "show_department_goal_pairs": True,
        },
    )


@login_required
def my_goal_view(request):
    current_year = get_app_setting().current_year
    instance = PersonalGoal.objects.filter(user=request.user, year=current_year).first()
    department_goal = DepartmentGoal.objects.filter(department=request.user.department, year=current_year).first()
    form = PersonalGoalForm(request.POST or None, instance=instance)
    is_goal_locked = request.user.goal_input_locked

    if is_goal_locked:
        for field in form.fields.values():
            field.disabled = True

    if request.method == "POST" and is_goal_locked:
        messages.error(request, "個人目標入力は上長によりロックされています。")
        return redirect(request.path)

    if request.method == "POST" and form.is_valid():
        personal_goal = form.save(commit=False)
        personal_goal.user = request.user
        personal_goal.year = current_year
        personal_goal.save()
        messages.success(request, "個人目標を保存しました。")
        return redirect(request.path)

    return render(
        request,
        "evaluation/entry_form.html",
        {
            "title": "個人目標入力",
            "description": "部署目標を見ながら個人目標を入力します。",
            "form": form,
            "shared_note_field": form["shared_note"],
            "department_goal": department_goal,
            "show_goal_pairs": True,
            "current_year": current_year,
            "is_goal_locked": is_goal_locked,
        },
    )


@login_required
def achievement_view(request):
    current_year = get_app_setting().current_year
    instance = Achievement.objects.filter(user=request.user, year=current_year).first()
    department_goal = DepartmentGoal.objects.filter(department=request.user.department, year=current_year).first()
    personal_goal = PersonalGoal.objects.filter(user=request.user, year=current_year).first()
    initial = {"shared_note": personal_goal.shared_note} if personal_goal else None
    form = AchievementForm(request.POST or None, instance=instance, initial=initial)

    if request.method == "POST" and form.is_valid():
        achievement = form.save(commit=False)
        achievement.user = request.user
        achievement.year = current_year
        achievement.save()
        PersonalGoal.objects.update_or_create(
            user=request.user,
            year=current_year,
            defaults={"shared_note": form.cleaned_data["shared_note"]},
        )
        messages.success(request, "達成状況を保存しました。")
        return redirect(request.path)

    return render(
        request,
        "evaluation/entry_form.html",
        {
            "title": "達成状況入力",
            "description": "部署目標と個人目標を見ながら達成状況を入力します。",
            "form": form,
            "shared_note_field": form["shared_note"],
            "department_goal": department_goal,
            "personal_goal": personal_goal,
            "show_achievement_pairs": True,
            "current_year": current_year,
        },
    )


@manager_required
def evaluate_view(request):
    app_setting = get_app_setting()
    current_year = app_setting.current_year
    evaluation_targets = User.objects.filter(department=request.user.department).order_by("username")
    selected_user = None
    department_goal = None
    personal_goal = None
    achievement = None

    action = request.POST.get("action") if request.method == "POST" else ""
    current_target_user = None

    if request.method == "POST" and action == "switch_user":
        current_target_id = request.POST.get("current_target_user")
        if current_target_id:
            current_target_user = evaluation_targets.filter(pk=current_target_id).first()
            selected_user = current_target_user
    elif request.method == "POST":
        user_id = request.POST.get("user")
        if user_id:
            selected_user = evaluation_targets.filter(pk=user_id).first()
    else:
        user_id = request.GET.get("user")
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
                    "user": selected_user,
                    "manager_note": evaluation.manager_note,
                    "philosophy_eval": evaluation.philosophy_eval,
                    "finance_eval": evaluation.finance_eval,
                    "safety_eval": evaluation.safety_eval,
                    "cooperation_eval": evaluation.cooperation_eval,
                    "philosophy_manager_eval": evaluation.philosophy_manager_eval,
                    "finance_manager_eval": evaluation.finance_manager_eval,
                    "safety_manager_eval": evaluation.safety_manager_eval,
                    "cooperation_manager_eval": evaluation.cooperation_manager_eval,
                    "philosophy_score": evaluation.philosophy_score,
                    "finance_score": evaluation.finance_score,
                    "safety_score": evaluation.safety_score,
                    "cooperation_score": evaluation.cooperation_score,
                }
            )
        else:
            initial["user"] = selected_user

    form_data = request.POST.copy() if request.method == "POST" else None

    if request.method == "POST" and action == "switch_user" and current_target_user:
        form_data = request.POST.copy()
        form_data["user"] = str(current_target_user.pk)

    if request.method == "POST" and action in {"lock_goal_input", "unlock_goal_input"} and selected_user:
        selected_user.goal_input_locked = action == "lock_goal_input"
        selected_user.save(update_fields=["goal_input_locked"])
        messages.success(
            request,
            "個人目標入力をロックしました。" if selected_user.goal_input_locked else "個人目標入力のロックを解除しました。",
        )
        return redirect(f"{request.path}?user={selected_user.pk}")

    if request.method == "POST" and selected_user:
        temp_form = EvaluationForm(form_data, initial=initial, user_queryset=evaluation_targets)
        if action == "generate_ai_all" and temp_form.is_valid():
            generated_labels = []
            try:
                deadline = time.monotonic() + BULK_AI_TIMEOUT_SECONDS
                for category_key in AI_FIELD_CONFIG:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("AI一括評価がタイムアウトしました。少し時間をおいて再実行してください。")
                    config = populate_ai_evaluation(
                        form_data,
                        app_setting=app_setting,
                        selected_user=selected_user,
                        category_key=category_key,
                        department_goal=department_goal,
                        personal_goal=personal_goal,
                        achievement=achievement,
                    )
                    generated_labels.append(config["label"])
                messages.success(request, f"{' / '.join(generated_labels)} のAI評価を生成しました。")
            except Exception as error:
                messages.error(request, str(error))
        elif action.startswith("generate_ai_") and temp_form.is_valid():
            category_key = action.removeprefix("generate_ai_")
            if category_key in AI_FIELD_CONFIG:
                try:
                    config = populate_ai_evaluation(
                        form_data,
                        app_setting=app_setting,
                        selected_user=selected_user,
                        category_key=category_key,
                        department_goal=department_goal,
                        personal_goal=personal_goal,
                        achievement=achievement,
                    )
                    messages.success(request, f"{config['label']} のAI評価を生成しました。")
                except Exception as error:
                    messages.error(request, str(error))

    form = EvaluationForm(form_data or request.POST or None, initial=initial, user_queryset=evaluation_targets)

    if request.method == "POST" and action == "switch_user" and current_target_user:
        if form.is_valid():
            save_evaluation_form(form, current_target_user, current_year)
            messages.success(request, "入力途中の評価を保存しました。")
            next_user_id = request.POST.get("user")
            if next_user_id:
                return redirect(f"{request.path}?user={next_user_id}")
        else:
            messages.error(request, "保存できない入力があります。内容を確認してください。")

    if request.method == "POST" and action == "save" and form.is_valid():
        evaluation_user = form.cleaned_data["user"]
        save_evaluation_form(form, evaluation_user, current_year)
        messages.success(request, "評価を保存しました。")
        return redirect(f"{request.path}?user={evaluation_user.pk}")

    return render(
        request,
        "evaluation/evaluate.html",
        {
            "title": "評価入力",
            "description": f"{request.user.department} の対象者に評価を入力します。",
            "form": form,
            "no_targets": not evaluation_targets.exists(),
            "current_year": current_year,
            "selected_user": selected_user,
            "selected_user_goal_locked": selected_user.goal_input_locked if selected_user else False,
            "department_goal": department_goal,
            "personal_goal": personal_goal,
            "achievement": achievement,
            "ai_actions": AI_FIELD_CONFIG,
        },
    )


@manager_required
def evaluate_ai_generate_view(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "POST only"}, status=405)

    app_setting = get_app_setting()
    current_year = app_setting.current_year
    user_id = request.POST.get("user")
    category_key = request.POST.get("category")

    if not user_id or not category_key:
        return JsonResponse({"ok": False, "message": "対象ユーザーまたは項目が不足しています。"}, status=400)

    if category_key not in AI_FIELD_CONFIG:
        return JsonResponse({"ok": False, "message": "不正な評価項目です。"}, status=400)

    selected_user = User.objects.filter(pk=user_id, department=request.user.department).first()
    if not selected_user:
        return JsonResponse({"ok": False, "message": "対象ユーザーが見つかりません。"}, status=404)

    department_goal = DepartmentGoal.objects.filter(department=selected_user.department, year=current_year).first()
    personal_goal = PersonalGoal.objects.filter(user=selected_user, year=current_year).first()
    achievement = Achievement.objects.filter(user=selected_user, year=current_year).first()

    try:
        config, generated_text = generate_ai_text_for_category(
            app_setting=app_setting,
            selected_user=selected_user,
            category_key=category_key,
            department_goal=department_goal,
            personal_goal=personal_goal,
            achievement=achievement,
        )
    except Exception as error:
        return JsonResponse({"ok": False, "message": str(error)}, status=502)

    Evaluation.objects.update_or_create(
        user=selected_user,
        year=current_year,
        defaults={config["ai_field_name"]: generated_text},
    )

    return JsonResponse(
        {
            "ok": True,
            "category": category_key,
            "label": config["label"],
            "field_name": config["ai_field_name"],
            "text": generated_text,
        }
    )
