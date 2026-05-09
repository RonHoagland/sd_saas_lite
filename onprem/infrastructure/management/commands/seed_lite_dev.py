"""
seed_lite_dev — populate the database with realistic Lite-tier dev data.

Usage:
    python3 manage.py seed_lite_dev               # idempotent reseed
    python3 manage.py seed_lite_dev --tenant acme # custom subdomain

Creates one tenant, one admin user (admin / admin), 5 customers (mix of
Residential and Commercial), 7 assets, 5 service requests in varied
statuses, 5 quotes, 6 work orders (2 of which are scheduled for *today*
so the dashboard's Today's Schedule has data to show), 4 invoices, and
2 payments.

Idempotent: re-running purges all records belonging to the test tenant
and recreates them. Safe to run repeatedly during development.

Source decisions: Architecture & Planning/LITE_DECISIONS.md (especially §A
asset types ValueList, §B no numbering control in Lite, §F manual payment).
"""

from __future__ import annotations

import datetime as _dt
import uuid
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from config.tenant_context import set_current_tenant_id, clear_current_tenant_id
from infrastructure.models import TenantState, SubdomainIndex
from numbering.models import NumberingRule
from users.models import User
from crm.models import Customer, Person
from maintenance.models import Asset
from service.models import ServiceRequest, WorkOrder, Quote, Invoice, Payments


SUBDOMAIN_DEFAULT = 'dev-test'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'  # Dev only. Phase 8.3 will enforce stronger policies.
ADMIN_EMAIL = 'admin@dev-test.servizdesk.local'


# ─── Sample data ──────────────────────────────────────────────────────────────

CUSTOMERS = [
    # (company_name, account_type, status)
    ('Anderson Residence',     'Residential', 'Active'),
    ('Rivera Family Home',     'Residential', 'Active'),
    ('Patel Household',        'Residential', 'Active'),
    ('Greenfield Office Park', 'Commercial',  'Active'),
    ('Northbridge Cafe',       'Commercial',  'Active'),
]

ASSETS = [
    # (customer_index, name, manufacturer, model_number)
    (0, 'Furnace - Garage Unit',     'Carrier',    'X38-HE'),
    (0, 'Water Heater - Basement',   'Rheem',      'WH-500'),
    (1, 'Central AC - Roof',         'Trane',      'AX2200'),
    (2, 'Boiler - Utility Room',     'Weil-McLain', 'GV90+'),
    (3, 'HVAC Unit - North Wing',    'Lennox',     'XC25'),
    (3, 'Backup Generator',          'Generac',    '24kW'),
    (4, 'Walk-in Cooler',            'True',       'TS-49'),
]


