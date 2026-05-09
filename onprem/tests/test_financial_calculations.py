# tests/test_financial_calculations.py
# Exhaustive tests for line-item auto-calculation, parent recalculate_totals,
# and payment → invoice status flow.

from decimal import Decimal

from service.models import (
    Invoice,
    InvoiceLine,
    Payments,
    Quote,
    QuoteLine,
    WorkOrder,
    WorkOrderLine,
)
from tests.base import SDTATestCase


# ═══════════════════════════════════════════════════════════════════════════════
# WorkOrderLine auto-calc
# ═══════════════════════════════════════════════════════════════════════════════

class WorkOrderLineAutoCalcTest(SDTATestCase):
    """WorkOrderLine.save() computes line_total = quantity * unit_price."""

    def _make_wo(self):
        return self.make_work_order(customer=self.make_customer(), subject='WOLine Test')

    def test_line_total_from_decimals(self):
        wo = self._make_wo()
        line = WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            quantity=Decimal('3'), unit_price=Decimal('25.50'),
        )
        self.assertEqual(line.line_total, Decimal('76.50'))

    def test_line_total_from_ints(self):
        wo = self._make_wo()
        line = WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            quantity=2, unit_price=50,
        )
        self.assertEqual(line.line_total, Decimal('100.00'))

    def test_line_total_from_floats(self):
        wo = self._make_wo()
        line = WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            quantity=1.5, unit_price=20.0,
        )
        self.assertEqual(line.line_total, Decimal('30.00'))

    def test_zero_quantity(self):
        wo = self._make_wo()
        line = WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            quantity=0, unit_price=Decimal('100.00'),
        )
        self.assertEqual(line.line_total, Decimal('0.00'))

    def test_zero_unit_price(self):
        wo = self._make_wo()
        line = WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            quantity=5, unit_price=0,
        )
        self.assertEqual(line.line_total, Decimal('0.00'))

    def test_updates_work_order_total(self):
        wo = self._make_wo()
        WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            quantity=1, unit_price=Decimal('50.00'),
        )
        WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            quantity=2, unit_price=Decimal('25.00'),
        )
        wo.refresh_from_db()
        self.assertEqual(wo.total_amount, Decimal('100.00'))

    def test_update_line_recalculates(self):
        wo = self._make_wo()
        line = WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            quantity=1, unit_price=Decimal('100.00'),
        )
        self.assertEqual(line.line_total, Decimal('100.00'))
        line.unit_price = Decimal('200.00')
        line.save()
        self.assertEqual(line.line_total, Decimal('200.00'))
        wo.refresh_from_db()
        self.assertEqual(wo.total_amount, Decimal('200.00'))

    def test_penny_precision(self):
        wo = self._make_wo()
        line = WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            quantity=Decimal('0.33'), unit_price=Decimal('10.00'),
        )
        self.assertEqual(line.line_total, Decimal('3.30'))


# ═══════════════════════════════════════════════════════════════════════════════
# QuoteLine auto-calc
# ═══════════════════════════════════════════════════════════════════════════════

class QuoteLineAutoCalcTest(SDTATestCase):
    """QuoteLine.save() computes line_total and triggers quote.recalculate_totals()."""

    def _make_quote(self, tax_rate=Decimal('0')):
        customer = self.make_customer()
        return Quote.objects.create(
            tenant_id=self.tenant_id, customer=customer, tax_rate=tax_rate,
        )

    def test_line_total_calculated(self):
        quote = self._make_quote()
        line = QuoteLine.objects.create(
            tenant_id=self.tenant_id, quote=quote,
            quantity=5, unit_price=Decimal('10.00'),
        )
        self.assertEqual(line.line_total, Decimal('50.00'))

    def test_quote_subtotal_updated(self):
        """QuoteLine.save() now persists parent Quote totals automatically."""
        quote = self._make_quote()
        QuoteLine.objects.create(
            tenant_id=self.tenant_id, quote=quote,
            quantity=2, unit_price=Decimal('30.00'),
        )
        QuoteLine.objects.create(
            tenant_id=self.tenant_id, quote=quote,
            quantity=1, unit_price=Decimal('20.00'),
        )
        quote.refresh_from_db()
        self.assertEqual(quote.subtotal, Decimal('80.00'))
        self.assertEqual(quote.total, Decimal('80.00'))

    def test_quote_with_tax(self):
        quote = self._make_quote(tax_rate=Decimal('0.1000'))
        QuoteLine.objects.create(
            tenant_id=self.tenant_id, quote=quote,
            quantity=1, unit_price=Decimal('100.00'),
        )
        quote.refresh_from_db()
        self.assertEqual(quote.subtotal, Decimal('100.00'))
        self.assertEqual(quote.tax_amount, Decimal('10.00'))
        self.assertEqual(quote.total, Decimal('110.00'))

    def test_empty_quote_zero_totals(self):
        quote = self._make_quote(tax_rate=Decimal('0.0800'))
        quote.save()
        quote.refresh_from_db()
        self.assertEqual(quote.subtotal, Decimal('0.00'))
        self.assertEqual(quote.total, Decimal('0.00'))


# ═══════════════════════════════════════════════════════════════════════════════
# InvoiceLine auto-calc
# ═══════════════════════════════════════════════════════════════════════════════

