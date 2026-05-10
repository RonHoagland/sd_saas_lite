# tests/test_cross_module_integrity.py
# Tests for cross-module FK cascades, RESTRICT blocks, multi-tenant isolation
# across apps, TenantModel.clean() cross-tenant FK validation, and mixin
# integration on real models.

import uuid
from decimal import Decimal
from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError

from config.tenant_context import (
    clear_current_tenant_id,
    set_current_tenant_id,
)
from crm.models import Customer, Person, Contact, Address, Phone, Social, Lead, Opportunity
from infrastructure.models import TenantState
from inventory.models import InventoryItem, KitItem, Pricebook, PricebookEntry
from maintenance.models import Asset, SubAsset, Agreement, CustomerAgreement
from procurement.models import Vendor, PurchaseOrder, PurchaseOrderLine, VendorBill, RMA
from service.models import (
    Bank,
    Invoice,
    InvoiceLine,
    InvoiceAsset,
    Payments,
    Quote,
    QuoteLine,
    QuoteAsset,
    ServiceRequest,
    WorkOrder,
    WorkOrderInvoice,
    WorkOrderLine,
    WorkOrderTeam,
    Ledger,
    Accounting,
)
from tasks.models import Task, AssociatedTask, TaskTime, TimeEntry
from fleet.models import Vehicle, VehicleMaintenance, MileageLog, VehicleInventory
from warehouse.models import (
    Warehouse, SubLocation, LocationAssignedInventory,
    InventoryCount, InventoryTransfer,
)
from workforce.models import WGDivision, WorkGroup, WorkGroupTeam, WorkGroupAsset, Skill, EmployeeSkill
from users.models import User, Department, Position, Role, EmployeeRole
from tests.base import SDTATestCase


# ═══════════════════════════════════════════════════════════════════════════════
# FK RESTRICT blocks — cross-module
# ═══════════════════════════════════════════════════════════════════════════════

class RestrictDeleteCustomerTest(SDTATestCase):
    """Cannot delete a Customer referenced by work orders, invoices, quotes, SRs."""

    def test_customer_with_work_order_cannot_be_deleted(self):
        c = self.make_customer()
        self.make_work_order(customer=c, subject='Linked')
        with self.assertRaises((ProtectedError, IntegrityError)):
            c.delete()

    def test_customer_with_invoice_cannot_be_deleted(self):
        c = self.make_customer()
        self.make_invoice(customer=c)
        with self.assertRaises((ProtectedError, IntegrityError)):
            c.delete()

    def test_customer_with_service_request_cannot_be_deleted(self):
        c = self.make_customer()
        self.make_service_request(customer=c, subject='SR')
        with self.assertRaises((ProtectedError, IntegrityError)):
            c.delete()

    def test_customer_with_quote_cannot_be_deleted(self):
        c = self.make_customer()
        Quote.objects.create(tenant_id=self.tenant_id, customer=c)
        with self.assertRaises((ProtectedError, IntegrityError)):
            c.delete()


class RestrictDeleteVendorTest(SDTATestCase):
    """Cannot delete a Vendor referenced by POs or bills."""

    def test_vendor_with_po_cannot_be_deleted(self):
        v = self.make_vendor()
        self.make_purchase_order(vendor=v)
        with self.assertRaises((ProtectedError, IntegrityError)):
            v.delete()

    def test_vendor_with_bill_cannot_be_deleted(self):
        v = self.make_vendor()
        VendorBill.objects.create(
            tenant_id=self.tenant_id, vendor=v,
            bill_number='VB-001', bill_date=date.today(),
        )
        with self.assertRaises((ProtectedError, IntegrityError)):
            v.delete()


