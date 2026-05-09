# tests/test_admin.py
# Tests for admin registration, changelist views, and TenantModelAdmin methods.
#
# Three test categories:
#   1. AdminRegistrationTest       — verifies every model has a registered admin class.
#   2. TenantModelAdminMethodTest  — unit tests for save_model / delete_model / get_queryset.
#   3. AdminChangelistViewTests    — HTTP 200 smoke tests for every changelist URL.
#
# @override_settings is applied to the view test class to suppress SSL and
# django-axes checks that would interfere with the test client.

from datetime import date

from django.contrib import admin
from django.contrib.auth.models import Group
from django.test import RequestFactory, TestCase, override_settings

from tests.base import SDTATestCase
from staff.admin import TenantModelAdmin as StaffTenantModelAdmin

# ── Import all models that must be registered ──────────────────────────────

from automation.models import (
    CommunicationTemplate, CommunicationTrigger, TriggerLog, TriggerTemplate,
)
from crm.models import (
    Address, Contact, Customer, Lead, Opportunity, OpportunityContacts,
    Person, Phone, Social,
)
from fleet.models import MileageLog, Vehicle, VehicleInventory, VehicleMaintenance
from infrastructure.models import (
    DataExportLog, EmailDeliveryLog, EmailUsageTracker, ErrorCode,
    IssuesErrors, NavigationAudit, Notification, OnboardingState,
    ProcessTransaction, SMSUsageTracker, StorageTracker,
    StripeAPIRequestLog, StripeConnection, StripeConnectionLog, StripeLog,
    StripeResponse, SubdomainIndex, SystemAudits, TenantAddOn, TenantState,
    TenantSyncLog, WebhookLog,
)
from inventory.models import InvPriceHistory, InventoryItem, KitItem, Pricebook, PricebookEntry
from maintenance.models import (
    Agreement, Asset, CustomerAgreement, PreventativeMaintenance, SubAsset,
)
from procurement.models import (
    LotInfo, PurchaseOrder, PurchaseOrderLine, Receiving,
    Requisition, RequisitionLine, Vendor, VendorBill,
)
from service.models import (
    Accounting, Bank, Invoice, InvoiceLine, InvoiceAsset, Ledger,
    Payments, Quote, QuoteLine, QuoteAsset, ServiceRequest, WorkOrder,
    WorkOrderInvoice, WorkOrderLine, WorkOrderTeam,
)
from staff.models import StaffUser
from tasks.models import AssociatedTask, Task, TaskTime, TaskToDo, TimeEntry
from users.models import (
    Department, EmployeePosition, EmployeePreference, EmployeeRole,
    LoginAttemptLog, Position, Role, RolePermission, SessionLog,
    TenantPreference, User,
)
from warehouse.models import (
    InventoryCount, InventoryTransfer, LocationAssignedInventory,
    SubLocation, Warehouse,
)
from workforce.models import (
    WGDivision, WGTRole, WorkGroup, WorkGroupAsset, WorkGroupTeam,
)


# ─── 1. Admin Registration Tests ──────────────────────────────────────────────

