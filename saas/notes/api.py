# notes/api.py
# REST API serializers and viewsets for the Notes Service.
# Source: Note & Document Implementation Specification V1
#
# Exports:
#   - NoteSerializer / NoteViewSet
#   - router (DefaultRouter with NoteViewSet registered)
#
# Design:
#   - Note has 25 nullable parent FKs (exclusive arc pattern)
#   - Serializer uses parent_entity (read-only) and parent_field/parent_id (write-only)
#   - create() override sets the correct FK based on parent_field/parent_id

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet
from .models import Note, NoteType


# ==============================================================================
# Parent FK Field Mapping
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

class NoteSerializer(TenantModelSerializer):
    """
    Serializer for Note (TenantModel with exclusive arc pattern).

    Attributes:
        parent_entity: SerializerMethodField (read-only) returning {"type": "customer", "id": "uuid"}
        parent_field: CharField (write-only) — field name indicating parent type (e.g., 'customer')
        parent_id: UUIDField (write-only) — ID of the parent entity
    """

    parent_entity = serializers.SerializerMethodField(read_only=True)
    parent_field = serializers.CharField(write_only=True, required=False, allow_blank=True)
    parent_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Note
        fields = TenantModelSerializer.Meta.fields + [
            'note_type',
            'body',
            'parent_entity',
            'parent_field',
            'parent_id',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + ['parent_entity']

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
                'parent_field and parent_id are required when creating a Note.'
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


# ==============================================================================
# ViewSets
# ==============================================================================

class NoteViewSet(TenantModelViewSet):
    """
    ViewSet for Note.
    Supports full CRUD with tenant scoping and filtering by note type and parent entity.
    """

    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    filterset_fields = ['note_type']
    search_fields = ['body']
    ordering_fields = ['note_type', 'created_on', 'updated_on']


# ==============================================================================
# Router
# ==============================================================================

router = DefaultRouter()
router.register(r'notes', NoteViewSet, basename='note')