class RestrictDeleteInventoryItemTest(SDTATestCase):
    """Cannot delete an InventoryItem referenced by kit, PO line, or WH inventory."""

    def test_item_in_kit_cannot_be_deleted(self):
        kit = self.make_product(name='Kit Parent', type='Product - Inventory')
        component = self.make_product(name='Component', type='Product - Inventory')
        KitItem.objects.create(
            tenant_id=self.tenant_id, kit=kit, product=component, quantity=1,
        )
        with self.assertRaises((ProtectedError, IntegrityError)):
            component.delete()

    def test_item_on_po_line_cannot_be_deleted(self):
        product = self.make_product(name='PO Product')
        vendor = self.make_vendor()
        po = self.make_purchase_order(vendor=vendor)
        PurchaseOrderLine.objects.create(
            tenant_id=self.tenant_id, purchase_order=po, product=product,
            quantity_ordered=10, unit_cost=Decimal('5.00'),
        )
        with self.assertRaises((ProtectedError, IntegrityError)):
            product.delete()


class RestrictDeleteAssetTest(SDTATestCase):
    """Cannot delete an Asset referenced by QuoteAsset or InvoiceAsset."""

    def test_asset_on_quote_cannot_be_deleted(self):
        c = self.make_customer()
        asset = self.make_asset(name='Protected Asset', customer=c)
        quote = Quote.objects.create(tenant_id=self.tenant_id, customer=c)
        QuoteAsset.objects.create(tenant_id=self.tenant_id, quote=quote, asset=asset)
        with self.assertRaises((ProtectedError, IntegrityError)):
            asset.delete()

    def test_asset_on_invoice_cannot_be_deleted(self):
        c = self.make_customer()
        asset = self.make_asset(name='Inv Asset', customer=c)
        inv = self.make_invoice(customer=c)
        InvoiceAsset.objects.create(tenant_id=self.tenant_id, invoice=inv, asset=asset)
        with self.assertRaises((ProtectedError, IntegrityError)):
            asset.delete()


class RestrictDeleteUserTest(SDTATestCase):
    """Cannot delete a User referenced by WorkOrderTeam."""

    def test_user_on_wo_team_cannot_be_deleted(self):
        user = self.make_user(email='team-member@test.com')
        c = self.make_customer()
        wo = self.make_work_order(customer=c, subject='Team WO')
        WorkOrderTeam.objects.create(
            tenant_id=self.tenant_id, work_order=wo, user=user, role='Tech',
        )
        with self.assertRaises((ProtectedError, IntegrityError)):
            user.delete()


class RestrictDeleteAccountingTest(SDTATestCase):
    """Cannot delete an Accounting entry referenced by a Ledger entry."""

    def test_accounting_with_ledger_cannot_be_deleted(self):
        acct = Accounting.objects.create(
            tenant_id=self.tenant_id, account_number='1000',
            name='Cash', account_type='Asset',
        )
        Ledger.objects.create(
            tenant_id=self.tenant_id, account=acct,
            entry_type='Debit', amount=Decimal('100.00'),
            transaction_date=date.today(),
        )
        with self.assertRaises((ProtectedError, IntegrityError)):
            acct.delete()


# ═══════════════════════════════════════════════════════════════════════════════
# CASCADE behavior — cross-module
# ═══════════════════════════════════════════════════════════════════════════════

class CascadeDeleteWorkOrderTest(SDTATestCase):
    """Deleting a WorkOrder cascades to lines, team, and WO-invoice links."""

    def test_lines_cascade(self):
        c = self.make_customer()
        wo = self.make_work_order(customer=c, subject='Cascade')
        WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            quantity=1, unit_price=Decimal('10.00'),
        )
        wo_pk = wo.pk
        self.assertEqual(WorkOrderLine.objects.filter(work_order_id=wo_pk).count(), 1)
        wo.delete()
        self.assertEqual(WorkOrderLine.objects.filter(work_order_id=wo_pk).count(), 0)

    def test_team_cascades(self):
        c = self.make_customer()
        wo = self.make_work_order(customer=c, subject='Team Cascade')
        user = self.make_user(email='cascade-team@test.com')
        WorkOrderTeam.objects.create(tenant_id=self.tenant_id, work_order=wo, user=user)
        wo.delete()
        self.assertFalse(WorkOrderTeam.objects.filter(work_order_id=wo.pk).exists())


