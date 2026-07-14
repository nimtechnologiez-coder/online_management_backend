from django.urls import path
from . import views

urlpatterns = [


    path('', views.admin_login, name='home'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('colleges/', views.college_management, name='collegemanagement'),
    path('colleges/add/', views.college_add, name='college_add'),

    path('departments/', views.department_management, name='department_management'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/edit/<int:id>/', views.department_edit, name='department_edit'),

    path('hods/', views.hod_management, name='hod_management'),

    path('principals/', views.principal_management, name='principal_management'),
    path('principals/add/', views.principal_add, name='principal_add'),

    path('students/', views.student_management, name='student_management'),
    path('students/add/', views.student_add, name='student_add'),

    # ================= VIDEO =================

    path('videos/', views.video_management, name='video_management'),
    path('videos/add/', views.video_add, name='video_add'),
    path('videos/edit/<int:id>/', views.video_edit, name='video_edit'),
    path('videos/delete/<int:id>/', views.video_delete, name='video_delete'),

    # ========================================

    path('analytics/', views.video_analytics, name='video_analytics'),
    path('reports/', views.reports, name='reports'),
    path('users/', views.user_management, name='user_management'),
    path('settings/', views.system_settings, name='system_settings'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.user_logout, name='logout'),
]