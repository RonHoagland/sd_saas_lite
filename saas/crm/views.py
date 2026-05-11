"""User-facing views for the CRM app — Customers list and detail.

The Customers list view (Phase 2.2) shapes its data into the List Block
contract from BLOCK_REFERENCE.md §3.2. Filtering, search, sorting, and
pagination are all server-rendered via GET query params.
"""

from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from crm.models import Customer


# Whitelist for ?sort= — guards against arbitrary order_by() injection. Maps
# column-key (the URL value) to the model field used for sorting.
_CUSTOMER_SORTABLE_FIELDS = {
    'company_name':    'company_name',
    'customer_number': 'customer_number',
    'status':          'status',
    'account_type':    'account_type',
    'customer_since':  'customer_since',
}

_CUSTOMER_PAGE_SIZE = 25


def _sort_url_for(column_key, current_sort, base_params):
    """Build the URL the column header should link to when clicked.

    Tri-state cycle simplified to asc ↔ desc for first pass:
      not currently sorted → asc
      currently asc        → desc
      currently desc       → asc

    Other GET params (search, filter, page) are preserved.
    """
    params = dict(base_params)
    params.pop('sort', None)
    params.pop('dir', None)
    # Reset to page 1 on sort change; keeping the user's old page after sort
    # is rarely what they want.
    params.pop('page', None)

    if current_sort and current_sort.get('column_key') == column_key:
        next_dir = 'desc' if current_sort.get('direction') == 'asc' else 'asc'
    else:
        next_dir = 'asc'

    params['sort'] = column_key
    params['dir'] = next_dir
    return '?' + urlencode(params)


def _page_url(page_num, base_params):
    """Build a pagination URL with page=N, preserving other params."""
    params = dict(base_params)
    params['page'] = page_num
    return '?' + urlencode(params)


