# notes/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from .models import Note


@admin.register(Note)
class NoteAdmin(TenantModelAdmin):
    list_display = (
        'note_type',
        'body_preview',
        'parent_entity',
        'tenant_id',
        'created_on',
        'created_by',
    )
    list_filter = ('tenant_id', 'note_type', 'created_on')
    search_fields = ('body', 'created_by')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'created_by', 'updated_on', 'updated_by')

    def body_preview(self, obj):
        """Show first 100 chars of body."""
        return obj.body[:100] + '...' if len(obj.body) > 100 else obj.body
    body_preview.short_description = 'Body'

    def parent_entity(self, obj):
        """Show which parent entity the note is attached to."""
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
