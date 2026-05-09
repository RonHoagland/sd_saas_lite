# service/models.py
# Source: Data Models V6, Sections 1.4, 1.5, 2.6.
#
# Models in this app:
#   ServiceRequest, WorkOrder, WorkOrderTeam, WorkOrderLine,
#   Quote, QuoteLine, QuoteAsset,
#   Invoice, InvoiceLine, InvoiceAsset, WorkOrderInvoice,
#   Payments, Bank, Accounting, Ledger
#
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

from decimal import Decimal
from django.db import models
from config.base_models import TenantModel
from numbering.mixins import NumberingMixin
from lifecycle.mixins import LifecycleMixin


# ---------------------------------------------------------------------------
# Service Requests & Work Orders
# ---------------------------------------------------------------------------

class ServiceRequest(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Customer-facing request for service.  Previously called TroubleCall in v1.
    Source: Data Models V6, Section 1.4.
    """
    numbering_entity_type = 'service_request'
    lifecycle_entity_type = 'service_request'

    class StatusChoices(models.TextChoices):
        NEW = 'New', 'New'
        ASSIGNED = 'Assigned', 'Assigned'
        IN_PROGRESS = 'In Progress', 'In Progress'
        ON_HOLD = 'On Hold', 'On Hold'
        RESOLVED = 'Resolved', 'Resolved'
        CLOSED = 'Closed', 'Closed'
        CANCELLED = 'Cancelled', 'Cancelled'

    class PriorityChoices(models.TextChoices):
        LOW = 'Low', 'Low'
        MEDIUM = 'Medium', 'Medium'
        HIGH = 'High', 'High'
        CRITICAL = 'Critical', 'Critical'

    request_number = models.CharField(max_length=20, blank=True)
    customer = models.ForeignKey('crm.Customer', on_delete=models.RESTRICT,
                                  related_name='service_requests')
    contact = models.ForeignKey('crm.Contact', null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='service_requests')
    asset = models.ForeignKey('maintenance.Asset', null=True, blank=True,
                               on_delete=models.SET_NULL,
                               related_name='service_requests')
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.NEW)
    priority = models.CharField(max_length=10, choices=PriorityChoices.choices,
                                 default=PriorityChoices.MEDIUM)
    subject = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    requested_date = models.DateField(null=True, blank=True)
    resolved_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey('users.User', null=True, blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name='assigned_service_requests')
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'service_servicerequest'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'customer_id']),
        ]

    def __str__(self):
        return f'[{self.request_number}] {self.subject}'

    def _apply_lifecycle_transition(self, *, from_state, to_state, reason, user):
        """Sync resolved_date with the audit log on lifecycle transitions.
        Called by ``lifecycle.services.execute_transition``.
        See Customer._apply_lifecycle_transition for the full pattern."""
        from django.utils import timezone
        if from_state == self.StatusChoices.RESOLVED and to_state != self.StatusChoices.RESOLVED:
            self.resolved_date = None
        if to_state == self.StatusChoices.RESOLVED:
            self.resolved_date = timezone.now().date()


class WorkOrder(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Internal work order generated from a ServiceRequest.
    Source: Data Models V6, Section 1.4.
    """
    numbering_entity_type = 'work_order'
    lifecycle_entity_type = 'work_order'

    class StatusChoices(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        SCHEDULED = 'Scheduled', 'Scheduled'
        IN_PROGRESS = 'In Progress', 'In Progress'
        ON_HOLD = 'On Hold', 'On Hold'
        COMPLETED = 'Completed', 'Completed'
        CANCELLED = 'Cancelled', 'Cancelled'

    class PriorityChoices(models.TextChoices):
        LOW = 'Low', 'Low'
        MEDIUM = 'Medium', 'Medium'
        HIGH = 'High', 'High'
        CRITICAL = 'Critical', 'Critical'

    wo_number = models.CharField(max_length=20, blank=True)
    service_request = models.ForeignKey(ServiceRequest, null=True, blank=True,
                                         on_delete=models.SET_NULL,
                                         related_name='work_orders')
    customer = models.ForeignKey('crm.Customer', on_delete=models.RESTRICT,
                                  related_name='work_orders')
    asset = models.ForeignKey('maintenance.Asset', null=True, blank=True,
                               on_delete=models.SET_NULL,
                               related_name='work_orders')
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.DRAFT)
    priority = models.CharField(max_length=10, choices=PriorityChoices.choices,
                                 default=PriorityChoices.MEDIUM)
    subject = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey('users.User', null=True, blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name='assigned_work_orders')
    estimated_hours = models.DecimalField(max_digits=8, decimal_places=2,
                                           null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tags = models.JSONField(default=list, blank=True)

    # Hold status fields (System Status V3 §5)
    hold_date = models.DateTimeField(null=True, blank=True)  # Recorded when status → On Hold
    hold_reason = models.TextField(blank=True)  # Required when status=On Hold

    # Plus+ features
    customer_facing_notes = models.TextField(blank=True)  # Customer-visible notes (Plus+ customer portal)
    recurrence_pattern = models.JSONField(default=dict, blank=True)  # Plus+ recurring work orders

    class Meta:
        db_table = 'service_workorder'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'customer_id']),
        ]

    def recalculate_totals(self):
        """Calculate total_amount from lines."""
        totals = self.lines.aggregate(
            total=models.Sum('line_total')
        )
        self.total_amount = totals['total'] or 0
        self.save(update_fields=['total_amount'])

    def save(self, *args, **kwargs):
        # Defense-in-depth (mirrors Customer.save()): On Hold requires a
        # reason per System Status V3 §5. The lifecycle service enforces this
        # on transitions; this guard catches direct status writes that bypass
        # the lifecycle service.
        if self.status == self.StatusChoices.ON_HOLD and not self.hold_reason:
            from django.core.exceptions import ValidationError
            raise ValidationError({'hold_reason': 'Required when status is On Hold.'})
        super().save(*args, **kwargs)

    def __str__(self):
        return f'WO {self.wo_number} — {self.subject}'

    def _apply_lifecycle_transition(self, *, from_state, to_state, reason, user):
        """Sync hold_date / hold_reason / completed_date with the audit log.
        Called by ``lifecycle.services.execute_transition``.
        See Customer._apply_lifecycle_transition for the full pattern."""
        from django.utils import timezone
        now = timezone.now()
        if from_state == self.StatusChoices.ON_HOLD and to_state != self.StatusChoices.ON_HOLD:
            self.hold_date = None
            self.hold_reason = ''
        if from_state == self.StatusChoices.COMPLETED and to_state != self.StatusChoices.COMPLETED:
            self.completed_date = None
        if to_state == self.StatusChoices.ON_HOLD:
            self.hold_date = now
            self.hold_reason = reason or ''
        elif to_state == self.StatusChoices.COMPLETED:
            self.completed_date = now.date()


