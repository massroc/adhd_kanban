from django.test import TestCase
from django.urls import reverse
from .models import Task
import json


class KanbanViewsTests(TestCase):
    def test_board_renders(self):
        response = self.client.get(reverse('kanban_board'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ADHD Kanban Organizer')

    def test_add_task_creates_task(self):
        response = self.client.post(reverse('add_task'), data={
            'title': 'Test Task',
            'description': 'Desc',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Task.objects.filter(title='Test Task').exists())

    def test_move_task_updates_status(self):
        task = Task.objects.create(title='Move me')
        # Obtain CSRF by loading page to set cookie
        self.client.get(reverse('kanban_board'))
        response = self.client.post(
            reverse('move_task'),
            data=json.dumps({'task_id': task.id, 'new_status': 'in_progress'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, 'in_progress')
