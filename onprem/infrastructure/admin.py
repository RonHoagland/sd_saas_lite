# infrastructure/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from infrastructure.models import (
    TenantState, TenantAddOn, SubdomainIndex,
    SystemAudits, Notification, IssuesErrors,
    StorageTracker, EmailUsageTracker, SMSUsageTracker,
    OnboardingState, TenantSyncLog, DataExportLog, EmailDeliveryLog,
    StripeConnection, StripeResponse, StripeLog, StripeConnectionLog,
    StripeAPIRequestLog, WebhookLog, ErrorCode, ProcessTransaction, NavigationAudit,
)


# --- Non-tenant models registered with base ModelAdmin ---

@admin.register(TenantState)
class TenantStateAdmin(admin.ModelAdmin):
    list_display = ('subdomain', 'company_name', 'status', 'tier',
                    'owner_email', 'created_on')
    list_filter = ('status', 'tier')
    search_fields = ('subdomain', 'company_name', 'owner_email')
    readonly_fields = ('id', 'created_on', 'updated_on')


@admin.register(TenantAddOn)
class TenantAddOnAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'add_on_key', 'is_active', 'activated_on', 'expires_on')
    list_filter = ('is_active',)
    search_fields = ('tenant__subdomain', 'add_on_key')
    readonly_fields = ('id', 'created_on', 'updated_on')


@admin.register(SubdomainIndex)
class SubdomainIndexAdmin(admin.ModelAdmin):
    list_display = ('subdomain', 'tenant')
    search_fields = ('subdomain',)
    readonly_fields = ('id',)


@admin.register(ErrorCode)
class ErrorCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'category', 'is_user_facing')
    list_filter = ('is_user_facing', 'category')
    search_fields = ('code', 'message_template')
    readonly_fields = ('id',)


# --- Tenant-scoped models registered with TenantModelAdmin ---

@admin.register(SystemAudits)
class SystemAuditsAdmin(TenantModelAdmin):
    list_display = ('actor', 'action', 'model_name', 'object_id',
                    'ip_address', 'created_on', 'tenant_id')
    list_filter = ('tenant_id', 'action', 'model_name')
    search_fields = ('model_name', 'actor__email')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on',
                       'before_snapshot', 'after_snapshot')


@admin.register(Notification)
class NotificationAdmin(TenantModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'is_read',
                    'read_at', 'tenant_id')
    list_filter = ('tenant_id', 'notification_type', 'is_read')
    search_fields = ('title', 'recipient__email')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(IssuesErrors)
class IssuesErrorsAdmin(TenantModelAdmin):
    list_display = ('error_code', 'severity', 'status', 'created_on', 'tenant_id')
    list_filter = ('tenant_id', 'severity', 'status')
    search_fields = ('error_code', 'message')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(StorageTracker)
class StorageTrackerAdmin(TenantModelAdmin):
    list_display = ('tenant_id', 'period_year', 'period_month', 'bytes_used', 'file_count')
    list_filter = ('tenant_id',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(EmailUsageTracker)
class EmailUsageTrackerAdmin(TenantModelAdmin):
    list_display = ('tenant_id', 'period_year', 'period_month', 'emails_sent')
    list_filter = ('tenant_id',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(SMSUsageTracker)
class SMSUsageTrackerAdmin(TenantModelAdmin):
    list_display = ('tenant_id', 'period_year', 'period_month', 'sms_sent')
    list_filter = ('tenant_id',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(OnboardingState)
class OnboardingStateAdmin(TenantModelAdmin):
    list_display = ('tenant_id', 'step_key', 'is_completed', 'completed_at', 'sort_order')
    list_filter = ('tenant_id', 'is_completed')
    search_fields = ('step_key',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(TenantSyncLog)
class TenantSyncLogAdmin(TenantModelAdmin):
    list_display = ('sync_type', 'status', 'started_at', 'completed_at',
                    'records_processed', 'records_failed', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'sync_type')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(DataExportLog)
class DataExportLogAdmin(TenantModelAdmin):
    list_display = ('export_type', 'status', 'requested_by', 'expires_at', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('export_type',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(EmailDeliveryLog)
class EmailDeliveryLogAdmin(TenantModelAdmin):
    list_display = ('recipient_email', 'subject', 'status', 'sent_at', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('recipient_email', 'subject')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(StripeConnection)
class StripeConnectionAdmin(TenantModelAdmin):
    list_display = ('tenant_id', 'stripe_customer_id', 'stripe_subscription_id',
                    'is_active', 'connected_at')
    list_filter = ('tenant_id', 'is_active')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(StripeResponse)
class StripeResponseAdmin(TenantModelAdmin):
    list_display = ('stripe_object_type', 'stripe_object_id', 'tenant_id')
    list_filter = ('tenant_id', 'stripe_object_type')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on', 'raw_response')


@admin.register(StripeLog)
class StripeLogAdmin(TenantModelAdmin):
    list_display = ('event_type', 'stripe_object_id', 'amount', 'created_on', 'tenant_id')
    list_filter = ('tenant_id', 'event_type')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(StripeConnectionLog)
class StripeConnectionLogAdmin(TenantModelAdmin):
    list_display = ('action', 'actor', 'created_on', 'tenant_id')
    list_filter = ('tenant_id', 'action')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(StripeAPIRequestLog)
class StripeAPIRequestLogAdmin(TenantModelAdmin):
    list_display = ('method', 'endpoint', 'status', 'http_status_code',
                    'duration_ms', 'created_on', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('endpoint',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on',
                       'request_payload', 'response_payload')


@admin.register(WebhookLog)
class WebhookLogAdmin(TenantModelAdmin):
    list_display = ('source', 'event_type', 'status', 'processed_at', 'tenant_id')
    list_filter = ('tenant_id', 'source', 'status')
    search_fields = ('event_type',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on', 'raw_payload')


@admin.register(ProcessTransaction)
class ProcessTransactionAdmin(TenantModelAdmin):
    list_display = ('process_name', 'idempotency_key', 'status',
                    'started_at', 'completed_at', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('process_name', 'idempotency_key')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on',
                       'payload', 'result')


@admin.register(NavigationAudit)
class NavigationAuditAdmin(TenantModelAdmin):
    list_display = ('user', 'method', 'path', 'http_status_code',
                    'response_ms', 'ip_address', 'created_on', 'tenant_id')
    list_filter = ('tenant_id', 'method')
    search_fields = ('path', 'user__email')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
