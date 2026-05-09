# tests/test_infrastructure.py
# CRUD and basic functionality tests for all models in the infrastructure app.

import uuid
from datetime import date

from tests.base import SDTATestCase
from infrastructure.models import (
    DataExportLog, EmailDeliveryLog, EmailUsageTracker, ErrorCode,
    IssuesErrors, NavigationAudit, Notification, OnboardingState,
    ProcessTransaction, SMSUsageTracker, StorageTracker,
    StripeAPIRequestLog, StripeConnection, StripeConnectionLog, StripeLog,
    StripeResponse, SubdomainIndex, SystemAudits, TenantAddOn, TenantState,
    TenantSyncLog, WebhookLog,
)


# ─── TenantState ──────────────────────────────────────────────────────────────

class TenantStateTest(SDTATestCase):
    """
    TenantState does NOT extend TenantModel — it IS the tenant registry.
    The shared cls.tenant created in setUpTestData is a TenantState instance.
    """

    def test_create(self):
        ts = TenantState.objects.create(
            subdomain=f'ts-{uuid.uuid4().hex[:6]}',
            company_name='New Corp',
            owner_email='owner@newcorp.com',
            status='Active',
            tier='Plus',
        )
        self.assertEqual(ts.company_name, 'New Corp')
        self.assertEqual(ts.status, 'Active')
        self.assertEqual(ts.tier, 'Plus')

    def test_str(self):
        subdomain = f'str-{uuid.uuid4().hex[:6]}'
        ts = TenantState.objects.create(
            subdomain=subdomain, company_name='Str Corp',
            owner_email='o@str.com',
        )
        result = str(ts)
        self.assertIn('Str Corp', result)
        self.assertIn(subdomain, result)

    def test_status_choices(self):
        for status in ('Active', 'Suspended', 'Cancelled', 'Trial', 'Onboarding'):
            subdomain = f'st-{uuid.uuid4().hex[:6]}'
            ts = TenantState.objects.create(
                subdomain=subdomain, company_name=f'Co {status}',
                owner_email=f'o@{subdomain}.com', status=status,
            )
            ts.refresh_from_db()
            self.assertEqual(ts.status, status)
            ts.delete()

    def test_tier_choices(self):
        for tier in ('Lite', 'Plus', 'Pro', 'Enterprise'):
            subdomain = f'tier-{uuid.uuid4().hex[:6]}'
            ts = TenantState.objects.create(
                subdomain=subdomain, company_name=f'Tier {tier}',
                owner_email=f'o@{subdomain}.com', tier=tier,
            )
            ts.refresh_from_db()
            self.assertEqual(ts.tier, tier)
            ts.delete()

    def test_unique_subdomain(self):
        from django.db import IntegrityError
        subdomain = f'dup-{uuid.uuid4().hex[:6]}'
        TenantState.objects.create(
            subdomain=subdomain, company_name='Dup1', owner_email='a@dup.com'
        )
        with self.assertRaises(IntegrityError):
            TenantState.objects.create(
                subdomain=subdomain, company_name='Dup2', owner_email='b@dup.com'
            )

    def test_uuid_pk(self):
        subdomain = f'uuid-{uuid.uuid4().hex[:6]}'
        ts = TenantState.objects.create(
            subdomain=subdomain, company_name='UUID Corp', owner_email='o@uuid.com'
        )
        self.assertIsInstance(ts.id, uuid.UUID)

    def test_trial_subscription_optional(self):
        subdomain = f'opt-{uuid.uuid4().hex[:6]}'
        ts = TenantState.objects.create(
            subdomain=subdomain, company_name='Opt Corp', owner_email='o@opt.com'
        )
        self.assertIsNone(ts.trial_ends_on)
        self.assertIsNone(ts.subscription_ends_on)

    def test_update_status(self):
        subdomain = f'upd-{uuid.uuid4().hex[:6]}'
        ts = TenantState.objects.create(
            subdomain=subdomain, company_name='Upd Corp', owner_email='o@upd.com',
            status='Trial',
        )
        ts.status = 'Active'
        ts.save()
        ts.refresh_from_db()
        self.assertEqual(ts.status, 'Active')

    def test_delete(self):
        subdomain = f'del-{uuid.uuid4().hex[:6]}'
        ts = TenantState.objects.create(
            subdomain=subdomain, company_name='Del Corp', owner_email='o@del.com'
        )
        ts_id = ts.id
        ts.delete()
        self.assertFalse(TenantState.objects.filter(id=ts_id).exists())


# ─── TenantAddOn ──────────────────────────────────────────────────────────────