class WorkOrderTeam(TenantModel):
    """
    Team members assigned to a WorkOrder.
    Source: Data Models V6, Section 1.4.
    """

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE,
                                    related_name='team_members')
    user = models.ForeignKey('users.User', on_delete=models.RESTRICT,
                              related_name='work_order_assignments')
    role = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'service_workorderteam'
        unique_together = [('work_order', 'user')]
        indexes = [
            models.Index(fields=['tenant_id', 'work_order_id']),
        ]

    def __str__(self):
        return f'{self.work_order} → {self.user}'


class WorkOrderLine(TenantModel):
    """
    Parts / labor line items on a WorkOrder.
    Source: Data Models V6, Section 1.4.
    """

    class LineTypeChoices(models.TextChoices):
        PART = 'Part', 'Part'
        LABOR = 'Labor', 'Labor'
        OTHER = 'Other', 'Other'

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE,
                                    related_name='lines')
    line_type = models.CharField(max_length=10, choices=LineTypeChoices.choices,
                                  default=LineTypeChoices.PART)
    product = models.ForeignKey('inventory.InventoryItem', null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='work_order_lines')
    description = models.CharField(max_length=300, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = 'service_workorderline'
        indexes = [
            models.Index(fields=['tenant_id', 'work_order_id']),
        ]

    def save(self, *args, **kwargs):
        """Automate line_total calculation and update WorkOrder total."""
        quantity_dec = self.quantity if isinstance(self.quantity, Decimal) else Decimal(str(self.quantity or 0))
        unit_price_dec = self.unit_price if isinstance(self.unit_price, Decimal) else Decimal(str(self.unit_price or 0))
        self.quantity = quantity_dec
        self.unit_price = unit_price_dec
        self.line_total = (quantity_dec * unit_price_dec).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)
        if self.work_order:
            self.work_order.recalculate_totals()

    def __str__(self):
        return f'{self.work_order} — {self.description or self.product}'


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------

