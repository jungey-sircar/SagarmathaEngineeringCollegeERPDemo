from rest_framework import serializers
from ..models import CustomUser, Course, Staff, Subject, Student, Attendance, AttendanceReport, LeaveReportStaff, Book, Session, StudentResult


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        exclude = ('password',)


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'


class StaffSerializer(serializers.ModelSerializer):
    admin = CustomUserSerializer(read_only=True)
    admin_id = serializers.PrimaryKeyRelatedField(write_only=True, source='admin', queryset=CustomUser.objects.all())

    class Meta:
        model = Staff
        fields = ['id', 'course', 'admin', 'admin_id', 'role', 'role_detail']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class StudentSerializer(serializers.ModelSerializer):
    admin = CustomUserSerializer(read_only=True)
    admin_id = serializers.PrimaryKeyRelatedField(write_only=True, source='admin', queryset=CustomUser.objects.all())

    class Meta:
        model = Student
        fields = ['id', 'admin', 'admin_id', 'course', 'session']


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceReport
        fields = '__all__'


class LeaveReportStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveReportStaff
        fields = '__all__'


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'


class StudentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentResult
        fields = '__all__'