class TenantAddOnTest(SDTATestCase):

    def test_create(self):
        addon = TenantAddOn.objects.create(
            tenant=self.tenant, add_on_key='fleet_module'
        )
        self.assertTrue(addon.is_active)
        self.assertEqual(addon.add_on_key, 'fleet_module')

    def test_str(self):
        addon = TenantAddOn.objects.create(
            tenant=self.tenant, add_on_key='str_addon'
        )
        result = str(addon)
        self.assertIn('str_addon', result)

    def test_unique_tenant_add_on_key(self):
        from django.db import IntegrityError
        TenantAddOn.objects.create(tenant=self.tenant, add_on_key='unique_addon')
        with self.assertRaises(IntegrityError):
            TenantAddOn.objects.create(tenant=self.tenant, add_on_key='unique_addon')

    def test_inactive(self):
        addon = TenantAddOn.objects.create(
            tenant=self.tenant, add_on_key='inactive_addon', is_active=False
        )
        addon.refresh_from_db()
        self.assertFalse(addon.is_active)

    def test_expiry_dates_optional(self):
        addon = TenantAddOn.objects.create(tenant=self.tenant, add_on_key='no_exp')
        self.assertIsNone(addon.activated_on)
        self.assertIsNone(addon.expires_on)

    def test_expiry_dates_set(self):
        addon = TenantAddOn.objects.create(
            tenant=self.tenant,
            add_on_key='with_exp',
            activated_on=date(2025, 1, 1),
            expires_on=date(2026, 1, 1),
        )
        addon.refresh_from_db()
        self.assertEqual(addon.activated_on, date(2025, 1, 1))
        self.assertEqual(addon.expires_on, date(2026, 1, 1))

    def test_delete(self):
        addon = TenantAddOn.objects.create(tenant=self.tenant, add_on_key='del_addon')
        addon_id = addon.id
        addon.delete()
        self.assertFalse(TenantAddOn.objects.filter(id=addon_id).exists())

    def test_cascade_delete_with_tenant(self):
        """TenantAddOn deleted when parent TenantState is deleted."""
        subdomain = f'cascade-addon-{uuid.uuid4().hex[:6]}'
        ts = TenantState.objects.create(
            subdomain=subdomain, company_name='Cascade Addon Corp',
            owner_email='o@cascade.com',
        )
        addon = TenantAddOn.objects.create(tenant=ts, add_on_key='cascade_key')
        addon_id = addon.id
        ts.delete()
        self.assertFalse(TenantAddOn.objects.filter(id=addon_id).exists())


# ─── SubdomainIndex ───────────────────────────────────────────────────────────

class SubdomainIndexTest(SDTATestCase):

    def _make_tenant(self):
        subdomain = f'si-{uuid.uuid4().hex[:6]}'
        return TenantState.objects.create(
            subdomain=subdomain,
            company_name='SI Corp',
            owner_email='o@si.com',
        )

    def test_create(self):
        ts = self._make_tenant()
        si = SubdomainIndex.objects.create(subdomain=ts.subdomain, tenant=ts)
        self.assertEqual(si.subdomain, ts.subdomain)

    def test_str(self):
        ts = self._make_tenant()
        si = SubdomainIndex.objects.create(subdomain=ts.subdomain, tenant=ts)
        self.assertEqual(str(si), ts.subdomain)

    def test_one_to_one_tenant(self):
        ts = self._make_tenant()
        SubdomainIndex.objects.create(subdomain=ts.subdomain, tenant=ts)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            SubdomainIndex.objects.create(subdomain=f'alt-{uuid.uuid4().hex[:6]}', tenant=ts)

    def test_delete(self):
        ts = self._make_tenant()
        si = SubdomainIndex.objects.create(subdomain=ts.subdomain, tenant=ts)
        si_id = si.id
        si.delete()
        self.assertFalse(SubdomainIndex.objects.filter(id=si_id).exists())


# ─── SystemAudits ─────────────────────────────────────────────────────────────

