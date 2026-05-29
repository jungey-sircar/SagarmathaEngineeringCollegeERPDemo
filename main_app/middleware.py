from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.shortcuts import redirect


def _is_hod_staff(user):
    """A user_type=2 staff member who acts as Head of Department."""
    if getattr(user, 'user_type', None) != '2':
        return False
    staff = getattr(user, 'staff', None)
    role = (getattr(staff, 'role', '') or '').strip().lower()
    return role.startswith('hod') or 'head of department' in role


class LoginCheckMiddleWare(MiddlewareMixin):
    """Restrict routes by user type while allowing HOD-role staff to use the
    HOD/management views (the screenshots show a staff HOD running the show).
    """

    PUBLIC_MODULES = {
        'django.contrib.auth.views',
        'main_app.views',  # login, logout, leave_balance, books_in_hand, etc.
    }

    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__
        user = request.user
        if not user.is_authenticated:
            login_paths = {reverse('login_page'), reverse('user_login')}
            if request.path in login_paths or modulename == 'django.contrib.auth.views':
                return None
            return redirect(reverse('login_page'))

        # Force first-login password change
        if getattr(user, 'must_change_password', False):
            change_url = reverse('change_password')
            logout_url = reverse('user_logout')
            if request.path == change_url or request.path == logout_url or request.path.startswith('/static/'):
                return None
            return redirect(change_url)

        # Logged-in routing rules
        user_type = getattr(user, 'user_type', None)

        if user_type == '1':  # Admin
            if modulename == 'main_app.student_views':
                return redirect(reverse('admin_home'))
            return None

        if user_type == '2':  # Staff
            if modulename == 'main_app.student_views':
                return redirect(reverse('staff_home'))
            if modulename == 'main_app.hod_views' and not _is_hod_staff(user):
                return redirect(reverse('staff_home'))
            if modulename == 'main_app.module_views' and not _is_hod_staff(user):
                return redirect(reverse('staff_home'))
            if modulename == 'main_app.extra_views':
                return None
            return None

        if user_type == '3':  # Student
            allowed_for_student = {
                'main_app.student_views',
                'main_app.views',
                'django.contrib.auth.views',
            }
            if modulename not in allowed_for_student:
                return redirect(reverse('student_home'))
            return None

        return redirect(reverse('login_page'))
