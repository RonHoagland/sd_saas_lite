"""
API tests for the new Payments transition endpoints (B13).

Until this fix, PaymentsViewSet was CRUD-only despite the model having
a 10-state lifecycle. Front-ends could not drive payment-state changes
through the proper lifecycle gate, which meant:
  - No audit row written for state changes
  - No required-reason / required-role enforcement
  - Bypass-prone (direct PATCH on `status` was the only path)

These tests cover the new actions:
  - POST /api/v1/service/payments/{pk}/transition/
  - GET  /api/v1/service/payments/{pk}/available-transitions/
"""

from decimal import Decimal

from django.test import override_settings
from rest_framework.test import APIClient

from lifecycle.models import (
    LifecycleStateDef,
    LifecycleTransitionAudit,
    LifecycleTransitionRule,
)
from service.models import Invoice, Payments
from tests.base import SDTATestCase


def _seed_payment_lifecycle(tenant_id):
    """Minimal payment lifecycle for these tests — Open → Pending →
    Processing → Applied / Paid, plus Voided as a final terminal."""
    states = [
        ('Open', 'normal'), ('Pending', 'normal'),
        ('Processing', 'normal'), ('Applied', 'normal'),
        ('Paid', 'normal'), ('Voided', 'final'),
    ]
    for name, st in states:
        LifecycleStateDef.objects.create(
            tenant_id=tenant_id, entity_type='payment',
            state_name=name, state_label=name, state_type=st,
        )
    transitions = [
        ('Open', 'Pending'), ('Open', 'Voided'),
        ('Pending', 'Processing'), ('Pending', 'Voided'),
        ('Processing', 'Applied'), ('Processing', 'Paid'),
        ('Applied', 'Paid'),
    ]
    for from_s, to_s in transitions:
        LifecycleTransitionRule.objects.create(
            tenant_id=tenant_id, entity_type='payment',
            from_state=from_s, to_state=to_s, requires_reason=False,
        )


@override_settings(SECURE_SSL_REDIRECT=False)
class PaymentsApiTransitionTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        _seed_payment_lifecycle(self.tenant_id)
        self.user = self.make_user()
        self.client = APIClient(enforce_csrf_checks=False)
        self.client.force_authenticate(user=self.user)

        customer = self.make_customer()
        self.invoice = Invoice.objects.create(
            tenant_id=self.tenant_id, customer=customer,
        )
        self.payment = Payments.objects.create(
            tenant_id=self.tenant_id,
            invoice=self.invoice,
            amount=Decimal('100.00'),
            payment_date='2026-04-05',
            status=Payments.StatusChoices.OPEN,
        )

    def _url(self, action):
        return f'/api/v1/service/payments/{self.payment.id}/{action}/'

    def test_available_transitions_lists_valid_next_states(self):
        resp = self.client.get(self._url('available-transitions'))
        self.assertEqual(resp.status_code, 200)
        next_states = sorted(t['to_state'] for t in resp.json())
        # Open → Pending, Open → Voided are the seeded edges from Open.
        self.assertEqual(next_states, ['Pending', 'Voided'])

    def test_transition_advances_state(self):
        resp = self.client.post(
            self._url('transition'),
            {'to_state': 'Pending'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'Pending')
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'Pending')

    def test_transition_writes_audit_row(self):
        self.client.post(
            self._url('transition'),
            {'to_state': 'Pending'},
            format='json',
        )
        audit = LifecycleTransitionAudit.objects.filter(
            entity_type='payment',
            entity_id=self.payment.id,
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.from_state, 'Open')
        self.assertEqual(audit.to_state, 'Pending')
        self.assertEqual(audit.user_id, self.user.id)

    def test_invalid_transition_rejected(self):
        """No rule from Open → Applied; the API must return an error
        rather than silently mutating the status."""
        from lifecycle.exceptions import TransitionDeniedError
        with self.assertRaises(TransitionDeniedError):
            # The DRF exception handler maps this to 400, but the call
            # site re-raises through the test client. Catching it here
            # documents the contract.
            self.client.post(
                self._url('transition'),
                {'to_state': 'Applied'},
                format='json',
            )
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'Open')

    def test_unauthenticated_request_rejected(self):
        anon = APIClient(enforce_csrf_checks=False)
        resp = anon.get(self._url('available-transitions'))
        self.assertIn(resp.status_code, [401, 403])
