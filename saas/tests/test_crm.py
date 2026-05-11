# tests/test_crm.py
# CRUD and basic functionality tests for all models in the crm app.

from tests.base import SDTATestCase
from crm.models import (
    Address, Contact, Customer, Lead, Opportunity,
    OpportunityContacts, Person, Phone, Social,
)
from lifecycle.models import LifecycleStateDef, LifecycleTransitionRule


# ─── Person ───────────────────────────────────────────────────────────────────

class PersonTest(SDTATestCase):

    def test_create(self):
        p = Person.objects.create(first_name='Alice', last_name='Smith')
        self.assertEqual(p.first_name, 'Alice')
        self.assertEqual(p.last_name, 'Smith')
        self.assertEqual(p.tenant_id, self.tenant_id)

    def test_str(self):
        p = Person.objects.create(first_name='Bob', last_name='Jones')
        self.assertEqual(str(p), 'Bob Jones')

    def test_read(self):
        p = Person.objects.create(first_name='Carol', last_name='White')
        fetched = Person.objects.get(id=p.id)
        self.assertEqual(fetched.first_name, 'Carol')

    def test_update(self):
        p = Person.objects.create(first_name='Dave', last_name='Old')
        p.last_name = 'New'
        p.save()
        p.refresh_from_db()
        self.assertEqual(p.last_name, 'New')

    def test_delete(self):
        p = Person.objects.create(first_name='Eve', last_name='Del')
        p_id = p.id
        p.delete()
        self.assertFalse(Person.objects.filter(id=p_id).exists())

    def test_str_uses_preferred_name_when_set(self):
        p = Person.objects.create(
            first_name='Robert', last_name='Smith', preferred_name='Bobby',
        )
        self.assertEqual(str(p), 'Bobby Smith')

    def test_str_falls_back_to_first_name(self):
        p = Person.objects.create(first_name='Robert', last_name='Smith')
        self.assertEqual(str(p), 'Robert Smith')

    def test_full_legal_name_with_all_parts(self):
        from datetime import date
        p = Person.objects.create(
            prefix='Dr', first_name='Robert', middle_name='James',
            last_name='Smith', suffix='Jr',
        )
        self.assertEqual(p.full_legal_name(), 'Dr Robert James Smith, Jr')

    def test_full_legal_name_skips_empty_parts(self):
        p = Person.objects.create(first_name='Jane', last_name='Doe')
        self.assertEqual(p.full_legal_name(), 'Jane Doe')

    def test_date_of_birth_optional(self):
        from datetime import date
        p = Person.objects.create(
            first_name='DOB', last_name='Test', date_of_birth=date(1990, 6, 15),
        )
        p.refresh_from_db()
        self.assertEqual(p.date_of_birth, date(1990, 6, 15))


# ─── Customer ─────────────────────────────────────────────────────────────────

