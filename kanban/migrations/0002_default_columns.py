# Data migration to create default columns

from django.db import migrations


def create_default_columns(apps, schema_editor):
    Column = apps.get_model('kanban', 'Column')
    default_columns = [
        ('Backlog', 1),
        ('Next', 2),
        ('Today', 3),
        ('In Progress', 4),
        ('Done', 5),
    ]
    for name, order in default_columns:
        Column.objects.create(name=name, order=order)


def remove_default_columns(apps, schema_editor):
    Column = apps.get_model('kanban', 'Column')
    Column.objects.filter(name__in=['Backlog', 'Next', 'Today', 'In Progress', 'Done']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('kanban', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_columns, remove_default_columns),
    ]