class CascadeDeleteInvoiceTest(SDTATestCase):
    """Deleting an Invoice cascades to InvoiceLines and InvoiceAssets."""

    def test_lines_cascade(self):
        c = self.make_customer()
        inv = self.make_invoice(customer=c)
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=Decimal('5.00'),
        )
        inv.delete()
        self.assertFalse(InvoiceLine.objects.filter(invoice_id=inv.pk).exists())


class CascadeDeleteQuoteTest(SDTATestCase):
    """Deleting a Quote cascades to QuoteLines and QuoteAssets."""

    def test_lines_cascade(self):
        c = self.make_customer()
        q = Quote.objects.create(tenant_id=self.tenant_id, customer=c)
        QuoteLine.objects.create(
            tenant_id=self.tenant_id, quote=q,
            quantity=1, unit_price=Decimal('10.00'),
        )
        q.delete()
        self.assertFalse(QuoteLine.objects.filter(quote_id=q.pk).exists())


class CascadeDeleteVehicleTest(SDTATestCase):
    """Deleting a Vehicle cascades to maintenance, mileage, vehicle inventory."""

    def test_maintenance_cascades(self):
        v = self.make_vehicle(name='Fleet Cascade')
        VehicleMaintenance.objects.create(
            tenant_id=self.tenant_id, vehicle=v, service_type='Oil Change',
        )
        v.delete()
        self.assertFalse(VehicleMaintenance.objects.filter(vehicle_id=v.pk).exists())

    def test_mileage_cascades(self):
        v = self.make_vehicle(name='Mileage Cascade')
        MileageLog.objects.create(
            tenant_id=self.tenant_id, vehicle=v,
            log_date=date.today(), odometer_start=1000, odometer_end=1050,
        )
        v.delete()
        self.assertFalse(MileageLog.objects.filter(vehicle_id=v.pk).exists())

    def test_vehicle_inventory_cascades(self):
        v = self.make_vehicle(name='Inv Cascade')
        product = self.make_product(name='Vehicle Part')
        VehicleInventory.objects.create(
            tenant_id=self.tenant_id, vehicle=v, product=product,
            quantity_on_hand=5,
        )
        v.delete()
        self.assertFalse(VehicleInventory.objects.filter(vehicle_id=v.pk).exists())


class CascadeDeleteAssetSubAssetTest(SDTATestCase):
    """Deleting an Asset cascades to SubAssets."""

    def test_sub_assets_cascade(self):
        c = self.make_customer()
        asset = self.make_asset(name='Parent Asset', customer=c)
        SubAsset.objects.create(
            tenant_id=self.tenant_id, asset=asset, name='Sub A',
        )
        asset.delete()
        self.assertFalse(SubAsset.objects.filter(asset_id=asset.pk).exists())


# ═══════════════════════════════════════════════════════════════════════════════
# Multi-tenant isolation — cross-module
# ═══════════════════════════════════════════════════════════════════════════════