class CustomerTest(SDTATestCase):

    def test_create_minimal(self):
        # Residential default — supply primary_person to satisfy clean().
        person = self.make_person()
        c = Customer.objects.create(company_name='Acme', primary_person=person)
        self.assertEqual(c.company_name, 'Acme')
        self.assertEqual(c.status, 'Active')
        self.assertEqual(c.account_type, 'Residential')

    def test_create_commercial(self):
        c = Customer.objects.create(
            company_name='BigCorp',
            account_type='Commercial',
        )
        c.account.tax_exempt = True
        c.account.save()
        self.assertEqual(c.account_type, 'Commercial')
        self.assertTrue(c.account.tax_exempt)

    def test_str_uses_company_name(self):
        c = Customer.objects.create(company_name='StrCo', account_type='Commercial')
        self.assertEqual(str(c), 'StrCo')

    def test_str_falls_back_to_number(self):
        c = Customer.objects.create(customer_number='C-001', account_type='Commercial')
        self.assertEqual(str(c), 'C-001')

    def test_read(self):
        c = Customer.objects.create(company_name='ReadCo', account_type='Commercial')
        fetched = Customer.objects.get(id=c.id)
        self.assertEqual(fetched.company_name, 'ReadCo')

    def test_update_status(self):
        c = Customer.objects.create(company_name='StatusCo', account_type='Commercial')
        c.status = 'Hold'
        c.hold_reason = 'Awaiting payment'  # required by save() validation
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'Hold')

    def test_total_payments_count_via_invoice(self):
        from service.models import Invoice, InvoiceLine, Payments
        cust = self.make_customer(company_name='PayCo', account_type='Commercial')
        other = self.make_customer(company_name='OtherCo', account_type='Commercial')
        inv = Invoice.objects.create(customer=cust, tax_rate=0)
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv, quantity=1, unit_price=100,
        )
        inv_other = Invoice.objects.create(customer=other, tax_rate=0)
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv_other, quantity=1, unit_price=50,
        )
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv, amount=10,
            payment_date='2026-05-01', status=Payments.StatusChoices.PAID,
        )
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv, amount=20,
            payment_date='2026-05-02', status=Payments.StatusChoices.PAID,
        )
        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv_other, amount=50,
            payment_date='2026-05-03', status=Payments.StatusChoices.PAID,
        )
        self.assertEqual(cust.total_payments_count, 2)
        self.assertEqual(other.total_payments_count, 1)
        self.assertCountEqual(
            list(cust.payments().values_list('amount', flat=True)),
            [10, 20],
        )

    def test_delete(self):
        c = Customer.objects.create(company_name='DelCo', account_type='Commercial')
        c_id = c.id
        c.delete()
        self.assertFalse(Customer.objects.filter(id=c_id).exists())

    def test_tags_default_empty_list(self):
        c = Customer.objects.create(company_name='TagCo', account_type='Commercial')
        self.assertEqual(c.tags, [])

    def test_credit_limit_default(self):
        c = Customer.objects.create(company_name='CreditCo', account_type='Commercial')
        self.assertEqual(float(c.account.credit_limit), 0.0)

    def test_account_auto_created(self):
        c = Customer.objects.create(company_name='AutoCo', account_type='Commercial')
        self.assertIsNotNone(c.account)
        self.assertEqual(c.account.credit_status, 'Good')
        self.assertEqual(c.account.tenant_id, c.tenant_id)


# ─── Customer lifecycle sync ─────────────────────────────────────────────────
#
# Verifies that execute_transition() updates Customer's denormalized
# state-context fields (hold_*, closed_*, inactive_*) in addition to writing
# the audit record. The audit log is canonical; these fields are a synced
# cache for fast display.

class CustomerLifecycleSyncTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        # Seed the state defs and transition rules execute_transition() needs.
        for name, st in [('Active', 'normal'), ('Inactive', 'normal'),
                         ('Hold', 'locked'), ('Closed', 'final')]:
            LifecycleStateDef.objects.create(
                tenant_id=self.tenant_id,
                entity_type='customer',
                state_name=name, state_label=name, state_type=st,
            )
        for from_s, to_s, req in [
            ('Active', 'Hold', True), ('Active', 'Closed', True),
            ('Active', 'Inactive', False),
            ('Hold', 'Active', False), ('Hold', 'Closed', True),
            ('Inactive', 'Active', False),
        ]:
            LifecycleTransitionRule.objects.create(
                tenant_id=self.tenant_id, entity_type='customer',
                from_state=from_s, to_state=to_s, requires_reason=req,
            )
        self.user = self.make_user()

    def test_active_to_hold_sets_hold_fields(self):
        c = self.make_customer(company_name='SyncCo')
        c.execute_transition('Hold', self.user, reason='Awaiting payment')
        c.refresh_from_db()
        self.assertEqual(c.status, 'Hold')
        self.assertIsNotNone(c.hold_date)
        self.assertEqual(c.hold_reason, 'Awaiting payment')

    def test_active_to_closed_sets_closed_fields(self):
        c = self.make_customer()
        c.execute_transition('Closed', self.user, reason='Customer left')
        c.refresh_from_db()
        self.assertEqual(c.status, 'Closed')
        self.assertIsNotNone(c.closed_at)
        self.assertEqual(c.closed_reason, 'Customer left')

    def test_active_to_inactive_sets_inactive_fields(self):
        c = self.make_customer()
        c.execute_transition('Inactive', self.user, reason='Dormant')
        c.refresh_from_db()
        self.assertEqual(c.status, 'Inactive')
        self.assertIsNotNone(c.inactive_at)
        self.assertEqual(c.inactive_reason, 'Dormant')

    def test_hold_to_active_clears_hold_fields(self):
        c = self.make_customer()
        c.execute_transition('Hold', self.user, reason='Awaiting')
        c.execute_transition('Active', self.user)
        c.refresh_from_db()
        self.assertEqual(c.status, 'Active')
        self.assertIsNone(c.hold_date)
        self.assertEqual(c.hold_reason, '')

    def test_hold_to_closed_clears_hold_and_sets_closed(self):
        c = self.make_customer()
        c.execute_transition('Hold', self.user, reason='Awaiting')
        c.execute_transition('Closed', self.user, reason='Gave up')
        c.refresh_from_db()
        self.assertEqual(c.status, 'Closed')
        self.assertIsNone(c.hold_date)
        self.assertEqual(c.hold_reason, '')
        self.assertIsNotNone(c.closed_at)
        self.assertEqual(c.closed_reason, 'Gave up')

    def test_inactive_to_active_clears_inactive_fields(self):
        c = self.make_customer()
        c.execute_transition('Inactive', self.user)
        c.execute_transition('Active', self.user)
        c.refresh_from_db()
        self.assertEqual(c.status, 'Active')
        self.assertIsNone(c.inactive_at)
        self.assertEqual(c.inactive_reason, '')

    def test_audit_record_is_also_written(self):
        c = self.make_customer()
        c.execute_transition('Hold', self.user, reason='Awaiting')
        history = list(c.get_transition_history())
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].from_state, 'Active')
        self.assertEqual(history[0].to_state, 'Hold')
        self.assertEqual(history[0].reason, 'Awaiting')


