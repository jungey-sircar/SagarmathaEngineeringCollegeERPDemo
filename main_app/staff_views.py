import json

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *
from . import forms, models
from .holiday_service import get_nepali_holiday_dashboard_data
from datetime import date


def _role_text(role_name):
    return (role_name or "").strip().lower()


def _role_matches(role_name, keywords):
    role_text = _role_text(role_name)
    return any(keyword in role_text for keyword in keywords)


def _is_hod_role(role_name):
    role_text = _role_text(role_name)
    return role_text.startswith("hod") or "head of department" in role_text


def _is_coordinator_role(role_name):
    return _role_matches(
        role_name,
        ["co-ordinator", "coordinator", "department coordinator", "coordination"],
    )


def _is_academic_incharge_role(role_name):
    return _role_matches(
        role_name,
        [
            "academic incharge",
            "academic in-charge",
            "academic coordinator",
            "exam incharge",
            "exam in-charge",
        ],
    )


def _is_teacher_role(role_name):
    return _role_matches(
        role_name,
        [
            "teacher",
            "lecturer",
            "assistant teacher",
            "senior teacher",
            "subject teacher",
        ],
    )


def _department_context(staff):
    department_subjects = Subject.objects.filter(course=staff.course)
    department_students = Student.objects.filter(course=staff.course)
    department_staff = Staff.objects.filter(course=staff.course)
    attendance_list = []
    subject_list = []
    for subject in department_subjects:
        attendance_list.append(Attendance.objects.filter(subject=subject).count())
        subject_list.append(subject.name)

    return (
        department_subjects,
        department_students,
        department_staff,
        subject_list,
        attendance_list,
    )


def staff_home(request):
    staff = get_object_or_404(Staff, admin=request.user)
    total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
    role_text = _role_text(staff.role)

    if _is_hod_role(role_text):
        (
            department_subjects,
            department_students,
            department_staff,
            subject_list,
            attendance_list,
        ) = _department_context(staff)
        holiday_data = get_nepali_holiday_dashboard_data()

        from .models import (
            Admission, Announcement, InventoryItem, KaajRequest,
            OptionalHolidayRequest, StoreRequisition, SubstituteRequest,
        )
        latest_announcement = Announcement.objects.first()

        class_routine = [
            ("Sun", "Routine has not been uploaded for Sunday."),
            ("Mon", "Routine has not been uploaded for Monday."),
            ("Tue", "Routine has not been uploaded for Tuesday."),
            ("Wed", "Routine has not been uploaded for Wednesday."),
            ("Thu", "Routine has not been uploaded for Thursday."),
            ("Fri", "Routine has not been uploaded for Friday."),
            ("Sat", "Routine has not been uploaded for Saturday."),
        ]

        store_requisition_count = StoreRequisition.objects.filter(status=0).count()

        context = {
            "page_title": "HOD Dashboard",
            "staff_name": staff.admin.get_full_name() or staff.admin.first_name,
            "role_title": staff.role,
            "role_detail": staff.role_detail or staff.course.name,
            "department_name": staff.course.name if staff.course else "Unassigned",
            "total_students": department_students.count(),
            "total_staff": department_staff.count(),
            "total_subject": department_subjects.count(),
            "total_attendance": Attendance.objects.filter(
                subject__in=department_subjects
            ).count(),
            "total_leave": total_leave,
            "subject_list": subject_list,
            "attendance_list": attendance_list,
            "clearance_request_count": LeaveReportStaff.objects.filter(status=0).count(),
            "library_books_count": Book.objects.count(),
            "leave_balance_count": LeaveReportStaff.objects.filter(staff=staff, status=1).count(),
            "pending_leave_count": LeaveReportStaff.objects.filter(status=0).count()
            + LeaveReportStudent.objects.filter(status=0).count(),
            "optional_holiday_count": OptionalHolidayRequest.objects.filter(status=0).count(),
            "kaaj_tour_count": KaajRequest.objects.filter(status=0).count(),
            "store_requisition_count": store_requisition_count,
            "substitute_work_day_count": SubstituteRequest.objects.filter(status=0).count(),
            "holiday_rows": holiday_data["holiday_rows"],
            "optional_holiday_rows": holiday_data["optional_holiday_rows"],
            "holiday_period_label": holiday_data["holiday_period_label"],
            "holiday_scroll_anchor": "2083/02/15",
            "class_routine": class_routine,
            "announcement": latest_announcement.body if latest_announcement else "",
            "announcement_title": latest_announcement.title if latest_announcement else "",
        }
        return render(request, "staff_template/hod_dashboard.html", context)

    if _is_coordinator_role(role_text):
        department_subjects, department_students, _, subject_list, attendance_list = (
            _department_context(staff)
        )
        context = {
            "page_title": "Coordinator Dashboard",
            "staff_name": staff.admin.get_full_name() or staff.admin.first_name,
            "role_title": staff.role,
            "role_detail": staff.role_detail or "General Coordination",
            "department_name": staff.course.name if staff.course else "Unassigned",
            "total_students": department_students.count(),
            "total_subject": department_subjects.count(),
            "total_leave": total_leave,
            "subject_list": subject_list,
            "attendance_list": attendance_list,
        }
        return render(request, "staff_template/coordinator_dashboard.html", context)

    if _is_academic_incharge_role(role_text):
        (
            department_subjects,
            department_students,
            department_staff,
            subject_list,
            attendance_list,
        ) = _department_context(staff)
        subject_rows = [
            {"name": subject_name, "attendance": attendance_count}
            for subject_name, attendance_count in zip(subject_list, attendance_list)
        ]
        context = {
            "page_title": "Academic Incharge Dashboard",
            "staff_name": staff.admin.get_full_name() or staff.admin.first_name,
            "role_title": staff.role,
            "role_detail": staff.role_detail or "Academic oversight",
            "department_name": staff.course.name if staff.course else "Unassigned",
            "total_students": department_students.count(),
            "total_staff": department_staff.count(),
            "total_subject": department_subjects.count(),
            "total_leave": total_leave,
            "subject_list": subject_list,
            "attendance_list": attendance_list,
            "subject_rows": subject_rows,
            "academic_focus": [
                "Review subject coverage and course load",
                "Monitor approvals and leave requests",
                "Coordinate academic planning and deadlines",
            ],
        }
        return render(
            request, "staff_template/academic_incharge_dashboard.html", context
        )

    if _is_teacher_role(role_text):
        total_students = Student.objects.filter(course=staff.course).count()
        subjects = Subject.objects.filter(staff=staff)
        total_subject = subjects.count()
        attendance_list = Attendance.objects.filter(subject__in=subjects)
        total_attendance = attendance_list.count()
        attendance_list = []
        subject_list = []
        for subject in subjects:
            attendance_count = Attendance.objects.filter(subject=subject).count()
            subject_list.append(subject.name)
            attendance_list.append(attendance_count)
        context = {
            "page_title": "Teacher Dashboard",
            "total_students": total_students,
            "total_attendance": total_attendance,
            "total_leave": total_leave,
            "total_subject": total_subject,
            "subject_list": subject_list,
            "attendance_list": attendance_list,
        }
        return render(request, "staff_template/home_content.html", context)

    total_students = Student.objects.filter(course=staff.course).count()
    subjects = Subject.objects.filter(staff=staff)
    total_subject = subjects.count()
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name)
        attendance_list.append(attendance_count)
    context = {
        "page_title": "Staff Panel - "
        + str(staff.admin.first_name)
        + " "
        + str(staff.admin.last_name[0])
        + ""
        + " ("
        + str(staff.course)
        + ")",
        "total_students": total_students,
        "total_attendance": total_attendance,
        "total_leave": total_leave,
        "total_subject": total_subject,
        "subject_list": subject_list,
        "attendance_list": attendance_list,
        "staff_role": staff.role,
        "role_detail": staff.role_detail,
    }
    return render(request, "staff_template/erpnext_staff_home.html", context)


