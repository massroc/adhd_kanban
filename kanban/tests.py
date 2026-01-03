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


class CardCreationPopupTests(TestCase):
    """Tests for card creation via popup modal."""
    
    def test_add_task_with_specific_column(self):
        """Test creating a task directly in a specific column."""
        response = self.client.post(reverse('add_task'), data={
            'title': 'Task in Progress',
            'description': 'Already started',
            'status': 'in_progress',
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        task = Task.objects.get(title='Task in Progress')
        self.assertEqual(task.status, 'in_progress')
        self.assertEqual(task.description, 'Already started')
    
    def test_add_task_defaults_to_todo_if_no_status(self):
        """Test that tasks default to 'todo' when no status specified."""
        response = self.client.post(reverse('add_task'), data={
            'title': 'Default Task',
        }, follow=True)
        
        task = Task.objects.get(title='Default Task')
        self.assertEqual(task.status, 'todo')
    
    def test_add_task_with_invalid_status_defaults_to_todo(self):
        """Test that invalid status values default to 'todo'."""
        response = self.client.post(reverse('add_task'), data={
            'title': 'Invalid Status Task',
            'status': 'invalid_status',
        }, follow=True)
        
        task = Task.objects.get(title='Invalid Status Task')
        self.assertEqual(task.status, 'todo')
    
    def test_add_task_requires_title(self):
        """Test that tasks without title are not created."""
        initial_count = Task.objects.count()
        
        response = self.client.post(reverse('add_task'), data={
            'title': '',
            'description': 'No title',
        }, follow=True)
        
        self.assertEqual(Task.objects.count(), initial_count)
    
    def test_add_task_with_empty_description(self):
        """Test that tasks can be created without description."""
        response = self.client.post(reverse('add_task'), data={
            'title': 'No Description Task',
            'description': '',
        }, follow=True)
        
        task = Task.objects.get(title='No Description Task')
        self.assertEqual(task.description, '')
    
    def test_board_contains_add_task_button(self):
        """Test that the board template includes an add task button/trigger."""
        response = self.client.get(reverse('kanban_board'))
        # We'll look for a button or element that opens the modal
        # This will pass once we add the UI element
        self.assertContains(response, 'Add Task')