# ─── Customer expanded fields ─────────────────────────────────────────────────

class CustomerDoNotContactCascadeTest(SDTATestCase):
    """Master/granular DNC sync — see Customer.save() (per Ron, Apr 2026)."""

    def test_master_true_cascades_to_granular(self):
        c = self.make_customer(do_not_contact=True)
        c.refresh_from_db()
        self.assertTrue(c.do_not_email)
        self.assertTrue(c.do_not_call)
        self.assertTrue(c.do_not_sms)
        self.assertTrue(c.do_not_contact)

    def test_any_granular_false_clears_master(self):
        c = self.make_customer(do_not_contact=True)
        c.do_not_email = False
        c.save()
        c.refresh_from_db()
        self.assertFalse(c.do_not_contact)

    def test_all_granular_true_does_not_promote_master(self):
        c = self.make_customer(
            do_not_email=True, do_not_call=True, do_not_sms=True,
        )
        c.refresh_from_db()
        # Master stays False — user setting all three granular individually
        # is intentional and we don't auto-promote.
        self.assertFalse(c.do_not_contact)


class CustomerEncryptedFieldsTest(SDTATestCase):
    """tax_id / ein / vat_number must be encrypted at rest in the DB column."""

    def test_tax_id_roundtrip(self):
        c = self.make_customer(tax_id='12-3456789')
        c.refresh_from_db()
        self.assertEqual(c.tax_id, '12-3456789')

    def test_tax_id_stored_encrypted(self):
        from django.db import connection
        c = self.make_customer(tax_id='SECRET-VALUE-XYZ')
        with connection.cursor() as cur:
            cur.execute(
                'SELECT tax_id FROM crm_customer WHERE id = %s', [str(c.id)]
            )
            raw = cur.fetchone()[0]
        # Raw column must be ciphertext (v1: prefix), never the plaintext.
        self.assertTrue(raw.startswith('v1:'))
        self.assertNotIn('SECRET-VALUE-XYZ', raw)

    def test_ein_and_vat_roundtrip(self):
        c = self.make_customer(ein='98-7654321', vat_number='GB123456789')
        c.refresh_from_db()
        self.assertEqual(c.ein, '98-7654321')
        self.assertEqual(c.vat_number, 'GB123456789')

    def test_blank_encrypted_field_stays_blank(self):
        c = self.make_customer()  # no tax_id provided
        c.refresh_from_db()
        self.assertEqual(c.tax_id, '')


