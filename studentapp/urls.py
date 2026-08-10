from django.urls import path
from . import views

urlpatterns = [

    path('', views.admin_login, name='home'),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('api/admin/login/', views.api_admin_login, name='api_admin_login'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('colleges/', views.college_management, name='collegemanagement'),
    path('colleges/add/', views.college_add, name='college_add'),
    path('colleges/edit/<int:id>/', views.college_edit, name='college_edit'),
    path('colleges/delete/<int:id>/', views.college_delete, name='college_delete'),

    path('departments/', views.department_management, name='department_management'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/edit/<int:id>/', views.department_edit, name='department_edit'),
    path('departments/<int:id>/delete/', views.department_delete, name='department_delete'),
    path('departments/<int:id>/update/', views.department_update, name='department_update'),

    path('hods/', views.hod_management, name='hod_management'),

    path('principals/', views.principal_management, name='principal_management'),
    path('principals/add/', views.principal_add, name='principal_add'),
    path('principals/edit/<int:id>/', views.principal_edit, name='principal_edit'),
    path('principals/delete/<int:id>/', views.principal_delete, name='principal_delete'),

    path('students/', views.student_management, name='student_management'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/delete/<int:student_id>/', views.student_delete, name='student_delete'),
    path('students/update/<int:student_id>/', views.student_update, name='student_update'),
    path('student/signup/', views.student_signup, name='student_signup'),
    path('api/student/signup/', views.student_signup, name='api_student_signup'),
    path('api/student/send-otp/', views.send_otp, name='api_send_otp'),
    path('api/student/verify-otp/', views.verify_otp, name='api_verify_otp'),
    path('api/student/create-account/', views.create_student_account, name='api_create_student_account'),
    path('api/student/forgot-password/send-otp/', views.forgot_password_send_otp, name='api_forgot_password_send_otp'),
    path('api/student/forgot-password/verify-otp/', views.forgot_password_verify_otp, name='api_forgot_password_verify_otp'),
    path('api/student/forgot-password/reset/', views.forgot_password_reset, name='api_forgot_password_reset'),
    path('api/get-principal-by-college/<int:college_id>/', views.get_principal_by_college, name='get_principal_by_college'),
    path('api/get-colleges/', views.api_get_colleges, name='api_get_colleges'),

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
    path('api/admin/logout/', views.api_admin_logout, name='api_admin_logout'),
    path('search/', views.global_search, name='global_search'),

    # ================= PRINCIPAL API =================

    path('api/principal/dashboard/', views.api_principal_dashboard, name='api_principal_dashboard'),
    path('api/principal/dashboard', views.api_principal_dashboard),
    path('api/principal/students/', views.api_principal_students, name='api_principal_students'),
    path('api/principal/students', views.api_principal_students),
    path('api/principal/students/<int:student_id>/delete/', views.api_principal_student_delete, name='api_principal_student_delete'),
    path('api/principal/students/<int:student_id>/delete', views.api_principal_student_delete),
    path('api/principal/profile/', views.api_principal_profile, name='api_principal_profile'),
    path('api/principal/profile', views.api_principal_profile),
    path('api/principal/departments/', views.api_principal_departments, name='api_principal_departments'),
    path('api/principal/departments', views.api_principal_departments),
    path('api/principal/videos/', views.api_principal_videos, name='api_principal_videos'),
    path('api/principal/videos', views.api_principal_videos),
    path('api/principal/attendance_reports/', views.api_principal_attendance_reports, name='api_principal_attendance_reports'),
    path('api/principal/attendance_reports', views.api_principal_attendance_reports),
    path('api/principal/login/', views.principal_login, name='principal_login'),
    path('api/principal/login', views.principal_login),

    # ================= STUDENT API =================

    path('api/student/login/', views.student_login, name='student_login'),
    path('api/student/login', views.student_login),
    path('api/student/logout/', views.api_student_logout, name='api_student_logout'),
    path('api/student/logout', views.api_student_logout),
    path('api/student/dashboard/', views.api_student_dashboard, name='api_student_dashboard'),
    path('api/student/dashboard', views.api_student_dashboard),
    path('api/student/videos/', views.api_student_videos, name='api_student_videos'),
    path('api/student/videos', views.api_student_videos),
    path('api/student/watch-history/', views.api_student_watch_history, name='api_student_watch_history'),
    path('api/student/watch-history', views.api_student_watch_history),
    path('api/student/videos/<int:video_id>/watch/', views.api_student_record_watch, name='api_student_record_watch'),
    path('api/student/videos/<int:video_id>/watch', views.api_student_record_watch),
    path('api/student/videos/<int:video_id>/progress/', views.api_student_save_progress, name='api_student_save_progress'),
    path('api/student/videos/<int:video_id>/progress', views.api_student_save_progress),
    path('api/student/videos/<int:video_id>/stream/', views.video_stream, name='video_stream'),
    path('api/student/videos/<int:video_id>/stream', views.video_stream),
    path('api/student/watch-history/clear/', views.api_student_delete_watch_history, name='api_student_clear_watch_history'),
    path('api/student/watch-history/clear', views.api_student_delete_watch_history),
    path('api/student/watch-history/<int:history_id>/delete/', views.api_student_delete_watch_history, name='api_student_delete_watch_history_item'),
    path('api/student/watch-history/<int:history_id>/delete', views.api_student_delete_watch_history),
    path('api/student/progress/', views.api_student_progress, name='api_student_progress'),
    path('api/student/progress', views.api_student_progress),

    # ================= HOD API =================
    path("api/hod/login/", views.hod_login, name="hod_login"),
    path("api/hod/dashboard/", views.api_hod_dashboard, name="api_hod_dashboard"),
    path("api/hod/students/", views.api_hod_students, name="api_hod_students"),
    path("api/hod/videos/", views.api_hod_videos, name="api_hod_videos"),
    path("api/hod/performance/", views.api_hod_performance, name="api_hod_performance"),
    path("api/hod/profile/", views.api_hod_profile, name="api_hod_profile"),
    path("api/hod/videos/upload/", views.api_hod_video_upload, name="api_hod_video_upload"),
    path("api/hod/videos/upload/<int:video_id>/", views.api_hod_video_delete, name="api_hod_video_delete"),

    # ================= PRINCIPAL / ADMIN APPROVAL API =================
    path("api/principal/video-approvals/", views.api_principal_video_approvals, name="api_principal_video_approvals"),
    path("api/principal/videos/<int:video_id>/approve/", views.api_principal_approve_video, name="api_principal_approve_video"),
    path("api/principal/videos/<int:video_id>/reject/", views.api_principal_reject_video, name="api_principal_reject_video"),

    # ================= DJANGO ADMIN VIDEO APPROVAL HTML PAGE =================
    path("video-approval/", views.admin_video_approval, name="admin_video_approval"),
    path("admin-approval/", views.admin_video_approval),
    path("video-approval/<int:video_id>/approve/", views.admin_approve_video_action, name="admin_approve_video_action"),
    path("video-approval/<int:video_id>/reject/", views.admin_reject_video_action, name="admin_reject_video_action"),
]