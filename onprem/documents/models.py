# documents/models.py
# Source: Note & Document Implementation Specification V1
#
# EXCLUSIVE ARC pattern with 25 nullable parent FKs directly on the model.
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).
#
# Models:
#   Document — file attachment with immutable metadata and virus scan status
#   FileUploadLog — audit log for upload operations
#   FileDownloadLog — immutable audit log for download operations

import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from config.base_models import TenantModel, ExclusiveArcMixin, PARENT_FK_FIELDS


# ==============================================================================
# ScanStatus enum
# ==============================================================================

class ScanStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CLEAN = 'clean', 'Clean'
    INFECTED = 'infected', 'Infected'


# ==============================================================================
# Document model - extends TenantModel, ExclusiveArcMixin
# ==============================================================================

class Document(ExclusiveArcMixin, TenantModel):
    """
    Document model with exclusive arc pattern and immutable file metadata.

    A Document must be attached to exactly one parent entity. File metadata
    (original_filename, file_key, file_size_bytes, mime_type, sha256_hash)
    cannot be changed after creation. Only scan_status can be updated.
    """

    original_filename = models.CharField(max_length=255)
    file_key = models.CharField(max_length=500)  # S3 key, internal only
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    sha256_hash = models.CharField(max_length=64, blank=True)
    scan_status = models.CharField(
        max_length=20,
        choices=ScanStatus.choices,
        default=ScanStatus.PENDING
    )

    # 25 nullable parent FKs (exactly one must be set)
    # related_name='document_records' avoids potential clashes with model fields.
    customer = models.ForeignKey(
        'crm.Customer',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    contact = models.ForeignKey(
        'crm.Contact',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    lead = models.ForeignKey(
        'crm.Lead',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    opportunity = models.ForeignKey(
        'crm.Opportunity',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    quote = models.ForeignKey(
        'service.Quote',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    invoice = models.ForeignKey(
        'service.Invoice',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    work_order = models.ForeignKey(
        'service.WorkOrder',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    asset = models.ForeignKey(
        'maintenance.Asset',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    service_request = models.ForeignKey(
        'service.ServiceRequest',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    prev_maint = models.ForeignKey(
        'maintenance.PreventativeMaintenance',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    workflow = models.ForeignKey(
        'automation.WorkFlow',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    payment = models.ForeignKey(
        'service.Payments',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    vendor = models.ForeignKey(
        'procurement.Vendor',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    purchase_order = models.ForeignKey(
        'procurement.PurchaseOrder',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    work_group = models.ForeignKey(
        'workforce.WorkGroup',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    vehicle = models.ForeignKey(
        'fleet.Vehicle',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    warehouse = models.ForeignKey(
        'warehouse.Warehouse',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    ledger = models.ForeignKey(
        'service.Ledger',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    requisition = models.ForeignKey(
        'procurement.Requisition',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    rma = models.ForeignKey(
        'procurement.RMA',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    equipment = models.ForeignKey(
        'automation.Equipment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    safety_form = models.ForeignKey(
        'automation.SafetyForm',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )
    vendor_bill = models.ForeignKey(
        'procurement.VendorBill',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_records'
    )

    class Meta:
        db_table = 'documents_document'
        indexes = [
            # Partial indexes per parent FK
            models.Index(
                fields=['tenant_id', 'customer_id'],
                condition=models.Q(customer_id__isnull=False),
                name='doc_customer_idx'
            ),
            models.Index(
                fields=['tenant_id', 'contact_id'],
                condition=models.Q(contact_id__isnull=False),
                name='doc_contact_idx'
            ),
            models.Index(
                fields=['tenant_id', 'lead_id'],
                condition=models.Q(lead_id__isnull=False),
                name='doc_lead_idx'
            ),
            models.Index(
                fields=['tenant_id', 'opportunity_id'],
                condition=models.Q(opportunity_id__isnull=False),
                name='doc_opportunity_idx'
            ),
            models.Index(
                fields=['tenant_id', 'quote_id'],
                condition=models.Q(quote_id__isnull=False),
                name='doc_quote_idx'
            ),
            models.Index(
                fields=['tenant_id', 'invoice_id'],
                condition=models.Q(invoice_id__isnull=False),
                name='doc_invoice_idx'
            ),
            models.Index(
                fields=['tenant_id', 'work_order_id'],
                condition=models.Q(work_order_id__isnull=False),
                name='doc_work_order_idx'
            ),
            models.Index(
                fields=['tenant_id', 'asset_id'],
                condition=models.Q(asset_id__isnull=False),
                name='doc_asset_idx'
            ),
            models.Index(
                fields=['tenant_id', 'service_request_id'],
                condition=models.Q(service_request_id__isnull=False),
                name='doc_service_request_idx'
            ),
            models.Index(
                fields=['tenant_id', 'prev_maint_id'],
                condition=models.Q(prev_maint_id__isnull=False),
                name='doc_prev_maint_idx'
            ),
            models.Index(
                fields=['tenant_id', 'payment_id'],
                condition=models.Q(payment_id__isnull=False),
                name='doc_payment_idx'
            ),
            models.Index(
                fields=['tenant_id', 'user_id'],
                condition=models.Q(user_id__isnull=False),
                name='doc_user_idx'
            ),
            models.Index(
                fields=['tenant_id', 'vendor_id'],
                condition=models.Q(vendor_id__isnull=False),
                name='doc_vendor_idx'
            ),
            models.Index(
                fields=['tenant_id', 'purchase_order_id'],
                condition=models.Q(purchase_order_id__isnull=False),
                name='doc_purchase_order_idx'
            ),
            models.Index(
                fields=['tenant_id', 'work_group_id'],
                condition=models.Q(work_group_id__isnull=False),
                name='doc_work_group_idx'
            ),
            models.Index(
                fields=['tenant_id', 'task_id'],
                condition=models.Q(task_id__isnull=False),
                name='doc_task_idx'
            ),
            models.Index(
                fields=['tenant_id', 'vehicle_id'],
                condition=models.Q(vehicle_id__isnull=False),
                name='doc_vehicle_idx'
            ),
            models.Index(
                fields=['tenant_id', 'warehouse_id'],
                condition=models.Q(warehouse_id__isnull=False),
                name='doc_warehouse_idx'
            ),
            models.Index(
                fields=['tenant_id', 'ledger_id'],
                condition=models.Q(ledger_id__isnull=False),
                name='doc_ledger_idx'
            ),
            models.Index(
                fields=['tenant_id', 'requisition_id'],
                condition=models.Q(requisition_id__isnull=False),
                name='doc_requisition_idx'
            ),
            models.Index(
                fields=['tenant_id', 'workflow_id'],
                condition=models.Q(workflow_id__isnull=False),
                name='doc_workflow_idx'
            ),
            models.Index(
                fields=['tenant_id', 'rma_id'],
                condition=models.Q(rma_id__isnull=False),
                name='doc_rma_idx'
            ),
            models.Index(
                fields=['tenant_id', 'equipment_id'],
                condition=models.Q(equipment_id__isnull=False),
                name='doc_equipment_idx'
            ),
            models.Index(
                fields=['tenant_id', 'safety_form_id'],
                condition=models.Q(safety_form_id__isnull=False),
                name='doc_safety_form_idx'
            ),
            models.Index(
                fields=['tenant_id', 'vendor_bill_id'],
                condition=models.Q(vendor_bill_id__isnull=False),
                name='doc_vendor_bill_idx'
            ),
        ]

    def save(self, *args, **kwargs):
        """
        Override save() to enforce immutability of file metadata.

        File metadata fields (original_filename, file_key, file_size_bytes,
        mime_type, sha256_hash) cannot be changed after creation.
        Only scan_status can be updated.
        """
        if self.pk and not self._state.adding:
            # Fetch the existing record to detect changes
            existing = Document.all_objects.get(pk=self.pk)

            if self.original_filename != existing.original_filename:
                raise ValidationError("Cannot modify original_filename after creation.")
            if self.file_key != existing.file_key:
                raise ValidationError("Cannot modify file_key after creation.")
            if self.file_size_bytes != existing.file_size_bytes:
                raise ValidationError("Cannot modify file_size_bytes after creation.")
            if self.mime_type != existing.mime_type:
                raise ValidationError("Cannot modify mime_type after creation.")
            if self.sha256_hash != existing.sha256_hash:
                raise ValidationError("Cannot modify sha256_hash after creation.")

        # Call parent's save() which includes ExclusiveArcMixin.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Document ({self.original_filename})"


# ==============================================================================
# FileUploadLog model - extends TenantModel
# ==============================================================================

class FileUploadLog(TenantModel):
    """
    Audit log for file upload operations.

    Records the outcome of each upload attempt: success, failure, or rejection.
    """

    class StatusChoices(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        REJECTED = 'rejected', 'Rejected'

    document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='upload_logs'
    )
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    original_filename = models.CharField(max_length=255)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices)
    failure_reason = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'documents_file_upload_log'
        indexes = [
            models.Index(fields=['tenant_id', 'entity_type', 'entity_id']),
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['created_on']),
        ]

    def __str__(self):
        return f"Upload ({self.original_filename}) - {self.status}"


# ==============================================================================
# FileDownloadLog model - NOT TenantModel, immutable raw fields
# ==============================================================================

class FileDownloadLog(models.Model):
    """
    Immutable audit log for file download operations.

    This is NOT a TenantModel. It has immutable raw fields (no edited_by/on).
    Records are append-only; they cannot be modified or deleted after creation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)  # Plain field, not a FK
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    user_id = models.UUIDField()  # Plain field, not a FK
    user_display = models.CharField(max_length=200)
    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name='download_logs'
    )
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'documents_file_download_log'
        default_permissions = ()
        indexes = [
            models.Index(fields=['tenant_id', 'document_id']),
            models.Index(fields=['tenant_id', 'user_id']),
            models.Index(fields=['timestamp']),
        ]

    def save(self, *args, **kwargs):
        """Immutability: prevent updates after creation."""
        if not self._state.adding:
            raise ValidationError("FileDownloadLog records are immutable and cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Immutability: prevent deletion."""
        raise ValidationError("FileDownloadLog records are immutable and cannot be deleted.")

    def __str__(self):
        return f"Download ({self.document.original_filename}) by {self.user_display}"
