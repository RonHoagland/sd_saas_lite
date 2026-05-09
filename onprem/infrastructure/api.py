# infrastructure/api.py
# REST API serializers and viewsets for infrastructure app models.
#
# Special note: TenantState, TenantAddOn, SubdomainIndex, and ErrorCode are NOT
# TenantModel and use plain ModelSerializer. All other models extend TenantModel.
#
# Models:
#   TenantState, TenantAddOn, SubdomainIndex, SystemAudits,
#   Notification, IssuesErrors, StorageTracker, EmailUsageTracker, SMSUsageTracker,
#   OnboardingState, TenantSyncLog, DataExportLog, EmailDeliveryLog,
#   StripeConnection, StripeResponse, StripeLog, StripeConnectionLog,
#   StripeAPIRequestLog, WebhookLog, ErrorCode, ProcessTransaction, NavigationAudit

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet, TenantNoDeleteViewSet, ReadOnlyTenantViewSet
from .models import (
    TenantState, TenantAddOn, SubdomainIndex, SystemAudits,
    Notification, IssuesErrors, StorageTracker, EmailUsageTracker, SMSUsageTracker,
    OnboardingState, TenantSyncLog, DataExportLog, EmailDeliveryLog,
    StripeConnection, StripeResponse, StripeLog, StripeConnectionLog,
    StripeAPIRequestLog, WebhookLog, ErrorCode, ProcessTransaction, NavigationAudit
)


# ─── Tenant Registry (NOT TenantModel) ────────────────────────────────────────

class TenantStateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TenantState
        fields = [
            'id',
            'subdomain',
            'company_name',
            'status',
            'tier',
            'owner_email',
            'owner_name',
            'timezone',
            'locale',
            'trial_ends_on',
            'subscription_ends_on',
            'created_on',
            'updated_on',
        ]
        read_only_fields = [
            'id',
            'created_on',
            'updated_on',
        ]


class TenantStateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TenantState.objects.all()
    serializer_class = TenantStateSerializer
    filterset_fields = ['status', 'tier']
    search_fields = ['company_name', 'subdomain', 'owner_email']
    ordering_fields = ['company_name', 'created_on', 'status']


class TenantAddOnSerializer(serializers.ModelSerializer):
    tenant_display = serializers.CharField(source='tenant.company_name', read_only=True)

    class Meta:
        model = TenantAddOn
        fields = [
            'id',
            'tenant',
            'tenant_display',
            'add_on_key',
            'is_active',
            'activated_on',
            'expires_on',
            'created_on',
            'updated_on',
        ]
        read_only_fields = [
            'id',
            'tenant_display',
            'created_on',
            'updated_on',
        ]


class TenantAddOnViewSet(viewsets.ModelViewSet):
    queryset = TenantAddOn.objects.all()
    serializer_class = TenantAddOnSerializer
    filterset_fields = ['tenant_id', 'add_on_key', 'is_active']
    search_fields = ['tenant__company_name', 'add_on_key']
    ordering_fields = ['activated_on', 'expires_on', 'created_on']


class SubdomainIndexSerializer(serializers.ModelSerializer):
    tenant_display = serializers.CharField(source='tenant.company_name', read_only=True)

    class Meta:
        model = SubdomainIndex
        fields = [
            'id',
            'subdomain',
            'tenant',
            'tenant_display',
        ]
        read_only_fields = [
            'id',
            'tenant_display',
        ]


class SubdomainIndexViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubdomainIndex.objects.all()
    serializer_class = SubdomainIndexSerializer
    filterset_fields = ['subdomain']
    search_fields = ['subdomain', 'tenant__company_name']
    ordering_fields = ['subdomain']


# ─── Audit & Monitoring ───────────────────────────────────────────────────────

class SystemAuditsSerializer(TenantModelSerializer):
    actor_display = serializers.CharField(source='actor.email', read_only=True)

    class Meta:
        model = SystemAudits
        fields = TenantModelSerializer.Meta.fields + [
            'actor',
            'actor_display',
            'action',
            'model_name',
            'object_id',
            'before_snapshot',
            'after_snapshot',
            'ip_address',
            'user_agent',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'actor_display',
        ]


class SystemAuditsViewSet(ReadOnlyTenantViewSet):
    queryset = SystemAudits.objects.all()
    serializer_class = SystemAuditsSerializer
    filterset_fields = ['actor_id', 'action', 'model_name']
    search_fields = ['model_name', 'actor__email']
    ordering_fields = ['created_on', 'action']


