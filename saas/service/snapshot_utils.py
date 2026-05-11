# service/snapshot_utils.py
# Immutable send-time snapshots for Quote / Invoice (Top-Down Phases 5.4 / 6.4).

from __future__ import annotations

from decimal import Decimal


def _line_dict(line):
    return {
        'line_type': line.line_type,
        'description': line.description,
        'quantity': str(line.quantity),
        'unit_price': str(line.unit_price),
        'line_total': str(line.line_total),
        'is_taxable': getattr(line, 'is_taxable', True),
        'is_discount': getattr(line, 'is_discount', False),
    }


def _customer_bits(customer):
    if customer is None:
        return '', '', '', ''
    phone = ''
    try:
        from crm.models import Phone
        p = Phone.objects.filter(customer=customer).order_by('-is_primary').first()
        if p:
            cc = (p.country_code or '').strip()
            phone = f'{cc}{p.number}'.strip()
    except Exception:
        phone = ''
    addr = ''
    try:
        from crm.models import Address
        a = Address.objects.filter(customer=customer).order_by('-is_primary').first()
        if a:
            parts = [a.street, a.street_2, a.city, a.state_code, a.zip]
            addr = ', '.join(x for x in parts if x)
    except Exception:
        addr = ''
    return (
        customer.company_name or '',
        customer.display_name or '',
        phone,
        addr,
    )


def record_quote_sent_snapshot(quote):
    """Persist a snapshot when a Quote transitions to Sent."""
    from .models import QuoteSnapshot

    quote.recalculate_totals()
    cust = quote.customer
    cname, dname, phone, addr = _customer_bits(cust)
    lines = [_line_dict(l) for l in quote.lines.all()]
    QuoteSnapshot.objects.create(
        tenant_id=quote.tenant_id,
        quote=quote,
        subtotal=quote.subtotal,
        tax_rate=quote.tax_rate,
        tax_amount=quote.tax_amount,
        total=quote.total,
        customer_company_name=cname[:200],
        customer_display_name=dname[:200],
        customer_phone=phone[:80],
        customer_address=addr[:1000],
        lines_json=lines,
    )


def record_invoice_sent_snapshot(invoice):
    """Persist a snapshot when an Invoice transitions to Sent."""
    from .models import InvoiceSnapshot

    invoice.recalculate_totals()
    cust = invoice.customer
    cname, dname, phone, addr = _customer_bits(cust)
    lines = [_line_dict(l) for l in invoice.lines.all()]
    InvoiceSnapshot.objects.create(
        tenant_id=invoice.tenant_id,
        invoice=invoice,
        subtotal=invoice.subtotal,
        tax_rate=invoice.tax_rate,
        tax_amount=invoice.tax_amount,
        total=invoice.total,
        deposit_applied=invoice.deposit_applied,
        deposit_amount=invoice.deposit_amount,
        customer_company_name=cname[:200],
        customer_display_name=dname[:200],
        customer_phone=phone[:80],
        customer_address=addr[:1000],
        lines_json=lines,
    )
