from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth
from datetime import timedelta
import json

from .models import (
    College,
    Principal,
    Department,
    Student,
    Video,
    VideoWatch,
)


def dashboard(request):
    today = timezone.now().date()

    # ==========================
    # Dashboard Statistics
    # ==========================

    total_colleges = College.objects.count()
    total_principals = Principal.objects.count()
    total_hods = Department.objects.count()
    total_students = Student.objects.count()
    total_videos = Video.objects.count()

    active_students = Student.objects.filter(
        status="active"
    ).count()

    today_views = VideoWatch.objects.filter(
        watched_at__date=today
    ).count()

    recent_videos = Video.objects.order_by("-uploaded_at")[:5]
    top_videos = Video.objects.order_by("-views")[:5]

    top_colleges = (
        College.objects.annotate(
            total_students=Count("students")
        ).order_by("-total_students")[:5]
    )

    # ==========================
    # Weekly Chart (Last 7 Days)
    # ==========================

    week_labels = []
    week_data = []

    for i in range(6, -1, -1):

        day = today - timedelta(days=i)

        week_labels.append(day.strftime("%a"))

        count = VideoWatch.objects.filter(
            watched_at__date=day
        ).count()

        week_data.append(count)

    # ==========================
    # Monthly Chart (Last 6 Months)
    # ==========================

    monthly = (
        VideoWatch.objects
        .annotate(month=TruncMonth("watched_at"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    month_labels = []
    month_data = []

    for item in monthly:
        month_labels.append(item["month"].strftime("%b"))
        month_data.append(item["total"])

    # ==========================
    # College-wise Chart
    # ==========================

    college_labels = []
    college_data = []

    for college in College.objects.all():

        total_views = VideoWatch.objects.filter(
            student__college=college
        ).count()

        college_labels.append(college.college_name)
        college_data.append(total_views)

    # ==========================
    # Context
    # ==========================

    context = {
        "total_colleges": total_colleges,
        "total_principals": total_principals,
        "total_hods": total_hods,
        "total_students": total_students,
        "total_videos": total_videos,
        "today_views": today_views,
        "active_students": active_students,

        "recent_videos": recent_videos,
        "top_videos": top_videos,
        "top_colleges": top_colleges,

        "week_labels": json.dumps(week_labels),
        "week_data": json.dumps(week_data),

        "month_labels": json.dumps(month_labels),
        "month_data": json.dumps(month_data),

        "college_labels": json.dumps(college_labels),
        "college_data": json.dumps(college_data),
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )

def admin_login(request):
    return render(request, "login/login.html")



def college_management(request):
    return render(request, 'collegemanagement/collegelist.html')

def college_add(request):
    return render(request, 'collegemanagement/add_college.html')


def department_management(request):
    return render(request, 'department/department_list.html')

def department_add(request):
    return render(request, 'department/add_department.html')

def department_edit(request, id):
    return render(request, 'department/edit_department.html', {'department_id': id})

def hod_management(request):
    return render(request, 'dashboard/hod_management.html')

def principal_management(request):
    return render(request, 'Principalmanagement/Principalmanagement.html')

def principal_add(request):
    return render(request, 'Principalmanagement/add_principal.html')

def student_management(request):
    return render(request, 'studentmanagement/studentmanagement.html')

def student_add(request):
    return render(request, 'studentmanagement/add_student.html')

def video_management(request):
    return render(request, "videomanagement/video_management.html")


def video_add(request):
    return render(request, "videomanagement/video_add.html")


def video_edit(request, id):
    return render(request, "video_edit.html")


def video_delete(request, id):
    return render(request, "video_delete.html")

def video_analytics(request):
    return render(request, 'videoanalytics/video_analytics.html')

def reports(request):
    return render(request, 'reportmanagement/report_management.html')

def user_management(request):
    return render(request, 'usermanagement/user_management.html')

def system_settings(request):
    return render(request, 'dashboard/system_settings.html')

def profile(request):
    return render(request, 'dashboard/profile.html')

def user_logout(request):
    # Add actual logout logic later
    return redirect('dashboard')
