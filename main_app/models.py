from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime,timedelta




class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = CustomUser(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        assert extra_fields["is_staff"]
        assert extra_fields["is_superuser"]
        return self._create_user(email, password, **extra_fields)


class Session(models.Model):
    start_year = models.DateField()
    end_year = models.DateField()

    def __str__(self):
        return "From " + str(self.start_year) + " to " + str(self.end_year)


class CustomUser(AbstractUser):
    USER_TYPE = ((1, "HOD"), (2, "Staff"), (3, "Student"))
    GENDER = [("M", "Male"), ("F", "Female")]
    
    
    username = None  # Removed username, using email instead
    email = models.EmailField(unique=True)
    user_type = models.CharField(default=1, choices=USER_TYPE, max_length=1)
    gender = models.CharField(max_length=1, choices=GENDER)
    profile_pic = models.ImageField()
    address = models.TextField()
    fcm_token = models.TextField(default="")  # For firebase notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    must_change_password = models.BooleanField(default=False)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return  self.first_name + " " + self.last_name


class Admin(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)



class Course(models.Model):
    name = models.CharField(max_length=120)
    hod = models.OneToOneField(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hod_course'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    name = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.PositiveIntegerField()
    category = models.CharField(max_length=50)

    def __str__(self):
        return str(self.name) + " ["+str(self.isbn)+']'


class Student(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return self.admin.last_name + ", " + self.admin.first_name

class Library(models.Model):
    student = models.ForeignKey(Student,  on_delete=models.CASCADE, null=True, blank=False)
    book = models.ForeignKey(Book,  on_delete=models.CASCADE, null=True, blank=False)
    def __str__(self):
        return str(self.student)

def expiry():
    return datetime.today() + timedelta(days=14)
class IssuedBook(models.Model):
    student_id = models.CharField(max_length=100, blank=True) 
    isbn = models.CharField(max_length=13)
    issued_date = models.DateField(auto_now=True)
    expiry_date = models.DateField(default=expiry)



class Staff(models.Model):
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    role = models.CharField(max_length=120, default='Teacher')
    role_detail = models.CharField(max_length=120, blank=True, default='')

    def __str__(self):
        return self.admin.first_name + " " +  self.admin.last_name


class Subject(models.Model):
    name = models.CharField(max_length=120)
    staff = models.ForeignKey(Staff,on_delete=models.CASCADE,)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Attendance(models.Model):
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING)
    subject = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AttendanceReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StudentResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    test = models.FloatField(default=0)
    exam = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Admission(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    STAGE_CHOICES = (
        ('inquiry', 'Pre-Admission Inquiry'),
        ('admitted', 'Admitted'),
    )
    candidate_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    stage = models.CharField(max_length=12, choices=STAGE_CHOICES, default='inquiry')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    applied_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.candidate_name} ({self.get_stage_display()})"


class Exam(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    )
    name = models.CharField(max_length=120)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_date = models.DateField()
    total_marks = models.PositiveIntegerField(default=100)
    duration_minutes = models.PositiveIntegerField(default=180)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-exam_date']

    def __str__(self):
        return f"{self.name} - {self.subject.name}"


class InventoryItem(models.Model):
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=80, default='General')
    quantity = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=20, default='pcs')
    location = models.CharField(max_length=120, blank=True)
    reorder_level = models.PositiveIntegerField(default=5)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    def __str__(self):
        return self.name


class Payslip(models.Model):
    MONTH_CHOICES = [(i, m) for i, m in enumerate(
        ['January', 'February', 'March', 'April', 'May', 'June',
         'July', 'August', 'September', 'October', 'November', 'December'], start=1
    )]
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='payslips')
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    year = models.PositiveIntegerField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.BooleanField(default=False)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year', '-month']
        unique_together = ('staff', 'month', 'year')

    @property
    def net_pay(self):
        return (self.basic_salary or 0) + (self.allowances or 0) - (self.deductions or 0)

    def __str__(self):
        return f"{self.staff} - {self.get_month_display()} {self.year}"


