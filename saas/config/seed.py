# config/seed.py
# Tenant provisioning seed data.
# Source: Top-Down Specifications V4, System Status V3, Data Models V6.
#
# Called once when a new tenant is provisioned. Seeds:
#   1. NumberingRule + NumberSequence — for 23 numbered entity types
#   2. LifecycleStateDef + LifecycleTransitionRule — for 29 lifecycle-managed entity types
#   3. ValueList + ValueListItem — for tenant-configurable dropdowns
#
# Usage:
#   from config.seed import seed_tenant
#   seed_tenant(tenant_id=tenant.id, created_by='System')
#
# Notes:
#   - Safe to call with or without tenant context set (passes tenant_id explicitly).
#   - Idempotent within a transaction: re-running on an already-seeded tenant will
#     raise IntegrityError on unique constraints. Wrap in try/except or check first.
#   - Payments has 10 lifecycle states covering the full payment lifecycle
#     (Open → Pending → Processing → Applied → Paid, with holds, returns, voids, refunds).

from django.db import transaction


# ═══════════════════════════════════════════════════════════════════════════════
# 1. NUMBERING RULE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════
# 23 entity types with NumberingMixin.
# Default pattern: PREFIX-YY-####  (e.g. C-26-0001)
# Reset behavior: yearly (sequence resets each calendar year).

NUMBERING_RULES = [
    # ── CRM ──
    {'entity_type': 'customer',        'prefix': 'C',   'description': 'Customer numbers'},
    {'entity_type': 'lead',            'prefix': 'L',   'description': 'Lead numbers'},
    {'entity_type': 'opportunity',     'prefix': 'OPP', 'description': 'Opportunity numbers'},

    # ── Service ──
    {'entity_type': 'service_request', 'prefix': 'SR',  'description': 'Service request numbers'},
    {'entity_type': 'work_order',      'prefix': 'WO',  'description': 'Work order numbers'},
    {'entity_type': 'quote',           'prefix': 'Q',   'description': 'Quote numbers'},
    {'entity_type': 'invoice',         'prefix': 'INV', 'description': 'Invoice numbers'},
    {'entity_type': 'payment',         'prefix': 'PAY', 'description': 'Payment numbers'},

    # ── Procurement ──
    {'entity_type': 'vendor',          'prefix': 'V',   'description': 'Vendor numbers'},
    {'entity_type': 'purchase_order',  'prefix': 'PO',  'description': 'Purchase order numbers'},
    {'entity_type': 'vendor_bill',     'prefix': 'VB',  'description': 'Vendor bill numbers'},
    {'entity_type': 'requisition',     'prefix': 'REQ', 'description': 'Requisition numbers'},
    {'entity_type': 'rma',             'prefix': 'RMA', 'description': 'RMA numbers'},

    # ── Maintenance ──
    {'entity_type': 'asset',                    'prefix': 'A',  'description': 'Asset numbers'},
    {'entity_type': 'agreement',                'prefix': 'AGR','description': 'Agreement numbers'},
    {'entity_type': 'preventative_maintenance', 'prefix': 'PM', 'description': 'PM schedule numbers'},

    # ── Tasks ──
    {'entity_type': 'task',            'prefix': 'T',   'description': 'Task numbers'},

    # ── Workforce ──
    {'entity_type': 'work_group',      'prefix': 'WG',  'description': 'Work group numbers'},

    # ── Fleet ──
    {'entity_type': 'vehicle',         'prefix': 'VH',  'description': 'Vehicle numbers'},

    # ── Inventory ──
    {'entity_type': 'inventory_item',  'prefix': 'XT',  'description': 'Product / inventory item numbers'},

    # ── Automation ──
    {'entity_type': 'workflow',        'prefix': 'WF',  'description': 'Workflow numbers'},
    {'entity_type': 'equipment',       'prefix': 'EQ',  'description': 'Equipment numbers'},

    # ── Users ──
    {'entity_type': 'employee',        'prefix': 'E',   'description': 'Employee numbers'},
]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. LIFECYCLE STATE + TRANSITION DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════
# 29 entity types with LifecycleMixin.
# state_name values MUST match the StatusChoices DB values on each model
# (e.g., 'Active', 'In Progress') since lifecycle services compare entity.status
# against these names.
#
# state_type: 'normal' | 'locked' | 'final'
#   - 'final' states cannot be transitioned out of (except via admin override).

def _states(items):
    """Build a list of state dicts from compact tuples.
    Each tuple: (state_name, state_label, state_type, is_default, sort_order)
    """
    return [
        {
            'state_name': s[0],
            'state_label': s[1],
            'state_type': s[2],
            'is_default': s[3],
            'sort_order': s[4],
        }
        for s in items
    ]