class AdminRegistrationTest(TestCase):
    """
    Verifies that every application model has a corresponding registered
    admin class in admin.site._registry.
    """

    def _assert_registered(self, model):
        self.assertIn(
            model,
            admin.site._registry,
            msg=f'{model.__name__} is not registered in admin.site',
        )

    # ── staff ──────────────────────────────────────────────────────────────
    def test_staff_user_registered(self):
        self._assert_registered(StaffUser)

    # ── users ──────────────────────────────────────────────────────────────
    def test_department_registered(self):       self._assert_registered(Department)
    def test_position_registered(self):         self._assert_registered(Position)
    def test_role_registered(self):             self._assert_registered(Role)
    def test_user_registered(self):             self._assert_registered(User)
    def test_employee_role_registered(self):    self._assert_registered(EmployeeRole)
    def test_employee_position_registered(self): self._assert_registered(EmployeePosition)
    def test_role_permission_registered(self):  self._assert_registered(RolePermission)
    def test_tenant_preference_registered(self): self._assert_registered(TenantPreference)
    def test_employee_preference_registered(self): self._assert_registered(EmployeePreference)
    def test_session_log_registered(self):      self._assert_registered(SessionLog)
    def test_login_attempt_log_registered(self): self._assert_registered(LoginAttemptLog)

    # ── crm ────────────────────────────────────────────────────────────────
    def test_person_registered(self):           self._assert_registered(Person)
    def test_customer_registered(self):         self._assert_registered(Customer)
    def test_contact_registered(self):          self._assert_registered(Contact)
    def test_address_registered(self):          self._assert_registered(Address)
    def test_phone_registered(self):            self._assert_registered(Phone)
    def test_social_registered(self):           self._assert_registered(Social)
    def test_lead_registered(self):             self._assert_registered(Lead)
    def test_opportunity_registered(self):      self._assert_registered(Opportunity)
    def test_opportunity_contacts_registered(self): self._assert_registered(OpportunityContacts)

    # ── inventory ──────────────────────────────────────────────────────────
    def test_inventory_item_registered(self):    self._assert_registered(InventoryItem)
    def test_kit_item_registered(self):         self._assert_registered(KitItem)
    def test_inv_price_history_registered(self): self._assert_registered(InvPriceHistory)
    def test_pricebook_registered(self):        self._assert_registered(Pricebook)
    def test_pricebook_entry_registered(self):  self._assert_registered(PricebookEntry)

    # ── warehouse ──────────────────────────────────────────────────────────
    def test_warehouse_registered(self):                        self._assert_registered(Warehouse)
    def test_sub_location_registered(self):                     self._assert_registered(SubLocation)
    def test_location_assigned_inventory_registered(self):      self._assert_registered(LocationAssignedInventory)
    def test_inventory_count_registered(self):                  self._assert_registered(InventoryCount)
    def test_inventory_transfer_registered(self):               self._assert_registered(InventoryTransfer)

    # ── procurement ────────────────────────────────────────────────────────
    def test_vendor_registered(self):               self._assert_registered(Vendor)
    def test_purchase_order_registered(self):        self._assert_registered(PurchaseOrder)
    def test_purchase_order_line_registered(self):   self._assert_registered(PurchaseOrderLine)
    def test_receiving_registered(self):             self._assert_registered(Receiving)
    def test_lot_info_registered(self):              self._assert_registered(LotInfo)
    def test_vendor_bill_registered(self):           self._assert_registered(VendorBill)
    def test_requisition_registered(self):           self._assert_registered(Requisition)
    def test_requisition_line_registered(self):      self._assert_registered(RequisitionLine)

    # ── service ────────────────────────────────────────────────────────────
    def test_service_request_registered(self):      self._assert_registered(ServiceRequest)
    def test_work_order_registered(self):            self._assert_registered(WorkOrder)
    def test_work_order_team_registered(self):       self._assert_registered(WorkOrderTeam)
    def test_work_order_line_registered(self):       self._assert_registered(WorkOrderLine)
    def test_quote_registered(self):                 self._assert_registered(Quote)
    def test_quote_line_registered(self):            self._assert_registered(QuoteLine)
    def test_quote_asset_registered(self):           self._assert_registered(QuoteAsset)
    def test_invoice_registered(self):               self._assert_registered(Invoice)
    def test_invoice_line_registered(self):          self._assert_registered(InvoiceLine)
    def test_invoice_asset_registered(self):         self._assert_registered(InvoiceAsset)
    def test_work_order_invoice_registered(self):    self._assert_registered(WorkOrderInvoice)
    def test_bank_registered(self):                  self._assert_registered(Bank)
    def test_payments_registered(self):              self._assert_registered(Payments)
    def test_ledger_registered(self):                self._assert_registered(Ledger)
    def test_accounting_registered(self):            self._assert_registered(Accounting)

    # ── maintenance ────────────────────────────────────────────────────────
    def test_asset_registered(self):                    self._assert_registered(Asset)
    def test_sub_asset_registered(self):                self._assert_registered(SubAsset)
    def test_agreement_registered(self):                self._assert_registered(Agreement)
    def test_customer_agreement_registered(self):       self._assert_registered(CustomerAgreement)
    def test_preventative_maintenance_registered(self): self._assert_registered(PreventativeMaintenance)

    # ── tasks ──────────────────────────────────────────────────────────────
    def test_task_registered(self):             self._assert_registered(Task)
    def test_associated_task_registered(self):  self._assert_registered(AssociatedTask)
    def test_task_time_registered(self):        self._assert_registered(TaskTime)
    def test_task_to_do_registered(self):       self._assert_registered(TaskToDo)
    def test_time_entry_registered(self):       self._assert_registered(TimeEntry)

    # ── workforce ──────────────────────────────────────────────────────────
    def test_wg_division_registered(self):      self._assert_registered(WGDivision)
    def test_work_group_registered(self):       self._assert_registered(WorkGroup)
    def test_wgt_role_registered(self):         self._assert_registered(WGTRole)
    def test_work_group_team_registered(self):  self._assert_registered(WorkGroupTeam)
    def test_work_group_asset_registered(self): self._assert_registered(WorkGroupAsset)

    # ── automation ─────────────────────────────────────────────────────────
    def test_communication_trigger_registered(self):    self._assert_registered(CommunicationTrigger)
    def test_communication_template_registered(self):   self._assert_registered(CommunicationTemplate)
    def test_trigger_template_registered(self):         self._assert_registered(TriggerTemplate)
    def test_trigger_log_registered(self):              self._assert_registered(TriggerLog)

    # ── fleet ──────────────────────────────────────────────────────────────
    def test_vehicle_registered(self):              self._assert_registered(Vehicle)
    def test_vehicle_maintenance_registered(self):  self._assert_registered(VehicleMaintenance)
    def test_mileage_log_registered(self):          self._assert_registered(MileageLog)
    def test_vehicle_inventory_registered(self):    self._assert_registered(VehicleInventory)

    # ── infrastructure ─────────────────────────────────────────────────────
    def test_tenant_state_registered(self):             self._assert_registered(TenantState)
    def test_tenant_add_on_registered(self):            self._assert_registered(TenantAddOn)
    def test_subdomain_index_registered(self):          self._assert_registered(SubdomainIndex)
    def test_error_code_registered(self):               self._assert_registered(ErrorCode)
    def test_system_audits_registered(self):            self._assert_registered(SystemAudits)
    def test_notification_registered(self):             self._assert_registered(Notification)
    def test_issues_errors_registered(self):            self._assert_registered(IssuesErrors)
    def test_storage_tracker_registered(self):          self._assert_registered(StorageTracker)
    def test_email_usage_tracker_registered(self):      self._assert_registered(EmailUsageTracker)
    def test_sms_usage_tracker_registered(self):        self._assert_registered(SMSUsageTracker)
    def test_onboarding_state_registered(self):         self._assert_registered(OnboardingState)
    def test_tenant_sync_log_registered(self):          self._assert_registered(TenantSyncLog)
    def test_data_export_log_registered(self):          self._assert_registered(DataExportLog)
    def test_email_delivery_log_registered(self):       self._assert_registered(EmailDeliveryLog)
    def test_stripe_connection_registered(self):        self._assert_registered(StripeConnection)
    def test_stripe_response_registered(self):          self._assert_registered(StripeResponse)
    def test_stripe_log_registered(self):               self._assert_registered(StripeLog)
    def test_stripe_connection_log_registered(self):    self._assert_registered(StripeConnectionLog)
    def test_stripe_api_request_log_registered(self):   self._assert_registered(StripeAPIRequestLog)
    def test_webhook_log_registered(self):              self._assert_registered(WebhookLog)
    def test_process_transaction_registered(self):      self._assert_registered(ProcessTransaction)
    def test_navigation_audit_registered(self):         self._assert_registered(NavigationAudit)