class NotificationSerializer(TenantModelSerializer):
    recipient_display = serializers.CharField(source='recipient.email', read_only=True)

    class Meta:
        model = Notification
        fields = TenantModelSerializer.Meta.fields + [
            'recipient',
            'recipient_display',
            'notification_type',
            'title',
            'body',
            'is_read',
            'read_at',
            'action_url',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'recipient_display',
        ]


class NotificationViewSet(TenantModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filterset_fields = ['recipient_id', 'notification_type', 'is_read']
    search_fields = ['title', 'recipient__email']
    ordering_fields = ['created_on', 'is_read']


class IssuesErrorsSerializer(TenantModelSerializer):

    class Meta:
        model = IssuesErrors
        fields = TenantModelSerializer.Meta.fields + [
            'error_code',
            'severity',
            'status',
            'message',
            'stack_trace',
            'context',
            'resolved_at',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class IssuesErrorsViewSet(TenantModelViewSet):
    queryset = IssuesErrors.objects.all()
    serializer_class = IssuesErrorsSerializer
    filterset_fields = ['severity', 'status', 'error_code']
    search_fields = ['message', 'error_code']
    ordering_fields = ['severity', 'created_on', 'status']


# ─── Usage Trackers ───────────────────────────────────────────────────────────

class StorageTrackerSerializer(TenantModelSerializer):

    class Meta:
        model = StorageTracker
        fields = TenantModelSerializer.Meta.fields + [
            'period_year',
            'period_month',
            'bytes_used',
            'file_count',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class StorageTrackerViewSet(ReadOnlyTenantViewSet):
    queryset = StorageTracker.objects.all()
    serializer_class = StorageTrackerSerializer
    filterset_fields = ['period_year', 'period_month']
    search_fields = []
    ordering_fields = ['period_year', 'period_month']


class EmailUsageTrackerSerializer(TenantModelSerializer):

    class Meta:
        model = EmailUsageTracker
        fields = TenantModelSerializer.Meta.fields + [
            'period_year',
            'period_month',
            'emails_sent',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class EmailUsageTrackerViewSet(ReadOnlyTenantViewSet):
    queryset = EmailUsageTracker.objects.all()
    serializer_class = EmailUsageTrackerSerializer
    filterset_fields = ['period_year', 'period_month']
    search_fields = []
    ordering_fields = ['period_year', 'period_month']


class SMSUsageTrackerSerializer(TenantModelSerializer):

    class Meta:
        model = SMSUsageTracker
        fields = TenantModelSerializer.Meta.fields + [
            'period_year',
            'period_month',
            'sms_sent',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class SMSUsageTrackerViewSet(ReadOnlyTenantViewSet):
    queryset = SMSUsageTracker.objects.all()
    serializer_class = SMSUsageTrackerSerializer
    filterset_fields = ['period_year', 'period_month']
    search_fields = []
    ordering_fields = ['period_year', 'period_month']


# ─── Onboarding & Sync ────────────────────────────────────────────────────────

class OnboardingStateSerializer(TenantModelSerializer):

    class Meta:
        model = OnboardingState
        fields = TenantModelSerializer.Meta.fields + [
            'step_key',
            'is_completed',
            'completed_at',
            'sort_order',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class OnboardingStateViewSet(TenantModelViewSet):
    queryset = OnboardingState.objects.all()
    serializer_class = OnboardingStateSerializer
    filterset_fields = ['step_key', 'is_completed']
    search_fields = ['step_key']
    ordering_fields = ['sort_order', 'created_on']


class TenantSyncLogSerializer(TenantModelSerializer):

    class Meta:
        model = TenantSyncLog
        fields = TenantModelSerializer.Meta.fields + [
            'sync_type',
            'status',
            'started_at',
            'completed_at',
            'records_processed',
            'records_failed',
            'error_detail',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class TenantSyncLogViewSet(ReadOnlyTenantViewSet):
    queryset = TenantSyncLog.objects.all()
    serializer_class = TenantSyncLogSerializer
    filterset_fields = ['sync_type', 'status']
    search_fields = ['sync_type']
    ordering_fields = ['started_at', 'created_on', 'status']


class DataExportLogSerializer(TenantModelSerializer):
    requested_by_display = serializers.CharField(source='requested_by.email', read_only=True)

    class Meta:
        model = DataExportLog
        fields = TenantModelSerializer.Meta.fields + [
            'requested_by',
            'requested_by_display',
            'export_type',
            'status',
            'file_url',
            'expires_at',
            'error_detail',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'requested_by_display',
        ]


class DataExportLogViewSet(ReadOnlyTenantViewSet):
    queryset = DataExportLog.objects.all()
    serializer_class = DataExportLogSerializer
    filterset_fields = ['requested_by_id', 'export_type', 'status']
    search_fields = ['export_type']
    ordering_fields = ['created_on', 'status']


class EmailDeliveryLogSerializer(TenantModelSerializer):
    trigger_log_display = serializers.SerializerMethodField(read_only=True)

    def get_trigger_log_display(self, obj):
        return str(obj.trigger_log_id) if obj.trigger_log else None

    class Meta:
        model = EmailDeliveryLog
        fields = TenantModelSerializer.Meta.fields + [
            'recipient_email',
            'subject',
            'status',
            'sent_at',
            'provider_message_id',
            'error_detail',
            'trigger_log',
            'trigger_log_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'trigger_log_display',
        ]


class EmailDeliveryLogViewSet(ReadOnlyTenantViewSet):
    queryset = EmailDeliveryLog.objects.all()
    serializer_class = EmailDeliveryLogSerializer
    filterset_fields = ['status', 'recipient_email']
    search_fields = ['recipient_email', 'subject']
    ordering_fields = ['sent_at', 'created_on', 'status']


# ─── Stripe Integration ───────────────────────────────────────────────────────

class StripeConnectionSerializer(TenantModelSerializer):

    class Meta:
        model = StripeConnection
        fields = TenantModelSerializer.Meta.fields + [
            'stripe_customer_id',
            'stripe_subscription_id',
            'is_active',
            'connected_at',
            'disconnected_at',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class StripeConnectionViewSet(TenantModelViewSet):
    queryset = StripeConnection.objects.all()
    serializer_class = StripeConnectionSerializer
    filterset_fields = ['is_active']
    search_fields = ['stripe_customer_id']
    ordering_fields = ['connected_at', 'created_on']


class StripeResponseSerializer(TenantModelSerializer):

    class Meta:
        model = StripeResponse
        fields = TenantModelSerializer.Meta.fields + [
            'stripe_object_type',
            'stripe_object_id',
            'raw_response',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class StripeResponseViewSet(ReadOnlyTenantViewSet):
    queryset = StripeResponse.objects.all()
    serializer_class = StripeResponseSerializer
    filterset_fields = ['stripe_object_type']
    search_fields = ['stripe_object_id']
    ordering_fields = ['created_on']


class StripeLogSerializer(TenantModelSerializer):

    class Meta:
        model = StripeLog
        fields = TenantModelSerializer.Meta.fields + [
            'event_type',
            'stripe_object_id',
            'description',
            'amount',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class StripeLogViewSet(ReadOnlyTenantViewSet):
    queryset = StripeLog.objects.all()
    serializer_class = StripeLogSerializer
    filterset_fields = ['event_type']
    search_fields = ['stripe_object_id', 'event_type']
    ordering_fields = ['created_on']


class StripeConnectionLogSerializer(TenantModelSerializer):
    actor_display = serializers.CharField(source='actor.email', read_only=True)

    class Meta:
        model = StripeConnectionLog
        fields = TenantModelSerializer.Meta.fields + [
            'action',
            'actor',
            'actor_display',
            'detail',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'actor_display',
        ]


class StripeConnectionLogViewSet(ReadOnlyTenantViewSet):
    queryset = StripeConnectionLog.objects.all()
    serializer_class = StripeConnectionLogSerializer
    filterset_fields = ['action', 'actor_id']
    search_fields = ['action', 'actor__email']
    ordering_fields = ['created_on']


class StripeAPIRequestLogSerializer(TenantModelSerializer):

    class Meta:
        model = StripeAPIRequestLog
        fields = TenantModelSerializer.Meta.fields + [
            'endpoint',
            'method',
            'status',
            'http_status_code',
            'request_payload',
            'response_payload',
            'duration_ms',
            'error_message',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class StripeAPIRequestLogViewSet(ReadOnlyTenantViewSet):
    queryset = StripeAPIRequestLog.objects.all()
    serializer_class = StripeAPIRequestLogSerializer
    filterset_fields = ['status', 'method']
    search_fields = ['endpoint']
    ordering_fields = ['created_on', 'status']


# ─── Webhook & Error Tracking ────────────────────────────────────────────────

class WebhookLogSerializer(TenantModelSerializer):

    class Meta:
        model = WebhookLog
        fields = TenantModelSerializer.Meta.fields + [
            'source',
            'event_type',
            'status',
            'raw_payload',
            'error_detail',
            'processed_at',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class WebhookLogViewSet(ReadOnlyTenantViewSet):
    queryset = WebhookLog.objects.all()
    serializer_class = WebhookLogSerializer
    filterset_fields = ['source', 'event_type', 'status']
    search_fields = ['source', 'event_type']
    ordering_fields = ['processed_at', 'created_on', 'status']


class ErrorCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ErrorCode
        fields = [
            'id',
            'code',
            'category',
            'message_template',
            'description',
            'is_user_facing',
        ]
        read_only_fields = [
            'id',
        ]


class ErrorCodeViewSet(viewsets.ModelViewSet):
    queryset = ErrorCode.objects.all()
    serializer_class = ErrorCodeSerializer
    filterset_fields = ['category', 'is_user_facing']
    search_fields = ['code', 'message_template']
    ordering_fields = ['code', 'category']


# ─── Background Jobs & Transactions ───────────────────────────────────────────

class ProcessTransactionSerializer(TenantModelSerializer):

    class Meta:
        model = ProcessTransaction
        fields = TenantModelSerializer.Meta.fields + [
            'idempotency_key',
            'process_name',
            'status',
            'payload',
            'result',
            'error_detail',
            'started_at',
            'completed_at',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class ProcessTransactionViewSet(TenantModelViewSet):
    queryset = ProcessTransaction.objects.all()
    serializer_class = ProcessTransactionSerializer
    filterset_fields = ['process_name', 'status']
    search_fields = ['process_name', 'idempotency_key']
    ordering_fields = ['started_at', 'completed_at', 'created_on', 'status']


# ─── Navigation Audit ────────────────────────────────────────────────────────

class NavigationAuditSerializer(TenantModelSerializer):
    user_display = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = NavigationAudit
        fields = TenantModelSerializer.Meta.fields + [
            'user',
            'user_display',
            'path',
            'method',
            'http_status_code',
            'response_ms',
            'ip_address',
            'user_agent',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'user_display',
        ]


class NavigationAuditViewSet(ReadOnlyTenantViewSet):
    queryset = NavigationAudit.objects.all()
    serializer_class = NavigationAuditSerializer
    filterset_fields = ['user_id', 'method', 'http_status_code']
    search_fields = ['path', 'user__email']
    ordering_fields = ['created_on']


# ─── Router ───────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register(r'tenant-states', TenantStateViewSet, basename='tenant-state')
router.register(r'tenant-addons', TenantAddOnViewSet, basename='tenant-addon')
router.register(r'subdomain-index', SubdomainIndexViewSet, basename='subdomain-index')
router.register(r'system-audits', SystemAuditsViewSet, basename='system-audit')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'issues-errors', IssuesErrorsViewSet, basename='issues-error')
router.register(r'storage-trackers', StorageTrackerViewSet, basename='storage-tracker')
router.register(r'email-usage-trackers', EmailUsageTrackerViewSet, basename='email-usage-tracker')
router.register(r'sms-usage-trackers', SMSUsageTrackerViewSet, basename='sms-usage-tracker')
router.register(r'onboarding-states', OnboardingStateViewSet, basename='onboarding-state')
router.register(r'tenant-sync-logs', TenantSyncLogViewSet, basename='tenant-sync-log')
router.register(r'data-export-logs', DataExportLogViewSet, basename='data-export-log')
router.register(r'email-delivery-logs', EmailDeliveryLogViewSet, basename='email-delivery-log')
router.register(r'stripe-connections', StripeConnectionViewSet, basename='stripe-connection')
router.register(r'stripe-responses', StripeResponseViewSet, basename='stripe-response')
router.register(r'stripe-logs', StripeLogViewSet, basename='stripe-log')
router.register(r'stripe-connection-logs', StripeConnectionLogViewSet, basename='stripe-connection-log')
router.register(r'stripe-api-request-logs', StripeAPIRequestLogViewSet, basename='stripe-api-request-log')
router.register(r'webhook-logs', WebhookLogViewSet, basename='webhook-log')
router.register(r'error-codes', ErrorCodeViewSet, basename='error-code')
router.register(r'process-transactions', ProcessTransactionViewSet, basename='process-transaction')
router.register(r'navigation-audits', NavigationAuditViewSet, basename='navigation-audit')
