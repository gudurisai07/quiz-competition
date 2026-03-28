from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('auth/register/', views.admin_register, name='admin_register'),
    path('auth/login/', views.admin_login, name='admin_login'),
    path('auth/logout/', views.admin_logout, name='admin_logout'),
    path('register/<int:team_id>/', views.register_view, name='register_view'),
    path('presentation/', views.presentation_view, name='presentation_view'),
    path('teams/', views.teams_api, name='teams'),
    path('teams/reset_all/', views.reset_all_scores, name='reset_all_scores'),
    path('teams/<int:pk>/', views.team_detail, name='team_detail'),
    path('teams/<int:team_id>/join/', views.join_team, name='join_team'),
    path('teams/<int:team_id>/add_point/', views.add_point, name='add_point'),
    path('teams/<int:team_id>/subtract_point/', views.subtract_point, name='subtract_point'),
    path('questions/upload/', views.upload_pdf, name='upload_pdf'),
    path('questions/', views.get_questions, name='get_questions'),
    path('questions/all/delete/', views.delete_all_questions, name='delete_all_questions'),
    path('questions/<int:pk>/', views.question_detail, name='question_detail'),
    path('questions/check/', views.check_answer, name='check_answer'),
]