class CustomerSerializerCustomerSinceTest(SDTATestCase):
    """customer_since is editable only by Tenant Admins once set."""

    def _request_for(self, user):
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        return Request(APIRequestFactory().patch('/'), parsers=[])

    def _serializer(self, customer, user, data):
        from crm.api import CustomerSerializer
        req = self._request_for(user)
        req.user = user
        return CustomerSerializer(
            instance=customer, data=data, partial=True, context={'request': req},
        )

    def test_first_set_allowed_by_non_admin(self):
        from datetime import date
        non_admin = self.make_user()
        c = self.make_customer()  # customer_since=None initially
        s = self._serializer(c, non_admin, {'customer_since': '2026-01-01'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_change_blocked_for_non_admin(self):
        from datetime import date
        non_admin = self.make_user()
        c = self.make_customer(customer_since=date(2026, 1, 1))
        s = self._serializer(c, non_admin, {'customer_since': '2026-06-01'})
        self.assertFalse(s.is_valid())
        self.assertIn('customer_since', s.errors)

    def test_change_allowed_for_admin(self):
        from datetime import date
        admin = self.make_user(is_tenant_admin=True)
        c = self.make_customer(customer_since=date(2026, 1, 1))
        s = self._serializer(c, admin, {'customer_since': '2026-06-01'})
        self.assertTrue(s.is_valid(), s.errors)


class CustomerReasonRequiredTest(SDTATestCase):
    """Defense-in-depth: Customer.save() rejects status=Hold/Closed/Inactive
    without the matching reason. Audit-spec rule (V6 Customer notes); the
    lifecycle service already enforces this on transitions, but direct
    status writes bypass the lifecycle. This catches both paths."""

    def test_hold_without_reason_rejected(self):
        from django.core.exceptions import ValidationError
        c = self.make_customer()
        c.status = 'Hold'
        with self.assertRaises(ValidationError) as ctx:
            c.save()
        self.assertIn('hold_reason', ctx.exception.message_dict)

    def test_hold_with_reason_accepted(self):
        c = self.make_customer()
        c.status = 'Hold'
        c.hold_reason = 'Awaiting docs'
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'Hold')

    def test_closed_without_reason_rejected(self):
        from django.core.exceptions import ValidationError
        c = self.make_customer()
        c.status = 'Closed'
        with self.assertRaises(ValidationError) as ctx:
            c.save()
        self.assertIn('closed_reason', ctx.exception.message_dict)

    def test_inactive_no_reason_required(self):
        # V6 spec: Inactive is a soft pause with no required reason.
        # Direct write must succeed.
        c = self.make_customer()
        c.status = 'Inactive'
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'Inactive')

    def test_active_status_no_reason_required(self):
        # Default Active state; no _reason field needed.
        c = self.make_customer()
        self.assertEqual(c.status, 'Active')


class CustomerPrimaryPersonValidationTest(SDTATestCase):
    """Residential customers should be linked to a Person via primary_person.
    Enforced by Customer.clean() (model layer, opt-in via full_clean) AND
    CustomerSerializer.validate (always at API boundary)."""

    def test_save_rejects_residential_without_person(self):
        # TenantModel.save() calls full_clean(), which calls Customer.clean(),
        # so the ValidationError fires during create — not afterwards.
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            Customer.objects.create(
                account_type='Residential', company_name='X',
            )
        self.assertIn('primary_person', ctx.exception.message_dict)

    def test_save_accepts_residential_with_person(self):
        person = self.make_person()
        c = Customer.objects.create(
            account_type='Residential', company_name='Y', primary_person=person,
        )
        self.assertEqual(c.primary_person, person)

    def test_save_accepts_commercial_without_person(self):
        c = Customer.objects.create(
            account_type='Commercial', company_name='Acme',
        )
        self.assertIsNone(c.primary_person)

    def test_serializer_rejects_residential_without_person(self):
        from crm.api import CustomerSerializer
        s = CustomerSerializer(data={
            'account_type': 'Residential',
            'company_name': 'Anonymous',
        })
        self.assertFalse(s.is_valid())
        self.assertIn('primary_person', s.errors)

    def test_serializer_accepts_partial_update_when_existing_has_person(self):
        # Partial update (PATCH) on a Residential customer that already has a
        # primary_person should not require resending primary_person.
        from crm.api import CustomerSerializer
        person = self.make_person()
        c = self.make_customer(account_type='Residential', primary_person=person)
        s = CustomerSerializer(
            instance=c, data={'company_name': 'Renamed'}, partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)


# ─── Contact ──────────────────────────────────────────────────────────────────

