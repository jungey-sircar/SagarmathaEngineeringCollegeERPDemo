"""Views for the HOD dashboard dropdowns:
Leave/Kaaj, Store (requisition workflow), Academic, Library, Others.
Also: one-click promote admission -> Student/CustomUser.
"""
from datetime import timedelta, date as date_cls
from io import BytesIO
import secrets

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db.models import Q

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from .models import (
    Admission,
    Announcement,
    AssessmentMark,
    Assignment,
    Book,
    BookLoan,
    Course,
    CustomUser,
    InventoryItem,
    KaajRequest,
    LeaveReportStaff,
    LeaveReportStudent,
    LessonPlan,
    OptionalHolidayRequest,
    Payslip,
    Session,
    Staff,
    StoreRequisition,
    Student,
    StudyMaterial,
    Subject,
    SubstituteRequest,
)


def _staff(request):
    """Helper: return the current staff profile or None."""
    return Staff.objects.filter(admin=request.user).first()


# ---------- Leave / Kaaj / Optional Holiday / Substitute ----------

def leaves_applied(request):
    staff = _staff(request)
    leaves = LeaveReportStaff.objects.filter(staff=staff).order_by('-id') if staff else []
    return render(request, 'modules/leave_list.html', {
        'page_title': 'Leaves Applied', 'rows': leaves,
        'kind': 'leave', 'show_apply_link': True,
    })


def kaaj_apply(request):
    staff = _staff(request)
    if request.method == 'POST' and staff:
        try:
            KaajRequest.objects.create(
                staff=staff,
                purpose=(request.POST.get('purpose') or '').strip(),
                destination=(request.POST.get('destination') or '').strip(),
                from_date=request.POST.get('from_date'),
                to_date=request.POST.get('to_date'),
            )
            messages.success(request, 'Kaaj request submitted.')
        except Exception as exc:
            messages.error(request, f'Could not submit: {exc}')
        return redirect(reverse('kaaj_applied'))
    return render(request, 'modules/kaaj_apply.html', {'page_title': 'Apply Kaaj'})


def kaaj_applied(request):
    staff = _staff(request)
    rows = KaajRequest.objects.filter(staff=staff) if staff else KaajRequest.objects.all()
    return render(request, 'modules/kaaj_list.html', {
        'page_title': 'Kaaj Applied List', 'rows': rows, 'is_admin_view': False,
    })


def optional_holiday_apply(request):
    staff = _staff(request)
    if request.method == 'POST' and staff:
        try:
            OptionalHolidayRequest.objects.create(
                staff=staff,
                holiday_name=(request.POST.get('holiday_name') or '').strip(),
                holiday_date=request.POST.get('holiday_date'),
                reason=(request.POST.get('reason') or '').strip(),
            )
            messages.success(request, 'Optional holiday request submitted.')
        except Exception as exc:
            messages.error(request, f'Could not submit: {exc}')
        return redirect(reverse('optional_holidays_applied'))
    return render(request, 'modules/optional_holiday_apply.html', {'page_title': 'Apply Optional Holiday'})


def optional_holidays_applied(request):
    staff = _staff(request)
    rows = OptionalHolidayRequest.objects.filter(staff=staff) if staff else OptionalHolidayRequest.objects.all()
    return render(request, 'modules/optional_holiday_list.html', {
        'page_title': 'Optional Holidays Applied', 'rows': rows, 'is_admin_view': False,
    })


def substitute_apply(request):
    staff = _staff(request)
    if request.method == 'POST' and staff:
        sub_for_id = request.POST.get('substitute_for') or None
        try:
            SubstituteRequest.objects.create(
                staff=staff,
                substitute_for=Staff.objects.filter(id=sub_for_id).first() if sub_for_id else None,
                work_date=request.POST.get('work_date'),
                description=(request.POST.get('description') or '').strip(),
            )
            messages.success(request, 'Substitute / extra work day request submitted.')
        except Exception as exc:
            messages.error(request, f'Could not submit: {exc}')
        return redirect(reverse('substitutes_applied'))
    return render(request, 'modules/substitute_apply.html', {
        'page_title': 'Apply Substitute / Extra Days',
        'staff_options': Staff.objects.exclude(admin=request.user),
    })


