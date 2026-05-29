"""Views for the new HOD/Staff modules surfaced in the Modules dropdown:
Pre Admissions, Admissions, Examination, Human Resource, Inventory.
Library and Attendance reuse existing views.
"""
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import (
    Admission,
    Announcement,
    Course,
    CustomUser,
    Exam,
    InventoryItem,
    LeaveReportStaff,
    LeaveReportStudent,
    Payslip,
    Staff,
    Student,
    Subject,
)


# ---------- Pre Admissions / Admissions ----------

def _save_admission_from_post(request, admission=None):
    candidate_name = (request.POST.get('candidate_name') or '').strip()
    email = (request.POST.get('email') or '').strip()
    phone = (request.POST.get('phone') or '').strip()
    course_id = request.POST.get('course')
    stage = request.POST.get('stage') or 'inquiry'
    status = request.POST.get('status') or 'pending'
    notes = request.POST.get('notes') or ''

    if not candidate_name or not email:
        messages.error(request, 'Candidate name and email are required.')
        return None

    course = Course.objects.filter(id=course_id).first() if course_id else None
    if admission is None:
        admission = Admission()
    admission.candidate_name = candidate_name
    admission.email = email
    admission.phone = phone
    admission.course = course
    admission.stage = stage
    admission.status = status
    admission.notes = notes
    admission.save()
    return admission


