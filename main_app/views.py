import json
import requests
from datetime import date
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt

from .EmailBackend import EmailBackend
from .models import (
    Attendance,
    Book,
    IssuedBook,
    LeaveReportStaff,
    LeaveReportStudent,
    Session,
    Staff,
    Student,
    Subject,
)

# Create your views here.


def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == "1":
            return redirect(reverse("admin_home"))
        elif request.user.user_type == "2":
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    return render(
        request,
        "main_app/login.html",
        {
            "recaptcha_site_key": settings.RECAPTCHA_PUBLIC_KEY,
        },
    )


@csrf_exempt
def doLogin(request, **kwargs):
    if request.method != "POST":
        return HttpResponse("<h4>Denied</h4>")
    else:
        # Google recaptcha
        captcha_token = request.POST.get("g-recaptcha-response")
        captcha_url = "https://www.google.com/recaptcha/api/siteverify"
        captcha_key = settings.RECAPTCHA_PRIVATE_KEY

        if captcha_key:
            data = {"secret": captcha_key, "response": captcha_token}
            # Make request with a timeout so a network issue doesn't block login forever
            try:
                captcha_server = requests.post(url=captcha_url, data=data, timeout=5)
                response = json.loads(captcha_server.text)
                if response.get("success") is False:
                    messages.error(request, "Invalid Captcha. Try Again")
                    return redirect("/")
            except requests.exceptions.RequestException:
                # Network error / timeout while contacting captcha server
                messages.error(request, "Captcha could not be verified. Try Again")
                return redirect("/")

        # Authenticate using Django's authenticate() so configured backends are used
        user = authenticate(
            request,
            username=request.POST.get("email"),
            password=request.POST.get("password"),
        )
        if user != None:
            login(request, user)

            # Handle "Remember Me" functionality
            remember_me = request.POST.get("remember")
            if remember_me:
                # Set session to expire when browser closes = False
                # Session will last for 30 days
                request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days in seconds
            else:
                # Set session to expire when browser closes
                request.session.set_expiry(0)

            if user.user_type == "1":
                return redirect(reverse("admin_home"))
            elif user.user_type == "2":
                return redirect(reverse("staff_home"))
            else:
                return redirect(reverse("student_home"))
        else:
            messages.error(request, "Invalid details")
            return redirect("/")


def logout_user(request):
    if request.user != None:
        logout(request)
    return redirect("/")


@csrf_exempt
def get_attendance(request):
    subject_id = request.POST.get("subject")
    session_id = request.POST.get("session")
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = Attendance.objects.filter(subject=subject, session=session)
        attendance_list = []
        for attd in attendance:
            data = {
                "id": attd.id,
                "attendance_date": str(attd.date),
                "session": attd.session.id,
            }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception as e:
        return None


def showFirebaseJS(request):
    # Embed the FIREBASE_CONFIG from Django settings into service worker JS
    firebase_config = getattr(settings, "FIREBASE_CONFIG", {}) or {}
    config_json = json.dumps(firebase_config)
    data = f"""
    // Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in
// your app's Firebase config object.
// https://firebase.google.com/docs/web/setup#config-object
    firebase.initializeApp({config});

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();
messaging.setBackgroundMessageHandler(function (payload) {
    const notification = JSON.parse(payload);
    const notificationOption = {
        body: notification.body,
        icon: notification.icon
    }
    return self.registration.showNotification(payload.notification.title, notificationOption);
});
    """
    # replace placeholder with JSON safely
    data = data.replace("{config}", config_json)
    return HttpResponse(data, content_type="application/javascript")


