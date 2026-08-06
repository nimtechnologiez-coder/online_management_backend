import calendar
import json
import random
import string
from datetime import date, timedelta


def _format_time_ago(value):
    if not value:
        return "just now"

    diff = timezone.now() - value
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return "just now"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} min ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hr ago"

    days = seconds // 86400
    return f"{days} day ago"

from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum, Max
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from .models import (
    College,
    Department,
    Principal,
    Student,
    Video,
    VideoWatch,
)

def dashboard(request):

    today = timezone.now().date()
    now = timezone.now()

    # ------------------------------------------
    # Chart Filter
    # ------------------------------------------

    period = request.GET.get("period", "week")

    # ------------------------------------------
    # Dashboard Statistics
    # ------------------------------------------

    total_colleges = College.objects.count()
    total_principals = Principal.objects.count()
    total_departments = Department.objects.count()
    total_students = Student.objects.count()
    total_videos = Video.objects.count()

    active_students = Student.objects.filter(
        status="active"
    ).count()

    # ------------------------------------------
    # Today's Student Engagement
    # ------------------------------------------

    today_active_students = (
        VideoWatch.objects.filter(
            watched_at__date=today
        )
        .values("student")
        .distinct()
        .count()
    )

    today_percentage = (
        round(
            (today_active_students / total_students) * 100,
            2,
        )
        if total_students
        else 0
    )

    # ------------------------------------------
    # Current Month Student Engagement
    # ------------------------------------------

    month_active_students = (
        VideoWatch.objects.filter(
            watched_at__year=now.year,
            watched_at__month=now.month,
        )
        .values("student")
        .distinct()
        .count()
    )

    month_percentage = (
        round(
            (month_active_students / total_students) * 100,
            2,
        )
        if total_students
        else 0
    )

    # ------------------------------------------
    # Recent Videos (latest 5)
    # ------------------------------------------

    recent_videos = Video.objects.order_by(
        "-uploaded_at"
    )[:5]

    # ------------------------------------------
    # Top Videos – Most Watched this Week (5 items)
    # ------------------------------------------

    week_start = today - timedelta(days=today.weekday())   # Monday
    week_end   = week_start + timedelta(days=6)            # Sunday

    top_videos = (
        Video.objects.annotate(
            total_views=Count(
                "watch_history",
                filter=Q(
                    watch_history__watched_at__date__range=(week_start, week_end),
                ),
            )
        )
        .order_by("-total_views")[:5]
    )
        # ==========================================
    # Top Colleges
    # ==========================================

    top_colleges = []

    for college in College.objects.all():

        college_students = Student.objects.filter(
            college=college
        ).count()

        active_students = (
            VideoWatch.objects.filter(
                watched_at__date__range=(week_start, week_end),
                student__college=college
            )
            .values("student")
            .distinct()
            .count()
        )

        percentage = (
            round(
                (active_students / college_students) * 100,
                2
            )
            if college_students
            else 0
        )

        top_colleges.append({
            "college": college,
            "students": college_students,
            "active_students": active_students,
            "percentage": percentage,
        })

    top_colleges = sorted(
        top_colleges,
        key=lambda x: (
            x["percentage"],
            x["active_students"]
        ),
        reverse=True
    )[:5]

    # ==========================================
    # Dynamic Chart Data
    # ==========================================

    chart_labels = []
    chart_data = []

    # ---------- This Week ----------
    if period == "week":

        for i in range(3, -1, -1):

            end_date = today - timedelta(days=i * 7)
            start_date = end_date - timedelta(days=6)

            active = (
                VideoWatch.objects.filter(
                    watched_at__date__range=(
                        start_date,
                        end_date
                    )
                )
                .values("student")
                .distinct()
                .count()
            )

            percentage = (
                round(
                    (active / total_students) * 100,
                    2
                )
                if total_students
                else 0
            )

            chart_labels.append(f"Week {4-i}")
            chart_data.append(percentage)

    # ---------- Last 3 Months ----------
    elif period == "3months":

        for i in range(2, -1, -1):

            month = now.month - i
            year = now.year

            while month <= 0:
                month += 12
                year -= 1

            active = (
                VideoWatch.objects.filter(
                    watched_at__year=year,
                    watched_at__month=month
                )
                .values("student")
                .distinct()
                .count()
            )

            percentage = (
                round(
                    (active / total_students) * 100,
                    2
                )
                if total_students
                else 0
            )

            chart_labels.append(
                calendar.month_abbr[month]
            )

            chart_data.append(
                percentage
            )

    # ---------- Last 6 Months ----------
    else:

        for i in range(5, -1, -1):

            month = now.month - i
            year = now.year

            while month <= 0:
                month += 12
                year -= 1

            active = (
                VideoWatch.objects.filter(
                    watched_at__year=year,
                    watched_at__month=month
                )
                .values("student")
                .distinct()
                .count()
            )

            percentage = (
                round(
                    (active / total_students) * 100,
                    2
                )
                if total_students
                else 0
            )

            chart_labels.append(
                calendar.month_abbr[month]
            )

            chart_data.append(
                percentage
            )

    # ==========================================
    # Monthly Analytics Data (Last 6 Months)
    # ==========================================
    monthly_labels = []
    monthly_data = []

    for i in range(5, -1, -1):
        month = now.month - i
        year = now.year
        while month <= 0:
            month += 12
            year -= 1

        active = (
            VideoWatch.objects.filter(
                watched_at__year=year,
                watched_at__month=month
            )
            .values("student")
            .distinct()
            .count()
        )

        percentage = (
            round((active / total_students) * 100, 2)
            if total_students
            else 0
        )

        monthly_labels.append(calendar.month_abbr[month])
        monthly_data.append(percentage)
    # College Distribution
    # ==========================================

    college_labels = []
    college_data = []

    total_active_students = (
        VideoWatch.objects
        .values("student")
        .distinct()
        .count()
    )

    for college in College.objects.all():

        active_students = (
            VideoWatch.objects.filter(
                student__college=college
            )
            .values("student")
            .distinct()
            .count()
        )

        percentage = (
            round(
                (active_students / total_active_students) * 100,
                2
            )
            if total_active_students
            else 0
        )

        college_labels.append(
            college.college_name
        )

        college_data.append(
            percentage
        )

    # ==========================================
    # Dynamic Recent Activity Logic
    # ==========================================

    recent_activities = []

    # 1. Colleges
    for c in College.objects.order_by("-created_at")[:5]:
        if c.created_at:
            recent_activities.append({
                "title": "New College Registered",
                "description": c.college_name,
                "timestamp": c.created_at,
                "icon": "fas fa-university",
                "dot_class": "dot-blue",
                "badge": "College"
            })

    # 2. Students
    for s in Student.objects.order_by("-created_at")[:5]:
        if s.created_at:
            college_title = s.college.college_name if s.college else "System"
            recent_activities.append({
                "title": "Student Enrolled",
                "description": f"{s.full_name} ({college_title})",
                "timestamp": s.created_at,
                "icon": "fas fa-user-graduate",
                "dot_class": "dot-purple",
                "badge": "Student"
            })

    # 3. Departments
    for d in Department.objects.order_by("-created_at")[:5]:
        if d.created_at:
            college_title = d.college.college_name if d.college else "System"
            recent_activities.append({
                "title": "Department Created",
                "description": f"{d.dept_name} ({college_title})",
                "timestamp": d.created_at,
                "icon": "fas fa-sitemap",
                "dot_class": "dot-green",
                "badge": "Department"
            })

    # 4. Videos Uploaded
    for v in Video.objects.order_by("-uploaded_at")[:5]:
        if v.uploaded_at:
            recent_activities.append({
                "title": "New Video Uploaded",
                "description": v.title,
                "timestamp": v.uploaded_at,
                "icon": "fas fa-video",
                "dot_class": "dot-pink",
                "badge": "Video"
            })

    # 5. Video Watches
    for w in VideoWatch.objects.order_by("-watched_at")[:5]:
        if w.watched_at:
            recent_activities.append({
                "title": "Video Watched",
                "description": f"{w.student.full_name} watched '{w.video.title}'",
                "timestamp": w.watched_at,
                "icon": "fas fa-play-circle",
                "dot_class": "dot-orange",
                "badge": "Watch"
            })

    recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_activities = recent_activities[:5]

    # ==========================================
    # Department & Category Breakdown (Replaces System Overview)
    # ==========================================

    dept_distribution = []
    if total_students > 0:
        depts = Department.objects.annotate(student_count=Count("students")).order_by("-student_count")[:5]
        for d in depts:
            pct = round((d.student_count / total_students) * 100, 1)
            dept_distribution.append({
                "dept_name": d.dept_name,
                "dept_code": d.dept_code,
                "student_count": d.student_count,
                "percentage": pct,
            })

    video_categories = list(Video.objects.values("category").annotate(count=Count("id")).order_by("-count")[:4])

    # ==========================================
    # Monthly Activities
    # ==========================================

    monthly_activities = (
        VideoWatch.objects
        .annotate(
            month=TruncMonth("watched_at")
        )
        .values("month")
        .annotate(
            active_students=Count(
                "student",
                distinct=True
            ),
            videos_watched=Count(
                "video",
                distinct=True
            ),
            total_views=Count("id")
        )
        .order_by("-month")[:6]
    )

    # ==========================================
    # Context
    # ==========================================

    context = {

        # Dashboard Cards
        "total_colleges": total_colleges,
        "total_principals": total_principals,
        "total_departments": total_departments,
        "total_students": total_students,
        "total_videos": total_videos,

        "active_students": active_students,
        "today_active_students": today_active_students,
        "month_active_students": month_active_students,

        "today_percentage": today_percentage,
        "month_percentage": month_percentage,

        # Lists & Activity
        "recent_videos": recent_videos,
        "top_videos": top_videos,
        "top_colleges": top_colleges,
        "monthly_activities": monthly_activities,
        "recent_activities": recent_activities,
        "dept_distribution": dept_distribution,
        "video_categories": video_categories,

        # Dynamic Chart
        "chart_labels": json.dumps(chart_labels),
        "chart_data": json.dumps(chart_data),
        "monthly_labels": json.dumps(monthly_labels),
        "monthly_data": json.dumps(monthly_data),

        # College Distribution
        "college_labels": json.dumps(college_labels),
        "college_data": json.dumps(college_data),

        # Selected Dropdown Value
        "selected_period": period,

        "now": now,

        # Weekly range (for Most Watched Videos label)
        "week_start": week_start,
        "week_end": week_end,
    }

    # ==========================================
    # Render
    # ==========================================

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )



from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

def admin_login(request):
    if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff):
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        remember = request.POST.get("remember")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_superuser or user.is_staff:
                login(request, user)
                if remember:
                    request.session.set_expiry(86400)  # Session automatically expires after 1 day (24 hours)
                else:
                    request.session.set_expiry(0)      # Expire session on browser/tab close or 1 day max
                return redirect("dashboard")
            else:
                messages.error(request, "Only Admin can login.")
        else:
            messages.error(request, "Invalid Username or Password.")

    return render(request, "login/login.html")