def substitutes_applied(request):
    rows = SubstituteRequest.objects.all()
    return render(request, 'modules/substitute_list.html', {
        'page_title': 'Substitutes / Extra Applied', 'rows': rows, 'is_admin_view': False,
    })


def my_substitutes(request):
    staff = _staff(request)
    rows = SubstituteRequest.objects.filter(substitute_for=staff) if staff else []
    return render(request, 'modules/substitute_list.html', {
        'page_title': 'My Substitues / Extra Days', 'rows': rows, 'is_admin_view': False,
    })


def requests_waiting_for_approval(request):
    """HOD/Staff approver dashboard for every pending request type."""
    if request.method == 'POST':
        action = request.POST.get('action')  # 'approve' or 'reject'
        kind = request.POST.get('kind')
        row_id = request.POST.get('id')
        new_status = 1 if action == 'approve' else -1
        model_map = {
            'leave': LeaveReportStaff,
            'kaaj': KaajRequest,
            'optional_holiday': OptionalHolidayRequest,
            'substitute': SubstituteRequest,
        }
        model = model_map.get(kind)
        if model:
            obj = model.objects.filter(id=row_id).first()
            if obj:
                obj.status = new_status
                obj.save()
                messages.success(request, f'{kind.replace("_", " ").title()} request {action}d.')
        return redirect(reverse('requests_waiting_for_approval'))

    return render(request, 'modules/approvals.html', {
        'page_title': 'Requests Waiting For Approval',
        'leave_rows': LeaveReportStaff.objects.filter(status=0),
        'kaaj_rows': KaajRequest.objects.filter(status=0),
        'optional_holiday_rows': OptionalHolidayRequest.objects.filter(status=0),
        'substitute_rows': SubstituteRequest.objects.filter(status=0),
    })


# ---------- Store: Requisition Form / View Past / Search Item ----------

def requisition_form(request):
    staff = _staff(request)
    if request.method == 'POST' and staff:
        try:
            item = get_object_or_404(InventoryItem, id=request.POST.get('item'))
            StoreRequisition.objects.create(
                requested_by=staff,
                item=item,
                quantity=int(request.POST.get('quantity') or 1),
                reason=(request.POST.get('reason') or '').strip(),
            )
            messages.success(request, 'Requisition submitted.')
        except Exception as exc:
            messages.error(request, f'Could not submit: {exc}')
        return redirect(reverse('view_past_requisitions'))
    return render(request, 'modules/requisition_form.html', {
        'page_title': 'Requisition Form',
        'items': InventoryItem.objects.all(),
    })


def view_past_requisitions(request):
    if request.method == 'POST':
        action = request.POST.get('action')  # approve / reject / fulfil / delete
        req_id = request.POST.get('id')
        req = get_object_or_404(StoreRequisition, id=req_id)
        decider = _staff(request)
        if action == 'approve':
            req.status = StoreRequisition.APPROVED_STORE
            req.decided_by = decider
        elif action == 'reject':
            req.status = StoreRequisition.REJECTED_STORE
            req.decided_by = decider
        elif action == 'fulfil':
            req.status = StoreRequisition.FULFILLED
            req.decided_by = decider
            # Deduct from inventory if available
            if req.item.quantity >= req.quantity:
                req.item.quantity -= req.quantity
                req.item.save()
        elif action == 'delete':
            req.delete()
            messages.success(request, 'Requisition deleted.')
            return redirect(reverse('view_past_requisitions'))
        req.save()
        messages.success(request, f'Requisition #{req.id} updated to {req.get_status_display()}.')
        return redirect(reverse('view_past_requisitions'))

    staff = _staff(request)
    rows = StoreRequisition.objects.select_related('item', 'requested_by__admin').all()
    return render(request, 'modules/requisitions_list.html', {
        'page_title': 'Past Store Requisitions',
        'rows': rows,
        'mine': StoreRequisition.objects.filter(requested_by=staff) if staff else None,
    })


def search_store_item(request):
    q = (request.GET.get('q') or '').strip()
    results = InventoryItem.objects.filter(
        Q(name__icontains=q) | Q(category__icontains=q) | Q(location__icontains=q)
    ) if q else InventoryItem.objects.none()
    return render(request, 'modules/store_search.html', {
        'page_title': 'Search Item In Store',
        'q': q,
        'results': results,
    })


