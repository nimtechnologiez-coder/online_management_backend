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
                    'error': f'A Principal with email "{principal_email}" already exists. Please use a different email.'
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

def principal_delete(request, id):
    if request.method == "POST":
        principal = Principal.objects.filter(id=id).first()
        if principal:
            principal.delete()
    return redirect('principal_management')

def student_management(request):
    import string, random
    from django.db.models import Q
    from django.http import JsonResponse
    from django.template.loader import render_to_string
    from datetime import date

    # Auto-expire students whose end_date has passed
    today = date.today()
    Student.objects.filter(end_date__lt=today, status='active').update(status='expired')

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
    error = None
    if request.method == 'POST':
        import string, random
        from datetime import date

        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        college_id = request.POST.get('college')
        dept_id = request.POST.get('department')
        student_id_val = request.POST.get('student_id')
        year = request.POST.get('year')
        status = request.POST.get('status', 'active')
        join_date_str = request.POST.get('join_date')

        college = College.objects.filter(id=college_id).first()
        dept = Department.objects.filter(id=dept_id).first()

        # Auto-calculate end_date based on college stream (no external package)
        end_date = None
        if join_date_str:
            try:
                join_date = date.fromisoformat(join_date_str)
                stream = college.college_stream if college else 'other'
                years = 3 if stream == 'arts_science' else 4
                # Add years manually using date.replace
                try:
                    end_date = join_date.replace(year=join_date.year + years)
                except ValueError:
                    # Handle Feb 29 leap year edge case
                    end_date = join_date.replace(year=join_date.year + years, day=28)
            except ValueError:
                end_date = None

        error = None

        if full_name and email and college and dept and student_id_val and year:
            # Check for duplicate student_id
            if Student.objects.filter(student_id=student_id_val).exists():
                error = f"Student ID '{student_id_val}' is already registered. Please use a different ID."
            # Check for duplicate email
            elif Student.objects.filter(email=email).exists():
                error = f"Email '{email}' is already registered for another student."
            else:
                # Auto-generate unique username from student_id
                base_username = student_id_val.upper()
                username = base_username
                # Append random suffix until unique
                while Student.objects.filter(username=username).exists():
                    username = f"{base_username}_{random.randint(1000, 9999)}"
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
                    join_date=date.fromisoformat(join_date_str) if join_date_str else None,
                    end_date=end_date,
                )
                return redirect('student_management')

    all_colleges = College.objects.all()
    all_departments = Department.objects.all()
    return render(request, 'studentmanagement/add_student.html', {
        'all_colleges': all_colleges,
        'all_departments': all_departments,
        'error': error,
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

# ------------------------------------------------------------------------------------------------------------------------------------------------------
#                                      API
# ------------------------------------------------------------------------------------------------------------------------------------------------------

from django.http import JsonResponse
from django.utils import timezone
from .models import Student, Video, VideoWatch, Department
from django.db.models import Count, Sum
from datetime import timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from .models import Student, Video, VideoWatch, Principal


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Principal
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
import json

from .models import Principal, Student, Video, VideoWatch

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
import json

from .models import Principal, Student, Video, VideoWatch


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

    principal = get_authenticated_principal(request)

    if principal is None:
        return JsonResponse({
            "status": "error",
            "message": "Please login"
        }, status=401)

    college = principal.college

    total_students = Student.objects.filter(college=college).count()
    active_students = Student.objects.filter(college=college, status="active").count()
    total_videos = Video.objects.count()
    total_views = VideoWatch.objects.filter(
        student__college=college
    ).count()

    # Recent views filtered specifically for logged in principal's college
    recent_views_qs = VideoWatch.objects.filter(
        student__college=college
    ).select_related("student", "student__department", "video")[:10]

    recent_views_data = [
        {
            "student": rw.student.full_name,
            "department": rw.student.department.dept_name if rw.student.department else "N/A",
            "video": rw.video.title,
            "watchTime": rw.video.duration,
            "lastViewed": rw.watched_at.strftime("%Y-%m-%d %H:%M"),
        }
        for rw in recent_views_qs
    ]

    # Latest videos
    latest_videos_qs = Video.objects.all()[:5]
    latest_videos_data = [
        {
            "title": v.title,
            "category": v.category,
            "duration": v.duration,
            "views": v.views,
            "uploadDate": v.uploaded_at.strftime("%Y-%m-%d"),
        }
        for v in latest_videos_qs
    ]

    return JsonResponse({
        "status": "success",
        "data": {
            "summaryCards": {
                "students": total_students,
                "activeStudents": active_students,
                "videos": total_videos,
                "totalViews": total_views,
                "watchTime": "0 Hours",
            },
            "dailyViews": [],
            "topCategories": [],
            "latestVideos": latest_videos_data,
            "recentViews": recent_views_data,
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

    data = []

    for student in students:
        data.append({
            "id": student.id,
            "student_id": student.student_id,
            "full_name": student.full_name,
            "email": student.email,
            "phone": student.phone,
            "department": student.department.dept_name if student.department else "N/A",
            "year": student.year,
            "status": student.status,
            "username": getattr(student, "username", student.student_id),
            "password": getattr(student, "password", "********"),
            "college": principal.college.college_name,
            "join_date": student.created_at.strftime("%Y-%m-%d") if hasattr(student, "created_at") and student.created_at else "2026-07-21",
            "end_date": "2030-07-21",
        })

    return JsonResponse({
        "status": "success",
        "college": principal.college.college_name,
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

def api_principal_profile(request):
    try:
        principal = get_authenticated_principal(request)
        if not principal:
            return JsonResponse({"status": "error", "message": "No authenticated principal found"}, status=401)
        
        college = principal.college
        
        return JsonResponse({
            "status": "success",
            "data": {
                "name": principal.principal_name,
                "email": principal.principal_email,
                "phone": principal.principal_mobile,
                "college": college.college_name,
                "joined": principal.created_at.strftime("%b %Y") if principal.created_at else "Aug 2015",
                "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={principal.principal_name}",
                "bio": f"{principal.principal_name} is the Principal at {college.college_name}.",
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
            return JsonResponse({"status": "error", "message": "Unauthorized or no college associated"}, status=401)

        departments = Department.objects.all()

        dept_colors = ["blue", "indigo", "teal", "emerald", "amber", "purple", "rose"]
        data = []

        for idx, dept in enumerate(departments):
            student_count = Student.objects.filter(college=principal.college, department=dept).count()
            video_count = Video.objects.count()

            data.append({
                "id": dept.id,
                "name": dept.dept_name,
                "code": dept.dept_code,
                "hod": dept.hod_name if dept.hod_name else f"HOD {dept.dept_code}",
                "email": dept.hod_email if dept.hod_email else f"hod.{dept.dept_code.lower()}@college.edu",
                "students": student_count,
                "videos": video_count,
                "completionRate": 75 if student_count > 0 else 0,
                "performance": "High" if student_count > 10 else ("Average" if student_count > 0 else "Low"),
                "trend": "+5%",
                "color": dept_colors[idx % len(dept_colors)],
            })

        return JsonResponse({
            "status": "success",
            "college": principal.college.college_name if principal.college else "College",
            "total": len(data),
            "data": data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def api_principal_videos(request):
    try:
        principal = get_authenticated_principal(request)
        if not principal or not principal.college:
            return JsonResponse({"status": "error", "message": "Unauthorized"}, status=401)

        # All students in this principal's college
        college_students = Student.objects.filter(college=principal.college)

        videos = Video.objects.all().order_by("-uploaded_at")
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

            data.append({
                "id": str(video.id),
                "title": video.title,
                "category": video.category,
                "duration": video.duration,
                "views": video.views,
                "uploadedDate": video.uploaded_at.strftime("%d %b %Y") if video.uploaded_at else "",
                "uploadedBy": "Company Admin",
                "status": video.status,
                "studentsViewed": students_viewed,
                "completionRate": completion_rate,
                "description": video.description or "",
                "thumbnail": thumb_label,
                "videoUrl": request.build_absolute_uri(video.video_file.url) if video.video_file else "",
            })

        total_views = sum(v["views"] for v in data)

        return JsonResponse({
            "status": "success",
            "college": principal.college.college_name,
            "total": len(data),
            "totalViews": total_views,
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
            return JsonResponse({"status": "error", "message": "Invalid academic credentials provided. Please check with your department admin."}, status=401)

        if student.status != "active":
            return JsonResponse({"status": "error", "message": f"Account is currently {student.status}. Please contact administrator."}, status=403)

        student_data = {
            "id": student.id,
            "student_id": student.student_id,
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
def api_student_dashboard(request):
    try:
        # Identify student via header or session
        student_id_header = request.headers.get("X-Student-Id") or request.META.get("HTTP_X_STUDENT_ID")
        student = None
        if student_id_header:
            student = Student.objects.filter(id=student_id_header).first()

        if not student:
            student = Student.objects.filter(status="active").first()

        if not student:
            return JsonResponse({"status": "error", "message": "No active student records found"}, status=404)
        total_videos = Video.objects.count()
        watched_videos = VideoWatch.objects.filter(student=student).values("video").distinct()
        completed_count = watched_videos.count()
        pending_count = max(0, total_videos - completed_count)
        total_watch_mins = 0
        for w in VideoWatch.objects.filter(student=student).select_related("video"):
            try:
                dur = w.video.duration or "0"
                import re
                mins = int(re.search(r'\d+', str(dur)).group()) if re.search(r'\d+', str(dur)) else 0
                total_watch_mins += mins
            except Exception:
                pass
        watch_hours = round(total_watch_mins / 60, 1)
        recent_watches = VideoWatch.objects.filter(student=student).select_related("video").order_by("-watched_at")[:6]
        continue_watching = []
        for rw in recent_watches:
            v = rw.video
            continue_watching.append({
                "id": v.id,
                "title": v.title,
                "subtitle": f"{v.category or 'General'} • {v.duration or 'N/A'}",
                "progress": 60,
                "badge": "In Progress",
            })
        recent_videos = Video.objects.order_by("-uploaded_at")[:5]
        recently_added = []
        for v in recent_videos:
            recently_added.append({
                "title": v.title,
                "category": v.category or "General",
                "date": v.uploaded_at.strftime("%d %b %Y") if v.uploaded_at else "",
                "duration": v.duration or "N/A",
            })

        return JsonResponse({
            "status": "success",
            "stats": {
                "totalVideos": total_videos,
                "completed": completed_count,
                "pending": pending_count,
                "watchHours": f"{watch_hours}h",
            },
            "continueWatching": continue_watching,
            "recentlyAdded": recently_added,
        })
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
        if student:
            watched_ids = set(
                VideoWatch.objects.filter(student=student).values_list("video_id", flat=True)
            )

        videos_data = []
        for v in videos_qs:
            mins = 0
            if v.duration:
                m = re.search(r'\d+', str(v.duration))
                if m:
                    mins = int(m.group())

            videos_data.append({
                "id": v.id,
                "title": v.title,
                "category": v.category or "General",
                "duration": v.duration or "N/A",
                "description": v.description or "",
                "video_url": v.video_file.url if v.video_file else "",
                "thumbnail_url": v.thumbnail.url if v.thumbnail else "",
                "views": v.views,
                "uploaded_at": v.uploaded_at.strftime("%d %b %Y") if v.uploaded_at else "",
                "watched": v.id in watched_ids,
            })

        # Category list for filter
        categories = list(Video.objects.filter(status="Published").values_list("category", flat=True).distinct())

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
    """Records that a student has started/rewatched a video and increments views."""
    try:
        student_id_header = request.headers.get("X-Student-Id") or request.META.get("HTTP_X_STUDENT_ID")
        student = None
        if student_id_header:
            student = Student.objects.filter(id=student_id_header).first()

        video = Video.objects.filter(id=video_id).first()
        if not video:
            return JsonResponse({"status": "error", "message": "Video not found"}, status=404)

        # Increment video view count
        video.views += 1
        video.save()

        # Record in VideoWatch history if student is identified
        # update_or_create prevents duplicate rows — rewatching updates the timestamp
        if student:
            VideoWatch.objects.update_or_create(
                student=student,
                video=video,
                defaults={"watched_at": timezone.now()},
            )

        return JsonResponse({
            "status": "success",
            "message": "Watch recorded successfully",
            "views": video.views
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
    """Returns analytics, category completion breakdown, watch time, and achievements for student."""
    try:
        import re
        student_id_header = request.headers.get("X-Student-Id") or request.META.get("HTTP_X_STUDENT_ID")
        student = None
        if student_id_header:
            student = Student.objects.filter(id=student_id_header).first()

        if not student:
            student = Student.objects.filter(status="active").first()

        if not student:
            return JsonResponse({"status": "error", "message": "No student record found"}, status=404)

        # Total published videos available
        total_videos = Video.objects.filter(status="Published").count()

        # Watched videos
        watched_records = VideoWatch.objects.filter(student=student).select_related("video")
        watched_video_ids = set(w.video.id for w in watched_records)
        completed_count = len(watched_video_ids)
        completion_rate = round((completed_count / total_videos) * 100) if total_videos > 0 else 0

        # Calculate total watch time from unique videos only (not rewatches)
        total_mins = 0
        seen_video_ids = set()
        for w in watched_records:
            try:
                if w.video.id not in seen_video_ids:
                    seen_video_ids.add(w.video.id)
                    m = re.search(r'\d+', str(w.video.duration or ""))
                    if m:
                        total_mins += int(m.group())
            except Exception:
                pass
        watch_hours = round(total_mins / 60, 1)

        # Subject/Category Completion Breakdown
        categories = Video.objects.filter(status="Published").values_list("category", flat=True).distinct()
        subject_breakdown = []
        for cat in categories:
            cat_name = cat or "General"
            cat_total = Video.objects.filter(status="Published", category=cat).count()
            cat_completed = VideoWatch.objects.filter(student=student, video__category=cat).values("video").distinct().count()
            cat_pct = round((cat_completed / cat_total) * 100) if cat_total > 0 else 0
            subject_breakdown.append({
                "subject": cat_name,
                "completed": cat_completed,
                "total": cat_total,
                "percentage": cat_pct,
            })

        # Daily Watch Activity (Mon-Sun) grouped by actual VideoWatch timestamps
        days_map = {"Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0}
        days_hours = {"Mon": 0.0, "Tue": 0.0, "Wed": 0.0, "Thu": 0.0, "Fri": 0.0, "Sat": 0.0, "Sun": 0.0}

        for w in watched_records:
            if w.watched_at:
                dname = w.watched_at.strftime("%a")  # e.g., Mon, Tue
                if dname in days_map:
                    days_map[dname] += 1
                    try:
                        m = re.search(r'\d+', str(w.video.duration or ""))
                        if m:
                            days_hours[dname] += round(int(m.group()) / 60, 1)
                    except Exception:
                        pass

        daily_activity = [
            {"day": d, "hours": round(days_hours[d], 1), "videos": days_map[d]}
            for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        ]

        return JsonResponse({
            "status": "success",
            "metrics": {
                "totalAssigned": total_videos,
                "completedCount": completed_count,
                "completionRate": completion_rate,
                "watchHours": watch_hours,
                "modulesMastered": len([s for s in subject_breakdown if s["percentage"] == 100]),
            },
            "subjectBreakdown": subject_breakdown,
            "weeklyActivity": daily_activity,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)