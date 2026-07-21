import json
from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth

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
    now = timezone.now()
    search = request.GET.get("q", "").strip()
    # ==========================================
    # Dashboard Statistics
    # ==========================================

    total_colleges = College.objects.count()
    total_principals = Principal.objects.count()
    total_hods = Department.objects.count()
    total_students = Student.objects.count()
    total_videos = Video.objects.count()

    active_students = Student.objects.filter(
        status="active"
    ).count()

    # Today's Views
    today_views = VideoWatch.objects.filter(
        watched_at__date=today
    ).count()

    # Monthly Views
    this_month_views = VideoWatch.objects.filter(
        watched_at__year=now.year,
        watched_at__month=now.month
    ).count()

    # Recent Videos
    recent_videos = Video.objects.order_by(
        "-uploaded_at"
    )[:5]

    # ==========================================
    # Most Watched Videos (Current Month)
    # ==========================================

    top_videos = (
        Video.objects.annotate(
            month_views=Count(
                "watch_history",
                filter=Q(
                    watch_history__watched_at__year=now.year,
                    watch_history__watched_at__month=now.month,
                )
            )
        )
        .order_by("-month_views")[:5]
    )

    # ==========================================
    # Top Performing Colleges
    # Monthly Target = 10000 Views
    # ==========================================

    MONTHLY_TARGET = 10000

    top_colleges = (
        College.objects.annotate(
            monthly_views=Count(
                "students__watch_history",
                filter=Q(
                    students__watch_history__watched_at__year=now.year,
                    students__watch_history__watched_at__month=now.month,
                )
            )
        )
        .order_by("-monthly_views")[:5]
    )

    # Progress based on Target
    for college in top_colleges:
        college.progress = min(
            round(
                (college.monthly_views / MONTHLY_TARGET) * 100
            ),
            100
        )

    # ==========================================
    # Weekly Chart (Last 7 Days)
    # ==========================================

    week_labels = []
    week_data = []

    for i in range(6, -1, -1):

        day = today - timedelta(days=i)

        week_labels.append(
            day.strftime("%a")
        )

        week_data.append(
            VideoWatch.objects.filter(
                watched_at__date=day
            ).count()
        )

    # ==========================================
    # Monthly Chart
    # ==========================================

    monthly = (
        VideoWatch.objects
        .annotate(
            month=TruncMonth("watched_at")
        )
        .values("month")
        .annotate(
            total=Count("id")
        )
        .order_by("month")
    )

    month_labels = []
    month_data = []

    for item in monthly:

        month_labels.append(
            item["month"].strftime("%b")
        )

        month_data.append(
            item["total"]
        )
        # ==========================================
    # College-wise Chart
    # ==========================================

    colleges = (
        College.objects.annotate(
            total_views=Count("students__watch_history")
        )
    )

    college_labels = []
    college_data = []

    for college in colleges:

        college_labels.append(
            college.college_name
        )

        college_data.append(
            college.total_views
        )

    # ==========================================
    # Monthly Activities (Last 6 Months)
    # ==========================================

    monthly_activities = (
        VideoWatch.objects
        .annotate(
            month=TruncMonth("watched_at")
        )
        .values("month")
        .annotate(
            total_views=Count("id"),
            active_students=Count(
                "student",
                distinct=True
            ),
            videos_watched=Count(
                "video",
                distinct=True
            ),
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
        "total_hods": total_hods,
        "total_students": total_students,
        "total_videos": total_videos,

        "today_views": today_views,
        "this_month_views": this_month_views,
        "active_students": active_students,

        # Lists
        "recent_videos": recent_videos,
        "top_videos": top_videos,
        "top_colleges": top_colleges,
        "monthly_activities": monthly_activities,

        # Monthly Target
        "monthly_target": MONTHLY_TARGET,

        # Weekly Chart
        "week_labels": json.dumps(
            week_labels
        ),
        "week_data": json.dumps(
            week_data
        ),

        # Monthly Chart
        "month_labels": json.dumps(
            month_labels
        ),
        "month_data": json.dumps(
            month_data
        ),

        # College Chart
        "college_labels": json.dumps(
            college_labels
        ),
        "college_data": json.dumps(
            college_data
        ),

        "now": now,
    }

    # ==========================================
    # Render Dashboard
    # ==========================================

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )

def admin_login(request):
    return render(request, "login/login.html")



from django.shortcuts import render, redirect, get_object_or_404
from .models import College

def college_management(request):
    colleges = College.objects.all()
    return render(request, 'collegemanagement/collegelist.html', {'colleges': colleges})

