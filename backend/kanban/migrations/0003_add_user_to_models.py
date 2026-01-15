# Migration to add user ownership to columns and tasks

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('kanban', '0002_default_columns'),
    ]

    operations = [
        # Add user field to Column (nullable initially for migration)
        migrations.AddField(
            model_name='column',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='columns',
                to=settings.AUTH_USER_MODEL,
                null=True,  # Temporarily nullable
            ),
        ),
        # Add user field to Task (nullable initially for migration)
        migrations.AddField(
            model_name='task',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tasks',
                to=settings.AUTH_USER_MODEL,
                null=True,  # Temporarily nullable
            ),
        ),
    ]