class ContactTest(SDTATestCase):

    def test_create(self):
        person = self.make_person()
        customer = self.make_customer()
        c = Contact.objects.create(person=person, customer=customer)
        self.assertEqual(c.status, 'Active')
        self.assertFalse(c.is_primary)

    def test_str(self):
        person = Person.objects.create(first_name='Frank', last_name='G')
        customer = self.make_customer()
        c = Contact.objects.create(person=person, customer=customer)
        self.assertIn('Frank', str(c))

    def test_primary_flag(self):
        person = self.make_person()
        customer = self.make_customer()
        c = Contact.objects.create(person=person, customer=customer, is_primary=True)
        c.refresh_from_db()
        self.assertTrue(c.is_primary)

    def test_update_role(self):
        person = self.make_person()
        customer = self.make_customer()
        c = Contact.objects.create(person=person, customer=customer)
        c.role_title = 'Procurement Manager'
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.role_title, 'Procurement Manager')

    def test_delete(self):
        person = self.make_person()
        customer = self.make_customer()
        c = Contact.objects.create(person=person, customer=customer)
        c_id = c.id
        c.delete()
        self.assertFalse(Contact.objects.filter(id=c_id).exists())

    def test_role_flags_default_false(self):
        person = self.make_person()
        customer = self.make_customer()
        c = Contact.objects.create(person=person, customer=customer)
        self.assertFalse(c.is_decision_maker)
        self.assertFalse(c.is_billing_contact)
        self.assertFalse(c.is_technical_contact)
        self.assertFalse(c.is_emergency_contact)

    def test_role_flags_set(self):
        person = self.make_person()
        customer = self.make_customer()
        c = Contact.objects.create(
            person=person, customer=customer,
            is_decision_maker=True, is_billing_contact=True,
        )
        c.refresh_from_db()
        self.assertTrue(c.is_decision_maker)
        self.assertTrue(c.is_billing_contact)

    def test_reports_to_org_hierarchy(self):
        manager_person = self.make_person(first_name='Manager', last_name='M')
        report_person = self.make_person(first_name='Report', last_name='R')
        customer = self.make_customer()
        manager = Contact.objects.create(person=manager_person, customer=customer)
        report = Contact.objects.create(
            person=report_person, customer=customer, reports_to=manager,
        )
        report.refresh_from_db()
        self.assertEqual(report.reports_to, manager)
        # Reverse relation
        self.assertIn(report, manager.direct_reports.all())

    def test_reports_to_set_null_on_manager_delete(self):
        manager_person = self.make_person(first_name='Boss', last_name='X')
        report_person = self.make_person(first_name='Junior', last_name='Y')
        customer = self.make_customer()
        manager = Contact.objects.create(person=manager_person, customer=customer)
        report = Contact.objects.create(
            person=report_person, customer=customer, reports_to=manager,
        )
        manager.delete()
        report.refresh_from_db()
        self.assertIsNone(report.reports_to)

    def test_serializer_rejects_self_report(self):
        from crm.api import ContactSerializer
        person = self.make_person()
        customer = self.make_customer()
        c = Contact.objects.create(person=person, customer=customer)
        s = ContactSerializer(
            instance=c, data={'reports_to': str(c.id)}, partial=True,
        )
        self.assertFalse(s.is_valid())
        self.assertIn('reports_to', s.errors)


# ─── Address ──────────────────────────────────────────────────────────────────

class AddressTest(SDTATestCase):

    def test_create_for_customer(self):
        customer = self.make_customer()
        addr = Address.objects.create(
            customer=customer,
            street='123 Main St',
            city='Austin',
            state='TX',
            zip='78701',
        )
        self.assertEqual(addr.city, 'Austin')
        self.assertEqual(addr.address_type, 'Service')

    def test_str(self):
        customer = self.make_customer()
        addr = Address.objects.create(
            customer=customer,
            street='456 Oak Ave',
            city='Dallas',
        )
        result = str(addr)
        self.assertIn('456 Oak Ave', result)
        self.assertIn('Dallas', result)

    def test_billing_type(self):
        customer = self.make_customer()
        addr = Address.objects.create(
            customer=customer,
            address_type='Billing',
            street='789 Elm Rd',
            city='Houston',
        )
        addr.refresh_from_db()
        self.assertEqual(addr.address_type, 'Billing')

    def test_update(self):
        customer = self.make_customer()
        addr = Address.objects.create(customer=customer, city='Old City')
        addr.city = 'New City'
        addr.save()
        addr.refresh_from_db()
        self.assertEqual(addr.city, 'New City')

    def test_delete(self):
        customer = self.make_customer()
        addr = Address.objects.create(customer=customer, city='Del City')
        addr_id = addr.id
        addr.delete()
        self.assertFalse(Address.objects.filter(id=addr_id).exists())

    def test_geocoding_fields(self):
        from datetime import datetime, timezone as tz
        customer = self.make_customer()
        now = datetime(2026, 5, 3, tzinfo=tz.utc)
        addr = Address.objects.create(
            customer=customer, street='1 Main', city='Austin',
            latitude='30.2672000', longitude='-97.7431000', geocoded_at=now,
        )
        addr.refresh_from_db()
        self.assertEqual(float(addr.latitude), 30.2672)
        self.assertEqual(float(addr.longitude), -97.7431)
        self.assertEqual(addr.geocoded_at, now)

    def test_country_and_state_codes(self):
        customer = self.make_customer()
        addr = Address.objects.create(
            customer=customer, street='1 Main', city='Austin',
            state='Texas', state_code='TX', country='United States', country_code='US',
        )
        addr.refresh_from_db()
        self.assertEqual(addr.state_code, 'TX')
        self.assertEqual(addr.country_code, 'US')

    def test_verification_default_false(self):
        customer = self.make_customer()
        addr = Address.objects.create(customer=customer, city='X')
        self.assertFalse(addr.is_verified)
        self.assertIsNone(addr.verified_at)

    def test_street_2_optional(self):
        customer = self.make_customer()
        addr = Address.objects.create(
            customer=customer, street='1 Main', street_2='Apt 4B', city='X',
        )
        addr.refresh_from_db()
        self.assertEqual(addr.street_2, 'Apt 4B')


