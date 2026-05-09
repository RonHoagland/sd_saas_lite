# tests/test_maintenance.py
# CRUD and basic functionality tests for all models in the maintenance app.

from datetime import date

from tests.base import SDTATestCase
from maintenance.models import (
    Agreement, Asset, CustomerAgreement, PreventativeMaintenance, SubAsset,
)


# ─── Asset ────────────────────────────────────────────────────────────────────

class AssetTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        asset = Asset.objects.create(name='Carrier HVAC Unit', customer=customer)
        self.assertEqual(asset.name, 'Carrier HVAC Unit')
        self.assertEqual(asset.status, 'Active')
        self.assertEqual(asset.customer, customer)

    def test_str(self):
        customer = self.make_customer()
        asset = Asset.objects.create(
            name='Str Asset', asset_number='A-001', customer=customer
        )
        result = str(asset)
        self.assertIn('A-001', result)
        self.assertIn('Str Asset', result)

    def test_read(self):
        customer = self.make_customer()
        asset = Asset.objects.create(name='Read Asset', customer=customer)
        fetched = Asset.objects.get(id=asset.id)
        self.assertEqual(fetched.name, 'Read Asset')

    def test_update_status(self):
        customer = self.make_customer()
        asset = Asset.objects.create(name='Status Asset', customer=customer)
        asset.status = 'Retired'
        asset.save()
        asset.refresh_from_db()
        self.assertEqual(asset.status, 'Retired')

    def test_delete(self):
        customer = self.make_customer()
        asset = Asset.objects.create(name='Del Asset', customer=customer)
        a_id = asset.id
        asset.delete()
        self.assertFalse(Asset.objects.filter(id=a_id).exists())

    def test_serial_number(self):
        customer = self.make_customer()
        asset = Asset.objects.create(
            name='Serial Asset', customer=customer,
            serial_number='SN-123456', manufacturer='Carrier',
        )
        asset.refresh_from_db()
        self.assertEqual(asset.serial_number, 'SN-123456')
        self.assertEqual(asset.manufacturer, 'Carrier')

    def test_address_fk_optional(self):
        customer = self.make_customer()
        asset = Asset.objects.create(name='No Addr Asset', customer=customer)
        self.assertIsNone(asset.address)

    def test_warranty_expiration(self):
        customer = self.make_customer()
        expiry = date(2027, 12, 31)
        asset = Asset.objects.create(
            name='Warranty Asset', customer=customer,
            warranty_expiration=expiry,
        )
        asset.refresh_from_db()
        self.assertEqual(asset.warranty_expiration, expiry)


# ─── SubAsset ─────────────────────────────────────────────────────────────────

class SubAssetTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        sub = SubAsset.objects.create(
            asset=asset, name='Compressor', manufacturer='Copeland'
        )
        self.assertEqual(sub.name, 'Compressor')
        self.assertEqual(sub.status, 'Active')

    def test_str(self):
        customer = self.make_customer()
        asset = self.make_asset(name='Parent Asset', customer=customer)
        sub = SubAsset.objects.create(asset=asset, name='Sub Motor')
        result = str(sub)
        self.assertIn('Parent Asset', result)
        self.assertIn('Sub Motor', result)

    def test_update_status(self):
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        sub = SubAsset.objects.create(asset=asset, name='Upd SubAsset')
        sub.status = 'Inactive'
        sub.save()
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'Inactive')

    def test_delete(self):
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        sub = SubAsset.objects.create(asset=asset, name='Del SubAsset')
        sub_id = sub.id
        sub.delete()
        self.assertFalse(SubAsset.objects.filter(id=sub_id).exists())

    def test_cascade_delete_with_asset(self):
        """SubAssets are deleted when parent Asset is deleted."""
        customer = self.make_customer()
        asset = self.make_asset(customer=customer, name='Cascade Asset')
        sub = SubAsset.objects.create(asset=asset, name='Cascade Sub')
        sub_id = sub.id
        asset.delete()
        self.assertFalse(SubAsset.objects.filter(id=sub_id).exists())


# ─── Agreement ────────────────────────────────────────────────────────────────

