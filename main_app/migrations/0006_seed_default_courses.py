from django.db import migrations


def seed_default_courses(apps, schema_editor):
    Course = apps.get_model('main_app', 'Course')
    Course.objects.get_or_create(name='Computer Science')


def reverse_noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0005_alter_staff_role'),
    ]

    operations = [
        migrations.RunPython(seed_default_courses, reverse_noop),
    ]