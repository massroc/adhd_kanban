# Data migration - now a no-op
# Default columns are created per-user during registration (see api/views.py RegisterView)

from django.db import migrations


def create_default_columns(apps, schema_editor):
    # No-op: columns are now created per-user on registration
    pass


def remove_default_columns(apps, schema_editor):
    # No-op
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('kanban', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_columns, remove_default_columns),
    ]
