# infrastructure/models.py
# Source: Data Models V6, Sections 1.9, 1.10, 1.11, 3.7.
#
# Models in this app:
#   TenantState, TenantAddOn, SubdomainIndex,
#   SystemAudits, Notification, IssuesErrors,
#   StorageTracker, EmailUsageTracker, SMSUsageTracker,
#   OnboardingState, TenantSyncLog, DataExportLog, EmailDeliveryLog,
#   StripeConnection, StripeResponse, StripeLog, StripeConnectionLog,
#   StripeAPIRequestLog, WebhookLog, ErrorCode, ProcessTransaction, NavigationAudit
#
# IMPORTANT:
#   TenantState is the central tenant registry.  It does NOT extend TenantModel
#   because it IS the tenant record — queried before tenant context is set.
#   All other models in this app extend TenantModel and inherit audit fields.

import uuid
from django.db import models
from config.base_models import TenantModel


# ---------------------------------------------------------------------------
# Tenant Registry
# ---------------------------------------------------------------------------

class TenantState(models.Model):
    """
    Master registry of all tenants.
    This model does NOT extend TenantModel — it IS the tenant record.
    Source: Data Models V6, Section 1.9.
    """

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        SUSPENDED = 'Suspended', 'Suspended'
        CANCELLED = 'Cancelled', 'Cancelled'
        TRIAL = 'Trial', 'Trial'
        ONBOARDING = 'Onboarding', 'Onboarding'

    class TierChoices(models.TextChoices):
        LITE = 'Lite', 'Lite'
        PLUS = 'Plus', 'Plus'
        PRO = 'Pro', 'Pro'
        ENTERPRISE = 'Enterprise', 'Enterprise'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subdomain = models.CharField(max_length=100, unique=True)
    company_name = models.CharField(max_length=200)
    status = models.CharField(max_length=12, choices=StatusChoices.choices,
                               default=StatusChoices.ONBOARDING)
    tier = models.CharField(max_length=12, choices=TierChoices.choices,
                             default=TierChoices.LITE)
    owner_email = models.EmailField()
    owner_name = models.CharField(max_length=200, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    locale = models.CharField(max_length=10, default='en-US')
    trial_ends_on = models.DateField(null=True, blank=True)
    subscription_ends_on = models.DateField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'infrastructure_tenantstate'

    def __str__(self):
        return f'{self.company_name} ({self.subdomain})'


class TenantAddOn(models.Model):
    """
    Optional add-on features purchased by a tenant.
    Source: Data Models V6, Section 1.9.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantState, on_delete=models.CASCADE,
                                related_name='add_ons')
    add_on_key = models.CharField(max_length=100,
                                   help_text='Internal key for the add-on feature.')
    is_active = models.BooleanField(default=True)
    activated_on = models.DateField(null=True, blank=True)
    expires_on = models.DateField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'infrastructure_tenantaddon'
        unique_together = [('tenant', 'add_on_key')]

    def __str__(self):
        return f'{self.tenant} — {self.add_on_key}'


class SubdomainIndex(models.Model):
    """
    Fast lookup index mapping subdomain slug to tenant UUID.
    Queried before tenant context is established, so no TenantModel.
    Source: Data Models V6, Section 1.9.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subdomain = models.CharField(max_length=100, unique=True, db_index=True)
    tenant = models.OneToOneField(TenantState, on_delete=models.CASCADE,
                                   related_name='subdomain_index')

    class Meta:
        db_table = 'infrastructure_subdomainindex'

    def __str__(self):
        return self.subdomain


# ---------------------------------------------------------------------------
# Tenant-Scoped Infrastructure
# ---------------------------------------------------------------------------

class SystemAudits(TenantModel):
    """
    Immutable record of every data-changing action performed by a user.
    Source: Data Models V6, Section 1.10.
    """

    actor = models.ForeignKey('users.User', null=True, blank=True,
                               on_delete=models.SET_NULL,
                               related_name='audit_entries')
    action = models.CharField(max_length=100,
                               help_text='e.g. create, update, delete, login')
    model_name = models.CharField(max_length=100)
    object_id = models.UUIDField(null=True, blank=True)
    before_snapshot = models.JSONField(null=True, blank=True)
    after_snapshot = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'infrastructure_systemaudits'
        indexes = [
            models.Index(fields=['tenant_id', 'model_name']),
            models.Index(fields=['tenant_id', 'actor_id']),
        ]

    def __str__(self):
        return f'{self.actor} {self.action} {self.model_name} ({self.created_on})'


class Notification(TenantModel):
    """
    In-app notification for a tenant user.
    Source: Data Models V6, Section 1.10.
    """

    class TypeChoices(models.TextChoices):
        INFO = 'Info', 'Info'
        WARNING = 'Warning', 'Warning'
        ERROR = 'Error', 'Error'
        SUCCESS = 'Success', 'Success'

    recipient = models.ForeignKey('users.User', on_delete=models.CASCADE,
                                   related_name='notifications')
    notification_type = models.CharField(max_length=10, choices=TypeChoices.choices,
                                          default=TypeChoices.INFO)
    title = models.CharField(max_length=300)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    action_url = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'infrastructure_notification'
        indexes = [
            models.Index(fields=['tenant_id', 'recipient_id', 'is_read']),
        ]

    def __str__(self):
        return f'{self.recipient} — {self.title}'


class IssuesErrors(TenantModel):
    """
    Application error / issue log captured at runtime.
    Source: Data Models V6, Section 1.10.
    """

    class SeverityChoices(models.TextChoices):
        LOW = 'Low', 'Low'
        MEDIUM = 'Medium', 'Medium'
        HIGH = 'High', 'High'
        CRITICAL = 'Critical', 'Critical'

    class StatusChoices(models.TextChoices):
        OPEN = 'Open', 'Open'
        ACKNOWLEDGED = 'Acknowledged', 'Acknowledged'
        RESOLVED = 'Resolved', 'Resolved'
        IGNORED = 'Ignored', 'Ignored'

    error_code = models.CharField(max_length=50, blank=True)
    severity = models.CharField(max_length=10, choices=SeverityChoices.choices,
                                 default=SeverityChoices.MEDIUM)
    status = models.CharField(max_length=15, choices=StatusChoices.choices,
                               default=StatusChoices.OPEN)
    message = models.TextField()
    stack_trace = models.TextField(blank=True)
    context = models.JSONField(default=dict, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'infrastructure_issueserrors'
        indexes = [
            models.Index(fields=['tenant_id', 'severity', 'status']),
        ]

    def __str__(self):
        return f'[{self.severity}] {self.error_code} — {self.message[:80]}'


# ---------------------------------------------------------------------------
# Usage Trackers
# ---------------------------------------------------------------------------

class StorageTracker(TenantModel):
    """
    Monthly storage usage snapshot for a tenant.
    Source: Data Models V6, Section 1.11.
    """

    period_year = models.PositiveSmallIntegerField()
    period_month = models.PositiveSmallIntegerField()
    bytes_used = models.BigIntegerField(default=0)
    file_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'infrastructure_storagetracker'
        unique_together = [('tenant_id', 'period_year', 'period_month')]

    def __str__(self):
        return f'{self.tenant_id} storage {self.period_year}-{self.period_month:02d}'


class EmailUsageTracker(TenantModel):
    """
    Monthly email send count for a tenant.
    Source: Data Models V6, Section 1.11.
    """

    period_year = models.PositiveSmallIntegerField()
    period_month = models.PositiveSmallIntegerField()
    emails_sent = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'infrastructure_emailusagetracker'
        unique_together = [('tenant_id', 'period_year', 'period_month')]

    def __str__(self):
        return f'{self.tenant_id} email {self.period_year}-{self.period_month:02d}'


class SMSUsageTracker(TenantModel):
    """
    Monthly SMS send count for a tenant.
    Source: Data Models V6, Section 1.11.
    """

    period_year = models.PositiveSmallIntegerField()
    period_month = models.PositiveSmallIntegerField()
    sms_sent = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'infrastructure_smsusagetracker'
        unique_together = [('tenant_id', 'period_year', 'period_month')]

    def __str__(self):
        return f'{self.tenant_id} sms {self.period_year}-{self.period_month:02d}'


# ---------------------------------------------------------------------------
# Onboarding & Sync
# ---------------------------------------------------------------------------

class OnboardingState(TenantModel):
    """
    Tracks per-tenant onboarding step completion.
    Source: Data Models V6, Section 1.9.
    """

    step_key = models.CharField(max_length=100)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'infrastructure_onboardingstate'
        unique_together = [('tenant_id', 'step_key')]
        ordering = ['sort_order']

    def __str__(self):
        return f'{self.tenant_id} — {self.step_key} ({"done" if self.is_completed else "pending"})'


class TenantSyncLog(TenantModel):
    """
    Log of external data sync operations (e.g. QuickBooks, Xero).
    Source: Data Models V6, Section 3.7.
    """

    class StatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        SUCCESS = 'Success', 'Success'
        PARTIAL = 'Partial', 'Partial'
        FAILED = 'Failed', 'Failed'

    sync_type = models.CharField(max_length=100,
                                  help_text='e.g. quickbooks_export, xero_import')
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_processed = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    error_detail = models.TextField(blank=True)

    class Meta:
        db_table = 'infrastructure_tenantsynclog'
        indexes = [
            models.Index(fields=['tenant_id', 'sync_type', 'status']),
        ]

    def __str__(self):
        return f'{self.sync_type} ({self.status}) @ {self.started_at}'


class DataExportLog(TenantModel):
    """
    Record of each data export triggered by a tenant user.
    Source: Data Models V6, Section 3.7.
    """

    class StatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        PROCESSING = 'Processing', 'Processing'
        COMPLETED = 'Completed', 'Completed'
        FAILED = 'Failed', 'Failed'

    requested_by = models.ForeignKey('users.User', null=True, blank=True,
                                      on_delete=models.SET_NULL,
                                      related_name='data_exports')
    export_type = models.CharField(max_length=100,
                                    help_text='e.g. full_export, invoices_csv')
    status = models.CharField(max_length=12, choices=StatusChoices.choices,
                               default=StatusChoices.PENDING)
    file_url = models.URLField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    error_detail = models.TextField(blank=True)

    class Meta:
        db_table = 'infrastructure_dataexportlog'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'{self.export_type} ({self.status})'


class EmailDeliveryLog(TenantModel):
    """
    Delivery status record for each outbound email.
    Source: Data Models V6, Section 3.7.
    """

    class StatusChoices(models.TextChoices):
        QUEUED = 'Queued', 'Queued'
        SENT = 'Sent', 'Sent'
        DELIVERED = 'Delivered', 'Delivered'
        BOUNCED = 'Bounced', 'Bounced'
        FAILED = 'Failed', 'Failed'
        SPAM = 'Spam', 'Spam'

    recipient_email = models.EmailField()
    subject = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.QUEUED)
    sent_at = models.DateTimeField(null=True, blank=True)
    provider_message_id = models.CharField(max_length=200, blank=True)
    error_detail = models.TextField(blank=True)

    # Optional trigger link
    trigger_log = models.ForeignKey('automation.TriggerLog', null=True, blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name='email_deliveries')

    class Meta:
        db_table = 'infrastructure_emaildeliverylog'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'recipient_email']),
        ]

    def __str__(self):
        return f'{self.recipient_email} — {self.subject} ({self.status})'


