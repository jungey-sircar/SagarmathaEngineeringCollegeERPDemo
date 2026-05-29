"""college_management_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path

from main_app.EditResultView import EditResultView

from . import extra_views, hod_views, module_views, staff_views, student_views, views

urlpatterns = [
    path("", views.login_page, name="login_page"),
    path("get_attendance", views.get_attendance, name="get_attendance"),
    path("firebase-messaging-sw.js", views.showFirebaseJS, name="showFirebaseJS"),
    path("doLogin/", views.doLogin, name="user_login"),
    path("logout_user/", views.logout_user, name="user_logout"),
    path("admin/home/", hod_views.admin_home, name="admin_home"),
    path("staff/add", hod_views.add_staff, name="add_staff"),
    path("course/add", hod_views.add_course, name="add_course"),
    path(
        "send_student_notification/",
        hod_views.send_student_notification,
        name="send_student_notification",
    ),
    path(
        "send_staff_notification/",
        hod_views.send_staff_notification,
        name="send_staff_notification",
    ),
    path("add_session/", hod_views.add_session, name="add_session"),
    path(
        "admin_notify_student",
        hod_views.admin_notify_student,
        name="admin_notify_student",
    ),
    path("admin_notify_staff", hod_views.admin_notify_staff, name="admin_notify_staff"),
    path("admin_view_profile", hod_views.admin_view_profile, name="admin_view_profile"),
    path(
        "check_email_availability",
        hod_views.check_email_availability,
        name="check_email_availability",
    ),
    path("session/manage/", hod_views.manage_session, name="manage_session"),
    path("session/edit/<int:session_id>", hod_views.edit_session, name="edit_session"),
    path(
        "student/view/feedback/",
        hod_views.student_feedback_message,
        name="student_feedback_message",
    ),
    path(
        "staff/view/feedback/",
        hod_views.staff_feedback_message,
        name="staff_feedback_message",
    ),
    path(
        "student/view/leave/",
        hod_views.view_student_leave,
        name="view_student_leave",
    ),
    path(
        "staff/view/leave/",
        hod_views.view_staff_leave,
        name="view_staff_leave",
    ),
    path(
        "attendance/view/",
        hod_views.admin_view_attendance,
        name="admin_view_attendance",
    ),
    path(
        "attendance/fetch/", hod_views.get_admin_attendance, name="get_admin_attendance"
    ),
    path("student/add/", hod_views.add_student, name="add_student"),
    path("subject/add/", hod_views.add_subject, name="add_subject"),
    path("staff/manage/", hod_views.manage_staff, name="manage_staff"),
    path("student/manage/", hod_views.manage_student, name="manage_student"),
    path("course/manage/", hod_views.manage_course, name="manage_course"),
    path("subject/manage/", hod_views.manage_subject, name="manage_subject"),
    path("staff/edit/<int:staff_id>", hod_views.edit_staff, name="edit_staff"),
    path("staff/delete/<int:staff_id>", hod_views.delete_staff, name="delete_staff"),
    path(
        "course/delete/<int:course_id>", hod_views.delete_course, name="delete_course"
    ),
    path(
        "subject/delete/<int:subject_id>",
        hod_views.delete_subject,
        name="delete_subject",
    ),
    path(
        "session/delete/<int:session_id>",
        hod_views.delete_session,
        name="delete_session",
    ),
    path(
        "student/delete/<int:student_id>",
        hod_views.delete_student,
        name="delete_student",
    ),
    path("student/edit/<int:student_id>", hod_views.edit_student, name="edit_student"),
    path("course/edit/<int:course_id>", hod_views.edit_course, name="edit_course"),
    path("subject/edit/<int:subject_id>", hod_views.edit_subject, name="edit_subject"),
    # Staff
    path("staff/home/", staff_views.staff_home, name="staff_home"),
    path("staff/apply/leave/", staff_views.staff_apply_leave, name="staff_apply_leave"),
    path("staff/feedback/", staff_views.staff_feedback, name="staff_feedback"),
    path(
        "staff/view/profile/", staff_views.staff_view_profile, name="staff_view_profile"
    ),
    path(
        "staff/attendance/take/",
        staff_views.staff_take_attendance,
        name="staff_take_attendance",
    ),
    path(
        "staff/attendance/update/",
        staff_views.staff_update_attendance,
        name="staff_update_attendance",
    ),
    path("staff/get_students/", staff_views.get_students, name="get_students"),
    path("staff/addbook/", staff_views.add_book, name="add_book"),
    path("staff/issue_book/", staff_views.issue_book, name="issue_book"),
    path(
        "staff/view_issued_book/", staff_views.view_issued_book, name="view_issued_book"
    ),
    path("selfservice/books-in-hand/", views.books_in_hand, name="books_in_hand"),
    path("selfservice/leave-balance/", views.leave_balance, name="leave_balance"),
    path("selfservice/payslip/", module_views.payslip, name="payslip_dashboard"),
    path("selfservice/store/", module_views.store, name="store_dashboard"),
    path("selfservice/academic/", views.academic_dashboard, name="academic_dashboard"),
    path("selfservice/others/", views.others_dashboard, name="others_dashboard"),
    # Modules
    path("modules/pre-admissions/", module_views.pre_admissions, name="pre_admissions"),
    path("modules/admissions/", module_views.admissions, name="admissions"),
    path("modules/admissions/<int:admission_id>/promote/", extra_views.promote_admission_to_student, name="promote_admission"),
    path("modules/admissions/bulk-promote/", extra_views.bulk_promote_admissions, name="bulk_promote_admissions"),
    path("account/change-password/", extra_views.change_password, name="change_password"),
    path("selfservice/payslip/<int:payslip_id>/pdf/", extra_views.payslip_pdf, name="payslip_pdf"),
    path("modules/examination/", module_views.examination, name="examination"),
    path("modules/human-resource/", module_views.human_resource, name="human_resource"),
    path("modules/inventory/", module_views.inventory, name="inventory"),
    # Leave / Kaaj / Optional Holiday / Substitute
    path("leave/leaves-applied/", extra_views.leaves_applied, name="leaves_applied"),
    path("leave/kaaj/apply/", extra_views.kaaj_apply, name="kaaj_apply"),
    path("leave/kaaj/list/", extra_views.kaaj_applied, name="kaaj_applied"),
    path("leave/optional-holiday/apply/", extra_views.optional_holiday_apply, name="optional_holiday_apply"),
    path("leave/optional-holiday/list/", extra_views.optional_holidays_applied, name="optional_holidays_applied"),
    path("leave/substitute/apply/", extra_views.substitute_apply, name="substitute_apply"),
    path("leave/substitute/list/", extra_views.substitutes_applied, name="substitutes_applied"),
    path("leave/substitute/mine/", extra_views.my_substitutes, name="my_substitutes"),
    path("leave/approvals/", extra_views.requests_waiting_for_approval, name="requests_waiting_for_approval"),
    # Store workflow
    path("store/requisition/", extra_views.requisition_form, name="requisition_form"),
    path("store/requisitions/", extra_views.view_past_requisitions, name="view_past_requisitions"),
    path("store/search/", extra_views.search_store_item, name="search_store_item"),
    # Academic
    path("academic/assessment-marks/", extra_views.assessment_marks_entry, name="assessment_marks_entry"),
    path("academic/study-materials/", extra_views.study_materials, name="study_materials"),
    path("academic/assignments/", extra_views.assignments, name="assignments"),
    path("academic/lesson-plans/", extra_views.lesson_plans, name="lesson_plans"),
    # Library management
    path("library/manage/", extra_views.library_manage, name="library_manage"),
    path(
        "staff/attendance/fetch/",
        staff_views.get_student_attendance,
        name="get_student_attendance",
    ),
    path("staff/attendance/save/", staff_views.save_attendance, name="save_attendance"),
    path(
        "staff/attendance/update_save/",
        staff_views.update_attendance,
        name="update_attendance",
    ),
    path("staff/fcmtoken/", staff_views.staff_fcmtoken, name="staff_fcmtoken"),
    path(
        "staff/view/notification/",
        staff_views.staff_view_notification,
        name="staff_view_notification",
    ),
    path("staff/result/add/", staff_views.staff_add_result, name="staff_add_result"),
    path("staff/result/edit/", EditResultView.as_view(), name="edit_student_result"),
    path(
        "staff/result/fetch/",
        staff_views.fetch_student_result,
        name="fetch_student_result",
    ),
    # Student
    path("student/home/", student_views.student_home, name="student_home"),
    path(
        "student/view/attendance/",
        student_views.student_view_attendance,
        name="student_view_attendance",
    ),
    path(
        "student/apply/leave/",
        student_views.student_apply_leave,
        name="student_apply_leave",
    ),
    path("student/feedback/", student_views.student_feedback, name="student_feedback"),
    path(
        "student/view/profile/",
        student_views.student_view_profile,
        name="student_view_profile",
    ),
    path("student/fcmtoken/", student_views.student_fcmtoken, name="student_fcmtoken"),
    # path('student/todo',student_views.todo,name='todo'),
    path("student/viewbooks/", student_views.view_books, name="view_books"),
    path(
        "student/view/notification/",
        student_views.student_view_notification,
        name="student_view_notification",
    ),
    path(
        "student/view/result/",
        student_views.student_view_result,
        name="student_view_result",
    ),
]
