"""User-facing views for the CRM app — Customers list and detail.

Read-only starter scaffolding (Phase 2 will add create/edit, duplicate
detection, inline-edit, and the activity timeline per spec §23).
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from crm.models import Customer


@login_required(login_url='/')
def customers_list_view(request):
    customers = (
        Customer.objects
        .all()
        .order_by('-customer_since', 'company_name')
    )
    return render(request, 'customers/list.html', {
        'active_nav': 'customers',
        'section_title': 'Customers',
        'customers': customers,
    })


@login_required(login_url='/')
def customer_detail_view(request, pk):
    customer = get_object_or_404(
        Customer.objects.select_related('assigned_to'),
        pk=pk,
    )
    return render(request, 'customers/detail.html', {
        'active_nav': 'customers',
        'section_title': customer.company_name or customer.customer_number or 'Customer',
        'customer': customer,
    })