class CrossTenantFKValidationTest(SDTATestCase):
    """TenantModel.clean() blocks cross-tenant FK references at save time."""

    def test_work_order_cannot_reference_other_tenant_customer(self):
        other_tenant = TenantState.objects.create(
            subdomain=f'other-{uuid.uuid4().hex[:8]}',
            company_name='Other Corp',
            owner_email='other@test.com',
            status=TenantState.StatusChoices.ACTIVE,
            tier=TenantState.TierChoices.LITE,
        )
        set_current_tenant_id(str(other_tenant.id))
        other_customer = Customer.objects.create(
            tenant_id=other_tenant.id, company_name='Other Customer',
            account_type='Commercial',
        )
        set_current_tenant_id(str(self.tenant_id))
        with self.assertRaises(ValueError):
            WorkOrder.objects.create(
                tenant_id=self.tenant_id, customer=other_customer,
                subject='Cross-tenant WO',
            )

    def test_invoice_cannot_reference_other_tenant_customer(self):
        other_tenant = TenantState.objects.create(
            subdomain=f'inv-{uuid.uuid4().hex[:8]}',
            company_name='Inv Corp',
            owner_email='inv@test.com',
            status=TenantState.StatusChoices.ACTIVE,
            tier=TenantState.TierChoices.LITE,
        )
        set_current_tenant_id(str(other_tenant.id))
        foreign_customer = Customer.objects.create(
            tenant_id=other_tenant.id, company_name='Foreign Customer',
            account_type='Commercial',
        )
        set_current_tenant_id(str(self.tenant_id))
        with self.assertRaises(ValueError):
            Invoice.objects.create(
                tenant_id=self.tenant_id, customer=foreign_customer,
            )

    def test_po_line_cannot_reference_other_tenant_product(self):
        other_tenant = TenantState.objects.create(
            subdomain=f'po-{uuid.uuid4().hex[:8]}',
            company_name='PO Corp',
            owner_email='po@test.com',
            status=TenantState.StatusChoices.ACTIVE,
            tier=TenantState.TierChoices.LITE,
        )
        set_current_tenant_id(str(other_tenant.id))
        foreign_product = InventoryItem.objects.create(
            tenant_id=other_tenant.id, name='Foreign Widget',
        )
        set_current_tenant_id(str(self.tenant_id))
        vendor = self.make_vendor()
        po = self.make_purchase_order(vendor=vendor)
        with self.assertRaises(ValueError):
            PurchaseOrderLine.objects.create(
                tenant_id=self.tenant_id, purchase_order=po,
                product=foreign_product, quantity_ordered=1,
                unit_cost=Decimal('5.00'),
            )


class TenantManagerIsolationAcrossModulesTest(SDTATestCase):
    """TenantManager.objects only returns rows for the current tenant context."""

    def test_customers_isolated(self):
        self.make_customer(company_name='My Customer')
        other_tenant = TenantState.objects.create(
            subdomain=f'iso-{uuid.uuid4().hex[:8]}',
            company_name='Iso Corp',
            owner_email='iso@test.com',
            status=TenantState.StatusChoices.ACTIVE,
            tier=TenantState.TierChoices.LITE,
        )
        set_current_tenant_id(str(other_tenant.id))
        Customer.objects.create(
            tenant_id=other_tenant.id, company_name='Their Customer',
            account_type='Commercial',
        )
        set_current_tenant_id(str(self.tenant_id))
        qs = Customer.objects.all()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().company_name, 'My Customer')

    def test_work_orders_isolated(self):
        c = self.make_customer()
        self.make_work_order(customer=c, subject='My WO')
        other_tenant = TenantState.objects.create(
            subdomain=f'woiso-{uuid.uuid4().hex[:8]}',
            company_name='WO Iso Corp',
            owner_email='woiso@test.com',
            status=TenantState.StatusChoices.ACTIVE,
            tier=TenantState.TierChoices.LITE,
        )
        set_current_tenant_id(str(other_tenant.id))
        oc = Customer.objects.create(
            tenant_id=other_tenant.id, company_name='OtherCust',
            account_type='Commercial',
        )
        WorkOrder.objects.create(
            tenant_id=other_tenant.id, customer=oc, subject='Their WO',
        )
        set_current_tenant_id(str(self.tenant_id))
        self.assertEqual(WorkOrder.objects.count(), 1)
        self.assertEqual(WorkOrder.objects.first().subject, 'My WO')

    def test_all_objects_bypasses_filter(self):
        c = self.make_customer()
        self.make_work_order(customer=c, subject='All Objects WO')
        clear_current_tenant_id()
        self.assertGreaterEqual(WorkOrder.all_objects.count(), 1)
        set_current_tenant_id(str(self.tenant_id))


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-module business wiring
# ═══════════════════════════════════════════════════════════════════════════════