def staff_take_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        "subjects": subjects,
        "sessions": sessions,
        "page_title": "Take Attendance",
    }

    return render(request, "staff_template/staff_take_attendance.html", context)


@csrf_exempt
def get_students(request):
    subject_id = request.POST.get("subject")
    session_id = request.POST.get("session")
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        students = Student.objects.filter(course_id=subject.course.id, session=session)
        student_data = []
        for student in students:
            data = {
                "id": student.id,
                "name": student.admin.last_name + " " + student.admin.first_name,
            }
            student_data.append(data)
        return JsonResponse(
            json.dumps(student_data), content_type="application/json", safe=False
        )
    except Exception as e:
        return e


@csrf_exempt
def save_attendance(request):
    student_data = request.POST.get("student_ids")
    date = request.POST.get("date")
    subject_id = request.POST.get("subject")
    session_id = request.POST.get("session")
    students = json.loads(student_data)
    try:
        session = get_object_or_404(Session, id=session_id)
        subject = get_object_or_404(Subject, id=subject_id)
        attendance = Attendance(session=session, subject=subject, date=date)
        attendance.save()

        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get("id"))
            attendance_report = AttendanceReport(
                student=student,
                attendance=attendance,
                status=student_dict.get("status"),
            )
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")


def staff_update_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        "subjects": subjects,
        "sessions": sessions,
        "page_title": "Update Attendance",
    }

    return render(request, "staff_template/staff_update_attendance.html", context)


@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get("attendance_date_id")
    try:
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=date)
        student_data = []
        for attendance in attendance_data:
            data = {
                "id": attendance.student.admin.id,
                "name": attendance.student.admin.last_name
                + " "
                + attendance.student.admin.first_name,
                "status": attendance.status,
            }
            student_data.append(data)
        return JsonResponse(
            json.dumps(student_data), content_type="application/json", safe=False
        )
    except Exception as e:
        return e


@csrf_exempt
def update_attendance(request):
    student_data = request.POST.get("student_ids")
    date = request.POST.get("date")
    students = json.loads(student_data)
    try:
        attendance = get_object_or_404(Attendance, id=date)

        for student_dict in students:
            student = get_object_or_404(Student, admin_id=student_dict.get("id"))
            attendance_report = get_object_or_404(
                AttendanceReport, student=student, attendance=attendance
            )
            attendance_report.status = student_dict.get("status")
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")