@login_required(login_url='/')
def customers_list_view(request):
    # Parse GET state.
    search_q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    sort_col = request.GET.get('sort', '').strip()
    sort_dir = request.GET.get('dir', 'asc').strip()
    if sort_dir not in ('asc', 'desc'):
        sort_dir = 'asc'

    # Build queryset.
    qs = Customer.objects.all()
    if search_q:
        qs = qs.filter(company_name__icontains=search_q)
    if status_filter:
        qs = qs.filter(status=status_filter)

    if sort_col in _CUSTOMER_SORTABLE_FIELDS:
        field = _CUSTOMER_SORTABLE_FIELDS[sort_col]
        qs = qs.order_by(f'-{field}' if sort_dir == 'desc' else field)
        current_sort = {'column_key': sort_col, 'direction': sort_dir}
    else:
        qs = qs.order_by('-customer_since', 'company_name')
        current_sort = None

    # Paginate.
    paginator = Paginator(qs, _CUSTOMER_PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page', 1))

    # Base params we'll preserve when constructing per-action URLs.
    base_params = {}
    if search_q:
        base_params['q'] = search_q
    if status_filter:
        base_params['status'] = status_filter

    # Columns — see BLOCK_REFERENCE.md §3.2 column dict.
    columns = [
        {'key': 'company_name',    'label': 'Customer',       'is_primary': True, 'sortable': True},
        {'key': 'customer_number', 'label': 'Number',                              'sortable': True},
        {'key': 'status',          'label': 'Status',                              'sortable': True},
        {'key': 'account_type',    'label': 'Type',                                'sortable': True},
        {'key': 'customer_since',  'label': 'Customer Since',                      'sortable': True, 'align': 'end'},
    ]
    sort_base = dict(base_params)  # don't include sort/dir/page — _sort_url_for strips them anyway
    for col in columns:
        col['sort_url'] = _sort_url_for(col['key'], current_sort, sort_base)

    # Rows — keys match column `key`; `_href` is the primary-cell link target.
    rows = [
        {
            'company_name':    c.company_name or '(unnamed)',
            'customer_number': c.customer_number or '—',
            'status':          c.status,
            'account_type':    c.account_type,
            'customer_since':  c.customer_since.strftime('%b %-d, %Y') if c.customer_since else '—',
            '_href':           f'/customers/{c.pk}/',
        }
        for c in page.object_list
    ]

    # Filters (full variant only). Status options match Customer.StatusChoices.
    # First option is always "All" (no filter applied) — convention for the
    # filter dropdown's button to read e.g. "Status: All" when unfiltered.
    status_options = [{'value': '', 'label': 'All'}] + [
        {'value': k, 'label': v} for k, v in Customer.StatusChoices.choices
    ]
    selected_status_label = next(
        (o['label'] for o in status_options if o['value'] == status_filter),
        'All',
    )
    filters = [{
        'label':       'Status',
        'name':        'status',
        'value':       status_filter,
        'value_label': selected_status_label,
        'options':     status_options,
    }]

    # Search.
    search = {
        'placeholder': 'Search customers…',
        'name':        'q',
        'value':       search_q,
    }

    # Pagination.
    pagination = {
        'page':         page.number,
        'total_pages':  paginator.num_pages,
        'has_prev':     page.has_previous(),
        'has_next':     page.has_next(),
        'prev_url':     _page_url(page.previous_page_number(), base_params) if page.has_previous() else '',
        'next_url':     _page_url(page.next_page_number(), base_params) if page.has_next() else '',
    } if paginator.num_pages > 1 else None

    # New-record action.
    new_record = {
        # TODO(Phase 2.4): wire to /customers/new/ once create page exists.
        'label': 'New Customer', 'href': '#', 'icon': 'plus',
    }

    return render(request, 'customers/list.html', {
        'active_nav':   'customers',
        'columns':      columns,
        'rows':         rows,
        'filters':      filters,
        'search':       search,
        'pagination':   pagination,
        'current_sort': current_sort,
        'new_record':   new_record,
    })


# Customer status → tag-pill variant. Hardcoded per BLOCK_REFERENCE.md §3.1
# pattern (Customer.StatusChoices is enum-like and lifecycle-driven, so a
# Python mapping is correct; user-controlled status sets would store the
# variant on the data record).
_CUSTOMER_STATUS_VARIANT = {
    'Active':   'success',
    'Inactive': 'neutral',
    'Hold':     'warning',
    'Closed':   'danger',
}


def _safe_count(obj, related_name):
    """Defensive count() — returns 0 if the relation doesn't exist or errors."""
    try:
        rel = getattr(obj, related_name, None)
        return rel.count() if rel is not None else 0
    except Exception:
        return 0


@login_required(login_url='/')
def customer_detail_view(request, pk):
    customer = get_object_or_404(
        Customer.objects.select_related('assigned_to', 'account'),
        pk=pk,
    )

    # ── Counters for the Tab Panel block (§3.5) ──
    counters = {
        'assets':       _safe_count(customer, 'assets'),
        'requests':     _safe_count(customer, 'service_requests'),
        'work_orders':  _safe_count(customer, 'work_orders'),
        'quotes':       _safe_count(customer, 'quotes'),
        'invoices':     _safe_count(customer, 'invoices'),
        'payments':     customer.total_payments_count,
        'notes':        0,  # Note uses ExclusiveArcMixin — wire in Phase 2.3 follow-up.
        'documents':    0,  # Same.
    }

    # ── Assets list (compact List Block in the context panel) ──
    asset_columns = [
        {'key': 'name',         'label': 'Asset',  'is_primary': True, 'sortable': False},
        {'key': 'asset_number', 'label': '#',                          'sortable': False},
        {'key': 'status',       'label': 'Status',                     'sortable': False},
    ]
    try:
        asset_qs = customer.assets.all().order_by('-install_date', 'name')[:50]
    except Exception:
        asset_qs = []
    asset_rows = [
        {
            'name':         a.name,
            'asset_number': a.asset_number or '—',
            'status':       a.status,
            '_href':        f'/assets/{a.pk}/',  # TODO(Phase 3.2): real route once Asset detail exists.
        }
        for a in asset_qs
    ]
    asset_new_record = {
        # TODO(Phase 3.3): wire to /assets/new/?customer=<pk> once Asset create page exists.
        'label': 'New Asset', 'href': '#', 'icon': 'plus',
    }

    # ── Tab Panel spec ──
    customer_tabs = [
        {'id': 'requests',     'label': 'Requests',     'count': counters['requests']},
        {'id': 'work-orders',  'label': 'Work Orders',  'count': counters['work_orders']},
        {'id': 'quotes',       'label': 'Quotes',       'count': counters['quotes']},
        {'id': 'invoices',     'label': 'Invoices',     'count': counters['invoices']},
        {'id': 'payments',     'label': 'Payments',     'count': counters['payments']},
        {'id': 'notes',        'label': 'Notes',        'count': counters['notes']},
        {'id': 'documents',    'label': 'Documents',    'count': counters['documents']},
    ]

    # ── Sub-header §5.1.2 record-context ──
    record_name = customer.company_name or customer.customer_number or 'Unnamed Customer'
    meta_parts = []
    if customer.customer_number and customer.company_name:
        meta_parts.append(customer.customer_number)
    if customer.account_type:
        meta_parts.append(customer.account_type)
    record_meta = ' · '.join(meta_parts)

    # Sub-header tags region intentionally left empty for now. The §5.1.2
    # contract supports tags (Status, Priority, Type pills) but Ron hasn't
    # asked for any on Customer Detail. Add later if/when needed.
    record_tags = []

    record_actions = [
        {
            'label':           'Edit',
            'icon':            'edit-3',
            'variant':         'primary',
            'data_bs_toggle':  'modal',
            'data_bs_target':  '#sd-customer-edit',
        },
    ]

    return render(request, 'customers/detail.html', {
        'active_nav':     'customers',
        'customer':       customer,
        'record_name':    record_name,
        'record_meta':    record_meta,
        'record_tags':    record_tags,
        'record_actions': record_actions,
        'asset_columns':  asset_columns,
        'asset_rows':     asset_rows,
        'asset_new_record': asset_new_record,
        'customer_tabs':  customer_tabs,
    })
