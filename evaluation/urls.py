from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('initial_password_change/', views.initial_password_change_view, name='initial_password_change'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('menu/', views.menu_view, name='menu'),
    path('year_setting/', views.year_setting_view, name='year_setting'),
    path('dept_goal/', views.dept_goal_view, name='dept_goal'),
    path('my_goal/', views.my_goal_view, name='my_goal'),
    path('achievement/', views.achievement_view, name='achievement'),
    path('evaluate/', views.evaluate_view, name='evaluate'),
]
