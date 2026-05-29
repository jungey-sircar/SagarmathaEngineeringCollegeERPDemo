import django.db.models.deletion
from django.db import migrations, models


def sync_course_hods(apps, schema_editor):
    Course = apps.get_model('main_app', 'Course')
    Staff = apps.get_model('main_app', 'Staff')

    for staff in Staff.objects.select_related('admin', 'course').all():
        role_text = (staff.role or '').strip().lower()
        if role_text.startswith('hod') or 'head of department' in role_text:
            if staff.course_id:
                Course.objects.filter(hod_id=staff.admin_id).exclude(id=staff.course_id).update(hod=None)
                Course.objects.filter(id=staff.course_id).update(hod_id=staff.admin_id)


def reverse_noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0006_seed_default_courses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='hod',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='hod_course',
                to='main_app.customuser',
            ),
        ),
        migrations.RunPython(sync_course_hods, reverse_noop),
    ]