class SystemAuditsTest(SDTATestCase):

    def test_create(self):
        audit = SystemAudits.objects.create(
            action='create', model_name='WorkOrder', object_id=uuid.uuid4()
        )
        self.assertEqual(audit.action, 'create')
        self.assertEqual(audit.model_name, 'WorkOrder')

    def test_str(self):
        audit = SystemAudits.objects.create(
            action='update', model_name='Invoice'
        )
        result = str(audit)
        self.assertIn('update', result)
        self.assertIn('Invoice', result)

    def test_actor_optional(self):
        audit = SystemAudits.objects.create(action='delete', model_name='Customer')
        self.assertIsNone(audit.actor)

    def test_actor_fk(self):
        user = self.make_user(email='auditor@acme.com')
        audit = SystemAudits.objects.create(
            action='login', model_name='User', actor=user
        )
        self.assertEqual(audit.actor.email, 'auditor@acme.com')

    def test_snapshots_optional(self):
        audit = SystemAudits.objects.create(action='view', model_name='Product')
        self.assertIsNone(audit.before_snapshot)
        self.assertIsNone(audit.after_snapshot)

    def test_snapshots_set(self):
        before = {'name': 'Old Name'}
        after = {'name': 'New Name'}
        audit = SystemAudits.objects.create(
            action='update', model_name='Product',
            before_snapshot=before, after_snapshot=after,
        )
        audit.refresh_from_db()
        self.assertEqual(audit.before_snapshot['name'], 'Old Name')
        self.assertEqual(audit.after_snapshot['name'], 'New Name')

    def test_delete(self):
        audit = SystemAudits.objects.create(action='del', model_name='Test')
        audit_id = audit.id
        audit.delete()
        self.assertFalse(SystemAudits.objects.filter(id=audit_id).exists())


# ─── Notification ─────────────────────────────────────────────────────────────

class NotificationTest(SDTATestCase):

    def test_create(self):
        user = self.make_user(email='notify@acme.com')
        notif = Notification.objects.create(
            recipient=user, title='Your work order is ready'
        )
        self.assertEqual(notif.title, 'Your work order is ready')
        self.assertEqual(notif.notification_type, 'Info')
        self.assertFalse(notif.is_read)

    def test_str(self):
        user = self.make_user(email='notify_str@acme.com')
        notif = Notification.objects.create(recipient=user, title='Str Notification')
        result = str(notif)
        self.assertIn('Str Notification', result)

    def test_type_choices(self):
        user = self.make_user(email='notify_type@acme.com')
        for ntype in ('Info', 'Warning', 'Error', 'Success'):
            n = Notification.objects.create(
                recipient=user, title=f'Type {ntype}', notification_type=ntype
            )
            n.refresh_from_db()
            self.assertEqual(n.notification_type, ntype)
            n.delete()

    def test_mark_read(self):
        user = self.make_user(email='read_notify@acme.com')
        notif = Notification.objects.create(recipient=user, title='Unread')
        notif.is_read = True
        notif.save()
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_action_url_optional(self):
        user = self.make_user(email='no_url@acme.com')
        notif = Notification.objects.create(recipient=user, title='No URL')
        self.assertEqual(notif.action_url, '')

    def test_delete(self):
        user = self.make_user(email='del_notify@acme.com')
        notif = Notification.objects.create(recipient=user, title='Del Notif')
        notif_id = notif.id
        notif.delete()
        self.assertFalse(Notification.objects.filter(id=notif_id).exists())


# ─── IssuesErrors ─────────────────────────────────────────────────────────────

class IssuesErrorsTest(SDTATestCase):

    def test_create(self):
        ie = IssuesErrors.objects.create(message='Unexpected NoneType error')
        self.assertEqual(ie.severity, 'Medium')
        self.assertEqual(ie.status, 'Open')

    def test_str(self):
        ie = IssuesErrors.objects.create(
            error_code='ERR-001', severity='High',
            message='Critical failure in payment processing module'
        )
        result = str(ie)
        self.assertIn('ERR-001', result)
        self.assertIn('High', result)

    def test_severity_choices(self):
        for sev in ('Low', 'Medium', 'High', 'Critical'):
            ie = IssuesErrors.objects.create(severity=sev, message=f'{sev} error')
            ie.refresh_from_db()
            self.assertEqual(ie.severity, sev)
            ie.delete()

    def test_status_choices(self):
        for status in ('Open', 'Acknowledged', 'Resolved', 'Ignored'):
            ie = IssuesErrors.objects.create(status=status, message=f'{status} error')
            ie.refresh_from_db()
            self.assertEqual(ie.status, status)
            ie.delete()

    def test_resolve(self):
        ie = IssuesErrors.objects.create(message='Resolvable error')
        ie.status = 'Resolved'
        ie.save()
        ie.refresh_from_db()
        self.assertEqual(ie.status, 'Resolved')

    def test_stack_trace_optional(self):
        ie = IssuesErrors.objects.create(message='No stack')
        self.assertEqual(ie.stack_trace, '')

    def test_delete(self):
        ie = IssuesErrors.objects.create(message='Del error')
        ie_id = ie.id
        ie.delete()
        self.assertFalse(IssuesErrors.objects.filter(id=ie_id).exists())


# ─── StorageTracker ───────────────────────────────────────────────────────────

