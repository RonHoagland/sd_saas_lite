# tests/test_stage_a5.py — Stage A.5: status lock, snapshots, lite limits, line tax.

import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from config.tenant_context import set_current_tenant_id, clear_current_tenant_id
from crm.models import Customer, Person
from infrastructure.models import TenantState
from lifecycle.models import LifecycleStateDef, LifecycleTransitionRule
from service.models import (
    Quote,
    QuoteLine,
    QuoteSnapshot,
    Invoice,
    InvoiceLine,
    ServiceRequest,
)
from service.services import convert_service_request_to_quote
from tests.base import SDTATestCase
from users.models import User


def _make_lite_tenant():
    return TenantState.objects.create(
        subdomain=f'lite-{uuid.uuid4().hex[:8]}',
        company_name='Lite Co',
        owner_email='o@lite.com',
        status=TenantState.StatusChoices.ACTIVE,
        tier=TenantState.TierChoices.LITE,
    )


def _make_pro_tenant():
    return TenantState.objects.create(
        subdomain=f'pro-{uuid.uuid4().hex[:8]}',
        company_name='Pro Co',
        owner_email='o@pro.com',
        status=TenantState.StatusChoices.ACTIVE,
        tier=TenantState.TierChoices.PRO,
    )


@override_settings(SECURE_SSL_REDIRECT=False)
class LifecycleStatusNotWritableViaApiTest(SDTATestCase):
    """PATCH on lifecycle entities must not change ``status`` (use transition)."""

    def setUp(self):
        super().setUp()
        self.user = self.make_user()
        self.client = APIClient(enforce_csrf_checks=False)
        self.client.force_authenticate(user=self.user)

    def test_patch_quote_status_ignored(self):
        cust = self.make_customer()
        q = Quote.objects.create(customer=cust, status=Quote.StatusChoices.DRAFT)
        self.client.patch(
            f'/api/v1/service/quotes/{q.id}/',
            {'status': Quote.StatusChoices.SENT},
            format='json',
        )
        q.refresh_from_db()
        self.assertEqual(q.status, Quote.StatusChoices.DRAFT)


class QuoteSendSnapshotTest(SDTATestCase):
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

    def test_sent_creates_snapshot(self):
        cust = self.make_customer()
        q = Quote.objects.create(customer=cust, tax_rate=Decimal('0.10'))
        QuoteLine.objects.create(
            tenant_id=self.tenant_id, quote=q,
            quantity=1, unit_price=Decimal('100.00'),
        )
        q.execute_transition('Sent', self.user, reason='send')
        self.assertEqual(QuoteSnapshot.objects.filter(quote=q).count(), 1)
        snap = QuoteSnapshot.objects.get(quote=q)
        self.assertEqual(snap.subtotal, Decimal('100.00'))
        self.assertGreater(snap.tax_amount, Decimal('0'))


class InvoiceLineTaxAndDepositTest(SDTATestCase):
    def test_non_taxable_line_excluded_from_tax(self):
        cust = self.make_customer()
        inv = Invoice.objects.create(customer=cust, tax_rate=Decimal('0.10'))
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=Decimal('100.00'), is_taxable=True,
        )
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=Decimal('50.00'), is_taxable=False,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.subtotal, Decimal('150.00'))
        self.assertEqual(inv.tax_amount, Decimal('10.00'))
        self.assertEqual(inv.total, Decimal('160.00'))

    def test_deposit_reduces_balance_due(self):
        cust = self.make_customer()
        inv = Invoice.objects.create(
            customer=cust, tax_rate=Decimal('0'),
            deposit_applied=True, deposit_amount=Decimal('25.00'),
            status=Invoice.StatusChoices.SENT,
        )
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=Decimal('100.00'),
        )
        inv.refresh_from_db()
        self.assertEqual(inv.balance_due, Decimal('75.00'))


class LiteTierLimitConversionTest(TestCase):
    def test_quote_cap_blocks_on_lite(self):
        tenant = _make_lite_tenant()
        set_current_tenant_id(str(tenant.id))
        try:
            person = Person.objects.create(first_name='A', last_name='B')
            cust = Customer.objects.create(
                company_name='C', account_type='Commercial',
                primary_person=person,
            )
            user = User.objects.create_user(
                f'u-{uuid.uuid4().hex[:8]}',
                password='p', email='e@e.com',
                person=person,
            )
            sr = ServiceRequest.objects.create(
                customer=cust, subject='SR',
                requested_date='2026-01-01', created_by=user,
            )
            for _ in range(5):
                convert_service_request_to_quote(sr)
            with self.assertRaises(ValidationError):
                convert_service_request_to_quote(sr)
        finally:
            clear_current_tenant_id()

    def test_quote_cap_not_applied_on_pro(self):
        tenant = _make_pro_tenant()
        set_current_tenant_id(str(tenant.id))
        try:
            person = Person.objects.create(first_name='A', last_name='B')
            cust = Customer.objects.create(
                company_name='C', account_type='Commercial',
                primary_person=person,
            )
            user = User.objects.create_user(
                f'u-{uuid.uuid4().hex[:8]}',
                password='p', email='e2@e.com',
                person=person,
            )
            sr = ServiceRequest.objects.create(
                customer=cust, subject='SR',
                requested_date='2026-01-01', created_by=user,
            )
            for _ in range(6):
                convert_service_request_to_quote(sr)
        finally:
            clear_current_tenant_id()
