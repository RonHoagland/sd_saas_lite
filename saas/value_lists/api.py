# value_lists/api.py
# REST API serializers and viewsets for the Value Lists Service.
# Source: Top-Down Specifications V4, Pre-Code Audit §4.7 / Task 3.2.
#
# Exports:
#   - ValueListSerializer / ValueListViewSet
#   - ValueListItemSerializer / ValueListItemViewSet
#   - router (DefaultRouter with all viewsets registered)

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet
from .models import ValueList, ValueListItem


# ==============================================================================
# Serializers
# ==============================================================================

class ValueListItemSerializer(TenantModelSerializer):
    """
    Serializer for ValueListItem (TenantModel).
    Represents a single selectable option within a ValueList.
    """

    class Meta:
        model = ValueListItem
        fields = TenantModelSerializer.Meta.fields + [
            'value_list',
            'label',
            'value',
            'sort_order',
            'is_default',
            'is_active',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class ValueListSerializer(TenantModelSerializer):
    """
    Serializer for ValueList (TenantModel).
    Includes nested items for convenience in read operations.
    """

    items = ValueListItemSerializer(many=True, read_only=True)

    class Meta:
        model = ValueList
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'slug',
            'description',
            'is_system',
            'items',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + ['is_system']


# ==============================================================================
# ViewSets
# ==============================================================================

class ValueListViewSet(TenantModelViewSet):
    """
    ViewSet for ValueList.
    Supports full CRUD with tenant scoping. System lists cannot be deleted
    (enforced by model.delete()).
    """

    queryset = ValueList.objects.all()
    serializer_class = ValueListSerializer
    filterset_fields = ['is_system', 'slug']
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'slug', 'created_on']


class ValueListItemViewSet(TenantModelViewSet):
    """
    ViewSet for ValueListItem.
    Supports full CRUD with tenant scoping and filtering by parent ValueList.
    """

    queryset = ValueListItem.objects.all()
    serializer_class = ValueListItemSerializer
    filterset_fields = ['value_list', 'is_active', 'is_default']
    search_fields = ['label', 'value', 'value_list__name']
    ordering_fields = ['sort_order', 'label', 'is_active', 'created_on']


# ==============================================================================
# Router
# ==============================================================================

router = DefaultRouter()
router.register(r'value-lists', ValueListViewSet, basename='valuelist')
router.register(r'value-list-items', ValueListItemViewSet, basename='valuelistitem')
