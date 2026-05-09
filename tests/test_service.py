# tests/test_service.py
# CRUD and basic functionality tests for all models in the service app.

from datetime import date
from decimal import Decimal

from tests.base import SDTATestCase
from lifecycle.models import LifecycleStateDef, LifecycleTransitionRule
from service.models import (
    Accounting, Bank, Invoice, InvoiceAsset, InvoiceLine,
    Ledger, Payments, Quote, QuoteAsset, QuoteLine,
    ServiceRequest, WorkOrder, WorkOrderInvoice, WorkOrderLine,
    WorkOrderTeam,
)


# ─── ServiceRequest ───────────────────────────────────────────────────────────

class ServiceRequestTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        sr = ServiceRequest.objects.create(
            customer=customer, subject='Leaky faucet'
        )
        self.assertEqual(sr.status, 'New')
        self.assertEqual(sr.priority, 'Medium')
        self.assertEqual(sr.subject, 'Leaky faucet')

    def test_str(self):
        customer = self.make_customer()
        sr = ServiceRequest.objects.create(
            customer=customer,
            subject='AC not cooling',
            request_number='SR-001',
        )
        self.assertIn('SR-001', str(sr))
        self.assertIn('AC not cooling', str(sr))

    def test_update_status(self):
        customer = self.make_customer()
        sr = ServiceRequest.objects.create(customer=customer, subject='Test')
        sr.status = 'In Progress'
        sr.save()
        sr.refresh_from_db()
        self.assertEqual(sr.status, 'In Progress')

    def test_priority_choices(self):
        customer = self.make_customer()
        sr = ServiceRequest.objects.create(
            customer=customer, subject='Critical', priority='Critical'
        )
        sr.refresh_from_db()
        self.assertEqual(sr.priority, 'Critical')

    def test_delete(self):
        customer = self.make_customer()
        sr = ServiceRequest.objects.create(customer=customer, subject='Del SR')
        sr_id = sr.id
        sr.delete()
        self.assertFalse(ServiceRequest.objects.filter(id=sr_id).exists())

    def test_optional_asset_fk(self):
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        sr = ServiceRequest.objects.create(
            customer=customer, subject='Asset SR', asset=asset
        )
        self.assertEqual(sr.asset, asset)


# ─── WorkOrder ────────────────────────────────────────────────────────────────

class WorkOrderTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        wo = WorkOrder.objects.create(customer=customer, subject='Install unit')
        self.assertEqual(wo.status, 'Draft')
        self.assertEqual(wo.priority, 'Medium')

    def test_str(self):
        customer = self.make_customer()
        wo = WorkOrder.objects.create(
            customer=customer, subject='Replace filter', wo_number='WO-001'
        )
        self.assertIn('WO-001', str(wo))
        self.assertIn('Replace filter', str(wo))

    def test_link_to_service_request(self):
        customer = self.make_customer()
        sr = ServiceRequest.objects.create(customer=customer, subject='Source SR')
        wo = WorkOrder.objects.create(
            customer=customer, subject='WO from SR', service_request=sr
        )
        self.assertEqual(wo.service_request, sr)

    def test_update_status(self):
        customer = self.make_customer()
        wo = WorkOrder.objects.create(customer=customer, subject='Status WO')
        wo.status = 'Completed'
        wo.save()
        wo.refresh_from_db()
        self.assertEqual(wo.status, 'Completed')

    def test_delete(self):
        customer = self.make_customer()
        wo = WorkOrder.objects.create(customer=customer, subject='Del WO')
        wo_id = wo.id
        wo.delete()
        self.assertFalse(WorkOrder.objects.filter(id=wo_id).exists())


# ─── WorkOrderTeam ────────────────────────────────────────────────────────────

class WorkOrderTeamTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        user = self.make_user(email='team_member@acme.com')
        wot = WorkOrderTeam.objects.create(work_order=wo, user=user, role='Lead')
        self.assertEqual(wot.role, 'Lead')

    def test_str(self):
        customer = self.make_customer()
        wo = WorkOrder.objects.create(customer=customer, subject='Team WO', wo_number='WO-T')
        user = self.make_user(email='wot_str@acme.com')
        wot = WorkOrderTeam.objects.create(work_order=wo, user=user)
        result = str(wot)
        self.assertIn('WO-T', result)

    def test_unique_wo_user(self):
        from django.db import IntegrityError
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        user = self.make_user(email='wot_uniq@acme.com')
        WorkOrderTeam.objects.create(work_order=wo, user=user)
        with self.assertRaises(IntegrityError):
            WorkOrderTeam.objects.create(work_order=wo, user=user)

    def test_delete(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        user = self.make_user(email='wot_del@acme.com')
        wot = WorkOrderTeam.objects.create(work_order=wo, user=user)
        wot_id = wot.id
        wot.delete()
        self.assertFalse(WorkOrderTeam.objects.filter(id=wot_id).exists())


# ─── WorkOrderLine ────────────────────────────────────────────────────────────

class WorkOrderLineTest(SDTATestCase):

    def test_create_part_line(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        product = self.make_product(name='WOL Part')
        line = WorkOrderLine.objects.create(
            work_order=wo, line_type='Part', product=product,
            quantity=2, unit_price='25.00', line_total='50.00',
        )
        self.assertEqual(line.line_type, 'Part')
        self.assertEqual(float(line.quantity), 2.0)

    def test_create_labor_line(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        line = WorkOrderLine.objects.create(
            work_order=wo, line_type='Labor',
            description='2 hrs @ $65/hr',
            quantity=2, unit_price='65.00', line_total='130.00',
        )
        self.assertEqual(line.line_type, 'Labor')

    def test_str(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        line = WorkOrderLine.objects.create(
            work_order=wo, description='Install part', quantity=1, unit_price='10.00',
        )
        self.assertIn('Install part', str(line))

    def test_delete(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        line = WorkOrderLine.objects.create(work_order=wo, quantity=1, unit_price='5.00')
        line_id = line.id
        line.delete()
        self.assertFalse(WorkOrderLine.objects.filter(id=line_id).exists())


# ─── Quote ────────────────────────────────────────────────────────────────────

class QuoteTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        q = Quote.objects.create(customer=customer)
        self.assertEqual(q.status, 'Draft')
        self.assertEqual(float(q.total), 0.0)

    def test_str(self):
        customer = self.make_customer()
        q = Quote.objects.create(customer=customer, quote_number='Q-001')
        result = str(q)
        self.assertIn('Q-001', result)

    def test_update_status(self):
        customer = self.make_customer()
        q = Quote.objects.create(customer=customer)
        q.status = 'Sent'
        q.save()
        q.refresh_from_db()
        self.assertEqual(q.status, 'Sent')

    def test_delete(self):
        customer = self.make_customer()
        q = Quote.objects.create(customer=customer)
        q_id = q.id
        q.delete()
        self.assertFalse(Quote.objects.filter(id=q_id).exists())


# ─── QuoteLine ────────────────────────────────────────────────────────────────

class QuoteLineTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        quote = Quote.objects.create(customer=customer)
        product = self.make_product(name='QL Product')
        ql = QuoteLine.objects.create(
            quote=quote, line_type='Part', product=product,
            quantity=1, unit_price='100.00',
        )
        self.assertEqual(float(ql.unit_price), 100.0)

    def test_str_uses_description(self):
        customer = self.make_customer()
        quote = Quote.objects.create(customer=customer)
        ql = QuoteLine.objects.create(
            quote=quote, description='Custom labor item',
            quantity=3, unit_price='50.00',
        )
        self.assertIn('Custom labor item', str(ql))

    def test_delete(self):
        customer = self.make_customer()
        quote = Quote.objects.create(customer=customer)
        product = self.make_product(name='QL Del Product')
        ql = QuoteLine.objects.create(
            quote=quote, product=product, quantity=1, unit_price='1.00'
        )
        ql_id = ql.id
        ql.delete()
        self.assertFalse(QuoteLine.objects.filter(id=ql_id).exists())


# ─── QuoteAsset ───────────────────────────────────────────────────────────────

class QuoteAssetTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        quote = Quote.objects.create(customer=customer)
        asset = self.make_asset(customer=customer)
        qa = QuoteAsset.objects.create(quote=quote, asset=asset)
        self.assertIsNotNone(qa.id)

    def test_str(self):
        customer = self.make_customer()
        quote = Quote.objects.create(customer=customer, quote_number='QA-STR')
        asset = self.make_asset(customer=customer, name='QA Asset')
        qa = QuoteAsset.objects.create(quote=quote, asset=asset)
        result = str(qa)
        self.assertIn('QA-STR', result)

    def test_delete(self):
        customer = self.make_customer()
        quote = Quote.objects.create(customer=customer)
        asset = self.make_asset(customer=customer)
        qa = QuoteAsset.objects.create(quote=quote, asset=asset)
        qa_id = qa.id
        qa.delete()
        self.assertFalse(QuoteAsset.objects.filter(id=qa_id).exists())


# ─── Invoice ──────────────────────────────────────────────────────────────────

class InvoiceTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(customer=customer)
        self.assertEqual(inv.status, 'Draft')
        self.assertEqual(float(inv.balance_due), 0.0)

    def test_str(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(customer=customer, invoice_number='INV-001')
        result = str(inv)
        self.assertIn('INV-001', result)

    def test_update_status(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(customer=customer)
        inv.status = 'Sent'
        inv.save()
        inv.refresh_from_db()
        self.assertEqual(inv.status, 'Sent')

    def test_delete(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(customer=customer)
        inv_id = inv.id
        inv.delete()
        self.assertFalse(Invoice.objects.filter(id=inv_id).exists())


# ─── InvoiceLine ──────────────────────────────────────────────────────────────

class InvoiceLineTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(customer=customer)
        product = self.make_product(name='IL Product')
        il = InvoiceLine.objects.create(
            invoice=inv, line_type='Part', product=product,
            quantity=2, unit_price='15.00',
        )
        self.assertEqual(float(il.quantity), 2.0)

    def test_delete(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(customer=customer)
        product = self.make_product(name='IL Del Product')
        il = InvoiceLine.objects.create(
            invoice=inv, product=product, quantity=1, unit_price='5.00'
        )
        il_id = il.id
        il.delete()
        self.assertFalse(InvoiceLine.objects.filter(id=il_id).exists())


# ─── InvoiceAsset ─────────────────────────────────────────────────────────────

class InvoiceAssetTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(customer=customer)
        asset = self.make_asset(customer=customer)
        ia = InvoiceAsset.objects.create(invoice=inv, asset=asset)
        self.assertIsNotNone(ia.id)

    def test_delete(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(customer=customer)
        asset = self.make_asset(customer=customer)
        ia = InvoiceAsset.objects.create(invoice=inv, asset=asset)
        ia_id = ia.id
        ia.delete()
        self.assertFalse(InvoiceAsset.objects.filter(id=ia_id).exists())


# ─── WorkOrderInvoice ─────────────────────────────────────────────────────────

class WorkOrderInvoiceTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        inv = Invoice.objects.create(customer=customer)
        woi = WorkOrderInvoice.objects.create(work_order=wo, invoice=inv)
        self.assertIsNotNone(woi.id)

    def test_unique_constraint(self):
        from django.db import IntegrityError
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        inv = Invoice.objects.create(customer=customer)
        WorkOrderInvoice.objects.create(work_order=wo, invoice=inv)
        with self.assertRaises(IntegrityError):
            WorkOrderInvoice.objects.create(work_order=wo, invoice=inv)

    def test_delete(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        inv = Invoice.objects.create(customer=customer)
        woi = WorkOrderInvoice.objects.create(work_order=wo, invoice=inv)
        woi_id = woi.id
        woi.delete()
        self.assertFalse(WorkOrderInvoice.objects.filter(id=woi_id).exists())


# ─── Bank ─────────────────────────────────────────────────────────────────────

class BankTest(SDTATestCase):

    def test_create(self):
        bank = Bank.objects.create(name='First National')
        self.assertEqual(bank.name, 'First National')
        self.assertEqual(bank.status, 'Active')

    def test_str(self):
        bank = Bank.objects.create(name='Str Bank')
        self.assertEqual(str(bank), 'Str Bank')

    def test_update(self):
        bank = Bank.objects.create(name='Old Bank')
        bank.name = 'New Bank'
        bank.save()
        bank.refresh_from_db()
        self.assertEqual(bank.name, 'New Bank')

    def test_delete(self):
        bank = Bank.objects.create(name='Del Bank')
        bank_id = bank.id
        bank.delete()
        self.assertFalse(Bank.objects.filter(id=bank_id).exists())


# ─── Payments ─────────────────────────────────────────────────────────────────

class PaymentsTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(customer=customer)
        payment = Payments.objects.create(
            invoice=inv, payment_date=date.today(),
            amount='500.00', method='Check',
        )
        self.assertEqual(float(payment.amount), 500.0)
        self.assertEqual(payment.method, 'Check')

    def test_str(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(customer=customer, invoice_number='PAY-INV')
        payment = Payments.objects.create(
            invoice=inv, payment_date=date.today(),
            amount='250.00', method='Cash',
        )
        result = str(payment)
        self.assertIn('250', result)

    def test_delete(self):
        customer = self.make_customer()
        inv = Invoice.objects.create(customer=customer)
        payment = Payments.objects.create(
            invoice=inv, payment_date=date.today(), amount='100.00',
        )
        pay_id = payment.id
        payment.delete()
        self.assertFalse(Payments.objects.filter(id=pay_id).exists())


# ─── Accounting ───────────────────────────────────────────────────────────────

class AccountingTest(SDTATestCase):

    def test_create(self):
        acc = Accounting.objects.create(
            account_number='4000',
            name='Service Revenue',
            account_type='Revenue',
        )
        self.assertEqual(acc.account_number, '4000')
        self.assertTrue(acc.is_active)

    def test_str(self):
        acc = Accounting.objects.create(
            account_number='1000', name='Cash', account_type='Asset'
        )
        result = str(acc)
        self.assertIn('1000', result)
        self.assertIn('Cash', result)

    def test_update(self):
        acc = Accounting.objects.create(
            account_number='5000', name='COGS', account_type='Expense'
        )
        acc.is_active = False
        acc.save()
        acc.refresh_from_db()
        self.assertFalse(acc.is_active)

    def test_delete(self):
        acc = Accounting.objects.create(
            account_number='9999', name='Del Acct', account_type='Expense'
        )
        acc_id = acc.id
        acc.delete()
        self.assertFalse(Accounting.objects.filter(id=acc_id).exists())


# ─── Ledger ───────────────────────────────────────────────────────────────────

class LedgerTest(SDTATestCase):

    def test_create(self):
        acc = Accounting.objects.create(
            account_number='4001', name='Lab Revenue', account_type='Revenue'
        )
        entry = Ledger.objects.create(
            account=acc,
            entry_type='Credit',
            amount='1000.00',
            transaction_date=date.today(),
        )
        self.assertEqual(entry.entry_type, 'Credit')
        self.assertEqual(float(entry.amount), 1000.0)

    def test_str(self):
        acc = Accounting.objects.create(
            account_number='4002', name='Str Revenue', account_type='Revenue'
        )
        entry = Ledger.objects.create(
            account=acc, entry_type='Debit',
            amount='500.00', transaction_date=date.today(),
        )
        result = str(entry)
        self.assertIn('Debit', result)
        self.assertIn('500', result)

    def test_delete(self):
        acc = Accounting.objects.create(
            account_number='4003', name='Del Revenue', account_type='Revenue'
        )
        entry = Ledger.objects.create(
            account=acc, entry_type='Credit',
            amount='100.00', transaction_date=date.today(),
        )
        entry_id = entry.id
        entry.delete()
        self.assertFalse(Ledger.objects.filter(id=entry_id).exists())


# ─── WorkOrder lifecycle sync ────────────────────────────────────────────────
#
# Verifies that execute_transition() updates WorkOrder's denormalized
# state-context fields (hold_*, completed_date) in addition to writing the
# audit record. Mirrors the Customer pattern.

class WorkOrderLifecycleSyncTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        for name, st in [
            ('Draft', 'normal'), ('Scheduled', 'normal'),
            ('In Progress', 'normal'), ('On Hold', 'locked'),
            ('Completed', 'final'), ('Cancelled', 'final'),
        ]:
            LifecycleStateDef.objects.create(
                tenant_id=self.tenant_id, entity_type='work_order',
                state_name=name, state_label=name, state_type=st,
            )
        for from_s, to_s, req in [
            ('Draft', 'Scheduled', False),
            ('Scheduled', 'In Progress', False),
            ('In Progress', 'On Hold', True),
            ('In Progress', 'Completed', False),
            ('On Hold', 'In Progress', False),
        ]:
            LifecycleTransitionRule.objects.create(
                tenant_id=self.tenant_id, entity_type='work_order',
                from_state=from_s, to_state=to_s, requires_reason=req,
            )
        self.user = self.make_user()
        # Need a WO in In Progress to test transitions to On Hold/Completed.
        self.wo = self.make_work_order()
        self.wo.execute_transition('Scheduled', self.user)
        self.wo.execute_transition('In Progress', self.user)

    def test_in_progress_to_on_hold_sets_hold_fields(self):
        self.wo.execute_transition('On Hold', self.user, reason='Parts ordered')
        self.wo.refresh_from_db()
        self.assertEqual(self.wo.status, 'On Hold')
        self.assertIsNotNone(self.wo.hold_date)
        self.assertEqual(self.wo.hold_reason, 'Parts ordered')

    def test_in_progress_to_completed_sets_completed_date(self):
        self.wo.execute_transition('Completed', self.user)
        self.wo.refresh_from_db()
        self.assertEqual(self.wo.status, 'Completed')
        self.assertIsNotNone(self.wo.completed_date)

    def test_on_hold_to_in_progress_clears_hold_fields(self):
        self.wo.execute_transition('On Hold', self.user, reason='Pause')
        self.wo.execute_transition('In Progress', self.user)
        self.wo.refresh_from_db()
        self.assertIsNone(self.wo.hold_date)
        self.assertEqual(self.wo.hold_reason, '')

    def test_direct_on_hold_without_reason_rejected(self):
        from django.core.exceptions import ValidationError
        self.wo.status = 'On Hold'
        with self.assertRaises(ValidationError) as ctx:
            self.wo.save()
        self.assertIn('hold_reason', ctx.exception.message_dict)


# ─── ServiceRequest lifecycle sync ──────────────────────────────────────────

class ServiceRequestLifecycleSyncTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        for name, st in [
            ('New', 'normal'), ('Assigned', 'normal'),
            ('In Progress', 'normal'), ('Resolved', 'normal'),
        ]:
            LifecycleStateDef.objects.create(
                tenant_id=self.tenant_id, entity_type='service_request',
                state_name=name, state_label=name, state_type=st,
            )
        for from_s, to_s in [('New', 'Assigned'), ('Assigned', 'In Progress'),
                             ('In Progress', 'Resolved'), ('Resolved', 'In Progress')]:
            LifecycleTransitionRule.objects.create(
                tenant_id=self.tenant_id, entity_type='service_request',
                from_state=from_s, to_state=to_s, requires_reason=False,
            )
        self.user = self.make_user()

    def test_in_progress_to_resolved_sets_resolved_date(self):
        sr = self.make_service_request()
        sr.execute_transition('Assigned', self.user)
        sr.execute_transition('In Progress', self.user)
        sr.execute_transition('Resolved', self.user)
        sr.refresh_from_db()
        self.assertEqual(sr.status, 'Resolved')
        self.assertIsNotNone(sr.resolved_date)

    def test_resolved_to_in_progress_clears_resolved_date(self):
        sr = self.make_service_request()
        sr.execute_transition('Assigned', self.user)
        sr.execute_transition('In Progress', self.user)
        sr.execute_transition('Resolved', self.user)
        sr.execute_transition('In Progress', self.user)
        sr.refresh_from_db()
        self.assertIsNone(sr.resolved_date)


# ─── Quote lifecycle sync ────────────────────────────────────────────────────

class QuoteLifecycleSyncTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        for name, st in [
            ('Draft', 'normal'), ('Sent', 'normal'), ('Accepted', 'normal'),
            ('Declined', 'final'), ('Expired', 'final'), ('Invoiced', 'final'),
        ]:
            LifecycleStateDef.objects.create(
                tenant_id=self.tenant_id, entity_type='quote',
                state_name=name, state_label=name, state_type=st,
            )
        for from_s, to_s in [('Draft', 'Sent'), ('Sent', 'Accepted'),
                             ('Sent', 'Declined'), ('Sent', 'Expired'),
                             ('Accepted', 'Invoiced')]:
            LifecycleTransitionRule.objects.create(
                tenant_id=self.tenant_id, entity_type='quote',
                from_state=from_s, to_state=to_s, requires_reason=False,
            )
        self.user = self.make_user()

    def _make_quote(self):
        return Quote.objects.create(customer=self.make_customer())

    def test_sent_sets_sent_at(self):
        q = self._make_quote()
        q.execute_transition('Sent', self.user)
        q.refresh_from_db()
        self.assertEqual(q.status, 'Sent')
        self.assertIsNotNone(q.sent_at)

    def test_accepted_sets_accepted_at(self):
        q = self._make_quote()
        q.execute_transition('Sent', self.user)
        q.execute_transition('Accepted', self.user)
        q.refresh_from_db()
        self.assertIsNotNone(q.accepted_at)

    def test_declined_sets_declined_at_and_reason(self):
        q = self._make_quote()
        q.execute_transition('Sent', self.user)
        q.execute_transition('Declined', self.user, reason='Too expensive')
        q.refresh_from_db()
        self.assertIsNotNone(q.declined_at)
        self.assertEqual(q.declined_reason, 'Too expensive')

    def test_invoiced_sets_invoiced_at(self):
        q = self._make_quote()
        q.execute_transition('Sent', self.user)
        q.execute_transition('Accepted', self.user)
        q.execute_transition('Invoiced', self.user)
        q.refresh_from_db()
        self.assertIsNotNone(q.invoiced_at)


# ─── Invoice lifecycle sync ──────────────────────────────────────────────────

class InvoiceLifecycleSyncTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        for name, st in [
            ('Draft', 'normal'), ('Sent', 'normal'), ('Partial', 'normal'),
            ('Paid', 'final'), ('Overdue', 'normal'), ('Voided', 'final'),
        ]:
            LifecycleStateDef.objects.create(
                tenant_id=self.tenant_id, entity_type='invoice',
                state_name=name, state_label=name, state_type=st,
            )
        for from_s, to_s, req in [
            ('Draft', 'Sent', False), ('Draft', 'Voided', True),
            ('Sent', 'Paid', False), ('Sent', 'Overdue', False),
            ('Sent', 'Voided', True),
        ]:
            LifecycleTransitionRule.objects.create(
                tenant_id=self.tenant_id, entity_type='invoice',
                from_state=from_s, to_state=to_s, requires_reason=req,
            )
        self.user = self.make_user()

    def _make_invoice(self):
        return Invoice.objects.create(customer=self.make_customer())

    def test_sent_sets_sent_at(self):
        inv = self._make_invoice()
        inv.execute_transition('Sent', self.user)
        inv.refresh_from_db()
        self.assertIsNotNone(inv.sent_at)

    def test_paid_sets_paid_at(self):
        inv = self._make_invoice()
        inv.execute_transition('Sent', self.user)
        inv.execute_transition('Paid', self.user)
        inv.refresh_from_db()
        self.assertIsNotNone(inv.paid_at)

    def test_overdue_sets_overdue_at(self):
        inv = self._make_invoice()
        inv.execute_transition('Sent', self.user)
        inv.execute_transition('Overdue', self.user)
        inv.refresh_from_db()
        self.assertIsNotNone(inv.overdue_at)

    def test_voided_sets_voided_at_and_reason(self):
        inv = self._make_invoice()
        inv.execute_transition('Voided', self.user, reason='Issued in error')
        inv.refresh_from_db()
        self.assertIsNotNone(inv.voided_at)
        self.assertEqual(inv.voided_reason, 'Issued in error')

    def test_direct_voided_without_reason_rejected(self):
        from django.core.exceptions import ValidationError
        inv = self._make_invoice()
        inv.status = 'Voided'
        with self.assertRaises(ValidationError) as ctx:
            inv.save()
        self.assertIn('voided_reason', ctx.exception.message_dict)
