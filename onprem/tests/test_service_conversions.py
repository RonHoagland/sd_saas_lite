# tests/test_service_conversions.py
# Tests for all service conversion functions in service/services.py.

from decimal import Decimal

from django.db import IntegrityError

from service.models import (
    Invoice,
    InvoiceLine,
    Quote,
    QuoteAsset,
    QuoteLine,
    ServiceRequest,
    WorkOrder,
    WorkOrderInvoice,
    WorkOrderLine,
)
from service.services import (
    convert_quote_to_invoice,
    convert_quote_to_work_order,
    convert_service_request_to_quote,
    convert_service_request_to_work_order,
    convert_work_order_to_invoice,
)
from tests.base import SDTATestCase


class ConvertServiceRequestToWorkOrderTest(SDTATestCase):
    """convert_service_request_to_work_order copies fields and updates SR status."""

    def test_basic_conversion(self):
        customer = self.make_customer()
        sr = self.make_service_request(customer=customer, subject='Broken pipe')
        wo = convert_service_request_to_work_order(sr)
        self.assertEqual(wo.customer, customer)
        self.assertEqual(wo.subject, 'Broken pipe')
        self.assertEqual(wo.service_request, sr)
        self.assertEqual(wo.status, WorkOrder.StatusChoices.DRAFT)
        sr.refresh_from_db()
        self.assertEqual(sr.status, ServiceRequest.StatusChoices.ASSIGNED)

    def test_preserves_priority(self):
        customer = self.make_customer()
        sr = self.make_service_request(
            customer=customer, subject='Urgent', priority='High'
        )
        wo = convert_service_request_to_work_order(sr)
        self.assertEqual(wo.priority, 'High')

    def test_preserves_description(self):
        customer = self.make_customer()
        sr = ServiceRequest.objects.create(
            tenant_id=self.tenant_id, customer=customer,
            subject='Desc test', description='Full details here',
        )
        wo = convert_service_request_to_work_order(sr)
        self.assertEqual(wo.description, 'Full details here')

    def test_preserves_asset_link(self):
        customer = self.make_customer()
        asset = self.make_asset(name='Unit A', customer=customer)
        sr = self.make_service_request(customer=customer, subject='Asset SR', asset=asset)
        wo = convert_service_request_to_work_order(sr)
        self.assertEqual(wo.asset, asset)

    def test_preserves_tenant_id(self):
        customer = self.make_customer()
        sr = self.make_service_request(customer=customer, subject='Tenant check')
        wo = convert_service_request_to_work_order(sr)
        self.assertEqual(str(wo.tenant_id), str(self.tenant_id))


class ConvertServiceRequestToQuoteTest(SDTATestCase):
    """convert_service_request_to_quote creates a draft quote from SR."""

    def test_basic_conversion(self):
        customer = self.make_customer()
        sr = self.make_service_request(customer=customer, subject='Quote me')
        quote = convert_service_request_to_quote(sr)
        self.assertEqual(quote.customer, customer)
        self.assertEqual(quote.status, Quote.StatusChoices.DRAFT)
        self.assertIn('Quote me', quote.notes)

    def test_asset_linked_as_quote_asset(self):
        customer = self.make_customer()
        asset = self.make_asset(name='Unit B', customer=customer)
        sr = self.make_service_request(customer=customer, subject='Asset Quote', asset=asset)
        quote = convert_service_request_to_quote(sr)
        qa = QuoteAsset.objects.filter(quote=quote, asset=asset)
        self.assertTrue(qa.exists())

    def test_no_asset_no_quote_asset(self):
        customer = self.make_customer()
        sr = self.make_service_request(customer=customer, subject='No Asset')
        quote = convert_service_request_to_quote(sr)
        self.assertEqual(QuoteAsset.objects.filter(quote=quote).count(), 0)

    def test_preserves_tenant_id(self):
        customer = self.make_customer()
        sr = self.make_service_request(customer=customer, subject='Tenant Q')
        quote = convert_service_request_to_quote(sr)
        self.assertEqual(str(quote.tenant_id), str(self.tenant_id))


