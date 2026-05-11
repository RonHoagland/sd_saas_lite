# service/lite_limits.py
# Lite-tier guard rails (ServizDesk Lite MVP — operational caps).

from django.core.exceptions import ValidationError

from infrastructure.models import TenantState

# Open quote = still negotiable (Draft or Sent).
LITE_MAX_OPEN_QUOTES_PER_CUSTOMER = 5

# Non-terminal work orders tied to a single service request.
LITE_MAX_ACTIVE_WORK_ORDERS_PER_SERVICE_REQUEST = 1

_WORK_ORDER_TERMINAL = ('Completed', 'Cancelled')


def _is_lite(tenant_id) -> bool:
    try:
        return TenantState.objects.get(pk=tenant_id).tier == TenantState.TierChoices.LITE
    except TenantState.DoesNotExist:
        return False


def enforce_lite_quote_cap(customer):
    if not _is_lite(customer.tenant_id):
        return
    from .models import Quote

    open_statuses = (Quote.StatusChoices.DRAFT, Quote.StatusChoices.SENT)
    n = Quote.objects.filter(customer=customer, status__in=open_statuses).count()
    if n >= LITE_MAX_OPEN_QUOTES_PER_CUSTOMER:
        raise ValidationError(
            f'Lite tier allows at most {LITE_MAX_OPEN_QUOTES_PER_CUSTOMER} open quotes '
            f'per customer.'
        )


def enforce_lite_work_order_cap(service_request):
    if not _is_lite(service_request.tenant_id):
        return
    from .models import WorkOrder

    n = WorkOrder.objects.filter(
        service_request=service_request,
    ).exclude(status__in=_WORK_ORDER_TERMINAL).count()
    if n >= LITE_MAX_ACTIVE_WORK_ORDERS_PER_SERVICE_REQUEST:
        raise ValidationError(
            f'Lite tier allows at most {LITE_MAX_ACTIVE_WORK_ORDERS_PER_SERVICE_REQUEST} '
            f'active work order(s) per service request.'
        )


def enforce_lite_invoice_cap_for_work_order(quote):
    """At most one non-paid invoice linked to the quote's work order (Lite)."""
    if not quote.work_order_id or not _is_lite(quote.tenant_id):
        return
    from .models import Invoice

    exists = Invoice.objects.filter(
        tenant_id=quote.tenant_id,
        work_order_invoices__work_order_id=quote.work_order_id,
        status__in=[
            Invoice.StatusChoices.DRAFT,
            Invoice.StatusChoices.SENT,
            Invoice.StatusChoices.PARTIAL,
            Invoice.StatusChoices.OVERDUE,
        ],
    ).exists()
    if exists:
        raise ValidationError(
            'Lite tier allows only one active invoice per job (work order). '
            'Close or void the existing invoice before creating another.'
        )
