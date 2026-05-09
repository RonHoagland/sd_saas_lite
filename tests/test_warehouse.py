# tests/test_warehouse.py
# CRUD and basic functionality tests for all models in the warehouse app.

from tests.base import SDTATestCase
from warehouse.models import (
    InventoryCount, InventoryTransfer, LocationAssignedInventory,
    Location, SubLocation, Warehouse,
)


# ─── Warehouse ────────────────────────────────────────────────────────────────

class WarehouseTest(SDTATestCase):

    def test_create(self):
        wh = Warehouse.objects.create(name='Main Hub', type='Physical Hub')
        self.assertEqual(wh.name, 'Main Hub')
        self.assertEqual(wh.status, 'Active')

    def test_str(self):
        wh = Warehouse.objects.create(
            name='Str Warehouse', warehouse_number='WH-01'
        )
        self.assertIn('WH-01', str(wh))
        self.assertIn('Str Warehouse', str(wh))

    def test_mobile_type(self):
        wh = Warehouse.objects.create(name='Van 42', type='Mobile')
        wh.refresh_from_db()
        self.assertEqual(wh.type, 'Mobile')

    def test_assigned_user_optional(self):
        wh = Warehouse.objects.create(name='Unassigned WH')
        self.assertIsNone(wh.assigned_user)

    def test_assigned_user_fk(self):
        user = self.make_user(email='wh_user@acme.com')
        wh = Warehouse.objects.create(name='Assigned WH', assigned_user=user)
        self.assertEqual(wh.assigned_user.email, 'wh_user@acme.com')

    def test_update_status(self):
        wh = Warehouse.objects.create(name='Status WH')
        wh.status = 'Inactive'
        wh.save()
        wh.refresh_from_db()
        self.assertEqual(wh.status, 'Inactive')

    def test_delete(self):
        wh = Warehouse.objects.create(name='Del WH')
        wh_id = wh.id
        wh.delete()
        self.assertFalse(Warehouse.objects.filter(id=wh_id).exists())


# ─── SubLocation ──────────────────────────────────────────────────────────────

class SubLocationTest(SDTATestCase):

    def test_create(self):
        wh = self.make_warehouse()
        sl = SubLocation.objects.create(
            warehouse=wh, location_number='A-01', location_type='Shelf'
        )
        self.assertEqual(sl.location_number, 'A-01')
        self.assertEqual(sl.status, 'Active')

    def test_str(self):
        wh = self.make_warehouse(name='SL Str WH')
        sl = SubLocation.objects.create(warehouse=wh, location_number='B-02')
        result = str(sl)
        self.assertIn('SL Str WH', result)
        self.assertIn('B-02', result)

    def test_warehouse_fk(self):
        wh = self.make_warehouse(name='SL FK WH')
        sl = SubLocation.objects.create(warehouse=wh, location_number='C-03')
        self.assertEqual(sl.warehouse.name, 'SL FK WH')

    def test_update_status(self):
        wh = self.make_warehouse()
        sl = SubLocation.objects.create(warehouse=wh, location_number='D-04')
        sl.status = 'Inactive'
        sl.save()
        sl.refresh_from_db()
        self.assertEqual(sl.status, 'Inactive')

    def test_delete(self):
        wh = self.make_warehouse()
        sl = SubLocation.objects.create(warehouse=wh, location_number='E-05')
        sl_id = sl.id
        sl.delete()
        self.assertFalse(SubLocation.objects.filter(id=sl_id).exists())


# ─── LocationAssignedInventory ────────────────────────────────────────────────

class LocationAssignedInventoryTest(SDTATestCase):

    def test_create(self):
        sl = self.make_sub_location()
        product = self.make_product(name='LAI Product')
        lai = LocationAssignedInventory.objects.create(
            sub_location=sl, product=product, quantity_on_hand=50
        )
        self.assertEqual(float(lai.quantity_on_hand), 50.0)

    def test_str(self):
        sl = self.make_sub_location(location_number='Z-01')
        product = self.make_product(name='LAI Str Product')
        lai = LocationAssignedInventory.objects.create(
            sub_location=sl, product=product, quantity_on_hand=10
        )
        result = str(lai)
        self.assertIn('LAI Str Product', result)
        self.assertIn('10', result)

    def test_serial_number_optional(self):
        sl = self.make_sub_location()
        product = self.make_product(name='No Serial')
        lai = LocationAssignedInventory.objects.create(
            sub_location=sl, product=product
        )
        self.assertEqual(lai.serial_number, '')

    def test_update_quantity(self):
        sl = self.make_sub_location()
        product = self.make_product(name='Qty Update Product')
        lai = LocationAssignedInventory.objects.create(
            sub_location=sl, product=product, quantity_on_hand=5
        )
        lai.quantity_on_hand = 25
        lai.save()
        lai.refresh_from_db()
        self.assertEqual(float(lai.quantity_on_hand), 25.0)

    def test_delete(self):
        sl = self.make_sub_location()
        product = self.make_product(name='Del LAI Product')
        lai = LocationAssignedInventory.objects.create(
            sub_location=sl, product=product
        )
        lai_id = lai.id
        lai.delete()
        self.assertFalse(LocationAssignedInventory.objects.filter(id=lai_id).exists())


# ─── InventoryCount ───────────────────────────────────────────────────────────