class AgreementTest(SDTATestCase):

    def test_create(self):
        ag = Agreement.objects.create(name='Annual PM Contract')
        self.assertEqual(ag.name, 'Annual PM Contract')
        self.assertEqual(ag.status, 'Active')
        self.assertEqual(ag.default_duration_months, 12)

    def test_str(self):
        ag = Agreement.objects.create(name='Str Agreement')
        self.assertEqual(str(ag), 'Str Agreement')

    def test_update_name(self):
        ag = Agreement.objects.create(name='Old Agreement')
        ag.name = 'New Agreement'
        ag.save()
        ag.refresh_from_db()
        self.assertEqual(ag.name, 'New Agreement')

    def test_delete(self):
        ag = Agreement.objects.create(name='Del Agreement')
        ag_id = ag.id
        ag.delete()
        self.assertFalse(Agreement.objects.filter(id=ag_id).exists())

    def test_inactive_status(self):
        ag = Agreement.objects.create(name='Inactive Ag', status='Inactive')
        ag.refresh_from_db()
        self.assertEqual(ag.status, 'Inactive')


# ─── CustomerAgreement ────────────────────────────────────────────────────────

class CustomerAgreementTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        ag = Agreement.objects.create(name='CA Test Ag')
        ca = CustomerAgreement.objects.create(
            agreement=ag,
            customer=customer,
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )
        self.assertEqual(ca.status, 'Active')
        self.assertFalse(ca.auto_renew)

    def test_str(self):
        customer = self.make_customer(company_name='CA Str Co')
        ag = Agreement.objects.create(name='CA Str Ag')
        ca = CustomerAgreement.objects.create(
            agreement=ag, customer=customer,
            start_date=date(2025, 1, 1), end_date=date(2026, 1, 1),
        )
        result = str(ca)
        self.assertIn('CA Str Ag', result)
        self.assertIn('CA Str Co', result)

    def test_auto_renew(self):
        customer = self.make_customer()
        ag = Agreement.objects.create(name='Renew Ag')
        ca = CustomerAgreement.objects.create(
            agreement=ag, customer=customer,
            start_date=date(2025, 1, 1), end_date=date(2026, 1, 1),
            auto_renew=True,
        )
        ca.refresh_from_db()
        self.assertTrue(ca.auto_renew)

    def test_update_status(self):
        customer = self.make_customer()
        ag = Agreement.objects.create(name='Status Ag')
        ca = CustomerAgreement.objects.create(
            agreement=ag, customer=customer,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        ca.status = 'Expired'
        ca.save()
        ca.refresh_from_db()
        self.assertEqual(ca.status, 'Expired')

    def test_delete(self):
        customer = self.make_customer()
        ag = Agreement.objects.create(name='Del CA Ag')
        ca = CustomerAgreement.objects.create(
            agreement=ag, customer=customer,
            start_date=date(2025, 1, 1), end_date=date(2026, 1, 1),
        )
        ca_id = ca.id
        ca.delete()
        self.assertFalse(CustomerAgreement.objects.filter(id=ca_id).exists())


# ─── PreventativeMaintenance ──────────────────────────────────────────────────

class PreventativeMaintenanceTest(SDTATestCase):

    def test_create(self):
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        pm = PreventativeMaintenance.objects.create(
            asset=asset,
            task_name='Filter Replacement',
            frequency='Monthly',
        )
        self.assertEqual(pm.task_name, 'Filter Replacement')
        self.assertEqual(pm.frequency, 'Monthly')
        self.assertEqual(pm.status, 'Active')

    def test_str(self):
        customer = self.make_customer()
        asset = self.make_asset(name='PM Asset', customer=customer)
        pm = PreventativeMaintenance.objects.create(
            asset=asset, task_name='Lubrication Check', frequency='Quarterly',
        )
        result = str(pm)
        self.assertIn('PM Asset', result)
        self.assertIn('Lubrication Check', result)
        self.assertIn('Quarterly', result)

    def test_frequency_choices(self):
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        for freq in ('Daily', 'Weekly', 'Monthly', 'Quarterly',
                     'Semi-Annual', 'Annual', 'As Needed'):
            pm = PreventativeMaintenance.objects.create(
                asset=asset, task_name=f'Task {freq}', frequency=freq
            )
            pm.refresh_from_db()
            self.assertEqual(pm.frequency, freq)
            pm.delete()

    def test_next_due_date(self):
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        next_due = date(2026, 6, 1)
        pm = PreventativeMaintenance.objects.create(
            asset=asset, task_name='Seasonal PM',
            frequency='Annual', next_due_date=next_due,
        )
        pm.refresh_from_db()
        self.assertEqual(pm.next_due_date, next_due)

    def test_delete(self):
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        pm = PreventativeMaintenance.objects.create(
            asset=asset, task_name='Del PM', frequency='Monthly',
        )
        pm_id = pm.id
        pm.delete()
        self.assertFalse(PreventativeMaintenance.objects.filter(id=pm_id).exists())
