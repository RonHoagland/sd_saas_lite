# value_lists/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from .models import ValueList, ValueListItem


class ValueListItemInline(admin.TabularInline):
    """Inline editor for ValueListItems within a ValueList."""
    model = ValueListItem
    extra = 1
    fields = ('label', 'value', 'sort_order', 'is_default', 'is_active')
    ordering = ('sort_order', 'label')


@admin.register(ValueList)
class ValueListAdmin(TenantModelAdmin):
    list_display = ('name', 'slug', 'is_system', 'tenant_id')
    list_filter = ('tenant_id', 'is_system')
    search_fields = ('name', 'slug')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ValueListItemInline]


@admin.register(ValueListItem)
class ValueListItemAdmin(TenantModelAdmin):
    list_display = ('label', 'value', 'value_list', 'sort_order', 'is_default', 'is_active', 'tenant_id')
    list_filter = ('tenant_id', 'is_active', 'is_default', 'value_list')
    search_fields = ('label', 'value')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