class Quote(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Customer quote (estimate) for services.
    Source: Data Models V6, Section 1.5.
    """
    numbering_entity_type = 'quote'
    lifecycle_entity_type = 'quote'

    class StatusChoices(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        SENT = 'Sent', 'Sent'
        ACCEPTED = 'Accepted', 'Accepted'
        DECLINED = 'Declined', 'Declined'
        EXPIRED = 'Expired', 'Expired'
        INVOICED = 'Invoiced', 'Invoiced'

    quote_number = models.CharField(max_length=20, blank=True)
    work_order = models.ForeignKey(WorkOrder, null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='quotes')
    customer = models.ForeignKey('crm.Customer', on_delete=models.RESTRICT,
                                  related_name='quotes')
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.DRAFT)
    quote_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # ── Lifecycle context (set by _apply_lifecycle_transition) ──
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    declined_reason = models.TextField(blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    invoiced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'service_quote'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'customer_id']),
        ]

    def recalculate_totals(self):
        """
        Recalculates subtotal, tax_amount, and total based on lines.
        """
        D2 = Decimal('0.01')
        raw_subtotal = sum((line.line_total for line in self.lines.all()), Decimal('0.00'))
        subtotal_dec = raw_subtotal if isinstance(raw_subtotal, Decimal) else Decimal(str(raw_subtotal or 0))
        tax_rate_dec = self.tax_rate if isinstance(self.tax_rate, Decimal) else Decimal(str(self.tax_rate or 0))

        self.subtotal = subtotal_dec.quantize(D2)
        self.tax_amount = (subtotal_dec * tax_rate_dec).quantize(D2)
        self.total = (self.subtotal + self.tax_amount).quantize(D2)

    def save(self, *args, **kwargs):
        """Enforce total recalculation if context allows."""
        # Note: In a real production scenario, we might use a signal or a more selective
        # recalculation to avoid N+1 queries during bulk saves.
        if self.pk:
            self.recalculate_totals()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Quote {self.quote_number} — {self.customer}'

    def _apply_lifecycle_transition(self, *, from_state, to_state, reason, user):
        """Sync lifecycle context fields. Quote lifecycle is forward-only —
        no clearing of timestamps when leaving a state."""
        from django.utils import timezone
        now = timezone.now()
        if to_state == self.StatusChoices.SENT:
            self.sent_at = now
        elif to_state == self.StatusChoices.ACCEPTED:
            self.accepted_at = now
        elif to_state == self.StatusChoices.DECLINED:
            self.declined_at = now
            self.declined_reason = reason or ''
        elif to_state == self.StatusChoices.EXPIRED:
            self.expired_at = now
        elif to_state == self.StatusChoices.INVOICED:
            self.invoiced_at = now


class QuoteLine(TenantModel):
    """
    Line items on a Quote.
    Source: Data Models V6, Section 1.5.
    """

    class LineTypeChoices(models.TextChoices):
        PART = 'Part', 'Part'
        LABOR = 'Labor', 'Labor'
        OTHER = 'Other', 'Other'

    quote = models.ForeignKey(Quote, on_delete=models.CASCADE,
                               related_name='lines')
    line_type = models.CharField(max_length=10, choices=LineTypeChoices.choices,
                                  default=LineTypeChoices.PART)
    product = models.ForeignKey('inventory.InventoryItem', null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='quote_lines')
    description = models.CharField(max_length=300, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = 'service_quoteline'
        indexes = [
            models.Index(fields=['tenant_id', 'quote_id']),
        ]

    def save(self, *args, **kwargs):
        """Automate line_total calculation and update Quote totals."""
        quantity_dec = self.quantity if isinstance(self.quantity, Decimal) else Decimal(str(self.quantity or 0))
        unit_price_dec = self.unit_price if isinstance(self.unit_price, Decimal) else Decimal(str(self.unit_price or 0))
        self.quantity = quantity_dec
        self.unit_price = unit_price_dec
        self.line_total = (quantity_dec * unit_price_dec).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)
        if self.quote:
            self.quote.recalculate_totals()
            self.quote.save()

    def __str__(self):
        return f'{self.quote} — {self.description or self.product}'


class QuoteAsset(TenantModel):
    """
    Assets referenced on a Quote.
    Source: Data Models V6, Section 1.5.
    """

    quote = models.ForeignKey(Quote, on_delete=models.CASCADE,
                               related_name='assets')
    asset = models.ForeignKey('maintenance.Asset', on_delete=models.RESTRICT,
                               related_name='quote_references')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'service_quoteasset'
        indexes = [
            models.Index(fields=['tenant_id', 'quote_id']),
        ]

    def __str__(self):
        return f'{self.quote} → {self.asset}'


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------

class Invoice(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Customer invoice for completed work.
    Source: Data Models V6, Section 2.6.
    """
    numbering_entity_type = 'invoice'
    lifecycle_entity_type = 'invoice'

    class StatusChoices(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        SENT = 'Sent', 'Sent'
        PARTIAL = 'Partial', 'Partial'
        PAID = 'Paid', 'Paid'
        OVERDUE = 'Overdue', 'Overdue'
        VOIDED = 'Voided', 'Voided'

    invoice_number = models.CharField(max_length=20, blank=True)
    customer = models.ForeignKey('crm.Customer', on_delete=models.RESTRICT,
                                  related_name='invoices')
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.DRAFT)
    invoice_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Stripe integration (Invoice Payment Specification V1)
    stripe_payment_link_url = models.URLField(blank=True)

    # Plus+ deposit flow (quote-to-invoice)
    class DepositTypeChoices(models.TextChoices):
        PERCENTAGE = 'Percentage', 'Percentage'
        FIXED_AMOUNT = 'Fixed Amount', 'Fixed Amount'

    deposit_applied = models.BooleanField(default=False)
    deposit_type = models.CharField(max_length=20,
                                     choices=DepositTypeChoices.choices,
                                     blank=True)
    deposit_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Plus+ recurring billing (Background Tasks V2)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.JSONField(default=dict, blank=True)

    # ── Lifecycle context (set by _apply_lifecycle_transition) ──
    sent_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    overdue_at = models.DateTimeField(null=True, blank=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'service_invoice'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'customer_id']),
        ]

    def recalculate_totals(self):
        """
        Recalculates subtotal, tax_amount, total, and balance_due.
        """
        # Precision constants
        D2 = Decimal('0.01')
        raw_subtotal = sum((line.line_total for line in self.lines.all()), Decimal('0.00'))
        subtotal_dec = raw_subtotal if isinstance(raw_subtotal, Decimal) else Decimal(str(raw_subtotal or 0))
        tax_rate_dec = self.tax_rate if isinstance(self.tax_rate, Decimal) else Decimal(str(self.tax_rate or 0))
        self.subtotal = subtotal_dec.quantize(D2)
        self.tax_amount = (subtotal_dec * tax_rate_dec).quantize(D2)
        self.total = (self.subtotal + self.tax_amount).quantize(D2)
        raw_amount_paid = sum((pmt.amount for pmt in self.payments.filter(
            status__in=[Payments.StatusChoices.APPLIED, Payments.StatusChoices.PAID]
        )), Decimal('0.00'))
        self.amount_paid = (
            raw_amount_paid if isinstance(raw_amount_paid, Decimal)
            else Decimal(str(raw_amount_paid or 0))
        ).quantize(D2)
        self.balance_due = (self.total - self.amount_paid).quantize(D2)

        # Auto-update status based on balance
        if self.total > 0:
            if self.balance_due <= 0:
                self.status = self.StatusChoices.PAID
            elif self.amount_paid > 0:
                self.status = self.StatusChoices.PARTIAL
            else:
                self.status = self.StatusChoices.DRAFT

    def save(self, *args, **kwargs):
        if self.pk:
            self.recalculate_totals()
        # Defense-in-depth: Voided requires voided_reason. Lifecycle service
        # enforces on transitions (rule's requires_reason flag); this catches
        # direct status writes that bypass the lifecycle service.
        if self.status == self.StatusChoices.VOIDED and not self.voided_reason:
            from django.core.exceptions import ValidationError
            raise ValidationError({'voided_reason': 'Required when status is Voided.'})
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Invoice {self.invoice_number} — {self.customer}'

    def _apply_lifecycle_transition(self, *, from_state, to_state, reason, user):
        """Sync lifecycle context fields. Some Invoice transitions are
        reversible (Overdue → Partial/Paid; Partial → Overdue), but the
        timestamps are historical milestones — they stay set even if the
        status moves away."""
        from django.utils import timezone
        now = timezone.now()
        if to_state == self.StatusChoices.SENT:
            self.sent_at = now
        elif to_state == self.StatusChoices.PAID:
            self.paid_at = now
        elif to_state == self.StatusChoices.OVERDUE:
            self.overdue_at = now
        elif to_state == self.StatusChoices.VOIDED:
            self.voided_at = now
            self.voided_reason = reason or ''


