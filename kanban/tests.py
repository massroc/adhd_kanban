from django.test import TestCase
from django.urls import reverse
from .models import Task, Column
import json


class ColumnModelTests(TestCase):
    """Tests for the Column model."""
    
    def test_create_column(self):
        """Test creating a column with name and order."""
        column = Column.objects.create(name='Backlog', order=1)
        self.assertEqual(column.name, 'Backlog')
        self.assertEqual(column.order, 1)
    
    def test_column_string_representation(self):
        """Test the string representation of a column."""
        column = Column.objects.create(name='In Progress', order=3)
        self.assertEqual(str(column), 'In Progress')
    
    def test_columns_ordered_by_order_field(self):
        """Test that columns are retrieved in order."""
        # Clear any existing columns first
        Column.objects.all().delete()
        
        # Create test columns
        Column.objects.create(name='Done', order=5)
        Column.objects.create(name='Backlog', order=1)
        Column.objects.create(name='Today', order=3)
        
        columns = list(Column.objects.all())
        self.assertEqual(columns[0].name, 'Backlog')
        self.assertEqual(columns[1].name, 'Today')
        self.assertEqual(columns[2].name, 'Done')


class ColumnCRUDTests(TestCase):
    """Tests for creating, updating, and deleting columns."""
    
    def setUp(self):
        """Create default columns for each test."""
        # Clear any default columns from migration
        Column.objects.all().delete()
        
        self.backlog = Column.objects.create(name='Backlog', order=1)
        self.next = Column.objects.create(name='Next', order=2)
        self.done = Column.objects.create(name='Done', order=3)
    
    def test_add_new_column(self):
        """Test adding a new column."""
        response = self.client.post(reverse('add_column'), data={
            'name': 'Blocked',
            'order': 4,
        })
        
        self.assertEqual(Column.objects.count(), 4)
        new_column = Column.objects.get(name='Blocked')
        self.assertEqual(new_column.order, 4)
    
    def test_rename_column(self):
        """Test renaming an existing column."""
        response = self.client.post(reverse('rename_column', args=[self.backlog.id]), data={
            'name': 'Icebox',
        })
        
        self.backlog.refresh_from_db()
        self.assertEqual(self.backlog.name, 'Icebox')
    
    def test_delete_column_with_no_tasks(self):
        """Test deleting a column that has no tasks."""
        column_id = self.next.id
        response = self.client.post(reverse('delete_column', args=[column_id]))
        
        self.assertEqual(Column.objects.count(), 2)
        self.assertFalse(Column.objects.filter(id=column_id).exists())
    
    def test_delete_column_moves_tasks_to_backlog(self):
        """Test that deleting a column moves its tasks to Backlog."""
        # Create tasks in the 'Next' column
        task1 = Task.objects.create(title='Task 1', column=self.next)
        task2 = Task.objects.create(title='Task 2', column=self.next)
        
        response = self.client.post(reverse('delete_column', args=[self.next.id]))
        
        # Tasks should be moved to Backlog (first column by order)
        task1.refresh_from_db()
        task2.refresh_from_db()
        self.assertEqual(task1.column, self.backlog)
        self.assertEqual(task2.column, self.backlog)
    
    def test_cannot_delete_last_column(self):
        """Test that you cannot delete the last remaining column."""
        # Delete all but one column
        self.next.delete()
        self.done.delete()
        
        response = self.client.post(reverse('delete_column', args=[self.backlog.id]))
        
        # Should still have 1 column
        self.assertEqual(Column.objects.count(), 1)
        self.assertTrue(Column.objects.filter(id=self.backlog.id).exists())
    
    def test_reorder_columns(self):
        """Test reordering columns via drag and drop."""
        # Swap order of Next and Done
        response = self.client.post(reverse('reorder_columns'), data=json.dumps({
            'column_orders': [
                {'id': self.backlog.id, 'order': 1},
                {'id': self.done.id, 'order': 2},
                {'id': self.next.id, 'order': 3},
            ]
        }), content_type='application/json')
        
        self.backlog.refresh_from_db()
        self.next.refresh_from_db()
        self.done.refresh_from_db()
        
        self.assertEqual(self.backlog.order, 1)
        self.assertEqual(self.done.order, 2)
        self.assertEqual(self.next.order, 3)
    
    def test_max_12_columns(self):
        """Test that users cannot create more than 12 columns."""
        # Create 9 more columns (we already have 3)
        for i in range(4, 13):
            Column.objects.create(name=f'Column {i}', order=i)
        
        # Try to create 13th column
        response = self.client.post(reverse('add_column'), data={
            'name': 'Too Many',
            'order': 13,
        })
        
        # Should still have only 12
        self.assertEqual(Column.objects.count(), 12)