class StorageTrackerTest(SDTATestCase):

    def test_create(self):
        st = StorageTracker.objects.create(
            period_year=2026, period_month=1, bytes_used=1024000, file_count=50
        )
        self.assertEqual(st.bytes_used, 1024000)
        self.assertEqual(st.file_count, 50)

    def test_str(self):
        st = StorageTracker.objects.create(period_year=2026, period_month=3)
        result = str(st)
        self.assertIn('2026', result)
        self.assertIn('03', result)

    def test_unique_tenant_period(self):
        from django.db import IntegrityError
        StorageTracker.objects.create(period_year=2025, period_month=6)
        with self.assertRaises(IntegrityError):
            StorageTracker.objects.create(period_year=2025, period_month=6)

    def test_default_values(self):
        st = StorageTracker.objects.create(period_year=2024, period_month=12)
        self.assertEqual(st.bytes_used, 0)
        self.assertEqual(st.file_count, 0)

    def test_delete(self):
        st = StorageTracker.objects.create(period_year=2023, period_month=1)
        st_id = st.id
        st.delete()
        self.assertFalse(StorageTracker.objects.filter(id=st_id).exists())


# ─── EmailUsageTracker ────────────────────────────────────────────────────────

class EmailUsageTrackerTest(SDTATestCase):

    def test_create(self):
        et = EmailUsageTracker.objects.create(
            period_year=2026, period_month=2, emails_sent=150
        )
        self.assertEqual(et.emails_sent, 150)

    def test_str(self):
        et = EmailUsageTracker.objects.create(period_year=2026, period_month=4)
        result = str(et)
        self.assertIn('2026', result)
        self.assertIn('04', result)

    def test_unique_tenant_period(self):
        from django.db import IntegrityError
        EmailUsageTracker.objects.create(period_year=2025, period_month=5)
        with self.assertRaises(IntegrityError):
            EmailUsageTracker.objects.create(period_year=2025, period_month=5)

    def test_default_zero(self):
        et = EmailUsageTracker.objects.create(period_year=2024, period_month=11)
        self.assertEqual(et.emails_sent, 0)

    def test_delete(self):
        et = EmailUsageTracker.objects.create(period_year=2023, period_month=2)
        et_id = et.id
        et.delete()
        self.assertFalse(EmailUsageTracker.objects.filter(id=et_id).exists())


# ─── SMSUsageTracker ──────────────────────────────────────────────────────────

class SMSUsageTrackerTest(SDTATestCase):

    def test_create(self):
        st = SMSUsageTracker.objects.create(
            period_year=2026, period_month=2, sms_sent=75
        )
        self.assertEqual(st.sms_sent, 75)

    def test_str(self):
        st = SMSUsageTracker.objects.create(period_year=2026, period_month=5)
        result = str(st)
        self.assertIn('2026', result)

    def test_unique_tenant_period(self):
        from django.db import IntegrityError
        SMSUsageTracker.objects.create(period_year=2025, period_month=7)
        with self.assertRaises(IntegrityError):
            SMSUsageTracker.objects.create(period_year=2025, period_month=7)

    def test_delete(self):
        st = SMSUsageTracker.objects.create(period_year=2023, period_month=3)
        st_id = st.id
        st.delete()
        self.assertFalse(SMSUsageTracker.objects.filter(id=st_id).exists())


# ─── OnboardingState ──────────────────────────────────────────────────────────

class OnboardingStateTest(SDTATestCase):

    def test_create(self):
        os = OnboardingState.objects.create(step_key='create_first_customer')
        self.assertEqual(os.step_key, 'create_first_customer')
        self.assertFalse(os.is_completed)

    def test_str(self):
        os = OnboardingState.objects.create(step_key='str_step')
        result = str(os)
        self.assertIn('str_step', result)
        self.assertIn('pending', result)

    def test_complete_step(self):
        os = OnboardingState.objects.create(step_key='set_up_team')
        os.is_completed = True
        os.save()
        os.refresh_from_db()
        self.assertTrue(os.is_completed)
        result = str(os)
        self.assertIn('done', result)

    def test_unique_tenant_step_key(self):
        from django.db import IntegrityError
        OnboardingState.objects.create(step_key='unique_step')
        with self.assertRaises(IntegrityError):
            OnboardingState.objects.create(step_key='unique_step')

    def test_sort_order_default(self):
        os = OnboardingState.objects.create(step_key='sort_step')
        self.assertEqual(os.sort_order, 0)

    def test_ordering_by_sort_order(self):
        OnboardingState.objects.create(step_key='step_b', sort_order=2)
        OnboardingState.objects.create(step_key='step_a', sort_order=1)
        steps = list(OnboardingState.objects.filter(
            step_key__in=['step_a', 'step_b']
        ))
        self.assertEqual(steps[0].step_key, 'step_a')
        self.assertEqual(steps[1].step_key, 'step_b')

    def test_delete(self):
        os = OnboardingState.objects.create(step_key='del_step')
        os_id = os.id
        os.delete()
        self.assertFalse(OnboardingState.objects.filter(id=os_id).exists())