LIFECYCLE_STATES = {

    # ── CRM ─────────────────────────────────────────────────────────────────

    'customer': _states([
        ('Active',   'Active',   'normal', True,  1),
        ('Inactive', 'Inactive', 'normal', False, 2),
        ('Hold',     'Hold',     'locked', False, 3),
        ('Closed',   'Closed',   'final',  False, 4),
    ]),
    'lead': _states([
        ('New',       'New',       'normal', True,  1),
        ('Contacted', 'Contacted', 'normal', False, 2),
        ('Qualified', 'Qualified', 'normal', False, 3),
        ('Converted', 'Converted', 'final',  False, 4),
        ('Lost',      'Lost',      'final',  False, 5),
    ]),
    'opportunity': _states([
        ('Open', 'Open', 'normal', True,  1),
        ('Won',  'Won',  'final',  False, 2),
        ('Lost', 'Lost', 'final',  False, 3),
    ]),

    # ── Service ─────────────────────────────────────────────────────────────

    'service_request': _states([
        ('New',         'New',         'normal', True,  1),
        ('Assigned',    'Assigned',    'normal', False, 2),
        ('In Progress', 'In Progress', 'normal', False, 3),
        ('On Hold',     'On Hold',     'locked', False, 4),
        ('Resolved',    'Resolved',    'normal', False, 5),
        ('Closed',      'Closed',      'final',  False, 6),
        ('Cancelled',   'Cancelled',   'final',  False, 7),
    ]),
    'work_order': _states([
        ('Draft',       'Draft',       'normal', True,  1),
        ('Scheduled',   'Scheduled',   'normal', False, 2),
        ('In Progress', 'In Progress', 'normal', False, 3),
        ('On Hold',     'On Hold',     'locked', False, 4),
        ('Completed',   'Completed',   'final',  False, 5),
        ('Cancelled',   'Cancelled',   'final',  False, 6),
    ]),
    'quote': _states([
        ('Draft',    'Draft',    'normal', True,  1),
        ('Sent',     'Sent',     'normal', False, 2),
        ('Accepted', 'Accepted', 'normal', False, 3),
        ('Declined', 'Declined', 'final',  False, 4),
        ('Expired',  'Expired',  'final',  False, 5),
        ('Invoiced', 'Invoiced', 'final',  False, 6),
    ]),
    'invoice': _states([
        ('Draft',   'Draft',          'normal', True,  1),
        ('Sent',    'Sent',           'normal', False, 2),
        ('Partial', 'Partially Paid', 'normal', False, 3),
        ('Paid',    'Paid',           'final',  False, 4),
        ('Overdue', 'Overdue',        'normal', False, 5),
        ('Voided',  'Voided',         'final',  False, 6),
    ]),
    'payment': _states([
        ('Open',              'Open',              'normal', True,  1),
        ('Pending',           'Pending',           'normal', False, 2),
        ('Processing',        'Processing',        'normal', False, 3),
        ('On Hold',           'On Hold',           'locked', False, 4),
        ('Partially Applied', 'Partially Applied', 'normal', False, 5),
        ('Applied',           'Applied',           'normal', False, 6),
        ('Paid',              'Paid',              'normal', False, 7),
        ('Returned',          'Returned',          'normal', False, 8),
        ('Voided',            'Voided',            'final',  False, 9),
        ('Refunded',          'Refunded',          'final',  False, 10),
    ]),

    # ── Procurement ─────────────────────────────────────────────────────────

    'vendor': _states([
        ('Active',     'Active',     'normal', True,  1),
        ('Inactive',   'Inactive',   'normal', False, 2),
        ('Do Not Use', 'Do Not Use', 'final',  False, 3),
    ]),
    'purchase_order': _states([
        ('Draft',              'Draft',              'normal', True,  1),
        ('Submitted',          'Submitted',          'normal', False, 2),
        ('Approved',           'Approved',           'normal', False, 3),
        ('Ordered',            'Ordered',            'normal', False, 4),
        ('Partially Received', 'Partially Received', 'normal', False, 5),
        ('Received',           'Received',           'final',  False, 6),
        ('Cancelled',          'Cancelled',          'final',  False, 7),
    ]),
    'vendor_bill': _states([
        ('Draft',   'Draft',   'normal', True,  1),
        ('Pending', 'Pending', 'normal', False, 2),
        ('Approved','Approved','normal', False, 3),
        ('Paid',    'Paid',    'final',  False, 4),
        ('Voided',  'Voided',  'final',  False, 5),
    ]),
    'requisition': _states([
        ('Draft',     'Draft',     'normal', True,  1),
        ('Submitted', 'Submitted', 'normal', False, 2),
        ('Approved',  'Approved',  'normal', False, 3),
        ('Rejected',  'Rejected',  'final',  False, 4),
        ('Converted', 'Converted', 'final',  False, 5),
    ]),
    'rma': _states([
        ('Initiated',          'Initiated',          'normal', True,  1),
        ('Shipped',            'Shipped',            'normal', False, 2),
        ('Received by Vendor', 'Received by Vendor', 'normal', False, 3),
        ('Credited',           'Credited',           'normal', False, 4),
        ('Closed',             'Closed',             'final',  False, 5),
        ('Denied',             'Denied',             'final',  False, 6),
    ]),

    # ── Maintenance ─────────────────────────────────────────────────────────

    'asset': _states([
        ('Active',   'Active',   'normal', True,  1),
        ('Inactive', 'Inactive', 'normal', False, 2),
        ('Retired',  'Retired',  'final',  False, 3),
        ('Sold',     'Sold',     'final',  False, 4),
    ]),
    'agreement': _states([
        ('Active',   'Active',   'normal', True,  1),
        ('Inactive', 'Inactive', 'normal', False, 2),
        ('Archived', 'Archived', 'final',  False, 3),
    ]),
    'preventative_maintenance': _states([
        ('Active',   'Active',   'normal', True,  1),
        ('Inactive', 'Inactive', 'normal', False, 2),
    ]),

    # ── Tasks ───────────────────────────────────────────────────────────────

    'task': _states([
        ('Not Started',  'Not Started',  'normal', True,  1),
        ('In Progress',  'In Progress',  'normal', False, 2),
        ('On Hold',      'On Hold',      'locked', False, 3),
        ('Completed',    'Completed',    'final',  False, 4),
        ('Cancelled',    'Cancelled',    'final',  False, 5),
    ]),

    # ── Workforce ───────────────────────────────────────────────────────────

    'wg_division': _states([
        ('Active',   'Active',   'normal', True,  1),
        ('Inactive', 'Inactive', 'normal', False, 2),
    ]),
    'work_group': _states([
        ('Active',   'Active',   'normal', True,  1),
        ('Inactive', 'Inactive', 'normal', False, 2),
    ]),

    # ── Fleet ───────────────────────────────────────────────────────────────

    'vehicle': _states([
        ('Active',         'Active',         'normal', True,  1),
        ('In Service',     'In Service',     'normal', False, 2),
        ('Out of Service', 'Out of Service', 'normal', False, 3),
        ('Retired',        'Retired',        'final',  False, 4),
    ]),
    'vehicle_maintenance': _states([
        ('Scheduled', 'Scheduled', 'normal', True,  1),
        ('Completed', 'Completed', 'final',  False, 2),
        ('Overdue',   'Overdue',   'normal', False, 3),
        ('Cancelled', 'Cancelled', 'final',  False, 4),
    ]),

    # ── Inventory ───────────────────────────────────────────────────────────

    'inventory_item': _states([
        ('Active',       'Active',       'normal', True,  1),
        ('Hold',         'Hold',         'locked', False, 2),
        ('Discontinued', 'Discontinued', 'final',  False, 3),
    ]),
    'pricebook_entry': _states([
        ('Active',       'Active',       'normal', True,  1),
        ('Inactive',     'Inactive',     'normal', False, 2),
        ('Discontinued', 'Discontinued', 'final',  False, 3),
    ]),

    # ── Users ───────────────────────────────────────────────────────────────

    'employee': _states([
        ('Active',     'Active',     'normal', True,  1),
        ('On Leave',   'On Leave',   'locked', False, 2),
        ('Inactive',   'Inactive',   'normal', False, 3),
        ('Terminated', 'Terminated', 'final',  False, 4),
    ]),

    # ── Automation ──────────────────────────────────────────────────────────

    'communication_trigger': _states([
        ('Active',   'Active',   'normal', True,  1),
        ('Inactive', 'Inactive', 'normal', False, 2),
    ]),
    'communication_template': _states([
        ('Active',   'Active',   'normal', True,  1),
        ('Inactive', 'Inactive', 'normal', False, 2),
    ]),
    'safety_form': _states([
        ('Draft',    'Draft',    'normal', False, 1),
        ('Active',   'Active',   'normal', True,  2),
        ('Inactive', 'Inactive', 'normal', False, 3),
    ]),
    'workflow': _states([
        ('Draft',    'Draft',    'normal', False, 1),
        ('Active',   'Active',   'normal', True,  2),
        ('Inactive', 'Inactive', 'normal', False, 3),
    ]),
    'equipment': _states([
        ('Available',      'Available',      'normal', True,  1),
        ('Checked Out',    'Checked Out',    'normal', False, 2),
        ('In Repair',      'In Repair',      'locked', False, 3),
        ('Decommissioned', 'Decommissioned', 'final',  False, 4),
    ]),
}


