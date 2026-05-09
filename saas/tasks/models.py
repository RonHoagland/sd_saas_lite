# tasks/models.py
# Source: Data Models V6, Sections 1.4, 1.6.
#
# Models in this app:
#   Task, AssociatedTask, TaskTime, TaskToDo, TimeEntry
#
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

from django.db import models
from config.base_models import TenantModel
from numbering.mixins import NumberingMixin
from lifecycle.mixins import LifecycleMixin


class Task(TenantModel, NumberingMixin, LifecycleMixin):
    """
    A discrete task that may be linked to a WorkOrder, ServiceRequest, or stand-alone.
    Source: Data Models V6, Sections 1.4, 1.6.
    """
    numbering_entity_type = 'task'
    lifecycle_entity_type = 'task'

    class StatusChoices(models.TextChoices):
        NOT_STARTED = 'Not Started', 'Not Started'
        IN_PROGRESS = 'In Progress', 'In Progress'
        ON_HOLD = 'On Hold', 'On Hold'
        COMPLETED = 'Completed', 'Completed'
        CANCELLED = 'Cancelled', 'Cancelled'

    class PriorityChoices(models.TextChoices):
        LOW = 'Low', 'Low'
        MEDIUM = 'Medium', 'Medium'
        HIGH = 'High', 'High'
        CRITICAL = 'Critical', 'Critical'

    task_number = models.CharField(max_length=20, blank=True)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=StatusChoices.choices,
                               default=StatusChoices.NOT_STARTED)
    priority = models.CharField(max_length=10, choices=PriorityChoices.choices,
                                 default=PriorityChoices.MEDIUM)
    assigned_to = models.ForeignKey('users.User', null=True, blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name='assigned_tasks')
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=8, decimal_places=2,
                                           null=True, blank=True)

    # Optional parent links — one of these may be set (exclusive arc).
    work_order = models.ForeignKey('service.WorkOrder', null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='tasks')
    service_request = models.ForeignKey('service.ServiceRequest', null=True, blank=True,
                                         on_delete=models.SET_NULL,
                                         related_name='tasks')

    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'tasks_task'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'assigned_to_id']),
        ]

    def __str__(self):
        return f'[{self.task_number}] {self.title}'


class AssociatedTask(TenantModel):
    """
    Links a Task to another Task as a dependency or related item.
    Source: Data Models V6, Section 1.6.
    """

    class RelationChoices(models.TextChoices):
        DEPENDS_ON = 'Depends On', 'Depends On'
        BLOCKS = 'Blocks', 'Blocks'
        RELATED = 'Related', 'Related'

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                              related_name='associated_tasks')
    related_task = models.ForeignKey(Task, on_delete=models.CASCADE,
                                      related_name='associated_by')
    relation = models.CharField(max_length=15, choices=RelationChoices.choices,
                                 default=RelationChoices.RELATED)

    class Meta:
        db_table = 'tasks_associatedtask'
        unique_together = [('task', 'related_task')]
        indexes = [
            models.Index(fields=['tenant_id', 'task_id']),
        ]

    def __str__(self):
        return f'{self.task} {self.relation} {self.related_task}'


class TaskTime(TenantModel):
    """
    Time logged directly against a Task (quick-entry; no TimeEntry detail).
    Source: Data Models V6, Section 1.6.
    """

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                              related_name='time_entries_quick')
    logged_by = models.ForeignKey('users.User', null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   related_name='task_time_entries')
    hours = models.DecimalField(max_digits=8, decimal_places=2)
    work_date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tasks_tasktime'
        indexes = [
            models.Index(fields=['tenant_id', 'task_id']),
        ]

    def __str__(self):
        return f'{self.task} — {self.hours}h ({self.work_date})'


class TaskToDo(TenantModel):
    """
    A checklist item (to-do) nested inside a Task.
    Source: Data Models V6, Section 1.6.
    """

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                              related_name='to_dos')
    title = models.CharField(max_length=300)
    is_completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey('users.User', null=True, blank=True,
                                      on_delete=models.SET_NULL,
                                      related_name='completed_to_dos')
    completed_date = models.DateField(null=True, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'tasks_tasktodo'
        ordering = ['sort_order']
        indexes = [
            models.Index(fields=['tenant_id', 'task_id']),
        ]

    def __str__(self):
        return f'{self.task} — {self.title}'


class TimeEntry(TenantModel):
    """
    Detailed time entry that may be linked to a Task, WorkOrder, or stand-alone.
    Source: Data Models V6, Section 1.6.
    """

    class BillableChoices(models.TextChoices):
        BILLABLE = 'Billable', 'Billable'
        NON_BILLABLE = 'Non-Billable', 'Non-Billable'

    logged_by = models.ForeignKey('users.User', null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   related_name='time_entries')
    work_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    hours = models.DecimalField(max_digits=8, decimal_places=2)
    billable = models.CharField(max_length=12, choices=BillableChoices.choices,
                                 default=BillableChoices.BILLABLE)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    # Optional parent links — one of these may be set (exclusive arc).
    task = models.ForeignKey(Task, null=True, blank=True,
                              on_delete=models.SET_NULL,
                              related_name='detailed_time_entries')
    work_order = models.ForeignKey('service.WorkOrder', null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='time_entries')

    class Meta:
        db_table = 'tasks_timeentry'
        indexes = [
            models.Index(fields=['tenant_id', 'logged_by_id']),
            models.Index(fields=['tenant_id', 'work_date']),
        ]

    def __str__(self):
        return f'{self.logged_by} — {self.hours}h ({self.work_date})'
