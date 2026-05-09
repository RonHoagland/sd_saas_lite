# maintenance/api.py
# REST API serializers and viewsets for maintenance app models.
#
# Models:
#   Asset, SubAsset, Agreement, CustomerAgreement, PreventativeMaintenance

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet, TenantNoDeleteViewSet
from .models import Asset, SubAsset, Agreement, CustomerAgreement, PreventativeMaintenance


# ─── Asset ────────────────────────────────────────────────────────────────────

class AssetSerializer(TenantModelSerializer):
    customer_display = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Asset
        fields = TenantModelSerializer.Meta.fields + [
            'asset_number',
            'name',
            'customer',
            'customer_display',
            'status',
            'manufacturer',
            'model_number',
            'serial_number',
            'install_date',
            'warranty_expiration',
            'address',
            'notes',
            'tags',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'asset_number',
            'customer_display',
        ]


class AssetViewSet(TenantModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    filterset_fields = ['customer_id', 'status']
    search_fields = ['name', 'asset_number', 'manufacturer', 'serial_number']
    ordering_fields = ['name', 'created_on', 'status']


# ─── SubAsset ─────────────────────────────────────────────────────────────────

class SubAssetSerializer(TenantModelSerializer):
    asset_display = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model = SubAsset
        fields = TenantModelSerializer.Meta.fields + [
            'asset',
            'asset_display',
            'name',
            'status',
            'manufacturer',
            'model_number',
            'serial_number',
            'install_date',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'asset_display',
        ]


class SubAssetViewSet(TenantModelViewSet):
    queryset = SubAsset.objects.all()
    serializer_class = SubAssetSerializer
    filterset_fields = ['asset_id', 'status']
    search_fields = ['name', 'manufacturer', 'serial_number']
    ordering_fields = ['name', 'created_on', 'status']


# ─── Agreement ────────────────────────────────────────────────────────────────

class AgreementSerializer(TenantModelSerializer):

    class Meta:
        model = Agreement
        fields = TenantModelSerializer.Meta.fields + [
            'agreement_number',
            'name',
            'status',
            'description',
            'default_duration_months',
            'terms',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'agreement_number',
        ]


class AgreementViewSet(TenantModelViewSet):
    queryset = Agreement.objects.all()
    serializer_class = AgreementSerializer
    filterset_fields = ['status']
    search_fields = ['name', 'agreement_number']
    ordering_fields = ['name', 'created_on', 'status']


# ─── CustomerAgreement ────────────────────────────────────────────────────────

class CustomerAgreementSerializer(TenantModelSerializer):
    agreement_display = serializers.CharField(source='agreement.name', read_only=True)
    customer_display = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = CustomerAgreement
        fields = TenantModelSerializer.Meta.fields + [
            'agreement',
            'agreement_display',
            'customer',
            'customer_display',
            'status',
            'start_date',
            'end_date',
            'auto_renew',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'agreement_display',
            'customer_display',
        ]


class CustomerAgreementViewSet(TenantModelViewSet):
    queryset = CustomerAgreement.objects.all()
    serializer_class = CustomerAgreementSerializer
    filterset_fields = ['agreement_id', 'customer_id', 'status']
    search_fields = ['agreement__name', 'customer__name']
    ordering_fields = ['start_date', 'end_date', 'created_on', 'status']


# ─── PreventativeMaintenance ──────────────────────────────────────────────────

class PreventativeMaintenanceSerializer(TenantModelSerializer):
    asset_display = serializers.CharField(source='asset.name', read_only=True)
    assigned_to_display = serializers.CharField(source='assigned_to.email', read_only=True)

    class Meta:
        model = PreventativeMaintenance
        fields = TenantModelSerializer.Meta.fields + [
            'pm_number',
            'asset',
            'asset_display',
            'task_name',
            'description',
            'frequency',
            'status',
            'last_performed_date',
            'next_due_date',
            'assigned_to',
            'assigned_to_display',
            'estimated_hours',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'pm_number',
            'asset_display',
            'assigned_to_display',
        ]


class PreventativeMaintenanceViewSet(TenantModelViewSet):
    queryset = PreventativeMaintenance.objects.all()
    serializer_class = PreventativeMaintenanceSerializer
    filterset_fields = ['asset_id', 'frequency', 'status']
    search_fields = ['task_name', 'pm_number']
    ordering_fields = ['next_due_date', 'created_on', 'frequency']


# ─── Router ───────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'sub-assets', SubAssetViewSet, basename='sub-asset')
router.register(r'agreements', AgreementViewSet, basename='agreement')
router.register(r'customer-agreements', CustomerAgreementViewSet, basename='customer-agreement')
router.register(r'preventative-maintenance', PreventativeMaintenanceViewSet, basename='preventative-maintenance')
