# tasks/api.py
# REST API serializers and viewsets for tasks app models.
#
# Models:
#   Task, AssociatedTask, TaskTime, TaskToDo, TimeEntry

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet, TenantNoDeleteViewSet
from .models import Task, AssociatedTask, TaskTime, TaskToDo, TimeEntry


# ─── Task ─────────────────────────────────────────────────────────────────────

class TaskSerializer(TenantModelSerializer):
    assigned_to_display = serializers.CharField(source='assigned_to.email', read_only=True)
    work_order_display = serializers.CharField(source='work_order.id', read_only=True)
    service_request_display = serializers.CharField(source='service_request.id', read_only=True)

    class Meta:
        model = Task
        fields = TenantModelSerializer.Meta.fields + [
            'task_number',
            'title',
            'description',
            'status',
            'priority',
            'assigned_to',
            'assigned_to_display',
            'due_date',
            'completed_date',
            'estimated_hours',
            'work_order',
            'work_order_display',
            'service_request',
            'service_request_display',
            'tags',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'task_number',
            'assigned_to_display',
            'work_order_display',
            'service_request_display',
        ]


class TaskViewSet(TenantModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filterset_fields = ['status', 'priority', 'assigned_to_id', 'work_order_id', 'service_request_id']
    search_fields = ['title', 'task_number']
    ordering_fields = ['due_date', 'priority', 'created_on', 'status']


# ─── AssociatedTask ───────────────────────────────────────────────────────────

class AssociatedTaskSerializer(TenantModelSerializer):
    task_display = serializers.CharField(source='task.title', read_only=True)
    related_task_display = serializers.CharField(source='related_task.title', read_only=True)

    class Meta:
        model = AssociatedTask
        fields = TenantModelSerializer.Meta.fields + [
            'task',
            'task_display',
            'related_task',
            'related_task_display',
            'relation',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'task_display',
            'related_task_display',
        ]


class AssociatedTaskViewSet(TenantModelViewSet):
    queryset = AssociatedTask.objects.all()
    serializer_class = AssociatedTaskSerializer
    filterset_fields = ['task_id', 'relation']
    search_fields = ['task__title', 'related_task__title']
    ordering_fields = ['created_on']


# ─── TaskTime ─────────────────────────────────────────────────────────────────

class TaskTimeSerializer(TenantModelSerializer):
    task_display = serializers.CharField(source='task.title', read_only=True)
    logged_by_display = serializers.CharField(source='logged_by.email', read_only=True)

    class Meta:
        model = TaskTime
        fields = TenantModelSerializer.Meta.fields + [
            'task',
            'task_display',
            'logged_by',
            'logged_by_display',
            'hours',
            'work_date',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'task_display',
            'logged_by_display',
        ]


class TaskTimeViewSet(TenantModelViewSet):
    queryset = TaskTime.objects.all()
    serializer_class = TaskTimeSerializer
    filterset_fields = ['task_id', 'logged_by_id', 'work_date']
    search_fields = ['task__title']
    ordering_fields = ['work_date', 'created_on']


# ─── TaskToDo ─────────────────────────────────────────────────────────────────

class TaskToDoSerializer(TenantModelSerializer):
    task_display = serializers.CharField(source='task.title', read_only=True)
    completed_by_display = serializers.CharField(source='completed_by.email', read_only=True)

    class Meta:
        model = TaskToDo
        fields = TenantModelSerializer.Meta.fields + [
            'task',
            'task_display',
            'title',
            'is_completed',
            'completed_by',
            'completed_by_display',
            'completed_date',
            'sort_order',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'task_display',
            'completed_by_display',
        ]


class TaskToDoViewSet(TenantModelViewSet):
    queryset = TaskToDo.objects.all()
    serializer_class = TaskToDoSerializer
    filterset_fields = ['task_id', 'is_completed']
    search_fields = ['title', 'task__title']
    ordering_fields = ['sort_order', 'created_on']


# ─── TimeEntry ────────────────────────────────────────────────────────────────

class TimeEntrySerializer(TenantModelSerializer):
    logged_by_display = serializers.CharField(source='logged_by.email', read_only=True)
    task_display = serializers.CharField(source='task.title', read_only=True)
    work_order_display = serializers.CharField(source='work_order.id', read_only=True)

    class Meta:
        model = TimeEntry
        fields = TenantModelSerializer.Meta.fields + [
            'logged_by',
            'logged_by_display',
            'work_date',
            'start_time',
            'end_time',
            'hours',
            'billable',
            'hourly_rate',
            'notes',
            'task',
            'task_display',
            'work_order',
            'work_order_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'logged_by_display',
            'task_display',
            'work_order_display',
        ]


class TimeEntryViewSet(TenantModelViewSet):
    queryset = TimeEntry.objects.all()
    serializer_class = TimeEntrySerializer
    filterset_fields = ['logged_by_id', 'work_date', 'billable', 'task_id', 'work_order_id']
    search_fields = ['task__title', 'work_order__id']
    ordering_fields = ['work_date', 'created_on']


# ─── Router ───────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'associated-tasks', AssociatedTaskViewSet, basename='associated-task')
router.register(r'task-time', TaskTimeViewSet, basename='task-time')
router.register(r'task-todos', TaskToDoViewSet, basename='task-todo')
router.register(r'time-entries', TimeEntryViewSet, basename='time-entry')
