# notes/models.py
# Source: Note & Document Implementation Specification V1
#
# EXCLUSIVE ARC pattern with 25 nullable parent FKs directly on the model.
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

from django.db import models
from django.conf import settings
from config.base_models import TenantModel, ExclusiveArcMixin, PARENT_FK_FIELDS
from documents.models import Document, FileUploadLog, FileDownloadLog, ScanStatus


# ==============================================================================
# NoteType enum
# ==============================================================================

class NoteType(models.TextChoices):
    INTERNAL_NOTE = 'internal_note', 'Internal Note'
    CALL = 'call', 'Call'
    EMAIL = 'email', 'Email'
    SITE_VISIT = 'site_visit', 'Site Visit'
    CUSTOMER_COMMENT = 'customer_comment', 'Customer Comment'
    REMINDER = 'reminder', 'Reminder'


NoteType.choices_dict = dict(NoteType.choices)


# ==============================================================================
# Note model - extends TenantModel, ExclusiveArcMixin
# ==============================================================================

class Note(ExclusiveArcMixin, TenantModel):
    """
    Note model with exclusive arc pattern.

    A Note must be attached to exactly one parent entity (customer, contact,
    work_order, etc.). The 25 nullable parent FKs enforce this via clean() validation
    and a database CHECK constraint applied via migration.
    """

    note_type = models.CharField(
        max_length=50,
        choices=NoteType.choices,
        default=NoteType.INTERNAL_NOTE
    )
    body = models.TextField()

    # 25 nullable parent FKs (exactly one must be set)
    # related_name='note_records' avoids clash with `notes` TextField on target models.
    customer = models.ForeignKey(
        'crm.Customer',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    contact = models.ForeignKey(
        'crm.Contact',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    lead = models.ForeignKey(
        'crm.Lead',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    opportunity = models.ForeignKey(
        'crm.Opportunity',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    quote = models.ForeignKey(
        'service.Quote',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    invoice = models.ForeignKey(
        'service.Invoice',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    work_order = models.ForeignKey(
        'service.WorkOrder',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    asset = models.ForeignKey(
        'maintenance.Asset',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    service_request = models.ForeignKey(
        'service.ServiceRequest',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    prev_maint = models.ForeignKey(
        'maintenance.PreventativeMaintenance',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    workflow = models.ForeignKey(
        'automation.WorkFlow',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    payment = models.ForeignKey(
        'service.Payments',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    purchase_order = models.ForeignKey(
        'procurement.PurchaseOrder',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    work_group = models.ForeignKey(
        'workforce.WorkGroup',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    vehicle = models.ForeignKey(
        'fleet.Vehicle',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    warehouse = models.ForeignKey(
        'warehouse.Warehouse',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    ledger = models.ForeignKey(
        'service.Ledger',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    requisition = models.ForeignKey(
        'procurement.Requisition',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    rma = models.ForeignKey(
        'procurement.RMA',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    equipment = models.ForeignKey(
        'automation.Equipment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    safety_form = models.ForeignKey(
        'automation.SafetyForm',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )
    vendor_bill = models.ForeignKey(
        'procurement.VendorBill',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='note_records'
    )

    class Meta:
        db_table = 'notes_note'
        indexes = [
            # Partial indexes per parent FK
            models.Index(
                fields=['tenant_id', 'customer_id'],
                condition=models.Q(customer_id__isnull=False),
                name='note_customer_idx'
            ),
            models.Index(
                fields=['tenant_id', 'contact_id'],
                condition=models.Q(contact_id__isnull=False),
                name='note_contact_idx'
            ),
            models.Index(
                fields=['tenant_id', 'lead_id'],
                condition=models.Q(lead_id__isnull=False),
                name='note_lead_idx'
            ),
            models.Index(
                fields=['tenant_id', 'opportunity_id'],
                condition=models.Q(opportunity_id__isnull=False),
                name='note_opportunity_idx'
            ),
            models.Index(
                fields=['tenant_id', 'quote_id'],
                condition=models.Q(quote_id__isnull=False),
                name='note_quote_idx'
            ),
            models.Index(
                fields=['tenant_id', 'invoice_id'],
                condition=models.Q(invoice_id__isnull=False),
                name='note_invoice_idx'
            ),
            models.Index(
                fields=['tenant_id', 'work_order_id'],
                condition=models.Q(work_order_id__isnull=False),
                name='note_work_order_idx'
            ),
            models.Index(
                fields=['tenant_id', 'asset_id'],
                condition=models.Q(asset_id__isnull=False),
                name='note_asset_idx'
            ),
            models.Index(
                fields=['tenant_id', 'service_request_id'],
                condition=models.Q(service_request_id__isnull=False),
                name='note_service_request_idx'
            ),
            models.Index(
                fields=['tenant_id', 'prev_maint_id'],
                condition=models.Q(prev_maint_id__isnull=False),
                name='note_prev_maint_idx'
            ),
            models.Index(
                fields=['tenant_id', 'payment_id'],
                condition=models.Q(payment_id__isnull=False),
                name='note_payment_idx'
            ),
            models.Index(
                fields=['tenant_id', 'user_id'],
                condition=models.Q(user_id__isnull=False),
                name='note_user_idx'
            ),
            models.Index(
                fields=['tenant_id', 'vendor_id'],
                condition=models.Q(vendor_id__isnull=False),
                name='note_vendor_idx'
            ),
            models.Index(
                fields=['tenant_id', 'purchase_order_id'],
                condition=models.Q(purchase_order_id__isnull=False),
                name='note_purchase_order_idx'
            ),
            models.Index(
                fields=['tenant_id', 'work_group_id'],
                condition=models.Q(work_group_id__isnull=False),
                name='note_work_group_idx'
            ),
            models.Index(
                fields=['tenant_id', 'task_id'],
                condition=models.Q(task_id__isnull=False),
                name='note_task_idx'
            ),
            models.Index(
                fields=['tenant_id', 'vehicle_id'],
                condition=models.Q(vehicle_id__isnull=False),
                name='note_vehicle_idx'
            ),
            models.Index(
                fields=['tenant_id', 'warehouse_id'],
                condition=models.Q(warehouse_id__isnull=False),
                name='note_warehouse_idx'
            ),
            models.Index(
                fields=['tenant_id', 'ledger_id'],
                condition=models.Q(ledger_id__isnull=False),
                name='note_ledger_idx'
            ),
            models.Index(
                fields=['tenant_id', 'requisition_id'],
                condition=models.Q(requisition_id__isnull=False),
                name='note_requisition_idx'
            ),
            models.Index(
                fields=['tenant_id', 'workflow_id'],
                condition=models.Q(workflow_id__isnull=False),
                name='note_workflow_idx'
            ),
            models.Index(
                fields=['tenant_id', 'rma_id'],
                condition=models.Q(rma_id__isnull=False),
                name='note_rma_idx'
            ),
            models.Index(
                fields=['tenant_id', 'equipment_id'],
                condition=models.Q(equipment_id__isnull=False),
                name='note_equipment_idx'
            ),
            models.Index(
                fields=['tenant_id', 'safety_form_id'],
                condition=models.Q(safety_form_id__isnull=False),
                name='note_safety_form_idx'
            ),
            models.Index(
                fields=['tenant_id', 'vendor_bill_id'],
                condition=models.Q(vendor_bill_id__isnull=False),
                name='note_vendor_bill_idx'
            ),
        ]

    def __str__(self):
        return f"Note ({self.note_type}) - {self.created_on}"
