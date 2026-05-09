# lifecycle/api.py
# REST API serializers and viewsets for the Lifecycle Framework.
# Source: Lifecycle Framework Specification V1, Sections 1–3.
#
# Exports:
#   - LifecycleStateDefSerializer / LifecycleStateDefViewSet
#   - LifecycleTransitionRuleSerializer / LifecycleTransitionRuleViewSet
#   - LifecycleTransitionAuditSerializer / LifecycleTransitionAuditViewSet (read-only)
#   - router (DefaultRouter with all viewsets registered)

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import (
    TenantModelSerializer,
    TenantModelViewSet,
    ReadOnlyTenantViewSet,
)
from .models import LifecycleStateDef, LifecycleTransitionRule, LifecycleTransitionAudit


# ==============================================================================
# Serializers
# ==============================================================================

class LifecycleStateDefSerializer(TenantModelSerializer):
    """
    Serializer for LifecycleStateDef (TenantModel).
    Includes state definition fields with tenant scoping.
    """

    class Meta:
        model = LifecycleStateDef
        fields = TenantModelSerializer.Meta.fields + [
            'entity_type',
            'state_name',
            'state_label',
            'state_type',
            'is_default',
            'sort_order',
            'description',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class LifecycleTransitionRuleSerializer(TenantModelSerializer):
    """
    Serializer for LifecycleTransitionRule (TenantModel).
    Includes transition rule fields with validation and tenant scoping.
    """

    class Meta:
        model = LifecycleTransitionRule
        fields = TenantModelSerializer.Meta.fields + [
            'entity_type',
            'from_state',
            'to_state',
            'required_role',
            'requires_reason',
            'is_admin_override',
            'description',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class LifecycleTransitionAuditSerializer(serializers.ModelSerializer):
    """
    Serializer for LifecycleTransitionAudit (immutable, non-TenantModel).
    Uses raw UUID fields to preserve audit records even if tenant/user is deleted.
    Read-only — append-only audit log.
    """

    class Meta:
        model = LifecycleTransitionAudit
        fields = [
            'id',
            'tenant_id',
            'timestamp',
            'user_id',
            'user_display',
            'entity_type',
            'entity_id',
            'from_state',
            'to_state',
            'reason',
            'is_override',
            'ip_address',
        ]
        read_only_fields = [
            'id',
            'tenant_id',
            'timestamp',
            'user_id',
            'user_display',
            'entity_type',
            'entity_id',
            'from_state',
            'to_state',
            'reason',
            'is_override',
            'ip_address',
        ]


# ==============================================================================
# ViewSets
# ==============================================================================

class LifecycleStateDefViewSet(TenantModelViewSet):
    """
    ViewSet for LifecycleStateDef.
    Supports full CRUD with tenant scoping and filtering by entity type.
    """

    queryset = LifecycleStateDef.all_objects.all()
    serializer_class = LifecycleStateDefSerializer
    filterset_fields = ['entity_type', 'state_type', 'is_default']
    search_fields = ['entity_type', 'state_name', 'state_label', 'description']
    ordering_fields = ['entity_type', 'sort_order', 'created_on']


class LifecycleTransitionRuleViewSet(TenantModelViewSet):
    """
    ViewSet for LifecycleTransitionRule.
    Supports full CRUD with tenant scoping and filtering by entity/state.
    """

    queryset = LifecycleTransitionRule.all_objects.all()
    serializer_class = LifecycleTransitionRuleSerializer
    filterset_fields = ['entity_type', 'from_state', 'to_state', 'is_admin_override']
    search_fields = ['entity_type', 'from_state', 'to_state', 'description']
    ordering_fields = ['entity_type', 'from_state', 'to_state', 'created_on']


class LifecycleTransitionAuditViewSet(ReadOnlyTenantViewSet):
    """
    Read-only ViewSet for LifecycleTransitionAudit.
    Immutable audit log — only list and retrieve operations permitted.
    Queries are filtered by tenant_id from the request context.
    """

    queryset = LifecycleTransitionAudit.objects.all()
    serializer_class = LifecycleTransitionAuditSerializer
    filterset_fields = ['tenant_id', 'entity_type', 'entity_id', 'user_id', 'is_override']
    search_fields = ['entity_type', 'from_state', 'to_state', 'user_display', 'reason']
    ordering_fields = ['timestamp', 'entity_type', 'user_id']

    def get_queryset(self):
        """Filter audit records by tenant from request context."""
        queryset = super().get_queryset()
        tenant_id = self.request.user.tenant_id if self.request.user else None
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset


# ==============================================================================
# Router
# ==============================================================================

router = DefaultRouter()
router.register(r'lifecycle-states', LifecycleStateDefViewSet, basename='lifecyclestatedef')
router.register(r'lifecycle-transitions', LifecycleTransitionRuleViewSet, basename='lifecycletransitionrule')
router.register(r'lifecycle-audit', LifecycleTransitionAuditViewSet, basename='lifecycletransitionaudit')