class InvoiceLineAutoCalcTest(SDTATestCase):
    """InvoiceLine.save() computes line_total and triggers invoice.recalculate_totals()."""

    def _make_invoice(self, tax_rate=Decimal('0')):
        customer = self.make_customer()
        return Invoice.objects.create(
            tenant_id=self.tenant_id, customer=customer, tax_rate=tax_rate,
        )

    def test_line_total_calculated(self):
        inv = self._make_invoice()
        line = InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=3, unit_price=Decimal('40.00'),
        )
        self.assertEqual(line.line_total, Decimal('120.00'))

    def test_invoice_subtotal_updated(self):
        inv = self._make_invoice()
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=Decimal('100.00'),
        )
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=2, unit_price=Decimal('50.00'),
        )
        inv.refresh_from_db()
        self.assertEqual(inv.subtotal, Decimal('200.00'))
        self.assertEqual(inv.total, Decimal('200.00'))
        self.assertEqual(inv.balance_due, Decimal('200.00'))

    def test_invoice_with_tax(self):
        inv = self._make_invoice(tax_rate=Decimal('0.0750'))
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=Decimal('200.00'),
        )
        inv.refresh_from_db()
        self.assertEqual(inv.subtotal, Decimal('200.00'))
        self.assertEqual(inv.tax_amount, Decimal('15.00'))
        self.assertEqual(inv.total, Decimal('215.00'))
        self.assertEqual(inv.balance_due, Decimal('215.00'))


# ═══════════════════════════════════════════════════════════════════════════════
# Invoice recalculate_totals — status auto-update
# ═══════════════════════════════════════════════════════════════════════════════

class InvoiceRecalculateTotalsStatusTest(SDTATestCase):
    """Invoice.recalculate_totals() auto-updates status based on balance."""

    def _make_invoice_with_line(self, amount, tax_rate=Decimal('0')):
        customer = self.make_customer()
        inv = Invoice.objects.create(
            tenant_id=self.tenant_id, customer=customer, tax_rate=tax_rate,
        )
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=amount,
        )
        inv.refresh_from_db()
        return inv

    def test_no_payment_stays_draft(self):
        inv = self._make_invoice_with_line(Decimal('100.00'))
        self.assertEqual(inv.status, Invoice.StatusChoices.DRAFT)

    def test_partial_payment_sets_partial(self):
        inv = self._make_invoice_with_line(Decimal('100.00'))
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('40.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.StatusChoices.PARTIAL)
        self.assertEqual(inv.amount_paid, Decimal('40.00'))
        self.assertEqual(inv.balance_due, Decimal('60.00'))

    def test_full_payment_sets_paid(self):
        inv = self._make_invoice_with_line(Decimal('100.00'))
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('100.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.StatusChoices.PAID)
        self.assertEqual(inv.balance_due, Decimal('0.00'))

    def test_overpayment_still_paid(self):
        inv = self._make_invoice_with_line(Decimal('50.00'))
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('60.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.StatusChoices.PAID)

    def test_voided_payment_not_counted(self):
        inv = self._make_invoice_with_line(Decimal('100.00'))
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('100.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.VOIDED,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.amount_paid, Decimal('0.00'))
        self.assertEqual(inv.status, Invoice.StatusChoices.DRAFT)

    def test_applied_payment_counted(self):
        inv = self._make_invoice_with_line(Decimal('100.00'))
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('100.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.APPLIED,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.StatusChoices.PAID)

    def test_multiple_payments_accumulate(self):
        inv = self._make_invoice_with_line(Decimal('100.00'))
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('30.00'), payment_date='2026-04-01',
            status=Payments.StatusChoices.PAID,
        )
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('30.00'), payment_date='2026-04-02',
            status=Payments.StatusChoices.PAID,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.amount_paid, Decimal('60.00'))
        self.assertEqual(inv.status, Invoice.StatusChoices.PARTIAL)

        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('40.00'), payment_date='2026-04-03',
            status=Payments.StatusChoices.PAID,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.amount_paid, Decimal('100.00'))
        self.assertEqual(inv.status, Invoice.StatusChoices.PAID)

    def test_zero_total_invoice_stays_draft(self):
        """An invoice with $0 total should not auto-flip to PAID."""
        customer = self.make_customer()
        inv = Invoice.objects.create(
            tenant_id=self.tenant_id, customer=customer,
        )
        inv.save()
        inv.refresh_from_db()
        self.assertEqual(inv.total, Decimal('0.00'))
        self.assertEqual(inv.status, Invoice.StatusChoices.DRAFT)


# ═══════════════════════════════════════════════════════════════════════════════
# Payments.save() triggers invoice refresh
# ═══════════════════════════════════════════════════════════════════════════════

class PaymentSaveTriggersInvoiceRefreshTest(SDTATestCase):
    """Payments.save() calls invoice.save() → recalculate_totals."""

    def test_creating_payment_updates_invoice(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(
            tenant_id=self.tenant_id, customer=customer,
        )
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=Decimal('200.00'),
        )
        inv.refresh_from_db()
        self.assertEqual(inv.balance_due, Decimal('200.00'))

        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('200.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.balance_due, Decimal('0.00'))
        self.assertEqual(inv.status, Invoice.StatusChoices.PAID)

    def test_updating_payment_amount_refreshes_invoice(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(
            tenant_id=self.tenant_id, customer=customer,
        )
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=Decimal('100.00'),
        )
        pmt = Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('50.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.StatusChoices.PARTIAL)

        pmt.amount = Decimal('100.00')
        pmt.save()
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.StatusChoices.PAID)
