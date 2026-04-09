from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    department = models.CharField(max_length=100, verbose_name="部署")
    is_manager = models.BooleanField(default=False, verbose_name="上長フラグ")
    require_password_change = models.BooleanField(default=True, verbose_name="初回パスワード変更")
    goal_input_locked = models.BooleanField(default=False, verbose_name="目標入力ロック")

    def __str__(self):
        return f"{self.username} {self.last_name}{self.first_name}".strip()


class AppSetting(models.Model):
    current_year = models.IntegerField(verbose_name="現在年度")
    ai_endpoint = models.URLField(
        default="http://172.16.98.16:8080/generate",
        verbose_name="AIエンドポイント",
    )
    ai_model = models.CharField(
        max_length=200,
        default="gemini-3.1-flash-preview",
        verbose_name="AIモデル名",
    )
    ai_prompt_template = models.TextField(
        default=(
            "あなたは人事評価支援AIです。以下の情報を読み、{category}の達成度合いを日本語で評価してください。\n"
            "100〜200字程度で、達成状況の要約、良い点、今後の課題がわかるように記述してください。\n\n"
            "年度: {year}\n"
            "対象者: {user_name}\n"
            "部署: {department}\n"
            "項目: {category}\n"
            "部署目標: {department_goal}\n"
            "個人目標: {personal_goal}\n"
            "達成状況: {achievement}\n"
        ),
        verbose_name="AI評価プロンプト",
    )

    class Meta:
        verbose_name = "年度設定"
        verbose_name_plural = "年度設定"

    def __str__(self):
        return f"現在年度: {self.current_year}"


class DepartmentGoal(models.Model):
    department = models.CharField(max_length=100, verbose_name="部署")
    year = models.IntegerField(verbose_name="年度")
    philosophy = models.TextField(blank=True, verbose_name="理念")
    finance = models.TextField(blank=True, verbose_name="経営")
    safety = models.TextField(blank=True, verbose_name="安全")
    cooperation = models.TextField(blank=True, verbose_name="連携")

    class Meta:
        ordering = ["-year", "department"]
        constraints = [
            models.UniqueConstraint(fields=["department", "year"], name="unique_department_goal_again")
        ]

    def __str__(self):
        return f"{self.department} / {self.year}"


class PersonalGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="personal_goals")
    year = models.IntegerField(verbose_name="年度")
    shared_note = models.CharField(max_length=400, blank=True, verbose_name="自由記載")
    philosophy_goal = models.TextField(blank=True, verbose_name="理念目標")
    finance_goal = models.TextField(blank=True, verbose_name="経営目標")
    safety_goal = models.TextField(blank=True, verbose_name="安全目標")
    cooperation_goal = models.TextField(blank=True, verbose_name="連携目標")

    class Meta:
        ordering = ["-year", "user__username"]
        constraints = [
            models.UniqueConstraint(fields=["user", "year"], name="unique_personal_goal_again")
        ]

    def __str__(self):
        return f"{self.user} / {self.year}"


class Achievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="achievements")
    year = models.IntegerField(verbose_name="年度")
    philosophy_result = models.TextField(blank=True, verbose_name="理念達成")
    finance_result = models.TextField(blank=True, verbose_name="経営達成")
    safety_result = models.TextField(blank=True, verbose_name="安全達成")
    cooperation_result = models.TextField(blank=True, verbose_name="連携達成")

    class Meta:
        ordering = ["-year", "user__username"]
        constraints = [
            models.UniqueConstraint(fields=["user", "year"], name="unique_achievement_again")
        ]

    def __str__(self):
        return f"{self.user} / {self.year}"


class Evaluation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="evaluations")
    year = models.IntegerField(verbose_name="年度")
    philosophy_eval = models.TextField(blank=True, verbose_name="理念AI評価")
    finance_eval = models.TextField(blank=True, verbose_name="経営AI評価")
    safety_eval = models.TextField(blank=True, verbose_name="安全AI評価")
    cooperation_eval = models.TextField(blank=True, verbose_name="連携AI評価")
    philosophy_manager_eval = models.TextField(blank=True, verbose_name="理念上長評価")
    finance_manager_eval = models.TextField(blank=True, verbose_name="経営上長評価")
    safety_manager_eval = models.TextField(blank=True, verbose_name="安全上長評価")
    cooperation_manager_eval = models.TextField(blank=True, verbose_name="連携上長評価")
    philosophy_score = models.PositiveIntegerField(blank=True, null=True, verbose_name="理念点数")
    finance_score = models.PositiveIntegerField(blank=True, null=True, verbose_name="経営点数")
    safety_score = models.PositiveIntegerField(blank=True, null=True, verbose_name="安全点数")
    cooperation_score = models.PositiveIntegerField(blank=True, null=True, verbose_name="連携点数")

    class Meta:
        ordering = ["-year", "user__username"]
        constraints = [
            models.UniqueConstraint(fields=["user", "year"], name="unique_evaluation_again")
        ]

    def __str__(self):
        return f"{self.user} / {self.year}"
