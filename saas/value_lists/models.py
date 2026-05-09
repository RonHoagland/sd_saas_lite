# value_lists/models.py
# Source: Top-Down Specifications V4, Pre-Code Audit §4.7 / Task 3.2.
#
# Models in this app:
#   ValueList, ValueListItem
#
# Provides tenant-configurable picklists (dropdowns) for entity fields
# like lead_source, work_order_type, asset_category, etc.
#
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

from django.db import models
from django.core.exceptions import ValidationError
from config.base_models import TenantModel


class ValueList(TenantModel):
    """
    A named collection of selectable values for a dropdown / picklist.

    System-seeded lists (is_system=True) are created during tenant provisioning
    and cannot be deleted — only extended or deactivated. Tenants may also
    create custom lists (is_system=False) for their own use.

    Source: Top-Down Specifications V4, Sections 1.1, 1.2, 10.
    """

    name = models.CharField(max_length=100,
                             help_text='Human-readable list name, e.g. "Lead Sources".')
    slug = models.SlugField(max_length=100,
                             help_text='Machine identifier for code reference, e.g. "lead_source".')
    description = models.TextField(blank=True)
    is_system = models.BooleanField(default=False,
                                     help_text='True for system-seeded lists created at provisioning.')

    class Meta:
        db_table = 'value_lists_valuelist'
        unique_together = [('tenant_id', 'slug')]
        indexes = [
            models.Index(fields=['tenant_id', 'slug']),
        ]

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        """Prevent deletion of system-seeded lists."""
        if self.is_system:
            raise ValidationError(
                f"System value list '{self.name}' cannot be deleted. "
                "Deactivate individual items instead."
            )
        super().delete(*args, **kwargs)


class ValueListItem(TenantModel):
    """
    A single selectable option within a ValueList.

    The 'value' field is what gets stored in referencing model fields (CharField).
    The 'label' field is what the UI displays in dropdowns.
    Deactivated items (is_active=False) remain in existing records but are
    hidden from new dropdown selections.

    Source: Top-Down Specifications V4, Sections 1.1, 1.2, 10.
    """

    value_list = models.ForeignKey(ValueList, on_delete=models.CASCADE,
                                    related_name='items')
    label = models.CharField(max_length=255,
                              help_text='Display text shown in UI dropdowns.')
    value = models.CharField(max_length=255,
                              help_text='Stored value in referencing model fields.')
    sort_order = models.IntegerField(default=0,
                                      help_text='Display ordering in dropdowns (ascending).')
    is_default = models.BooleanField(default=False,
                                      help_text='If True, pre-selected in new records.')
    is_active = models.BooleanField(default=True,
                                     help_text='Inactive items hidden from new selections.')

    class Meta:
        db_table = 'value_lists_valuelistitem'
        unique_together = [('tenant_id', 'value_list', 'value')]
        ordering = ['sort_order', 'label']
        indexes = [
            models.Index(fields=['tenant_id', 'value_list_id']),
            models.Index(fields=['tenant_id', 'value_list_id', 'is_active']),
        ]

    def __str__(self):
        return f'{self.label} ({self.value})'

    def clean(self):
        """Validate that only one item per list is marked as default."""
        if self.is_default:
            existing_default = ValueListItem.objects.filter(
                tenant_id=self.tenant_id,
                value_list=self.value_list,
                is_default=True,
            ).exclude(pk=self.pk)
            if existing_default.exists():
                raise ValidationError(
                    f"Only one default item is allowed per value list. "
                    f"'{existing_default.first().label}' is already the default."
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
