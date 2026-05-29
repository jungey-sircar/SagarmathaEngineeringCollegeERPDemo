from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    CourseSerializer, StaffSerializer, SubjectSerializer, StudentSerializer,
    AttendanceSerializer, AttendanceReportSerializer, LeaveReportStaffSerializer,
    BookSerializer, SessionSerializer, StudentResultSerializer
)
from ..models import Course, Staff, Subject, Student, Attendance, AttendanceReport, LeaveReportStaff, Book, Session, StudentResult


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.select_related('admin', 'course').all()
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated]


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.select_related('course', 'staff').all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.select_related('admin', 'course').all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related('subject').all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]


class AttendanceReportViewSet(viewsets.ModelViewSet):
    queryset = AttendanceReport.objects.select_related('student', 'attendance').all()
    serializer_class = AttendanceReportSerializer
    permission_classes = [IsAuthenticated]


class LeaveReportStaffViewSet(viewsets.ModelViewSet):
    queryset = LeaveReportStaff.objects.select_related('staff').all()
    serializer_class = LeaveReportStaffSerializer
    permission_classes = [IsAuthenticated]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]


class StudentResultViewSet(viewsets.ModelViewSet):
    queryset = StudentResult.objects.select_related('student', 'subject').all()
    serializer_class = StudentResultSerializer
    permission_classes = [IsAuthenticated]
