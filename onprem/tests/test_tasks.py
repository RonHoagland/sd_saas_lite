# tests/test_tasks.py
# CRUD and basic functionality tests for all models in the tasks app.

from datetime import date

from tests.base import SDTATestCase
from tasks.models import AssociatedTask, Task, TaskTime, TaskToDo, TimeEntry


# ─── Task ─────────────────────────────────────────────────────────────────────

class TaskTest(SDTATestCase):

    def test_create(self):
        task = Task.objects.create(title='Install New Thermostat')
        self.assertEqual(task.title, 'Install New Thermostat')
        self.assertEqual(task.status, 'Not Started')
        self.assertEqual(task.priority, 'Medium')

    def test_str(self):
        task = Task.objects.create(task_number='T-001', title='Str Task')
        result = str(task)
        self.assertIn('T-001', result)
        self.assertIn('Str Task', result)

    def test_read(self):
        task = Task.objects.create(title='Read Task')
        fetched = Task.objects.get(id=task.id)
        self.assertEqual(fetched.title, 'Read Task')

    def test_update_status(self):
        task = Task.objects.create(title='Status Task')
        task.status = 'In Progress'
        task.save()
        task.refresh_from_db()
        self.assertEqual(task.status, 'In Progress')

    def test_delete(self):
        task = Task.objects.create(title='Del Task')
        t_id = task.id
        task.delete()
        self.assertFalse(Task.objects.filter(id=t_id).exists())

    def test_status_choices(self):
        for status in ('Not Started', 'In Progress', 'On Hold', 'Completed', 'Cancelled'):
            t = Task.objects.create(title=f'Task {status}', status=status)
            t.refresh_from_db()
            self.assertEqual(t.status, status)
            t.delete()

    def test_priority_choices(self):
        for priority in ('Low', 'Medium', 'High', 'Critical'):
            t = Task.objects.create(title=f'Task {priority}', priority=priority)
            t.refresh_from_db()
            self.assertEqual(t.priority, priority)
            t.delete()

    def test_due_date_optional(self):
        task = Task.objects.create(title='No Due Date')
        self.assertIsNone(task.due_date)

    def test_due_date_set(self):
        due = date(2026, 12, 31)
        task = Task.objects.create(title='Due Date Task', due_date=due)
        task.refresh_from_db()
        self.assertEqual(task.due_date, due)

    def test_estimated_hours_optional(self):
        task = Task.objects.create(title='No Hours Task')
        self.assertIsNone(task.estimated_hours)

    def test_estimated_hours_set(self):
        task = Task.objects.create(title='Hours Task', estimated_hours='4.50')
        task.refresh_from_db()
        self.assertEqual(float(task.estimated_hours), 4.50)

    def test_tags_default_empty(self):
        task = Task.objects.create(title='Tags Task')
        self.assertEqual(task.tags, [])

    def test_assigned_to_optional(self):
        task = Task.objects.create(title='Unassigned Task')
        self.assertIsNone(task.assigned_to)

    def test_assigned_to_user(self):
        user = self.make_user(email='task_user@acme.com')
        task = Task.objects.create(title='Assigned Task', assigned_to=user)
        self.assertEqual(task.assigned_to.email, 'task_user@acme.com')

    def test_work_order_link_optional(self):
        task = Task.objects.create(title='No WO Task')
        self.assertIsNone(task.work_order)

    def test_work_order_link(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        task = Task.objects.create(title='WO Task', work_order=wo)
        task.refresh_from_db()
        self.assertEqual(task.work_order_id, wo.id)

    def test_service_request_link(self):
        customer = self.make_customer()
        sr = self.make_service_request(customer=customer)
        task = Task.objects.create(title='SR Task', service_request=sr)
        task.refresh_from_db()
        self.assertEqual(task.service_request_id, sr.id)


# ─── AssociatedTask ───────────────────────────────────────────────────────────

class AssociatedTaskTest(SDTATestCase):

    def _make_two_tasks(self):
        t1 = Task.objects.create(title='Task A')
        t2 = Task.objects.create(title='Task B')
        return t1, t2

    def test_create(self):
        t1, t2 = self._make_two_tasks()
        at = AssociatedTask.objects.create(task=t1, related_task=t2)
        self.assertEqual(at.relation, 'Related')

    def test_str(self):
        t1, t2 = self._make_two_tasks()
        at = AssociatedTask.objects.create(task=t1, related_task=t2, relation='Blocks')
        result = str(at)
        self.assertIn('Task A', result)
        self.assertIn('Task B', result)
        self.assertIn('Blocks', result)

    def test_relation_choices(self):
        t1 = Task.objects.create(title='Dep Task A')
        t2 = Task.objects.create(title='Dep Task B')
        t3 = Task.objects.create(title='Dep Task C')
        at1 = AssociatedTask.objects.create(task=t1, related_task=t2, relation='Depends On')
        at2 = AssociatedTask.objects.create(task=t1, related_task=t3, relation='Blocks')
        at1.refresh_from_db()
        at2.refresh_from_db()
        self.assertEqual(at1.relation, 'Depends On')
        self.assertEqual(at2.relation, 'Blocks')

    def test_unique_task_related_task(self):
        from django.db import IntegrityError
        t1, t2 = self._make_two_tasks()
        AssociatedTask.objects.create(task=t1, related_task=t2)
        with self.assertRaises(IntegrityError):
            AssociatedTask.objects.create(task=t1, related_task=t2, relation='Blocks')

    def test_delete(self):
        t1, t2 = self._make_two_tasks()
        at = AssociatedTask.objects.create(task=t1, related_task=t2)
        at_id = at.id
        at.delete()
        self.assertFalse(AssociatedTask.objects.filter(id=at_id).exists())

    def test_cascade_delete_with_task(self):
        """AssociatedTask deleted when parent Task is deleted."""
        t1, t2 = self._make_two_tasks()
        at = AssociatedTask.objects.create(task=t1, related_task=t2)
        at_id = at.id
        t1.delete()
        self.assertFalse(AssociatedTask.objects.filter(id=at_id).exists())


# ─── TaskTime ─────────────────────────────────────────────────────────────────

class TaskTimeTest(SDTATestCase):

    def test_create(self):
        task = Task.objects.create(title='TT Parent')
        tt = TaskTime.objects.create(
            task=task, hours='2.50', work_date=date.today()
        )
        self.assertEqual(float(tt.hours), 2.50)

    def test_str(self):
        task = Task.objects.create(task_number='T-TT', title='TT Str Task')
        tt = TaskTime.objects.create(
            task=task, hours='1.00', work_date=date(2026, 1, 15)
        )
        result = str(tt)
        self.assertIn('1.00', result)
        self.assertIn('2026-01-15', result)

    def test_logged_by_optional(self):
        task = Task.objects.create(title='No User TT')
        tt = TaskTime.objects.create(task=task, hours='1.00', work_date=date.today())
        self.assertIsNone(tt.logged_by)

    def test_logged_by_user(self):
        task = Task.objects.create(title='User TT')
        user = self.make_user(email='tt_user@acme.com')
        tt = TaskTime.objects.create(
            task=task, hours='3.00', work_date=date.today(), logged_by=user
        )
        self.assertEqual(tt.logged_by.email, 'tt_user@acme.com')

    def test_notes_optional(self):
        task = Task.objects.create(title='Notes TT')
        tt = TaskTime.objects.create(task=task, hours='1.00', work_date=date.today())
        self.assertEqual(tt.notes, '')

    def test_delete(self):
        task = Task.objects.create(title='Del TT')
        tt = TaskTime.objects.create(task=task, hours='1.00', work_date=date.today())
        tt_id = tt.id
        tt.delete()
        self.assertFalse(TaskTime.objects.filter(id=tt_id).exists())

    def test_cascade_delete_with_task(self):
        task = Task.objects.create(title='Cascade TT Task')
        tt = TaskTime.objects.create(task=task, hours='1.00', work_date=date.today())
        tt_id = tt.id
        task.delete()
        self.assertFalse(TaskTime.objects.filter(id=tt_id).exists())


# ─── TaskToDo ─────────────────────────────────────────────────────────────────

class TaskToDoTest(SDTATestCase):

    def test_create(self):
        task = Task.objects.create(title='ToDo Parent')
        todo = TaskToDo.objects.create(task=task, title='Check filters')
        self.assertEqual(todo.title, 'Check filters')
        self.assertFalse(todo.is_completed)
        self.assertEqual(todo.sort_order, 0)

    def test_str(self):
        task = Task.objects.create(task_number='T-TD', title='TD Task')
        todo = TaskToDo.objects.create(task=task, title='Verify wiring')
        result = str(todo)
        self.assertIn('TD Task', result)
        self.assertIn('Verify wiring', result)

    def test_mark_completed(self):
        task = Task.objects.create(title='Complete ToDo Task')
        todo = TaskToDo.objects.create(task=task, title='Step 1')
        todo.is_completed = True
        todo.completed_date = date.today()
        todo.save()
        todo.refresh_from_db()
        self.assertTrue(todo.is_completed)
        self.assertEqual(todo.completed_date, date.today())

    def test_completed_by_optional(self):
        task = Task.objects.create(title='No CB Task')
        todo = TaskToDo.objects.create(task=task, title='Uncompleted Item')
        self.assertIsNone(todo.completed_by)

    def test_sort_order(self):
        task = Task.objects.create(title='Sort Task')
        todo1 = TaskToDo.objects.create(task=task, title='First', sort_order=1)
        todo2 = TaskToDo.objects.create(task=task, title='Second', sort_order=2)
        todos = list(TaskToDo.objects.filter(task=task))
        self.assertEqual(todos[0].sort_order, 1)
        self.assertEqual(todos[1].sort_order, 2)

    def test_delete(self):
        task = Task.objects.create(title='Del ToDo Task')
        todo = TaskToDo.objects.create(task=task, title='Del Item')
        todo_id = todo.id
        todo.delete()
        self.assertFalse(TaskToDo.objects.filter(id=todo_id).exists())

    def test_cascade_delete_with_task(self):
        task = Task.objects.create(title='Cascade ToDo Task')
        todo = TaskToDo.objects.create(task=task, title='Cascade Item')
        todo_id = todo.id
        task.delete()
        self.assertFalse(TaskToDo.objects.filter(id=todo_id).exists())


# ─── TimeEntry ────────────────────────────────────────────────────────────────

class TimeEntryTest(SDTATestCase):

    def test_create(self):
        te = TimeEntry.objects.create(
            work_date=date.today(), hours='8.00'
        )
        self.assertEqual(float(te.hours), 8.00)
        self.assertEqual(te.billable, 'Billable')
        self.assertEqual(float(te.hourly_rate), 0.0)

    def test_str(self):
        user = self.make_user(email='te_user@acme.com')
        te = TimeEntry.objects.create(
            work_date=date(2026, 2, 10), hours='4.00', logged_by=user
        )
        result = str(te)
        self.assertIn('4.00', result)
        self.assertIn('2026-02-10', result)

    def test_billable_non_billable(self):
        te = TimeEntry.objects.create(
            work_date=date.today(), hours='2.00', billable='Non-Billable'
        )
        te.refresh_from_db()
        self.assertEqual(te.billable, 'Non-Billable')

    def test_hourly_rate(self):
        te = TimeEntry.objects.create(
            work_date=date.today(), hours='1.00', hourly_rate='75.00'
        )
        te.refresh_from_db()
        self.assertEqual(float(te.hourly_rate), 75.00)

    def test_logged_by_optional(self):
        te = TimeEntry.objects.create(work_date=date.today(), hours='1.00')
        self.assertIsNone(te.logged_by)

    def test_start_end_time_optional(self):
        te = TimeEntry.objects.create(work_date=date.today(), hours='1.00')
        self.assertIsNone(te.start_time)
        self.assertIsNone(te.end_time)

    def test_task_link_optional(self):
        te = TimeEntry.objects.create(work_date=date.today(), hours='1.00')
        self.assertIsNone(te.task)

    def test_task_link(self):
        task = Task.objects.create(title='TE Task')
        te = TimeEntry.objects.create(
            work_date=date.today(), hours='2.00', task=task
        )
        te.refresh_from_db()
        self.assertEqual(te.task_id, task.id)

    def test_work_order_link(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        te = TimeEntry.objects.create(
            work_date=date.today(), hours='3.00', work_order=wo
        )
        te.refresh_from_db()
        self.assertEqual(te.work_order_id, wo.id)

    def test_delete(self):
        te = TimeEntry.objects.create(work_date=date.today(), hours='1.00')
        te_id = te.id
        te.delete()
        self.assertFalse(TimeEntry.objects.filter(id=te_id).exists())