class ConvertQuoteToWorkOrderTest(SDTATestCase):
    """convert_quote_to_work_order copies lines and links to quote."""

    def test_basic_conversion(self):
        customer = self.make_customer()
        quote = Quote.objects.create(
            tenant_id=self.tenant_id, customer=customer,
            status=Quote.StatusChoices.ACCEPTED,
        )
        QuoteLine.objects.create(
            tenant_id=self.tenant_id, quote=quote,
            line_type='Part', description='Widget',
            quantity=3, unit_price=Decimal('10.00'),
        )
        quote.refresh_from_db()
        wo = convert_quote_to_work_order(quote)
        self.assertEqual(wo.customer, customer)
        self.assertEqual(wo.status, WorkOrder.StatusChoices.DRAFT)
        self.assertEqual(wo.lines.count(), 1)
        line = wo.lines.first()
        self.assertEqual(line.description, 'Widget')
        self.assertEqual(line.quantity, Decimal('3.00'))
        quote.refresh_from_db()
        self.assertEqual(quote.work_order, wo)

    def test_copies_multiple_lines(self):
        customer = self.make_customer()
        quote = Quote.objects.create(
            tenant_id=self.tenant_id, customer=customer,
        )
        for i in range(5):
            QuoteLine.objects.create(
                tenant_id=self.tenant_id, quote=quote,
                description=f'Line {i}', quantity=1, unit_price=Decimal('5.00'),
            )
        quote.refresh_from_db()
        wo = convert_quote_to_work_order(quote)
        self.assertEqual(wo.lines.count(), 5)

    def test_subject_derived_from_quote_number(self):
        customer = self.make_customer()
        quote = Quote.objects.create(
            tenant_id=self.tenant_id, customer=customer,
            quote_number='Q-001',
        )
        wo = convert_quote_to_work_order(quote)
        self.assertIn('Q-001', wo.subject)


class ConvertQuoteToInvoiceTest(SDTATestCase):
    """convert_quote_to_invoice copies lines, tax, and creates WO link if applicable."""

    def test_basic_conversion(self):
        customer = self.make_customer()
        quote = Quote.objects.create(
            tenant_id=self.tenant_id, customer=customer,
            tax_rate=Decimal('0.0800'), status=Quote.StatusChoices.ACCEPTED,
        )
        QuoteLine.objects.create(
            tenant_id=self.tenant_id, quote=quote,
            description='Service call', quantity=1, unit_price=Decimal('200.00'),
        )
        quote.refresh_from_db()

        invoice = convert_quote_to_invoice(quote)
        self.assertEqual(invoice.customer, customer)
        self.assertEqual(invoice.lines.count(), 1)
        self.assertEqual(invoice.status, Invoice.StatusChoices.DRAFT)
        quote.refresh_from_db()
        self.assertEqual(quote.status, Quote.StatusChoices.INVOICED)

    def test_with_work_order_creates_link(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer, subject='Linked WO')
        quote = Quote.objects.create(
            tenant_id=self.tenant_id, customer=customer,
            work_order=wo, status=Quote.StatusChoices.ACCEPTED,
        )
        QuoteLine.objects.create(
            tenant_id=self.tenant_id, quote=quote,
            description='Part', quantity=1, unit_price=Decimal('50.00'),
        )
        quote.refresh_from_db()
        invoice = convert_quote_to_invoice(quote)
        link = WorkOrderInvoice.objects.filter(work_order=wo, invoice=invoice)
        self.assertTrue(link.exists())

    def test_without_work_order_no_link(self):
        customer = self.make_customer()
        quote = Quote.objects.create(
            tenant_id=self.tenant_id, customer=customer,
            status=Quote.StatusChoices.ACCEPTED,
        )
        QuoteLine.objects.create(
            tenant_id=self.tenant_id, quote=quote,
            description='Solo', quantity=1, unit_price=Decimal('100.00'),
        )
        quote.refresh_from_db()
        invoice = convert_quote_to_invoice(quote)
        self.assertEqual(WorkOrderInvoice.objects.filter(invoice=invoice).count(), 0)


class ConvertWorkOrderToInvoiceTest(SDTATestCase):
    """convert_work_order_to_invoice copies WO lines to a new invoice."""

    def test_basic_conversion(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer, subject='WO Invoice')
        WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            description='Labor 4h', line_type='Labor',
            quantity=4, unit_price=Decimal('75.00'),
        )
        invoice = convert_work_order_to_invoice(wo)
        self.assertEqual(invoice.customer, customer)
        self.assertEqual(invoice.lines.count(), 1)
        link = WorkOrderInvoice.objects.get(work_order=wo, invoice=invoice)
        self.assertIsNotNone(link)

    def test_copies_multiple_lines(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer, subject='Multi Line WO')
        for i in range(3):
            WorkOrderLine.objects.create(
                tenant_id=self.tenant_id, work_order=wo,
                description=f'Item {i}', quantity=1, unit_price=Decimal('10.00'),
            )
        invoice = convert_work_order_to_invoice(wo)
        self.assertEqual(invoice.lines.count(), 3)

    def test_invoice_totals_recalculated(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer, subject='Total WO')
        WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            description='Big job', quantity=2, unit_price=Decimal('100.00'),
        )
        invoice = convert_work_order_to_invoice(wo)
        invoice.refresh_from_db()
        self.assertEqual(invoice.subtotal, Decimal('200.00'))
        self.assertEqual(invoice.total, Decimal('200.00'))

    def test_empty_work_order_produces_empty_invoice(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer, subject='Empty WO')
        invoice = convert_work_order_to_invoice(wo)
        self.assertEqual(invoice.lines.count(), 0)
        invoice.refresh_from_db()
        self.assertEqual(invoice.subtotal, Decimal('0.00'))
