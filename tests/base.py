# tests/base.py
# Base test case and factory helpers shared across all SDTA test modules.
#
# Usage:
#   from tests.base import SDTATestCase
#
#   class MyTest(SDTATestCase):
#       def test_something(self):
#           customer = self.make_customer()
#           ...
#
# Key behaviours:
#   - One TenantState and one StaffUser are created for the entire class.
#   - Tenant context (set_current_tenant_id) is set before every test and
#     cleared after, exactly as TenantMiddleware does in production.
#   - databases = ('default',) — see class attribute (worker is a separate PG
#     connection even when mirrored to the same DB name).

import uuid
from datetime import date, datetime, timezone

from django.test import TestCase

from config.tenant_context import clear_current_tenant_id, set_current_tenant_id
from infrastructure.models import TenantState
from staff.models import StaffUser


class SDTATestCase(TestCase):
    """
    Base TestCase for all SDTA model and admin tests.

    Provides:
      self.tenant       — TenantState instance (shared across all tests in class)
      self.tenant_id    — UUID of the tenant
      self.staff_user   — StaffUser with is_superuser=True (for admin tests)

    Factory helpers:
      make_person(), make_customer(), make_user(), make_product(),
      make_vendor(), make_asset(), make_work_order(), make_department(),
      make_warehouse(), make_sub_location()
    """

    # Use only the 'default' alias for TestCase transaction wrapping.
    # Test settings mirror `worker` to the same PostgreSQL database name, but
    # `default` and `worker` are still separate connections; uncommitted rows
    # on one are not visible to the other (unlike a single in-memory SQLite).
    databases = ('default',)

    @classmethod
    def setUpTestData(cls):
        """
        Create shared fixtures once per test class.
        These objects persist across all test methods in the class
        (Django wraps them in a savepoint, not a full rollback).
        """
        # TenantState does not extend TenantModel — safe to create without context.
        cls.tenant = TenantState.objects.create(
            subdomain=f'test-{uuid.uuid4().hex[:8]}',
            company_name='Test Company',
            owner_email='owner@test.com',
            status=TenantState.StatusChoices.ACTIVE,
            tier=TenantState.TierChoices.LITE,
        )
        cls.tenant_id = cls.tenant.id

        # StaffUser — needed for admin view tests.
        cls.staff_user = StaffUser.objects.create_superuser(
            email='staff@servizdesk.com',
            name='Test Staff',
            password='StaffPass123!',
        )

    def setUp(self):
        """Set tenant context before every test, exactly as middleware does."""
        set_current_tenant_id(self.tenant_id)

    def tearDown(self):
        """Clear tenant context after every test."""
        clear_current_tenant_id()

    # ─── Factory Helpers ──────────────────────────────────────────────────────

    def make_person(self, first_name='Test', last_name='User'):
        from crm.models import Person
        return Person.objects.create(first_name=first_name, last_name=last_name)

    def make_customer(self, company_name='Acme Corp', **kwargs):
        from crm.models import Customer
        defaults = {'company_name': company_name}
        defaults.update(kwargs)
        # Customer.clean() requires primary_person for Residential customers.
        # Auto-create one for the default to keep test fixtures terse. Tests
        # that need a specific Person can pass primary_person=… explicitly.
        if (defaults.get('account_type', 'Residential') == 'Residential'
                and 'primary_person' not in defaults):
            defaults['primary_person'] = self.make_person()
        return Customer.objects.create(**defaults)

    def make_contact(self, person=None, customer=None, **kwargs):
        from crm.models import Contact
        if person is None:
            person = self.make_person()
        if customer is None:
            customer = self.make_customer()
        return Contact.objects.create(person=person, customer=customer, **kwargs)

    def make_user(self, username=None, email=None, person=None, **kwargs):
        from users.models import User
        if person is None:
            person = self.make_person()
        if email is None:
            email = f'user-{uuid.uuid4().hex[:6]}@test.com'
        if username is None:
            username = f'testuser_{uuid.uuid4().hex[:12]}'
        password = kwargs.pop('password', 'TestPass123!')
        return User.objects.create_user(
            username,
            tenant_id=self.tenant_id,
            password=password,
            email=email,
            person=person,
            **kwargs,
        )

    def make_department(self, name='Engineering', **kwargs):
        from users.models import Department
        return Department.objects.create(name=name, **kwargs)

    def make_position(self, department=None, title='Developer', **kwargs):
        from users.models import Position
        if department is None:
            department = self.make_department()
        return Position.objects.create(department=department, title=title, **kwargs)

    def make_role(self, name='Technician', **kwargs):
        from users.models import Role
        return Role.objects.create(name=name, **kwargs)

    def make_product(self, name='Test Product', **kwargs):
        from inventory.models import InventoryItem
        defaults = {'name': name, 'type': 'Service'}
        defaults.update(kwargs)
        return InventoryItem.objects.create(**defaults)

    def make_vendor(self, name='Acme Supplies', **kwargs):
        from procurement.models import Vendor
        return Vendor.objects.create(name=name, **kwargs)

    def make_warehouse(self, name='Main Warehouse', **kwargs):
        from warehouse.models import Warehouse
        return Warehouse.objects.create(name=name, **kwargs)

    def make_sub_location(self, warehouse=None, location_number='A-01', **kwargs):
        from warehouse.models import SubLocation
        if warehouse is None:
            warehouse = self.make_warehouse()
        return SubLocation.objects.create(
            warehouse=warehouse, location_number=location_number, **kwargs
        )

    def make_asset(self, name='HVAC Unit', customer=None, **kwargs):
        from maintenance.models import Asset
        if customer is None:
            customer = self.make_customer()
        return Asset.objects.create(name=name, customer=customer, **kwargs)

    def make_service_request(self, customer=None, subject='Fix unit', **kwargs):
        from service.models import ServiceRequest
        if customer is None:
            customer = self.make_customer()
        return ServiceRequest.objects.create(
            customer=customer, subject=subject, **kwargs
        )

    def make_work_order(self, customer=None, subject='WO Test', **kwargs):
        from service.models import WorkOrder
        if customer is None:
            customer = self.make_customer()
        return WorkOrder.objects.create(
            customer=customer, subject=subject, **kwargs
        )

    def make_purchase_order(self, vendor=None, **kwargs):
        from procurement.models import PurchaseOrder
        if vendor is None:
            vendor = self.make_vendor()
        return PurchaseOrder.objects.create(vendor=vendor, **kwargs)

    def make_invoice(self, customer=None, **kwargs):
        from service.models import Invoice
        if customer is None:
            customer = self.make_customer()
        return Invoice.objects.create(customer=customer, **kwargs)

    def make_work_group(self, name='Field Team', **kwargs):
        from workforce.models import WorkGroup
        return WorkGroup.objects.create(name=name, **kwargs)

    def make_vehicle(self, name='Van 1', **kwargs):
        from fleet.models import Vehicle
        return Vehicle.objects.create(name=name, **kwargs)

    def make_task(self, title='Task 1', **kwargs):
        from tasks.models import Task
        defaults = {'title': title}
        defaults.update(kwargs)
        return Task.objects.create(**defaults)

    def make_workflow(self, name='Test Workflow', **kwargs):
        from automation.models import WorkFlow
        defaults = {'name': name}
        defaults.update(kwargs)
        return WorkFlow.objects.create(**defaults)

    def make_safety_form(self, form_name='Test Safety Form', **kwargs):
        from automation.models import SafetyForm
        defaults = {'form_name': form_name}
        defaults.update(kwargs)
        return SafetyForm.objects.create(**defaults)

    def make_equipment(self, name='Tool 1', **kwargs):
        from automation.models import Equipment
        defaults = {'name': name}
        defaults.update(kwargs)
        return Equipment.objects.create(**defaults)

    def make_skill(self, name='Skill 1', **kwargs):
        from workforce.models import Skill
        defaults = {'name': name}
        defaults.update(kwargs)
        return Skill.objects.create(**defaults)

    def make_rma(self, product=None, vendor=None, **kwargs):
        from procurement.models import RMA
        if product is None:
            product = self.make_product()
        if vendor is None:
            vendor = self.make_vendor()
        return RMA.objects.create(product=product, vendor=vendor, **kwargs)

    def make_credit_card(self, employee=None, **kwargs):
        from automation.models import CreditCard
        from datetime import date
        if employee is None:
            employee = self.make_user()
        defaults = {
            'last_four': '1234',
            'expiration_date': date(2026, 12, 31),
        }
        defaults.update(kwargs)
        return CreditCard.objects.create(employee=employee, **defaults)

    def make_portfolio(self, name='Portfolio 1', **kwargs):
        from automation.models import Portfolio
        defaults = {'name': name}
        defaults.update(kwargs)
        return Portfolio.objects.create(**defaults)

    def make_sprint(self, project=None, name='Sprint 1', **kwargs):
        from automation.models import Sprint
        from datetime import date
        if project is None:
            project = self.make_work_group()
        defaults = {
            'name': name,
            'start_date': date.today(),
            'end_date': date.today(),
        }
        defaults.update(kwargs)
        return Sprint.objects.create(project=project, **defaults)

    def make_milestone(self, project=None, name='Milestone 1', **kwargs):
        from automation.models import Milestone
        if project is None:
            project = self.make_work_group()
        defaults = {'name': name}
        defaults.update(kwargs)
        return Milestone.objects.create(project=project, **defaults)

    def make_territory_zone(self, name='Zone 1', **kwargs):
        from automation.models import TerritoryZone
        defaults = {'name': name}
        defaults.update(kwargs)
        return TerritoryZone.objects.create(**defaults)

    def make_value_list(self, name='Test List', slug=None, **kwargs):
        from value_lists.models import ValueList
        if slug is None:
            slug = f'test-list-{uuid.uuid4().hex[:6]}'
        defaults = {'name': name, 'slug': slug}
        defaults.update(kwargs)
        return ValueList.objects.create(**defaults)

    def make_value_list_item(self, value_list=None, label='Item 1', value=None, **kwargs):
        from value_lists.models import ValueListItem
        if value_list is None:
            value_list = self.make_value_list()
        if value is None:
            value = label.lower().replace(' ', '_')
        defaults = {'value_list': value_list, 'label': label, 'value': value}
        defaults.update(kwargs)
        return ValueListItem.objects.create(**defaults)