class Announcement(models.Model):
    title = models.CharField(max_length=160)
    body = models.TextField()
    audience = models.CharField(
        max_length=10,
        choices=(('all', 'All'), ('staff', 'Staff'), ('students', 'Students')),
        default='all',
    )
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title


# ---------- Leave / Kaaj / Optional Holiday / Substitute ----------

STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED = 0, 1, -1
APPROVAL_STATUS_CHOICES = (
    (STATUS_PENDING, 'Pending'),
    (STATUS_APPROVED, 'Approved'),
    (STATUS_REJECTED, 'Rejected'),
)


class KaajRequest(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='kaaj_requests')
    purpose = models.CharField(max_length=255)
    destination = models.CharField(max_length=160, blank=True)
    from_date = models.DateField()
    to_date = models.DateField()
    status = models.SmallIntegerField(choices=APPROVAL_STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class OptionalHolidayRequest(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='optional_holiday_requests')
    holiday_name = models.CharField(max_length=160)
    holiday_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.SmallIntegerField(choices=APPROVAL_STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class SubstituteRequest(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='substitute_requests')
    substitute_for = models.ForeignKey(
        Staff, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='substituted_by_requests',
    )
    work_date = models.DateField()
    description = models.CharField(max_length=255)
    status = models.SmallIntegerField(choices=APPROVAL_STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


# ---------- Store Requisition (approval workflow) ----------

class StoreRequisition(models.Model):
    REQUESTED, APPROVED_STORE, FULFILLED, REJECTED_STORE = 0, 1, 2, -1
    STATUS_CHOICES = (
        (REQUESTED, 'Requested'),
        (APPROVED_STORE, 'Approved'),
        (FULFILLED, 'Fulfilled'),
        (REJECTED_STORE, 'Rejected'),
    )

    requested_by = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='requisitions')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='requisitions')
    quantity = models.PositiveIntegerField(default=1)
    reason = models.CharField(max_length=255, blank=True)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=REQUESTED)
    decided_by = models.ForeignKey(
        Staff, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='decided_requisitions',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


# ---------- Academic items (Assessment, Study Material, Assignment, Lesson Plan) ----------

class AssessmentMark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assessment_marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assessment_marks')
    assessment_name = models.CharField(max_length=120, default='Internal')
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']


class StudyMaterial(models.Model):
    title = models.CharField(max_length=160)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='study_materials')
    description = models.TextField(blank=True)
    link = models.URLField(blank=True)
    uploaded_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']


class Assignment(models.Model):
    title = models.CharField(max_length=160)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    description = models.TextField(blank=True)
    due_date = models.DateField()
    assigned_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-due_date']


class LessonPlan(models.Model):
    title = models.CharField(max_length=160)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='lesson_plans')
    week_number = models.PositiveSmallIntegerField(default=1)
    topics = models.TextField(blank=True)
    is_lab = models.BooleanField(default=False)
    prepared_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['week_number']


# ---------- Library issue / return ----------

class BookLoan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans')
    borrower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='book_loans')
    issued_on = models.DateField(auto_now_add=True)
    due_on = models.DateField()
    returned_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-issued_on']

    @property
    def is_returned(self):
        return self.returned_on is not None


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if not created:
        return

    user_type = str(instance.user_type)
    if user_type == '1':
        Admin.objects.get_or_create(admin=instance)
    if user_type == '2':
        Staff.objects.get_or_create(admin=instance)
    if user_type == '3':
        Student.objects.get_or_create(admin=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    user_type = str(instance.user_type)
    if user_type == '1':
        profile, _ = Admin.objects.get_or_create(admin=instance)
        profile.save()
    if user_type == '2':
        profile, _ = Staff.objects.get_or_create(admin=instance)
        profile.save()
    if user_type == '3':
        profile, _ = Student.objects.get_or_create(admin=instance)
        profile.save()

# todos
