from django.db import migrations


def backfill_missing_profiles(apps, schema_editor):
    CustomUser = apps.get_model('main_app', 'CustomUser')
    Admin = apps.get_model('main_app', 'Admin')
    Staff = apps.get_model('main_app', 'Staff')
    Student = apps.get_model('main_app', 'Student')

    admin_ids = set(Admin.objects.values_list('admin_id', flat=True))
    staff_ids = set(Staff.objects.values_list('admin_id', flat=True))
    student_ids = set(Student.objects.values_list('admin_id', flat=True))

    for user in CustomUser.objects.all().only('id', 'user_type'):
        user_type = str(user.user_type)
        if user_type == '1' and user.id not in admin_ids:
            Admin.objects.create(admin_id=user.id)
        elif user_type == '2' and user.id not in staff_ids:
            Staff.objects.create(admin_id=user.id)
        elif user_type == '3' and user.id not in student_ids:
            Student.objects.create(admin_id=user.id)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0003_staff_role_staff_role_detail'),
    ]

    operations = [
        migrations.RunPython(backfill_missing_profiles, reverse_noop),
    ]