# ─── 2. TenantModelAdmin Method Unit Tests ────────────────────────────────────

class TenantModelAdminMethodTest(SDTATestCase):
    """
    Direct unit tests for TenantModelAdmin.save_model() and delete_model().
    These tests bypass the HTTP layer and call the methods directly so the
    worker DB alias behavior can be exercised without an HTTP round-trip.
    """

    # TenantModelAdmin explicitly uses .using('worker'), so both aliases must
    # be included here.
    databases = ('default', 'worker')

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.staff_user

    # ── save_model ─────────────────────────────────────────────────────────

    def test_save_model_raises_when_tenant_id_missing(self):
        """save_model() must raise ValueError for a new object with no tenant_id."""
        from config.tenant_context import clear_current_tenant_id
        from staff.admin import TenantModelAdmin

        clear_current_tenant_id()
        try:
            product_admin = TenantModelAdmin(InventoryItem, admin.site)
            obj = InventoryItem(name='No Tenant Product')   # tenant_id is None
            with self.assertRaises(ValueError):
                product_admin.save_model(self.request, obj, form=None, change=False)
        finally:
            from config.tenant_context import set_current_tenant_id
            set_current_tenant_id(self.tenant_id)

    def test_save_model_persists_object_via_worker(self):
        """save_model() calls obj.save(using='worker')."""
        from unittest.mock import MagicMock
        from staff.admin import TenantModelAdmin

        product_admin = TenantModelAdmin(InventoryItem, admin.site)
        obj = MagicMock(spec=InventoryItem)
        obj.tenant_id = self.tenant_id
        product_admin.save_model(self.request, obj, form=None, change=False)
        obj.save.assert_called_once_with(using='worker')

    def test_save_model_updates_existing_object(self):
        """save_model() with change=True persists updates."""
        from staff.admin import TenantModelAdmin

        product_admin = TenantModelAdmin(InventoryItem, admin.site)
        obj = InventoryItem.all_objects.using('worker').create(
            name='Before Update', tenant_id=self.tenant_id
        )
        obj.name = 'After Update'
        product_admin.save_model(self.request, obj, form=None, change=True)
        refreshed = InventoryItem.all_objects.using('worker').get(pk=obj.pk)
        self.assertEqual(refreshed.name, 'After Update')

    def test_save_model_writes_staff_audit_entry(self):
        """save_model() records an audit row for staff writes."""
        from staff.admin import TenantModelAdmin

        product_admin = TenantModelAdmin(InventoryItem, admin.site)
        obj = InventoryItem(name='Audit Product', tenant_id=self.tenant_id)
        self.request.POST = {'_staff_reason': 'Support correction'}
        product_admin.save_model(self.request, obj, form=None, change=False)
        audit = (
            SystemAudits.all_objects.using('worker')
            .filter(
                tenant_id=self.tenant_id,
                action='staff_admin_create',
                model_name='inventory.product',
            )
            .latest('created_on')
        )
        self.assertIn('Support correction', audit.created_by)

    # ── delete_model ───────────────────────────────────────────────────────

    def test_delete_model_removes_object(self):
        """delete_model() removes persisted objects."""
        from staff.admin import TenantModelAdmin

        product_admin = TenantModelAdmin(InventoryItem, admin.site)
        obj = InventoryItem.objects.create(name='Delete Product', tenant_id=self.tenant_id)
        obj_id = obj.pk
        product_admin.delete_model(self.request, obj)
        self.assertFalse(InventoryItem.all_objects.using('worker').filter(pk=obj_id).exists())

    def test_delete_model_writes_staff_audit_entry(self):
        """delete_model() records an audit row for staff deletes."""
        from staff.admin import TenantModelAdmin

        product_admin = TenantModelAdmin(InventoryItem, admin.site)
        obj = InventoryItem.objects.create(name='Delete Me', tenant_id=self.tenant_id)
        self.request.POST = {'_staff_reason': 'Cleanup'}
        product_admin.delete_model(self.request, obj)
        audit = (
            SystemAudits.all_objects.using('worker')
            .filter(
                tenant_id=self.tenant_id,
                action='staff_admin_delete',
                model_name='inventory.product',
            )
            .latest('created_on')
        )
        self.assertIn('Cleanup', audit.created_by)

    # ── get_queryset ───────────────────────────────────────────────────────

    def test_get_queryset_uses_worker_alias(self):
        """get_queryset() returns a queryset bound to the worker DB alias."""
        from staff.admin import TenantModelAdmin

        product_admin = TenantModelAdmin(InventoryItem, admin.site)
        qs = product_admin.get_queryset(self.request)
        self.assertEqual(qs.db, 'worker')

    def test_get_queryset_returns_all_tenants(self):
        """
        get_queryset() binds to the 'worker' alias, which in production uses
        the sdta_migration role (BYPASSRLS=TRUE) to see all tenants' rows.
        In SQLite tests there is no RLS; we verify only that the alias is
        'worker' (the production RLS bypass cannot be exercised here).
        """
        from staff.admin import TenantModelAdmin

        product_admin = TenantModelAdmin(InventoryItem, admin.site)
        qs = product_admin.get_queryset(self.request)
        self.assertEqual(qs.db, 'worker')

    def test_support_group_is_read_only(self):
        """Support role can view but not add/change/delete."""
        from staff.admin import TenantModelAdmin

        support = Group.objects.create(name='support')
        self.staff_user.is_superuser = False
        self.staff_user.save(update_fields=['is_superuser'])
        self.staff_user.groups.add(support)

        product_admin = TenantModelAdmin(InventoryItem, admin.site)
        self.assertTrue(product_admin.has_view_permission(self.request))
        self.assertFalse(product_admin.has_add_permission(self.request))
        self.assertFalse(product_admin.has_change_permission(self.request))
        self.assertFalse(product_admin.has_delete_permission(self.request))

    def test_ops_group_can_write_but_not_delete(self):
        """Ops role can add/change but cannot delete."""
        from staff.admin import TenantModelAdmin

        ops = Group.objects.create(name='ops')
        self.staff_user.is_superuser = False
        self.staff_user.save(update_fields=['is_superuser'])
        self.staff_user.groups.add(ops)

        product_admin = TenantModelAdmin(InventoryItem, admin.site)
        self.assertTrue(product_admin.has_view_permission(self.request))
        self.assertTrue(product_admin.has_add_permission(self.request))
        self.assertTrue(product_admin.has_change_permission(self.request))
        self.assertFalse(product_admin.has_delete_permission(self.request))


