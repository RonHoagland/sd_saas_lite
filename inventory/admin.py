# inventory/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from inventory.models import (
    InventoryItem, KitItem, InvPriceHistory, Pricebook, PricebookEntry,
)


@admin.register(InventoryItem)
class InventoryItemAdmin(TenantModelAdmin):
    list_display = ('product_number', 'name', 'type', 'status',
                    'unit_cost', 'unit_price', 'is_low_stock',
                    'is_out_of_stock', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'type', 'taxable',
                   'is_bundle', 'is_low_stock', 'is_out_of_stock')
    search_fields = ('product_number', 'name', 'sku', 'category')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on',
                       'is_low_stock', 'is_out_of_stock')


@admin.register(KitItem)
class KitItemAdmin(TenantModelAdmin):
    list_display = ('kit', 'product', 'quantity', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('kit__name', 'product__name')


@admin.register(InvPriceHistory)
class InvPriceHistoryAdmin(TenantModelAdmin):
    list_display = ('product', 'old_unit_price', 'new_unit_price',
                    'old_unit_cost', 'new_unit_cost', 'changed_at',
                    'changed_by', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('product__name', 'product__product_number')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'changed_at')


@admin.register(Pricebook)
class PricebookAdmin(TenantModelAdmin):
    list_display = ('name', 'is_active', 'tenant_id')
    list_filter = ('tenant_id', 'is_active')
    search_fields = ('name',)
    readonly_fields = ('id', 'tenant_id', 'created_on')


@admin.register(PricebookEntry)
class PricebookEntryAdmin(TenantModelAdmin):
    list_display = ('pricebook', 'product', 'price', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('pricebook__name', 'product__name', 'product__product_number')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