@csrf_exempt
def api_admin_login(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
        username = data.get("username") or request.POST.get("username")
        password = data.get("password") or request.POST.get("password")
    except Exception:
        username = request.POST.get("username")
        password = request.POST.get("password")

    if not username or not password:
        return JsonResponse({"status": "error", "message": "Username and password required."}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is not None:
        if user.is_superuser or user.is_staff:
            login(request, user)
            return JsonResponse({
                "status": "success",
                "message": "Admin login successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_superuser": user.is_superuser,
                    "is_staff": user.is_staff,
                }
            })
        else:
            return JsonResponse({"status": "error", "message": "Only Admin can login."}, status=403)
    else:
        return JsonResponse({"status": "error", "message": "Invalid Username or Password."}, status=401)




from django.shortcuts import render, redirect, get_object_or_404
from .models import College
from django.core.paginator import Paginator

def college_management(request):
    college_list = College.objects.all().order_by("-id")

    paginator = Paginator(college_list, 10)   # 10 records per page

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    page_range = list(paginator.get_elided_page_range(page_obj.number))

    return render(request, "collegemanagement/collegelist.html", {
        "page_obj": page_obj,
        "colleges": page_obj.object_list,
        "page_range": page_range,
        "states": College.STATE_CHOICES,
        "state_districts_json": json.dumps(College.STATE_DISTRICTS),
    })


def college_add(request):
    base_context = {
        'states': College.STATE_CHOICES,
        'state_districts_json': json.dumps(College.STATE_DISTRICTS),
    }

    if request.method == "POST":
        college_code = request.POST.get('college_code')
        college_name = request.POST.get('college_name')
        university = request.POST.get('university')
        college_type = request.POST.get('college_type')
        college_stream = request.POST.get('college_stream', 'other')
        status = request.POST.get('status', 'active')
        state = request.POST.get('state')
        district = request.POST.get('district')
        address = request.POST.get('address')
        contact_email = request.POST.get('college_email')
        contact_phone = request.POST.get('college_phone')
        website = request.POST.get('website')
        college_logo = request.FILES.get('college_logo')
        principal_name = request.POST.get('principal_name')
        principal_email = request.POST.get('principal_email')
        principal_mobile = request.POST.get('principal_mobile')
        principal_status = request.POST.get('principal_status', 'active')

        if college_name:
            if principal_email and Principal.objects.filter(principal_email=principal_email).exists():
                return render(request, 'collegemanagement/add_college.html', {
                    **base_context,
                    'error': f'A Principal with email "{principal_email}" already exists. Please use a different email.',
                })

            college = College.objects.create(
                college_code=college_code,
                college_name=college_name,
                university=university,
                college_type=college_type,
                college_stream=college_stream,
                status=status,
                state=state,
                district=district,
                address=address,
                contact_email=contact_email,
                contact_phone=contact_phone,
                website=website,
                college_logo=college_logo
            )

            if principal_name and principal_email:
                import string
                import random

                # Generate unique username
                base_college = college.college_name[:3].upper().replace(" ", "")
                username = f"{base_college}_PR_{random.randint(100, 999)}"
                while Principal.objects.filter(username=username).exists():
                    username = f"{base_college}_PR_{random.randint(100, 999)}"

                # Generate random password
                chars = string.ascii_letters + string.digits + "!@#$%^&*"
                password = ''.join(random.choices(chars, k=10))

                Principal.objects.create(
                    college=college,
                    principal_name=principal_name,
                    principal_email=principal_email,
                    principal_mobile=principal_mobile,
                    status=principal_status,
                    username=username,
                    password=password
                )

            return redirect('collegemanagement')

    return render(request, 'collegemanagement/add_college.html', base_context)


def college_edit(request, id):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Method not allowed.'}, status=405)

    college = get_object_or_404(College, id=id)
    college.college_code = request.POST.get('college_code', college.college_code)
    college.college_name = request.POST.get('college_name', college.college_name)
    college.university = request.POST.get('university', college.university)
    college.college_type = request.POST.get('college_type', college.college_type)
    college.college_stream = request.POST.get('college_stream', college.college_stream or 'other')
    college.status = request.POST.get('status', college.status)
    college.state = request.POST.get('state', college.state)
    college.district = request.POST.get('district', college.district)
    college.address = request.POST.get('address', college.address)
    college.contact_email = request.POST.get('contact_email', college.contact_email)
    college.contact_phone = request.POST.get('contact_phone', college.contact_phone)
    college.website = request.POST.get('website', college.website)
    college.save()

    return JsonResponse({'status': 'success', 'message': 'College updated successfully.'})


def college_delete(request, id):
    if request.method == "POST":
        college = get_object_or_404(College, id=id)
        college.delete()
        return redirect('collegemanagement')
    return redirect('collegemanagement')

# ----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                     department_management
# ----------------------------------------------------------------------------------------------------------------------------------------------------------

def department_management(request):
    # Base QuerySet
    department_list = (
        Department.objects
        .select_related("college")
        .order_by("-id")
    )

    # -----------------------------
    # Filters
    # -----------------------------
    search_query = request.GET.get("q", "").strip()
    college_filter = request.GET.get("college", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if search_query:
        department_list = department_list.filter(
            Q(dept_name__icontains=search_query) |
            Q(dept_code__icontains=search_query) |
            Q(hod_name__icontains=search_query) |
            Q(username__icontains=search_query)
        )

    if college_filter:
        department_list = department_list.filter(
            college__college_name__iexact=college_filter
        )

    if status_filter:
        department_list = department_list.filter(
            status__iexact=status_filter
        )

    # -----------------------------
    # Statistics (Overall)
    # -----------------------------
    total_count = Department.objects.count()

    active_count = Department.objects.filter(
        status__iexact="active"
    ).count()

    inactive_count = Department.objects.filter(
        status__iexact="inactive"
    ).count()

    college_count = Department.objects.values(
        "college"
    ).distinct().count()

    # -----------------------------
    # Pagination
    # -----------------------------
    paginator = Paginator(department_list, 10)

    page_number = request.GET.get("page", 1)

    try:
        departments = paginator.page(page_number)
    except Exception:
        departments = paginator.page(1)

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        "departments": departments,
        "colleges": College.objects.order_by("college_name"),

        "search_query": search_query,
        "college_filter": college_filter,
        "status_filter": status_filter,

        "total_count": total_count,
        "active_count": active_count,
        "inactive_count": inactive_count,
        "college_count": college_count,

        "elided_page_range": paginator.get_elided_page_range(
            number=departments.number,
            on_each_side=1,
            on_ends=1,
        ),
    }

    return render(
        request,
        "department/department_list.html",
        context,
    )




import string
import random
import re
from django.shortcuts import render, redirect
from .models import College, Principal, Department, Student, Video, VideoWatch


def generate_dept_code(dept_name):
    """
    Build a short, unique department code from the department name.
    e.g. "Computer Science and Engineering" -> "CSE"
    Falls back to first 3 letters if only one word is given,
    and appends a numeric suffix on collision.
    """
    words = re.findall(r'[A-Za-z]+', dept_name)
    if len(words) >= 2:
        code = ''.join(w[0] for w in words).upper()
    else:
        code = dept_name[:3].upper()

    code = code or "DEPT"
    base_code = code
    counter = 1
    while Department.objects.filter(dept_code=code).exists():
        counter += 1
        code = f"{base_code}{counter}"
    return code

def department_add(request):
    error = None
    form_data = {
        'college_id': '',
        'dept_name': '',
        'hod_name': '',
        'hod_email': '',
        'hod_phone': '',
        'status': 'active',
    }

    if request.method == "POST":
        college_id = request.POST.get('college')
        dept_name = request.POST.get('dept_name', '').strip()
        hod_name = request.POST.get('hod_name', '').strip()
        hod_email = request.POST.get('hod_email', '').strip()
        hod_phone = request.POST.get('hod_phone', '').strip()
        status = request.POST.get('status', 'active') or 'active'

        form_data.update({
            'college_id': college_id,
            'dept_name': dept_name,
            'hod_name': hod_name,
            'hod_email': hod_email,
            'hod_phone': hod_phone,
            'status': status,
        })

        college = College.objects.filter(id=college_id).first() if college_id else None

        if college and dept_name and hod_name and hod_email:
            if Department.objects.filter(hod_email=hod_email).exists():
                error = f"HOD email '{hod_email}' is already in use by another department."
            else:
                dept_code = generate_dept_code(dept_name)

                # Generate username
                base_college = college.college_name[:3].upper().replace(" ", "")
                username = f"{base_college}_{dept_code}_HOD"

                # Generate random password
                chars = string.ascii_letters + string.digits + "!@#$%^&*"
                password = ''.join(random.choices(chars, k=10))

                try:
                    Department.objects.create(
                        college=college,
                        dept_code=dept_code,
                        dept_name=dept_name,
                        hod_name=hod_name,
                        hod_email=hod_email,
                        hod_phone=hod_phone,
                        status=status,
                        username=username,
                        password=password
                    )
                    return redirect('department_management')
                except IntegrityError:
                    error = "Could not create department — one of the values conflicts with an existing record."
        else:
            error = "Please fill all required fields."

    colleges = College.objects.all()
    return render(request, 'department/add_department.html', {
        'colleges': colleges,
        'error': error,
        'form': form_data,
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError


def department_edit(request, id):
    department = get_object_or_404(Department, id=id)
    error = None

    if request.method == "POST":
        college_id = request.POST.get('college', '').strip()
        dept_code = request.POST.get('dept_code', '').strip()
        dept_name = request.POST.get('dept_name', '').strip()
        dept_short_name = request.POST.get('dept_short_name', '').strip()
        description = request.POST.get('description', '').strip()
        hod_name = request.POST.get('hod_name', '').strip()
        hod_email = request.POST.get('hod_email', '').strip()
        hod_phone = request.POST.get('hod_phone', '').strip()
        status = request.POST.get('status', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        college = College.objects.filter(id=college_id).first() if college_id else None

        # Basic required-field validation
        if not (college and dept_code and dept_name and hod_name and hod_email and username):
            error = "Please fill all required fields."
        elif Department.objects.filter(dept_code=dept_code).exclude(id=department.id).exists():
            error = f"Department code '{dept_code}' is already in use by another department."
        elif Department.objects.filter(hod_email=hod_email).exclude(id=department.id).exists():
            error = f"Email '{hod_email}' is already in use by another department's HOD."
        elif Department.objects.filter(username=username).exclude(id=department.id).exists():
            error = f"Username '{username}' is already in use."
        else:
            department.college = college
            department.dept_code = dept_code
            department.dept_name = dept_name
            department.dept_short_name = dept_short_name
            department.description = description
            department.hod_name = hod_name
            department.hod_email = hod_email
            department.hod_phone = hod_phone
            department.status = status
            department.username = username
            if password:
                department.password = password

            try:
                department.save()
                return redirect('department_management')
            except IntegrityError:
                error = "Could not save changes — one of the values conflicts with an existing record."

    colleges = College.objects.all()
    return render(request, 'department/edit_department.html', {
        'department': department,
        'colleges': colleges,
        'error': error,
    })




@require_POST
def department_update(request, id):
    department = Department.objects.filter(id=id).first()
    if not department:
        return JsonResponse({'status': 'error', 'message': 'Department not found'}, status=404)

    dept_name = request.POST.get('dept_name', '').strip()
    college_id = request.POST.get('college', '').strip()
    hod_name = request.POST.get('hod_name', '').strip()
    hod_email = request.POST.get('hod_email', '').strip()
    hod_phone = request.POST.get('hod_phone', '').strip()
    status = request.POST.get('status', '').strip()

    if not dept_name or not college_id or not hod_name or not hod_email or not status:
        return JsonResponse({'status': 'error', 'message': 'Please fill all required fields.'}, status=400)

    college = College.objects.filter(id=college_id).first()
    if not college:
        return JsonResponse({'status': 'error', 'message': 'Invalid college selected.'}, status=400)

    if Department.objects.filter(hod_email=hod_email).exclude(id=department.id).exists():
        return JsonResponse({'status': 'error', 'message': f"Email '{hod_email}' is already used by another department."}, status=400)

    department.dept_name = dept_name
    department.college = college
    department.hod_name = hod_name
    department.hod_email = hod_email
    department.hod_phone = hod_phone
    department.status = status
    department.save()

    return JsonResponse({
        'status': 'success',
        'message': 'Department updated successfully',
        'data': {
            'id': department.id,
            'name': department.dept_name,
            'college': department.college.college_name,
            'collegeId': department.college.id,
            'hod': department.hod_name,
            'hodEmail': department.hod_email,
            'hodPhone': department.hod_phone,
            'hodInitials': (department.hod_name[:2].upper() if department.hod_name else ''),
            'status': department.status,
        }
    })
def hod_management(request):
    return render(request, 'dashboard/hod_management.html')

from django.core.paginator import Paginator

from django.db.models import Q

def principal_management(request):
    principals_list = Principal.objects.all().order_by('-created_at')

    q = request.GET.get('q', '')
    college_id = request.GET.get('college', '')
    status = request.GET.get('status', '')

    if q:
        principals_list = principals_list.filter(
            Q(principal_name__icontains=q) |
            Q(principal_email__icontains=q)
        )
    if college_id:
        principals_list = principals_list.filter(college_id=college_id)
    if status:
        principals_list = principals_list.filter(status=status)

    paginator = Paginator(principals_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    all_colleges = College.objects.all()

    context = {
        'page_obj': page_obj,
        'principals': page_obj.object_list,
        'all_colleges': all_colleges,
        'colleges': all_colleges,
        'q': q,
        'selected_college': college_id,
        'selected_status': status,
        'new_credentials': request.session.pop('new_principal_credentials', None),
        # Live stat counts
        'total_principals': Principal.objects.count(),
        'active_principals': Principal.objects.filter(status='active').count(),
        'inactive_principals': Principal.objects.filter(status='inactive').count(),
        'total_colleges': College.objects.count(),
    }

    if request.GET.get('partial') == '1':
        from django.http import JsonResponse
        from django.template.loader import render_to_string
        rows_html = render_to_string('Principalmanagement/partials/principal_rows.html', context, request=request)

        try:
            start_idx = page_obj.start_index()
            end_idx = page_obj.end_index()
        except:
            start_idx = 0
            end_idx = 0

        return JsonResponse({
            'rows_html': rows_html,
            'start_index': start_idx,
            'end_index': end_idx,
            'total': paginator.count,
            'current_page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        })

    return render(request, 'Principalmanagement/Principalmanagement.html', context)

def principal_add(request):
    if request.method == 'POST':
        name     = request.POST.get('principal_name', '').strip()
        email    = request.POST.get('principal_email', '').strip()
        mobile   = request.POST.get('principal_mobile', '').strip()
        college_id = request.POST.get('college', '').strip()
        status   = request.POST.get('status', 'active').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if name and email and college_id:
            try:
                college = College.objects.get(id=college_id)
                Principal.objects.create(
                    principal_name=name,
                    principal_email=email,
                    principal_mobile=mobile,
                    college=college,
                    status=status,
                    username=username,
                    password=password,
                )
                # Store credentials in session so management page can show them
                request.session['new_principal_credentials'] = {
                    'name': name,
                    'username': username,
                    'password': password,
                }
            except Exception:
                pass
        return redirect('principal_management')
    return redirect('principal_management')


from django.views.decorators.http import require_POST

@require_POST
def department_delete(request, id):
    department = Department.objects.filter(id=id).first()
    if not department:
        return JsonResponse({'status': 'error', 'message': 'Department not found'}, status=404)

    department.delete()
    return JsonResponse({'status': 'success', 'message': 'Department deleted successfully'})



def principal_edit(request, id):
    if request.method == "POST":
        principal = Principal.objects.filter(id=id).first()
        if principal:
            college_id = request.POST.get('college')
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            mobile = request.POST.get('principal_mobile')
            status = request.POST.get('status')

            if college_id:
                principal.college_id = college_id
            if full_name:
                principal.principal_name = full_name
            if email:
                principal.principal_email = email
            if mobile:
                principal.principal_mobile = mobile
            if status:
                principal.status = status

            principal.save()
    return redirect('principal_management')

def principal_delete(request, id):
    if request.method == "POST":
        principal = Principal.objects.filter(id=id).first()
        if principal:
            principal.delete()
    return redirect('principal_management')



def student_management(request):
    import string, random, json
    from django.db.models import Q
    from django.http import JsonResponse
    from django.template.loader import render_to_string
    from datetime import date

    # Auto-expire students whose end_date has passed
    today = date.today()
    Student.objects.filter(end_date__lt=today, status='active').update(status='expired')

    # select_related avoids N+1 queries and guarantees college_id / department_id
    # (and their names) are populated for every row rendered in student_rows.html —
    # this is what lets the Edit modal filter Department options by college.
    # Only include completed signup users who have verified their email OTP
    students_list = Student.objects.filter(is_verified=True).select_related('college', 'department').order_by('-created_at')

    q = request.GET.get('q', '')
    college_id = request.GET.get('college', '')
    dept_id = request.GET.get('department', '')
    year = request.GET.get('year', '')
    status = request.GET.get('status', '')

    if q:
        students_list = students_list.filter(
            Q(full_name__icontains=q) | Q(email__icontains=q) | Q(username__icontains=q)
        )
    if college_id:
        students_list = students_list.filter(college_id=college_id)
    if dept_id:
        students_list = students_list.filter(department_id=dept_id)
    if year:
        students_list = students_list.filter(year=year)
    if status:
        students_list = students_list.filter(status=status)

    paginator = Paginator(students_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    all_colleges = College.objects.all()
    all_departments = Department.objects.all()

    # ── Departments grouped by college, computed in Python (guaranteed correct) ──
    # The Edit modal's Department dropdown reads THIS instead of trying to match
    # data-college-id against option[data-college] in the DOM, which is fragile.
    departments_by_college = {}
    for d in all_departments:
        departments_by_college.setdefault(str(d.college_id), []).append(
            {'id': d.id, 'name': d.dept_name}
        )

    verified_students_qs = Student.objects.filter(is_verified=True)

    context = {
        'page_obj': page_obj,
        'students': page_obj.object_list,
        'all_colleges': all_colleges,
        'all_departments': all_departments,
        'departments_by_college_json': json.dumps(departments_by_college),
        'q': q,
        'selected_college': college_id,
        'selected_dept': dept_id,
        'selected_year': year,
        'selected_status': status,
        'total_students': verified_students_qs.count(),
        'active_students': verified_students_qs.filter(status='active').count(),
        'inactive_students': verified_students_qs.filter(status='inactive').count(),
        'college_count': College.objects.count(),
    }

    # AJAX partial request – return JSON for smooth pagination
    if request.GET.get('partial') == '1':
        rows_html = render_to_string('studentmanagement/partials/student_rows.html', context, request=request)

        # Handle empty pages safely
        try:
            start_idx = page_obj.start_index()
            end_idx = page_obj.end_index()
        except Exception:
            start_idx = 0
            end_idx = 0

        return JsonResponse({
            'rows_html': rows_html,
            'start_index': start_idx,
            'end_index': end_idx,
            'total': paginator.count,
            'current_page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        })

    return render(request, 'studentmanagement/studentmanagement.html', context)


def student_add(request):
    """
    Manual Admin Add Student has been disabled in favor of Student Self-Signup.
    """
    return redirect("student_management")


def get_principal_by_college(request, college_id):
    """
    Returns Principal name & email dynamically when a college is selected.
    """
    college = College.objects.filter(id=college_id).first()
    if not college:
        return JsonResponse({"status": "error", "message": "College not found"}, status=404)

    principal = Principal.objects.filter(college=college, status="active").first()
    if not principal:
        # Fallback to any principal attached to the college
        principal = Principal.objects.filter(college=college).first()

    return JsonResponse({
        "status": "success",
        "college_id": college.id,
        "college_name": college.college_name,
        "principal_name": principal.principal_name if principal else "Not Assigned",
        "principal_email": principal.principal_email if principal else "N/A",
    })


@csrf_exempt
def student_signup(request):
    """
    Student Self-Signup endpoint.
    Expects: full_name, email, phone, date_of_birth, college_id, department_id, year, password, confirm_password.
    Sends 6-digit OTP to student's email.
    """
    if request.method == "GET":
        colleges = College.objects.filter(status="active").order_by("college_name")
        departments = Department.objects.filter(status="active").order_by("dept_name")
        return render(request, "studentmanagement/student_signup.html", {
            "colleges": colleges,
            "departments": departments,
        })

@csrf_exempt
def send_otp(request):
    """
    1. send_otp API: Sends OTP code to student email.
    Features 60s resend cooldown and 10-minute expiry.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required"}, status=405)

    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
        email = data.get("email", "").strip().lower()
        full_name = data.get("full_name", "").strip() or email.split('@')[0]

        if not email:
            return JsonResponse({"status": "error", "message": "Email address is required."}, status=400)

        # 60s Cooldown Check
        student = Student.objects.filter(email__iexact=email).first()
        if student and student.otp_created_at:
            seconds_since = (timezone.now() - student.otp_created_at).total_seconds()
            if seconds_since < 60:
                remaining = int(60 - seconds_since)
                return JsonResponse({"status": "error", "message": f"Please wait {remaining} seconds before requesting another OTP."}, status=429)

        # Generate 6-digit OTP
        otp = f"{random.randint(100000, 999999)}"

        # Get default college & department fallback for temp OTP creation
        default_college = College.objects.first()
        default_dept = Department.objects.filter(college=default_college).first() if default_college else Department.objects.first()

        # Store OTP temporary record (unverified)
        if student:
            student.otp_code = otp
            student.otp_created_at = timezone.now()
            student.otp_attempts = 0  # Reset attempts on new send
            student.save()
        else:
            student = Student.objects.create(
                full_name=full_name,
                email=email,
                username=email,
                college=default_college,
                department=default_dept,
                is_verified=False,
                otp_code=otp,
                otp_created_at=timezone.now(),
                status="pending_approval"
            )

        # Send Email OTP via SMTP / Brevo REST API
        subject = f"Your Verification Code: {otp}"
        message = f"Hello {full_name},\n\nYour OTP for registration verification is: {otp}\n\nThis code will expire in 10 minutes."
        email_sent = False

        try:
            from django.conf import settings
            from django.core.mail import send_mail
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'moontonabin@gmail.com')
            send_mail(subject, message, from_email, [email], fail_silently=False)
            email_sent = True
        except Exception as mail_err:
            print(f"[MAIL ERROR] {mail_err}")

        return JsonResponse({
            "status": "success",
            "message": "OTP verification code sent to your email.",
            "email_sent": email_sent
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def verify_otp(request):
    """
    2. verify_otp API: Validates the 6-digit OTP code sent to the email address with 10-minute expiry.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required"}, status=405)

    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
        email = data.get("email", "").strip().lower()
        otp_code = data.get("otp_code", "").strip()

        if not email or not otp_code:
            return JsonResponse({"status": "error", "message": "Email and OTP Code are required."}, status=400)

        student = Student.objects.filter(email__iexact=email).first()
        if not student:
            return JsonResponse({"status": "error", "message": "Student account record not found. Please request OTP again."}, status=404)

        # 10-Minute Expiry Check
        if student.otp_created_at:
            elapsed_minutes = (timezone.now() - student.otp_created_at).total_seconds() / 60
            if elapsed_minutes > 10:
                return JsonResponse({"status": "error", "message": "OTP code has expired (valid for 10 minutes). Please request a new OTP."}, status=400)

        # Tracking attempts (assuming field exists or logic handling)
        if str(student.otp_code).strip() != otp_code:
            student.otp_attempts = getattr(student, 'otp_attempts', 0) + 1
            student.save()
            return JsonResponse({"status": "error", "message": "Invalid OTP code provided. Please check your email and try again."}, status=400)

        return JsonResponse({
            "status": "success",
            "message": "OTP verified successfully! You can now complete your academic registration."
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def create_student_account(request):
    """
    3. create_student_account API: Creates the student account only after successful OTP verification.
    Executes duplicate verified email check (Student.objects.filter(email__iexact=email, is_verified=True).exists())
    only at this final step.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required"}, status=405)

    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST

        full_name = data.get("full_name", "").strip()
        email = data.get("email", "").strip().lower()
        phone = data.get("phone", "").strip()
        date_of_birth = data.get("date_of_birth")
        college_id = data.get("college_id") or data.get("college")
        dept_id = data.get("department_id") or data.get("department")
        year = data.get("year", "").strip()
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")

        if not full_name or not email or not password:
            return JsonResponse({"status": "error", "message": "Full Name, Email, and Password are required."}, status=400)

        if password != confirm_password:
            return JsonResponse({"status": "error", "message": "Password and Confirm Password do not match."}, status=400)

        # Duplicate email check ONLY during final account creation
        is_already_registered = Student.objects.filter(email__iexact=email, is_verified=True).exists()
        if is_already_registered:
            return JsonResponse({
                "status": "error",
                "message": "This email is already registered. Please log in."
            }, status=400)

        college = College.objects.filter(id=college_id).first() if college_id else None
        if not college:
            college = College.objects.first()

        dept = Department.objects.filter(id=dept_id).first() if dept_id else None
        if not dept and college:
            dept = Department.objects.filter(college=college).first()
        if not dept:
            dept = Department.objects.first()

        today = date.today()
        years = 3 if (college and college.college_stream == "arts_science") else 4
        try:
            computed_end_date = today.replace(year=today.year + years)
        except ValueError:
            computed_end_date = today.replace(year=today.year + years, day=28)

        student = Student.objects.filter(email__iexact=email).first()
        if student:
            student.full_name = full_name
            student.phone = phone
            if date_of_birth:
                try:
                    student.date_of_birth = date.fromisoformat(str(date_of_birth))
                except ValueError:
                    pass
            student.join_date = today
            student.end_date = computed_end_date
            student.college = college
            student.department = dept
            student.year = year
            student.username = email
            student.password = password
            student.is_verified = True
            student.status = "active"
            student.otp_code = None
            student.save()
        else:
            student = Student.objects.create(
                full_name=full_name,
                email=email,
                phone=phone,
                date_of_birth=date.fromisoformat(str(date_of_birth)) if date_of_birth else None,
                college=college,
                department=dept,
                year=year,
                join_date=today,
                end_date=computed_end_date,
                username=email,
                password=password,
                is_verified=True,
                status="active"
            )

        return JsonResponse({
            "status": "success",
            "message": "Student account created successfully! You can now log in.",
            "student_id": student.id
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def forgot_password_send_otp(request):
    """
    Step 1: Verify registered email and send password reset OTP.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required"}, status=405)

    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
        email = data.get("email", "").strip().lower()

        if not email:
            return JsonResponse({"status": "error", "message": "Email address is required."}, status=400)

        student = Student.objects.filter(email__iexact=email).first()
        if not student:
            return JsonResponse({"status": "error", "message": "Email not found. Please enter your registered email address."}, status=404)

        # Generate 6-digit OTP
        import random
        otp = str(random.randint(100000, 999999))
        student.otp_code = otp
        student.otp_created_at = timezone.now()
        student.save()

        # Send Email OTP via SMTP / Brevo REST API
        subject = f"Your Password Reset Code: {otp}"
        message = f"Hello {student.full_name},\n\nYour OTP for resetting your password is: {otp}\n\nThis code will expire in 10 minutes."
        email_sent = False

        try:
            from django.conf import settings
            from django.core.mail import send_mail
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'divv26979@gmail.com')
            send_mail(subject, message, from_email, [email], fail_silently=False)
            email_sent = True
        except Exception as mail_err:
            print("SMTP send error in password reset:", mail_err)

        if not email_sent:
            try:
                import urllib.request
                from django.conf import settings
                api_key = getattr(settings, 'BREVO_API_KEY', '')
                sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'divv26979@gmail.com')
                
                payload = json.dumps({
                    "sender": {"name": "Educational Portal", "email": sender_email},
                    "to": [{"email": email, "name": student.full_name}],
                    "subject": subject,
                    "textContent": message
                }).encode('utf-8')

                req = urllib.request.Request(
                    "https://api.brevo.com/v3/smtp/email",
                    data=payload,
                    headers={
                        "accept": "application/json",
                        "api-key": api_key,
                        "content-type": "application/json"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req) as resp:
                    print("Brevo API Email Dispatch status:", resp.status)
                    email_sent = True
            except Exception as brevo_err:
                print("Brevo API password reset email dispatch error:", brevo_err)

        return JsonResponse({
            "status": "success",
            "message": f"Password reset OTP code sent successfully to {email}.",
            "email": email
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def forgot_password_verify_otp(request):
    """
    Step 2: Verify reset OTP.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required"}, status=405)

    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
        email = data.get("email", "").strip().lower()
        otp_code = data.get("otp_code", "").strip()

        if not email or not otp_code:
            return JsonResponse({"status": "error", "message": "Email and OTP Code are required."}, status=400)

        student = Student.objects.filter(email__iexact=email).first()
        if not student:
            return JsonResponse({"status": "error", "message": "Student account not found."}, status=404)

        if student.otp_code != otp_code:
            return JsonResponse({"status": "error", "message": "Invalid OTP code provided. Please check your email and try again."}, status=400)

        return JsonResponse({
            "status": "success",
            "message": "OTP verified successfully. Please enter your new password."
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def forgot_password_reset(request):
    """
    Step 3: Reset Student Password.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required"}, status=405)

    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
        email = data.get("email", "").strip().lower()
        otp_code = data.get("otp_code", "").strip()
        new_password = data.get("new_password", "").strip()
        confirm_password = data.get("confirm_password", "").strip()

        if not email or not new_password or not confirm_password:
            return JsonResponse({"status": "error", "message": "All fields are required."}, status=400)

        if new_password != confirm_password:
            return JsonResponse({"status": "error", "message": "Passwords do not match."}, status=400)

        student = Student.objects.filter(email__iexact=email).first()
        if not student:
            return JsonResponse({"status": "error", "message": "Student account not found."}, status=404)

        if student.otp_code and student.otp_code != otp_code:
            return JsonResponse({"status": "error", "message": "Invalid or expired OTP session."}, status=400)

        student.password = new_password
        student.otp_code = None
        student.save()

        return JsonResponse({
            "status": "success",
            "message": "Password updated successfully. Please sign in with your new password."
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def api_get_colleges(request):
    """
    Returns active colleges and optionally filtered departments for signup.
    """
    colleges = College.objects.filter(status="active").order_by("college_name")
    college_data = [{"id": c.id, "name": c.college_name} for c in colleges]

    college_id = request.GET.get("college_id")
    dept_qs = Department.objects.filter(status="active")
    if college_id:
        dept_qs = dept_qs.filter(college_id=college_id)
    dept_data = [{"id": d.id, "name": d.dept_name, "college_id": d.college_id} for d in dept_qs.order_by("dept_name")]

    return JsonResponse({
        "status": "success",
        "colleges": college_data,
        "departments": dept_data
    })


def student_delete(request, student_id):
    from django.views.decorators.csrf import csrf_exempt
    from django.http import JsonResponse

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    student = Student.objects.filter(id=student_id).first()
    if not student:
        return JsonResponse({'status': 'error', 'message': 'Student not found'}, status=404)

    student.delete()
    return JsonResponse({'status': 'success', 'message': 'Student deleted successfully'})

from datetime import date

from datetime import date
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from datetime import date
from django.shortcuts import get_object_or_404
from django.http import JsonResponse


def student_update(request, student_id):
    """
    Only these fields are editable from the UI:
        - full_name
        - department
        - year
        - join_date
        - status

    Everything else (username, password, college) is read-only
    and is preserved as-is from the existing record.
    """
    student = get_object_or_404(Student, id=student_id)

    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "Invalid request."
        })

    try:
        full_name = request.POST.get("full_name", "").strip()
        status = request.POST.get("status")
        year = request.POST.get("year", "").strip()
        join_date_str = request.POST.get("join_date")
        college = student.college

        if full_name:
            student.full_name = full_name

        if request.POST.get("department"):
            dept = Department.objects.filter(id=request.POST.get("department")).first()
            if dept:
                student.department = dept

        if year:
            student.year = year

        if status:
            student.status = status

        if join_date_str:
            join_date = date.fromisoformat(join_date_str)
            years = 3 if college.college_stream == "arts_science" else 4
            try:
                end_date = join_date.replace(year=join_date.year + years)
            except ValueError:
                end_date = join_date.replace(year=join_date.year + years, day=28)
            student.join_date = join_date
            student.end_date = end_date

        student.save()

        return JsonResponse({
            "status": "success",
            "message": "Student updated successfully."
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        })

def video_management(request):
    from django.core.paginator import Paginator
    from django.db.models import Q

    videos_list = Video.objects.all().order_by('-uploaded_at')

    q = request.GET.get('q', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')

    if q:
        videos_list = videos_list.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if category:
        videos_list = videos_list.filter(category=category)
    if status:
        videos_list = videos_list.filter(status__iexact=status)

    paginator = Paginator(videos_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'videos': page_obj.object_list,
        'q': q,
        'selected_category': category,
        'selected_status': status,
        'total_videos': Video.objects.count(),
        'published_videos': Video.objects.filter(status='Published').count(),
        'draft_videos': Video.objects.filter(status='Draft').count(),
        # Dummy value for views for now until an aggregate is added
        'total_views': "0",
    }

    if request.GET.get('partial') == '1':
        from django.http import JsonResponse
        from django.template.loader import render_to_string
        rows_html = render_to_string('videomanagement/partials/video_rows.html', context, request=request)

        try:
            start_idx = page_obj.start_index()
            end_idx = page_obj.end_index()
        except:
            start_idx = 0
            end_idx = 0

        return JsonResponse({
            'rows_html': rows_html,
            'start_index': start_idx,
            'end_index': end_idx,
            'total': paginator.count,
            'current_page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        })

    return render(request, "videomanagement/video_management.html", context)


def video_add(request):
    if request.method == "POST":
        title = request.POST.get("title")
        category = request.POST.get("category")
        duration = request.POST.get("duration")
        description = request.POST.get("description", "")
        status = request.POST.get("status", "Published")

        video_file = request.FILES.get("video_file")
        thumbnail = request.FILES.get("thumbnail")

        if title and category and duration and video_file and thumbnail:

            Video.objects.create(
                title=title,
                category=category,
                duration=duration,
                description=description,
                status=status,
                video_file=video_file,
                thumbnail=thumbnail,

                # Admin Upload
                is_admin_video=True
            )

            return redirect("video_management")

    return render(request, "videomanagement/video_add.html")


def video_edit(request, id):
    video = get_object_or_404(Video, id=id)
    if request.method == "POST":
        video.title = request.POST.get('title', video.title)
        video.category = request.POST.get('category', video.category)
        video.duration = request.POST.get('duration', video.duration)
        video.description = request.POST.get('description', video.description)
        video.status = request.POST.get('status', video.status)
        if request.FILES.get('video_file'):
            video.video_file = request.FILES.get('video_file')
        if request.FILES.get('thumbnail'):
            video.thumbnail = request.FILES.get('thumbnail')
        video.save()
        return JsonResponse({'status': 'success', 'message': 'Video updated successfully.'})
    return JsonResponse({'status': 'error', 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
def video_delete(request, id):
    if request.method in ["POST", "DELETE"]:
        try:
            video = Video.objects.get(id=id)
            video.delete()
            return JsonResponse({'status': 'success', 'message': 'Video deleted successfully.'})
        except Video.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Video not found or already deleted.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed.'}, status=405)




import json
import re
from collections import Counter
from datetime import timedelta

from django.db.models import Count, Sum, F, ExpressionWrapper, FloatField
from django.db.models.functions import TruncDate, TruncMonth
from django.shortcuts import render
from django.utils import timezone

from .models import College, Department, Student, Video, VideoWatch


# ----------------------------------------------------------------------
# Helper: "12:34" -> 754 seconds, "1:02:15" -> 3735 seconds
# ----------------------------------------------------------------------
def parse_duration_to_seconds(duration_str):
    if not duration_str:
        return 0
    parts = re.split(r"[:.]", duration_str.strip())
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        return 0
    parts = parts[-3:]  # keep at most H, M, S
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return h * 3600 + m * 60 + s


def video_analytics(request):
    now = timezone.now()
    today = now.date()

    # ------------------------------------------------------------
    # Filters (optional query params from the topbar dropdowns)
    # ------------------------------------------------------------
    college_id = request.GET.get("college")
    dept_id = request.GET.get("department")
    video_status = request.GET.get("video_status")
    date_filter = request.GET.get("date_filter", "all")

    watches = VideoWatch.objects.all()
    videos = Video.objects.all()

    if date_filter == "today":
        watches = watches.filter(watched_at__date=today)
        videos = videos.filter(uploaded_at__date=today)
    elif date_filter == "this_week":
        start_w = today - timedelta(days=6)
        watches = watches.filter(watched_at__date__gte=start_w)
        videos = videos.filter(uploaded_at__date__gte=start_w)
    elif date_filter == "this_month":
        start_m = today.replace(day=1)
        watches = watches.filter(watched_at__date__gte=start_m)
        videos = videos.filter(uploaded_at__date__gte=start_m)
    elif date_filter == "this_year":
        start_y = today.replace(month=1, day=1)
        watches = watches.filter(watched_at__date__gte=start_y)
        videos = videos.filter(uploaded_at__date__gte=start_y)

    if college_id:
        watches = watches.filter(student__college_id=college_id)
        videos = videos.filter(uploaded_by_hod__college_id=college_id)
    if dept_id:
        watches = watches.filter(student__department_id=dept_id)
        videos = videos.filter(uploaded_by_hod_id=dept_id)
    if video_status in ("Published", "Draft"):
        videos = videos.filter(status=video_status)

    # Pre-compute each video's duration in seconds once (used for
    # watch-time + completion math below).
    duration_seconds_by_id = {
        v.id: parse_duration_to_seconds(v.duration) for v in Video.objects.all()
    }

    # ------------------------------------------------------------
    # Top summary cards
    # ------------------------------------------------------------
    total_videos = videos.count()
    total_views = videos.aggregate(total=Sum("views"))["total"] or 0

    total_watch_seconds = 0
    all_completion_ratios = []
    for vw in watches.only("video_id", "watched_seconds"):
        total_watch_seconds += vw.watched_seconds
        dur = duration_seconds_by_id.get(vw.video_id, 0)
        if dur > 0:
            all_completion_ratios.append(min(vw.watched_seconds / dur, 1.0))
    watch_hours = round(total_watch_seconds / 3600, 1)
    avg_completion = round((sum(all_completion_ratios) / len(all_completion_ratios)) * 100, 1) if all_completion_ratios else 0

    month_start = today.replace(day=1)
    videos_uploaded = videos.filter(uploaded_at__date__gte=month_start).count()
    videos_uploaded_last_month = videos.filter(
        uploaded_at__date__lt=month_start,
        uploaded_at__date__gte=(month_start - timedelta(days=30)),
    ).count()

    top_video = videos.order_by("-views").first()
    top_video_title = top_video.title if top_video else "—"
    top_video_views = top_video.views if top_video else 0

    # ------------------------------------------------------------
    # Trend charts — last 7 calendar days, from real VideoWatch rows
    # ------------------------------------------------------------
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    daily_labels = [d.strftime("%b %d") for d in days]

    watches_by_day = (
        watches.annotate(day=TruncDate("watched_at"))
        .filter(day__gte=days[0])
        .values("day")
        .annotate(count=Count("id"))
    )
    views_by_day_map = {row["day"]: row["count"] for row in watches_by_day}
    views_series = [views_by_day_map.get(d, 0) for d in days]

    # Watch time per day (seconds -> hours), computed row by row
    watch_seconds_by_day = {d: 0 for d in days}
    completion_ratios_by_day = {d: [] for d in days}
    for vw in watches.filter(watched_at__date__gte=days[0]).only(
        "video_id", "watched_at", "watched_seconds"
    ):
        d = vw.watched_at.date()
        if d in watch_seconds_by_day:
            watch_seconds_by_day[d] += vw.watched_seconds
            dur = duration_seconds_by_id.get(vw.video_id, 0)
            if dur > 0:
                completion_ratios_by_day[d].append(
                    min(vw.watched_seconds / dur, 1.0)
                )

    watch_time_series = [round(watch_seconds_by_day[d] / 3600, 2) for d in days]
    completion_series = [
        round(
            (sum(completion_ratios_by_day[d]) / len(completion_ratios_by_day[d])) * 100,
            1,
        )
        if completion_ratios_by_day[d]
        else 0
        for d in days
    ]

    # ------------------------------------------------------------
    # Department-wise / College-wise views
    # (Video has no direct FK to College/Department, so this is
    # derived by joining VideoWatch -> Student -> Department/College)
    # ------------------------------------------------------------
    dept_rows = (
        watches.exclude(student__department__isnull=True)
        .values("student__department__dept_name")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    dept_labels = [row["student__department__dept_name"] for row in dept_rows]
    dept_data = [row["count"] for row in dept_rows]

    # Weekly variant for Dept switcher
    _week_start = today - timedelta(days=today.weekday())  # Monday this week
    dept_week_rows = (
        watches.filter(watched_at__date__gte=_week_start)
        .exclude(student__department__isnull=True)
        .values("student__department__dept_name")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    dept_week_labels = [row["student__department__dept_name"] for row in dept_week_rows]
    dept_week_data   = [row["count"] for row in dept_week_rows]

    college_rows = (
        watches.exclude(student__college__isnull=True)
        .values("student__college__college_name")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    college_labels_chart = [row["student__college__college_name"] for row in college_rows]
    college_data_chart = [row["count"] for row in college_rows]

    # Weekly variant for College switcher
    college_week_rows = (
        watches.filter(watched_at__date__gte=_week_start)
        .exclude(student__college__isnull=True)
        .values("student__college__college_name")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    college_week_labels = [row["student__college__college_name"] for row in college_week_rows]
    college_week_data   = [row["count"] for row in college_week_rows]

    # ------------------------------------------------------------
    # Category distribution
    # ------------------------------------------------------------
    cat_rows = videos.values("category").annotate(count=Count("id")).order_by("-count")
    category_labels = [row["category"] for row in cat_rows if row["category"]]
    category_data = [row["count"] for row in cat_rows if row["category"]]

    if not category_labels:
        # Standardized fallback video categories if database rows lack explicit category tags
        cat_counts = {}
        for v in videos:
            c = v.category or "General"
            cat_counts[c] = cat_counts.get(c, 0) + 1
        if cat_counts:
            category_labels = list(cat_counts.keys())
            category_data = list(cat_counts.values())
        else:
            category_labels = []
            category_data = []

    # ------------------------------------------------------------
    # Monthly upload trend (this calendar year)
    # ------------------------------------------------------------
    upload_rows = (
        videos.filter(uploaded_at__year=today.year)
        .annotate(month=TruncMonth("uploaded_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    monthly_labels = [row["month"].strftime("%b") for row in upload_rows]
    monthly_data = [row["count"] for row in upload_rows]

    # ------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------
    most_watched = list(videos.order_by("-views")[:5])
    least_performing = list(videos.order_by("views")[:5])
    recent_uploads = list(videos.order_by("-uploaded_at")[:5])

    # Attach real completion % / watch time onto each video object
    # in most_watched / least_performing for the template to read.
    for bucket in (most_watched, least_performing):
        for v in bucket:
            v_watches = watches.filter(video_id=v.id).only("watched_seconds")
            secs = [w.watched_seconds for w in v_watches]
            v.watch_time_display = f"{round(sum(secs) / 3600, 1)} hrs" if secs else "—"
            dur = duration_seconds_by_id.get(v.id, 0)
            if dur > 0 and secs:
                v.completion_display = f"{round((sum(secs) / len(secs)) / dur * 100)}%"
            else:
                v.completion_display = "—"

    # ------------------------------------------------------------
    # Student activity summary
    # ------------------------------------------------------------
    today_active = (
        watches.filter(watched_at__date=today).values("student_id").distinct().count()
    )
    week_start = today - timedelta(days=6)
    week_active = (
        watches.filter(watched_at__date__gte=week_start)
        .values("student_id")
        .distinct()
        .count()
    )
    month_active = (
        watches.filter(watched_at__date__gte=month_start)
        .values("student_id")
        .distinct()
        .count()
    )

    total_students = Student.objects.filter(status="active").count()
    total_watch_rows = watches.count()
    avg_videos_per_student = (
        round(total_watch_rows / total_students, 2) if total_students else 0
    )

    # ------------------------------------------------------------
    # Filter dropdown options
    # ------------------------------------------------------------
    all_colleges = College.objects.filter(status="active").order_by("college_name")
    all_departments = Department.objects.filter(status="active").order_by("dept_name")

    context = {
        "all_colleges": all_colleges,
        "colleges": all_colleges,
        "selected_college_id": college_id,
        "selected_date_filter": request.GET.get("date_filter", "all"),
        "all_departments": all_departments,

        "total_videos": total_videos,
        "total_views": total_views,
        "watch_hours": watch_hours,
        "avg_completion": avg_completion,
        "videos_uploaded": videos_uploaded,
        "videos_uploaded_last_month": videos_uploaded_last_month,
        "top_video_title": top_video_title,
        "top_video_views": top_video_views,

        "daily_labels": json.dumps(daily_labels),
        "views_series": json.dumps(views_series),
        "watch_time_series": json.dumps(watch_time_series),
        "completion_series": json.dumps(completion_series),

        "dept_labels": json.dumps(dept_labels),
        "dept_data": json.dumps(dept_data),
        "dept_week_labels": json.dumps(dept_week_labels),
        "dept_week_data": json.dumps(dept_week_data),
        "college_labels_chart": json.dumps(college_labels_chart),
        "college_data_chart": json.dumps(college_data_chart),
        "college_week_labels": json.dumps(college_week_labels),
        "college_week_data": json.dumps(college_week_data),
        "category_labels": json.dumps(category_labels),
        "category_data": json.dumps(category_data),
        "monthly_labels": json.dumps(monthly_labels),
        "monthly_data": json.dumps(monthly_data),

        "most_watched": most_watched,
        "least_performing": least_performing,
        "recent_uploads": recent_uploads,

        "today_active": today_active,
        "week_active": week_active,
        "month_active": month_active,
        "avg_videos_per_student": avg_videos_per_student,
    }

    return render(request, "videoanalytics/video_analytics.html", context)


def reports(request):
    return render(request, 'reportmanagement/report_management.html')

def user_management(request):
    return render(request, 'usermanagement/user_management.html')

def system_settings(request):
    return render(request, 'dashboard/system_settings.html')

def profile(request):
    return render(request, 'dashboard/profile.html')






from django.contrib.auth import logout as auth_logout

def user_logout(request):
    auth_logout(request)
    return redirect('home')

@csrf_exempt
def api_admin_logout(request):
    auth_logout(request)
    return JsonResponse({"status": "success", "message": "Logged out successfully"})

def global_search(request):
    from django.db.models import Q
    query = request.GET.get('q', '').strip()
    results = {
        'query': query,
        'colleges': [],
        'principals': [],
        'students': [],
        'videos': [],
        'total': 0,
    }
    if query:
        colleges = College.objects.filter(college_name__icontains=query)
        principals = Principal.objects.filter(
            Q(principal_name__icontains=query) | Q(principal_email__icontains=query)
        ).select_related('college')
        students = Student.objects.filter(
            Q(full_name__icontains=query) | Q(email__icontains=query) | Q(username__icontains=query)
        ).select_related('college', 'department')
        videos = Video.objects.filter(
            Q(title__icontains=query) | Q(category__icontains=query) | Q(description__icontains=query)
        )

        results['total'] = colleges.count() + principals.count() + students.count() + videos.count()
        results['colleges'] = colleges[:10]
        results['principals'] = principals[:10]
        results['students'] = students[:10]
        results['videos'] = videos[:10]

    return render(request, 'search/search_results.html', results)

def reports(request):
    # Pass some dynamic data that can be used for reports
    context = {
        'total_colleges': College.objects.count(),
        'total_students': Student.objects.count(),
        'total_videos': Video.objects.count(),
        'total_principals': Principal.objects.count(),
    }
    return render(request, 'reportmanagement/report_management.html', context)

# ------------------------------------------------------------------------------------------------------------------------------------------------------
#                                      API
# ------------------------------------------------------------------------------------------------------------------------------------------------------




@csrf_exempt
def principal_login(request):
    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "Only POST method allowed"
        }, status=405)

    try:
        data = json.loads(request.body)

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        principal = Principal.objects.select_related("college").filter(
            username=username,
            password=password,
            status="active"
        ).first()

        if principal is None:
            return JsonResponse({
                "status": "error",
                "message": "Invalid Username or Password"
            }, status=401)

        request.session.flush()
        request.session["principal_id"] = principal.id
        request.session["college_id"] = principal.college.id
        request.session.save()

        print("Session Created:", request.session.session_key)
        print("Session Data:", dict(request.session))

        return JsonResponse({
            "status": "success",
            "message": "Login Successful",
            "data": {
                "id": principal.id,
                "principal_name": principal.principal_name,
                "college_id": principal.college.id,
                "college_name": principal.college.college_name,
            }
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)


from .models import Principal

def get_authenticated_principal(request):
    principal_id = request.headers.get("X-Principal-Id") or request.session.get("principal_id") or request.GET.get("principal_id")

    print("Session:", dict(request.session))
    print("Principal ID:", principal_id)

    if not principal_id:
        # Development fallback: use active principal if session/headers are missing
        principal = Principal.objects.filter(status="active").first()
        if principal:
            return principal
        return None

    return Principal.objects.select_related("college").filter(
        id=principal_id,
        status="active"
    ).first()

def api_principal_dashboard(request):
    from collections import Counter
    import re

    principal = get_authenticated_principal(request)

    if principal is None:
        return JsonResponse({
            "status": "error",
            "message": "Please login"
        }, status=401)

    college = principal.college

    college_students = Student.objects.filter(college=college)
    total_students = college_students.count()
    active_students = college_students.filter(status="active").count()
    total_videos = Video.objects.count()

    watches_qs = VideoWatch.objects.filter(student__college=college).select_related("student", "video")
    total_views = watches_qs.count()

    # Calculate real watch hours
    total_watch_seconds = 0
    for w in watches_qs:
        if getattr(w, "watched_seconds", 0) > 0:
            total_watch_seconds += w.watched_seconds
        elif w.video and w.video.duration:
            m = re.search(r'\d+', str(w.video.duration))
            if m:
                total_watch_seconds += int(m.group()) * 60

    watch_hours = round(total_watch_seconds / 3600, 1)
    watch_time_str = f"{watch_hours} Hours" if watch_hours >= 1 else f"{round(total_watch_seconds / 60)} Mins"

    engagement_rate = round((active_students / total_students) * 100, 1) if total_students > 0 else 0.0

    recent_views_qs = watches_qs.select_related("student__department").order_by("-watched_at")[:10]
    recent_views_data = [
        {
            "student": rw.student.full_name,
            "department": rw.student.department.dept_name if rw.student.department else "N/A",
            "video": rw.video.title if rw.video else "N/A",
            "watchTime": rw.video.duration if rw.video else "N/A",
            "lastViewed": _format_time_ago(rw.watched_at),
        }
        for rw in recent_views_qs
    ]

    latest_videos_qs = Video.objects.all().order_by("-uploaded_at")[:5]
    latest_videos_data = [
        {
            "title": v.title,
            "category": v.category or "General",
            "duration": v.duration or "N/A",
            "views": v.views or 0,
            "uploadDate": v.uploaded_at.strftime("%Y-%m-%d") if v.uploaded_at else "Recently",
            "thumbnail": request.build_absolute_uri(v.thumbnail.url) if v.thumbnail else None,
        }
        for v in latest_videos_qs
    ]

    today = timezone.localdate()
    daily_views = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
        day_end = day_start + timedelta(days=1)
        count = watches_qs.filter(
            watched_at__gte=day_start,
            watched_at__lt=day_end,
        ).count()
        daily_views.append({"day": day.strftime("%b %d"), "views": count})

    category_counts = Counter(
        watch.video.category
        for watch in watches_qs
        if watch.video and watch.video.category
    )
    palette = ["#6366f1", "#0d9488", "#f59e0b", "#10b981", "#8b5cf6", "#ec4899"]
    top_categories = [
        {
            "name": category,
            "value": count,
            "color": palette[index % len(palette)],
        }
        for index, (category, count) in enumerate(category_counts.most_common(5))
    ]

    # Department Performance Analytics
    departments = Department.objects.filter(college=college)
    dept_performance = []
    for dept in departments:
        dept_students = Student.objects.filter(college=college, department=dept)
        std_count = dept_students.count()
        dept_views = VideoWatch.objects.filter(student__in=dept_students).count()
        comp_rate = round((dept_views / (std_count * max(total_videos, 1))) * 100) if std_count > 0 else 0
        dept_performance.append({
            "name": dept.dept_name,
            "code": dept.dept_code,
            "students": std_count,
            "views": dept_views,
            "completionRate": min(100, comp_rate),
            "hod": dept.hod_name or "N/A",
        })

    # Live Activity Feed
    live_activities = []
    for w in watches_qs.order_by("-watched_at")[:6]:
        live_activities.append({
            "id": f"watch-{w.id}",
            "type": "watch",
            "title": "Video Watched",
            "description": f"{w.student.full_name} watched '{w.video.title if w.video else 'Lecture'}'",
            "time": _format_time_ago(w.watched_at),
            "badge": w.student.department.dept_name if w.student.department else "General",
        })

    return JsonResponse({
        "status": "success",
        "data": {
            "summaryCards": {
                "students": total_students,
                "activeStudents": active_students,
                "videos": total_videos,
                "totalViews": total_views,
                "watchTime": watch_time_str,
                "engagementRate": engagement_rate,
            },
            "dailyViews": daily_views,
            "topCategories": top_categories,
            "latestVideos": latest_videos_data,
            "recentViews": recent_views_data,
            "departmentPerformance": dept_performance,
            "liveActivities": live_activities,
            "collegeName": college.college_name if college else "Institutional Portal",
        }
    })


def api_principal_students(request):
    principal = get_authenticated_principal(request)

    if not principal:
        return JsonResponse({
            "status": "error",
            "message": "Please login"
        }, status=401)

    students = Student.objects.filter(
        college=principal.college
    ).select_related("department", "college")

    total_videos = Video.objects.count()
    data = []

    for student in students:
        join_date_value = student.join_date or getattr(student, "created_at", None)
        end_date_value = student.end_date

        student_watches = VideoWatch.objects.filter(student=student).select_related("video")
        viewed_videos_count = student_watches.values("video").distinct().count()
        total_student_views = student_watches.count()
        progress_pct = round((viewed_videos_count / total_videos) * 100) if total_videos > 0 else 0

        recent_vids = [
            {
                "title": sw.video.title,
                "date": _format_time_ago(sw.watched_at)
            }
            for sw in student_watches.order_by("-watched_at")[:4] if sw.video
        ]
        recent_acts = [
            f"Watched '{sw.video.title}' ({_format_time_ago(sw.watched_at)})"
            for sw in student_watches.order_by("-watched_at")[:4] if sw.video
        ]

        data.append({
            "id": student.id,
            "student_id": getattr(student, "student_id", student.username or f"STD{student.id}"),
            "full_name": student.full_name or "",
            "email": student.email or "",
            "phone": student.phone or "",
            "department": student.department.dept_name if student.department else "N/A",
            "year": student.year or "",
            "status": student.status or "active",
            "username": getattr(student, "username", None) or getattr(student, "student_id", None) or f"STD{student.id}",
            "password": getattr(student, "password", "********") or "********",
            "college": principal.college.college_name if principal.college else "N/A",
            "join_date": join_date_value.strftime("%Y-%m-%d") if join_date_value else "2026-07-21",
            "end_date": end_date_value.strftime("%Y-%m-%d") if end_date_value else "2030-07-21",
            "viewedVideos": viewed_videos_count,
            "totalVideos": total_videos,
            "totalViews": total_student_views,
            "progress": min(100, progress_pct),
            "lastLogin": _format_time_ago(student_watches.order_by("-watched_at").first().watched_at) if student_watches.exists() else "No recent login",
            "last_viewed": student_watches.order_by("-watched_at").first().watched_at.strftime("%Y-%m-%d") if student_watches.exists() and student_watches.order_by("-watched_at").first().watched_at else (join_date_value.strftime("%Y-%m-%d") if join_date_value else ""),
            "recentVideos": recent_vids,
            "recentActivity": recent_acts,
        })

    return JsonResponse({
        "status": "success",
        "college": principal.college.college_name if principal.college else "N/A",
        "total": len(data),
        "data": data
    })

def api_principal_student_delete(request, student_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    principal = get_authenticated_principal(request)
    if not principal:
        return JsonResponse({"status": "error", "message": "Unauthorized"}, status=401)

    student = Student.objects.filter(
        id=student_id,
        college=principal.college
    ).first()

    if not student:
        return JsonResponse({"status": "error", "message": "Student not found or unauthorized"}, status=404)

    student.delete()
    return JsonResponse({"status": "success", "message": "Student deleted successfully"})

@csrf_exempt
def api_principal_profile(request):
    try:
        principal = get_authenticated_principal(request)
        if not principal:
            return JsonResponse({"status": "error", "message": "No authenticated principal found"}, status=401)

        if request.method == "POST":
            import json
            data = {}
            if request.content_type == "application/json" and request.body:
                data = json.loads(request.body.decode("utf-8"))
            else:
                data = request.POST

            email = data.get("email")
            phone = data.get("phone")
            custom_bio = data.get("bio")
            avatar = data.get("avatar")
            cover_photo = data.get("cover_photo")

            if email:
                principal.principal_email = email.strip()
            if phone:
                principal.principal_mobile = phone.strip()
            if custom_bio is not None:
                principal.bio = custom_bio.strip()
            if avatar is not None:
                principal.avatar = avatar
            if cover_photo is not None:
                principal.cover_photo = cover_photo

            principal.save()

            default_bio = f"{principal.principal_name} is the Principal at {principal.college.college_name if principal.college else ''}."
            default_avatar = f"https://api.dicebear.com/7.x/avataaars/svg?seed={principal.principal_name}"

            return JsonResponse({
                "status": "success",
                "message": "Profile updated successfully",
                "data": {
                    "name": principal.principal_name,
                    "email": principal.principal_email,
                    "phone": principal.principal_mobile,
                    "college": principal.college.college_name if principal.college else "",
                    "joined": principal.created_at.strftime("%b %Y") if principal.created_at else "Aug 2015",
                    "avatar": principal.avatar if principal.avatar else default_avatar,
                    "cover_photo": principal.cover_photo if principal.cover_photo else "",
                    "bio": principal.bio if principal.bio else default_bio,
                    "username": principal.username,
                    "status": principal.status
                }
            })

        college = principal.college
        default_bio = f"{principal.principal_name} is the Principal at {college.college_name if college else ''}."
        default_avatar = f"https://api.dicebear.com/7.x/avataaars/svg?seed={principal.principal_name}"

        return JsonResponse({
            "status": "success",
            "data": {
                "name": principal.principal_name,
                "email": principal.principal_email,
                "phone": principal.principal_mobile,
                "college": college.college_name if college else "",
                "joined": principal.created_at.strftime("%b %Y") if college and principal.created_at else "Aug 2015",
                "avatar": principal.avatar if principal.avatar else default_avatar,
                "cover_photo": principal.cover_photo if principal.cover_photo else "",
                "bio": principal.bio if principal.bio else default_bio,
                "username": principal.username,
                "status": principal.status
            }
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)



def api_principal_departments(request):
    try:
        principal = get_authenticated_principal(request)

        if not principal or not principal.college:
            return JsonResponse({
                "status": "error",
                "message": "Unauthorized"
            }, status=401)

        departments = Department.objects.filter(
            college=principal.college,
            status="active"
        ).order_by("dept_name")

        dept_colors = ["blue", "indigo", "teal", "emerald", "amber", "purple", "rose"]
        data = []

        for idx, dept in enumerate(departments):
            student_count = dept.students.count()

            data.append({
                "id": dept.id,
                "name": dept.dept_name,
                "code": dept.dept_code,
                "hod": dept.hod_name,
                "email": dept.hod_email,
                "students": student_count,
                "videos": Video.objects.count(),
                "views": student_count * 12,
                "completionRate": 75 if student_count > 0 else 0,
                "performance": "High" if student_count > 10 else ("Average" if student_count > 0 else "Low"),
                "trend": "+5%",
                "color": dept_colors[idx % len(dept_colors)],
            })

        return JsonResponse({
            "status": "success",
            "college": principal.college.college_name,
            "total": len(data),
            "data": data
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)



def api_principal_videos(request):
    try:
        principal = get_authenticated_principal(request)
        if not principal:
            return JsonResponse({"status": "error", "message": "Unauthorized"}, status=401)

        # All students in this principal's college
        college_students = Student.objects.filter(college=principal.college) if (principal and principal.college) else Student.objects.all()

        category_param = request.GET.get("category")
        status_param = request.GET.get("status")
        query_param = request.GET.get("q") or request.GET.get("query")

        videos = Video.objects.all().order_by("-uploaded_at")
        if category_param and category_param != "All Categories":
            videos = videos.filter(category=category_param)
        if status_param and status_param != "All Status":
            videos = videos.filter(status=status_param)
        if query_param:
            videos = videos.filter(title__icontains=query_param.strip())

        data = []

        for video in videos:
            # Count unique students in this college who watched this video
            students_viewed = VideoWatch.objects.filter(
                video=video,
                student__in=college_students
            ).values("student").distinct().count()

            total_college_students = college_students.count()
            completion_rate = round((students_viewed / total_college_students) * 100) if total_college_students > 0 else 0

            # Thumbnail: first two letters of title in uppercase
            thumb_label = (video.title[:2]).upper() if video.title else "VD"

            uploader_name = f"System Admin ({principal.college.college_name if (principal and principal.college) else 'College'})"
            if video.uploaded_by_hod:
                hod_person = video.uploaded_by_hod.hod_name or "HOD"
                dept_title = video.uploaded_by_hod.dept_name or "Department"
                clg_title = video.uploaded_by_hod.college.college_name if (video.uploaded_by_hod.college) else (principal.college.college_name if (principal and principal.college) else "")
                uploader_name = f"{hod_person} | {dept_title} | {clg_title}".strip(" |")
            elif getattr(video, "uploaded_by_name", None):
                uploader_name = video.uploaded_by_name

            data.append({
                "id": str(video.id),
                "title": video.title,
                "category": video.category or "General",
                "duration": video.duration or "15 min",
                "views": video.views or 0,
                "uploadedDate": video.uploaded_at.strftime("%d %b %Y") if getattr(video, "uploaded_at", None) else "01 Jul 2026",
                "uploadedBy": uploader_name,
                "status": video.status or "Published",
                "studentsViewed": students_viewed,
                "completionRate": completion_rate,
                "description": video.description or "",
                "thumbnail": thumb_label,
                "videoUrl": request.build_absolute_uri(video.video_file.url) if (getattr(video, "video_file", None) and hasattr(video.video_file, "url") and video.video_file) else "",
            })

        # Department-wise view analytics strictly from VideoWatch
        dept_views_map = {}
        for vw in VideoWatch.objects.filter(student__in=college_students).select_related("student__department"):
            if vw.student and vw.student.department:
                dname = vw.student.department.dept_name
                dept_views_map[dname] = dept_views_map.get(dname, 0) + 1

        dept_breakdown = [
            {"department": dname, "views": count}
            for dname, count in dept_views_map.items()
        ]

        total_views = sum(v["views"] for v in data)

        return JsonResponse({
            "status": "success",
            "college": principal.college.college_name if (principal and principal.college) else "College",
            "total": len(data),
            "totalViews": total_views,
            "departmentBreakdown": dept_breakdown,
            "data": data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def api_principal_attendance_reports(request):
    try:
        principal = get_authenticated_principal(request)
        if not principal or not principal.college:
            return JsonResponse({"status": "error", "message": "Unauthorized"}, status=401)

        students = Student.objects.filter(college=principal.college)
        total_students = students.count()

        student_list = []
        dept_views_map = {}
        below_threshold_count = 0
        total_attendance_sum = 0

        dept_colors = ["bg-blue-500", "bg-amber-500", "bg-emerald-500", "bg-indigo-500", "bg-rose-500"]

        for std in students:
            dept_name = std.department.dept_name if std.department else "General"
            watches = VideoWatch.objects.filter(student=std)
            videos_watched = watches.values("video").distinct().count()

            # Calculate simulated attendance based on watched videos or default
            total_videos = Video.objects.count()
            if total_videos > 0:
                attendance_rate = min(100, round((videos_watched / total_videos) * 100))
            else:
                attendance_rate = 85

            if attendance_rate >= 75:
                status = "Safe"
            elif attendance_rate >= 70:
                status = "At Risk"
                below_threshold_count += 1
            else:
                status = "Critical"
                below_threshold_count += 1

            total_attendance_sum += attendance_rate
            streak = f"{videos_watched * 2} Days" if videos_watched > 0 else "0 Days"

            student_list.append({
                "id": std.username or f"S{std.id}",
                "name": std.full_name or std.username,
                "dept": dept_name,
                "attendance": attendance_rate,
                "status": status,
                "streak": streak
            })

            if dept_name not in dept_views_map:
                dept_views_map[dept_name] = {"total_rate": 0, "count": 0}
            dept_views_map[dept_name]["total_rate"] += attendance_rate
            dept_views_map[dept_name]["count"] += 1

        overall_attendance = round(total_attendance_sum / total_students, 1) if total_students > 0 else 84.2
        avg_daily_present = round(total_students * (overall_attendance / 100)) if total_students > 0 else 0

        summary_stats = [
            {"label": "Overall Attendance", "value": f"{overall_attendance}%", "trend": "+2.1%", "trendUp": True, "iconName": "Users", "color": "text-blue-600", "bg": "bg-blue-100"},
            {"label": "Avg. Daily Present", "value": f"{avg_daily_present:,}", "trend": "+1.4%", "trendUp": True, "iconName": "CheckCircle2", "color": "text-emerald-600", "bg": "bg-emerald-100"},
            {"label": "Below 75% Mark", "value": str(below_threshold_count), "trend": f"{below_threshold_count} students", "trendUp": False, "iconName": "UserX", "color": "text-rose-600", "bg": "bg-rose-100"},
            {"label": "Leave Requests", "value": "12", "trend": "Pending", "trendUp": None, "iconName": "Calendar", "color": "text-amber-600", "bg": "bg-amber-100"},
        ]

        dept_comparison = []
        for idx, (d_name, d_info) in enumerate(dept_views_map.items()):
            avg_rate = round(d_info["total_rate"] / d_info["count"]) if d_info["count"] > 0 else 0
            dept_comparison.append({
                "name": d_name,
                "rate": avg_rate,
                "color": dept_colors[idx % len(dept_colors)]
            })

        return JsonResponse({
            "status": "success",
            "college": principal.college.college_name,
            "summaryStats": summary_stats,
            "deptAttendance": dept_comparison,
            "belowThresholdCount": below_threshold_count,
            "data": student_list
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def student_login(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)
        email_or_username = data.get('email') or data.get('username')
        password = data.get('password')

        if not email_or_username or not password:
            return JsonResponse({"status": "error", "message": "Email/Username and password are required"}, status=400)

        # Authenticate against Student model (matches email or username)
        student = Student.objects.filter(
            Q(email__iexact=email_or_username) | Q(username__iexact=email_or_username),
            password=password
        ).first()

        if not student:
            return JsonResponse({"status": "error", "message": "Invalid email or password. Please check your credentials."}, status=401)

        if not student.is_verified:
            return JsonResponse({"status": "error", "message": "Email is not verified. Please complete OTP verification before logging in."}, status=403)

        if student.status != "active":
            return JsonResponse({"status": "error", "message": f"Account is currently {student.status}. Please contact administrator."}, status=403)

        student_data = {
            "id": student.id,
            "student_id": getattr(student, "student_id", student.username or f"STD{student.id}"),
            "full_name": student.full_name,
            "email": student.email,
            "username": student.username,
            "department": student.department.dept_name if student.department else "",
            "college": student.college.college_name if student.college else "",
            "year": student.year,
            "status": student.status,
        }

        return JsonResponse({
            "status": "success",
            "message": "Login successful",
            "student": student_data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def video_stream(request, video_id):
    """
    Streams a video file with HTTP Range Request support so browsers can seek.
    Returns 206 Partial Content when the client sends a Range header,
    or 200 OK with the full file if no Range header is present.
    """
    import os
    import mimetypes
    from django.http import StreamingHttpResponse, HttpResponse

    video = Video.objects.filter(id=video_id).first()
    if not video:
        return HttpResponse("Video not found.", status=404)

    # Check if a valid local video file exists on disk
    file_path = None
    if video.video_file:
        try:
            file_path = video.video_file.path
        except Exception:
            file_path = None

    if not file_path or not os.path.exists(file_path):
        # Fallback to external video URL redirect if provided
        if getattr(video, "video_url", None) and str(video.video_url).startswith("http"):
            from django.shortcuts import redirect
            return redirect(video.video_url)
        return HttpResponse("Video file missing on disk.", status=404)

    file_size = os.path.getsize(file_path)
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = "video/mp4"

    range_header = request.META.get("HTTP_RANGE", "").strip()
    CHUNK = 1024 * 1024  # 1 MB chunks

    if range_header:
        # Parse Range: bytes=start-end
        try:
            byte_range = range_header.replace("bytes=", "").split("-")
            first_byte = int(byte_range[0]) if byte_range[0] else 0
            last_byte = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1
        except (ValueError, IndexError):
            return HttpResponse(status=416)  # Range Not Satisfiable

        last_byte = min(last_byte, file_size - 1)
        length = last_byte - first_byte + 1

        def file_iterator(path, offset, chunk_size, remaining):
            with open(path, "rb") as f:
                f.seek(offset)
                while remaining > 0:
                    data = f.read(min(chunk_size, remaining))
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        response = StreamingHttpResponse(
            file_iterator(file_path, first_byte, CHUNK, length),
            status=206,
            content_type=content_type,
        )
        response["Content-Length"] = str(length)
        response["Content-Range"] = f"bytes {first_byte}-{last_byte}/{file_size}"
        response["Accept-Ranges"] = "bytes"
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Expose-Headers"] = "Content-Range, Accept-Ranges, Content-Length"
        return response
    else:
        # No Range header: stream entire file
        def full_iterator(path, chunk_size):
            with open(path, "rb") as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    yield data

        response = StreamingHttpResponse(
            full_iterator(file_path, CHUNK),
            status=200,
            content_type=content_type,
        )
        response["Content-Length"] = str(file_size)
        response["Accept-Ranges"] = "bytes"
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Expose-Headers"] = "Content-Range, Accept-Ranges, Content-Length"
        return response


@csrf_exempt
def api_student_dashboard(request):
    try:
        # Identify student strictly via header or session
        student_id_header = request.headers.get("X-Student-Id") or request.META.get("HTTP_X_STUDENT_ID")
        student = None
        if student_id_header and student_id_header != "0":
            student = Student.objects.filter(id=student_id_header).first()

        if not student:
            # Fallback to current authenticated student in request session if available
            student_session_id = request.session.get("student_id")
            if student_session_id:
                student = Student.objects.filter(id=student_session_id).first()

        if not student:
            return JsonResponse({"status": "error", "message": "Student session not found. Please log in."}, status=401)

        # Published assigned videos queryset
        videos_qs = Video.objects.filter(status="Published")

        total_videos = videos_qs.count()

        # Strict watch history records for THIS specific logged-in student
        watched_records = VideoWatch.objects.filter(student=student).select_related("video")
        completed_count = watched_records.filter(watched_seconds__gt=0).count()
        pending_count = max(0, total_videos - completed_count)

        total_watch_seconds = sum(w.watched_seconds for w in watched_records)
        watch_hours = round(total_watch_seconds / 3600, 1)

        # Build Continue Watching list for THIS student only
        recent_watches = VideoWatch.objects.filter(student=student, watched_seconds__gt=0).select_related("video").order_by("-watched_at")[:6]
        continue_watching = []
        for rw in recent_watches:
            v = rw.video
            progress_val = 0
            try:
                import re as _re
                dur_str = str(v.duration or "0")
                dur_mins = int(_re.search(r'\d+', dur_str).group()) if _re.search(r'\d+', dur_str) else 0
                dur_secs = dur_mins * 60
                if dur_secs > 0 and rw.watched_seconds > 0:
                    progress_val = min(100, round((rw.watched_seconds / dur_secs) * 100))
                elif rw.watched_seconds == 0:
                    progress_val = 0
            except Exception:
                progress_val = 0
            thumb_url = request.build_absolute_uri(v.thumbnail.url) if (v.thumbnail and hasattr(v.thumbnail, 'url')) else ""
            continue_watching.append({
                "id": v.id,
                "title": v.title,
                "subtitle": f"{v.category or 'General'} • {v.duration or 'N/A'}",
                "progress": progress_val,
                "badge": "Completed" if progress_val >= 95 else ("In Progress" if progress_val > 0 else "Not Started"),
                "video_url": request.build_absolute_uri(v.video_file.url) if v.video_file else (getattr(v, 'youtube_url', '') or ""),
                "thumbnail": thumb_url,
            })

        # Recently added published videos for the student
        recent_videos = videos_qs.order_by("-uploaded_at")[:6]
        recently_added = []
        for v in recent_videos:
            thumb_url = request.build_absolute_uri(v.thumbnail.url) if (v.thumbnail and hasattr(v.thumbnail, 'url')) else ""
            recently_added.append({
                "id": v.id,
                "title": v.title,
                "category": v.category or "General",
                "date": v.uploaded_at.strftime("%d %b %Y") if v.uploaded_at else "Recently",
                "duration": v.duration or "N/A",
                "video_url": request.build_absolute_uri(v.video_file.url) if v.video_file else (getattr(v, 'youtube_url', '') or ""),
                "thumbnail": thumb_url,
            })

        # Top Categories dynamically computed from published videos
        cat_counts = videos_qs.values('category').annotate(count=Count('id')).order_by('-count')
        top_categories = []
        for item in cat_counts:
            c_name = item['category'] or "General"
            top_categories.append({
                "name": c_name,
                "count": f"{item['count']} videos"
            })

        # Recommended videos dynamically based on published videos
        rec_qs = videos_qs.order_by("-views", "-uploaded_at")[:4]
        recommended_videos = []
        for v in rec_qs:
            thumb_url = request.build_absolute_uri(v.thumbnail.url) if (v.thumbnail and hasattr(v.thumbnail, 'url')) else ""
            recommended_videos.append({
                "id": v.id,
                "title": v.title,
                "category": v.category or "General",
                "duration": v.duration or "15:00",
                "rating": "4.8",
                "views": f"{v.views} views",
                "video_url": request.build_absolute_uri(v.video_file.url) if v.video_file else (getattr(v, 'youtube_url', '') or ""),
                "thumbnail": thumb_url,
            })

        return JsonResponse({
            "status": "success",
            "student": {
                "id": student.id,
                "full_name": student.full_name,
                "student_id": getattr(student, "student_id", student.username or f"STD{student.id}"),
                "department": student.department.dept_name if student.department else "General",
            },
            "stats": {
                "totalVideos": total_videos,
                "completed": completed_count,
                "pending": pending_count,
                "watchHours": f"{watch_hours}h",
            },
            "continueWatching": continue_watching,
            "recentlyAdded": recently_added,
            "topCategories": top_categories,
            "recommendedVideos": recommended_videos,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def api_student_videos(request):
    try:
        import re
        student_id_header = request.headers.get("X-Student-Id") or request.META.get("HTTP_X_STUDENT_ID")
        student = None
        if student_id_header:
            student = Student.objects.filter(id=student_id_header).first()
        search = request.GET.get("search", "").strip()
        category_filter = request.GET.get("category", "").strip()

        videos_qs = Video.objects.filter(status="Published").order_by("-uploaded_at")
        if search:
            videos_qs = videos_qs.filter(Q(title__icontains=search) | Q(category__icontains=search))
        if category_filter and category_filter != "All":
            videos_qs = videos_qs.filter(category=category_filter)
        watched_ids = set()
        watched_seconds_map = {}  # video_id -> watched_seconds
        if student:
            watch_records = VideoWatch.objects.filter(student=student).values("video_id", "watched_seconds")
            for wr in watch_records:
                watched_ids.add(wr["video_id"])
                watched_seconds_map[wr["video_id"]] = wr["watched_seconds"]

        videos_data = []
        for v in videos_qs:
            mins = 0
            if v.duration:
                m = re.search(r'\d+', str(v.duration))
                if m:
                    mins = int(m.group())

            # Compute real progress percentage from watched_seconds
            duration_secs = mins * 60
            vid_watched_seconds = watched_seconds_map.get(v.id, 0)
            if duration_secs > 0 and vid_watched_seconds > 0:
                progress_pct = min(100, round((vid_watched_seconds / duration_secs) * 100))
            else:
                progress_pct = 100 if (v.id in watched_ids and vid_watched_seconds == 0) else 0

            thumb_url = request.build_absolute_uri(v.thumbnail.url) if (v.thumbnail and hasattr(v.thumbnail, 'url')) else ""
            videos_data.append({
                "id": v.id,
                "title": v.title,
                "category": v.category or "General",
                "duration": v.duration or "N/A",
                "description": v.description or "",
                "video_url": request.build_absolute_uri(v.video_file.url) if v.video_file else "",
                "thumbnail_url": thumb_url,
                "views": v.views,
                "uploaded_at": v.uploaded_at.strftime("%d %b %Y") if v.uploaded_at else "",
                "watched": v.id in watched_ids,
                "watched_seconds": vid_watched_seconds,
                "progress": progress_pct,
            })

        # Category list for filter
        raw_cats = Video.objects.filter(status="Published").values_list("category", flat=True).distinct()
        categories = list(dict.fromkeys([c for c in raw_cats if c]))

        return JsonResponse({
            "status": "success",
            "videos": videos_data,
            "categories": ["All"] + categories,
            "total": len(videos_data),
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def api_student_watch_history(request):
    try:
        student_id_header = request.headers.get("X-Student-Id") or request.META.get("HTTP_X_STUDENT_ID")
        student = None
        if student_id_header:
            student = Student.objects.filter(id=student_id_header).first()

        if not student:
            student = Student.objects.filter(status="active").first()

        if not student:
            return JsonResponse({"status": "error", "message": "No active student found"}, status=404)

        history_qs = VideoWatch.objects.filter(student=student).select_related("video").order_by("-watched_at")

        history_data = []
        for w in history_qs:
            v = w.video
            history_data.append({
                "id": w.id,
                "video_id": v.id,
                "title": v.title,
                "category": v.category or "General",
                "duration": v.duration or "N/A",
                "watched_at": w.watched_at.strftime("%d %b %Y, %I:%M %p") if w.watched_at else "",
                "completed": True,
                "video_url": v.video_file.url if v.video_file else "",
            })

        return JsonResponse({
            "status": "success",
            "history": history_data,
            "total": len(history_data),
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def api_student_record_watch(request, video_id):
    """Records that a student has started/rewatched a video.
    View count is incremented ONLY on the first watch per student.
    Rewatches update the timestamp but do NOT add to the count.
    """
    try:
        student_id_header = request.headers.get("X-Student-Id") or request.META.get("HTTP_X_STUDENT_ID")
        student = None
        if student_id_header:
            student = Student.objects.filter(id=student_id_header).first()

        video = Video.objects.filter(id=video_id).first()
        if not video:
            return JsonResponse({"status": "error", "message": "Video not found"}, status=404)

        if student:
            # Only count as a new view if this student has NOT watched it before
            watch_obj, created = VideoWatch.objects.get_or_create(
                student=student,
                video=video,
                defaults={"watched_at": timezone.now()},
            )
            if not created:
                # Already watched before — just refresh the timestamp, don't increment views
                watch_obj.watched_at = timezone.now()
                watch_obj.save(update_fields=["watched_at"])
            else:
                # First time this student watches — count it
                video.views += 1
                video.save(update_fields=["views"])
        else:
            # Anonymous viewer — always count (no dedup possible without identity)
            video.views += 1
            video.save(update_fields=["views"])

        return JsonResponse({
            "status": "success",
            "message": "Watch recorded successfully",
            "views": video.views,
            "is_new_view": student is not None,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def api_student_save_progress(request, video_id):
    if request.method not in ("POST", "PATCH"):
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
    try:
        import json
        student_id_header = request.headers.get("X-Student-Id") or request.META.get("HTTP_X_STUDENT_ID")
        student = None
        if student_id_header:
            student = Student.objects.filter(id=student_id_header).first()
        if not student:
            return JsonResponse({"status": "error", "message": "Student not identified"}, status=401)

        video = Video.objects.filter(id=video_id).first()
        if not video:
            return JsonResponse({"status": "error", "message": "Video not found"}, status=404)

        body = json.loads(request.body or "{}")
        watched_seconds = int(body.get("watched_seconds", 0))

        watch_obj, created = VideoWatch.objects.get_or_create(
            student=student,
            video=video,
            defaults={"watched_at": timezone.now(), "watched_seconds": watched_seconds},
        )
        if not created:
            # Only update if the new position is further along
            if watched_seconds > watch_obj.watched_seconds:
                watch_obj.watched_seconds = watched_seconds
            watch_obj.watched_at = timezone.now()
            watch_obj.save(update_fields=["watched_seconds", "watched_at"])

        return JsonResponse({
            "status": "success",
            "watched_seconds": watch_obj.watched_seconds,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def api_student_delete_watch_history(request, history_id=None):
    """Deletes single watch history item or clears all history for the student."""
    try:
        student_id_header = request.headers.get("X-Student-Id") or request.META.get("HTTP_X_STUDENT_ID")
        student = None
        if student_id_header:
            student = Student.objects.filter(id=student_id_header).first()

        if not student:
            student = Student.objects.filter(status="active").first()

        if not student:
            return JsonResponse({"status": "error", "message": "No active student found"}, status=404)

        if history_id:
            VideoWatch.objects.filter(id=history_id, student=student).delete()
        else:
            VideoWatch.objects.filter(student=student).delete()

        return JsonResponse({
            "status": "success",
            "message": "Watch history deleted successfully"
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def api_student_progress(request):
    """
    Aggregates real progress analytics for a student:
    - Student profile info
    - Weekly watch time (last 7 days, per day in hours)
    - Monthly progress trend (last 6 months, % completion)
    - Category-wise completion breakdown
    - KPI stats (total videos, completed, watch hours, completion %)
    - Recent video activity (last watched sessions)
    """
    import re
    from datetime import timedelta
    from django.utils import timezone
    from django.db.models import Sum, Count

    try:
        student_id_header = request.headers.get("X-Student-Id") or request.META.get("HTTP_X_STUDENT_ID")
        student = None
        if student_id_header and student_id_header != "0":
            try:
                student = Student.objects.filter(id=int(student_id_header)).first()
            except (ValueError, TypeError):
                pass

        if not student:
            student_session_id = request.session.get("student_id")
            if student_session_id:
                student = Student.objects.filter(id=student_session_id).first()

        if not student:
            return JsonResponse({"status": "error", "message": "Student session not found. Please log in."}, status=401)

        # ------------------------------------------------------------------
        # Helper: parse duration string "45 mins" / "1h 30m" -> seconds
        # ------------------------------------------------------------------
        def duration_to_secs(dur_str):
            if not dur_str:
                return 0
            total = 0
            h = re.search(r'(\d+)\s*h', str(dur_str))
            m = re.search(r'(\d+)\s*(min|m\b)', str(dur_str))
            if h:
                total += int(h.group(1)) * 3600
            if m:
                total += int(m.group(1)) * 60
            if total == 0:
                digits = re.search(r'(\d+)', str(dur_str))
                if digits:
                    total = int(digits.group(1)) * 60
            return total

        # ------------------------------------------------------------------
        # All published videos
        # ------------------------------------------------------------------
        all_videos = Video.objects.filter(status="Published")
        total_videos = all_videos.count()

        # Watch records for this student
        watch_qs = VideoWatch.objects.filter(student=student, watched_seconds__gt=0).select_related("video")
        has_watch_history = watch_qs.exists()

        if not has_watch_history:
            dept = student.department
            college = student.college
            student_data = {
                "id": student.id,
                "full_name": student.full_name,
                "email": student.email,
                "phone": student.phone or "",
                "username": student.username or "",
                "status": student.status,
                "year": student.year or "",
                "department_name": dept.dept_name if dept else "",
                "college_name": college.college_name if college else "",
                "hod_name": dept.hod_name if dept else "",
                "join_date": student.join_date.strftime("%d %b %Y") if student.join_date else "",
                "end_date": student.end_date.strftime("%b %Y") if student.end_date else "",
            }
            return JsonResponse({
                "status": "success",
                "student": student_data,
                "stats": {
                    "totalVideos": total_videos,
                    "completed": 0,
                    "pending": total_videos,
                    "watchHours": 0,
                    "completionPct": 0,
                },
                "weeklyWatchTime": [],
                "monthlyTrend": [],
                "categoryBreakdown": [],
                "recentVideos": [],
            })

        # ------------------------------------------------------------------
        # KPI: completed, watch hours, completion %
        # ------------------------------------------------------------------
        completed_count = 0
        total_watched_secs = 0
        for w in watch_qs:
            total_watched_secs += w.watched_seconds or 0
            dur_secs = duration_to_secs(w.video.duration)
            if dur_secs > 0:
                pct = (w.watched_seconds or 0) / dur_secs * 100
                if pct >= 90:
                    completed_count += 1
            else:
                # No duration info — count as complete if watched at all
                completed_count += 1

        watch_hours_total = round(total_watched_secs / 3600, 1)
        overall_completion_pct = round((completed_count / total_videos) * 100) if total_videos > 0 else 0

        # ------------------------------------------------------------------
        # Weekly Watch Time — last 7 days (Mon … Sun or today-6 … today)
        # ------------------------------------------------------------------
        now = timezone.now()
        today = now.date()
        DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        weekly_watch_time = []
        for i in range(6, -1, -1):
            day_date = today - timedelta(days=i)
            day_label = DAYS[day_date.weekday()]
            day_watches = watch_qs.filter(watched_at__date=day_date)
            day_secs = sum(w.watched_seconds or 0 for w in day_watches)
            weekly_watch_time.append({
                "day": day_label,
                "hours": round(day_secs / 3600, 2),
                "date": day_date.strftime("%d %b"),
            })

        # ------------------------------------------------------------------
        # Monthly Progress Trend — last 6 months
        # ------------------------------------------------------------------
        monthly_trend = []
        for i in range(5, -1, -1):
            # Go back i full months from today
            month_date = today.replace(day=1)
            for _ in range(i):
                month_date = (month_date - timedelta(days=1)).replace(day=1)
            month_label = month_date.strftime("%b")
            month_end = (month_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            # Videos watched strictly by this student up to end of this month
            watched_by_month = watch_qs.filter(watched_at__date__lte=month_end, watched_seconds__gt=0).count()
            pct = round((watched_by_month / total_videos) * 100) if total_videos > 0 else 0
            monthly_trend.append({"month": month_label, "progress": min(pct, 100)})

        # ------------------------------------------------------------------
        # Category-wise completion breakdown
        # ------------------------------------------------------------------
        category_breakdown = []
        categories_qs = all_videos.values_list("category", flat=True).distinct()
        for cat in categories_qs:
            if not cat:
                continue
            cat_total = all_videos.filter(category=cat).count()
            cat_watched_ids = watch_qs.filter(video__category=cat).values_list("video_id", flat=True)
            cat_completed = 0
            for w in watch_qs.filter(video__category=cat):
                dur_secs = duration_to_secs(w.video.duration)
                if dur_secs > 0:
                    pct = (w.watched_seconds or 0) / dur_secs * 100
                    if pct >= 90:
                        cat_completed += 1
                else:
                    cat_completed += 1
            cat_pct = round((cat_completed / cat_total) * 100) if cat_total > 0 else 0
            category_breakdown.append({
                "category": cat,
                "total": cat_total,
                "completed": cat_completed,
                "percent": cat_pct,
            })

        # Sort by percent descending
        category_breakdown.sort(key=lambda x: x["percent"], reverse=True)

        # ------------------------------------------------------------------
        # Recent video activity (last 10 watch records)
        # ------------------------------------------------------------------
        recent_watches = watch_qs.order_by("-watched_at")[:10]
        recent_videos = []
        for w in recent_watches:
            v = w.video
            dur_secs = duration_to_secs(v.duration)
            progress_pct = 0
            if dur_secs > 0 and w.watched_seconds:
                progress_pct = min(100, round((w.watched_seconds / dur_secs) * 100))
            elif w.watched_seconds == 0 and v.id in watched_video_ids:
                progress_pct = 100
            thumb = request.build_absolute_uri(v.thumbnail.url) if (v.thumbnail and hasattr(v.thumbnail, 'url')) else ""
            recent_videos.append({
                "id": w.id,
                "video_id": v.id,
                "title": v.title,
                "subtitle": v.category or "General",
                "category": v.category or "General",
                "duration": v.duration or "N/A",
                "date": w.watched_at.strftime("%d %b %Y, %I:%M %p") if w.watched_at else "",
                "progress": progress_pct,
                "thumbnail": thumb,
                "completed": progress_pct >= 90,
            })

        # ------------------------------------------------------------------
        # Student profile fields
        # ------------------------------------------------------------------
        dept = student.department
        college = student.college
        student_data = {
            "id": student.id,
            "full_name": student.full_name,
            "email": student.email,
            "phone": student.phone or "",
            "username": student.username or "",
            "status": student.status,
            "year": student.year or "",
            "department_name": dept.dept_name if dept else "",
            "college_name": college.college_name if college else "",
            "hod_name": dept.hod_name if dept else "",
            "join_date": student.join_date.strftime("%d %b %Y") if student.join_date else "",
            "end_date": student.end_date.strftime("%b %Y") if student.end_date else "",
        }

        has_watch_history = watch_qs.filter(watched_seconds__gt=0).exists()

        return JsonResponse({
            "status": "success",
            "student": student_data,
            "stats": {
                "totalVideos": total_videos,
                "completed": completed_count,
                "pending": max(0, total_videos - completed_count),
                "watchHours": watch_hours_total,
                "completionPct": overall_completion_pct,
            },
            "weeklyWatchTime": weekly_watch_time if has_watch_history else [],
            "monthlyTrend": monthly_trend if has_watch_history else [],
            "categoryBreakdown": category_breakdown if has_watch_history else [],
            "recentVideos": recent_videos if has_watch_history else [],
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)



# --hodlogin-------------------------------------------




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# ---------------------------------------------------
# HOD Authentication Helper
# ---------------------------------------------------
def get_authenticated_hod(request):
    hod_id = (
        request.headers.get("X-Hod-Id")
        or request.session.get("hod_id")
        or request.GET.get("hod_id")
    )

    if not hod_id:
        return None

    return (
        Department.objects
        .select_related("college")
        .filter(id=hod_id, status="active")
        .first()
    )


# ---------------------------------------------------
# HOD Login
# ---------------------------------------------------
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def hod_login(request):

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        hod = Department.objects.select_related("college").filter(
            username__iexact=username,
            password=password
        ).first()

        if not hod:
            return JsonResponse({
                "success": False,
                "message": "Invalid Username or Password"
            }, status=401)

        if hasattr(hod, "status") and hod.status and hod.status != "active":
            return JsonResponse({
                "success": False,
                "message": "Department account is inactive. Please contact administrator."
            }, status=401)

        request.session["hod_id"] = hod.id

        return JsonResponse({
            "success": True,
            "message": "Login Successful",

            "user": {
                "id": hod.id,
                "name": hod.hod_name,
                "department": hod.dept_name,
                "college": hod.college.college_name if hod.college else "Institution",
                "username": hod.username
            }
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)


def get_authenticated_hod(request):
    hod_id = request.session.get("hod_id")

    if not hod_id:
        hod_id = request.headers.get("X-Hod-Id")

    if not hod_id:
        hod_id = request.GET.get("hod_id")

    if hod_id:
        try:
            return Department.objects.select_related("college").get(
                id=hod_id,
                status="active"
            )
        except (Department.DoesNotExist, ValueError):
            pass

    return Department.objects.select_related("college").filter(status="active").first()
    
@csrf_exempt
def api_hod_dashboard(request):

    if request.method != "GET":
        return JsonResponse({"status":"error"}, status=405)

    hod = get_authenticated_hod(request)

    if not hod:
        return JsonResponse({
            "status":"error",
            "message":"Unauthorized"
        }, status=401)

    students = Student.objects.filter(
        department=hod,
        college=hod.college,
    ).select_related("college", "department")

    total_students = students.count()
    active_students = students.filter(status="active").count()

    watched_videos = VideoWatch.objects.filter(
        student__department=hod,
        student__college=hod.college,
    )
    total_videos = watched_videos.values("video").distinct().count()

    all_videos = Video.objects.all()
    total_video_views = all_videos.aggregate(total_views=Sum("views"))["total_views"] or 0
    this_month_videos = all_videos.filter(
        uploaded_at__year=timezone.now().year,
        uploaded_at__month=timezone.now().month,
    ).count()
    this_month_views = watched_videos.filter(
        watched_at__year=timezone.now().year,
        watched_at__month=timezone.now().month,
    ).count()

    period = request.GET.get("period", "week")
    engagement_data = []

    if period == "month":
        # 4 Weeks breakdown for the month
        for i in range(3, -1, -1):
            start_d = timezone.now().date() - timedelta(days=(i + 1) * 7 - 1)
            end_d = timezone.now().date() - timedelta(days=i * 7)
            count = (
                watched_videos.filter(watched_at__date__range=(start_d, end_d))
                .values("student")
                .distinct()
                .count()
            )
            pct = int(round((count / max(total_students, 1)) * 100)) if total_students else 0
            engagement_data.append({
                "day": f"W{4 - i}",
                "value": min(100, pct),
            })
    else:
        # 7 Days breakdown for the week
        for offset in range(6, -1, -1):
            day = timezone.now().date() - timedelta(days=offset)
            day_count = (
                watched_videos.filter(watched_at__date=day)
                .values("student")
                .distinct()
                .count()
            )
            pct = int(round((day_count / max(total_students, 1)) * 100)) if total_students else 0
            engagement_data.append({
                "day": day.strftime("%a"),
                "value": min(100, pct),
            })

    top_students_qs = students.annotate(
        watched_videos=Count("watch_history", distinct=True),
        last_watch=Max("watch_history__watched_at"),
    ).order_by("-id")[:5]

    top_students = []
    for index, student in enumerate(top_students_qs, start=1):
        watched_count = student.watched_videos or 0
        score = int(round((watched_count / max(total_videos, 1)) * 100)) if total_videos else 0
        top_students.append({
            "rank": index,
            "name": student.full_name,
            "year": student.year,
            "score": max(0, min(100, score)),
        })

    recent_activities = []
    for watch in watched_videos.select_related("student", "video").order_by("-watched_at")[:5]:
        completed = watch.watched_seconds >= 60
        recent_activities.append({
            "id": watch.id,
            "name": watch.student.full_name,
            "action": f"{'completed' if completed else 'watched'} \"{watch.video.title}\"",
            "time": _format_time_ago(watch.watched_at),
            "icon": "check" if completed else "play",
            "color": "green" if completed else "purple",
        })

    recent_videos = []
    for video in all_videos.order_by("-uploaded_at")[:4]:
        recent_videos.append({
            "id": video.id,
            "title": video.title,
            "sub": f"Uploaded {video.uploaded_at.strftime('%b %d')}",
            "views": video.views,
            "status": video.status,
            "bgColor": ["#3776ab", "#092e20", "#1e2338", "#e34c26"][len(recent_videos) % 4],
            "emoji": ["🎥", "📘", "🧠", "🌐"][len(recent_videos) % 4],
        })

    year_distribution = []
    year_order = ["I", "II", "III", "IV"]
    year_colors = {
        "I": "#4f6cf7",
        "II": "#22c55e",
        "III": "#f97316",
        "IV": "#06b6d4",
    }
    for year in year_order:
        count = students.filter(year=year).count()
        percent = round((count / total_students) * 100, 1) if total_students else 0
        year_distribution.append({
            "label": f"{year} Year",
            "count": count,
            "percent": percent,
            "color": year_colors.get(year, "#4f6cf7"),
        })

    quick_overview = [
        {"label": "Total Videos", "value": str(all_videos.count()), "icon": "video-sm", "color": "purple"},
        {"label": "Total Views", "value": f"{total_video_views:,}", "icon": "eye-sm", "color": "blue"},
        {"label": "Videos This Month", "value": str(this_month_videos), "icon": "calendar-sm", "color": "red"},
    ]

    return JsonResponse({
        "status":"success",
        "hod":{
            "name":hod.hod_name,
            "department":hod.dept_name,
            "college":hod.college.college_name,
        },
        "stats":{
            "totalStudents":total_students,
            "activeStudents":active_students,
            "totalVideos":total_videos,
            "totalViews":total_video_views,
            "monthViews":this_month_views,
        },
        "engagementData": engagement_data,
        "topStudents": top_students,
        "recentActivities": recent_activities,
        "recentVideos": recent_videos,
        "yearDistribution": year_distribution,
        "quickOverview": quick_overview,
    })


@csrf_exempt
def api_hod_videos(request):

    if request.method != "GET":
        return JsonResponse({"status": "error"}, status=405)

    hod = get_authenticated_hod(request)

    if not hod:
        return JsonResponse({
            "status": "error",
            "message": "Unauthorized"
        }, status=401)

    videos = (
        Video.objects
        .filter(status="Published")
        .select_related("uploaded_by_hod")
        .order_by("-uploaded_at")
    )

    data = []

    for video in videos:

        # Uploaded By
        if video.is_admin_video:
            uploaded_by = "Admin"
        elif video.uploaded_by_hod:
            uploaded_by = video.uploaded_by_hod.hod_name
        else:
            uploaded_by = "Unknown"

        data.append({
            "id": video.id,
            "title": video.title,
            "category": video.category,
            "duration": video.duration,
            "description": video.description or "",
            "views": video.views or 0,
            "uploadDate": (
                video.uploaded_at.strftime("%d %b %Y")
                if video.uploaded_at else ""
            ),
            "uploadedBy": uploaded_by,
            "status": video.status,
            "thumbnail": (
                request.build_absolute_uri(video.thumbnail.url)
                if video.thumbnail else ""
            ),
            "videoUrl": (
                request.build_absolute_uri(video.video_file.url)
                if video.video_file else ""
            ),

            # Only current HOD uploads
            "isMine": (
                video.uploaded_by_hod_id == hod.id
            ),
        })

    return JsonResponse({
        "status": "success",
        "college": hod.college.college_name,
        "department": hod.dept_name,
        "total": len(data),
        "videos": data,
    })


@csrf_exempt
def api_hod_video_upload(request):

    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "Method Not Allowed"
        }, status=405)

    hod = get_authenticated_hod(request)

    if not hod:
        return JsonResponse({
            "status": "error",
            "message": "Unauthorized"
        }, status=401)

    title = request.POST.get("title")
    category = request.POST.get("category")
    duration = request.POST.get("duration")
    description = request.POST.get("description", "")

    # Frontend அனுப்பும் key-க்கு match ஆக வேண்டும்
    video_file = request.FILES.get("video")
    thumbnail = request.FILES.get("thumbnail")

    if not all([title, category, duration, video_file, thumbnail]):
        return JsonResponse({
            "status": "error",
            "message": "All fields are required."
        }, status=400)

    video = Video.objects.create(
        title=title,
        category=category,
        duration=duration,
        description=description,
        status="Published",
        video_file=video_file,
        thumbnail=thumbnail,
        uploaded_by_hod=hod,
        is_admin_video=False,
    )

    return JsonResponse({
        "status": "success",
        "message": "Video uploaded successfully.",
        "video": {
            "id": video.id,
            "title": video.title,
            "category": video.category,
            "duration": video.duration,
            "description": video.description,
            "uploadedBy": hod.hod_name,
            "uploadDate": video.uploaded_at.strftime("%d %b %Y"),
            "thumbnail": request.build_absolute_uri(video.thumbnail.url),
            "videoUrl": request.build_absolute_uri(video.video_file.url),
            "views": video.views,
            "status": video.status,
            "isMine": True,
        }
    })


@csrf_exempt
def api_hod_video_delete(request, video_id):

    if request.method != "DELETE":
        return JsonResponse(
            {"status": "error", "message": "Method not allowed"},
            status=405,
        )

    hod = get_authenticated_hod(request)

    if not hod:
        return JsonResponse(
            {"status": "error", "message": "Unauthorized"},
            status=401,
        )

    video = Video.objects.filter(
        id=video_id,
        uploaded_by_hod=hod
    ).first()

    if not video:
        return JsonResponse(
            {"status": "error", "message": "Video not found"},
            status=404,
        )

    video.delete()

    return JsonResponse({
        "status": "success",
        "message": "Video deleted successfully"
    })
 
@csrf_exempt
def api_hod_performance(request):

    if request.method != "GET":
        return JsonResponse({"status":"error"}, status=405)

    hod = get_authenticated_hod(request)

    if not hod:
        return JsonResponse({
            "status":"error",
            "message":"Unauthorized"
        }, status=401)

    students = Student.objects.filter(
        department=hod,
        college=hod.college,
    ).select_related("college", "department")

    watched_videos = VideoWatch.objects.filter(
        student__department=hod
    ).select_related("student", "video")

    total_students = students.count()
    active_students = students.filter(status="active").count()

    video_count = Video.objects.filter(status="Published").count()
    total_views = Video.objects.aggregate(total_views=Sum("views"))["total_views"] or 0

    avg_watch_mins = int((watched_videos.aggregate(total=Sum("watched_seconds"))["total"] or 0) // 60)
    avg_watch_time_mins = round(avg_watch_mins / total_students) if total_students > 0 else 0

    weekly_views = []
    for offset in range(6, -1, -1):
        day = timezone.now().date() - timedelta(days=offset)
        count = watched_videos.filter(watched_at__date=day).count()
        weekly_views.append({
            "label": day.strftime("%a"),
            "value": count,
        })

    weekly_active = []
    for offset in range(6, -1, -1):
        day = timezone.now().date() - timedelta(days=offset)
        active_cnt = (
            watched_videos.filter(watched_at__date=day)
            .values("student")
            .distinct()
            .count()
        )
        weekly_active.append({
            "label": day.strftime("%a"),
            "value": active_cnt,
        })

    student_rows = []
    for student in students.order_by("full_name"):
        student_watch_history = watched_videos.filter(student=student)
        watched_seconds = int(student_watch_history.aggregate(total=Sum("watched_seconds"))["total"] or 0)
        watched_count = student_watch_history.values("video").distinct().count()
        completion_pct = min(100, int(round((watched_count / max(1, video_count)) * 100))) if video_count else 0
        last_watch = student_watch_history.order_by("-watched_at").first()

        student_rows.append({
            "id": student.id,
            "name": student.full_name,
            "videosWatched": watched_count,
            "videosTotal": video_count,
            "watchTimeMinutes": max(0, watched_seconds // 60),
            "completion": completion_pct,
            "lastActivity": _format_time_ago(last_watch.watched_at) if last_watch else "No activity",
        })

    most_watched = []
    top_vids = Video.objects.filter(status="Published").order_by("-views")[:5]
    total_top_views = sum(v.views or 0 for v in top_vids) or 1
    palette = ["#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6", "#ec4899"]

    for idx, video in enumerate(top_vids):
        v_views = video.views or 0
        pct = round((v_views / total_top_views) * 100)
        most_watched.append({
            "name": video.title,
            "value": v_views,
            "percent": pct,
            "color": palette[idx % len(palette)],
        })

    overall_completion = round(sum(s["completion"] for s in student_rows) / len(student_rows)) if student_rows else 0

    return JsonResponse({
        "status": "success",
        "hod": {
            "name": hod.hod_name,
            "department": hod.dept_name,
            "college": hod.college.college_name if hod.college else "Institutional Portal",
        },
        "dateRange": f"{(timezone.now() - timedelta(days=7)).strftime('%d %b %Y')} – {timezone.now().strftime('%d %b %Y')}",
        "stats": {
            "totalStudents": total_students,
            "activeStudents": active_students,
            "totalVideos": video_count,
            "totalViews": total_views,
            "avgWatchTimeMinutes": avg_watch_time_mins,
            "completionRate": overall_completion,
        },
        "videoViewsWeek": weekly_views,
        "mostWatchedVideos": most_watched,
        "weeklyActiveStudents": weekly_active,
        "students": student_rows,
    })


@csrf_exempt
def api_hod_students(request):

    if request.method != "GET":
        return JsonResponse({"status":"error"}, status=405)

    hod = get_authenticated_hod(request)

    if not hod:
        return JsonResponse({
            "status":"error",
            "message":"Unauthorized"
        }, status=401)

    students = Student.objects.filter(
        department=hod,
        college=hod.college,
    ).select_related(
        "college",
        "department"
    ).order_by("full_name")

    data = []

    for student in students:
       data.append({
    "id": student.id,
    "name": student.full_name,
    "username": student.username,
    "password": student.password,
    "email": student.email,
    "phone": student.phone,
    "year": student.year,
    "joinDate": student.join_date,
    "status": student.status,
    "college": student.college.college_name,
    "department": student.department.dept_name,
}) 

    return JsonResponse({
        "status": "success",
        "college": hod.college.college_name,
        "department": hod.dept_name,
        "totalStudents": len(data),
        "students": data,
    })





@csrf_exempt
def api_hod_profile(request):
    try:
        hod = get_authenticated_hod(request)
        if not hod:
            return JsonResponse({"status": "error", "message": "Unauthorized"}, status=401)

        if request.method == "POST":
            import json
            data = {}
            if request.content_type == "application/json" and request.body:
                data = json.loads(request.body.decode("utf-8"))
            else:
                data = request.POST

            email = data.get("email")
            phone = data.get("phone")
            custom_bio = data.get("bio")
            avatar = data.get("avatar")
            cover_photo = data.get("cover_photo")

            if email:
                hod.hod_email = email.strip()
            if phone:
                hod.hod_phone = phone.strip()
            if custom_bio is not None:
                hod.bio = custom_bio.strip()
            if avatar is not None:
                hod.avatar = avatar
            if cover_photo is not None:
                hod.cover_photo = cover_photo

            hod.save()

            default_bio = f"{hod.hod_name} is the Head of Department for {hod.dept_name} at {hod.college.college_name if hod.college else ''}."
            default_avatar = ""

            return JsonResponse({
                "status": "success",
                "message": "Profile updated successfully",
                "data": {
                    "id": hod.id,
                    "name": hod.hod_name,
                    "email": hod.hod_email,
                    "phone": hod.hod_phone,
                    "department": hod.dept_name,
                    "college": hod.college.college_name if hod.college else "",
                    "joined": hod.created_at.strftime("%b %Y") if hod.created_at else "Aug 2018",
                    "avatar": hod.avatar if hod.avatar else default_avatar,
                    "cover_photo": hod.cover_photo if hod.cover_photo else "",
                    "bio": hod.bio if hod.bio else default_bio,
                    "username": hod.username,
                    "status": hod.status
                }
            })

        default_bio = f"{hod.hod_name} is the Head of Department for {hod.dept_name} at {hod.college.college_name if hod.college else ''}."
        default_avatar = ""

        return JsonResponse({
            "status": "success",
            "data": {
                "id": hod.id,
                "name": hod.hod_name,
                "email": hod.hod_email,
                "phone": hod.hod_phone,
                "department": hod.dept_name,
                "college": hod.college.college_name if hod.college else "",
                "joined": hod.created_at.strftime("%b %Y") if hod.created_at else "Aug 2018",
                "avatar": hod.avatar if hod.avatar else default_avatar,
                "cover_photo": hod.cover_photo if hod.cover_photo else "",
                "bio": hod.bio if hod.bio else default_bio,
                "username": hod.username,
                "status": hod.status
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# ==========================================================
# VIDEO APPROVAL WORKFLOW API ENDPOINTS
# ==========================================================

@csrf_exempt
def api_hod_videos(request):
    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    hod = get_authenticated_hod(request)
    if not hod:
        return JsonResponse({"status": "error", "message": "Unauthorized"}, status=401)

    # 1) Get all published videos (including Admin uploaded videos)
    # 2) Plus all videos uploaded by this HOD (even if Pending or Rejected)
    videos_qs = Video.objects.filter(
        Q(status="Published") | Q(uploaded_by_hod=hod) | Q(is_admin_video=True)
    ).distinct().order_by("-uploaded_at")

    videos_list = []
    for vid in videos_qs:
        is_mine = (vid.uploaded_by_hod_id == hod.id)
        uploader_name = vid.uploaded_by_hod.hod_name if vid.uploaded_by_hod else "System Admin"

        videos_list.append({
            "id": vid.id,
            "title": vid.title,
            "category": vid.category or "Programming",
            "duration": vid.duration or "15:00",
            "description": vid.description or "",
            "status": vid.status,  # "Pending", "Published", or "Rejected"
            "views": vid.views,
            "uploadedBy": uploader_name,
            "uploadDate": vid.uploaded_at.strftime("%d %b %Y") if vid.uploaded_at else "",
            "videoUrl": vid.video_file.url if vid.video_file else "",
            "thumbnail": vid.thumbnail.url if vid.thumbnail else "",
            "isMine": is_mine,
        })

    return JsonResponse({
        "status": "success",
        "videos": videos_list,
    })


@csrf_exempt
def api_hod_video_upload(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    hod = get_authenticated_hod(request)
    if not hod:
        return JsonResponse({"status": "error", "message": "Unauthorized"}, status=401)

    try:
        import json
        data = {}
        if request.content_type == "application/json" and request.body:
            data = json.loads(request.body.decode("utf-8"))
        else:
            data = request.POST

        title = data.get("title") or "New Course Video"
        category = data.get("category") or "Programming"
        duration = data.get("duration") or "15:00"
        description = data.get("description") or ""

        # ALWAYS set status='Pending' when uploaded by HOD!
        new_vid = Video.objects.create(
            title=title,
            category=category,
            duration=duration,
            description=description,
            status="Pending",
            uploaded_by_hod=hod,
        )

        return JsonResponse({
            "status": "success",
            "message": "Video uploaded successfully and submitted for Admin approval.",
            "video": {
                "id": new_vid.id,
                "title": new_vid.title,
                "category": new_vid.category,
                "duration": new_vid.duration,
                "description": new_vid.description,
                "status": "Pending",
                "uploadedBy": hod.hod_name,
                "uploadDate": new_vid.uploaded_at.strftime("%d %b %Y"),
                "isMine": True,
                "views": 0,
            }
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def api_hod_video_delete(request, video_id):
    if request.method not in ["DELETE", "POST"]:
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    hod = get_authenticated_hod(request)
    if not hod:
        return JsonResponse({"status": "error", "message": "Unauthorized"}, status=401)

    try:
        Video.objects.filter(id=video_id, uploaded_by_hod=hod).delete()
        return JsonResponse({"status": "success", "message": "Video deleted successfully"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def api_principal_video_approvals(request):
    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    # Filter ONLY HOD uploaded videos for approval queue
    hod_videos = Video.objects.filter(uploaded_by_hod__isnull=False)
    pending_qs = hod_videos.filter(status="Pending").order_by("-uploaded_at")
    published_qs = hod_videos.filter(status="Published").order_by("-uploaded_at")
    rejected_qs = hod_videos.filter(status="Rejected").order_by("-uploaded_at")

    def serialize_vids(qs):
        res = []
        for v in qs:
            hod_name = v.uploaded_by_hod.hod_name if v.uploaded_by_hod else "HOD Admin"
            dept_name = v.uploaded_by_hod.dept_name if v.uploaded_by_hod else "General"
            res.append({
                "id": v.id,
                "title": v.title,
                "category": v.category,
                "duration": v.duration,
                "description": v.description,
                "status": v.status,
                "uploadedBy": hod_name,
                "department": dept_name,
                "uploadDate": v.uploaded_at.strftime("%d %b %Y") if v.uploaded_at else "",
                "views": v.views,
                "videoUrl": v.video_file.url if v.video_file else "",
                "thumbnail": v.thumbnail.url if v.thumbnail else "",
            })
        return res

    return JsonResponse({
        "status": "success",
        "pendingVideos": serialize_vids(pending_qs),
        "publishedVideos": serialize_vids(published_qs),
        "rejectedVideos": serialize_vids(rejected_qs),
        "counts": {
            "pending": pending_qs.count(),
            "published": published_qs.count(),
            "rejected": rejected_qs.count(),
            "total": hod_videos.count(),
        }
    })


@csrf_exempt
def api_principal_approve_video(request, video_id):
    if request.method not in ["POST", "PUT"]:
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    try:
        video = Video.objects.get(id=video_id)
        video.status = "Published"
        video.save()
        return JsonResponse({
            "status": "success",
            "message": f"Video '{video.title}' approved successfully and published for students.",
            "video_id": video.id,
            "new_status": "Published"
        })
    except Video.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Video not found"}, status=404)


@csrf_exempt
def api_principal_reject_video(request, video_id):
    if request.method not in ["POST", "PUT"]:
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    try:
        video = Video.objects.get(id=video_id)
        video.status = "Rejected"
        video.save()
        return JsonResponse({
            "status": "success",
            "message": f"Video '{video.title}' rejected.",
            "video_id": video.id,
            "new_status": "Rejected"
        })
    except Video.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Video not found"}, status=404)


@csrf_exempt
def api_student_videos(request):
    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    search_q = (request.GET.get("search") or request.GET.get("q") or "").strip()
    category_q = (request.GET.get("category") or "").strip()

    # Filter strictly for status="Published" -> Only approved HOD and Admin videos are shown to students
    videos_qs = Video.objects.filter(status="Published")

    if search_q:
        videos_qs = videos_qs.filter(
            Q(title__icontains=search_q) | Q(description__icontains=search_q) | Q(category__icontains=search_q)
        )
    if category_q and category_q != "All":
        videos_qs = videos_qs.filter(category=category_q)

    videos_qs = videos_qs.order_by("-uploaded_at")

    all_categories = list(
        Video.objects.filter(status="Published")
        .values_list("category", flat=True)
        .distinct()
    )
    all_categories = [c for c in all_categories if c]

    data = []
    for vid in videos_qs:
        hod_name = vid.uploaded_by_hod.hod_name if vid.uploaded_by_hod else "Faculty"
        dept_name = vid.uploaded_by_hod.dept_name if vid.uploaded_by_hod else "General"

        data.append({
            "id": vid.id,
            "title": vid.title,
            "category": vid.category or "Programming",
            "duration": vid.duration or "15:00",
            "description": vid.description or "",
            "views": vid.views,
            "uploadedBy": hod_name,
            "department": dept_name,
            "uploadDate": vid.uploaded_at.strftime("%d %b %Y") if vid.uploaded_at else "",
            "videoUrl": vid.video_file.url if vid.video_file else "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
            "thumbnail": vid.thumbnail.url if vid.thumbnail else f"https://picsum.photos/seed/{vid.id}/160/90",
            "thumbnail_url": vid.thumbnail.url if vid.thumbnail else f"https://picsum.photos/seed/{vid.id}/160/90",
        })

    return JsonResponse({
        "status": "success",
        "videos": data,
        "categories": all_categories,
    })


# ==========================================================
# DJANGO TEMPLATE VIEWS FOR VIDEO MANAGEMENT (http://127.0.0.1:8000/videos/)
# ==========================================================

from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404


@csrf_exempt
def video_management(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()

    qs = Video.objects.all().order_by("-uploaded_at")

    if q:
        qs = qs.filter(title__icontains=q)
    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)

    total_videos = Video.objects.count()
    published_videos = Video.objects.filter(status="Published").count()
    pending_videos = Video.objects.filter(status="Pending").count()
    draft_videos = Video.objects.filter(status__in=["Draft", "Pending"]).count()
    total_views = Video.objects.aggregate(total=Sum("views"))["total"] or 0

    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "videos": page_obj.object_list,
        "page_obj": page_obj,
        "total_videos": total_videos,
        "published_videos": published_videos,
        "pending_videos": pending_videos,
        "draft_videos": draft_videos,
        "total_views": total_views,
        "q": q,
        "selected_category": category,
        "selected_status": status,
    }
    return render(request, "videomanagement/video_management.html", context)


@csrf_exempt
def video_add(request):
    if request.method == "POST":
        title = request.POST.get("title") or "Untitled Video"
        category = request.POST.get("category") or "Programming"
        duration = request.POST.get("duration") or "10:00"
        description = request.POST.get("description") or ""
        status = request.POST.get("status") or "Pending"
        video_file = request.FILES.get("video_file")
        thumbnail = request.FILES.get("thumbnail")

        Video.objects.create(
            title=title,
            category=category,
            duration=duration,
            description=description,
            status=status,
            video_file=video_file,
            thumbnail=thumbnail,
        )
        return redirect("video_management")

    return render(request, "videomanagement/video_add.html")


@csrf_exempt
def video_edit(request, id):
    video = get_object_or_404(Video, id=id)
    if request.method == "POST":
        video.title = request.POST.get("title", video.title)
        video.category = request.POST.get("category", video.category)
        video.duration = request.POST.get("duration", video.duration)
        video.description = request.POST.get("description", video.description)
        if "status" in request.POST:
            video.status = request.POST.get("status")
        if "video_file" in request.FILES:
            video.video_file = request.FILES["video_file"]
        if "thumbnail" in request.FILES:
            video.thumbnail = request.FILES["thumbnail"]
        video.save()
        return redirect("video_management")

    return render(request, "videomanagement/video_add.html", {"video": video})





# ==========================================================
# DJANGO ADMIN VIDEO APPROVAL HTML PAGE (http://localhost:8000/admin/video-approval/)
# ==========================================================

@csrf_exempt
def admin_video_approval(request):
    q = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "Pending").strip()

    # Filter ONLY HOD uploaded videos for approval queue
    hod_videos = Video.objects.filter(uploaded_by_hod__isnull=False)
    qs = hod_videos.order_by("-uploaded_at")

    if status_filter and status_filter != "All":
        qs = qs.filter(status=status_filter)
    if q:
        qs = qs.filter(title__icontains=q)

    pending_count = hod_videos.filter(status="Pending").count()
    published_count = hod_videos.filter(status="Published").count()
    rejected_count = hod_videos.filter(status="Rejected").count()
    total_count = hod_videos.count()

    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "videos": page_obj.object_list,
        "page_obj": page_obj,
        "pending_count": pending_count,
        "published_count": published_count,
        "rejected_count": rejected_count,
        "total_count": total_count,
        "q": q,
        "selected_status": status_filter,
    }
    return render(request, "videomanagement/admin_video_approval.html", context)


@csrf_exempt
def admin_approve_video_action(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    video.status = "Published"
    video.save()
    next_url = request.META.get("HTTP_REFERER") or "admin_video_approval"
    return redirect(next_url)


@csrf_exempt
def admin_reject_video_action(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    video.status = "Rejected"
    video.save()
    next_url = request.META.get("HTTP_REFERER") or "admin_video_approval"
    return redirect(next_url)