# ─── TenantSyncLog ────────────────────────────────────────────────────────────

class TenantSyncLogTest(SDTATestCase):

    def test_create(self):
        tsl = TenantSyncLog.objects.create(sync_type='quickbooks_export')
        self.assertEqual(tsl.sync_type, 'quickbooks_export')
        self.assertEqual(tsl.status, 'Pending')

    def test_str(self):
        tsl = TenantSyncLog.objects.create(
            sync_type='xero_import', status='Success'
        )
        result = str(tsl)
        self.assertIn('xero_import', result)
        self.assertIn('Success', result)

    def test_status_choices(self):
        for status in ('Pending', 'Success', 'Partial', 'Failed'):
            tsl = TenantSyncLog.objects.create(
                sync_type=f'sync_{status}', status=status
            )
            tsl.refresh_from_db()
            self.assertEqual(tsl.status, status)
            tsl.delete()

    def test_records_processed_default(self):
        tsl = TenantSyncLog.objects.create(sync_type='default_sync')
        self.assertEqual(tsl.records_processed, 0)
        self.assertEqual(tsl.records_failed, 0)

    def test_update_records(self):
        tsl = TenantSyncLog.objects.create(sync_type='update_sync')
        tsl.records_processed = 500
        tsl.records_failed = 3
        tsl.save()
        tsl.refresh_from_db()
        self.assertEqual(tsl.records_processed, 500)
        self.assertEqual(tsl.records_failed, 3)

    def test_delete(self):
        tsl = TenantSyncLog.objects.create(sync_type='del_sync')
        tsl_id = tsl.id
        tsl.delete()
        self.assertFalse(TenantSyncLog.objects.filter(id=tsl_id).exists())


# ─── DataExportLog ────────────────────────────────────────────────────────────

class DataExportLogTest(SDTATestCase):

    def test_create(self):
        del_obj = DataExportLog.objects.create(export_type='full_export')
        self.assertEqual(del_obj.export_type, 'full_export')
        self.assertEqual(del_obj.status, 'Pending')

    def test_str(self):
        del_obj = DataExportLog.objects.create(
            export_type='invoices_csv', status='Completed'
        )
        result = str(del_obj)
        self.assertIn('invoices_csv', result)
        self.assertIn('Completed', result)

    def test_requested_by_optional(self):
        del_obj = DataExportLog.objects.create(export_type='no_user_export')
        self.assertIsNone(del_obj.requested_by)

    def test_requested_by_user(self):
        user = self.make_user(email='exporter@acme.com')
        del_obj = DataExportLog.objects.create(
            export_type='user_export', requested_by=user
        )
        self.assertEqual(del_obj.requested_by.email, 'exporter@acme.com')

    def test_status_choices(self):
        for status in ('Pending', 'Processing', 'Completed', 'Failed'):
            d = DataExportLog.objects.create(
                export_type=f'export_{status}', status=status
            )
            d.refresh_from_db()
            self.assertEqual(d.status, status)
            d.delete()

    def test_delete(self):
        del_obj = DataExportLog.objects.create(export_type='del_export')
        del_id = del_obj.id
        del_obj.delete()
        self.assertFalse(DataExportLog.objects.filter(id=del_id).exists())


# ─── EmailDeliveryLog ─────────────────────────────────────────────────────────

class EmailDeliveryLogTest(SDTATestCase):

    def test_create(self):
        edl = EmailDeliveryLog.objects.create(
            recipient_email='cust@example.com',
            subject='Your invoice is ready',
        )
        self.assertEqual(edl.recipient_email, 'cust@example.com')
        self.assertEqual(edl.status, 'Queued')

    def test_str(self):
        edl = EmailDeliveryLog.objects.create(
            recipient_email='str@example.com', subject='Str Subject', status='Sent'
        )
        result = str(edl)
        self.assertIn('str@example.com', result)
        self.assertIn('Str Subject', result)
        self.assertIn('Sent', result)

    def test_status_choices(self):
        for status in ('Queued', 'Sent', 'Delivered', 'Bounced', 'Failed', 'Spam'):
            edl = EmailDeliveryLog.objects.create(
                recipient_email=f'{status.lower()}@example.com', status=status
            )
            edl.refresh_from_db()
            self.assertEqual(edl.status, status)
            edl.delete()

    def test_trigger_log_optional(self):
        edl = EmailDeliveryLog.objects.create(recipient_email='no_tl@example.com')
        self.assertIsNone(edl.trigger_log)

    def test_provider_message_id_optional(self):
        edl = EmailDeliveryLog.objects.create(recipient_email='no_id@example.com')
        self.assertEqual(edl.provider_message_id, '')

    def test_delete(self):
        edl = EmailDeliveryLog.objects.create(recipient_email='del@example.com')
        edl_id = edl.id
        edl.delete()
        self.assertFalse(EmailDeliveryLog.objects.filter(id=edl_id).exists())


