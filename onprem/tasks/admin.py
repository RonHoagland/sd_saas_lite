# tasks/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from tasks.models import Task, AssociatedTask, TaskTime, TaskToDo, TimeEntry


@admin.register(Task)
class TaskAdmin(TenantModelAdmin):
    list_display = ('task_number', 'title', 'status', 'priority',
                    'assigned_to', 'due_date', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'priority')
    search_fields = ('task_number', 'title')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(AssociatedTask)
class AssociatedTaskAdmin(TenantModelAdmin):
    list_display = ('task', 'relation', 'related_task', 'tenant_id')
    list_filter = ('tenant_id', 'relation')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(TaskTime)
class TaskTimeAdmin(TenantModelAdmin):
    list_display = ('task', 'logged_by', 'hours', 'work_date', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('task__title', 'task__task_number')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(TaskToDo)
class TaskToDoAdmin(TenantModelAdmin):
    list_display = ('title', 'task', 'is_completed', 'completed_by',
                    'completed_date', 'sort_order', 'tenant_id')
    list_filter = ('tenant_id', 'is_completed')
    search_fields = ('title', 'task__title')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(TimeEntry)
class TimeEntryAdmin(TenantModelAdmin):
    list_display = ('logged_by', 'work_date', 'hours', 'billable',
                    'hourly_rate', 'task', 'work_order', 'tenant_id')
    list_filter = ('tenant_id', 'billable')
    search_fields = ('logged_by__email', 'notes')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