# ─── Phone ────────────────────────────────────────────────────────────────────

class PhoneTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        phone = Phone.objects.create(
            customer=customer,
            number='555-1234',
            phone_type='Mobile',
        )
        self.assertEqual(phone.number, '555-1234')

    def test_str(self):
        customer = self.make_customer()
        phone = Phone.objects.create(customer=customer, number='555-9999')
        self.assertEqual(str(phone), '555-9999')

    def test_primary_flag(self):
        customer = self.make_customer()
        phone = Phone.objects.create(customer=customer, number='555-0001', is_primary=True)
        phone.refresh_from_db()
        self.assertTrue(phone.is_primary)

    def test_delete(self):
        customer = self.make_customer()
        phone = Phone.objects.create(customer=customer, number='555-0002')
        phone_id = phone.id
        phone.delete()
        self.assertFalse(Phone.objects.filter(id=phone_id).exists())

    def test_country_code_storage(self):
        customer = self.make_customer()
        phone = Phone.objects.create(
            customer=customer, country_code='+1', number='555-0003',
        )
        phone.refresh_from_db()
        self.assertEqual(phone.country_code, '+1')

    def test_sms_capable_independent_of_phone_type(self):
        customer = self.make_customer()
        landline = Phone.objects.create(
            customer=customer, number='555-0004', phone_type='Office', sms_capable=False,
        )
        forwarded = Phone.objects.create(
            customer=customer, number='555-0005', phone_type='Office', sms_capable=True,
        )
        self.assertFalse(landline.sms_capable)
        self.assertTrue(forwarded.sms_capable)

    def test_verification_default_false(self):
        customer = self.make_customer()
        phone = Phone.objects.create(customer=customer, number='555-0006')
        self.assertFalse(phone.is_verified)
        self.assertIsNone(phone.verified_at)


# ─── Social ───────────────────────────────────────────────────────────────────

class SocialTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        social = Social.objects.create(
            customer=customer,
            type='Email',
            value='contact@acme.com',
        )
        self.assertEqual(social.value, 'contact@acme.com')

    def test_str(self):
        customer = self.make_customer()
        social = Social.objects.create(customer=customer, type='LinkedIn', value='acme-corp')
        self.assertIn('LinkedIn', str(social))
        self.assertIn('acme-corp', str(social))

    def test_delete(self):
        customer = self.make_customer()
        social = Social.objects.create(customer=customer, type='Email', value='x@y.com')
        s_id = social.id
        social.delete()
        self.assertFalse(Social.objects.filter(id=s_id).exists())


# ─── Lead ─────────────────────────────────────────────────────────────────────

