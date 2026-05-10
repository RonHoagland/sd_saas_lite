# tests/test_financial_calculations.py
# Exhaustive tests for line-item auto-calculation, parent recalculate_totals,
# and payment → invoice status flow.

from decimal import Decimal

from lifecycle.models import (
    LifecycleStateDef,
    LifecycleTransitionAudit,
    LifecycleTransitionRule,
)
from lifecycle.services import SYSTEM_USER_ID
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


# ─── Helpers ────────────────────────────────────────────────────────────────

def _seed_invoice_lifecycle(tenant_id):
    """Seed Invoice lifecycle states + transitions used by the financial
    tests. Replicates the relevant subset of seed.py for tests that
    exercise payment-driven status changes through `execute_transition`.

    Invoice.recalculate_totals attempts to auto-transition to PARTIAL/PAID
    when payments are applied. Without these rules in place, the
    transition silently no-ops (correct fail-safe behaviour: numbers
    update, status stays put).
    """
    states = [
        ('Draft', 'normal'), ('Sent', 'normal'),
        ('Partial', 'normal'), ('Paid', 'final'),
        ('Overdue', 'normal'), ('Voided', 'final'),
    ]
    for name, st in states:
        LifecycleStateDef.objects.create(
            tenant_id=tenant_id, entity_type='invoice',
            state_name=name, state_label=name, state_type=st,
        )
    transitions = [
        ('Draft', 'Sent'),
        ('Sent', 'Partial'), ('Sent', 'Paid'), ('Sent', 'Overdue'),
        ('Partial', 'Paid'), ('Partial', 'Overdue'),
        ('Overdue', 'Partial'), ('Overdue', 'Paid'),
    ]
    for from_s, to_s in transitions:
        LifecycleTransitionRule.objects.create(
            tenant_id=tenant_id, entity_type='invoice',
            from_state=from_s, to_state=to_s, requires_reason=False,
        )


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
    """Invoice.recalculate_totals() goes through the lifecycle layer to
    auto-transition Sent → Partial / Paid as payments are applied."""

    def setUp(self):
        super().setUp()
        _seed_invoice_lifecycle(self.tenant_id)

    def _make_sent_invoice_with_line(self, amount, tax_rate=Decimal('0')):
        """Build an invoice in Sent state with a single line item.

        Status is set directly here to keep the test concise; production
        code reaches Sent via execute_transition (covered by
        test_service.InvoiceLifecycleSyncTest).
        """
        customer = self.make_customer()
        inv = Invoice.objects.create(
            tenant_id=self.tenant_id, customer=customer, tax_rate=tax_rate,
        )
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=amount,
        )
        inv.refresh_from_db()
        inv.status = Invoice.StatusChoices.SENT
        inv.save()
        return inv

    def test_no_payment_stays_sent(self):
        inv = self._make_sent_invoice_with_line(Decimal('100.00'))
        self.assertEqual(inv.status, Invoice.StatusChoices.SENT)

    def test_partial_payment_sets_partial(self):
        inv = self._make_sent_invoice_with_line(Decimal('100.00'))
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
        inv = self._make_sent_invoice_with_line(Decimal('100.00'))
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('100.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.StatusChoices.PAID)
        self.assertEqual(inv.balance_due, Decimal('0.00'))

    def test_overpayment_still_paid(self):
        inv = self._make_sent_invoice_with_line(Decimal('50.00'))
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('60.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.StatusChoices.PAID)

    def test_voided_payment_not_counted(self):
        inv = self._make_sent_invoice_with_line(Decimal('100.00'))
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('100.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.VOIDED,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.amount_paid, Decimal('0.00'))
        self.assertEqual(inv.status, Invoice.StatusChoices.SENT)

    def test_applied_payment_counted(self):
        inv = self._make_sent_invoice_with_line(Decimal('100.00'))
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('100.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.APPLIED,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.StatusChoices.PAID)

    def test_multiple_payments_accumulate(self):
        inv = self._make_sent_invoice_with_line(Decimal('100.00'))
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

    # ── Lifecycle gate: Draft invoices must be Sent before they can Pay ──

    def test_draft_invoice_payment_does_not_transition_silently(self):
        """A Draft invoice with a payment recorded against it is a real
        scenario (e.g. cash collected at the door before the invoice
        was formally sent). The numeric fields must update, but the
        status stays Draft until the user explicitly Sends — there is
        no Draft → Paid transition in the seed graph and we don't
        invent one silently."""
        customer = self.make_customer()
        inv = Invoice.objects.create(
            tenant_id=self.tenant_id, customer=customer,
        )
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=Decimal('100.00'),
        )
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('100.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        inv.refresh_from_db()
        # Numbers updated:
        self.assertEqual(inv.amount_paid, Decimal('100.00'))
        self.assertEqual(inv.balance_due, Decimal('0.00'))
        # Status untouched — Draft → Paid is not a valid transition.
        self.assertEqual(inv.status, Invoice.StatusChoices.DRAFT)


class InvoicePaymentLifecycleAuditTest(SDTATestCase):
    """Confirms the payment-driven auto-transition writes a proper
    LifecycleTransitionAudit row attributed to the System sentinel and
    sets paid_at via _apply_lifecycle_transition."""

    def setUp(self):
        super().setUp()
        _seed_invoice_lifecycle(self.tenant_id)

    def _make_sent_invoice(self, amount=Decimal('100.00')):
        customer = self.make_customer()
        inv = Invoice.objects.create(
            tenant_id=self.tenant_id, customer=customer,
        )
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=amount,
        )
        inv.refresh_from_db()
        inv.status = Invoice.StatusChoices.SENT
        inv.save()
        return inv

    def test_full_payment_writes_audit_row(self):
        inv = self._make_sent_invoice()
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('100.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        audit = LifecycleTransitionAudit.objects.filter(
            tenant_id=self.tenant_id,
            entity_type='invoice',
            entity_id=inv.id,
            to_state='Paid',
        ).first()
        self.assertIsNotNone(audit, 'expected a Sent → Paid audit row')
        self.assertEqual(audit.from_state, 'Sent')
        self.assertEqual(audit.user_id, SYSTEM_USER_ID)
        self.assertEqual(audit.user_display, 'System')

    def test_full_payment_sets_paid_at(self):
        inv = self._make_sent_invoice()
        self.assertIsNone(inv.paid_at)
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('100.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.StatusChoices.PAID)
        self.assertIsNotNone(
            inv.paid_at,
            'paid_at must be populated by _apply_lifecycle_transition',
        )

    def test_partial_payment_writes_audit_row(self):
        inv = self._make_sent_invoice()
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('40.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        audit = LifecycleTransitionAudit.objects.filter(
            tenant_id=self.tenant_id,
            entity_type='invoice',
            entity_id=inv.id,
            to_state='Partial',
        ).first()
        self.assertIsNotNone(audit, 'expected a Sent → Partial audit row')
        self.assertEqual(audit.user_id, SYSTEM_USER_ID)

    def test_no_audit_when_no_rule_exists(self):
        """A Draft invoice + payment should not produce an audit row
        because Draft → Paid is not a legal transition."""
        customer = self.make_customer()
        inv = Invoice.objects.create(
            tenant_id=self.tenant_id, customer=customer,
        )
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=Decimal('100.00'),
        )
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('100.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        self.assertFalse(
            LifecycleTransitionAudit.objects.filter(
                entity_type='invoice', entity_id=inv.id,
            ).exists(),
            'No audit row should be written when no transition rule fires.',
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Payments.save() triggers invoice refresh
# ═══════════════════════════════════════════════════════════════════════════════

class PaymentSaveTriggersInvoiceRefreshTest(SDTATestCase):
    """Payments.save() calls invoice.save() → recalculate_totals →
    payment-driven lifecycle transition."""

    def setUp(self):
        super().setUp()
        _seed_invoice_lifecycle(self.tenant_id)

    def _make_sent_invoice(self, line_amount):
        customer = self.make_customer()
        inv = Invoice.objects.create(
            tenant_id=self.tenant_id, customer=customer,
        )
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=line_amount,
        )
        inv.refresh_from_db()
        inv.status = Invoice.StatusChoices.SENT
        inv.save()
        return inv

    def test_creating_payment_updates_invoice(self):
        inv = self._make_sent_invoice(Decimal('200.00'))
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
        inv = self._make_sent_invoice(Decimal('100.00'))
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
