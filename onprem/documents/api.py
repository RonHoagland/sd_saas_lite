# documents/api.py
# REST API serializers and viewsets for the Documents Service.
# Source: Note & Document Implementation Specification V1
#
# Exports:
#   - DocumentSerializer / DocumentViewSet
#   - FileUploadLogSerializer / FileUploadLogViewSet
#   - FileDownloadLogSerializer / FileDownloadLogViewSet (read-only)
#   - router (DefaultRouter with all viewsets registered)
#
# Design:
#   - Document: TenantModel with exclusive arc pattern (25 parent FKs)
#     File metadata is immutable; only scan_status can be updated
#   - FileUploadLog: TenantModel audit log for upload operations
#   - FileDownloadLog: Immutable append-only audit log (raw fields, NOT TenantModel)

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import (
    TenantModelSerializer,
    TenantModelViewSet,
    ReadOnlyTenantViewSet,
)
from .models import Document, FileUploadLog, FileDownloadLog


# ==============================================================================
# Parent FK Field Mapping (25 parent FKs for exclusive arc pattern)
# ==============================================================================

PARENT_FIELD_TO_FK = {
    'customer': 'customer_id',
    'contact': 'contact_id',
    'lead': 'lead_id',
    'opportunity': 'opportunity_id',
    'quote': 'quote_id',
    'invoice': 'invoice_id',
    'work_order': 'work_order_id',
    'asset': 'asset_id',
    'service_request': 'service_request_id',
    'prev_maint': 'prev_maint_id',
    'workflow': 'workflow_id',
    'payment': 'payment_id',
    'user': 'user_id',
    'vendor': 'vendor_id',
    'purchase_order': 'purchase_order_id',
    'work_group': 'work_group_id',
    'task': 'task_id',
    'vehicle': 'vehicle_id',
    'warehouse': 'warehouse_id',
    'ledger': 'ledger_id',
    'requisition': 'requisition_id',
    'rma': 'rma_id',
    'equipment': 'equipment_id',
    'safety_form': 'safety_form_id',
    'vendor_bill': 'vendor_bill_id',
}


# ==============================================================================
# Serializers
# ==============================================================================