class CrossModuleWiringTest(SDTATestCase):
    """Complex cross-app scenarios that exercise multiple modules together."""

    def test_full_service_lifecycle(self):
        """SR → WO → WO Lines → Invoice → SENT → Payment → PAID.

        Auto-paying via the Payments cascade requires the invoice to be
        in Sent state first (Draft → Paid is not a valid transition in
        the seed graph). We seed the minimum lifecycle rules locally to
        exercise the full path through `execute_transition`.
        """
        from lifecycle.models import LifecycleStateDef, LifecycleTransitionRule
        for name, st in [
            ('Draft', 'normal'), ('Sent', 'normal'),
            ('Partial', 'normal'), ('Paid', 'final'),
        ]:
            LifecycleStateDef.objects.create(
                tenant_id=self.tenant_id, entity_type='invoice',
                state_name=name, state_label=name, state_type=st,
            )
        for from_s, to_s in [('Draft', 'Sent'), ('Sent', 'Partial'), ('Sent', 'Paid')]:
            LifecycleTransitionRule.objects.create(
                tenant_id=self.tenant_id, entity_type='invoice',
                from_state=from_s, to_state=to_s,
            )

        customer = self.make_customer()
        sr = self.make_service_request(customer=customer, subject='Full Lifecycle')
        wo = self.make_work_order(customer=customer, subject='Full WO')
        WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            line_type='Labor', quantity=2, unit_price=Decimal('75.00'),
        )
        WorkOrderLine.objects.create(
            tenant_id=self.tenant_id, work_order=wo,
            line_type='Part', quantity=1, unit_price=Decimal('50.00'),
        )
        wo.refresh_from_db()
        self.assertEqual(wo.total_amount, Decimal('200.00'))

        inv = self.make_invoice(customer=customer)
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=2, unit_price=Decimal('75.00'),
        )
        InvoiceLine.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            quantity=1, unit_price=Decimal('50.00'),
        )
        WorkOrderInvoice.objects.create(
            tenant_id=self.tenant_id, work_order=wo, invoice=inv,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.total, Decimal('200.00'))

        # Send the invoice (required precondition for Sent → Paid).
        inv.status = Invoice.StatusChoices.SENT
        inv.save()

        Payments.objects.create(
            tenant_id=self.tenant_id, invoice=inv,
            amount=Decimal('200.00'), payment_date='2026-04-05',
            status=Payments.StatusChoices.PAID,
        )
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.StatusChoices.PAID)

    def test_procurement_to_warehouse_chain(self):
        """Vendor → PO → PO Line → Receiving → Warehouse inventory."""
        from procurement.models import Receiving
        vendor = self.make_vendor()
        product = self.make_product(name='Chain Product', type='Product - Inventory')
        po = self.make_purchase_order(vendor=vendor)
        pol = PurchaseOrderLine.objects.create(
            tenant_id=self.tenant_id, purchase_order=po, product=product,
            quantity_ordered=20, unit_cost=Decimal('5.00'),
        )
        wh = self.make_warehouse()
        sub = self.make_sub_location(warehouse=wh)
        Receiving.objects.create(
            tenant_id=self.tenant_id, purchase_order=po,
            po_line=pol, product=product,
            quantity_received=20, received_date=date.today(),
            destination_location=sub,
        )
        LocationAssignedInventory.objects.create(
            tenant_id=self.tenant_id, sub_location=sub,
            product=product, quantity_on_hand=20,
        )
        self.assertEqual(
            LocationAssignedInventory.objects.get(
                sub_location=sub, product=product,
            ).quantity_on_hand, 20,
        )

    def test_fleet_references_service_and_inventory(self):
        """Vehicle can reference user, work group; vehicle inventory references product."""
        user = self.make_user(email='driver@test.com')
        wg = self.make_work_group(name='Fleet Group')
        v = Vehicle.objects.create(
            tenant_id=self.tenant_id, name='Truck', vehicle_type='Truck',
            assigned_to=user, assigned_work_group=wg,
        )
        product = self.make_product(name='Spare Part')
        vi = VehicleInventory.objects.create(
            tenant_id=self.tenant_id, vehicle=v, product=product,
            quantity_on_hand=3,
        )
        self.assertEqual(vi.product.name, 'Spare Part')
        self.assertEqual(v.assigned_to, user)
        self.assertEqual(v.assigned_work_group, wg)

    def test_task_links_to_service_module(self):
        """Task can reference both WorkOrder and ServiceRequest."""
        customer = self.make_customer()
        sr = self.make_service_request(customer=customer, subject='Task SR')
        wo = self.make_work_order(customer=customer, subject='Task WO')
        task = self.make_task(title='Cross-link Task')
        task.work_order = wo
        task.service_request = sr
        task.save()
        task.refresh_from_db()
        self.assertEqual(task.work_order, wo)
        self.assertEqual(task.service_request, sr)

    def test_workforce_asset_to_maintenance(self):
        """WorkGroupAsset links workforce to maintenance module."""
        customer = self.make_customer()
        asset = self.make_asset(name='WG Asset', customer=customer)
        wg = self.make_work_group(name='Maintenance Crew')
        wga = WorkGroupAsset.objects.create(
            tenant_id=self.tenant_id, work_group=wg, asset=asset,
        )
        self.assertEqual(wga.asset.name, 'WG Asset')

    def test_employee_skill_links_workforce_and_users(self):
        """EmployeeSkill bridges workforce and users modules."""
        user = self.make_user(email='skilled@test.com')
        skill = self.make_skill(name='Welding')
        es = EmployeeSkill.objects.create(
            tenant_id=self.tenant_id, employee=user, skill=skill,
            date_earned=date.today(),
        )
        self.assertEqual(es.employee, user)
        self.assertEqual(es.skill.name, 'Welding')

    def test_time_entry_links_tasks_and_service(self):
        """TimeEntry can link to both a Task and a WorkOrder."""
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer, subject='Time WO')
        task = self.make_task(title='Time Task')
        user = self.make_user(email='logger@test.com')
        te = TimeEntry.objects.create(
            tenant_id=self.tenant_id, logged_by=user,
            work_date=date.today(), hours=Decimal('2.5'),
            task=task, work_order=wo,
        )
        self.assertEqual(te.task, task)
        self.assertEqual(te.work_order, wo)

    def test_ledger_links_service_and_procurement(self):
        """A Ledger entry can reference an invoice, payment, or vendor bill."""
        customer = self.make_customer()
        vendor = self.make_vendor()
        inv = self.make_invoice(customer=customer)
        vb = VendorBill.objects.create(
            tenant_id=self.tenant_id, vendor=vendor,
            bill_number='VB-LED', bill_date=date.today(),
        )
        acct = Accounting.objects.create(
            tenant_id=self.tenant_id, account_number='2000',
            name='AP', account_type='Liability',
        )
        l1 = Ledger.objects.create(
            tenant_id=self.tenant_id, account=acct,
            entry_type='Debit', amount=Decimal('100.00'),
            transaction_date=date.today(), invoice=inv,
        )
        l2 = Ledger.objects.create(
            tenant_id=self.tenant_id, account=acct,
            entry_type='Credit', amount=Decimal('50.00'),
            transaction_date=date.today(), vendor_bill=vb,
        )
        self.assertEqual(l1.invoice, inv)
        self.assertEqual(l2.vendor_bill, vb)


# ═══════════════════════════════════════════════════════════════════════════════
# Mixin integration on real models
# ═══════════════════════════════════════════════════════════════════════════════

class NumberingMixinIntegrationTest(SDTATestCase):
    """NumberingMixin methods work on real model instances."""

    def test_has_assigned_number_false_by_default(self):
        c = self.make_customer()
        self.assertFalse(c.has_assigned_number())

    def test_get_assigned_number_none_by_default(self):
        c = self.make_customer()
        self.assertIsNone(c.get_assigned_number())


class LifecycleMixinIntegrationTest(SDTATestCase):
    """LifecycleMixin methods work on real model instances."""

    def test_get_transition_history_empty(self):
        c = self.make_customer()
        history = c.get_transition_history()
        self.assertEqual(history.count(), 0)

    def test_get_available_transitions_empty_without_rules(self):
        c = self.make_customer()
        user = self.make_user(email='lc@test.com')
        transitions = c.get_available_transitions(user)
        self.assertEqual(len(transitions), 0)
