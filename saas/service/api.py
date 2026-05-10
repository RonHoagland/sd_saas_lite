# service/api.py
# REST API serializers and viewsets for Service models.
# Source: Data Models V6, Sections 1.4, 1.5, 2.6.

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers, viewsets, status
from rest_framework.routers import DefaultRouter
from lifecycle.services import execute_transition, get_available_transitions
from api.permissions import IsTenantAdmin, IsTenantUser
from .services import (
    convert_service_request_to_work_order,
    convert_service_request_to_quote,
    convert_quote_to_invoice,
    convert_quote_to_work_order,
    convert_work_order_to_invoice
)
from api.base import (
    TenantModelSerializer,
    TenantModelViewSet,
    ReadOnlyTenantViewSet,
    TenantNoDeleteViewSet,
)
from .models import (
    ServiceRequest,
    WorkOrder,
    WorkOrderTeam,
    WorkOrderLine,
    Quote,
    QuoteLine,
    QuoteAsset,
    Invoice,
    InvoiceLine,
    InvoiceAsset,
    WorkOrderInvoice,
    Bank,
    Payments,
    Accounting,
    Ledger,
)


# ---------------------------------------------------------------------------
# Service Request Serializers & ViewSets
# ---------------------------------------------------------------------------

class ServiceRequestSerializer(TenantModelSerializer):
    """Serializer for ServiceRequest model."""

    customer_name = serializers.CharField(
        source='customer.company_name',
        read_only=True,
    )
    contact_name = serializers.CharField(
        source='contact.person.__str__',
        read_only=True,
        allow_null=True,
    )
    asset_name = serializers.CharField(
        source='asset.__str__',
        read_only=True,
        allow_null=True,
    )
    assigned_to_username = serializers.CharField(
        source='assigned_to.username',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = ServiceRequest
        fields = TenantModelSerializer.Meta.fields + [
            'request_number',
            'customer',
            'customer_name',
            'contact',
            'contact_name',
            'asset',
            'asset_name',
            'status',
            'priority',
            'subject',
            'description',
            'requested_date',
            'resolved_date',
            'assigned_to',
            'assigned_to_username',
            'tags',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'request_number',
            'customer_name',
            'contact_name',
            'asset_name',
            'assigned_to_username',
        ]


class ServiceRequestViewSet(TenantModelViewSet):
    """ViewSet for ServiceRequest CRUD operations."""

    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ['status', 'priority', 'customer_id', 'assigned_to_id']
    search_fields = ['request_number', 'subject', 'description', 'customer__company_name']
    ordering_fields = ['created_on', 'request_number', 'status', 'priority', 'requested_date']

    @action(detail=True, methods=['post'], url_path='convert-to-quote')
    def convert_to_quote(self, request, pk=None):
        """Action to convert a ServiceRequest to a Quote."""
        service_request = self.get_object()
        quote = convert_service_request_to_quote(service_request)
        return Response({'quote_id': quote.id, 'quote_number': quote.quote_number},
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='convert-to-work-order')
    def convert_to_work_order(self, request, pk=None):
        """Action to convert a ServiceRequest to a WorkOrder."""
        service_request = self.get_object()
        work_order = convert_service_request_to_work_order(service_request)
        return Response({'work_order_id': work_order.id, 'wo_number': work_order.wo_number},
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        """Execute a lifecycle transition."""
        entity = self.get_object()
        to_state = request.data.get('to_state')
        reason = request.data.get('reason', '')
        execute_transition(entity, to_state, request.user, reason=reason)
        return Response({'status': entity.status})

    @action(detail=True, methods=['get'], url_path='available-transitions')
    def available_transitions(self, request, pk=None):
        """Get available lifecycle transitions for this entity."""
        entity = self.get_object()
        transitions = get_available_transitions(entity, request.user)
        return Response(transitions)


# ---------------------------------------------------------------------------
# Work Order Line Serializers & ViewSets
# ---------------------------------------------------------------------------

class WorkOrderLineSerializer(TenantModelSerializer):
    """Serializer for WorkOrderLine model."""

    product_name = serializers.CharField(
        source='product.__str__',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = WorkOrderLine
        fields = TenantModelSerializer.Meta.fields + [
            'work_order',
            'line_type',
            'product',
            'product_name',
            'description',
            'quantity',
            'unit_price',
            'line_total',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'product_name',
        ]


class WorkOrderLineViewSet(TenantModelViewSet):
    """ViewSet for WorkOrderLine CRUD operations."""

    queryset = WorkOrderLine.objects.all()
    serializer_class = WorkOrderLineSerializer
    filterset_fields = ['line_type', 'work_order_id', 'product_id']
    search_fields = ['description', 'product__name']
    ordering_fields = ['created_on', 'line_type']


# ---------------------------------------------------------------------------
# Work Order Serializers & ViewSets
# ---------------------------------------------------------------------------

class WorkOrderTeamSerializer(TenantModelSerializer):
    """Nested serializer for WorkOrderTeam."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True,
    )
    user_username = serializers.CharField(
        source='user.username',
        read_only=True,
    )

    class Meta:
        model = WorkOrderTeam
        fields = TenantModelSerializer.Meta.fields + [
            'work_order',
            'user',
            'user_name',
            'user_username',
            'role',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'user_name',
            'user_username',
        ]


class WorkOrderTeamViewSet(TenantModelViewSet):
    """ViewSet for WorkOrderTeam CRUD operations."""

    queryset = WorkOrderTeam.objects.all()
    serializer_class = WorkOrderTeamSerializer
    filterset_fields = ['work_order_id', 'user_id']
    search_fields = ['user__first_name', 'user__last_name', 'role']
    ordering_fields = ['created_on', 'role']


class WorkOrderSerializer(TenantModelSerializer):
    """Serializer for WorkOrder model."""

    customer_name = serializers.CharField(
        source='customer.company_name',
        read_only=True,
    )
    service_request_number = serializers.CharField(
        source='service_request.request_number',
        read_only=True,
        allow_null=True,
    )
    asset_name = serializers.CharField(
        source='asset.__str__',
        read_only=True,
        allow_null=True,
    )
    assigned_to_username = serializers.CharField(
        source='assigned_to.username',
        read_only=True,
        allow_null=True,
    )
    # Nested collections for read operations
    lines = WorkOrderLineSerializer(
        many=True,
        read_only=True,
    )
    team_members = WorkOrderTeamSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = WorkOrder
        fields = TenantModelSerializer.Meta.fields + [
            'wo_number',
            'service_request',
            'service_request_number',
            'customer',
            'customer_name',
            'asset',
            'asset_name',
            'status',
            'priority',
            'subject',
            'description',
            'scheduled_date',
            'scheduled_time',
            'completed_date',
            'assigned_to',
            'assigned_to_username',
            'estimated_hours',
            'actual_hours',
            'tags',
            'hold_date',
            'hold_reason',
            'customer_facing_notes',
            'recurrence_pattern',
            'lines',
            'team_members',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'wo_number',
            'service_request_number',
            'customer_name',
            'asset_name',
            'assigned_to_username',
            'lines',
            'team_members',
        ]


class WorkOrderViewSet(TenantModelViewSet):
    """ViewSet for WorkOrder CRUD operations."""

    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ['status', 'priority', 'customer_id', 'assigned_to_id', 'service_request_id']
    search_fields = ['wo_number', 'subject', 'description', 'customer__company_name']
    ordering_fields = ['created_on', 'wo_number', 'status', 'priority', 'scheduled_date']

    @action(detail=True, methods=['post'], url_path='convert-to-invoice')
    def convert_to_invoice(self, request, pk=None):
        """Action to convert a WorkOrder to an Invoice."""
        work_order = self.get_object()
        invoice = convert_work_order_to_invoice(work_order)
        return Response({'invoice_id': invoice.id, 'invoice_number': invoice.invoice_number},
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        """Execute a lifecycle transition."""
        entity = self.get_object()
        to_state = request.data.get('to_state')
        reason = request.data.get('reason', '')
        execute_transition(entity, to_state, request.user, reason=reason)
        return Response({'status': entity.status})

    @action(detail=True, methods=['get'], url_path='available-transitions')
    def available_transitions(self, request, pk=None):
        """Get available lifecycle transitions for this entity."""
        entity = self.get_object()
        transitions = get_available_transitions(entity, request.user)
        return Response(transitions)


# ---------------------------------------------------------------------------
# Quote Line Serializers & ViewSets
# ---------------------------------------------------------------------------

class QuoteLineSerializer(TenantModelSerializer):
    """Serializer for QuoteLine model."""

    product_name = serializers.CharField(
        source='product.__str__',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = QuoteLine
        fields = TenantModelSerializer.Meta.fields + [
            'quote',
            'line_type',
            'product',
            'product_name',
            'description',
            'quantity',
            'unit_price',
            'line_total',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'product_name',
        ]


class QuoteLineViewSet(TenantModelViewSet):
    """ViewSet for QuoteLine CRUD operations."""

    queryset = QuoteLine.objects.all()
    serializer_class = QuoteLineSerializer
    filterset_fields = ['line_type', 'quote_id', 'product_id']
    search_fields = ['description', 'product__name']
    ordering_fields = ['created_on', 'line_type']


# ---------------------------------------------------------------------------
# Quote Asset Serializers & ViewSets
# ---------------------------------------------------------------------------

class QuoteAssetSerializer(TenantModelSerializer):
    """Serializer for QuoteAsset model."""

    asset_name = serializers.CharField(
        source='asset.__str__',
        read_only=True,
    )

    class Meta:
        model = QuoteAsset
        fields = TenantModelSerializer.Meta.fields + [
            'quote',
            'asset',
            'asset_name',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'asset_name',
        ]


class QuoteAssetViewSet(TenantModelViewSet):
    """ViewSet for QuoteAsset CRUD operations."""

    queryset = QuoteAsset.objects.all()
    serializer_class = QuoteAssetSerializer
    filterset_fields = ['quote_id', 'asset_id']
    search_fields = ['notes', 'asset__name']
    ordering_fields = ['created_on']


# ---------------------------------------------------------------------------
# Quote Serializers & ViewSets
# ---------------------------------------------------------------------------

class QuoteSerializer(TenantModelSerializer):
    """Serializer for Quote model."""

    customer_name = serializers.CharField(
        source='customer.company_name',
        read_only=True,
    )
    work_order_number = serializers.CharField(
        source='work_order.wo_number',
        read_only=True,
        allow_null=True,
    )
    # Nested collections for read operations
    lines = QuoteLineSerializer(
        many=True,
        read_only=True,
    )
    assets = QuoteAssetSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Quote
        fields = TenantModelSerializer.Meta.fields + [
            'quote_number',
            'work_order',
            'work_order_number',
            'customer',
            'customer_name',
            'status',
            'quote_date',
            'expiration_date',
            'notes',
            'subtotal',
            'tax_rate',
            'tax_amount',
            'total',
            'sent_at',
            'accepted_at',
            'declined_at',
            'declined_reason',
            'expired_at',
            'invoiced_at',
            'lines',
            'assets',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'quote_number',
            'work_order_number',
            'customer_name',
            'lines',
            'assets',
            # Lifecycle-managed denormalized fields.
            'sent_at', 'accepted_at', 'declined_at', 'declined_reason',
            'expired_at', 'invoiced_at',
        ]


class QuoteViewSet(TenantModelViewSet):
    """ViewSet for Quote CRUD operations."""

    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ['status', 'customer_id', 'work_order_id']
    search_fields = ['quote_number', 'notes', 'customer__company_name']
    ordering_fields = ['created_on', 'quote_number', 'status', 'quote_date', 'expiration_date']

    @action(detail=True, methods=['post'], url_path='convert-to-invoice')
    def convert_to_invoice(self, request, pk=None):
        """Action to convert an Accepted Quote to an Invoice."""
        quote = self.get_object()
        invoice = convert_quote_to_invoice(quote)
        return Response({'invoice_id': invoice.id, 'invoice_number': invoice.invoice_number},
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='convert-to-work-order')
    def convert_to_work_order(self, request, pk=None):
        """Action to convert an Accepted Quote to a WorkOrder."""
        quote = self.get_object()
        work_order = convert_quote_to_work_order(quote)
        return Response({'work_order_id': work_order.id, 'wo_number': work_order.wo_number},
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        """Execute a lifecycle transition."""
        entity = self.get_object()
        to_state = request.data.get('to_state')
        reason = request.data.get('reason', '')
        execute_transition(entity, to_state, request.user, reason=reason)
        return Response({'status': entity.status})

    @action(detail=True, methods=['get'], url_path='available-transitions')
    def available_transitions(self, request, pk=None):
        """Get available lifecycle transitions for this entity."""
        entity = self.get_object()
        transitions = get_available_transitions(entity, request.user)
        return Response(transitions)


# ---------------------------------------------------------------------------
# Invoice Line Serializers & ViewSets
# ---------------------------------------------------------------------------

class InvoiceLineSerializer(TenantModelSerializer):
    """Serializer for InvoiceLine model."""

    product_name = serializers.CharField(
        source='product.__str__',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = InvoiceLine
        fields = TenantModelSerializer.Meta.fields + [
            'invoice',
            'line_type',
            'product',
            'product_name',
            'description',
            'quantity',
            'unit_price',
            'line_total',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'product_name',
        ]


class InvoiceLineViewSet(TenantModelViewSet):
    """ViewSet for InvoiceLine CRUD operations."""

    queryset = InvoiceLine.objects.all()
    serializer_class = InvoiceLineSerializer
    filterset_fields = ['line_type', 'invoice_id', 'product_id']
    search_fields = ['description', 'product__name']
    ordering_fields = ['created_on', 'line_type']


# ---------------------------------------------------------------------------
# Invoice Asset Serializers & ViewSets
# ---------------------------------------------------------------------------

class InvoiceAssetSerializer(TenantModelSerializer):
    """Serializer for InvoiceAsset model."""

    asset_name = serializers.CharField(
        source='asset.__str__',
        read_only=True,
    )

    class Meta:
        model = InvoiceAsset
        fields = TenantModelSerializer.Meta.fields + [
            'invoice',
            'asset',
            'asset_name',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'asset_name',
        ]


class InvoiceAssetViewSet(TenantModelViewSet):
    """ViewSet for InvoiceAsset CRUD operations."""

    queryset = InvoiceAsset.objects.all()
    serializer_class = InvoiceAssetSerializer
    filterset_fields = ['invoice_id', 'asset_id']
    search_fields = ['notes', 'asset__name']
    ordering_fields = ['created_on']


# ---------------------------------------------------------------------------
# Work Order Invoice Serializers & ViewSets
# ---------------------------------------------------------------------------

class WorkOrderInvoiceSerializer(TenantModelSerializer):
    """Serializer for WorkOrderInvoice junction model."""

    work_order_number = serializers.CharField(
        source='work_order.wo_number',
        read_only=True,
    )
    invoice_number = serializers.CharField(
        source='invoice.invoice_number',
        read_only=True,
    )

    class Meta:
        model = WorkOrderInvoice
        fields = TenantModelSerializer.Meta.fields + [
            'work_order',
            'work_order_number',
            'invoice',
            'invoice_number',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'work_order_number',
            'invoice_number',
        ]


class WorkOrderInvoiceViewSet(TenantModelViewSet):
    """ViewSet for WorkOrderInvoice M2M operations."""

    queryset = WorkOrderInvoice.objects.all()
    serializer_class = WorkOrderInvoiceSerializer
    filterset_fields = ['work_order_id', 'invoice_id']
    search_fields = ['work_order__wo_number', 'invoice__invoice_number']
    ordering_fields = ['created_on']


# ---------------------------------------------------------------------------
# Invoice Serializers & ViewSets
# ---------------------------------------------------------------------------

class InvoiceSerializer(TenantModelSerializer):
    """Serializer for Invoice model."""

    customer_name = serializers.CharField(
        source='customer.company_name',
        read_only=True,
    )
    # Nested collections for read operations
    lines = InvoiceLineSerializer(
        many=True,
        read_only=True,
    )
    assets = InvoiceAssetSerializer(
        many=True,
        read_only=True,
    )
    work_order_invoices = WorkOrderInvoiceSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Invoice
        fields = TenantModelSerializer.Meta.fields + [
            'invoice_number',
            'customer',
            'customer_name',
            'status',
            'invoice_date',
            'due_date',
            'notes',
            'subtotal',
            'tax_rate',
            'tax_amount',
            'total',
            'amount_paid',
            'balance_due',
            'stripe_payment_link_url',
            'deposit_applied',
            'deposit_type',
            'deposit_amount',
            'is_recurring',
            'recurrence_pattern',
            'sent_at',
            'paid_at',
            'overdue_at',
            'voided_at',
            'voided_reason',
            'lines',
            'assets',
            'work_order_invoices',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'invoice_number',
            'customer_name',
            'lines',
            'assets',
            'work_order_invoices',
            # Lifecycle-managed denormalized fields.
            'sent_at', 'paid_at', 'overdue_at', 'voided_at', 'voided_reason',
        ]


class InvoiceViewSet(TenantModelViewSet):
    """ViewSet for Invoice CRUD operations."""

    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ['status', 'customer_id', 'deposit_applied', 'is_recurring']
    search_fields = ['invoice_number', 'notes', 'customer__company_name']
    ordering_fields = ['created_on', 'invoice_number', 'status', 'invoice_date', 'due_date']

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        """Execute a lifecycle transition."""
        entity = self.get_object()
        to_state = request.data.get('to_state')
        reason = request.data.get('reason', '')
        execute_transition(entity, to_state, request.user, reason=reason)
        return Response({'status': entity.status})

    @action(detail=True, methods=['get'], url_path='available-transitions')
    def available_transitions(self, request, pk=None):
        """Get available lifecycle transitions for this entity."""
        entity = self.get_object()
        transitions = get_available_transitions(entity, request.user)
        return Response(transitions)


# ---------------------------------------------------------------------------
# Bank Serializers & ViewSets
# ---------------------------------------------------------------------------

class BankSerializer(TenantModelSerializer):
    """Serializer for Bank model."""

    class Meta:
        model = Bank
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'account_number_last4',
            'routing_number_last4',
            'status',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class BankViewSet(TenantModelViewSet):
    """ViewSet for Bank CRUD operations."""

    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    filterset_fields = ['status']
    search_fields = ['name', 'account_number_last4', 'routing_number_last4']
    ordering_fields = ['created_on', 'name', 'status']


# ---------------------------------------------------------------------------
# Payment Serializers & ViewSets
# ---------------------------------------------------------------------------

class PaymentsSerializer(TenantModelSerializer):
    """Serializer for Payments model."""

    invoice_number = serializers.CharField(
        source='invoice.invoice_number',
        read_only=True,
    )
    bank_name = serializers.CharField(
        source='bank.name',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Payments
        fields = TenantModelSerializer.Meta.fields + [
            'payment_number',
            'invoice',
            'invoice_number',
            'payment_date',
            'amount',
            'status',
            'method',
            'reference_number',
            'bank',
            'bank_name',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'payment_number',
            'invoice_number',
            'bank_name',
        ]


class PaymentsViewSet(TenantModelViewSet):
    """ViewSet for Payments CRUD operations."""

    queryset = Payments.objects.all()
    serializer_class = PaymentsSerializer
    filterset_fields = ['status', 'method', 'invoice_id', 'bank_id']
    search_fields = ['payment_number', 'reference_number', 'invoice__invoice_number']
    ordering_fields = ['created_on', 'payment_number', 'status', 'payment_date', 'amount']

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        """Execute a Payment lifecycle transition (e.g. Open → Applied,
        Processing → Returned)."""
        entity = self.get_object()
        to_state = request.data.get('to_state')
        reason = request.data.get('reason', '')
        execute_transition(entity, to_state, request.user, reason=reason)
        return Response({'status': entity.status})

    @action(detail=True, methods=['get'], url_path='available-transitions')
    def available_transitions(self, request, pk=None):
        """Return the set of valid next states for this Payment from its
        current state, given the requesting user's roles."""
        entity = self.get_object()
        transitions = get_available_transitions(entity, request.user)
        return Response(transitions)


# ---------------------------------------------------------------------------
# Accounting Serializers & ViewSets
# ---------------------------------------------------------------------------

class AccountingSerializer(TenantModelSerializer):
    """Serializer for Accounting (Chart of Accounts) model."""

    class Meta:
        model = Accounting
        fields = TenantModelSerializer.Meta.fields + [
            'account_number',
            'name',
            'account_type',
            'description',
            'is_active',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class AccountingViewSet(ReadOnlyTenantViewSet):
    """ViewSet for Accounting (Chart of Accounts) read-only operations."""

    queryset = Accounting.objects.all()
    serializer_class = AccountingSerializer
    filterset_fields = ['account_type', 'is_active']
    search_fields = ['account_number', 'name', 'description']
    ordering_fields = ['account_number', 'account_type', 'name']


# ---------------------------------------------------------------------------
# Ledger Serializers & ViewSets
# ---------------------------------------------------------------------------

class LedgerSerializer(TenantModelSerializer):
    """Serializer for Ledger (General Ledger) model."""

    account_number = serializers.CharField(
        source='account.account_number',
        read_only=True,
    )
    account_name = serializers.CharField(
        source='account.name',
        read_only=True,
    )
    invoice_number = serializers.CharField(
        source='invoice.invoice_number',
        read_only=True,
        allow_null=True,
    )
    payment_number = serializers.CharField(
        source='payment.payment_number',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Ledger
        fields = TenantModelSerializer.Meta.fields + [
            'account',
            'account_number',
            'account_name',
            'entry_type',
            'amount',
            'transaction_date',
            'reference',
            'description',
            'invoice',
            'invoice_number',
            'payment',
            'payment_number',
            'vendor_bill',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'account_number',
            'account_name',
            'invoice_number',
            'payment_number',
        ]


class LedgerViewSet(ReadOnlyTenantViewSet):
    """ViewSet for Ledger read-only operations."""

    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer
    filterset_fields = ['account_id', 'entry_type', 'invoice_id', 'payment_id']
    search_fields = ['account__account_number', 'reference', 'description']
    ordering_fields = ['created_on', 'transaction_date', 'account__account_number', 'amount']


# ---------------------------------------------------------------------------
# Router Setup
# ---------------------------------------------------------------------------

router = DefaultRouter()
router.register(r'service-requests', ServiceRequestViewSet, basename='service-request')
router.register(r'work-orders', WorkOrderViewSet, basename='work-order')
router.register(r'work-order-teams', WorkOrderTeamViewSet, basename='work-order-team')
router.register(r'work-order-lines', WorkOrderLineViewSet, basename='work-order-line')
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'quote-lines', QuoteLineViewSet, basename='quote-line')
router.register(r'quote-assets', QuoteAssetViewSet, basename='quote-asset')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'invoice-lines', InvoiceLineViewSet, basename='invoice-line')
router.register(r'invoice-assets', InvoiceAssetViewSet, basename='invoice-asset')
router.register(r'work-order-invoices', WorkOrderInvoiceViewSet, basename='work-order-invoice')
router.register(r'banks', BankViewSet, basename='bank')
router.register(r'payments', PaymentsViewSet, basename='payment')
router.register(r'accounting', AccountingViewSet, basename='accounting')
router.register(r'ledger', LedgerViewSet, basename='ledger')