# ---------------------------------------------------------------------------
# Stripe Integration
# ---------------------------------------------------------------------------

class StripeConnection(TenantModel):
    """
    Stripe account connection for a tenant.
    Source: Data Models V6, Section 3.7.
    """

    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=False)
    connected_at = models.DateTimeField(null=True, blank=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'infrastructure_stripeconnection'
        indexes = [
            models.Index(fields=['tenant_id']),
        ]

    def __str__(self):
        return f'{self.tenant_id} — {self.stripe_customer_id}'


class StripeResponse(TenantModel):
    """
    Raw Stripe API response payload storage.
    Source: Data Models V6, Section 3.7.
    """

    stripe_object_type = models.CharField(max_length=100,
                                           help_text='e.g. customer, subscription, invoice')
    stripe_object_id = models.CharField(max_length=100)
    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'infrastructure_striperesponse'
        indexes = [
            models.Index(fields=['tenant_id', 'stripe_object_type']),
        ]

    def __str__(self):
        return f'{self.stripe_object_type} {self.stripe_object_id}'


class StripeLog(TenantModel):
    """
    High-level log of significant Stripe lifecycle events.
    Source: Data Models V6, Section 3.7.
    """

    event_type = models.CharField(max_length=100)
    stripe_object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'infrastructure_stripelog'
        indexes = [
            models.Index(fields=['tenant_id', 'event_type']),
        ]

    def __str__(self):
        return f'{self.event_type} — {self.stripe_object_id}'


class StripeConnectionLog(TenantModel):
    """
    Audit log of Stripe connection / disconnection events.
    Source: Data Models V6, Section 3.7.
    """

    action = models.CharField(max_length=50,
                               help_text='e.g. connected, disconnected, updated')
    actor = models.ForeignKey('users.User', null=True, blank=True,
                               on_delete=models.SET_NULL,
                               related_name='stripe_connection_logs')
    detail = models.TextField(blank=True)

    class Meta:
        db_table = 'infrastructure_stripeconnectionlog'
        indexes = [
            models.Index(fields=['tenant_id']),
        ]

    def __str__(self):
        return f'{self.action} @ {self.created_on}'


class StripeAPIRequestLog(TenantModel):
    """
    Low-level log of every outbound Stripe API call.
    Source: Data Models V6, Section 3.7.
    """

    class StatusChoices(models.TextChoices):
        SUCCESS = 'Success', 'Success'
        FAILED = 'Failed', 'Failed'

    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.SUCCESS)
    http_status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'infrastructure_stripeapirequestlog'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'{self.method} {self.endpoint} ({self.status})'