def books_in_hand(request):
    student = (
        Student.objects.filter(admin=request.user)
        .select_related("admin", "course")
        .first()
    )
    if student:
        issued_books = IssuedBook.objects.filter(student_id=str(student.id)).order_by(
            "-issued_date"
        )
        display_name = student.admin.get_full_name() or student.admin.first_name
    else:
        issued_books = IssuedBook.objects.all().order_by("-issued_date")
        display_name = request.user.get_full_name() or request.user.first_name

    books_in_hand_rows = []
    for issued_book in issued_books:
        book = Book.objects.filter(isbn=issued_book.isbn).first()
        days_left = (
            (issued_book.expiry_date - date.today()).days
            if issued_book.expiry_date
            else None
        )
        books_in_hand_rows.append(
            {
                "book_name": book.name if book else "Unknown book",
                "author": book.author if book else "-",
                "isbn": issued_book.isbn,
                "issued_date": issued_book.issued_date,
                "expiry_date": issued_book.expiry_date,
                "days_left": days_left,
            }
        )

    context = {
        "page_title": "Books in Hand",
        "display_name": display_name,
        "books_in_hand_rows": books_in_hand_rows,
        "total_books_in_hand": len(books_in_hand_rows),
    }
    return render(request, "main_app/books_in_hand.html", context)


def leave_balance(request):
    student = (
        Student.objects.filter(admin=request.user)
        .select_related("admin", "course")
        .first()
    )
    staff = (
        None
        if student
        else Staff.objects.filter(admin=request.user)
        .select_related("admin", "course")
        .first()
    )

    if student:
        leave_qs = LeaveReportStudent.objects.filter(student=student).order_by(
            "-created_at"
        )
        owner_name = student.admin.get_full_name() or student.admin.first_name
        page_title = "Individual Leave Summary"
    else:
        leave_qs = (
            LeaveReportStaff.objects.filter(staff=staff).order_by("-created_at")
            if staff
            else LeaveReportStaff.objects.none()
        )
        owner_name = (
            (staff.admin.get_full_name() or staff.admin.first_name)
            if staff
            else (request.user.get_full_name() or request.user.first_name)
        )
        page_title = "Leave Balance"

    summary_rows = []
    approved_count = leave_qs.filter(status=1).count()
    pending_count = leave_qs.filter(status=0).count()
    rejected_count = leave_qs.filter(status=-1).count()

    for leave in leave_qs:
        summary_rows.append(
            {
                "date": leave.date,
                "message": leave.message,
                "status": leave.status,
                "submitted_on": leave.created_at,
            }
        )

    context = {
        "page_title": page_title,
        "owner_name": owner_name,
        "approved_count": approved_count,
        "pending_count": pending_count,
        "rejected_count": rejected_count,
        "leave_rows": summary_rows,
        "leave_balance_count": approved_count,
    }
    return render(request, "main_app/leave_balance.html", context)


def payslip_dashboard(request):
    context = {
        "page_title": "Payslip",
        "message": "Payslip content will be added here for the HOD section.",
    }
    return render(request, "main_app/module_placeholder.html", context)


def store_dashboard(request):
    context = {
        "page_title": "Store",
        "message": "Store requisitions will be shown here for the HOD section.",
    }
    return render(request, "main_app/module_placeholder.html", context)


def academic_dashboard(request):
    context = {
        "page_title": "Academic",
        "message": "Academic links for the HOD section are grouped here.",
        "links": [
            {
                "label": "Manage Faculties / Departments",
                "url": reverse("manage_course"),
            },
            {"label": "Manage Subjects", "url": reverse("manage_subject")},
            {"label": "Manage Students", "url": reverse("manage_student")},
            {"label": "View Attendance", "url": reverse("admin_view_attendance")},
        ],
    }
    return render(request, "main_app/module_placeholder.html", context)


def others_dashboard(request):
    context = {
        "page_title": "Others",
        "message": "Additional HOD actions and reports are listed here.",
        "links": [
            {"label": "Staff Feedback", "url": reverse("staff_feedback_message")},
            {"label": "Student Feedback", "url": reverse("student_feedback_message")},
            {"label": "Notifications", "url": reverse("staff_view_notification")},
            {"label": "Profile", "url": reverse("staff_view_profile")},
        ],
    }
    return render(request, "main_app/module_placeholder.html", context)