class DocumentSerializer(TenantModelSerializer):
    """
    Serializer for Document (TenantModel with exclusive arc pattern).

    Attributes:
        parent_entity: SerializerMethodField (read-only) returning {"type": "customer", "id": "uuid"}
        parent_field: CharField (write-only) — field name indicating parent type
        parent_id: UUIDField (write-only) — ID of the parent entity

    Immutability:
        File metadata fields (original_filename, file_key, file_size_bytes, mime_type, sha256_hash)
        are read-only after creation. Only scan_status can be updated.
    """

    parent_entity = serializers.SerializerMethodField(read_only=True)
    parent_field = serializers.CharField(write_only=True, required=False, allow_blank=True)
    parent_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Document
        fields = TenantModelSerializer.Meta.fields + [
            'original_filename',
            'file_key',
            'file_size_bytes',
            'mime_type',
            'sha256_hash',
            'scan_status',
            'parent_entity',
            'parent_field',
            'parent_id',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'original_filename',
            'file_key',
            'file_size_bytes',
            'mime_type',
            'sha256_hash',
        ]

    def get_parent_entity(self, obj):
        """
        Return the parent entity as {"type": "field_name", "id": "uuid"}.
        Scans all 25 parent FK fields to find the non-null one.
        """
        for field_name, fk_attr in PARENT_FIELD_TO_FK.items():
            value = getattr(obj, fk_attr, None)
            if value:
                return {
                    'type': field_name,
                    'id': str(value),
                }
        return None

    def create(self, validated_data):
        """
        Override create() to set the correct parent FK based on parent_field/parent_id.
        """
        parent_field = validated_data.pop('parent_field', None)
        parent_id = validated_data.pop('parent_id', None)

        if not parent_field or not parent_id:
            raise serializers.ValidationError(
                'parent_field and parent_id are required when creating a Document.'
            )

        if parent_field not in PARENT_FIELD_TO_FK:
            raise serializers.ValidationError(
                f'parent_field must be one of: {", ".join(PARENT_FIELD_TO_FK.keys())}'
            )

        # Set the FK field
        fk_attr = PARENT_FIELD_TO_FK[parent_field]
        validated_data[fk_attr] = parent_id

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Override update() to handle parent_field/parent_id changes.
        Clears all parent FKs and sets only the specified one.
        """
        parent_field = validated_data.pop('parent_field', None)
        parent_id = validated_data.pop('parent_id', None)

        # If parent info is provided, reset all parent FKs and set the new one
        if parent_field is not None or parent_id is not None:
            if not parent_field or not parent_id:
                raise serializers.ValidationError(
                    'Both parent_field and parent_id must be provided together.'
                )

            if parent_field not in PARENT_FIELD_TO_FK:
                raise serializers.ValidationError(
                    f'parent_field must be one of: {", ".join(PARENT_FIELD_TO_FK.keys())}'
                )

            # Clear all parent FKs
            for fk_attr in PARENT_FIELD_TO_FK.values():
                setattr(instance, fk_attr, None)

            # Set the new parent FK
            fk_attr = PARENT_FIELD_TO_FK[parent_field]
            setattr(instance, fk_attr, parent_id)

        return super().update(instance, validated_data)


class FileUploadLogSerializer(TenantModelSerializer):
    """
    Serializer for FileUploadLog (TenantModel audit log).
    Records the outcome of each upload attempt: success, failure, or rejection.
    """

    class Meta:
        model = FileUploadLog
        fields = TenantModelSerializer.Meta.fields + [
            'document',
            'entity_type',
            'entity_id',
            'original_filename',
            'file_size_bytes',
            'status',
            'failure_reason',
            'ip_address',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class FileDownloadLogSerializer(serializers.ModelSerializer):
    """
    Serializer for FileDownloadLog (immutable, non-TenantModel).
    Append-only audit log with raw UUID fields (no FK to tenant/user to preserve records).
    All fields are read-only; records cannot be created or modified via API.
    """

    class Meta:
        model = FileDownloadLog
        fields = [
            'id',
            'tenant_id',
            'timestamp',
            'user_id',
            'user_display',
            'document',
            'entity_type',
            'entity_id',
            'ip_address',
        ]
        read_only_fields = [
            'id',
            'tenant_id',
            'timestamp',
            'user_id',
            'user_display',
            'document',
            'entity_type',
            'entity_id',
            'ip_address',
        ]


# ==============================================================================
# ViewSets
# ==============================================================================

class DocumentViewSet(TenantModelViewSet):
    """
    ViewSet for Document.
    Supports full CRUD with tenant scoping. File metadata is immutable;
    only scan_status can be updated.
    """

    queryset = Document.all_objects.all()
    serializer_class = DocumentSerializer
    filterset_fields = ['scan_status']
    search_fields = ['original_filename', 'mime_type']
    ordering_fields = ['original_filename', 'scan_status', 'created_on', 'updated_on']


class FileUploadLogViewSet(TenantModelViewSet):
    """
    ViewSet for FileUploadLog.
    Supports full CRUD with tenant scoping and filtering by status/entity.
    """

    queryset = FileUploadLog.all_objects.all()
    serializer_class = FileUploadLogSerializer
    filterset_fields = ['status', 'entity_type']
    search_fields = ['original_filename', 'failure_reason']
    ordering_fields = ['status', 'created_on']


class FileDownloadLogViewSet(ReadOnlyTenantViewSet):
    """
    Read-only ViewSet for FileDownloadLog.
    Immutable append-only audit log — only list and retrieve operations permitted.
    Filters are applied by tenant_id from request context.
    """

    queryset = FileDownloadLog.objects.all()
    serializer_class = FileDownloadLogSerializer
    filterset_fields = ['tenant_id', 'user_id', 'entity_type']
    search_fields = ['user_display']
    ordering_fields = ['timestamp', 'user_id']

    def get_queryset(self):
        """Filter download logs by tenant from request context."""
        queryset = super().get_queryset()
        tenant_id = self.request.user.tenant_id if self.request.user else None
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset


# ==============================================================================
# Router
# ==============================================================================

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'file-upload-logs', FileUploadLogViewSet, basename='fileuploadlog')
router.register(r'file-download-logs', FileDownloadLogViewSet, basename='filedownloadlog')