def pre_admissions(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            Admission.objects.filter(id=request.POST.get('id')).delete()
            messages.success(request, 'Inquiry removed.')
        elif action == 'promote':
            admission = get_object_or_404(Admission, id=request.POST.get('id'))
            admission.stage = 'admitted'
            admission.status = 'approved'
            admission.save()
            messages.success(request, f'{admission.candidate_name} promoted to Admissions.')
        else:
            forced_stage = request.POST.copy()
            forced_stage['stage'] = 'inquiry'
            request.POST = forced_stage
            if _save_admission_from_post(request):
                messages.success(request, 'Inquiry added.')
        return redirect(reverse('pre_admissions'))

    inquiries = Admission.objects.filter(stage='inquiry')
    context = {
        'page_title': 'Pre Admissions',
        'inquiries': inquiries,
        'courses': Course.objects.all(),
        'pending_count': inquiries.filter(status='pending').count(),
        'approved_count': inquiries.filter(status='approved').count(),
        'rejected_count': inquiries.filter(status='rejected').count(),
    }
    return render(request, 'modules/pre_admissions.html', context)


def admissions(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            Admission.objects.filter(id=request.POST.get('id')).delete()
            messages.success(request, 'Admission removed.')
        else:
            forced_stage = request.POST.copy()
            forced_stage['stage'] = 'admitted'
            request.POST = forced_stage
            if _save_admission_from_post(request):
                messages.success(request, 'Admission saved.')
        return redirect(reverse('admissions'))

    admitted = Admission.objects.filter(stage='admitted')
    context = {
        'page_title': 'Admissions',
        'admissions': admitted,
        'students': Student.objects.select_related('admin', 'course').all(),
        'courses': Course.objects.all(),
        'total_admissions': admitted.count(),
        'approved_count': admitted.filter(status='approved').count(),
        'pending_count': admitted.filter(status='pending').count(),
    }
    return render(request, 'modules/admissions.html', context)


# ---------- Examination ----------

def examination(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            Exam.objects.filter(id=request.POST.get('id')).delete()
            messages.success(request, 'Exam removed.')
        else:
            name = (request.POST.get('name') or '').strip()
            subject_id = request.POST.get('subject')
            exam_date = request.POST.get('exam_date')
            total_marks = request.POST.get('total_marks') or 100
            duration_minutes = request.POST.get('duration_minutes') or 180
            status = request.POST.get('status') or 'scheduled'
            subject = Subject.objects.filter(id=subject_id).first()
            if not name or not subject or not exam_date:
                messages.error(request, 'Name, subject, and exam date are required.')
            else:
                Exam.objects.create(
                    name=name,
                    subject=subject,
                    exam_date=exam_date,
                    total_marks=int(total_marks),
                    duration_minutes=int(duration_minutes),
                    status=status,
                )
                messages.success(request, 'Exam scheduled.')
        return redirect(reverse('examination'))

    exams = Exam.objects.select_related('subject', 'subject__course').all()
    context = {
        'page_title': 'Examination',
        'exams': exams,
        'subjects': Subject.objects.select_related('course').all(),
        'scheduled_count': exams.filter(status='scheduled').count(),
        'ongoing_count': exams.filter(status='ongoing').count(),
        'completed_count': exams.filter(status='completed').count(),
    }
    return render(request, 'modules/examination.html', context)


# ---------- Human Resource ----------

def human_resource(request):
    staff_qs = Staff.objects.select_related('admin', 'course').all().order_by('admin__first_name')
    staff_rows = []
    for staff in staff_qs:
        leave_count = LeaveReportStaff.objects.filter(staff=staff).count()
        pending_leaves = LeaveReportStaff.objects.filter(staff=staff, status=0).count()
        staff_rows.append({
            'id': staff.id,
            'name': f"{staff.admin.first_name} {staff.admin.last_name}".strip() or staff.admin.email,
            'email': staff.admin.email,
            'role': staff.role,
            'role_detail': staff.role_detail,
            'department': staff.course.name if staff.course else '-',
            'leave_count': leave_count,
            'pending_leaves': pending_leaves,
        })

    pending_staff_leaves = LeaveReportStaff.objects.filter(status=0).count()
    approved_staff_leaves = LeaveReportStaff.objects.filter(status=1).count()
    pending_student_leaves = LeaveReportStudent.objects.filter(status=0).count()

    context = {
        'page_title': 'Human Resource',
        'staff_rows': staff_rows,
        'total_staff': len(staff_rows),
        'total_students': Student.objects.count(),
        'total_departments': Course.objects.count(),
        'pending_staff_leaves': pending_staff_leaves,
        'approved_staff_leaves': approved_staff_leaves,
        'pending_student_leaves': pending_student_leaves,
    }
    return render(request, 'modules/human_resource.html', context)


# ---------- Inventory ----------

def inventory(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            InventoryItem.objects.filter(id=request.POST.get('id')).delete()
            messages.success(request, 'Item removed.')
        elif action == 'edit':
            item_id = request.POST.get('id')
            item = get_object_or_404(InventoryItem, id=item_id)
            item.name = (request.POST.get('name') or item.name).strip()
            item.category = (request.POST.get('category') or item.category).strip()
            item.quantity = int(request.POST.get('quantity') or item.quantity)
            item.unit = (request.POST.get('unit') or item.unit).strip()
            item.location = (request.POST.get('location') or '').strip()
            item.reorder_level = int(request.POST.get('reorder_level') or item.reorder_level)
            item.save()
            messages.success(request, 'Item updated.')
        else:
            name = (request.POST.get('name') or '').strip()
            if not name:
                messages.error(request, 'Item name is required.')
            else:
                InventoryItem.objects.create(
                    name=name,
                    category=(request.POST.get('category') or 'General').strip(),
                    quantity=int(request.POST.get('quantity') or 0),
                    unit=(request.POST.get('unit') or 'pcs').strip(),
                    location=(request.POST.get('location') or '').strip(),
                    reorder_level=int(request.POST.get('reorder_level') or 5),
                )
                messages.success(request, 'Item added.')
        return redirect(reverse('inventory'))

    items = InventoryItem.objects.all()
    low_stock = [i for i in items if i.is_low_stock]
    context = {
        'page_title': 'Inventory',
        'items': items,
        'total_items': items.count(),
        'total_quantity': items.aggregate(total=Sum('quantity'))['total'] or 0,
        'low_stock_count': len(low_stock),
        'healthy_stock_count': items.count() - len(low_stock),
        'low_stock_items': low_stock,
    }
    return render(request, 'modules/inventory.html', context)


# ---------- Payslip (real implementation) ----------

def payslip(request):
    staff = Staff.objects.filter(admin=request.user).first()
    if request.method == 'POST' and staff and request.POST.get('action') == 'generate':
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))
        basic = Decimal(request.POST.get('basic_salary') or '40000')
        allowances = Decimal(request.POST.get('allowances') or '5000')
        deductions = Decimal(request.POST.get('deductions') or '2000')
        Payslip.objects.update_or_create(
            staff=staff, month=month, year=year,
            defaults={
                'basic_salary': basic,
                'allowances': allowances,
                'deductions': deductions,
                'paid': True,
            },
        )
        messages.success(request, 'Payslip generated.')
        return redirect(reverse('payslip_dashboard'))

    if staff:
        payslips = Payslip.objects.filter(staff=staff)
        owner_name = staff.admin.get_full_name() or staff.admin.first_name
    else:
        payslips = Payslip.objects.select_related('staff', 'staff__admin').all()
        owner_name = request.user.get_full_name() or request.user.first_name

    context = {
        'page_title': 'Payslip',
        'payslips': payslips,
        'owner_name': owner_name,
        'is_staff': bool(staff),
        'month_choices': Payslip.MONTH_CHOICES,
    }
    return render(request, 'modules/payslip.html', context)


# ---------- Store (Store Requisitions) ----------

def store(request):
    # Reuse inventory data + low-stock requisitions view
    items = InventoryItem.objects.all()
    low_stock = [i for i in items if i.is_low_stock]
    requisitions = sorted(low_stock, key=lambda i: i.quantity)
    context = {
        'page_title': 'Store',
        'requisitions': requisitions,
        'requisition_count': len(requisitions),
        'total_items': items.count(),
    }
    return render(request, 'modules/store.html', context)
