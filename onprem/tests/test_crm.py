# tests/test_crm.py
# CRUD and basic functionality tests for all models in the crm app.

from tests.base import SDTATestCase
from crm.models import (
    Address, Contact, Customer, Lead, Opportunity,
    OpportunityContacts, Person, Phone, Social,
)


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


# ─── Customer ─────────────────────────────────────────────────────────────────

class CustomerTest(SDTATestCase):

    def test_create_minimal(self):
        c = Customer.objects.create(company_name='Acme')
        self.assertEqual(c.company_name, 'Acme')
        self.assertEqual(c.status, 'Active')
        self.assertEqual(c.account_type, 'Residential')

    def test_create_commercial(self):
        c = Customer.objects.create(
            company_name='BigCorp',
            account_type='Commercial',
            tax_exempt=True,
        )
        self.assertEqual(c.account_type, 'Commercial')
        self.assertTrue(c.tax_exempt)

    def test_str_uses_company_name(self):
        c = Customer.objects.create(company_name='StrCo')
        self.assertEqual(str(c), 'StrCo')

    def test_str_falls_back_to_number(self):
        c = Customer.objects.create(customer_number='C-001')
        self.assertEqual(str(c), 'C-001')

    def test_read(self):
        c = Customer.objects.create(company_name='ReadCo')
        fetched = Customer.objects.get(id=c.id)
        self.assertEqual(fetched.company_name, 'ReadCo')

    def test_update_status(self):
        c = Customer.objects.create(company_name='StatusCo')
        c.status = 'Hold'
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'Hold')

    def test_delete(self):
        c = Customer.objects.create(company_name='DelCo')
        c_id = c.id
        c.delete()
        self.assertFalse(Customer.objects.filter(id=c_id).exists())

    def test_tags_default_empty_list(self):
        c = Customer.objects.create(company_name='TagCo')
        self.assertEqual(c.tags, [])

    def test_credit_limit_default(self):
        c = Customer.objects.create(company_name='CreditCo')
        self.assertEqual(float(c.credit_limit), 0.0)


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

    def test_create(self):
        lead = Lead.objects.create(first_name='John', last_name='Doe')
        self.assertEqual(lead.status, 'New')
        self.assertEqual(lead.first_name, 'John')

    def test_str(self):
        lead = Lead.objects.create(first_name='Jane', last_name='Smith')
        self.assertIn('Jane Smith', str(lead))
        self.assertIn('New', str(lead))

    def test_update_status(self):
        lead = Lead.objects.create(first_name='Alex', last_name='B')
        lead.status = 'Qualified'
        lead.save()
        lead.refresh_from_db()
        self.assertEqual(lead.status, 'Qualified')

    def test_delete(self):
        lead = Lead.objects.create(first_name='Del', last_name='Lead')
        lead_id = lead.id
        lead.delete()
        self.assertFalse(Lead.objects.filter(id=lead_id).exists())

    def test_optional_customer_fk(self):
        customer = self.make_customer()
        lead = Lead.objects.create(
            first_name='Linked',
            last_name='Lead',
            customer=customer,
        )
        self.assertEqual(lead.customer, customer)


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