class InventoryCountTest(SDTATestCase):

    def test_create(self):
        from datetime import date
        product = self.make_product(name='Count Product')
        ic = InventoryCount.objects.create(
            product=product,
            count_date=date.today(),
            physical_count=100,
            system_count=95,
            variance=5,
        )
        self.assertEqual(float(ic.variance), 5.0)
        self.assertFalse(ic.adjustment_applied)

    def test_str(self):
        from datetime import date
        product = self.make_product(name='IC Str Product')
        ic = InventoryCount.objects.create(
            product=product,
            count_date=date.today(),
            physical_count=10,
            system_count=10,
        )
        result = str(ic)
        self.assertIn('IC Str Product', result)

    def test_adjustment_applied(self):
        from datetime import date
        product = self.make_product(name='Adj Product')
        ic = InventoryCount.objects.create(
            product=product,
            count_date=date.today(),
            physical_count=10,
            system_count=8,
            variance=2,
            adjustment_applied=True,
        )
        ic.refresh_from_db()
        self.assertTrue(ic.adjustment_applied)

    def test_delete(self):
        from datetime import date
        product = self.make_product(name='Del Count Product')
        ic = InventoryCount.objects.create(
            product=product,
            count_date=date.today(),
            physical_count=1,
            system_count=1,
        )
        ic_id = ic.id
        ic.delete()
        self.assertFalse(InventoryCount.objects.filter(id=ic_id).exists())


# ─── InventoryTransfer ────────────────────────────────────────────────────────

class InventoryTransferTest(SDTATestCase):

    def test_create(self):
        from datetime import date
        product = self.make_product(name='Transfer Product')
        wh = self.make_warehouse()
        src = SubLocation.objects.create(warehouse=wh, location_number='SRC-01')
        dst = SubLocation.objects.create(warehouse=wh, location_number='DST-01')
        transfer = InventoryTransfer.objects.create(
            product=product,
            source_location=src,
            dest_location=dst,
            quantity=10,
            transfer_date=date.today(),
        )
        self.assertEqual(float(transfer.quantity), 10.0)
        self.assertEqual(transfer.status, 'Pending')

    def test_str(self):
        from datetime import date
        product = self.make_product(name='IT Str Product')
        wh = self.make_warehouse()
        src = SubLocation.objects.create(warehouse=wh, location_number='SRC-S')
        dst = SubLocation.objects.create(warehouse=wh, location_number='DST-S')
        t = InventoryTransfer.objects.create(
            product=product, source_location=src, dest_location=dst,
            quantity=5, transfer_date=date.today(),
        )
        result = str(t)
        self.assertIn('IT Str Product', result)

    def test_update_status(self):
        from datetime import date
        product = self.make_product(name='Status Transfer')
        wh = self.make_warehouse()
        src = SubLocation.objects.create(warehouse=wh, location_number='SRC-U')
        dst = SubLocation.objects.create(warehouse=wh, location_number='DST-U')
        t = InventoryTransfer.objects.create(
            product=product, source_location=src, dest_location=dst,
            quantity=3, transfer_date=date.today(),
        )
        t.status = 'Completed'
        t.save()
        t.refresh_from_db()
        self.assertEqual(t.status, 'Completed')

    def test_delete(self):
        from datetime import date
        product = self.make_product(name='Del Transfer Product')
        wh = self.make_warehouse()
        src = SubLocation.objects.create(warehouse=wh, location_number='SRC-D')
        dst = SubLocation.objects.create(warehouse=wh, location_number='DST-D')
        t = InventoryTransfer.objects.create(
            product=product, source_location=src, dest_location=dst,
            quantity=1, transfer_date=date.today(),
        )
        t_id = t.id
        t.delete()
        self.assertFalse(InventoryTransfer.objects.filter(id=t_id).exists())


# ─── Location ──────────────────────────────────────────────────────────────

class LocationTest(SDTATestCase):

    def test_create(self):
        loc = Location.objects.create(name='Main Facility')
        self.assertEqual(loc.name, 'Main Facility')

    def test_str(self):
        loc = Location.objects.create(name='Str Location')
        self.assertEqual(str(loc), 'Str Location')

    def test_department_fk_optional(self):
        loc = Location.objects.create(name='No Dept')
        self.assertIsNone(loc.department)

    def test_department_fk(self):
        dept = self.make_department(name='Engineering')
        loc = Location.objects.create(name='Eng Location', department=dept)
        self.assertEqual(loc.department.name, 'Engineering')

    def test_warehouse_fk_optional(self):
        loc = Location.objects.create(name='No WH')
        self.assertIsNone(loc.warehouse)

    def test_warehouse_fk(self):
        wh = self.make_warehouse(name='Main Warehouse')
        loc = Location.objects.create(name='WH Location', warehouse=wh)
        self.assertEqual(loc.warehouse.name, 'Main Warehouse')

    def test_both_fks_optional_independently(self):
        dept = self.make_department()
        wh = self.make_warehouse()
        loc1 = Location.objects.create(name='Dept Only', department=dept)
        loc2 = Location.objects.create(name='WH Only', warehouse=wh)
        self.assertIsNotNone(loc1.department)
        self.assertIsNone(loc1.warehouse)
        self.assertIsNone(loc2.department)
        self.assertIsNotNone(loc2.warehouse)

    def test_update_name(self):
        loc = Location.objects.create(name='Old Name')
        loc.name = 'New Name'
        loc.save()
        loc.refresh_from_db()
        self.assertEqual(loc.name, 'New Name')

    def test_delete(self):
        loc = Location.objects.create(name='Del Location')
        loc_id = loc.id
        loc.delete()
        self.assertFalse(Location.objects.filter(id=loc_id).exists())
