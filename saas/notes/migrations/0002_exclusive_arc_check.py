"""
Add a database-level CHECK constraint enforcing the 25-FK exclusive arc
on notes_note. Per Note & Document Implementation Specification V1 §2.2,
exactly one parent FK must be non-null.

Until this migration, the constraint was only enforced in Python
(`config/base_models.ExclusiveArcMixin.clean()`). A raw INSERT (or any
future code path that bypasses `.save()` -> `full_clean()`) could create
a Note with zero or two+ parents.

Field list is frozen at 25 columns as of this migration; adding a 26th
parent FK requires a follow-up migration that drops and re-adds the
constraint with the new column included.
"""

from django.db import migrations


# Frozen list — keep in sync with config.base_models.PARENT_FK_FIELDS as
# of the time this migration was authored. Do NOT import that module
# here; migrations must remain immutable across future code changes.
_PARENT_FK_COLUMNS = [
    'customer_id', 'contact_id', 'lead_id', 'opportunity_id', 'quote_id',
    'invoice_id', 'work_order_id', 'asset_id', 'service_request_id',
    'prev_maint_id', 'workflow_id', 'payment_id', 'user_id', 'vendor_id',
    'purchase_order_id', 'work_group_id', 'task_id', 'vehicle_id',
    'warehouse_id', 'ledger_id', 'requisition_id', 'rma_id',
    'equipment_id', 'safety_form_id', 'vendor_bill_id',
]
_TABLE = 'notes_note'
_CONSTRAINT = 'notes_note_exclusive_parent_arc'


def _build_check_sql():
    parts = [f'({col} IS NOT NULL)::int' for col in _PARENT_FK_COLUMNS]
    expression = ' + '.join(parts)
    return (
        f'ALTER TABLE {_TABLE} '
        f'ADD CONSTRAINT {_CONSTRAINT} '
        f'CHECK ({expression} = 1);'
    )


def _build_drop_sql():
    return f'ALTER TABLE {_TABLE} DROP CONSTRAINT IF EXISTS {_CONSTRAINT};'


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=_build_check_sql(),
            reverse_sql=_build_drop_sql(),
        ),
    ]
