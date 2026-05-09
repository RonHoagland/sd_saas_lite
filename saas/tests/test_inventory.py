# tests/test_inventory.py
# CRUD and basic functionality tests for all models in the inventory app.

from datetime import datetime, timezone
from decimal import Decimal

from tests.base import SDTATestCase
from inventory.models import InvPriceHistory, KitItem, Pricebook, PricebookEntry, InventoryItem


# ─── InventoryItem ────────────────────────────────────────────────────────────

class InventoryItemTest(SDTATestCase):

    def test_create_service_product(self):
        p = InventoryItem.objects.create(name='AC Tune-Up', type='Service')
        self.assertEqual(p.name, 'AC Tune-Up')
        self.assertEqual(p.type, 'Service')
        self.assertEqual(p.status, 'Active')
        self.assertFalse(p.is_low_stock)
        self.assertFalse(p.is_out_of_stock)

    def test_create_inventory_product(self):
        p = InventoryItem.objects.create(
            name='Filter 12x24',
            type='Product - Inventory',
            sku='FLT-12-24',
            unit_cost='4.50',
            unit_price='9.99',
        )
        self.assertEqual(p.sku, 'FLT-12-24')
        self.assertEqual(float(p.unit_price), 9.99)

    def test_str(self):
        p = InventoryItem.objects.create(name='Str Product', product_number='XT-0001')
        self.assertIn('XT-0001', str(p))
        self.assertIn('Str Product', str(p))

    def test_read(self):
        p = InventoryItem.objects.create(name='Read Product')
        fetched = InventoryItem.objects.get(id=p.id)
        self.assertEqual(fetched.name, 'Read Product')

    def test_update(self):
        p = InventoryItem.objects.create(name='Old Name')
        p.name = 'New Name'
        p.save()
        p.refresh_from_db()
        self.assertEqual(p.name, 'New Name')

    def test_delete(self):
        p = InventoryItem.objects.create(name='Del Product')
        p_id = p.id
        p.delete()
        self.assertFalse(InventoryItem.objects.filter(id=p_id).exists())

    def test_system_flags_default_false(self):
        p = InventoryItem.objects.create(name='Flag Product', type='Product - Inventory')
        self.assertFalse(p.is_low_stock)
        self.assertFalse(p.is_out_of_stock)

    def test_taxable_default_true(self):
        p = InventoryItem.objects.create(name='Tax Product')
        self.assertTrue(p.taxable)

    def test_bundle_flag(self):
        p = InventoryItem.objects.create(name='Bundle Kit', is_bundle=True)
        p.refresh_from_db()
        self.assertTrue(p.is_bundle)

    def test_preferred_vendor_fk(self):
        vendor = self.make_vendor(name='Parts Supplier')
        p = InventoryItem.objects.create(name='Vendored Part', preferred_vendor=vendor)
        self.assertEqual(p.preferred_vendor.name, 'Parts Supplier')

    def test_preferred_vendor_optional(self):
        p = InventoryItem.objects.create(name='No Vendor Part')
        self.assertIsNone(p.preferred_vendor)

    def test_status_choices(self):
        for status in ('Active', 'Hold', 'Discontinued'):
            p = InventoryItem.objects.create(name=f'Status {status}', status=status)
            p.refresh_from_db()
            self.assertEqual(p.status, status)


# ─── KitItem ──────────────────────────────────────────────────────────────────

class KitItemTest(SDTATestCase):

    def test_create(self):
        kit = self.make_product(name='HVAC Kit', is_bundle=True)
        component = self.make_product(name='Filter')
        ki = KitItem.objects.create(kit=kit, product=component, quantity=2)
        self.assertEqual(float(ki.quantity), 2.0)

    def test_str(self):
        kit = self.make_product(name='Str Kit')
        component = self.make_product(name='Str Part')
        ki = KitItem.objects.create(kit=kit, product=component, quantity=3)
        self.assertIn('Str Part', str(ki))
        self.assertIn('Str Kit', str(ki))

    def test_unique_kit_product(self):
        from django.db import IntegrityError
        kit = self.make_product(name='Unique Kit')
        component = self.make_product(name='Unique Part')
        KitItem.objects.create(kit=kit, product=component, quantity=1)
        with self.assertRaises(IntegrityError):
            KitItem.objects.create(kit=kit, product=component, quantity=2)

    def test_update_quantity(self):
        kit = self.make_product(name='Qty Kit')
        component = self.make_product(name='Qty Part')
        ki = KitItem.objects.create(kit=kit, product=component, quantity=1)
        ki.quantity = 5
        ki.save()
        ki.refresh_from_db()
        self.assertEqual(float(ki.quantity), 5.0)

    def test_delete(self):
        kit = self.make_product(name='Del Kit')
        component = self.make_product(name='Del Part')
        ki = KitItem.objects.create(kit=kit, product=component, quantity=1)
        ki_id = ki.id
        ki.delete()
        self.assertFalse(KitItem.objects.filter(id=ki_id).exists())


