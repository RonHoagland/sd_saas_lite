# numbering/api.py
# REST API serializers and viewsets for the Numbering Service.
# Source: Numbering Service Specification V1, Sections 2, 3.
#
# Exports:
#   - NumberingRuleSerializer / NumberingRuleViewSet
#   - NumberSequenceSerializer / NumberSequenceViewSet
#   - AssignedNumberSerializer / AssignedNumberViewSet (read-only)
#   - router (DefaultRouter with all viewsets registered)

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet, ReadOnlyTenantViewSet
from .models import NumberingRule, NumberSequence, AssignedNumber


# ==============================================================================
# Serializers
# ==============================================================================

class NumberingRuleSerializer(TenantModelSerializer):
    """
    Serializer for NumberingRule (TenantModel).
    Includes all fields from TenantModelSerializer plus numbering-specific fields.
    """

    class Meta:
        model = NumberingRule
        fields = TenantModelSerializer.Meta.fields + [
            'entity_type',
            'is_enabled',
            'prefix',
            'include_year',
            'year_format',
            'include_month',
            'sequence_length',
            'delimiter',
            'reset_behavior',
            'description',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class NumberSequenceSerializer(serializers.ModelSerializer):
    """
    Serializer for NumberSequence (plain ModelSerializer — NOT TenantModel).
    Includes rule FK and sequence tracking fields.
    """

    class Meta:
        model = NumberSequence
        fields = [
            'id',
            'rule',
            'current_value',
            'last_reset_date',
        ]
        read_only_fields = ['id']


class AssignedNumberSerializer(TenantModelSerializer):
    """
    Serializer for AssignedNumber (immutable TenantModel).
    Read-only — AssignedNumbers are created by the system and cannot be modified.
    """

    class Meta:
        model = AssignedNumber
        fields = TenantModelSerializer.Meta.fields + [
            'rule',
            'entity_type',
            'entity_id',
            'number',
            'assigned_at',
            'assigned_by',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'rule',
            'entity_type',
            'entity_id',
            'number',
            'assigned_at',
            'assigned_by',
        ]


# ==============================================================================
# ViewSets
# ==============================================================================

class NumberingRuleViewSet(TenantModelViewSet):
    """
    ViewSet for NumberingRule.
    Supports full CRUD operations with tenant scoping and filtering.
    """

    queryset = NumberingRule.all_objects.all()
    serializer_class = NumberingRuleSerializer
    filterset_fields = ['entity_type', 'is_enabled', 'reset_behavior']
    search_fields = ['entity_type', 'prefix', 'description']
    ordering_fields = ['entity_type', 'created_on', 'updated_on']


class NumberSequenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for NumberSequence (plain Django model).
    Supports full CRUD operations with filtering and search.
    """

    queryset = NumberSequence.objects.all()
    serializer_class = NumberSequenceSerializer
    filterset_fields = ['rule_id']
    search_fields = ['rule__entity_type']
    ordering_fields = ['current_value', 'last_reset_date']


class AssignedNumberViewSet(ReadOnlyTenantViewSet):
    """
    Read-only ViewSet for AssignedNumber.
    Immutable records — only list and retrieve operations permitted.
    """

    queryset = AssignedNumber.all_objects.all()
    serializer_class = AssignedNumberSerializer
    filterset_fields = ['entity_type', 'entity_id', 'rule_id']
    search_fields = ['number', 'entity_type', 'assigned_by']
    ordering_fields = ['assigned_at', 'entity_type', 'number']


# ==============================================================================
# Router
# ==============================================================================

router = DefaultRouter()
router.register(r'numbering-rules', NumberingRuleViewSet, basename='numberingrule')
router.register(r'number-sequences', NumberSequenceViewSet, basename='numbersequence')
router.register(r'assigned-numbers', AssignedNumberViewSet, basename='assignednumber')