def college_add(request):
    if request.method == "POST":
        college_code = request.POST.get('college_code')
        college_name = request.POST.get('college_name')
        university = request.POST.get('university')
        college_type = request.POST.get('college_type')
        status = request.POST.get('status', 'active')
        state = request.POST.get('state')
        district = request.POST.get('district')
        address = request.POST.get('address')
        contact_email = request.POST.get('college_email')
        contact_phone = request.POST.get('college_phone')
        website = request.POST.get('website')
        college_logo = request.FILES.get('college_logo')
        
        if college_name:
            College.objects.create(
                college_code=college_code,
                college_name=college_name,
                university=university,
                college_type=college_type,
                status=status,
                state=state,
                district=district,
                address=address,
                contact_email=contact_email,
                contact_phone=contact_phone,
                website=website,
                college_logo=college_logo
            )
            return redirect('collegemanagement')
    return render(request, 'collegemanagement/add_college.html')

def college_delete(request, id):
    if request.method == "POST":
        college = get_object_or_404(College, id=id)
        college.delete()
        return redirect('collegemanagement')
    return redirect('collegemanagement')


def department_management(request):
    departments = Department.objects.all()
    return render(request, 'department/department_list.html', {'departments': departments})

def department_add(request):
    if request.method == "POST":
        college_id = request.POST.get('college')
        dept_code = request.POST.get('dept_code')
        dept_name = request.POST.get('dept_name')
        dept_short_name = request.POST.get('dept_short_name')
        description = request.POST.get('description')
        hod_name = request.POST.get('hod_name')
        hod_email = request.POST.get('hod_email')
        hod_phone = request.POST.get('hod_phone')
        status = request.POST.get('status')

        college = College.objects.filter(id=college_id).first() if college_id else None

        if college and dept_code and dept_name and hod_email:
            import string
            import random
            
            # Generate username
            base_college = college.college_name[:3].upper().replace(" ", "")
            username = f"{base_college}_{dept_code.upper()}_HOD"
            
            # Generate random password
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(random.choices(chars, k=10))

            Department.objects.create(
                college=college,
                dept_code=dept_code,
                dept_name=dept_name,
                dept_short_name=dept_short_name,
                description=description,
                hod_name=hod_name,
                hod_email=hod_email,
                hod_phone=hod_phone,
                status=status,
                username=username,
                password=password
            )
            return redirect('department_management')

    colleges = College.objects.all()
    return render(request, 'department/add_department.html', {'colleges': colleges})

def department_edit(request, id):
    department = Department.objects.filter(id=id).first()
    if request.method == "POST" and department:
        department.college_id = request.POST.get('college')
        department.dept_code = request.POST.get('dept_code')
        department.dept_name = request.POST.get('dept_name')
        department.dept_short_name = request.POST.get('dept_short_name')
        department.description = request.POST.get('description')
        department.hod_name = request.POST.get('hod_name')
        department.hod_email = request.POST.get('hod_email')
        department.hod_phone = request.POST.get('hod_phone')
        department.status = request.POST.get('status')
        department.username = request.POST.get('username')
        
        password = request.POST.get('password')
        if password:
            department.password = password
            
        department.save()
        return redirect('department_management')
        
    colleges = College.objects.all()
    return render(request, 'department/edit_department.html', {'department': department, 'colleges': colleges})

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

def student_management(request):
    import string, random
    from django.db.models import Q
    from django.http import JsonResponse
    from django.template.loader import render_to_string

    students_list = Student.objects.all().order_by('-created_at')

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

    context = {
        'page_obj': page_obj,
        'students': page_obj.object_list,
        'all_colleges': all_colleges,
        'all_departments': all_departments,
        'q': q,
        'selected_college': college_id,
        'selected_dept': dept_id,
        'selected_year': year,
        'selected_status': status,
        'total_students': Student.objects.count(),
        'active_students': Student.objects.filter(status='active').count(),
        'inactive_students': Student.objects.filter(status='inactive').count(),
        'college_count': Student.objects.values('college').distinct().count(),
    }

    # AJAX partial request – return JSON for smooth pagination
    if request.GET.get('partial') == '1':
        rows_html = render_to_string('studentmanagement/partials/student_rows.html', context, request=request)
        
        # Handle empty pages safely
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

    return render(request, 'studentmanagement/studentmanagement.html', context)