def staff_apply_leave(request):
    form = LeaveReportStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        "form": form,
        "leave_history": LeaveReportStaff.objects.filter(staff=staff),
        "page_title": "Apply for Leave",
    }
    if request.method == "POST":
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review"
                )
                return redirect(reverse("staff_apply_leave"))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_apply_leave.html", context)


def staff_feedback(request):
    form = FeedbackStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        "form": form,
        "feedbacks": FeedbackStaff.objects.filter(staff=staff),
        "page_title": "Add Feedback",
    }
    if request.method == "POST":
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse("staff_feedback"))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_feedback.html", context)


def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    form = StaffEditForm(request.POST or None, request.FILES or None, instance=staff)
    context = {
        "form": form,
        "page_title": "View/Update Profile",
        "current_profile_pic": getattr(staff.admin.profile_pic, "url", "") if getattr(staff.admin, "profile_pic", None) else "",
    }
    if request.method == "POST":
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get("first_name")
                last_name = form.cleaned_data.get("last_name")
                password = form.cleaned_data.get("password") or None
                address = form.cleaned_data.get("address")
                gender = form.cleaned_data.get("gender")
                passport = request.FILES.get("profile_pic") or None
                admin = staff.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    admin.profile_pic = passport
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                staff.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse("staff_view_profile"))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(
                    request, "staff_template/staff_view_profile.html", context
                )
        except Exception as e:
            messages.error(request, "Error Occured While Updating Profile " + str(e))
            return render(request, "staff_template/staff_view_profile.html", context)

    return render(request, "staff_template/staff_view_profile.html", context)


@csrf_exempt
def staff_fcmtoken(request):
    token = request.POST.get("token")
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def staff_view_notification(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff)
    context = {"notifications": notifications, "page_title": "View Notifications"}
    return render(request, "staff_template/staff_view_notification.html", context)


def staff_add_result(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    sessions = Session.objects.all()
    context = {
        "page_title": "Result Upload",
        "subjects": subjects,
        "sessions": sessions,
    }
    if request.method == "POST":
        try:
            student_id = request.POST.get("student_list")
            subject_id = request.POST.get("subject")
            test = request.POST.get("test")
            exam = request.POST.get("exam")
            student = get_object_or_404(Student, id=student_id)
            subject = get_object_or_404(Subject, id=subject_id)
            try:
                data = StudentResult.objects.get(student=student, subject=subject)
                data.exam = exam
                data.test = test
                data.save()
                messages.success(request, "Scores Updated")
            except:
                result = StudentResult(
                    student=student, subject=subject, test=test, exam=exam
                )
                result.save()
                messages.success(request, "Scores Saved")
        except Exception as e:
            messages.warning(request, "Error Occured While Processing Form")
    return render(request, "staff_template/staff_add_result.html", context)


@csrf_exempt
def fetch_student_result(request):
    try:
        subject_id = request.POST.get("subject")
        student_id = request.POST.get("student")
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)
        result = StudentResult.objects.get(student=student, subject=subject)
        result_data = {"exam": result.exam, "test": result.test}
        return HttpResponse(json.dumps(result_data))
    except Exception as e:
        return HttpResponse("False")


# library
def add_book(request):
    if request.method == "POST":
        name = request.POST["name"]
        author = request.POST["author"]
        isbn = request.POST["isbn"]
        category = request.POST["category"]

        books = Book.objects.create(
            name=name, author=author, isbn=isbn, category=category
        )
        books.save()
        alert = True
        return render(request, "staff_template/add_book.html", {"alert": alert})
    context = {"page_title": "Add Book"}
    return render(request, "staff_template/add_book.html", context)


# issue book


def issue_book(request):
    form = forms.IssueBookForm()
    if request.method == "POST":
        form = forms.IssueBookForm(request.POST)
        if form.is_valid():
            obj = models.IssuedBook()
            obj.student_id = request.POST["name2"]
            obj.isbn = request.POST["isbn2"]
            obj.save()
            alert = True
            return render(
                request, "staff_template/issue_book.html", {"obj": obj, "alert": alert}
            )
    return render(request, "staff_template/issue_book.html", {"form": form})


def view_issued_book(request):
    issuedBooks = IssuedBook.objects.all()
    details = []
    for i in issuedBooks:
        days = date.today() - i.issued_date
        d = days.days
        fine = 0
        if d > 14:
            day = d - 14
            fine = day * 5
        books = list(models.Book.objects.filter(isbn=i.isbn))
        # students = list(models.Student.objects.filter(admin=i.admin))
        i = 0
        for l in books:
            t = (
                books[i].name,
                books[i].isbn,
                issuedBooks[0].issued_date,
                issuedBooks[0].expiry_date,
                fine,
            )
            i = i + 1
            details.append(t)
    return render(
        request,
        "staff_template/view_issued_book.html",
        {"issuedBooks": issuedBooks, "details": details},
    )