# ---------------------------------------------------------------------------
# Webhook & Error Tracking
# ---------------------------------------------------------------------------

class WebhookLog(TenantModel):
    """
    Inbound webhook event log (Stripe, Pusher, etc.).
    Source: Data Models V6, Section 3.7.
    """

    class StatusChoices(models.TextChoices):
        RECEIVED = 'Received', 'Received'
        PROCESSED = 'Processed', 'Processed'
        FAILED = 'Failed', 'Failed'
        IGNORED = 'Ignored', 'Ignored'

    source = models.CharField(max_length=50,
                               help_text='e.g. stripe, pusher, internal')
    event_type = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.RECEIVED)
    raw_payload = models.JSONField(default=dict, blank=True)
    error_detail = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'infrastructure_webhooklog'
        indexes = [
            models.Index(fields=['tenant_id', 'source', 'event_type']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'{self.source} {self.event_type} ({self.status})'


class ErrorCode(models.Model):
    """
    Lookup table of application error codes and their descriptions.
    Global (not tenant-scoped).
    Source: Data Models V6, Section 3.7.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100, blank=True)
    message_template = models.TextField()
    description = models.TextField(blank=True)
    is_user_facing = models.BooleanField(default=False)

    class Meta:
        db_table = 'infrastructure_errorcode'

    def __str__(self):
        return f'[{self.code}] {self.message_template[:80]}'


class ProcessTransaction(TenantModel):
    """
    Idempotency record for background jobs / task processing.
    Source: Data Models V6, Section 3.7.
    """

    class StatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        PROCESSING = 'Processing', 'Processing'
        COMPLETED = 'Completed', 'Completed'
        FAILED = 'Failed', 'Failed'

    idempotency_key = models.CharField(max_length=200)
    process_name = models.CharField(max_length=200)
    status = models.CharField(max_length=12, choices=StatusChoices.choices,
                               default=StatusChoices.PENDING)
    payload = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error_detail = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'infrastructure_processtransaction'
        unique_together = [('tenant_id', 'idempotency_key')]
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'{self.process_name} ({self.status})'


class NavigationAudit(TenantModel):
    """
    Per-request navigation log for analytics and security review.
    Source: Data Models V6, Section 1.10.
    """

    user = models.ForeignKey('users.User', null=True, blank=True,
                              on_delete=models.SET_NULL,
                              related_name='navigation_audits')
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10, default='GET')
    http_status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    response_ms = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'infrastructure_navigationaudit'
        indexes = [
            models.Index(fields=['tenant_id', 'user_id']),
            models.Index(fields=['tenant_id', 'created_on']),
        ]

    def __str__(self):
        return f'{self.method} {self.path} ({self.http_status_code})'
