# documents/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from .models import Document, FileUploadLog, FileDownloadLog


@admin.register(Document)
class DocumentAdmin(TenantModelAdmin):
    list_display = (
        'original_filename',
        'mime_type',
        'file_size_bytes',
        'scan_status',
        'parent_entity',
        'tenant_id',
        'created_on',
        'created_by',
    )
    list_filter = ('tenant_id', 'scan_status', 'mime_type', 'created_on')
    search_fields = ('original_filename', 'created_by')
    readonly_fields = (
        'id', 'tenant_id', 'created_on', 'created_by', 'updated_on', 'updated_by',
        'file_key', 'original_filename', 'file_size_bytes', 'mime_type', 'sha256_hash'
    )

    def parent_entity(self, obj):
        """Show which parent entity the document is attached to."""
        parent_fields = [
            'customer', 'contact', 'lead', 'opportunity', 'quote', 'invoice',
            'work_order', 'asset', 'service_request', 'prev_maint', 'workflow',
            'payment', 'user', 'vendor', 'purchase_order', 'work_group', 'task',
            'vehicle', 'warehouse', 'ledger', 'requisition', 'rma', 'equipment',
            'safety_form', 'vendor_bill',
        ]
        for field in parent_fields:
            fk_value = getattr(obj, f'{field}_id', None)
            if fk_value:
                return f"{field}: {fk_value}"
        return "No parent"
    parent_entity.short_description = 'Parent Entity'


@admin.register(FileUploadLog)
class FileUploadLogAdmin(TenantModelAdmin):
    list_display = (
        'original_filename',
        'entity_type',
        'status',
        'file_size_bytes',
        'tenant_id',
        'created_on',
    )
    list_filter = ('tenant_id', 'status', 'entity_type', 'created_on')
    search_fields = ('original_filename', 'entity_type')
    readonly_fields = (
        'id', 'tenant_id', 'created_on', 'created_by',
        'document', 'entity_type', 'entity_id', 'original_filename',
        'file_size_bytes', 'status', 'failure_reason', 'ip_address'
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FileDownloadLog)
class FileDownloadLogAdmin(admin.ModelAdmin):
    list_display = (
        'document',
        'user_display',
        'entity_type',
        'timestamp',
        'tenant_id',
    )
    list_filter = ('tenant_id', 'timestamp')
    search_fields = ('user_display', 'entity_type')
    readonly_fields = (
        'id', 'tenant_id', 'timestamp', 'user_id', 'user_display',
        'document', 'entity_type', 'entity_id', 'ip_address'
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
