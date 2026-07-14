from django.db import models
from django.utils import timezone

# ==========================================
# College Model
# ==========================================
class College(models.Model):
    college_name = models.CharField(max_length=200)

    def __str__(self):
        return self.college_name

    class Meta:
        verbose_name = "College"
        verbose_name_plural = "Colleges"
        ordering = ["college_name"]

# ==========================================
# Principal Model
# ==========================================
class Principal(models.Model):
    STATUS = (
        ("active", "Active"),
        ("inactive", "Inactive"),
    )

    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="principals"
    )

    principal_name = models.CharField(max_length=150)
    principal_email = models.EmailField(unique=True)
    principal_mobile = models.CharField(max_length=15)

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="active"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.principal_name

    class Meta:
        ordering = ["principal_name"]


# ==========================================
# Department (HOD) Model
# ==========================================
class Department(models.Model):
    STATUS = (
        ("active", "Active"),
        ("inactive", "Inactive"),
    )

    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="departments"
    )

    principal = models.ForeignKey(
        Principal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments"
    )

    dept_code = models.CharField(max_length=20, unique=True)
    dept_name = models.CharField(max_length=150)
    dept_short_name = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    # HOD Details
    hod_name = models.CharField(max_length=150)
    hod_email = models.EmailField(unique=True)
    hod_phone = models.CharField(max_length=15, blank=True)

    # Login Credentials
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="active"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.dept_name} - {self.college.college_name}"

    class Meta:
        ordering = ["dept_name"]


# ==========================================
# Student Model
# ==========================================
class Student(models.Model):
    STATUS = (
        ("active", "Active"),
        ("inactive", "Inactive"),
    )

    YEAR = (
        ("I", "First Year"),
        ("II", "Second Year"),
        ("III", "Third Year"),
        ("IV", "Fourth Year"),
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)

    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="students"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="students"
    )

    student_id = models.CharField(
        max_length=30,
        unique=True
    )

    year = models.CharField(
        max_length=10,
        choices=YEAR
    )

    username = models.CharField(
        max_length=100,
        unique=True
    )

    password = models.CharField(
        max_length=100
    )

    profile_pic = models.ImageField(
        upload_to="students/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="active"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ["full_name"]


# ==========================================
# Video Model
# ==========================================
class Video(models.Model):
    STATUS = (
        ("Published", "Published"),
        ("Draft", "Draft"),
    )

    CATEGORY = (
        ("Programming", "Programming"),
        ("Mathematics", "Mathematics"),
        ("Physics", "Physics"),
        ("Soft Skills", "Soft Skills"),
    )

    title = models.CharField(max_length=250)

    category = models.CharField(
        max_length=100,
        choices=CATEGORY
    )

    duration = models.CharField(max_length=20)

    description = models.TextField(blank=True)

    video_file = models.FileField(
        upload_to="videos/"
    )

    thumbnail = models.ImageField(
        upload_to="thumbnails/"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="Published"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-uploaded_at"]


# ==========================================
# Video Watch History
# ==========================================
# ==========================================
# Video Watch History
# ==========================================
class VideoWatch(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="watch_history"
    )

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="watch_history"
    )

    watched_at = models.DateTimeField(
        default=timezone.now
    )

    def __str__(self):
        return f"{self.student.full_name} - {self.video.title}"

    class Meta:
        ordering = ["-watched_at"]