# api/base.py
# Base serializer and viewset classes for all SDTA API endpoints.
# Source: Technical Architecture V2, Section 7; Internal API Specification V1.
#
# Design decisions:
#   - TenantModelSerializer auto-injects tenant_id and audit fields on create/update.
#   - TenantModelViewSet restricts queryset to the current tenant via TenantManager.
#   - All read endpoints include id, tenant_id, created_by, created_on, updated_by, updated_on.
#   - Audit fields (created_by/on, updated_by/on, tenant_id) are read-only in API input.
#
# Usage:
#   from api.base import TenantModelSerializer, TenantModelViewSet
#
#   class CustomerSerializer(TenantModelSerializer):
#       class Meta(TenantModelSerializer.Meta):
#           model = Customer
#           fields = TenantModelSerializer.Meta.fields + ['company_name', 'status']
#
#   class CustomerViewSet(TenantModelViewSet):
#       queryset = Customer.objects.all()
#       serializer_class = CustomerSerializer

from rest_framework import serializers, viewsets, mixins, status
from rest_framework.response import Response

from config.tenant_context import get_current_tenant_id


def _scope_to_current_tenant(qs):
    """Force a tenant_id filter on a queryset.

    Defence-in-depth for the API layer. Even if a viewset declares its
    `queryset` using `.all_objects` (which bypasses TenantManager), the
    HTTP layer must never return rows from a different tenant than the
    one the request is authenticated for.

    Returns an empty queryset when no tenant context is established —
    fail-safe (no rows) rather than fail-open (every row).
    """
    tenant_id = get_current_tenant_id()
    if tenant_id is None:
        return qs.none()
    return qs.filter(tenant_id=tenant_id)


# ═══════════════════════════════════════════════════════════════════════════════
# BASE SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class TenantModelSerializer(serializers.ModelSerializer):
    """
    Base serializer for all TenantModel subclasses.

    Automatically handles:
      - Read-only audit fields (id, tenant_id, created_by/on, updated_by/on).
      - Auto-injection of tenant_id and created_by/updated_by on create.
      - Auto-injection of updated_by on update.
      - Read-only ``status`` for models using ``LifecycleMixin`` — state
        changes must go through the ``transition`` action / lifecycle service.

    Subclasses extend Meta.fields with their model-specific fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model = getattr(self.Meta, 'model', None)
        if model is None or 'status' not in self.fields:
            return
        from lifecycle.mixins import LifecycleMixin
        try:
            if issubclass(model, LifecycleMixin):
                self.fields['status'].read_only = True
        except TypeError:
            pass

    class Meta:
        fields = [
            'id', 'tenant_id',
            'created_by', 'created_on',
            'updated_by', 'updated_on',
        ]
        read_only_fields = [
            'id', 'tenant_id',
            'created_by', 'created_on',
            'updated_by', 'updated_on',
        ]

    def create(self, validated_data):
        """Inject tenant_id and audit fields on create."""
        request = self.context.get('request')
        tenant_id = get_current_tenant_id()

        validated_data['tenant_id'] = tenant_id

        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user_display = getattr(request.user, 'email', str(request.user))
            validated_data.setdefault('created_by', user_display)
            validated_data.setdefault('updated_by', user_display)
        else:
            validated_data.setdefault('created_by', 'System')
            validated_data.setdefault('updated_by', 'System')

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Inject updated_by on update."""
        request = self.context.get('request')

        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user_display = getattr(request.user, 'email', str(request.user))
            validated_data['updated_by'] = user_display
        else:
            validated_data['updated_by'] = 'System'

        return super().update(instance, validated_data)


class ReadOnlyTenantSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for TenantModel subclasses.

    Used for nested representations and list views where writes
    are not needed. No create/update logic.
    """

    class Meta:
        fields = [
            'id', 'tenant_id',
            'created_by', 'created_on',
            'updated_by', 'updated_on',
        ]
        read_only_fields = fields


class ImmutableModelSerializer(serializers.ModelSerializer):
    """
    Serializer for immutable models (LifecycleTransitionAudit, FileDownloadLog, etc.).

    All fields are read-only. No create/update via API — these records
    are created internally by services.
    """

    class Meta:
        fields = ['id']

    def create(self, validated_data):
        raise serializers.ValidationError("This resource is immutable and cannot be created via API.")

    def update(self, instance, validated_data):
        raise serializers.ValidationError("This resource is immutable and cannot be modified.")


# ═══════════════════════════════════════════════════════════════════════════════
# BASE VIEWSETS
# ═══════════════════════════════════════════════════════════════════════════════

class TenantModelViewSet(viewsets.ModelViewSet):
    """
    Full CRUD ViewSet for TenantModel subclasses.

    Automatically:
      - Re-filters queryset to the current tenant on every request, even
        when the class `queryset` was declared with `.all_objects.all()`
        (defence-in-depth — see `_scope_to_current_tenant`).
      - Passes request context to serializer.
      - Supports search, ordering, and filtering via DRF filters.

    Subclasses must set:
      - queryset
      - serializer_class
      - Optionally: filterset_fields, search_fields, ordering_fields
    """
    throttle_scope = 'standard'

    def get_queryset(self):
        return _scope_to_current_tenant(super().get_queryset())

    def perform_create(self, serializer):
        """Save with request context for audit field injection."""
        serializer.save()

    def perform_update(self, serializer):
        """Save with request context for audit field injection."""
        serializer.save()


class ReadOnlyTenantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for TenantModel-aligned subclasses.

    Provides list and retrieve actions only. No create/update/delete.
    Used for audit logs, immutable records, and reference data.

    Re-filters queryset to the current tenant on every request — works
    for both TenantModel subclasses and standalone models that carry a
    `tenant_id` UUIDField (e.g. LifecycleTransitionAudit, FileDownloadLog).
    """
    throttle_scope = 'standard'

    def get_queryset(self):
        return _scope_to_current_tenant(super().get_queryset())


class TenantCreateReadViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Create + Read-only ViewSet (no update, no delete).

    Used for append-only models like upload logs. Tenant scoping enforced
    at every read.
    """
    throttle_scope = 'standard'

    def get_queryset(self):
        return _scope_to_current_tenant(super().get_queryset())


class TenantNoDeleteViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    CRUD without delete. Used for models where records should
    be deactivated rather than deleted. Tenant scoping enforced.
    """
    throttle_scope = 'standard'

    def get_queryset(self):
        return _scope_to_current_tenant(super().get_queryset())