# ─── StripeConnection ─────────────────────────────────────────────────────────

class StripeConnectionTest(SDTATestCase):

    def test_create(self):
        sc = StripeConnection.objects.create(
            stripe_customer_id='cus_test123',
            stripe_subscription_id='sub_test456',
        )
        self.assertFalse(sc.is_active)
        self.assertEqual(sc.stripe_customer_id, 'cus_test123')

    def test_str(self):
        sc = StripeConnection.objects.create(stripe_customer_id='cus_str')
        result = str(sc)
        self.assertIn('cus_str', result)

    def test_activate(self):
        sc = StripeConnection.objects.create(stripe_customer_id='cus_act')
        sc.is_active = True
        sc.save()
        sc.refresh_from_db()
        self.assertTrue(sc.is_active)

    def test_optional_ids(self):
        sc = StripeConnection.objects.create()
        self.assertEqual(sc.stripe_customer_id, '')
        self.assertEqual(sc.stripe_subscription_id, '')

    def test_delete(self):
        sc = StripeConnection.objects.create(stripe_customer_id='cus_del')
        sc_id = sc.id
        sc.delete()
        self.assertFalse(StripeConnection.objects.filter(id=sc_id).exists())


# ─── StripeResponse ───────────────────────────────────────────────────────────

class StripeResponseTest(SDTATestCase):

    def test_create(self):
        sr = StripeResponse.objects.create(
            stripe_object_type='customer',
            stripe_object_id='cus_resp123',
            raw_response={'id': 'cus_resp123', 'object': 'customer'},
        )
        self.assertEqual(sr.stripe_object_type, 'customer')
        self.assertEqual(sr.raw_response['object'], 'customer')

    def test_str(self):
        sr = StripeResponse.objects.create(
            stripe_object_type='subscription',
            stripe_object_id='sub_str001',
            raw_response={},
        )
        result = str(sr)
        self.assertIn('subscription', result)
        self.assertIn('sub_str001', result)

    def test_delete(self):
        sr = StripeResponse.objects.create(
            stripe_object_type='invoice',
            stripe_object_id='inv_del',
            raw_response={},
        )
        sr_id = sr.id
        sr.delete()
        self.assertFalse(StripeResponse.objects.filter(id=sr_id).exists())


# ─── StripeLog ────────────────────────────────────────────────────────────────

class StripeLogTest(SDTATestCase):

    def test_create(self):
        sl = StripeLog.objects.create(
            event_type='customer.subscription.updated',
            stripe_object_id='sub_log001',
        )
        self.assertEqual(sl.event_type, 'customer.subscription.updated')

    def test_str(self):
        sl = StripeLog.objects.create(
            event_type='invoice.paid', stripe_object_id='inv_sl001'
        )
        result = str(sl)
        self.assertIn('invoice.paid', result)
        self.assertIn('inv_sl001', result)

    def test_amount_optional(self):
        sl = StripeLog.objects.create(event_type='test.event')
        self.assertIsNone(sl.amount)

    def test_amount_set(self):
        sl = StripeLog.objects.create(
            event_type='charge.succeeded', amount='99.99'
        )
        sl.refresh_from_db()
        self.assertEqual(float(sl.amount), 99.99)

    def test_delete(self):
        sl = StripeLog.objects.create(event_type='del.event')
        sl_id = sl.id
        sl.delete()
        self.assertFalse(StripeLog.objects.filter(id=sl_id).exists())


# ─── StripeConnectionLog ──────────────────────────────────────────────────────