class InvoiceLine(TenantModel):
    """
    Line items on an Invoice.
    Source: Data Models V6, Section 2.6.
    """

    class LineTypeChoices(models.TextChoices):
        PART = 'Part', 'Part'
        LABOR = 'Labor', 'Labor'
        OTHER = 'Other', 'Other'

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,
                                 related_name='lines')
    line_type = models.CharField(max_length=10, choices=LineTypeChoices.choices,
                                  default=LineTypeChoices.PART)
    product = models.ForeignKey('inventory.InventoryItem', null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='invoice_lines')
    description = models.CharField(max_length=300, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = 'service_invoiceline'
        indexes = [
            models.Index(fields=['tenant_id', 'invoice_id']),
        ]

    def save(self, *args, **kwargs):
        """Automate line_total calculation and update Invoice totals."""
        quantity_dec = self.quantity if isinstance(self.quantity, Decimal) else Decimal(str(self.quantity or 0))
        unit_price_dec = self.unit_price if isinstance(self.unit_price, Decimal) else Decimal(str(self.unit_price or 0))
        self.quantity = quantity_dec
        self.unit_price = unit_price_dec
        self.line_total = (quantity_dec * unit_price_dec).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)
        if self.invoice:
            self.invoice.recalculate_totals()
            self.invoice.save()

    def __str__(self):
        return f'{self.invoice} — {self.description or self.product}'