class TaskColumnIntegrationTests(TestCase):
    """Tests for Task model integration with Column model."""
    
    def setUp(self):
        """Create columns and tasks."""
        # Clear any default columns from migration
        Column.objects.all().delete()
        
        self.backlog = Column.objects.create(name='Backlog', order=1)
        self.in_progress = Column.objects.create(name='In Progress', order=2)
        self.done = Column.objects.create(name='Done', order=3)
    
    def test_create_task_in_column(self):
        """Test creating a task in a specific column."""
        task = Task.objects.create(
            title='Test Task',
            description='Description',
            column=self.backlog
        )
        
        self.assertEqual(task.column, self.backlog)
        self.assertEqual(task.title, 'Test Task')
    
    def test_move_task_between_columns(self):
        """Test moving a task from one column to another."""
        task = Task.objects.create(title='Move me', column=self.backlog)
        
        # Move to In Progress
        task.column = self.in_progress
        task.save()
        
        task.refresh_from_db()
        self.assertEqual(task.column, self.in_progress)
    
    def test_tasks_have_order_field(self):
        """Test that tasks have an order field for prioritization."""
        task1 = Task.objects.create(title='Task 1', column=self.backlog, order=1)
        task2 = Task.objects.create(title='Task 2', column=self.backlog, order=2)
        
        self.assertEqual(task1.order, 1)
        self.assertEqual(task2.order, 2)
    
    def test_tasks_ordered_by_order_field(self):
        """Test that tasks are retrieved in order within a column."""
        task3 = Task.objects.create(title='Task 3', column=self.backlog, order=3)
        task1 = Task.objects.create(title='Task 1', column=self.backlog, order=1)
        task2 = Task.objects.create(title='Task 2', column=self.backlog, order=2)
        
        tasks = list(self.backlog.tasks.all())
        self.assertEqual(tasks[0].title, 'Task 1')
        self.assertEqual(tasks[1].title, 'Task 2')
        self.assertEqual(tasks[2].title, 'Task 3')
    
    def test_reorder_tasks_within_column(self):
        """Test reordering tasks within the same column."""
        task1 = Task.objects.create(title='Task 1', column=self.backlog, order=1)
        task2 = Task.objects.create(title='Task 2', column=self.backlog, order=2)
        task3 = Task.objects.create(title='Task 3', column=self.backlog, order=3)
        
        # Reorder: move task3 to position 1
        response = self.client.post(reverse('reorder_tasks'), data=json.dumps({
            'column_id': self.backlog.id,
            'task_orders': [
                {'id': task3.id, 'order': 1},
                {'id': task1.id, 'order': 2},
                {'id': task2.id, 'order': 3},
            ]
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify new order (tasks should be renumbered globally)
        task1.refresh_from_db()
        task2.refresh_from_db()
        task3.refresh_from_db()
        
        # Task3 should now be first in order
        self.assertLess(task3.order, task1.order)
        self.assertLess(task3.order, task2.order)
    
    def test_global_order_persists_across_columns(self):
        """Test that task order persists when moving between columns."""
        # Create tasks with specific global order
        task1 = Task.objects.create(title='High Priority', column=self.backlog, order=1)
        task2 = Task.objects.create(title='Medium Priority', column=self.backlog, order=2)
        task3 = Task.objects.create(title='Low Priority', column=self.in_progress, order=3)
        
        # Move task1 to in_progress - order should persist
        response = self.client.post(reverse('move_task'), data=json.dumps({
            'task_id': task1.id,
            'column_id': self.in_progress.id
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        task1.refresh_from_db()
        self.assertEqual(task1.column, self.in_progress)
        self.assertEqual(task1.order, 1)  # Order should remain 1
        
        # task1 should still be displayed before task3 in the same column
        in_progress_tasks = list(self.in_progress.tasks.all())
        self.assertEqual(in_progress_tasks[0], task1)  # task1 first (order=1)
        self.assertEqual(in_progress_tasks[1], task3)  # task3 second (order=3)
    
    def test_edit_task_title_and_description(self):
        """Test editing a task's title and description."""
        task = Task.objects.create(
            title='Original Title',
            description='Original description',
            column=self.backlog,
            order=1
        )
        
        response = self.client.post(reverse('edit_task', args=[task.id]), data=json.dumps({
            'title': 'Updated Title',
            'description': 'Updated description'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated Title')
        self.assertEqual(task.description, 'Updated description')
    
    def test_edit_task_requires_title(self):
        """Test that editing a task still requires a title."""
        task = Task.objects.create(
            title='Original Title',
            column=self.backlog,
            order=1
        )
        
        response = self.client.post(reverse('edit_task', args=[task.id]), data=json.dumps({
            'title': '',
            'description': 'Some description'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        task.refresh_from_db()
        self.assertEqual(task.title, 'Original Title')  # Unchanged
    
    def test_edit_task_returns_updated_data(self):
        """Test that edit endpoint returns the updated task data."""
        task = Task.objects.create(
            title='Original',
            description='',
            column=self.backlog,
            order=1
        )
        
        response = self.client.post(reverse('edit_task', args=[task.id]), data=json.dumps({
            'title': 'New Title',
            'description': 'New description'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['task']['title'], 'New Title')
        self.assertEqual(data['task']['description'], 'New description')


class KanbanBoardViewTests(TestCase):
    """Tests for the board view with dynamic columns."""
    
    def setUp(self):
        """Create test columns."""
        Column.objects.all().delete()
        self.col1 = Column.objects.create(name='Backlog', order=1)
        self.col2 = Column.objects.create(name='Done', order=2)
    
    def test_board_renders(self):
        """Test that the board page renders successfully."""
        response = self.client.get(reverse('kanban_board'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ADHD Kanban Organizer')
    
    def test_board_displays_all_columns(self):
        """Test that all columns are displayed on the board."""
        response = self.client.get(reverse('kanban_board'))
        self.assertContains(response, 'Backlog')
        self.assertContains(response, 'Done')
    
    def test_add_task_requires_title(self):
        """Test that creating a task without title fails."""
        initial_count = Task.objects.count()
        
        response = self.client.post(reverse('add_task'), data={
            'title': '',
            'column_id': self.col1.id,
        }, follow=True)
        
        self.assertEqual(Task.objects.count(), initial_count)
    
    def test_add_task_defaults_to_first_column(self):
        """Test that tasks default to first column if no column specified."""
        response = self.client.post(reverse('add_task'), data={
            'title': 'Default Column Task',
        }, follow=True)
        
        task = Task.objects.get(title='Default Column Task')
        self.assertEqual(task.column, self.col1)  # First column by order
    
    def test_board_shows_column_management_controls(self):
        """Test that column management controls are present."""
        response = self.client.get(reverse('kanban_board'))
        # Should have add column button
        self.assertContains(response, 'Add Column')
        # Should have delete buttons for columns
        self.assertContains(response, 'delete-column')
    
    def test_board_shows_max_12_columns_warning(self):
        """Test warning appears when at max columns."""
        # Create 10 more columns (we have 2)
        for i in range(3, 13):
            Column.objects.create(name=f'Column {i}', order=i)
        
        response = self.client.get(reverse('kanban_board'))
        # Should show we're at max
        self.assertEqual(Column.objects.count(), 12)