# ---------- Academic: Assessment / Study Materials / Assignments / Lesson Plans ----------

def assessment_marks_entry(request):
    if request.method == 'POST':
        student = get_object_or_404(Student, id=request.POST.get('student'))
        subject = get_object_or_404(Subject, id=request.POST.get('subject'))
        AssessmentMark.objects.create(
            student=student, subject=subject,
            assessment_name=(request.POST.get('assessment_name') or 'Internal').strip(),
            marks_obtained=request.POST.get('marks_obtained') or 0,
            max_marks=request.POST.get('max_marks') or 100,
        )
        messages.success(request, 'Marks recorded.')
        return redirect(reverse('assessment_marks_entry'))
    return render(request, 'modules/assessment_marks.html', {
        'page_title': 'Assessment Marks Entry',
        'students': Student.objects.select_related('admin', 'course').all(),
        'subjects': Subject.objects.select_related('course').all(),
        'rows': AssessmentMark.objects.select_related('student__admin', 'subject').all()[:100],
    })


def study_materials(request):
    staff = _staff(request)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            StudyMaterial.objects.filter(id=request.POST.get('id')).delete()
            messages.success(request, 'Study material removed.')
        else:
            subject = get_object_or_404(Subject, id=request.POST.get('subject'))
            StudyMaterial.objects.create(
                title=(request.POST.get('title') or 'Untitled').strip(),
                subject=subject,
                description=(request.POST.get('description') or '').strip(),
                link=(request.POST.get('link') or '').strip(),
                uploaded_by=staff,
            )
            messages.success(request, 'Study material added.')
        return redirect(reverse('study_materials'))
    return render(request, 'modules/study_materials.html', {
        'page_title': 'Study Materials',
        'subjects': Subject.objects.select_related('course').all(),
        'rows': StudyMaterial.objects.select_related('subject', 'uploaded_by__admin').all(),
    })


def assignments(request):
    staff = _staff(request)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            Assignment.objects.filter(id=request.POST.get('id')).delete()
            messages.success(request, 'Assignment removed.')
        else:
            subject = get_object_or_404(Subject, id=request.POST.get('subject'))
            Assignment.objects.create(
                title=(request.POST.get('title') or 'Assignment').strip(),
                subject=subject,
                description=(request.POST.get('description') or '').strip(),
                due_date=request.POST.get('due_date') or date_cls.today(),
                assigned_by=staff,
            )
            messages.success(request, 'Assignment created.')
        return redirect(reverse('assignments'))
    return render(request, 'modules/assignments.html', {
        'page_title': 'Assignments',
        'subjects': Subject.objects.select_related('course').all(),
        'rows': Assignment.objects.select_related('subject').all(),
    })


def lesson_plans(request):
    staff = _staff(request)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            LessonPlan.objects.filter(id=request.POST.get('id')).delete()
            messages.success(request, 'Lesson plan removed.')
        else:
            subject = get_object_or_404(Subject, id=request.POST.get('subject'))
            LessonPlan.objects.create(
                title=(request.POST.get('title') or 'Lesson').strip(),
                subject=subject,
                week_number=int(request.POST.get('week_number') or 1),
                topics=(request.POST.get('topics') or '').strip(),
                is_lab=request.POST.get('is_lab') == 'on',
                prepared_by=staff,
            )
            messages.success(request, 'Lesson / lab plan added.')
        return redirect(reverse('lesson_plans'))
    return render(request, 'modules/lesson_plans.html', {
        'page_title': 'Lesson / Lab Plan',
        'subjects': Subject.objects.select_related('course').all(),
        'rows': LessonPlan.objects.select_related('subject').all(),
    })


# ---------- Library management (book CRUD + issue/return) ----------

