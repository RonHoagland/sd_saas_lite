# service/services.py
# Business logic for entity conversions and complex operations in the service app.
# Source: Front-end Readiness Roadmap, Phase 2.

from django.core.exceptions import ValidationError
from django.db import transaction
from .models import (
    ServiceRequest, WorkOrder, WorkOrderLine,
    Quote, QuoteLine, Invoice, InvoiceLine, WorkOrderInvoice
)


def convert_service_request_to_work_order(service_request):
    """
    Creates a WorkOrder from a ServiceRequest.
    Preserves tenant_id, customer, asset, subject, and priority.
    """
    with transaction.atomic():
        work_order = WorkOrder.objects.create(
            tenant_id=service_request.tenant_id,
            service_request=service_request,
            customer=service_request.customer,
            asset=service_request.asset,
            subject=service_request.subject,
            description=service_request.description,
            priority=service_request.priority,
            status=WorkOrder.StatusChoices.DRAFT,
            created_by=service_request.created_by
        )
        
        # Optional: update status of service request via lifecycle transition
        # For now, we do a direct update or leave it to the caller.
        service_request.status = ServiceRequest.StatusChoices.ASSIGNED
        service_request.save()
        
        return work_order


def convert_service_request_to_quote(service_request):
    """
    Creates a Quote from a ServiceRequest.
    Quote has no 'service_request' or 'subject' field, so we store the
    originating SR context in the notes field and link via work_order if one
    exists later.
    """
    with transaction.atomic():
        quote = Quote.objects.create(
            tenant_id=service_request.tenant_id,
            customer=service_request.customer,
            notes=(
                f"Quote for {service_request.subject}. "
                f"Based on Service Request {service_request.request_number}. "
                f"{service_request.description}"
            ),
            status=Quote.StatusChoices.DRAFT,
            created_by=service_request.created_by,
        )

        if service_request.asset:
            from .models import QuoteAsset
            QuoteAsset.objects.create(
                tenant_id=service_request.tenant_id,
                quote=quote,
                asset=service_request.asset,
            )

        return quote


def convert_quote_to_work_order(quote):
    """
    Creates a WorkOrder from an accepted Quote.
    Copies all line items as initial work order lines.
    Quote has no 'subject' field; we derive the WO subject from the
    quote number and fall back to a generic label.
    """
    with transaction.atomic():
        subject = f"Work Order from Quote {quote.quote_number}" if quote.quote_number else "Work Order from Quote"
        work_order = WorkOrder.objects.create(
            tenant_id=quote.tenant_id,
            customer=quote.customer,
            subject=subject,
            description=quote.notes,
            priority=WorkOrder.PriorityChoices.MEDIUM,
            status=WorkOrder.StatusChoices.DRAFT,
            created_by=quote.created_by,
        )

        quote.work_order = work_order
        quote.save()

        for line in quote.lines.all():
            WorkOrderLine.objects.create(
                tenant_id=quote.tenant_id,
                work_order=work_order,
                line_type=line.line_type,
                product=line.product,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                line_total=line.line_total,
            )

        return work_order


def convert_quote_to_invoice(quote):
    """
    Create an Invoice from an Accepted Quote.

    Copies all line items and tax settings from the source quote, sets the
    quote's status to Invoiced, and links any associated WorkOrder via a
    WorkOrderInvoice junction row.

    Per Lite MVP V4 §18 / §20 and `LITE_BUILD_TODO` Phase 5.3, only quotes
    in the Accepted state may be invoiced. Drafts and Sent quotes still
    represent open negotiations; Declined / Expired / already-Invoiced
    quotes are terminal.

    Raises:
        ValidationError: when the source quote is not in Accepted state.
    """
    if quote.status != Quote.StatusChoices.ACCEPTED:
        raise ValidationError(
            f"Cannot create an invoice from a quote in '{quote.status}' "
            f"status. Only Accepted quotes may be invoiced."
        )

    with transaction.atomic():
        invoice = Invoice.objects.create(
            tenant_id=quote.tenant_id,
            customer=quote.customer,
            subtotal=quote.subtotal,
            tax_rate=quote.tax_rate,
            tax_amount=quote.tax_amount,
            total=quote.total,
            balance_due=quote.total,
            notes=f"Generated from Quote {quote.quote_number}. {quote.notes}",
            status=Invoice.StatusChoices.DRAFT,
            created_by=quote.created_by
        )

        # Copy line items
        for line in quote.lines.all():
            InvoiceLine.objects.create(
                tenant_id=quote.tenant_id,
                invoice=invoice,
                line_type=line.line_type,
                product=line.product,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                line_total=line.line_total
            )

        # Update Quote status
        quote.status = Quote.StatusChoices.INVOICED
        quote.save()

        # Link WorkOrder if present
        if quote.work_order:
            WorkOrderInvoice.objects.create(
                tenant_id=quote.tenant_id,
                work_order=quote.work_order,
                invoice=invoice
            )

        return invoice


def convert_work_order_to_invoice(work_order):
    """
    Creates an Invoice from a completed WorkOrder.
    Copies all line items (parts and labor).
    """
    with transaction.atomic():
        # Invoices for work orders usually start as Draft.
        invoice = Invoice.objects.create(
            tenant_id=work_order.tenant_id,
            customer=work_order.customer,
            # Totals will be calculated on save() once lines are added
            # but we can pre-calculate if we want.
            notes=f"Generated from Work Order {work_order.wo_number}.",
            status=Invoice.StatusChoices.DRAFT,
            created_by=work_order.created_by
        )

        # Copy line items
        for line in work_order.lines.all():
            InvoiceLine.objects.create(
                tenant_id=work_order.tenant_id,
                invoice=invoice,
                line_type=line.line_type,
                product=line.product,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                line_total=line.line_total
            )

        # Linking
        WorkOrderInvoice.objects.create(
            tenant_id=work_order.tenant_id,
            work_order=work_order,
            invoice=invoice
        )

        # Trigger total calculation on invoice
        invoice.save()

        return invoice