class InvoiceAsset(TenantModel):
    """
    Assets referenced on an Invoice.
    Source: Data Models V6, Section 2.6.
    """

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,
                                 related_name='assets')
    asset = models.ForeignKey('maintenance.Asset', on_delete=models.RESTRICT,
                               related_name='invoice_references')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'service_invoiceasset'
        indexes = [
            models.Index(fields=['tenant_id', 'invoice_id']),
        ]

    def __str__(self):
        return f'{self.invoice} → {self.asset}'


class WorkOrderInvoice(TenantModel):
    """
    Links a WorkOrder to one or more Invoices (M2M with metadata).
    Source: Data Models V6, Section 2.6.
    """

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE,
                                    related_name='invoiced_work_orders')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,
                                 related_name='work_order_invoices')

    class Meta:
        db_table = 'service_workinvoice'
        unique_together = [('work_order', 'invoice')]
        indexes = [
            models.Index(fields=['tenant_id', 'work_order_id']),
        ]

    def __str__(self):
        return f'{self.work_order} ↔ {self.invoice}'


# ---------------------------------------------------------------------------
# Payments & Accounting
# ---------------------------------------------------------------------------

class Bank(TenantModel):
    """
    Bank account record for deposit tracking.
    Source: Data Models V6, Section 2.6.
    """

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    name = models.CharField(max_length=200)
    account_number_last4 = models.CharField(max_length=4, blank=True)
    routing_number_last4 = models.CharField(max_length=4, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'service_bank'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return self.name


class Payments(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Payment applied to an Invoice.
    Source: Data Models V6, Section 2.6.
    """
    numbering_entity_type = 'payment'
    lifecycle_entity_type = 'payment'

    class StatusChoices(models.TextChoices):
        OPEN = 'Open', 'Open'
        PENDING = 'Pending', 'Pending'
        PROCESSING = 'Processing', 'Processing'
        ON_HOLD = 'On Hold', 'On Hold'
        PARTIALLY_APPLIED = 'Partially Applied', 'Partially Applied'
        APPLIED = 'Applied', 'Applied'
        PAID = 'Paid', 'Paid'
        RETURNED = 'Returned', 'Returned'
        VOIDED = 'Voided', 'Voided'
        REFUNDED = 'Refunded', 'Refunded'

    class MethodChoices(models.TextChoices):
        CASH = 'Cash', 'Cash'
        CHECK = 'Check', 'Check'
        CREDIT_CARD = 'Credit Card', 'Credit Card'
        ACH = 'ACH', 'ACH'
        OTHER = 'Other', 'Other'

    payment_number = models.CharField(max_length=20, blank=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.RESTRICT,
                                 related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.OPEN,
    )
    method = models.CharField(max_length=20, choices=MethodChoices.choices,
                               default=MethodChoices.CASH)
    reference_number = models.CharField(max_length=100, blank=True)
    bank = models.ForeignKey(Bank, null=True, blank=True,
                              on_delete=models.SET_NULL,
                              related_name='payments')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'service_payments'
        indexes = [
            models.Index(fields=['tenant_id', 'invoice_id']),
        ]

    def save(self, *args, **kwargs):
        """Update parent invoice totals on payment change."""
        super().save(*args, **kwargs)
        if self.invoice:
            self.invoice.save()

    def __str__(self):
        return f'Payment {self.amount} on {self.invoice} ({self.payment_date})'


class Accounting(TenantModel):
    """
    Chart of accounts entry for general ledger categorisation.
    Source: Data Models V6, Section 2.6.
    """

    class AccountTypeChoices(models.TextChoices):
        ASSET = 'Asset', 'Asset'
        LIABILITY = 'Liability', 'Liability'
        EQUITY = 'Equity', 'Equity'
        REVENUE = 'Revenue', 'Revenue'
        EXPENSE = 'Expense', 'Expense'

    account_number = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=AccountTypeChoices.choices)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'service_accounting'
        indexes = [
            models.Index(fields=['tenant_id', 'account_type']),
        ]

    def __str__(self):
        return f'[{self.account_number}] {self.name}'


class Ledger(TenantModel):
    """
    General ledger transaction entry.
    Source: Data Models V6, Section 2.6.
    """

    class EntryTypeChoices(models.TextChoices):
        DEBIT = 'Debit', 'Debit'
        CREDIT = 'Credit', 'Credit'

    account = models.ForeignKey(Accounting, on_delete=models.RESTRICT,
                                 related_name='ledger_entries')
    entry_type = models.CharField(max_length=6, choices=EntryTypeChoices.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    transaction_date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    # Source document links — only one should be set per entry (exclusive arc).
    invoice = models.ForeignKey(Invoice, null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='ledger_entries')
    payment = models.ForeignKey(Payments, null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='ledger_entries')
    vendor_bill = models.ForeignKey('procurement.VendorBill', null=True, blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name='ledger_entries')

    class Meta:
        db_table = 'service_ledger'
        indexes = [
            models.Index(fields=['tenant_id', 'account_id']),
            models.Index(fields=['tenant_id', 'transaction_date']),
        ]

    def __str__(self):
        return f'{self.entry_type} {self.amount} — {self.account} ({self.transaction_date})'