# ── Transition rules ────────────────────────────────────────────────────────
# Each tuple: (from_state, to_state, required_role, requires_reason)
# Empty string for required_role = no role restriction.

def _transitions(items):
    """Build a list of transition dicts from compact tuples."""
    return [
        {
            'from_state': t[0],
            'to_state': t[1],
            'required_role': t[2] if len(t) > 2 else '',
            'requires_reason': t[3] if len(t) > 3 else False,
        }
        for t in items
    ]


LIFECYCLE_TRANSITIONS = {

    # ── CRM ─────────────────────────────────────────────────────────────────

    'customer': _transitions([
        ('Active',   'Inactive'),
        ('Active',   'Hold',     '', True),       # reason required for hold
        ('Active',   'Closed',   '', True),
        ('Inactive', 'Active'),
        ('Hold',     'Active'),
        ('Hold',     'Closed',   '', True),
    ]),
    'lead': _transitions([
        ('New',       'Contacted'),
        ('New',       'Lost',      '', True),
        ('Contacted', 'Qualified'),
        ('Contacted', 'Lost',      '', True),
        ('Qualified', 'Converted'),
        ('Qualified', 'Lost',      '', True),
    ]),
    'opportunity': _transitions([
        ('Open', 'Won'),
        ('Open', 'Lost', '', True),
    ]),

    # ── Service ─────────────────────────────────────────────────────────────

    'service_request': _transitions([
        ('New',         'Assigned'),
        ('New',         'Cancelled',   '', True),
        ('Assigned',    'In Progress'),
        ('Assigned',    'On Hold',     '', True),
        ('Assigned',    'Cancelled',   '', True),
        ('In Progress', 'On Hold',     '', True),
        ('In Progress', 'Resolved'),
        ('In Progress', 'Cancelled',   '', True),
        ('On Hold',     'Assigned'),
        ('On Hold',     'In Progress'),
        ('On Hold',     'Cancelled',   '', True),
        ('Resolved',    'Closed'),
    ]),
    'work_order': _transitions([
        ('Draft',       'Scheduled'),
        ('Draft',       'Cancelled',   '', True),
        ('Scheduled',   'In Progress'),
        ('Scheduled',   'Cancelled',   '', True),
        ('In Progress', 'On Hold',     '', True),
        ('In Progress', 'Completed'),
        ('In Progress', 'Cancelled',   '', True),
        ('On Hold',     'In Progress'),
        ('On Hold',     'Cancelled',   '', True),
    ]),
    'quote': _transitions([
        ('Draft',    'Sent'),
        ('Sent',     'Accepted'),
        ('Sent',     'Declined'),
        ('Sent',     'Expired'),
        ('Accepted', 'Invoiced'),
    ]),
    'invoice': _transitions([
        ('Draft',   'Sent'),
        ('Draft',   'Voided',  '', True),
        ('Sent',    'Partial'),
        ('Sent',    'Paid'),
        ('Sent',    'Overdue'),
        ('Sent',    'Voided',  '', True),
        ('Partial', 'Paid'),
        ('Partial', 'Overdue'),
        ('Overdue', 'Partial'),
        ('Overdue', 'Paid'),
        ('Overdue', 'Voided',  '', True),
    ]),
    'payment': _transitions([
        # Open → next stages
        ('Open',              'Pending'),
        ('Open',              'Processing'),
        ('Open',              'On Hold'),
        ('Open',              'Voided',            '', True),
        # Pending → processing or hold
        ('Pending',           'Processing'),
        ('Pending',           'On Hold'),
        ('Pending',           'Voided',            '', True),
        # Processing → outcomes
        ('Processing',        'Applied'),
        ('Processing',        'Partially Applied'),
        ('Processing',        'Returned'),
        ('Processing',        'Voided',            '', True),
        # On Hold → resume
        ('On Hold',           'Pending'),
        ('On Hold',           'Processing'),
        ('On Hold',           'Voided',            '', True),
        # Partially Applied → completion
        ('Partially Applied', 'Applied'),
        ('Partially Applied', 'Paid'),
        ('Partially Applied', 'Voided',            '', True),
        # Applied → settlement
        ('Applied',           'Partially Applied'),
        ('Applied',           'Paid'),
        ('Applied',           'Refunded',          '', True),
        ('Applied',           'Voided',            '', True),
        # Paid → refund only
        ('Paid',              'Refunded',          '', True),
        # Returned → retry or void
        ('Returned',          'Pending'),
        ('Returned',          'Voided',            '', True),
    ]),

    # ── Procurement ─────────────────────────────────────────────────────────

    'vendor': _transitions([
        ('Active',   'Inactive'),
        ('Active',   'Do Not Use', '', True),
        ('Inactive', 'Active'),
    ]),
    'purchase_order': _transitions([
        ('Draft',              'Submitted'),
        ('Draft',              'Cancelled',          '', True),
        ('Submitted',          'Approved'),
        ('Submitted',          'Cancelled',          '', True),
        ('Approved',           'Ordered'),
        ('Ordered',            'Partially Received'),
        ('Ordered',            'Received'),
        ('Ordered',            'Cancelled',          '', True),
        ('Partially Received', 'Received'),
    ]),
    'vendor_bill': _transitions([
        ('Draft',    'Pending'),
        ('Pending',  'Approved'),
        ('Pending',  'Voided', '', True),
        ('Approved', 'Paid'),
        ('Approved', 'Voided', '', True),
    ]),
    'requisition': _transitions([
        ('Draft',     'Submitted'),
        ('Submitted', 'Approved'),
        ('Submitted', 'Rejected', '', True),
        ('Approved',  'Converted'),
    ]),
    'rma': _transitions([
        ('Initiated',          'Shipped'),
        ('Initiated',          'Denied',             '', True),
        ('Shipped',            'Received by Vendor'),
        ('Received by Vendor', 'Credited'),
        ('Received by Vendor', 'Denied',             '', True),
        ('Credited',           'Closed'),
    ]),

    # ── Maintenance ─────────────────────────────────────────────────────────

    'asset': _transitions([
        ('Active',   'Inactive'),
        ('Active',   'Retired',  '', True),
        ('Active',   'Sold',     '', True),
        ('Inactive', 'Active'),
        ('Inactive', 'Retired',  '', True),
        ('Inactive', 'Sold',     '', True),
    ]),
    'agreement': _transitions([
        ('Active',   'Inactive'),
        ('Active',   'Archived', '', True),
        ('Inactive', 'Active'),
        ('Inactive', 'Archived', '', True),
    ]),
    'preventative_maintenance': _transitions([
        ('Active',   'Inactive'),
        ('Inactive', 'Active'),
    ]),

    # ── Tasks ───────────────────────────────────────────────────────────────

    'task': _transitions([
        ('Not Started',  'In Progress'),
        ('Not Started',  'Cancelled',  '', True),
        ('In Progress',  'On Hold',    '', True),
        ('In Progress',  'Completed'),
        ('In Progress',  'Cancelled',  '', True),
        ('On Hold',      'In Progress'),
        ('On Hold',      'Cancelled',  '', True),
    ]),

    # ── Workforce ───────────────────────────────────────────────────────────

    'wg_division': _transitions([
        ('Active',   'Inactive'),
        ('Inactive', 'Active'),
    ]),
    'work_group': _transitions([
        ('Active',   'Inactive'),
        ('Inactive', 'Active'),
    ]),

    # ── Fleet ───────────────────────────────────────────────────────────────

    'vehicle': _transitions([
        ('Active',         'In Service'),
        ('Active',         'Out of Service'),
        ('Active',         'Retired',        '', True),
        ('In Service',     'Active'),
        ('In Service',     'Out of Service'),
        ('Out of Service', 'In Service'),
        ('Out of Service', 'Active'),
        ('Out of Service', 'Retired',        '', True),
    ]),
    'vehicle_maintenance': _transitions([
        ('Scheduled', 'Completed'),
        ('Scheduled', 'Overdue'),
        ('Scheduled', 'Cancelled', '', True),
        ('Overdue',   'Completed'),
        ('Overdue',   'Cancelled', '', True),
    ]),

    # ── Inventory ───────────────────────────────────────────────────────────

    'inventory_item': _transitions([
        ('Active', 'Hold'),
        ('Active', 'Discontinued', '', True),
        ('Hold',   'Active'),
        ('Hold',   'Discontinued', '', True),
    ]),
    'pricebook_entry': _transitions([
        ('Active',   'Inactive'),
        ('Active',   'Discontinued', '', True),
        ('Inactive', 'Active'),
        ('Inactive', 'Discontinued', '', True),
    ]),

    # ── Users ───────────────────────────────────────────────────────────────

    'employee': _transitions([
        ('Active',   'On Leave'),
        ('Active',   'Inactive'),
        ('Active',   'Terminated', '', True),
        ('On Leave', 'Active'),
        ('On Leave', 'Inactive'),
        ('Inactive', 'Active'),
        ('Inactive', 'Terminated', '', True),
    ]),

    # ── Automation ──────────────────────────────────────────────────────────

    'communication_trigger': _transitions([
        ('Active',   'Inactive'),
        ('Inactive', 'Active'),
    ]),
    'communication_template': _transitions([
        ('Active',   'Inactive'),
        ('Inactive', 'Active'),
    ]),
    'safety_form': _transitions([
        ('Draft',    'Active'),
        ('Active',   'Inactive'),
        ('Inactive', 'Active'),
    ]),
    'workflow': _transitions([
        ('Draft',    'Active'),
        ('Active',   'Inactive'),
        ('Inactive', 'Active'),
    ]),
    'equipment': _transitions([
        ('Available',   'Checked Out'),
        ('Available',   'In Repair'),
        ('Available',   'Decommissioned', '', True),
        ('Checked Out', 'Available'),
        ('Checked Out', 'In Repair'),
        ('In Repair',   'Available'),
        ('In Repair',   'Decommissioned', '', True),
    ]),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. VALUE LIST DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════
# Tenant-configurable dropdowns seeded with sensible defaults.
# All lists are marked is_system=True (cannot be deleted by tenant, only extended).

VALUE_LISTS = [
    {
        'name': 'Lead Sources',
        'slug': 'lead_source',
        'description': 'Where leads originate from.',
        'items': [
            {'label': 'Referral',       'value': 'referral',       'sort_order': 1, 'is_default': True},
            {'label': 'Website',        'value': 'website',        'sort_order': 2},
            {'label': 'Advertisement',  'value': 'advertisement',  'sort_order': 3},
            {'label': 'Trade Show',     'value': 'trade_show',     'sort_order': 4},
            {'label': 'Cold Call',      'value': 'cold_call',      'sort_order': 5},
            {'label': 'Social Media',   'value': 'social_media',   'sort_order': 6},
            {'label': 'Partner',        'value': 'partner',        'sort_order': 7},
            {'label': 'Other',          'value': 'other',          'sort_order': 99},
        ],
    },
    {
        'name': 'Account Terms',
        'slug': 'account_terms',
        'description': 'Payment terms for customer accounts.',
        'items': [
            {'label': 'Due on Receipt', 'value': 'due_on_receipt', 'sort_order': 1, 'is_default': True},
            {'label': 'Net 15',         'value': 'net_15',         'sort_order': 2},
            {'label': 'Net 30',         'value': 'net_30',         'sort_order': 3},
            {'label': 'Net 45',         'value': 'net_45',         'sort_order': 4},
            {'label': 'Net 60',         'value': 'net_60',         'sort_order': 5},
        ],
    },
    {
        'name': 'Industries',
        'slug': 'industry',
        'description': 'NAICS top-level sectors used for customer firmographics.',
        'items': [
            {'label': 'Agriculture, Forestry, Fishing & Hunting',                 'value': 'agriculture',                 'sort_order': 11},
            {'label': 'Mining, Quarrying, Oil & Gas Extraction',                  'value': 'mining',                      'sort_order': 21},
            {'label': 'Utilities',                                                 'value': 'utilities',                   'sort_order': 22},
            {'label': 'Construction',                                              'value': 'construction',                'sort_order': 23},
            {'label': 'Manufacturing',                                             'value': 'manufacturing',               'sort_order': 31},
            {'label': 'Wholesale Trade',                                           'value': 'wholesale_trade',             'sort_order': 42},
            {'label': 'Retail Trade',                                              'value': 'retail_trade',                'sort_order': 44},
            {'label': 'Transportation & Warehousing',                              'value': 'transportation_warehousing',  'sort_order': 48},
            {'label': 'Information',                                               'value': 'information',                 'sort_order': 51},
            {'label': 'Finance & Insurance',                                       'value': 'finance_insurance',           'sort_order': 52},
            {'label': 'Real Estate, Rental & Leasing',                             'value': 'real_estate',                 'sort_order': 53},
            {'label': 'Professional, Scientific & Technical Services',             'value': 'professional_services',       'sort_order': 54},
            {'label': 'Management of Companies & Enterprises',                     'value': 'management',                  'sort_order': 55},
            {'label': 'Administrative, Support & Waste Management Services',       'value': 'administrative_support',      'sort_order': 56},
            {'label': 'Educational Services',                                      'value': 'education',                   'sort_order': 61},
            {'label': 'Health Care & Social Assistance',                           'value': 'healthcare',                  'sort_order': 62},
            {'label': 'Arts, Entertainment & Recreation',                          'value': 'arts_entertainment',          'sort_order': 71},
            {'label': 'Accommodation & Food Services',                             'value': 'accommodation_food',          'sort_order': 72},
            {'label': 'Other Services (except Public Administration)',             'value': 'other_services',              'sort_order': 81},
            {'label': 'Public Administration',                                     'value': 'public_administration',       'sort_order': 92},
        ],
    },
    {
        'name': 'Asset Categories',
        'slug': 'asset_category',
        'description': 'High-level categories for customer assets.',
        'items': [
            {'label': 'HVAC',         'value': 'hvac',         'sort_order': 1, 'is_default': True},
            {'label': 'Plumbing',     'value': 'plumbing',     'sort_order': 2},
            {'label': 'Electrical',   'value': 'electrical',   'sort_order': 3},
            {'label': 'Fire Safety',  'value': 'fire_safety',  'sort_order': 4},
            {'label': 'Building',     'value': 'building',     'sort_order': 5},
            {'label': 'Equipment',    'value': 'equipment',    'sort_order': 6},
            {'label': 'Other',        'value': 'other',        'sort_order': 99},
        ],
    },
    {
        'name': 'Asset Types',
        'slug': 'asset_type',
        'description': 'Classification of asset hardware/infrastructure.',
        'items': [
            {'label': 'Equipment',      'value': 'equipment',      'sort_order': 1, 'is_default': True},
            {'label': 'Vehicle',        'value': 'vehicle',        'sort_order': 2},
            {'label': 'Building',       'value': 'building',       'sort_order': 3},
            {'label': 'Infrastructure', 'value': 'infrastructure', 'sort_order': 4},
            {'label': 'Tool',           'value': 'tool',           'sort_order': 5},
            {'label': 'Other',          'value': 'other',          'sort_order': 99},
        ],
    },
    {
        'name': 'Work Order Types',
        'slug': 'work_order_type',
        'description': 'Classification of work order purpose.',
        'items': [
            {'label': 'Repair',       'value': 'repair',       'sort_order': 1, 'is_default': True},
            {'label': 'Installation', 'value': 'installation', 'sort_order': 2},
            {'label': 'Maintenance',  'value': 'maintenance',  'sort_order': 3},
            {'label': 'Inspection',   'value': 'inspection',   'sort_order': 4},
            {'label': 'Emergency',    'value': 'emergency',    'sort_order': 5},
            {'label': 'Warranty',     'value': 'warranty',     'sort_order': 6},
            {'label': 'Other',        'value': 'other',        'sort_order': 99},
        ],
    },
    {
        'name': 'Vehicle Types',
        'slug': 'vehicle_type',
        'description': 'Classification of fleet vehicles.',
        'items': [
            {'label': 'Van',             'value': 'van',             'sort_order': 1, 'is_default': True},
            {'label': 'Truck',           'value': 'truck',           'sort_order': 2},
            {'label': 'Car',             'value': 'car',             'sort_order': 3},
            {'label': 'Trailer',         'value': 'trailer',         'sort_order': 4},
            {'label': 'Heavy Equipment', 'value': 'heavy_equipment', 'sort_order': 5},
            {'label': 'Other',           'value': 'other',           'sort_order': 99},
        ],
    },
    {
        'name': 'Maintenance Types',
        'slug': 'maintenance_type',
        'description': 'Classification of maintenance activities.',
        'items': [
            {'label': 'Preventative', 'value': 'preventative', 'sort_order': 1, 'is_default': True},
            {'label': 'Corrective',   'value': 'corrective',   'sort_order': 2},
            {'label': 'Predictive',   'value': 'predictive',   'sort_order': 3},
            {'label': 'Emergency',    'value': 'emergency',    'sort_order': 4},
            {'label': 'Routine',      'value': 'routine',      'sort_order': 5},
        ],
    },
    {
        'name': 'Trip Purposes',
        'slug': 'trip_purpose',
        'description': 'Reason for fleet vehicle trips.',
        'items': [
            {'label': 'Service Call', 'value': 'service_call', 'sort_order': 1, 'is_default': True},
            {'label': 'Delivery',     'value': 'delivery',     'sort_order': 2},
            {'label': 'Pickup',       'value': 'pickup',       'sort_order': 3},
            {'label': 'Inspection',   'value': 'inspection',   'sort_order': 4},
            {'label': 'Meeting',      'value': 'meeting',      'sort_order': 5},
            {'label': 'Other',        'value': 'other',        'sort_order': 99},
        ],
    },
    {
        'name': 'Payment Methods',
        'slug': 'payment_method',
        'description': 'Accepted payment methods.',
        'items': [
            {'label': 'Cash',          'value': 'cash',          'sort_order': 1},
            {'label': 'Check',         'value': 'check',         'sort_order': 2},
            {'label': 'Credit Card',   'value': 'credit_card',   'sort_order': 3, 'is_default': True},
            {'label': 'ACH',           'value': 'ach',           'sort_order': 4},
            {'label': 'Wire Transfer', 'value': 'wire_transfer', 'sort_order': 5},
            {'label': 'Other',         'value': 'other',         'sort_order': 99},
        ],
    },
    {
        'name': 'Customer Account Types',
        'slug': 'customer_account_type',
        'description': 'Classification of customer accounts.',
        'items': [
            {'label': 'Residential', 'value': 'residential', 'sort_order': 1, 'is_default': True},
            {'label': 'Commercial',  'value': 'commercial',  'sort_order': 2},
            {'label': 'Government',  'value': 'government',  'sort_order': 3},
            {'label': 'Non-Profit',  'value': 'non_profit',  'sort_order': 4},
            {'label': 'Other',       'value': 'other',       'sort_order': 99},
        ],
    },
    {
        'name': 'Contact Statuses',
        'slug': 'contact_status',
        'description': 'Status of customer contacts.',
        'items': [
            {'label': 'Active',          'value': 'active',           'sort_order': 1, 'is_default': True},
            {'label': 'Left Company',    'value': 'left_company',     'sort_order': 2},
            {'label': 'Do Not Contact',  'value': 'do_not_contact',   'sort_order': 3},
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# SEED FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@transaction.atomic
def seed_tenant(tenant_id, created_by='System'):
    """
    Provision all default data for a new tenant.

    Args:
        tenant_id: UUID of the tenant being provisioned.
        created_by: Audit field value (default 'System').

    Creates:
        - 23 NumberingRule + 23 NumberSequence records
        - LifecycleStateDef records for 29 entity types (~120 states)
        - LifecycleTransitionRule records for 29 entity types (~150 transitions)
        - 12 ValueList + ~90 ValueListItem records

    Raises:
        IntegrityError if tenant is already seeded (unique constraints).
    """
    counts = {}
    counts['numbering'] = seed_numbering(tenant_id, created_by)
    counts['lifecycle'] = seed_lifecycle(tenant_id, created_by)
    counts['value_lists'] = seed_value_lists(tenant_id, created_by)
    return counts


def seed_numbering(tenant_id, created_by='System'):
    """
    Create NumberingRule + NumberSequence for each numbered entity type.

    Default pattern: PREFIX-YY-#### with yearly reset.
    Tenants can customize rules later via admin.
    """
    from numbering.models import NumberingRule, NumberSequence

    rules_created = 0
    for rule_def in NUMBERING_RULES:
        rule = NumberingRule(
            tenant_id=tenant_id,
            entity_type=rule_def['entity_type'],
            prefix=rule_def['prefix'],
            description=rule_def.get('description', ''),
            is_enabled=True,
            include_year=True,
            year_format='YY',
            include_month=False,
            sequence_length=4,
            delimiter='-',
            reset_behavior='yearly',
            created_by=created_by,
            updated_by=created_by,
        )
        rule.save()

        NumberSequence.objects.create(
            rule=rule,
            current_value=0,
        )
        rules_created += 1

    return rules_created


def seed_lifecycle(tenant_id, created_by='System'):
    """
    Create LifecycleStateDef and LifecycleTransitionRule records for all
    lifecycle-managed entity types.

    States are created first (required for transition rule validation).
    Transition rules are bulk-created to skip per-row validation queries,
    since the data is known-good from the definitions above.
    """
    from lifecycle.models import LifecycleStateDef, LifecycleTransitionRule

    states_created = 0
    transitions_created = 0

    # ── Phase 1: Create all state definitions ──
    state_objects = []
    for entity_type, states in LIFECYCLE_STATES.items():
        for state in states:
            state_objects.append(LifecycleStateDef(
                tenant_id=tenant_id,
                entity_type=entity_type,
                state_name=state['state_name'],
                state_label=state['state_label'],
                state_type=state['state_type'],
                is_default=state['is_default'],
                sort_order=state['sort_order'],
                created_by=created_by,
                updated_by=created_by,
            ))

    # Bulk create states — skips the custom save() that clears other defaults,
    # but that logic is only needed when changing defaults on existing data.
    # For initial seed, each entity_type has exactly one is_default=True.
    LifecycleStateDef.all_objects.bulk_create(state_objects)
    states_created = len(state_objects)

    # ── Phase 2: Create all transition rules ──
    transition_objects = []
    for entity_type, transitions in LIFECYCLE_TRANSITIONS.items():
        for trans in transitions:
            transition_objects.append(LifecycleTransitionRule(
                tenant_id=tenant_id,
                entity_type=entity_type,
                from_state=trans['from_state'],
                to_state=trans['to_state'],
                required_role=trans.get('required_role', ''),
                requires_reason=trans.get('requires_reason', False),
                is_admin_override=False,
                created_by=created_by,
                updated_by=created_by,
            ))

    # Bulk create transitions — skips full_clean() validation queries.
    # Safe because all from_state/to_state values match LIFECYCLE_STATES above.
    LifecycleTransitionRule.all_objects.bulk_create(transition_objects)
    transitions_created = len(transition_objects)

    return {'states': states_created, 'transitions': transitions_created}


def seed_value_lists(tenant_id, created_by='System'):
    """
    Create ValueList and ValueListItem records for tenant-configurable dropdowns.

    All seeded lists are marked is_system=True (protected from deletion).
    Tenants can add custom items to these lists and create new custom lists.
    """
    from value_lists.models import ValueList, ValueListItem

    lists_created = 0
    items_created = 0

    for vl_def in VALUE_LISTS:
        vl = ValueList(
            tenant_id=tenant_id,
            name=vl_def['name'],
            slug=vl_def['slug'],
            description=vl_def.get('description', ''),
            is_system=True,
            created_by=created_by,
            updated_by=created_by,
        )
        vl.save()
        lists_created += 1

        item_objects = []
        for item_def in vl_def['items']:
            item_objects.append(ValueListItem(
                tenant_id=tenant_id,
                value_list=vl,
                label=item_def['label'],
                value=item_def['value'],
                sort_order=item_def.get('sort_order', 0),
                is_default=item_def.get('is_default', False),
                is_active=True,
                created_by=created_by,
                updated_by=created_by,
            ))

        # Bulk create items — skips the one-default-per-list validation in clean().
        # Safe because each list definition has at most one is_default=True.
        ValueListItem.all_objects.bulk_create(item_objects)
        items_created += len(item_objects)

    return {'lists': lists_created, 'items': items_created}