# ─── 3. Admin Changelist HTTP 200 Smoke Tests ─────────────────────────────────

@override_settings(
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
    AXES_ENABLED=False,
)
class AdminChangelistViewTests(SDTATestCase):
    """
    Smoke tests: each registered model's changelist URL must return HTTP 200
    when accessed by a superuser staff account.
    Tests populate minimal fixture data so the changelist has at least one row
    to render, which exercises list_display fields.
    """

    # Admin views call TenantModelAdmin.get_queryset().using('worker').
    databases = ('default', 'worker')

    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff_user)

    def _get(self, url):
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 200,
            msg=f'Expected HTTP 200 for {url}, got {response.status_code}',
        )
        return response

    # ── staff ──────────────────────────────────────────────────────────────

    def test_staff_staffuser_changelist(self):
        self._get('/admin/staff/staffuser/')

    # ── users ──────────────────────────────────────────────────────────────

    def test_users_department_changelist(self):
        self.make_department()
        self._get('/admin/users/department/')

    def test_users_position_changelist(self):
        self.make_position()
        self._get('/admin/users/position/')

    def test_users_role_changelist(self):
        self.make_role()
        self._get('/admin/users/role/')

    def test_users_user_changelist(self):
        self.make_user(email='cl_user@acme.com')
        self._get('/admin/users/user/')

    def test_users_employeerole_changelist(self):
        from users.models import EmployeeRole
        user = self.make_user(email='er_cl@acme.com')
        role = self.make_role()
        EmployeeRole.objects.create(employee=user, role=role)
        self._get('/admin/users/employeerole/')

    def test_users_employeeposition_changelist(self):
        from users.models import EmployeePosition
        user = self.make_user(email='ep_cl@acme.com')
        pos = self.make_position()
        EmployeePosition.objects.create(employee=user, position=pos)
        self._get('/admin/users/employeeposition/')

    def test_users_rolepermission_changelist(self):
        from users.models import RolePermission
        role = self.make_role()
        RolePermission.objects.create(role=role, resource_key='customers')
        self._get('/admin/users/rolepermission/')

    def test_users_tenantpreference_changelist(self):
        from users.models import TenantPreference
        # TenantPreference has unique_together on tenant_id; use get_or_create
        TenantPreference.objects.get_or_create(tenant_id=self.tenant_id)
        self._get('/admin/users/tenantpreference/')

    def test_users_employeepreference_changelist(self):
        from users.models import EmployeePreference
        user = self.make_user(email='empref_cl@acme.com')
        EmployeePreference.objects.create(user=user)
        self._get('/admin/users/employeepreference/')

    def test_users_sessionlog_changelist(self):
        from datetime import datetime, timezone
        from users.models import SessionLog
        import uuid
        user = self.make_user(email='sl_cl@acme.com')
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        SessionLog.objects.create(
            user=user,
            session_id=str(uuid.uuid4()),
            login_at=now,
            expiration_at=now,
            ip_address='127.0.0.1',
            user_agent='TestAgent/1.0',
        )
        self._get('/admin/users/sessionlog/')

    def test_users_loginattemptlog_changelist(self):
        from users.models import LoginAttemptLog
        LoginAttemptLog.objects.create(
            user_email='attempt@acme.com',
            ip_address='127.0.0.1',
            user_agent='TestAgent/1.0',
            success=False,
        )
        self._get('/admin/users/loginattemptlog/')

    # ── crm ────────────────────────────────────────────────────────────────

    def test_crm_person_changelist(self):
        self.make_person()
        self._get('/admin/crm/person/')

    def test_crm_customer_changelist(self):
        self.make_customer()
        self._get('/admin/crm/customer/')

    def test_crm_contact_changelist(self):
        from crm.models import Contact
        customer = self.make_customer()
        person = self.make_person(first_name='CL', last_name='Contact')
        Contact.objects.create(customer=customer, person=person)
        self._get('/admin/crm/contact/')

    def test_crm_address_changelist(self):
        from crm.models import Address
        customer = self.make_customer()
        Address.objects.create(customer=customer, address_type='Billing')
        self._get('/admin/crm/address/')

    def test_crm_phone_changelist(self):
        from crm.models import Phone
        customer = self.make_customer()
        Phone.objects.create(customer=customer, number='555-1234')
        self._get('/admin/crm/phone/')

    def test_crm_social_changelist(self):
        from crm.models import Social
        customer = self.make_customer()
        # Social.type and .value are the actual field names (not platform/handle)
        Social.objects.create(customer=customer, type='Email', value='test@example.com')
        self._get('/admin/crm/social/')

    def test_crm_lead_changelist(self):
        from crm.models import Lead
        Lead.objects.create(
            customer=self.make_customer(),
            person=self.make_person(first_name='Lead', last_name='Corp'),
        )
        self._get('/admin/crm/lead/')

    def test_crm_opportunity_changelist(self):
        from crm.models import Opportunity
        customer = self.make_customer()
        Opportunity.objects.create(name='Test Opp', customer=customer)
        self._get('/admin/crm/opportunity/')

    def test_crm_opportunitycontacts_changelist(self):
        from crm.models import Opportunity, OpportunityContacts
        customer = self.make_customer()
        # OpportunityContacts requires opportunity + contact + customer FKs
        contact = self.make_contact(customer=customer)
        opp = Opportunity.objects.create(name='OC Opp', customer=customer)
        OpportunityContacts.objects.create(
            opportunity=opp, contact=contact, customer=customer
        )
        self._get('/admin/crm/opportunitycontacts/')

    # ── inventory ──────────────────────────────────────────────────────────

    def test_inventory_product_changelist(self):
        self.make_product()
        self._get('/admin/inventory/inventoryitem/')

    def test_inventory_kititem_changelist(self):
        kit = self.make_product(name='CL Kit', is_bundle=True)
        component = self.make_product(name='CL Kit Component')
        KitItem.objects.create(kit=kit, product=component, quantity=1)
        self._get('/admin/inventory/kititem/')

    def test_inventory_invpricehistory_changelist(self):
        from datetime import timezone
        from datetime import datetime
        product = self.make_product(name='CL PH Product')
        InvPriceHistory.objects.create(
            product=product,
            old_unit_cost='1.00', new_unit_cost='2.00',
            old_unit_price='3.00', new_unit_price='4.00',
            changed_at=datetime.now(tz=timezone.utc),
        )
        self._get('/admin/inventory/invpricehistory/')

    def test_inventory_pricebook_changelist(self):
        Pricebook.objects.create(name='CL Pricebook')
        self._get('/admin/inventory/pricebook/')

    def test_inventory_pricebookentry_changelist(self):
        pb = Pricebook.objects.create(name='CL PBE PB')
        product = self.make_product(name='CL PBE Product')
        PricebookEntry.objects.create(pricebook=pb, product=product, price='5.00')
        self._get('/admin/inventory/pricebookentry/')

    # ── warehouse ──────────────────────────────────────────────────────────

    def test_warehouse_warehouse_changelist(self):
        self.make_warehouse()
        self._get('/admin/warehouse/warehouse/')

    def test_warehouse_sublocation_changelist(self):
        self.make_sub_location()
        self._get('/admin/warehouse/sublocation/')

    def test_warehouse_locationassignedinventory_changelist(self):
        sl = self.make_sub_location()
        product = self.make_product(name='CL LAI Product')
        LocationAssignedInventory.objects.create(
            sub_location=sl, product=product, quantity_on_hand=5
        )
        self._get('/admin/warehouse/locationassignedinventory/')

    def test_warehouse_inventorycount_changelist(self):
        product = self.make_product(name='CL IC Product')
        InventoryCount.objects.create(
            product=product, count_date=date.today(),
            physical_count=10, system_count=10,
        )
        self._get('/admin/warehouse/inventorycount/')

    def test_warehouse_inventorytransfer_changelist(self):
        product = self.make_product(name='CL IT Product')
        wh = self.make_warehouse()
        src = SubLocation.objects.create(warehouse=wh, location_number='CL-SRC')
        dst = SubLocation.objects.create(warehouse=wh, location_number='CL-DST')
        InventoryTransfer.objects.create(
            product=product, source_location=src, dest_location=dst,
            quantity=1, transfer_date=date.today(),
        )
        self._get('/admin/warehouse/inventorytransfer/')

    # ── procurement ────────────────────────────────────────────────────────

    def test_procurement_vendor_changelist(self):
        self.make_vendor()
        self._get('/admin/procurement/vendor/')

    def test_procurement_purchaseorder_changelist(self):
        vendor = self.make_vendor()
        self.make_purchase_order(vendor=vendor)
        self._get('/admin/procurement/purchaseorder/')

    def test_procurement_purchaseorderline_changelist(self):
        vendor = self.make_vendor()
        po = self.make_purchase_order(vendor=vendor)
        product = self.make_product(name='CL POL Product')
        PurchaseOrderLine.objects.create(
            purchase_order=po, product=product, quantity_ordered=1, unit_cost='1.00'
        )
        self._get('/admin/procurement/purchaseorderline/')

    def test_procurement_receiving_changelist(self):
        vendor = self.make_vendor()
        po = self.make_purchase_order(vendor=vendor)
        product = self.make_product(name='CL Recv Product')
        line = PurchaseOrderLine.objects.create(
            purchase_order=po, product=product, quantity_ordered=5, unit_cost='1.00'
        )
        Receiving.objects.create(
            purchase_order=po, po_line=line, product=product,
            quantity_received=3, received_date=date.today(),
        )
        self._get('/admin/procurement/receiving/')

    def test_procurement_lotinfo_changelist(self):
        vendor = self.make_vendor()
        po = self.make_purchase_order(vendor=vendor)
        product = self.make_product(name='CL Lot Product')
        line = PurchaseOrderLine.objects.create(
            purchase_order=po, product=product, quantity_ordered=10, unit_cost='1.00'
        )
        recv = Receiving.objects.create(
            purchase_order=po, po_line=line, product=product,
            quantity_received=5, received_date=date.today(),
        )
        LotInfo.objects.create(
            receiving=recv, product=product, lot_number='CL-LOT-001', quantity=5
        )
        self._get('/admin/procurement/lotinfo/')

    def test_procurement_vendorbill_changelist(self):
        vendor = self.make_vendor()
        VendorBill.objects.create(vendor=vendor)
        self._get('/admin/procurement/vendorbill/')

    def test_procurement_requisition_changelist(self):
        Requisition.objects.create(requisition_number='CL-REQ-001')
        self._get('/admin/procurement/requisition/')

    def test_procurement_requisitionline_changelist(self):
        req = Requisition.objects.create()
        product = self.make_product(name='CL RL Product')
        RequisitionLine.objects.create(
            requisition=req, product=product, quantity_requested=1
        )
        self._get('/admin/procurement/requisitionline/')

    # ── service ────────────────────────────────────────────────────────────

    def test_service_servicerequest_changelist(self):
        customer = self.make_customer()
        self.make_service_request(customer=customer)
        self._get('/admin/service/servicerequest/')

    def test_service_workorder_changelist(self):
        customer = self.make_customer()
        self.make_work_order(customer=customer)
        self._get('/admin/service/workorder/')

    def test_service_workorderline_changelist(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        product = self.make_product(name='CL WOL Product')
        WorkOrderLine.objects.create(
            work_order=wo, product=product, quantity='1', unit_price='10.00'
        )
        self._get('/admin/service/workorderline/')

    def test_service_workorderteam_changelist(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        user = self.make_user(email='cl_wot@acme.com')
        WorkOrderTeam.objects.create(work_order=wo, user=user)
        self._get('/admin/service/workorderteam/')

    def test_service_quote_changelist(self):
        customer = self.make_customer()
        Quote.objects.create(customer=customer)
        self._get('/admin/service/quote/')

    def test_service_quoteline_changelist(self):
        customer = self.make_customer()
        quote = Quote.objects.create(customer=customer)
        product = self.make_product(name='CL QL Product')
        QuoteLine.objects.create(
            quote=quote, product=product, quantity='1', unit_price='10.00'
        )
        self._get('/admin/service/quoteline/')

    def test_service_quoteasset_changelist(self):
        customer = self.make_customer()
        quote = Quote.objects.create(customer=customer)
        asset = self.make_asset(customer=customer)
        QuoteAsset.objects.create(quote=quote, asset=asset)
        self._get('/admin/service/quoteasset/')

    def test_service_invoice_changelist(self):
        customer = self.make_customer()
        self.make_invoice(customer=customer)
        self._get('/admin/service/invoice/')

    def test_service_invoiceline_changelist(self):
        customer = self.make_customer()
        invoice = self.make_invoice(customer=customer)
        product = self.make_product(name='CL IL Product')
        InvoiceLine.objects.create(
            invoice=invoice, product=product, quantity='1', unit_price='10.00'
        )
        self._get('/admin/service/invoiceline/')

    def test_service_invoiceasset_changelist(self):
        customer = self.make_customer()
        invoice = self.make_invoice(customer=customer)
        asset = self.make_asset(customer=customer)
        InvoiceAsset.objects.create(invoice=invoice, asset=asset)
        self._get('/admin/service/invoiceasset/')

    def test_service_workorderinvoice_changelist(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        invoice = self.make_invoice(customer=customer)
        WorkOrderInvoice.objects.create(work_order=wo, invoice=invoice)
        self._get('/admin/service/workorderinvoice/')

    def test_service_bank_changelist(self):
        Bank.objects.create(name='CL Bank')
        self._get('/admin/service/bank/')

    def test_service_payments_changelist(self):
        customer = self.make_customer()
        invoice = self.make_invoice(customer=customer)
        Payments.objects.create(
            invoice=invoice, amount='100.00', payment_date=date.today()
        )
        self._get('/admin/service/payments/')

    def test_service_accounting_changelist(self):
        Accounting.objects.create(
            account_number='4000', name='CL Revenue Account', account_type='Revenue'
        )
        self._get('/admin/service/accounting/')

    def test_service_ledger_changelist(self):
        acct = Accounting.objects.create(
            account_number='4001', name='CL Ledger Acct', account_type='Revenue'
        )
        Ledger.objects.create(
            account=acct, entry_type='Credit',
            amount='500.00', transaction_date=date.today(),
        )
        self._get('/admin/service/ledger/')

    # ── maintenance ────────────────────────────────────────────────────────

    def test_maintenance_asset_changelist(self):
        customer = self.make_customer()
        self.make_asset(customer=customer)
        self._get('/admin/maintenance/asset/')

    def test_maintenance_subasset_changelist(self):
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        SubAsset.objects.create(asset=asset, name='CL SubAsset')
        self._get('/admin/maintenance/subasset/')

    def test_maintenance_agreement_changelist(self):
        Agreement.objects.create(name='CL Agreement')
        self._get('/admin/maintenance/agreement/')

    def test_maintenance_customeragreement_changelist(self):
        customer = self.make_customer()
        ag = Agreement.objects.create(name='CL CA Agreement')
        CustomerAgreement.objects.create(
            agreement=ag, customer=customer,
            start_date=date(2025, 1, 1), end_date=date(2026, 1, 1),
        )
        self._get('/admin/maintenance/customeragreement/')

    def test_maintenance_preventativemaintenance_changelist(self):
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        PreventativeMaintenance.objects.create(
            asset=asset, task_name='CL PM Task', frequency='Monthly'
        )
        self._get('/admin/maintenance/preventativemaintenance/')

    # ── tasks ──────────────────────────────────────────────────────────────

    def test_tasks_task_changelist(self):
        Task.objects.create(title='CL Task')
        self._get('/admin/tasks/task/')

    def test_tasks_associatedtask_changelist(self):
        t1 = Task.objects.create(title='CL AT Task A')
        t2 = Task.objects.create(title='CL AT Task B')
        AssociatedTask.objects.create(task=t1, related_task=t2)
        self._get('/admin/tasks/associatedtask/')

    def test_tasks_tasktime_changelist(self):
        task = Task.objects.create(title='CL TT Task')
        TaskTime.objects.create(task=task, hours='1.00', work_date=date.today())
        self._get('/admin/tasks/tasktime/')

    def test_tasks_tasktodo_changelist(self):
        task = Task.objects.create(title='CL ToDo Task')
        TaskToDo.objects.create(task=task, title='CL ToDo Item')
        self._get('/admin/tasks/tasktodo/')

    def test_tasks_timeentry_changelist(self):
        TimeEntry.objects.create(work_date=date.today(), hours='2.00')
        self._get('/admin/tasks/timeentry/')

    # ── workforce ──────────────────────────────────────────────────────────

    def test_workforce_wgdivision_changelist(self):
        WGDivision.objects.create(name='CL Division')
        self._get('/admin/workforce/wgdivision/')

    def test_workforce_workgroup_changelist(self):
        self.make_work_group()
        self._get('/admin/workforce/workgroup/')

    def test_workforce_wgtrole_changelist(self):
        wg = self.make_work_group()
        WGTRole.objects.create(work_group=wg, name='CL Role')
        self._get('/admin/workforce/wgtrole/')

    def test_workforce_workgroupteam_changelist(self):
        wg = self.make_work_group()
        user = self.make_user(email='cl_wgt@acme.com')
        WorkGroupTeam.objects.create(work_group=wg, user=user)
        self._get('/admin/workforce/workgroupteam/')

    def test_workforce_workgroupasset_changelist(self):
        wg = self.make_work_group()
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        WorkGroupAsset.objects.create(work_group=wg, asset=asset)
        self._get('/admin/workforce/workgroupasset/')

    # ── automation ─────────────────────────────────────────────────────────

    def test_automation_communicationtrigger_changelist(self):
        CommunicationTrigger.objects.create(
            name='CL Trigger', event_name='cl.event'
        )
        self._get('/admin/automation/communicationtrigger/')

    def test_automation_communicationtemplate_changelist(self):
        CommunicationTemplate.objects.create(
            name='CL Template', body='CL body'
        )
        self._get('/admin/automation/communicationtemplate/')

    def test_automation_triggertemplate_changelist(self):
        trigger = CommunicationTrigger.objects.create(
            name='CL TT Trigger', event_name='cl.tt.event'
        )
        template = CommunicationTemplate.objects.create(
            name='CL TT Template', body='body'
        )
        TriggerTemplate.objects.create(trigger=trigger, template=template)
        self._get('/admin/automation/triggertemplate/')

    def test_automation_triggerlog_changelist(self):
        trigger = CommunicationTrigger.objects.create(
            name='CL TL Trigger', event_name='cl.tl.event'
        )
        template = CommunicationTemplate.objects.create(
            name='CL TL Template', body='body'
        )
        tt = TriggerTemplate.objects.create(trigger=trigger, template=template)
        TriggerLog.objects.create(trigger_template=tt, recipient='cl@example.com')
        self._get('/admin/automation/triggerlog/')

    # ── fleet ──────────────────────────────────────────────────────────────

    def test_fleet_vehicle_changelist(self):
        self.make_vehicle()
        self._get('/admin/fleet/vehicle/')

    def test_fleet_vehiclemaintenance_changelist(self):
        v = self.make_vehicle()
        VehicleMaintenance.objects.create(vehicle=v, service_type='CL Oil Change')
        self._get('/admin/fleet/vehiclemaintenance/')

    def test_fleet_mileagelog_changelist(self):
        v = self.make_vehicle()
        MileageLog.objects.create(
            vehicle=v, log_date=date.today(), miles_driven=50
        )
        self._get('/admin/fleet/mileagelog/')

    def test_fleet_vehicleinventory_changelist(self):
        v = self.make_vehicle()
        product = self.make_product(name='CL VI Product')
        VehicleInventory.objects.create(vehicle=v, product=product, quantity_on_hand=5)
        self._get('/admin/fleet/vehicleinventory/')

    # ── infrastructure ─────────────────────────────────────────────────────

    def test_infrastructure_tenantstate_changelist(self):
        self._get('/admin/infrastructure/tenantstate/')

    def test_infrastructure_tenantaddon_changelist(self):
        TenantAddOn.objects.create(tenant=self.tenant, add_on_key='cl_addon')
        self._get('/admin/infrastructure/tenantaddon/')

    def test_infrastructure_subdomainindex_changelist(self):
        import uuid
        subdomain = f'cl-si-{uuid.uuid4().hex[:6]}'
        ts = TenantState.objects.create(
            subdomain=subdomain, company_name='CL SI Corp', owner_email='o@clsi.com'
        )
        SubdomainIndex.objects.create(subdomain=subdomain, tenant=ts)
        self._get('/admin/infrastructure/subdomainindex/')

    def test_infrastructure_errorcode_changelist(self):
        ErrorCode.objects.create(code='CL-ERR-001', message_template='CL error msg')
        self._get('/admin/infrastructure/errorcode/')

    def test_infrastructure_systemaudits_changelist(self):
        SystemAudits.objects.create(action='cl_action', model_name='CLModel')
        self._get('/admin/infrastructure/systemaudits/')

    def test_infrastructure_notification_changelist(self):
        user = self.make_user(email='cl_notify@acme.com')
        Notification.objects.create(recipient=user, title='CL Notification')
        self._get('/admin/infrastructure/notification/')

    def test_infrastructure_issueserrors_changelist(self):
        IssuesErrors.objects.create(message='CL error message')
        self._get('/admin/infrastructure/issueserrors/')

    def test_infrastructure_storagetracker_changelist(self):
        StorageTracker.objects.create(period_year=2030, period_month=1)
        self._get('/admin/infrastructure/storagetracker/')

    def test_infrastructure_emailusagetracker_changelist(self):
        EmailUsageTracker.objects.create(period_year=2030, period_month=2)
        self._get('/admin/infrastructure/emailusagetracker/')

    def test_infrastructure_smsusagetracker_changelist(self):
        SMSUsageTracker.objects.create(period_year=2030, period_month=3)
        self._get('/admin/infrastructure/smsusagetracker/')

    def test_infrastructure_onboardingstate_changelist(self):
        OnboardingState.objects.create(step_key='cl_onboard_step')
        self._get('/admin/infrastructure/onboardingstate/')

    def test_infrastructure_tenantsynclog_changelist(self):
        TenantSyncLog.objects.create(sync_type='cl_sync')
        self._get('/admin/infrastructure/tenantsynclog/')

    def test_infrastructure_dataexportlog_changelist(self):
        DataExportLog.objects.create(export_type='cl_export')
        self._get('/admin/infrastructure/dataexportlog/')

    def test_infrastructure_emaildeliverylog_changelist(self):
        EmailDeliveryLog.objects.create(recipient_email='cl_edl@example.com')
        self._get('/admin/infrastructure/emaildeliverylog/')

    def test_infrastructure_stripeconnection_changelist(self):
        StripeConnection.objects.create(stripe_customer_id='cus_cl001')
        self._get('/admin/infrastructure/stripeconnection/')

    def test_infrastructure_striperesponse_changelist(self):
        StripeResponse.objects.create(
            stripe_object_type='customer', stripe_object_id='cus_sr001', raw_response={}
        )
        self._get('/admin/infrastructure/striperesponse/')

    def test_infrastructure_stripelog_changelist(self):
        StripeLog.objects.create(event_type='cl.stripe.event')
        self._get('/admin/infrastructure/stripelog/')

    def test_infrastructure_stripeconnectionlog_changelist(self):
        StripeConnectionLog.objects.create(action='cl_connected')
        self._get('/admin/infrastructure/stripeconnectionlog/')

    def test_infrastructure_stripeapirequestlog_changelist(self):
        StripeAPIRequestLog.objects.create(endpoint='/v1/cl', method='GET')
        self._get('/admin/infrastructure/stripeapirequestlog/')

    def test_infrastructure_webhooklog_changelist(self):
        WebhookLog.objects.create(source='cl', event_type='cl.webhook.event')
        self._get('/admin/infrastructure/webhooklog/')

    def test_infrastructure_processtransaction_changelist(self):
        ProcessTransaction.objects.create(
            idempotency_key='cl-idem-key', process_name='cl_process'
        )
        self._get('/admin/infrastructure/processtransaction/')

    def test_infrastructure_navigationaudit_changelist(self):
        NavigationAudit.objects.create(path='/cl/path/', method='GET')
        self._get('/admin/infrastructure/navigationaudit/')


# Real TenantModelAdmin.get_queryset uses .using('worker'). Under PostgreSQL,
# TestCase keeps test data in an open transaction on `default`; `worker` is a
# second session and cannot see those rows, so change views return 302. For
# these smoke tests only, read through the default connection (same as ORM
# factories). Restored in tearDownClass.
_ORIG_TENANT_MODEL_ADMIN_GET_QUERYSET = StaffTenantModelAdmin.get_queryset


def _tenant_model_admin_get_queryset_test_smoke(self, request):
    return admin.ModelAdmin.get_queryset(self, request)


# ─── 4. Admin Change View Smoke Tests ─────────────────────────────────────────

@override_settings(
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
    AXES_ENABLED=False,
)
class AdminChangeViewTests(SDTATestCase):
    """
    Verifies that the change (edit) view for a representative model from each
    app returns HTTP 200, ensuring the admin fieldsets render without error.
    """

    databases = ('default', 'worker')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        StaffTenantModelAdmin.get_queryset = _tenant_model_admin_get_queryset_test_smoke

    @classmethod
    def tearDownClass(cls):
        StaffTenantModelAdmin.get_queryset = _ORIG_TENANT_MODEL_ADMIN_GET_QUERYSET
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff_user)

    def _get_change(self, url):
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 200,
            msg=f'Expected HTTP 200 for change view {url}, got {response.status_code}',
        )

    def test_staff_user_change_view(self):
        self._get_change(f'/admin/staff/staffuser/{self.staff_user.pk}/change/')

    def test_users_department_change_view(self):
        dept = self.make_department()
        self._get_change(f'/admin/users/department/{dept.pk}/change/')

    def test_users_user_change_view(self):
        user = self.make_user(email='cv_user@acme.com')
        self._get_change(f'/admin/users/user/{user.pk}/change/')

    def test_crm_customer_change_view(self):
        customer = self.make_customer()
        self._get_change(f'/admin/crm/customer/{customer.pk}/change/')

    def test_inventory_product_change_view(self):
        product = self.make_product(name='CV Product')
        self._get_change(f'/admin/inventory/inventoryitem/{product.pk}/change/')

    def test_warehouse_warehouse_change_view(self):
        wh = self.make_warehouse()
        self._get_change(f'/admin/warehouse/warehouse/{wh.pk}/change/')

    def test_procurement_vendor_change_view(self):
        vendor = self.make_vendor()
        self._get_change(f'/admin/procurement/vendor/{vendor.pk}/change/')

    def test_service_workorder_change_view(self):
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        self._get_change(f'/admin/service/workorder/{wo.pk}/change/')

    def test_maintenance_asset_change_view(self):
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        self._get_change(f'/admin/maintenance/asset/{asset.pk}/change/')

    def test_tasks_task_change_view(self):
        task = Task.objects.create(title='CV Task')
        self._get_change(f'/admin/tasks/task/{task.pk}/change/')

    def test_workforce_workgroup_change_view(self):
        wg = self.make_work_group()
        self._get_change(f'/admin/workforce/workgroup/{wg.pk}/change/')

    def test_automation_communicationtrigger_change_view(self):
        ct = CommunicationTrigger.objects.create(
            name='CV Trigger', event_name='cv.event'
        )
        self._get_change(f'/admin/automation/communicationtrigger/{ct.pk}/change/')

    def test_fleet_vehicle_change_view(self):
        v = self.make_vehicle()
        self._get_change(f'/admin/fleet/vehicle/{v.pk}/change/')

    def test_infrastructure_tenantstate_change_view(self):
        self._get_change(f'/admin/infrastructure/tenantstate/{self.tenant.pk}/change/')

