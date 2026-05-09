# service/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from service.models import (
    ServiceRequest, WorkOrder, WorkOrderTeam, WorkOrderLine,
    Quote, QuoteLine, QuoteAsset,
    Invoice, InvoiceLine, InvoiceAsset, WorkOrderInvoice,
    Bank, Payments, Accounting, Ledger,
)


@admin.register(ServiceRequest)
class ServiceRequestAdmin(TenantModelAdmin):
    list_display = ('request_number', 'customer', 'subject', 'status',
                    'priority', 'assigned_to', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'priority')
    search_fields = ('request_number', 'subject', 'customer__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WorkOrder)
class WorkOrderAdmin(TenantModelAdmin):
    list_display = ('wo_number', 'customer', 'subject', 'status',
                    'priority', 'scheduled_date', 'assigned_to', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'priority')
    search_fields = ('wo_number', 'subject', 'customer__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WorkOrderTeam)
class WorkOrderTeamAdmin(TenantModelAdmin):
    list_display = ('work_order', 'user', 'role', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('work_order__wo_number', 'user__email')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WorkOrderLine)
class WorkOrderLineAdmin(TenantModelAdmin):
    list_display = ('work_order', 'line_type', 'product', 'description',
                    'quantity', 'unit_price', 'line_total', 'tenant_id')
    list_filter = ('tenant_id', 'line_type')
    search_fields = ('work_order__wo_number', 'description')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Quote)
class QuoteAdmin(TenantModelAdmin):
    list_display = ('quote_number', 'customer', 'status', 'quote_date',
                    'expiration_date', 'total', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('quote_number', 'customer__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(QuoteLine)
class QuoteLineAdmin(TenantModelAdmin):
    list_display = ('quote', 'line_type', 'product', 'description',
                    'quantity', 'unit_price', 'line_total', 'tenant_id')
    list_filter = ('tenant_id', 'line_type')
    search_fields = ('quote__quote_number', 'description')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(QuoteAsset)
class QuoteAssetAdmin(TenantModelAdmin):
    list_display = ('quote', 'asset', 'tenant_id')
    list_filter = ('tenant_id',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Invoice)
class InvoiceAdmin(TenantModelAdmin):
    list_display = ('invoice_number', 'customer', 'status', 'invoice_date',
                    'due_date', 'total', 'amount_paid', 'balance_due', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('invoice_number', 'customer__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(InvoiceLine)
class InvoiceLineAdmin(TenantModelAdmin):
    list_display = ('invoice', 'line_type', 'product', 'description',
                    'quantity', 'unit_price', 'line_total', 'tenant_id')
    list_filter = ('tenant_id', 'line_type')
    search_fields = ('invoice__invoice_number', 'description')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(InvoiceAsset)
class InvoiceAssetAdmin(TenantModelAdmin):
    list_display = ('invoice', 'asset', 'tenant_id')
    list_filter = ('tenant_id',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WorkOrderInvoice)
class WorkOrderInvoiceAdmin(TenantModelAdmin):
    list_display = ('work_order', 'invoice', 'tenant_id')
    list_filter = ('tenant_id',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Bank)
class BankAdmin(TenantModelAdmin):
    list_display = ('name', 'account_number_last4', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('name',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Payments)
class PaymentsAdmin(TenantModelAdmin):
    list_display = ('invoice', 'payment_date', 'amount', 'method',
                    'reference_number', 'bank', 'tenant_id')
    list_filter = ('tenant_id', 'method')
    search_fields = ('reference_number', 'invoice__invoice_number')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Accounting)
class AccountingAdmin(TenantModelAdmin):
    list_display = ('account_number', 'name', 'account_type', 'is_active', 'tenant_id')
    list_filter = ('tenant_id', 'account_type', 'is_active')
    search_fields = ('account_number', 'name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Ledger)
class LedgerAdmin(TenantModelAdmin):
    list_display = ('account', 'entry_type', 'amount', 'transaction_date',
                    'reference', 'tenant_id')
    list_filter = ('tenant_id', 'entry_type')
    search_fields = ('reference', 'account__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