class LeadTest(SDTATestCase):
    """Lead is the sales-tracking shell around Customer + Person.
    All operational data (name, phone, email, notes) lives on those records,
    not on Lead itself."""

    def _make_lead(self, **kwargs):
        from crm.models import Lead
        defaults = {
            'customer': self.make_customer(),
            'person': self.make_person(first_name='John', last_name='Doe'),
        }
        defaults.update(kwargs)
        return Lead.objects.create(**defaults)

    def test_create(self):
        lead = self._make_lead()
        self.assertEqual(lead.status, 'New')
        self.assertIsNotNone(lead.customer)
        self.assertIsNotNone(lead.person)

    def test_str_uses_person_and_status(self):
        person = self.make_person(first_name='Jane', last_name='Smith')
        lead = self._make_lead(person=person)
        self.assertIn('Jane Smith', str(lead))
        self.assertIn('New', str(lead))

    def test_update_status(self):
        lead = self._make_lead()
        lead.status = 'Qualified'
        lead.save()
        lead.refresh_from_db()
        self.assertEqual(lead.status, 'Qualified')

    def test_delete(self):
        lead = self._make_lead()
        lead_id = lead.id
        lead.delete()
        self.assertFalse(Lead.objects.filter(id=lead_id).exists())

    def test_customer_required(self):
        # customer FK is non-null+PROTECT — creating without it must fail.
        # TenantModel.save() runs full_clean(), so the empty FK trips
        # ValidationError from field-level validation before it ever reaches
        # the DB layer (where it would also fail with IntegrityError).
        from django.core.exceptions import ValidationError
        from django.db import IntegrityError, transaction
        with self.assertRaises((ValidationError, IntegrityError, ValueError)):
            with transaction.atomic():
                Lead.objects.create(
                    person=self.make_person(),
                    # customer omitted
                )

    def test_person_required(self):
        from django.core.exceptions import ValidationError
        from django.db import IntegrityError, transaction
        with self.assertRaises((ValidationError, IntegrityError, ValueError)):
            with transaction.atomic():
                Lead.objects.create(
                    customer=self.make_customer(),
                    # person omitted
                )

    def test_customer_protect_blocks_delete(self):
        # PROTECT on customer FK means deleting a Customer with leads fails.
        from django.db.models.deletion import ProtectedError
        lead = self._make_lead()
        with self.assertRaises(ProtectedError):
            lead.customer.delete()

    def test_person_protect_blocks_delete(self):
        from django.db.models.deletion import ProtectedError
        lead = self._make_lead()
        with self.assertRaises(ProtectedError):
            lead.person.delete()


# ─── Opportunity ──────────────────────────────────────────────────────────────

class OpportunityTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        opp = Opportunity.objects.create(
            customer=customer,
            name='HVAC Contract',
            estimated_value='50000.00',
        )
        self.assertEqual(opp.name, 'HVAC Contract')
        self.assertEqual(opp.status, 'Open')

    def test_str(self):
        customer = self.make_customer()
        opp = Opportunity.objects.create(customer=customer, name='Big Deal')
        self.assertEqual(str(opp), 'Big Deal')

    def test_update_status(self):
        customer = self.make_customer()
        opp = Opportunity.objects.create(customer=customer, name='Won Deal')
        opp.status = 'Won'
        opp.save()
        opp.refresh_from_db()
        self.assertEqual(opp.status, 'Won')

    def test_delete(self):
        customer = self.make_customer()
        opp = Opportunity.objects.create(customer=customer, name='Del Opp')
        opp_id = opp.id
        opp.delete()
        self.assertFalse(Opportunity.objects.filter(id=opp_id).exists())


# ─── Lead lifecycle sync ─────────────────────────────────────────────────────

class LeadLifecycleSyncTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        for name, st in [
            ('New', 'normal'), ('Contacted', 'normal'),
            ('Qualified', 'normal'), ('Converted', 'final'),
            ('Lost', 'final'),
        ]:
            LifecycleStateDef.objects.create(
                tenant_id=self.tenant_id, entity_type='lead',
                state_name=name, state_label=name, state_type=st,
            )
        for from_s, to_s, req in [
            ('New', 'Contacted', False), ('Contacted', 'Qualified', False),
            ('Qualified', 'Converted', False), ('Qualified', 'Lost', True),
        ]:
            LifecycleTransitionRule.objects.create(
                tenant_id=self.tenant_id, entity_type='lead',
                from_state=from_s, to_state=to_s, requires_reason=req,
            )
        self.user = self.make_user()

    def _make_lead(self):
        return Lead.objects.create(
            customer=self.make_customer(),
            person=self.make_person(first_name='Test', last_name='Lead'),
        )

    def test_qualified_sets_qualified_at(self):
        lead = self._make_lead()
        lead.execute_transition('Contacted', self.user)
        lead.execute_transition('Qualified', self.user)
        lead.refresh_from_db()
        self.assertEqual(lead.status, 'Qualified')
        self.assertIsNotNone(lead.qualified_at)

    def test_converted_sets_converted_at(self):
        lead = self._make_lead()
        lead.execute_transition('Contacted', self.user)
        lead.execute_transition('Qualified', self.user)
        lead.execute_transition('Converted', self.user)
        lead.refresh_from_db()
        self.assertIsNotNone(lead.converted_at)

    def test_lost_sets_lost_at_and_reason(self):
        lead = self._make_lead()
        lead.execute_transition('Contacted', self.user)
        lead.execute_transition('Qualified', self.user)
        lead.execute_transition('Lost', self.user, reason='No budget')
        lead.refresh_from_db()
        self.assertEqual(lead.status, 'Lost')
        self.assertIsNotNone(lead.lost_at)
        self.assertEqual(lead.lost_reason, 'No budget')

    def test_direct_lost_without_reason_rejected(self):
        from django.core.exceptions import ValidationError
        lead = self._make_lead()
        lead.status = 'Lost'
        with self.assertRaises(ValidationError) as ctx:
            lead.save()
        self.assertIn('lost_reason', ctx.exception.message_dict)