class Command(BaseCommand):
    help = 'Populate the database with realistic Lite-tier dev data (idempotent).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            default=SUBDOMAIN_DEFAULT,
            help=f'Subdomain for the dev tenant (default: {SUBDOMAIN_DEFAULT}).',
        )

    def handle(self, *args, **opts):
        subdomain = opts['tenant']
        self.stdout.write(self.style.NOTICE(f'Seeding Lite dev data for tenant `{subdomain}`…'))

        with transaction.atomic():
            tenant = self._upsert_tenant(subdomain)
            set_current_tenant_id(tenant.id)
            try:
                self._purge_tenant_data(tenant.id)
                self._seed_numbering_rules(tenant.id)
                admin = self._seed_admin_user(tenant.id)
                customers = self._seed_customers(tenant.id, admin)
                assets = self._seed_assets(customers)
                self._seed_service_requests(customers, admin)
                self._seed_quotes(customers)
                self._seed_work_orders(customers, assets, admin)
                self._seed_invoices_and_payments(customers)
            finally:
                clear_current_tenant_id()

        # The username may have been auto-suffixed if 'admin' was already taken
        # globally (UserManager guarantees globally-unique usernames).
        self.stdout.write(self.style.SUCCESS(
            f'Seed complete. Login at /  with username `{admin.username}` / password `{ADMIN_PASSWORD}`.'
        ))

    # ─── Tenant ───────────────────────────────────────────────────────────────

    def _upsert_tenant(self, subdomain: str) -> TenantState:
        try:
            tenant = TenantState.objects.get(subdomain=subdomain)
            self.stdout.write(f'  • Reusing existing tenant {tenant.id} ({tenant.company_name})')
        except TenantState.DoesNotExist:
            tenant = TenantState.objects.create(
                id=uuid.uuid4(),
                subdomain=subdomain,
                company_name='Dev Test Co.',
                status=TenantState.StatusChoices.ACTIVE,
                tier=TenantState.TierChoices.LITE,
                owner_email=ADMIN_EMAIL,
                owner_name='Dev Admin',
            )
            SubdomainIndex.objects.create(subdomain=subdomain, tenant=tenant)
            self.stdout.write(f'  • Created tenant {tenant.id} ({tenant.company_name})')
        return tenant

    def _purge_tenant_data(self, tenant_id):
        """Wipe all tenant-scoped records before reseeding (FK-safe order)."""
        # Use all_objects to bypass tenant filtering during deletion.
        deletions = [
            Payments, Invoice, Quote, WorkOrder, ServiceRequest,
            Asset, Customer,
            User,
            Person,  # Person is FK'd by User; delete after User
            NumberingRule,
        ]
        for model in deletions:
            mgr = getattr(model, 'all_objects', model.objects)
            count, _ = mgr.filter(tenant_id=tenant_id).delete()
            if count:
                self.stdout.write(f'    purged {count} {model.__name__}')

    # ─── Numbering rules ──────────────────────────────────────────────────────

    def _seed_numbering_rules(self, tenant_id):
        """One rule per entity type. Uses Lite system defaults per LITE_DECISIONS.md §B."""
        rules = [
            ('customer',         'C'),
            ('asset',            'A'),
            ('service_request',  'SR'),
            ('work_order',       'W'),
            ('quote',            'Q'),
            ('invoice',          'I'),
            ('payment',          'P'),
            ('employee',         'E'),
        ]
        for entity_type, prefix in rules:
            NumberingRule.objects.create(
                tenant_id=tenant_id,
                entity_type=entity_type,
                prefix=prefix,
                include_year=(entity_type != 'employee'),
                year_format='YY',
                sequence_length=4,
                reset_behavior='yearly' if entity_type != 'employee' else 'none',
                is_enabled=True,
            )

    # ─── Users ────────────────────────────────────────────────────────────────

    def _seed_admin_user(self, tenant_id):
        admin = User.objects.create_user(
            username=ADMIN_USERNAME,
            tenant_id=tenant_id,
            password=ADMIN_PASSWORD,
            email=ADMIN_EMAIL,
            first_name='Dev',
            last_name='Admin',
            is_tenant_admin=True,
            is_active=True,
            is_staff=False,
        )
        self.stdout.write(f'  • Admin user `{admin.username}` (tenant_admin=True)')
        return admin

    # ─── Customers ────────────────────────────────────────────────────────────

    def _seed_customers(self, tenant_id, admin):
        created = []
        for company_name, account_type, status in CUSTOMERS:
            customer = Customer.objects.create(
                tenant_id=tenant_id,
                company_name=company_name,
                account_type=account_type,
                status=status,
                assigned_to=admin,
                customer_since=_dt.date.today() - _dt.timedelta(days=180),
                created_by='seed',
                updated_by='seed',
            )
            created.append(customer)
        self.stdout.write(f'  • {len(created)} customers')
        return created

    # ─── Assets ───────────────────────────────────────────────────────────────

    def _seed_assets(self, customers):
        created = []
        for customer_idx, name, manufacturer, model_number in ASSETS:
            asset = Asset.objects.create(
                tenant_id=customers[customer_idx].tenant_id,
                customer=customers[customer_idx],
                name=name,
                manufacturer=manufacturer,
                model_number=model_number,
                status=Asset.StatusChoices.ACTIVE,
                install_date=_dt.date.today() - _dt.timedelta(days=365 * 3),
                created_by='seed',
                updated_by='seed',
            )
            created.append(asset)
        self.stdout.write(f'  • {len(created)} assets')
        return created

    # ─── Service Requests ─────────────────────────────────────────────────────

    def _seed_service_requests(self, customers, admin):
        items = [
            (0, 'Furnace not igniting',       ServiceRequest.StatusChoices.NEW),
            (1, 'AC blowing warm air',        ServiceRequest.StatusChoices.ASSIGNED),
            (2, 'Boiler making knocking sound', ServiceRequest.StatusChoices.IN_PROGRESS),
            (3, 'HVAC quarterly check',       ServiceRequest.StatusChoices.RESOLVED),
            (4, 'Walk-in cooler temp drift',  ServiceRequest.StatusChoices.NEW),
        ]
        for idx, subject, status in items:
            ServiceRequest.objects.create(
                tenant_id=customers[idx].tenant_id,
                customer=customers[idx],
                subject=subject,
                description=f'Customer reports: {subject.lower()}.',
                status=status,
                priority=ServiceRequest.PriorityChoices.MEDIUM,
                assigned_to=admin if status != ServiceRequest.StatusChoices.NEW else None,
                requested_date=_dt.date.today() - _dt.timedelta(days=2),
                created_by='seed',
                updated_by='seed',
            )
        self.stdout.write(f'  • {len(items)} service requests')

    # ─── Quotes ───────────────────────────────────────────────────────────────

    def _seed_quotes(self, customers):
        items = [
            (0, Quote.StatusChoices.DRAFT,    Decimal('850.00')),
            (1, Quote.StatusChoices.SENT,     Decimal('1450.00')),
            (2, Quote.StatusChoices.SENT,     Decimal('2200.00')),
            (3, Quote.StatusChoices.ACCEPTED, Decimal('540.00')),
            (4, Quote.StatusChoices.DECLINED, Decimal('1100.00')),
        ]
        for idx, status, total in items:
            Quote.objects.create(
                tenant_id=customers[idx].tenant_id,
                customer=customers[idx],
                status=status,
                quote_date=_dt.date.today() - _dt.timedelta(days=5),
                expiration_date=_dt.date.today() + _dt.timedelta(days=25),
                subtotal=total,
                tax_rate=Decimal('0.0825'),
                tax_amount=(total * Decimal('0.0825')).quantize(Decimal('0.01')),
                total=(total * Decimal('1.0825')).quantize(Decimal('0.01')),
                created_by='seed',
                updated_by='seed',
            )
        self.stdout.write(f'  • {len(items)} quotes')

    # ─── Work Orders (Jobs) ───────────────────────────────────────────────────

    def _seed_work_orders(self, customers, assets, admin):
        today = _dt.date.today()
        # (customer_idx, asset_idx_or_none, subject, status, scheduled_date, scheduled_time)
        items = [
            (0, 0, 'Furnace ignition repair',  WorkOrder.StatusChoices.SCHEDULED, today,                     _dt.time(9, 0)),
            (1, 2, 'AC compressor diagnostic', WorkOrder.StatusChoices.SCHEDULED, today,                     _dt.time(13, 30)),
            (2, 3, 'Boiler service call',      WorkOrder.StatusChoices.IN_PROGRESS, today - _dt.timedelta(days=1), _dt.time(10, 0)),
            (3, 4, 'HVAC quarterly maintenance', WorkOrder.StatusChoices.COMPLETED, today - _dt.timedelta(days=3), _dt.time(14, 0)),
            (4, 6, 'Walk-in cooler inspection', WorkOrder.StatusChoices.DRAFT,    None,                       None),
            (0, 1, 'Water heater follow-up',   WorkOrder.StatusChoices.ON_HOLD,   today + _dt.timedelta(days=4), _dt.time(11, 0)),
        ]
        for cust_idx, asset_idx, subject, status, sched_date, sched_time in items:
            wo = WorkOrder(
                tenant_id=customers[cust_idx].tenant_id,
                customer=customers[cust_idx],
                asset=assets[asset_idx] if asset_idx is not None else None,
                subject=subject,
                description=f'Scope: {subject.lower()}.',
                status=status,
                priority=WorkOrder.PriorityChoices.MEDIUM,
                scheduled_date=sched_date,
                scheduled_time=sched_time,
                assigned_to=admin,
                created_by='seed',
                updated_by='seed',
            )
            # On Hold requires hold_reason per System Status V3 §5.
            if status == WorkOrder.StatusChoices.ON_HOLD:
                wo.hold_date = _dt.datetime.now(_dt.timezone.utc)
                wo.hold_reason = 'Awaiting customer confirmation on warranty terms.'
            wo.save()
        self.stdout.write(f'  • {len(items)} work orders ({sum(1 for x in items if x[4] == today)} scheduled today)')

    # ─── Invoices + Payments ──────────────────────────────────────────────────

    def _seed_invoices_and_payments(self, customers):
        # (customer_idx, status, subtotal)
        items = [
            (3, Invoice.StatusChoices.PAID,    Decimal('540.00')),
            (1, Invoice.StatusChoices.SENT,    Decimal('1450.00')),
            (2, Invoice.StatusChoices.SENT,    Decimal('2200.00')),
            (0, Invoice.StatusChoices.DRAFT,   Decimal('320.00')),
        ]
        invoices = []
        for cust_idx, target_status, subtotal in items:
            tax_rate = Decimal('0.0825')
            tax = (subtotal * tax_rate).quantize(Decimal('0.01'))
            total = (subtotal + tax).quantize(Decimal('0.01'))
            inv = Invoice.objects.create(
                tenant_id=customers[cust_idx].tenant_id,
                customer=customers[cust_idx],
                # Set status to its draft baseline; status auto-recalcs on payment save below.
                status=Invoice.StatusChoices.DRAFT if target_status == Invoice.StatusChoices.PAID else target_status,
                invoice_date=_dt.date.today() - _dt.timedelta(days=10),
                due_date=_dt.date.today() + _dt.timedelta(days=20),
                subtotal=subtotal,
                tax_rate=tax_rate,
                tax_amount=tax,
                total=total,
                amount_paid=Decimal('0.00'),
                balance_due=total,
                created_by='seed',
                updated_by='seed',
            )
            invoices.append((inv, target_status, total))

        # For invoices targeting Paid, attach a Payment for the full amount.
        # For Sent invoices, leave them as-is.
        paid_count = 0
        for inv, target_status, total in invoices:
            if target_status == Invoice.StatusChoices.PAID:
                Payments.objects.create(
                    tenant_id=inv.tenant_id,
                    invoice=inv,
                    payment_date=_dt.date.today() - _dt.timedelta(days=2),
                    amount=total,
                    method=Payments.MethodChoices.CHECK,
                    status=Payments.StatusChoices.APPLIED,
                    reference_number='Check #1042',
                    created_by='seed',
                    updated_by='seed',
                )
                # Invoice auto-recalculates balance + status to Paid on save trigger.
                inv.amount_paid = total
                inv.balance_due = Decimal('0.00')
                inv.status = Invoice.StatusChoices.PAID
                inv.save()
                paid_count += 1

        self.stdout.write(f'  • {len(invoices)} invoices ({paid_count} paid)')
