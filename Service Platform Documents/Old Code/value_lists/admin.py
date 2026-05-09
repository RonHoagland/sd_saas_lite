from django.contrib import admin
from .models import ValueList, ValueItem

class ValueItemInline(admin.TabularInline):
    model = ValueItem
    extra = 1
    fields = ('value', 'sort_order', 'is_active')

@admin.register(ValueList)
class ValueListAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    search_fields = ('name', 'slug')
    inlines = [ValueItemInline]