def student_add(request):
    if request.method == 'POST':
        import string, random
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        college_id = request.POST.get('college')
        dept_id = request.POST.get('department')
        student_id_val = request.POST.get('student_id')
        year = request.POST.get('year')
        status = request.POST.get('status', 'active')
        end_date = request.POST.get('end_date')

        college = College.objects.filter(id=college_id).first()
        dept = Department.objects.filter(id=dept_id).first()

        if full_name and email and college and dept and student_id_val and year:
            # Auto-generate username from student_id
            username = student_id_val.upper()
            # Auto-generate secure random password
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(random.choices(chars, k=10))

            Student.objects.create(
                full_name=full_name,
                email=email,
                phone=phone,
                college=college,
                department=dept,
                student_id=student_id_val,
                year=year,
                username=username,
                password=password,
                status=status,
                end_date=end_date if end_date else None,
            )
            return redirect('student_management')

    all_colleges = College.objects.all()
    all_departments = Department.objects.all()
    return render(request, 'studentmanagement/add_student.html', {
        'all_colleges': all_colleges,
        'all_departments': all_departments,
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
        title = request.POST.get('title')
        category = request.POST.get('category')
        duration = request.POST.get('duration')
        description = request.POST.get('description', '')
        status = request.POST.get('status', 'Published')
        video_file = request.FILES.get('video_file')
        thumbnail = request.FILES.get('thumbnail')
        
        if title and category and duration and video_file and thumbnail:
            Video.objects.create(
                title=title,
                category=category,
                duration=duration,
                description=description,
                status=status,
                video_file=video_file,
                thumbnail=thumbnail
            )
            return redirect('video_management')
            
    return render(request, "videomanagement/video_add.html")




def video_analytics(request):
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    today = now.date()

    # ── Summary Stats ──────────────────────────────
    total_videos = Video.objects.count()
    total_views = Video.objects.aggregate(total=Sum('views'))['total'] or 0

    # Watch hours: sum of all VideoWatch records (approx 15 min per watch event)
    total_watch_events = VideoWatch.objects.count()
    watch_hours = (total_watch_events * 15) // 60

    active_students = VideoWatch.objects.values('student').distinct().count()

    # Completion rate — 0 if no watch data, else 100% (simple binary watch model)
    completion_rate = 0 if total_watch_events == 0 else 100

    most_watched = Video.objects.order_by('-views')[:5]
    recent_activity = VideoWatch.objects.select_related('student', 'video').order_by('-watched_at')[:5]

    # ── Weekly Trend (Last 7 Days) ─────────────────
    week_labels = []
    week_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        week_labels.append(day.strftime('%a'))
        week_data.append(VideoWatch.objects.filter(watched_at__date=day).count())

    # ── Daily Trend (Last 7 Days, same as weekly by day) ──
    daily_labels = week_labels
    daily_data = week_data

    # ── Monthly Trend (Last 6 Months) ─────────────
    monthly_labels = []
    monthly_data = []
    for i in range(5, -1, -1):
        # Go back i months
        month_date = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        count = VideoWatch.objects.filter(
            watched_at__year=month_date.year,
            watched_at__month=month_date.month
        ).count()
        monthly_labels.append(month_date.strftime('%b'))
        monthly_data.append(count)

    # ── Category Distribution ──────────────────────
    categories = ['Programming', 'Mathematics', 'Physics', 'Soft Skills']
    category_data = []
    for cat in categories:
        # Count VideoWatch events for videos in this category
        count = VideoWatch.objects.filter(video__category=cat).count()
        category_data.append(count)

    # If no watch history at all, fall back to video count per category
    if sum(category_data) == 0:
        category_data = []
        for cat in categories:
            count = Video.objects.filter(category=cat).count()
            category_data.append(count)

    context = {
        'total_videos': total_videos,
        'total_views': total_views,
        'watch_hours': watch_hours,
        'active_students': active_students,
        'completion_rate': completion_rate,
        'most_watched': most_watched,
        'recent_activity': recent_activity,
        # Chart data (passed as JSON-safe Python lists)
        'week_labels': week_labels,
        'week_data': week_data,
        'daily_labels': daily_labels,
        'daily_data': daily_data,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'category_labels': categories,
        'category_data': category_data,
    }
    return render(request, 'videoanalytics/video_analytics.html', context)


def reports(request):
    return render(request, 'reportmanagement/report_management.html')

def user_management(request):
    return render(request, 'usermanagement/user_management.html')

def system_settings(request):
    return render(request, 'dashboard/system_settings.html')

def profile(request):
    return render(request, 'dashboard/profile.html')


def video_edit(request, id):
    return render(request, "video_edit.html")


def video_delete(request, id):
    return render(request, "video_delete.html")

def user_logout(request):
    # Add actual logout logic later
    return redirect('dashboard')

def global_search(request):
    from django.db.models import Q
    query = request.GET.get('q', '').strip()
    results = {
        'query': query,
        'colleges': [],
        'principals': [],
        'students': [],
        'videos': [],
    }
    if query:
        results['colleges']   = College.objects.filter(college_name__icontains=query)[:10]
        results['principals'] = Principal.objects.filter(
            Q(principal_name__icontains=query) | Q(principal_email__icontains=query)
        ).select_related('college')[:10]
        results['students']   = Student.objects.filter(
            Q(full_name__icontains=query) | Q(email__icontains=query) | Q(student_id__icontains=query)
        ).select_related('college', 'department')[:10]
        results['videos']     = Video.objects.filter(
            Q(title__icontains=query) | Q(category__icontains=query) | Q(description__icontains=query)
        )[:10]

    total = (
        results['colleges'].count() +
        results['principals'].count() +
        results['students'].count() +
        results['videos'].count()
    )
    results['total'] = total
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