# ─── InvPriceHistory ──────────────────────────────────────────────────────────

class InvPriceHistoryTest(SDTATestCase):

    def test_create(self):
        product = self.make_product(name='Priced Part')
        now = datetime.now(tz=timezone.utc)
        ph = InvPriceHistory.objects.create(
            product=product,
            old_unit_cost='4.00',
            new_unit_cost='5.00',
            old_unit_price='8.00',
            new_unit_price='10.00',
            changed_at=now,
        )
        self.assertEqual(float(ph.new_unit_cost), 5.0)

    def test_str(self):
        product = self.make_product(name='PH Str Part')
        now = datetime.now(tz=timezone.utc)
        ph = InvPriceHistory.objects.create(
            product=product,
            old_unit_cost='1.00', new_unit_cost='2.00',
            old_unit_price='3.00', new_unit_price='4.00',
            changed_at=now,
        )
        self.assertIn('PH Str Part', str(ph))

    def test_changed_by_optional(self):
        product = self.make_product(name='PH No User')
        now = datetime.now(tz=timezone.utc)
        ph = InvPriceHistory.objects.create(
            product=product,
            old_unit_cost='1.00', new_unit_cost='2.00',
            old_unit_price='3.00', new_unit_price='4.00',
            changed_at=now,
        )
        self.assertIsNone(ph.changed_by)

    def test_delete(self):
        product = self.make_product(name='PH Del Part')
        now = datetime.now(tz=timezone.utc)
        ph = InvPriceHistory.objects.create(
            product=product,
            old_unit_cost='1.00', new_unit_cost='2.00',
            old_unit_price='3.00', new_unit_price='4.00',
            changed_at=now,
        )
        ph_id = ph.id
        ph.delete()
        self.assertFalse(InvPriceHistory.objects.filter(id=ph_id).exists())


# ─── Pricebook ────────────────────────────────────────────────────────────────

class PricebookTest(SDTATestCase):

    def test_create(self):
        pb = Pricebook.objects.create(name='Gold Pricing')
        self.assertEqual(pb.name, 'Gold Pricing')
        self.assertTrue(pb.is_active)

    def test_str(self):
        pb = Pricebook.objects.create(name='Str Pricebook')
        self.assertEqual(str(pb), 'Str Pricebook')

    def test_update(self):
        pb = Pricebook.objects.create(name='Old PB')
        pb.name = 'New PB'
        pb.save()
        pb.refresh_from_db()
        self.assertEqual(pb.name, 'New PB')

    def test_inactive(self):
        pb = Pricebook.objects.create(name='Inactive PB', is_active=False)
        pb.refresh_from_db()
        self.assertFalse(pb.is_active)

    def test_delete(self):
        pb = Pricebook.objects.create(name='Del PB')
        pb_id = pb.id
        pb.delete()
        self.assertFalse(Pricebook.objects.filter(id=pb_id).exists())


# ─── PricebookEntry ───────────────────────────────────────────────────────────

class PricebookEntryTest(SDTATestCase):

    def test_create(self):
        pb = Pricebook.objects.create(name='PBE Test PB')
        product = self.make_product(name='PBE Product')
        entry = PricebookEntry.objects.create(
            pricebook=pb, product=product, price='12.99'
        )
        self.assertEqual(float(entry.price), 12.99)
        self.assertEqual(entry.status, 'Active')

    def test_str(self):
        pb = Pricebook.objects.create(name='PBE Str PB')
        product = self.make_product(name='PBE Str Product')
        entry = PricebookEntry.objects.create(
            pricebook=pb, product=product, price='9.99'
        )
        result = str(entry)
        self.assertIn('PBE Str PB', result)
        self.assertIn('9.99', result)

    def test_unique_pricebook_product(self):
        from django.db import IntegrityError
        pb = Pricebook.objects.create(name='Unique PBE PB')
        product = self.make_product(name='Unique PBE Product')
        PricebookEntry.objects.create(pricebook=pb, product=product, price='10.00')
        with self.assertRaises(IntegrityError):
            PricebookEntry.objects.create(pricebook=pb, product=product, price='11.00')

    def test_update_price(self):
        pb = Pricebook.objects.create(name='Upd PBE PB')
        product = self.make_product(name='Upd PBE Product')
        entry = PricebookEntry.objects.create(
            pricebook=pb, product=product, price='5.00'
        )
        entry.price = Decimal('6.00')
        entry.save()
        entry.refresh_from_db()
        self.assertEqual(float(entry.price), 6.0)

    def test_delete(self):
        pb = Pricebook.objects.create(name='Del PBE PB')
        product = self.make_product(name='Del PBE Product')
        entry = PricebookEntry.objects.create(
            pricebook=pb, product=product, price='1.00'
        )
        entry_id = entry.id
        entry.delete()
        self.assertFalse(PricebookEntry.objects.filter(id=entry_id).exists())