def library_manage(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_book':
            isbn = request.POST.get('isbn')
            Book.objects.update_or_create(
                isbn=isbn,
                defaults={
                    'name': (request.POST.get('name') or '').strip(),
                    'author': (request.POST.get('author') or '').strip(),
                    'category': (request.POST.get('category') or 'General').strip(),
                },
            )
            messages.success(request, 'Book saved.')
        elif action == 'delete_book':
            Book.objects.filter(id=request.POST.get('id')).delete()
            messages.success(request, 'Book deleted.')
        elif action == 'issue_book':
            book = get_object_or_404(Book, id=request.POST.get('book_id'))
            borrower = get_object_or_404(CustomUser, id=request.POST.get('borrower_id'))
            due = request.POST.get('due_on') or (date_cls.today() + timedelta(days=14))
            BookLoan.objects.create(book=book, borrower=borrower, due_on=due)
            messages.success(request, f'Issued "{book.name}" to {borrower.email}.')
        elif action == 'return_book':
            loan = get_object_or_404(BookLoan, id=request.POST.get('loan_id'))
            loan.returned_on = date_cls.today()
            loan.save()
            messages.success(request, 'Book marked returned.')
        return redirect(reverse('library_manage'))

    return render(request, 'modules/library_manage.html', {
        'page_title': 'Library Management',
        'books': Book.objects.all(),
        'loans': BookLoan.objects.select_related('book', 'borrower').filter(returned_on__isnull=True),
        'past_loans': BookLoan.objects.select_related('book', 'borrower').filter(returned_on__isnull=False).order_by('-returned_on')[:20],
        'borrowers': CustomUser.objects.filter(user_type__in=['2', '3']).order_by('email'),
    })


# ---------- One-click promote Admission -> Student ----------

def _promote_admission(admission):
    """Core: create CustomUser+Student from an Admission. Returns
    (user, temp_password, error_message). On error, the first two are None."""
    course = admission.course or Course.objects.first()
    if not course:
        return None, None, 'No Course exists. Create one first.'

    session = Session.objects.order_by('-end_year').first()
    if not session:
        today = date_cls.today()
        session = Session.objects.create(
            start_year=today.replace(month=1, day=1),
            end_year=today.replace(month=12, day=31),
        )

    if CustomUser.objects.filter(email=admission.email).exists():
        return None, None, f'A user with {admission.email} already exists.'

    parts = admission.candidate_name.split(' ', 1)
    first = parts[0]
    last = parts[1] if len(parts) > 1 else ''
    temp_password = secrets.token_urlsafe(6)

    user = CustomUser.objects.create_user(
        email=admission.email,
        password=temp_password,
        first_name=first,
        last_name=last,
        user_type='3',
        gender='M',
        address='',
    )
    user.must_change_password = True
    user.save()

    student = Student.objects.filter(admin=user).first()
    if student is None:
        student = Student.objects.create(admin=user, course=course, session=session)
    else:
        student.course = course
        student.session = session
        student.save()

    admission.status = 'approved'
    admission.stage = 'admitted'
    admission.save()
    return user, temp_password, None


def _email_temp_password(user, temp_password):
    """Send the temp password. With console backend the email is printed to
    backend logs which is fine for dev/demo."""
    try:
        send_mail(
            subject='Welcome to Sagarmatha College — Your Student Account',
            message=(
                f'Hello {user.first_name},\n\n'
                'Your student account has been created.\n\n'
                f'Email: {user.email}\n'
                f'Temporary password: {temp_password}\n\n'
                'Please log in and change your password on first sign-in.\n\n'
                'Regards,\nSagarmatha College ERP'
            ),
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=[user.email],
            fail_silently=True,
        )
        return True
    except Exception:
        return False


def promote_admission_to_student(request, admission_id):
    if request.method != 'POST':
        return redirect(reverse('admissions'))
    admission = get_object_or_404(Admission, id=admission_id)
    user, temp_password, err = _promote_admission(admission)
    if err:
        messages.error(request, f'Cannot promote: {err}')
        return redirect(reverse('admissions'))

    emailed = _email_temp_password(user, temp_password)
    if emailed:
        messages.success(
            request,
            f'Promoted {admission.candidate_name} to Student. '
            f'Login email + temp password have been sent to {user.email} '
            f'(also visible in backend logs / temp password: {temp_password}).',
        )
    else:
        messages.success(
            request,
            f'Promoted {admission.candidate_name} to Student. '
            f'Email send failed; temp password: {temp_password}.',
        )
    return redirect(reverse('admissions'))


def bulk_promote_admissions(request):
    """Promote every selected Admission (POST `ids` list) to Student."""
    if request.method != 'POST':
        return redirect(reverse('admissions'))
    ids = request.POST.getlist('ids')
    if not ids:
        messages.warning(request, 'No admissions selected.')
        return redirect(reverse('admissions'))

    promoted, skipped = [], []
    for admission_id in ids:
        admission = Admission.objects.filter(id=admission_id).first()
        if admission is None:
            continue
        user, temp_password, err = _promote_admission(admission)
        if err:
            skipped.append(f'{admission.candidate_name}: {err}')
            continue
        _email_temp_password(user, temp_password)
        promoted.append(f'{admission.candidate_name} ({user.email})')

    if promoted:
        messages.success(
            request,
            f'Promoted {len(promoted)} admission(s): ' + ', '.join(promoted)
            + '. Temp passwords have been emailed (console backend logs them).',
        )
    if skipped:
        messages.warning(request, 'Skipped: ' + '; '.join(skipped))
    return redirect(reverse('admissions'))


# ---------- First-login password change ----------

def change_password(request):
    user = request.user
    if request.method == 'POST':
        old = request.POST.get('old_password') or ''
        new1 = request.POST.get('new_password1') or ''
        new2 = request.POST.get('new_password2') or ''
        if not user.check_password(old):
            messages.error(request, 'Current password is incorrect.')
        elif len(new1) < 6:
            messages.error(request, 'New password must be at least 6 characters.')
        elif new1 != new2:
            messages.error(request, 'New passwords do not match.')
        else:
            user.set_password(new1)
            user.must_change_password = False
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed. Welcome!')
            # Route by user_type
            if user.user_type == '1':
                return redirect(reverse('admin_home'))
            if user.user_type == '2':
                return redirect(reverse('staff_home'))
            return redirect(reverse('student_home'))
    return render(request, 'modules/change_password.html', {
        'page_title': 'Change Password',
        'forced': user.must_change_password,
    })


# ---------- Payslip PDF ----------

def payslip_pdf(request, payslip_id):
    payslip = get_object_or_404(Payslip, id=payslip_id)
    # Authorization: staff can download only their own; HOD can download any
    requester_staff = _staff(request)
    if (requester_staff is None) or (
        payslip.staff_id != requester_staff.id
        and (requester_staff.role or '').strip().lower().startswith('hod') is False
    ):
        # Allow user_type=1 (admin) too
        if request.user.user_type != '1':
            return HttpResponse('Forbidden', status=403)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'title', parent=styles['Heading1'], fontSize=20, leading=24,
        textColor=colors.HexColor('#1f3a68'), spaceAfter=4,
    )
    label_style = ParagraphStyle('label', parent=styles['Normal'], textColor=colors.grey)

    story = []
    story.append(Paragraph('Sagarmatha Engineering College', title_style))
    story.append(Paragraph('Payslip', styles['Heading2']))
    story.append(Spacer(1, 6))

    employee_table = Table([
        ['Employee', f'{payslip.staff.admin.first_name} {payslip.staff.admin.last_name}'],
        ['Email', payslip.staff.admin.email],
        ['Department', payslip.staff.course.name if payslip.staff.course else '-'],
        ['Period', f'{payslip.get_month_display()} {payslip.year}'],
        ['Generated', payslip.generated_at.strftime('%Y-%m-%d %H:%M')],
    ], colWidths=[40*mm, 110*mm])
    employee_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.lightgrey),
    ]))
    story.append(employee_table)
    story.append(Spacer(1, 12))

    earnings_table = Table([
        ['Earnings', 'Amount (NPR)'],
        ['Basic Salary', f'{payslip.basic_salary:,.2f}'],
        ['Allowances', f'{payslip.allowances:,.2f}'],
        ['Gross', f'{(payslip.basic_salary + payslip.allowances):,.2f}'],
        ['', ''],
        ['Deductions', f'{payslip.deductions:,.2f}'],
        ['', ''],
        ['Net Pay', f'{payslip.net_pay:,.2f}'],
    ], colWidths=[100*mm, 50*mm])
    earnings_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f3a68')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f0fe')),
    ]))
    story.append(earnings_table)
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f'Status: <b>{"Paid" if payslip.paid else "Pending"}</b>',
        label_style,
    ))
    story.append(Spacer(1, 36))
    story.append(Paragraph(
        '<i>This is a computer-generated payslip and does not require a signature.</i>',
        label_style,
    ))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    filename = (
        f'payslip_{payslip.staff.admin.last_name or payslip.staff.admin.first_name}_'
        f'{payslip.year}_{payslip.month:02d}.pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
