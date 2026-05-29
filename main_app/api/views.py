from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import (
    Staff,
    Subject,
    Student,
    Attendance,
    Course,
    LeaveReportStaff,
    Book,
    AttendanceReport,
)
from ..holiday_service import get_nepali_holiday_dashboard_data


class HODDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # ensure user has a Staff profile
        staff = get_object_or_404(Staff, admin=request.user)
        role_text = (staff.role or "").strip().lower()
        # only HODs should use this endpoint, but return data anyway
        department_subjects = Subject.objects.filter(course=staff.course)
        department_students = Student.objects.filter(course=staff.course)
        department_staff = Staff.objects.filter(course=staff.course)

        subject_list = [s.name for s in department_subjects]
        attendance_list = [
            Attendance.objects.filter(subject=s).count() for s in department_subjects
        ]

        holiday_data = get_nepali_holiday_dashboard_data()

        class_routine = [
            ("Sun", "Routine has not been uploaded for Sunday."),
            ("Mon", "Routine has not been uploaded for Monday."),
            ("Tue", "Routine has not been uploaded for Tuesday."),
            ("Wed", "Routine has not been uploaded for Wednesday."),
            ("Thu", "Routine has not been uploaded for Thursday."),
            ("Fri", "Routine has not been uploaded for Friday."),
            ("Sat", "Routine has not been uploaded for Saturday."),
        ]

        data = {
            "page_title": "HOD Dashboard",
            "staff_name": staff.admin.get_full_name() or staff.admin.first_name,
            "role_title": staff.role,
            "role_detail": staff.role_detail
            or (staff.course.name if staff.course else ""),
            "department_name": staff.course.name if staff.course else "Unassigned",
            "total_students": department_students.count(),
            "total_staff": department_staff.count(),
            "total_subject": department_subjects.count(),
            "total_attendance": Attendance.objects.filter(
                subject__in=department_subjects
            ).count(),
            "total_leave": LeaveReportStaff.objects.filter(staff=staff).count(),
            "subject_list": subject_list,
            "attendance_list": attendance_list,
            "clearance_request_count": 0,
            "library_books_count": Book.objects.count(),
            "leave_balance_count": 0,
            "pending_leave_count": LeaveReportStaff.objects.filter(status=0).count(),
            "holiday_rows": holiday_data["holiday_rows"],
            "optional_holiday_rows": holiday_data["optional_holiday_rows"],
            "holiday_period_label": holiday_data["holiday_period_label"],
            "class_routine": class_routine,
            "announcement": "",
        }

        return Response(data)
