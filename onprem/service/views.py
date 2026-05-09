"""User-facing views for the service app — Jobs, Service Requests, Schedule,
Quotes, Invoices, Payments. All read-only starter scaffolding.

Each list view orders newest-first using `created_on` from TenantModel. Detail
views use `select_related` to avoid N+1 on customer/asset/etc. lookups.

Phase 4–8 will deepen each: state transitions, line-item drawers, send actions,
PDF print, snapshot rules, etc.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from service.models import (
    ServiceRequest, WorkOrder, Quote, Invoice, Payments,
)


# ─── Jobs (WorkOrder) ─────────────────────────────────────────────────────────

@login_required(login_url='/')
def jobs_list_view(request):
    jobs = (
        WorkOrder.objects
        .select_related('customer', 'asset', 'assigned_to')
        .order_by('-created_on')
    )
    return render(request, 'jobs/list.html', {
        'active_nav': 'jobs',
        'section_title': 'Jobs',
        'jobs': jobs,
    })


@login_required(login_url='/')
def job_detail_view(request, pk):
    job = get_object_or_404(
        WorkOrder.objects.select_related('customer', 'asset', 'assigned_to', 'service_request'),
        pk=pk,
    )
    return render(request, 'jobs/detail.html', {
        'active_nav': 'jobs',
        'section_title': job.subject or f'Job {job.wo_number}',
        'job': job,
    })


# ─── Service Requests ─────────────────────────────────────────────────────────

@login_required(login_url='/')
def requests_list_view(request):
    items = (
        ServiceRequest.objects
        .select_related('customer', 'asset', 'assigned_to')
        .order_by('-created_on')
    )
    return render(request, 'requests/list.html', {
        'active_nav': 'requests',
        'section_title': 'Service Requests',
        'service_requests': items,
    })


@login_required(login_url='/')
def request_detail_view(request, pk):
    sr = get_object_or_404(
        ServiceRequest.objects.select_related('customer', 'asset', 'assigned_to'),
        pk=pk,
    )
    return render(request, 'requests/detail.html', {
        'active_nav': 'requests',
        'section_title': sr.subject or f'Request {sr.request_number}',
        'service_request': sr,
    })


# ─── Schedule ─────────────────────────────────────────────────────────────────

@login_required(login_url='/')
def schedule_view(request):
    """Upcoming jobs by date. Calendar (FullCalendar) will replace this in Phase 8.1."""
    today = timezone.localdate()
    jobs = (
        WorkOrder.objects
        .filter(scheduled_date__gte=today)
        .exclude(status__in=[
            WorkOrder.StatusChoices.COMPLETED,
            WorkOrder.StatusChoices.CANCELLED,
        ])
        .select_related('customer', 'assigned_to')
        .order_by('scheduled_date', 'scheduled_time')[:50]
    )
    unscheduled = (
        WorkOrder.objects
        .filter(scheduled_date__isnull=True)
        .exclude(status__in=[
            WorkOrder.StatusChoices.COMPLETED,
            WorkOrder.StatusChoices.CANCELLED,
        ])
        .select_related('customer', 'assigned_to')
        .order_by('-created_on')[:20]
    )
    return render(request, 'schedule/list.html', {
        'active_nav': 'schedule',
        'section_title': 'Schedule',
        'jobs': jobs,
        'unscheduled': unscheduled,
    })


# ─── Quotes ───────────────────────────────────────────────────────────────────

@login_required(login_url='/')
def quotes_list_view(request):
    quotes = (
        Quote.objects
        .select_related('customer', 'work_order')
        .order_by('-created_on')
    )
    return render(request, 'quotes/list.html', {
        'active_nav': 'quotes',
        'section_title': 'Quotes',
        'quotes': quotes,
    })


@login_required(login_url='/')
def quote_detail_view(request, pk):
    quote = get_object_or_404(
        Quote.objects.select_related('customer', 'work_order').prefetch_related('lines'),
        pk=pk,
    )
    return render(request, 'quotes/detail.html', {
        'active_nav': 'quotes',
        'section_title': f'Quote {quote.quote_number}' if quote.quote_number else 'Quote',
        'quote': quote,
    })


# ─── Invoices ─────────────────────────────────────────────────────────────────

@login_required(login_url='/')
def invoices_list_view(request):
    invoices = (
        Invoice.objects
        .select_related('customer')
        .order_by('-created_on')
    )
    return render(request, 'invoices/list.html', {
        'active_nav': 'invoices',
        'section_title': 'Invoices',
        'invoices': invoices,
    })


@login_required(login_url='/')
def invoice_detail_view(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related('customer').prefetch_related('payments'),
        pk=pk,
    )
    return render(request, 'invoices/detail.html', {
        'active_nav': 'invoices',
        'section_title': f'Invoice {invoice.invoice_number}' if invoice.invoice_number else 'Invoice',
        'invoice': invoice,
    })


# ─── Payments ─────────────────────────────────────────────────────────────────

@login_required(login_url='/')
def payments_list_view(request):
    payments = (
        Payments.objects
        .select_related('invoice', 'invoice__customer', 'bank')
        .order_by('-payment_date', '-created_on')
    )
    return render(request, 'payments/list.html', {
        'active_nav': 'payments',
        'section_title': 'Payments',
        'payments': payments,
    })


@login_required(login_url='/')
def payment_detail_view(request, pk):
    payment = get_object_or_404(
        Payments.objects.select_related('invoice', 'invoice__customer', 'bank'),
        pk=pk,
    )
    return render(request, 'payments/detail.html', {
        'active_nav': 'payments',
        'section_title': f'Payment {payment.payment_number}' if payment.payment_number else 'Payment',
        'payment': payment,
    })
