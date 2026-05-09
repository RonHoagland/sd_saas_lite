# service/tests.py
# Verification tests for Phase 2 Business Logic.

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from crm.models import Customer, Person
from .models import Invoice, InvoiceLine, Quote, QuoteLine, Payments, ServiceRequest, WorkOrder
from .services import convert_service_request_to_work_order, convert_quote_to_invoice

User = get_user_model()

class ServiceBusinessLogicTest(TestCase):
    def setUp(self):
        self.tenant_id = '00000000-0000-0000-0000-000000000001'
        person = Person.objects.create(
            tenant_id=self.tenant_id,
            first_name='Test',
            last_name='User',
            created_by='System',
            updated_by='System',
        )
        self.user = User.objects.create_user(
            'svc_test_user',
            tenant_id=self.tenant_id,
            password='password',
            email='test@example.com',
            person=person,
        )
        self.customer = Customer.objects.create(
            tenant_id=self.tenant_id,
            company_name='Test Customer',
            account_type='Commercial',
            created_by=self.user
        )

    def test_invoice_calculations(self):
        """Verify that invoice totals are calculated correctly."""
        invoice = Invoice.objects.create(
            tenant_id=self.customer.tenant_id,
            customer=self.customer,
            tax_rate=Decimal('0.1000'),  # 10% tax
            created_by=self.user
        )
        
        # Add line items
        InvoiceLine.objects.create(
            tenant_id=invoice.tenant_id,
            invoice=invoice,
            quantity=2,
            unit_price=50.00  # 100.00
        )
        InvoiceLine.objects.create(
            tenant_id=invoice.tenant_id,
            invoice=invoice,
            quantity=1,
            unit_price=25.00  # 25.00
        )
        
        invoice.refresh_from_db()
        self.assertEqual(invoice.subtotal, 125.00)
        self.assertEqual(invoice.tax_amount, 12.50)
        self.assertEqual(invoice.total, 137.50)
        self.assertEqual(invoice.balance_due, 137.50)
        self.assertEqual(invoice.status, Invoice.StatusChoices.DRAFT)

    def test_payment_updates_invoice(self):
        """Verify that payments update invoice amount_paid and status."""
        invoice = Invoice.objects.create(
            tenant_id=self.customer.tenant_id,
            customer=self.customer,
            tax_rate=0.0,
            created_by=self.user
        )
        InvoiceLine.objects.create(
            tenant_id=invoice.tenant_id,
            invoice=invoice,
            quantity=1,
            unit_price=100.00
        )
        invoice.refresh_from_db()
        
        # Apply partial payment
        Payments.objects.create(
            tenant_id=invoice.tenant_id,
            invoice=invoice,
            amount=40.00,
            payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
            created_by=self.user
        )
        
        invoice.refresh_from_db()
        self.assertEqual(invoice.amount_paid, 40.00)
        self.assertEqual(invoice.balance_due, 60.00)
        self.assertEqual(invoice.status, Invoice.StatusChoices.PARTIAL)
        
        # Apply remaining payment
        Payments.objects.create(
            tenant_id=invoice.tenant_id,
            invoice=invoice,
            amount=60.00,
            payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
            created_by=self.user
        )
        
        invoice.refresh_from_db()
        self.assertEqual(invoice.amount_paid, 100.00)
        self.assertEqual(invoice.balance_due, 0.00)
        self.assertEqual(invoice.status, Invoice.StatusChoices.PAID)

    def test_quote_to_invoice_conversion(self):
        """Verify that conversion services copy data correctly."""
        quote = Quote.objects.create(
            tenant_id=self.customer.tenant_id,
            customer=self.customer,
            tax_rate=0.0,
            created_by=self.user
        )
        QuoteLine.objects.create(
            tenant_id=quote.tenant_id,
            quote=quote,
            quantity=1,
            unit_price=200.00
        )
        quote.refresh_from_db()
        quote.status = Quote.StatusChoices.ACCEPTED
        quote.save()
        
        invoice = convert_quote_to_invoice(quote)
        
        self.assertEqual(invoice.customer, self.customer)
        self.assertEqual(invoice.total, 200.00)
        self.assertEqual(invoice.lines.count(), 1)
        self.assertEqual(invoice.lines.first().line_total, 200.00)
        self.assertEqual(quote.status, Quote.StatusChoices.INVOICED)