# ─── Opportunity lifecycle sync ──────────────────────────────────────────────

class OpportunityLifecycleSyncTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        for name, st in [('Open', 'normal'), ('Won', 'final'), ('Lost', 'final')]:
            LifecycleStateDef.objects.create(
                tenant_id=self.tenant_id, entity_type='opportunity',
                state_name=name, state_label=name, state_type=st,
            )
        for from_s, to_s, req in [('Open', 'Won', False), ('Open', 'Lost', True)]:
            LifecycleTransitionRule.objects.create(
                tenant_id=self.tenant_id, entity_type='opportunity',
                from_state=from_s, to_state=to_s, requires_reason=req,
            )
        self.user = self.make_user()

    def test_won_sets_won_at_and_defaults_actual_value(self):
        from decimal import Decimal
        c = self.make_customer()
        opp = Opportunity.objects.create(
            customer=c, name='Big Deal', estimated_value=Decimal('5000.00'),
        )
        opp.execute_transition('Won', self.user)
        opp.refresh_from_db()
        self.assertEqual(opp.status, 'Won')
        self.assertIsNotNone(opp.won_at)
        self.assertEqual(opp.actual_value, Decimal('5000.00'))

    def test_won_keeps_explicit_actual_value(self):
        from decimal import Decimal
        c = self.make_customer()
        opp = Opportunity.objects.create(
            customer=c, name='Negotiated', estimated_value=Decimal('5000.00'),
            actual_value=Decimal('4500.00'),
        )
        opp.execute_transition('Won', self.user)
        opp.refresh_from_db()
        self.assertEqual(opp.actual_value, Decimal('4500.00'))

    def test_lost_sets_lost_at_and_reason(self):
        c = self.make_customer()
        opp = Opportunity.objects.create(customer=c, name='Lost Deal')
        opp.execute_transition('Lost', self.user, reason='Chose competitor')
        opp.refresh_from_db()
        self.assertEqual(opp.status, 'Lost')
        self.assertIsNotNone(opp.lost_at)
        self.assertEqual(opp.lost_reason, 'Chose competitor')

    def test_direct_lost_without_reason_rejected(self):
        from django.core.exceptions import ValidationError
        c = self.make_customer()
        opp = Opportunity.objects.create(customer=c, name='Bad Direct')
        opp.status = 'Lost'
        with self.assertRaises(ValidationError) as ctx:
            opp.save()
        self.assertIn('lost_reason', ctx.exception.message_dict)


# ─── OpportunityContacts ──────────────────────────────────────────────────────

class OpportunityContactsTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        opp = Opportunity.objects.create(customer=customer, name='Opp Contact Test')
        contact = self.make_contact(customer=customer)
        oc = OpportunityContacts.objects.create(
            opportunity=opp,
            contact=contact,
            customer=customer,
        )
        self.assertIsNotNone(oc.id)

    def test_str(self):
        customer = self.make_customer()
        opp = Opportunity.objects.create(customer=customer, name='OC Str Test')
        contact = self.make_contact(customer=customer)
        oc = OpportunityContacts.objects.create(
            opportunity=opp, contact=contact, customer=customer
        )
        self.assertIn('OC Str Test', str(oc))

    def test_delete(self):
        customer = self.make_customer()
        opp = Opportunity.objects.create(customer=customer, name='OC Del Test')
        contact = self.make_contact(customer=customer)
        oc = OpportunityContacts.objects.create(
            opportunity=opp, contact=contact, customer=customer
        )
        oc_id = oc.id
        oc.delete()
        self.assertFalse(OpportunityContacts.objects.filter(id=oc_id).exists())
