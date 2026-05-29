from django import forms
from django.db.models import Q
from django.forms.widgets import DateInput, TextInput

from .models import *
from . import models


ROLE_TITLE_PRESETS = [
    'HOD',
    'Co-ordinator',
    'Academic Incharge',
    'Teacher',
    'Assistant Teacher',
    'Senior Teacher',
    'Lecturer',
    'Lab Incharge',
    'Exam Incharge',
    'Library Incharge',
    'Sports Incharge',
]


def _is_hod_role(role_name):
    role_text = (role_name or '').strip().lower()
    return role_text.startswith('hod') or 'head of department' in role_text


class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class CustomUserForm(FormSettings):
    email = forms.EmailField(required=True)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea)
    password = forms.CharField(widget=forms.PasswordInput)
    widget = {
        'password': forms.PasswordInput(),
    }
    profile_pic = forms.ImageField()

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)

        if kwargs.get('instance'):
            instance = kwargs.get('instance').admin.__dict__
            self.fields['password'].required = False
            self.fields['profile_pic'].required = False
            for field in CustomUserForm.Meta.fields:
                self.fields[field].initial = instance.get(field)
            if self.instance.pk is not None:
                self.fields['password'].widget.attrs['placeholder'] = "Fill this only if you wish to update password"

    def clean_email(self, *args, **kwargs):
        formEmail = self.cleaned_data['email'].lower()
        if self.instance.pk is None:  # Insert
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError(
                    "The given email is already registered")
        else:  # Update
            dbEmail = self.Meta.model.objects.get(
                id=self.instance.pk).admin.email.lower()
            if dbEmail != formEmail:  # There has been changes
                if CustomUser.objects.filter(email=formEmail).exists():
                    raise forms.ValidationError("The given email is already registered")

        return formEmail

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'gender',  'password','profile_pic', 'address' ]


class StudentForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields + \
            ['course', 'session']


class AdminForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Admin
        fields = CustomUserForm.Meta.fields


class StaffForm(CustomUserForm):
    staff_role = forms.CharField(required=True, max_length=120, label='Role Title')
    role_detail = forms.CharField(required=False, label='Department / Coordination Area')

    def __init__(self, *args, **kwargs):
        super(StaffForm, self).__init__(*args, **kwargs)
        self.fields['course'].label = 'Department / Faculty'
        self.fields['staff_role'].help_text = 'Choose a preset role or type a custom one. Examples: HOD, Co-ordinator, Academic Incharge, Teacher.'
        self.fields['staff_role'].widget.attrs.update({
            'placeholder': 'Select or type a role title',
            'list': 'role-options',
        })
        self.fields['role_detail'].help_text = 'Optional role scope or area. Example: Academic, Sports, Exam, Library.'

        role_suggestions = list(
            Staff.objects.exclude(role__exact='').values_list('role', flat=True).distinct().order_by('role')
        )
        self.role_suggestions = list(dict.fromkeys(ROLE_TITLE_PRESETS + role_suggestions))

        if self.instance and getattr(self.instance, 'pk', None):
            self.fields['staff_role'].initial = self.instance.role
            self.fields['role_detail'].initial = self.instance.role_detail

    class Meta(CustomUserForm.Meta):
        model = Staff
        fields = CustomUserForm.Meta.fields + \
            ['course' ]

    def clean(self):
        cleaned_data = super().clean()
        staff_role = cleaned_data.get('staff_role')
        if staff_role:
            cleaned_data['staff_role'] = staff_role.strip()
        return cleaned_data


class CourseForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = 'Faculty / Department Name'
        if 'hod' in self.fields:
            self.fields['hod'].label = 'Head of Department'
            hod_ids = [
                staff.admin_id
                for staff in Staff.objects.select_related('admin').all()
                if _is_hod_role(staff.role)
            ]
            queryset = CustomUser.objects.filter(id__in=hod_ids)
            if self.instance and getattr(self.instance, 'pk', None):
                queryset = queryset.filter(Q(hod_course__isnull=True) | Q(hod_course__id=self.instance.id))
            else:
                queryset = queryset.filter(hod_course__isnull=True)
            self.fields['hod'].queryset = queryset.order_by('first_name', 'last_name')

    class Meta:
        model = Course
        fields = ['name', 'hod']


class SubjectForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(SubjectForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Subject
        fields = ['name', 'staff', 'course']


class SessionForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(SessionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Session
        fields = '__all__'
        widgets = {
            'start_year': DateInput(attrs={'type': 'date'}),
            'end_year': DateInput(attrs={'type': 'date'}),
        }


class LeaveReportStaffForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportStaffForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStaff
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class FeedbackStaffForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(FeedbackStaffForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackStaff
        fields = ['feedback']


class LeaveReportStudentForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStudent
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class FeedbackStudentForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(FeedbackStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackStudent
        fields = ['feedback']


class StudentEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StudentEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields 


class StaffEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StaffEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Staff
        fields = CustomUserForm.Meta.fields


class EditResultForm(FormSettings):
    session_year = forms.ModelChoiceField(
        label="Session Year", queryset=Session.objects.none(), required=True)

    def __init__(self, *args, **kwargs):
        super(EditResultForm, self).__init__(*args, **kwargs)
        self.fields['session_year'].queryset = Session.objects.all()

    class Meta:
        model = StudentResult
        fields = ['session_year', 'subject', 'student', 'test', 'exam']

#todos
# class TodoForm(forms.ModelForm):
#     class Meta:
#         model=Todo
#         fields=["title","is_finished"]

#issue book

class IssueBookForm(forms.Form):
    isbn2 = forms.ModelChoiceField(queryset=models.Book.objects.none(), empty_label="Book Name [ISBN]", to_field_name="isbn", label="Book (Name and ISBN)")
    name2 = forms.ModelChoiceField(queryset=models.Student.objects.none(), empty_label="Name ", to_field_name="", label="Student Details")

    isbn2.widget.attrs.update({'class': 'form-control'})
    name2.widget.attrs.update({'class':'form-control'})

    def __init__(self, *args, **kwargs):
        super(IssueBookForm, self).__init__(*args, **kwargs)
        self.fields['isbn2'].queryset = models.Book.objects.all()
        self.fields['name2'].queryset = models.Student.objects.all()