class StripeConnectionLogTest(SDTATestCase):

    def test_create(self):
        scl = StripeConnectionLog.objects.create(action='connected')
        self.assertEqual(scl.action, 'connected')

    def test_str(self):
        scl = StripeConnectionLog.objects.create(action='disconnected')
        result = str(scl)
        self.assertIn('disconnected', result)

    def test_actor_optional(self):
        scl = StripeConnectionLog.objects.create(action='updated')
        self.assertIsNone(scl.actor)

    def test_actor_fk(self):
        user = self.make_user(email='stripe_actor@acme.com')
        scl = StripeConnectionLog.objects.create(action='connected', actor=user)
        self.assertEqual(scl.actor.email, 'stripe_actor@acme.com')

    def test_delete(self):
        scl = StripeConnectionLog.objects.create(action='del_action')
        scl_id = scl.id
        scl.delete()
        self.assertFalse(StripeConnectionLog.objects.filter(id=scl_id).exists())


# ─── StripeAPIRequestLog ──────────────────────────────────────────────────────

class StripeAPIRequestLogTest(SDTATestCase):

    def test_create(self):
        sarl = StripeAPIRequestLog.objects.create(
            endpoint='/v1/customers', method='POST', status='Success',
            http_status_code=200,
        )
        self.assertEqual(sarl.endpoint, '/v1/customers')
        self.assertEqual(sarl.status, 'Success')

    def test_str(self):
        sarl = StripeAPIRequestLog.objects.create(
            endpoint='/v1/invoices', method='GET', status='Failed',
        )
        result = str(sarl)
        self.assertIn('GET', result)
        self.assertIn('/v1/invoices', result)
        self.assertIn('Failed', result)

    def test_status_choices(self):
        for status in ('Success', 'Failed'):
            sarl = StripeAPIRequestLog.objects.create(
                endpoint='/test', method='POST', status=status
            )
            sarl.refresh_from_db()
            self.assertEqual(sarl.status, status)
            sarl.delete()

    def test_optional_fields(self):
        sarl = StripeAPIRequestLog.objects.create(
            endpoint='/v1/test', method='GET'
        )
        self.assertIsNone(sarl.http_status_code)
        self.assertEqual(sarl.request_payload, {})
        self.assertEqual(sarl.response_payload, {})
        self.assertIsNone(sarl.duration_ms)
        self.assertEqual(sarl.error_message, '')

    def test_delete(self):
        sarl = StripeAPIRequestLog.objects.create(
            endpoint='/v1/del', method='DELETE'
        )
        sarl_id = sarl.id
        sarl.delete()
        self.assertFalse(StripeAPIRequestLog.objects.filter(id=sarl_id).exists())


# ─── WebhookLog ───────────────────────────────────────────────────────────────

class WebhookLogTest(SDTATestCase):

    def test_create(self):
        wl = WebhookLog.objects.create(
            source='stripe', event_type='invoice.payment_succeeded'
        )
        self.assertEqual(wl.source, 'stripe')
        self.assertEqual(wl.status, 'Received')

    def test_str(self):
        wl = WebhookLog.objects.create(
            source='pusher', event_type='channel.message', status='Processed'
        )
        result = str(wl)
        self.assertIn('pusher', result)
        self.assertIn('channel.message', result)
        self.assertIn('Processed', result)

    def test_status_choices(self):
        for status in ('Received', 'Processed', 'Failed', 'Ignored'):
            wl = WebhookLog.objects.create(
                source='internal', event_type=f'evt.{status}', status=status
            )
            wl.refresh_from_db()
            self.assertEqual(wl.status, status)
            wl.delete()

    def test_raw_payload_default_empty(self):
        wl = WebhookLog.objects.create(source='stripe', event_type='test.event')
        self.assertEqual(wl.raw_payload, {})

    def test_raw_payload_set(self):
        payload = {'id': 'evt_001', 'type': 'invoice.paid'}
        wl = WebhookLog.objects.create(
            source='stripe', event_type='invoice.paid', raw_payload=payload
        )
        wl.refresh_from_db()
        self.assertEqual(wl.raw_payload['id'], 'evt_001')

    def test_delete(self):
        wl = WebhookLog.objects.create(source='del', event_type='del.event')
        wl_id = wl.id
        wl.delete()
        self.assertFalse(WebhookLog.objects.filter(id=wl_id).exists())


# ─── ErrorCode ────────────────────────────────────────────────────────────────

