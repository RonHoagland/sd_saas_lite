# workforce/api.py
# REST API serializers and viewsets for workforce app models.
#
# Models:
#   WGDivision, WorkGroup, WGTRole, WorkGroupTeam, WorkGroupAsset,
#   Skill, EmployeeSkill

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet, TenantNoDeleteViewSet
from .models import (
    WGDivision, WorkGroup, WGTRole, WorkGroupTeam, WorkGroupAsset,
    Skill, EmployeeSkill
)


# ─── WGDivision ───────────────────────────────────────────────────────────────

class WGDivisionSerializer(TenantModelSerializer):

    class Meta:
        model = WGDivision
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'status',
            'description',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class WGDivisionViewSet(TenantModelViewSet):
    queryset = WGDivision.objects.all()
    serializer_class = WGDivisionSerializer
    filterset_fields = ['status']
    search_fields = ['name']
    ordering_fields = ['name', 'created_on', 'status']


# ─── WorkGroup ────────────────────────────────────────────────────────────────

class WorkGroupSerializer(TenantModelSerializer):
    division_display = serializers.CharField(source='division.name', read_only=True)
    manager_display = serializers.CharField(source='manager.email', read_only=True)

    class Meta:
        model = WorkGroup
        fields = TenantModelSerializer.Meta.fields + [
            'work_group_number',
            'name',
            'division',
            'division_display',
            'status',
            'description',
            'manager',
            'manager_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'work_group_number',
            'division_display',
            'manager_display',
        ]


class WorkGroupViewSet(TenantModelViewSet):
    queryset = WorkGroup.objects.all()
    serializer_class = WorkGroupSerializer
    filterset_fields = ['division_id', 'status', 'manager_id']
    search_fields = ['name', 'work_group_number']
    ordering_fields = ['name', 'created_on', 'status']


# ─── WGTRole ──────────────────────────────────────────────────────────────────

class WGTRoleSerializer(TenantModelSerializer):
    work_group_display = serializers.CharField(source='work_group.name', read_only=True)

    class Meta:
        model = WGTRole
        fields = TenantModelSerializer.Meta.fields + [
            'work_group',
            'work_group_display',
            'name',
            'description',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'work_group_display',
        ]


class WGTRoleViewSet(TenantModelViewSet):
    queryset = WGTRole.objects.all()
    serializer_class = WGTRoleSerializer
    filterset_fields = ['work_group_id']
    search_fields = ['name', 'work_group__name']
    ordering_fields = ['name', 'created_on']


# ─── WorkGroupTeam ────────────────────────────────────────────────────────────

class WorkGroupTeamSerializer(TenantModelSerializer):
    work_group_display = serializers.CharField(source='work_group.name', read_only=True)
    user_display = serializers.CharField(source='user.email', read_only=True)
    role_display = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = WorkGroupTeam
        fields = TenantModelSerializer.Meta.fields + [
            'work_group',
            'work_group_display',
            'user',
            'user_display',
            'role',
            'role_display',
            'is_lead',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'work_group_display',
            'user_display',
            'role_display',
        ]


class WorkGroupTeamViewSet(TenantModelViewSet):
    queryset = WorkGroupTeam.objects.all()
    serializer_class = WorkGroupTeamSerializer
    filterset_fields = ['work_group_id', 'user_id', 'role_id', 'is_lead']
    search_fields = ['work_group__name', 'user__email']
    ordering_fields = ['created_on']


# ─── WorkGroupAsset ───────────────────────────────────────────────────────────

class WorkGroupAssetSerializer(TenantModelSerializer):
    work_group_display = serializers.CharField(source='work_group.name', read_only=True)
    asset_display = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model = WorkGroupAsset
        fields = TenantModelSerializer.Meta.fields + [
            'work_group',
            'work_group_display',
            'asset',
            'asset_display',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'work_group_display',
            'asset_display',
        ]


class WorkGroupAssetViewSet(TenantModelViewSet):
    queryset = WorkGroupAsset.objects.all()
    serializer_class = WorkGroupAssetSerializer
    filterset_fields = ['work_group_id', 'asset_id']
    search_fields = ['work_group__name', 'asset__name']
    ordering_fields = ['created_on']


# ─── Skill ────────────────────────────────────────────────────────────────────

class SkillSerializer(TenantModelSerializer):

    class Meta:
        model = Skill
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'category',
            'status',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class SkillViewSet(TenantModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    filterset_fields = ['category', 'status']
    search_fields = ['name']
    ordering_fields = ['name', 'created_on', 'status']


# ─── EmployeeSkill ────────────────────────────────────────────────────────────

class EmployeeSkillSerializer(TenantModelSerializer):
    employee_display = serializers.CharField(source='employee.email', read_only=True)
    skill_display = serializers.CharField(source='skill.name', read_only=True)

    class Meta:
        model = EmployeeSkill
        fields = TenantModelSerializer.Meta.fields + [
            'employee',
            'employee_display',
            'skill',
            'skill_display',
            'date_earned',
            'expiration_date',
            'status',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'employee_display',
            'skill_display',
        ]


class EmployeeSkillViewSet(TenantModelViewSet):
    queryset = EmployeeSkill.objects.all()
    serializer_class = EmployeeSkillSerializer
    filterset_fields = ['employee_id', 'skill_id', 'status']
    search_fields = ['employee__email', 'skill__name']
    ordering_fields = ['date_earned', 'expiration_date', 'created_on', 'status']


# ─── Router ───────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register(r'wg-divisions', WGDivisionViewSet, basename='wg-division')
router.register(r'work-groups', WorkGroupViewSet, basename='work-group')
router.register(r'wgt-roles', WGTRoleViewSet, basename='wgt-role')
router.register(r'work-group-teams', WorkGroupTeamViewSet, basename='work-group-team')
router.register(r'work-group-assets', WorkGroupAssetViewSet, basename='work-group-asset')
router.register(r'skills', SkillViewSet, basename='skill')
router.register(r'employee-skills', EmployeeSkillViewSet, basename='employee-skill')
