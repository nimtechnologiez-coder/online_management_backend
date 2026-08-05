

from django.db import models
from django.utils import timezone

# ==========================================
# College Model
# ==========================================
class College(models.Model):

    STATE_CHOICES = [
        ("Tamil Nadu", "Tamil Nadu"),
        ("Kerala", "Kerala"),
        ("Karnataka", "Karnataka"),
        ("Andhra Pradesh", "Andhra Pradesh"),
        ("Telangana", "Telangana"),
        ("Maharashtra", "Maharashtra"),
        # Add more states here...
    ]

    DISTRICT_CHOICES = [

        # ---------------- Tamil Nadu ----------------
        ("Ariyalur", "Ariyalur"),
        ("Chengalpattu", "Chengalpattu"),
        ("Chennai", "Chennai"),
        ("Coimbatore", "Coimbatore"),
        ("Cuddalore", "Cuddalore"),
        ("Dharmapuri", "Dharmapuri"),
        ("Dindigul", "Dindigul"),
        ("Erode", "Erode"),
        ("Kallakurichi", "Kallakurichi"),
        ("Kanchipuram", "Kanchipuram"),
        ("Kanyakumari", "Kanyakumari"),
        ("Karur", "Karur"),
        ("Krishnagiri", "Krishnagiri"),
        ("Madurai", "Madurai"),
        ("Mayiladuthurai", "Mayiladuthurai"),
        ("Nagapattinam", "Nagapattinam"),
        ("Namakkal", "Namakkal"),
        ("Nilgiris", "Nilgiris"),
        ("Perambalur", "Perambalur"),
        ("Pudukkottai", "Pudukkottai"),
        ("Ramanathapuram", "Ramanathapuram"),
        ("Ranipet", "Ranipet"),
        ("Salem", "Salem"),
        ("Sivaganga", "Sivaganga"),
        ("Tenkasi", "Tenkasi"),
        ("Thanjavur", "Thanjavur"),
        ("Theni", "Theni"),
        ("Thoothukudi", "Thoothukudi"),
        ("Tiruchirappalli", "Tiruchirappalli"),
        ("Tirunelveli", "Tirunelveli"),
        ("Tirupathur", "Tirupathur"),
        ("Tiruppur", "Tiruppur"),
        ("Tiruvallur", "Tiruvallur"),
        ("Tiruvannamalai", "Tiruvannamalai"),
        ("Tiruvarur", "Tiruvarur"),
        ("Vellore", "Vellore"),
        ("Viluppuram", "Viluppuram"),
        ("Virudhunagar", "Virudhunagar"),

        # ---------------- Kerala ----------------
        ("Alappuzha", "Alappuzha"),
        ("Ernakulam", "Ernakulam"),
        ("Idukki", "Idukki"),
        ("Kannur", "Kannur"),
        ("Kasaragod", "Kasaragod"),
        ("Kollam", "Kollam"),
        ("Kottayam", "Kottayam"),
        ("Kozhikode", "Kozhikode"),
        ("Malappuram", "Malappuram"),
        ("Palakkad", "Palakkad"),
        ("Pathanamthitta", "Pathanamthitta"),
        ("Thiruvananthapuram", "Thiruvananthapuram"),
        ("Thrissur", "Thrissur"),
        ("Wayanad", "Wayanad"),

        # ---------------- Karnataka ----------------
        ("Bagalkote", "Bagalkote"),
        ("Belagavi", "Belagavi"),
        ("Ballari", "Ballari"),
        ("Bengaluru Rural", "Bengaluru Rural"),
        ("Bengaluru Urban", "Bengaluru Urban"),
        ("Bidar", "Bidar"),
        ("Chamarajanagar", "Chamarajanagar"),
        ("Chikkaballapur", "Chikkaballapur"),
        ("Chikkamagaluru", "Chikkamagaluru"),
        ("Dakshina Kannada", "Dakshina Kannada"),
        ("Davanagere", "Davanagere"),
        ("Dharwad", "Dharwad"),
        ("Hassan", "Hassan"),
        ("Kodagu", "Kodagu"),
        ("Kolar", "Kolar"),
        ("Mandya", "Mandya"),
        ("Mysuru", "Mysuru"),
        ("Shivamogga", "Shivamogga"),
        ("Tumakuru", "Tumakuru"),
        ("Udupi", "Udupi"),

        # ---------------- Andhra Pradesh ----------------
        ("Anakapalli", "Anakapalli"),
        ("Anantapur", "Anantapur"),
        ("Chittoor", "Chittoor"),
        ("East Godavari", "East Godavari"),
        ("Eluru", "Eluru"),
        ("Guntur", "Guntur"),
        ("Kadapa", "Kadapa"),
        ("Kakinada", "Kakinada"),
        ("Krishna", "Krishna"),
        ("Kurnool", "Kurnool"),
        ("Nandyal", "Nandyal"),
        ("Nellore", "Nellore"),
        ("Prakasam", "Prakasam"),
        ("Srikakulam", "Srikakulam"),
        ("Visakhapatnam", "Visakhapatnam"),
        ("Vizianagaram", "Vizianagaram"),
        ("West Godavari", "West Godavari"),

        # ---------------- Telangana ----------------
        ("Adilabad", "Adilabad"),
        ("Hyderabad", "Hyderabad"),
        ("Karimnagar", "Karimnagar"),
        ("Khammam", "Khammam"),
        ("Mahabubnagar", "Mahabubnagar"),
        ("Medak", "Medak"),
        ("Nalgonda", "Nalgonda"),
        ("Nizamabad", "Nizamabad"),
        ("Rangareddy", "Rangareddy"),
        ("Warangal", "Warangal"),

        # ---------------- Maharashtra ----------------
        ("Ahmednagar", "Ahmednagar"),
        ("Aurangabad", "Aurangabad"),
        ("Kolhapur", "Kolhapur"),
        ("Mumbai", "Mumbai"),
        ("Nagpur", "Nagpur"),
        ("Nashik", "Nashik"),
        ("Pune", "Pune"),
        ("Sangli", "Sangli"),
        ("Satara", "Satara"),
        ("Solapur", "Solapur"),
        ("Thane", "Thane"),
    ]

    # ------------------------------------------------------------------
    # State -> District mapping, used to feed the Add College form's
    # dropdowns dynamically (state select changes -> district list updates).
    # Keep this in sync whenever STATE_CHOICES / DISTRICT_CHOICES change.
    # ------------------------------------------------------------------
    STATE_DISTRICTS = {
        "Tamil Nadu": [
            "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
            "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kanchipuram",
            "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
            "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
            "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi",
            "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
            "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur",
            "Vellore", "Viluppuram", "Virudhunagar",
        ],
        "Kerala": [
            "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam",
            "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta",
            "Thiruvananthapuram", "Thrissur", "Wayanad",
        ],
        "Karnataka": [
            "Bagalkote", "Belagavi", "Ballari", "Bengaluru Rural", "Bengaluru Urban",
            "Bidar", "Chamarajanagar", "Chikkaballapur", "Chikkamagaluru",
            "Dakshina Kannada", "Davanagere", "Dharwad", "Hassan", "Kodagu",
            "Kolar", "Mandya", "Mysuru", "Shivamogga", "Tumakuru", "Udupi",
        ],
        "Andhra Pradesh": [
            "Anakapalli", "Anantapur", "Chittoor", "East Godavari", "Eluru",
            "Guntur", "Kadapa", "Kakinada", "Krishna", "Kurnool", "Nandyal",
            "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram",
            "West Godavari",
        ],
        "Telangana": [
            "Adilabad", "Hyderabad", "Karimnagar", "Khammam", "Mahabubnagar",
            "Medak", "Nalgonda", "Nizamabad", "Rangareddy", "Warangal",
        ],
        "Maharashtra": [
            "Ahmednagar", "Aurangabad", "Kolhapur", "Mumbai", "Nagpur", "Nashik",
            "Pune", "Sangli", "Satara", "Solapur", "Thane",
        ],
    }

    college_code = models.CharField(max_length=50, blank=True, null=True)
    college_name = models.CharField(max_length=200)
    university = models.CharField(max_length=200, blank=True, null=True)
    college_type = models.CharField(max_length=50, blank=True, null=True)
    college_stream = models.CharField(
        max_length=50,
        choices=[
            ('engineering', 'Engineering'),
            ('arts_science', 'Arts & Science'),
            ('other', 'Other'),
        ],
        default='other',
        blank=True,
        null=True
    )
    status = models.CharField(max_length=20, default='active')

    # NOTE: state/district now use choices sourced from STATE_CHOICES /
    # DISTRICT_CHOICES above (previously free-text CharFields).
    state = models.CharField(
        max_length=100,
        choices=STATE_CHOICES,
        default="Tamil Nadu",
        blank=True,
        null=True
    )
    district = models.CharField(
        max_length=100,
        choices=DISTRICT_CHOICES,
        blank=True,
        null=True
    )

    address = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    college_logo = models.ImageField(upload_to='college_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

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

    username = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    password = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    bio = models.TextField(null=True, blank=True)
    avatar = models.TextField(null=True, blank=True)
    cover_photo = models.TextField(null=True, blank=True)

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

    bio = models.TextField(null=True, blank=True)
    avatar = models.TextField(null=True, blank=True)
    cover_photo = models.TextField(null=True, blank=True)

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
        ("pending_approval", "Pending Approval"),
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    )

    YEAR = (
        ("I", "First Year"),
        ("II", "Second Year"),
        ("III", "Third Year"),
        ("IV", "Fourth Year"),
    )

    full_name = models.CharField(max_length=150)

    email = models.EmailField(
        unique=True
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

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

    join_date = models.DateField(
        blank=True,
        null=True
    )

    end_date = models.DateField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="active"
    )

    is_verified = models.BooleanField(
        default=False
    )

    otp_code = models.CharField(
        max_length=6,
        blank=True,
        null=True
    )

    otp_created_at = models.DateTimeField(
        blank=True,
        null=True
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
        ("Pending", "Pending"),
        ("Rejected", "Rejected"),
        ("Draft", "Draft"),
    )

    CATEGORY = (
        ("Programming", "Programming"),
        ("Mathematics", "Mathematics"),
        ("Physics", "Physics"),
        ("Soft Skills", "Soft Skills"),
    )

    title = models.CharField(max_length=250)
    category = models.CharField(max_length=100, choices=CATEGORY)
    duration = models.CharField(max_length=20)
    description = models.TextField(blank=True)

    video_file = models.FileField(upload_to="videos/", blank=True, null=True)
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS, default="Pending")

    uploaded_by_hod = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="videos"
    )

    is_admin_video = models.BooleanField(default=False)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)


# ==========================================
# Video Watch History
# ==========================================
# ==========================================
# ONE ADDITION NEEDED IN YOUR EXISTING models.py
# ==========================================
# Your current VideoWatch model only records THAT a student watched a
# video, not HOW MUCH of it they watched. Without that, "Completion
# Rate" cannot be calculated from real data at all — it would have to
# be faked. Add one field so it's real:

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

    # NEW FIELD -----------------------------------------------------
    # How many seconds of the video this student actually watched.
    # Update this from your video player's JS (e.g. on pause/ended,
    # POST the current playback position to an endpoint that saves it
    # here). Completion % = watched_seconds / video.duration_seconds.
    watched_seconds = models.PositiveIntegerField(default=0)
    # -----------------------------------------------------------------

    def __str__(self):
        return f"{self.student.full_name} - {self.video.title}"

    class Meta:
        ordering = ["-watched_at"]
        unique_together = (("student", "video"),)