class ErrorCodeTest(SDTATestCase):
    """ErrorCode is a global (non-tenant) model."""

    def test_create(self):
        ec = ErrorCode.objects.create(
            code='AUTH-001',
            category='Authentication',
            message_template='Invalid credentials provided.',
        )
        self.assertEqual(ec.code, 'AUTH-001')
        self.assertFalse(ec.is_user_facing)

    def test_str(self):
        ec = ErrorCode.objects.create(
            code='STR-001',
            message_template='A str test error occurred with details here.',
        )
        result = str(ec)
        self.assertIn('STR-001', result)

    def test_unique_code(self):
        from django.db import IntegrityError
        ErrorCode.objects.create(code='DUP-001', message_template='Dup msg')
        with self.assertRaises(IntegrityError):
            ErrorCode.objects.create(code='DUP-001', message_template='Dup2')

    def test_is_user_facing(self):
        ec = ErrorCode.objects.create(
            code='USER-001',
            message_template='Something went wrong. Please try again.',
            is_user_facing=True,
        )
        ec.refresh_from_db()
        self.assertTrue(ec.is_user_facing)

    def test_uuid_pk(self):
        ec = ErrorCode.objects.create(code='UUID-001', message_template='UUID test')
        self.assertIsInstance(ec.id, uuid.UUID)

    def test_delete(self):
        ec = ErrorCode.objects.create(code='DEL-001', message_template='Del msg')
        ec_id = ec.id
        ec.delete()
        self.assertFalse(ErrorCode.objects.filter(id=ec_id).exists())


# ─── ProcessTransaction ───────────────────────────────────────────────────────

class ProcessTransactionTest(SDTATestCase):

    def test_create(self):
        pt = ProcessTransaction.objects.create(
            idempotency_key='idem-key-001', process_name='send_invoice_email'
        )
        self.assertEqual(pt.status, 'Pending')
        self.assertEqual(pt.idempotency_key, 'idem-key-001')

    def test_str(self):
        pt = ProcessTransaction.objects.create(
            idempotency_key='idem-str', process_name='generate_pdf',
            status='Completed',
        )
        result = str(pt)
        self.assertIn('generate_pdf', result)
        self.assertIn('Completed', result)

    def test_unique_tenant_idempotency_key(self):
        from django.db import IntegrityError
        ProcessTransaction.objects.create(
            idempotency_key='dup-idem', process_name='sync'
        )
        with self.assertRaises(IntegrityError):
            ProcessTransaction.objects.create(
                idempotency_key='dup-idem', process_name='sync2'
            )

    def test_status_choices(self):
        for status in ('Pending', 'Processing', 'Completed', 'Failed'):
            pt = ProcessTransaction.objects.create(
                idempotency_key=f'pt-{status}', process_name='test', status=status
            )
            pt.refresh_from_db()
            self.assertEqual(pt.status, status)
            pt.delete()

    def test_payload_default_empty(self):
        pt = ProcessTransaction.objects.create(
            idempotency_key='no-payload', process_name='empty'
        )
        self.assertEqual(pt.payload, {})
        self.assertEqual(pt.result, {})

    def test_delete(self):
        pt = ProcessTransaction.objects.create(
            idempotency_key='del-idem', process_name='del'
        )
        pt_id = pt.id
        pt.delete()
        self.assertFalse(ProcessTransaction.objects.filter(id=pt_id).exists())


# ─── NavigationAudit ──────────────────────────────────────────────────────────

class NavigationAuditTest(SDTATestCase):

    def test_create(self):
        na = NavigationAudit.objects.create(path='/api/v1/work-orders/', method='GET')
        self.assertEqual(na.path, '/api/v1/work-orders/')
        self.assertEqual(na.method, 'GET')

    def test_str(self):
        na = NavigationAudit.objects.create(
            path='/admin/service/workorder/', method='POST', http_status_code=200
        )
        result = str(na)
        self.assertIn('POST', result)
        self.assertIn('/admin/service/workorder/', result)
        self.assertIn('200', result)

    def test_user_optional(self):
        na = NavigationAudit.objects.create(path='/public/login/', method='GET')
        self.assertIsNone(na.user)

    def test_user_fk(self):
        user = self.make_user(email='nav_user@acme.com')
        na = NavigationAudit.objects.create(
            path='/dashboard/', method='GET', user=user
        )
        self.assertEqual(na.user.email, 'nav_user@acme.com')

    def test_http_status_optional(self):
        na = NavigationAudit.objects.create(path='/test/', method='GET')
        self.assertIsNone(na.http_status_code)

    def test_response_ms_optional(self):
        na = NavigationAudit.objects.create(path='/test/', method='GET')
        self.assertIsNone(na.response_ms)

    def test_performance_data(self):
        na = NavigationAudit.objects.create(
            path='/api/invoices/', method='GET',
            http_status_code=200, response_ms=45,
        )
        na.refresh_from_db()
        self.assertEqual(na.http_status_code, 200)
        self.assertEqual(na.response_ms, 45)

    def test_delete(self):
        na = NavigationAudit.objects.create(path='/del/', method='DELETE')
        na_id = na.id
        na.delete()
        self.assertFalse(NavigationAudit.objects.filter(id=na_id).exists())
