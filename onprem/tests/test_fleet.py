# tests/test_fleet.py
# CRUD and basic functionality tests for all models in the fleet app.

from datetime import date

from tests.base import SDTATestCase
from fleet.models import MileageLog, Vehicle, VehicleInventory, VehicleMaintenance


# ─── Vehicle ──────────────────────────────────────────────────────────────────

class VehicleTest(SDTATestCase):

    def test_create(self):
        v = Vehicle.objects.create(name='Service Van 1', vehicle_number='VAN-01')
        self.assertEqual(v.name, 'Service Van 1')
        self.assertEqual(v.status, 'Active')
        self.assertEqual(v.vehicle_type, 'Van')

    def test_str(self):
        v = Vehicle.objects.create(
            name='Str Van', vehicle_number='VAN-STR',
            year=2022, make='Ford', model='Transit',
        )
        result = str(v)
        self.assertIn('VAN-STR', result)
        self.assertIn('Ford', result)
        self.assertIn('Transit', result)

    def test_vehicle_type_choices(self):
        for vtype in ('Van', 'Truck', 'Car', 'Trailer', 'Heavy Equipment', 'Other'):
            v = Vehicle.objects.create(name=f'Type {vtype}', vehicle_type=vtype)
            v.refresh_from_db()
            self.assertEqual(v.vehicle_type, vtype)
            v.delete()

    def test_status_choices(self):
        for status in ('Active', 'In Service', 'Out of Service', 'Retired'):
            v = Vehicle.objects.create(name=f'Status {status}', status=status)
            v.refresh_from_db()
            self.assertEqual(v.status, status)
            v.delete()

    def test_optional_fields_blank(self):
        v = Vehicle.objects.create(name='Minimal Vehicle')
        self.assertEqual(v.make, '')
        self.assertEqual(v.model, '')
        self.assertIsNone(v.year)
        self.assertEqual(v.vin, '')
        self.assertEqual(v.license_plate, '')
        self.assertIsNone(v.assigned_to)
        self.assertIsNone(v.assigned_work_group)
        self.assertIsNone(v.registration_expiry)
        self.assertIsNone(v.insurance_expiry)

    def test_assigned_to_user(self):
        user = self.make_user(email='driver@acme.com')
        v = Vehicle.objects.create(name='Assigned Van', assigned_to=user)
        self.assertEqual(v.assigned_to.email, 'driver@acme.com')

    def test_assigned_work_group(self):
        wg = self.make_work_group()
        v = Vehicle.objects.create(name='WG Van', assigned_work_group=wg)
        self.assertEqual(v.assigned_work_group, wg)

    def test_registration_insurance_expiry(self):
        reg = date(2026, 12, 31)
        ins = date(2027, 6, 30)
        v = Vehicle.objects.create(
            name='Expiry Van', registration_expiry=reg, insurance_expiry=ins
        )
        v.refresh_from_db()
        self.assertEqual(v.registration_expiry, reg)
        self.assertEqual(v.insurance_expiry, ins)

    def test_update_status(self):
        v = Vehicle.objects.create(name='Status Upd Van')
        v.status = 'Out of Service'
        v.save()
        v.refresh_from_db()
        self.assertEqual(v.status, 'Out of Service')

    def test_delete(self):
        v = Vehicle.objects.create(name='Del Van')
        v_id = v.id
        v.delete()
        self.assertFalse(Vehicle.objects.filter(id=v_id).exists())


# ─── VehicleMaintenance ───────────────────────────────────────────────────────

class VehicleMaintenanceTest(SDTATestCase):

    def test_create(self):
        v = self.make_vehicle()
        vm = VehicleMaintenance.objects.create(
            vehicle=v, service_type='Oil Change'
        )
        self.assertEqual(vm.service_type, 'Oil Change')
        self.assertEqual(vm.status, 'Scheduled')
        self.assertEqual(float(vm.cost), 0.0)

    def test_str(self):
        v = self.make_vehicle(name='VM Str Van', vehicle_number='VAN-VM')
        vm = VehicleMaintenance.objects.create(
            vehicle=v, service_type='Tire Rotation', service_date=date(2026, 3, 1)
        )
        result = str(vm)
        self.assertIn('Tire Rotation', result)
        self.assertIn('2026-03-01', result)

    def test_status_choices(self):
        v = self.make_vehicle()
        for status in ('Scheduled', 'Completed', 'Overdue', 'Cancelled'):
            vm = VehicleMaintenance.objects.create(
                vehicle=v, service_type=f'Svc {status}', status=status
            )
            vm.refresh_from_db()
            self.assertEqual(vm.status, status)
            vm.delete()

    def test_optional_date_fields(self):
        v = self.make_vehicle()
        vm = VehicleMaintenance.objects.create(vehicle=v, service_type='No Dates')
        self.assertIsNone(vm.service_date)
        self.assertIsNone(vm.next_service_date)

    def test_mileage_fields(self):
        v = self.make_vehicle()
        vm = VehicleMaintenance.objects.create(
            vehicle=v, service_type='Mileage Svc',
            mileage_at_service=50000, next_service_mileage=55000,
        )
        vm.refresh_from_db()
        self.assertEqual(vm.mileage_at_service, 50000)
        self.assertEqual(vm.next_service_mileage, 55000)

    def test_cost(self):
        v = self.make_vehicle()
        vm = VehicleMaintenance.objects.create(
            vehicle=v, service_type='Costly Svc', cost='250.00'
        )
        vm.refresh_from_db()
        self.assertEqual(float(vm.cost), 250.0)

    def test_performed_by_optional(self):
        v = self.make_vehicle()
        vm = VehicleMaintenance.objects.create(vehicle=v, service_type='Self Svc')
        self.assertEqual(vm.performed_by, '')

    def test_delete(self):
        v = self.make_vehicle()
        vm = VehicleMaintenance.objects.create(vehicle=v, service_type='Del Svc')
        vm_id = vm.id
        vm.delete()
        self.assertFalse(VehicleMaintenance.objects.filter(id=vm_id).exists())

    def test_cascade_delete_with_vehicle(self):
        """VehicleMaintenance deleted when parent Vehicle is deleted."""
        v = Vehicle.objects.create(name='Cascade VM Van')
        vm = VehicleMaintenance.objects.create(vehicle=v, service_type='Cascade Svc')
        vm_id = vm.id
        v.delete()
        self.assertFalse(VehicleMaintenance.objects.filter(id=vm_id).exists())


# ─── MileageLog ───────────────────────────────────────────────────────────────

class MileageLogTest(SDTATestCase):

    def test_create(self):
        v = self.make_vehicle()
        ml = MileageLog.objects.create(
            vehicle=v,
            log_date=date.today(),
            odometer_start=10000,
            odometer_end=10150,
            miles_driven=150,
        )
        self.assertEqual(ml.miles_driven, 150)

    def test_str(self):
        v = self.make_vehicle(name='ML Van', vehicle_number='ML-01')
        ml = MileageLog.objects.create(
            vehicle=v, log_date=date(2026, 4, 1),
            odometer_start=5000, odometer_end=5075, miles_driven=75,
        )
        result = str(ml)
        self.assertIn('75', result)
        self.assertIn('2026-04-01', result)

    def test_driver_optional(self):
        v = self.make_vehicle()
        ml = MileageLog.objects.create(
            vehicle=v, log_date=date.today(), miles_driven=0
        )
        self.assertIsNone(ml.driver)

    def test_driver_fk(self):
        v = self.make_vehicle()
        driver = self.make_user(email='ml_driver@acme.com')
        ml = MileageLog.objects.create(
            vehicle=v, log_date=date.today(), miles_driven=50, driver=driver
        )
        self.assertEqual(ml.driver.email, 'ml_driver@acme.com')

    def test_work_order_optional(self):
        v = self.make_vehicle()
        ml = MileageLog.objects.create(
            vehicle=v, log_date=date.today(), miles_driven=0
        )
        self.assertIsNone(ml.work_order)

    def test_work_order_link(self):
        v = self.make_vehicle()
        customer = self.make_customer()
        wo = self.make_work_order(customer=customer)
        ml = MileageLog.objects.create(
            vehicle=v, log_date=date.today(), miles_driven=30, work_order=wo
        )
        ml.refresh_from_db()
        self.assertEqual(ml.work_order_id, wo.id)

    def test_purpose_optional(self):
        v = self.make_vehicle()
        ml = MileageLog.objects.create(
            vehicle=v, log_date=date.today(), miles_driven=0
        )
        self.assertEqual(ml.purpose, '')

    def test_default_odometer_values(self):
        v = self.make_vehicle()
        ml = MileageLog.objects.create(vehicle=v, log_date=date.today())
        self.assertEqual(ml.odometer_start, 0)
        self.assertEqual(ml.odometer_end, 0)
        self.assertEqual(ml.miles_driven, 0)

    def test_delete(self):
        v = self.make_vehicle()
        ml = MileageLog.objects.create(vehicle=v, log_date=date.today())
        ml_id = ml.id
        ml.delete()
        self.assertFalse(MileageLog.objects.filter(id=ml_id).exists())

    def test_cascade_delete_with_vehicle(self):
        """MileageLog deleted when parent Vehicle is deleted."""
        v = Vehicle.objects.create(name='Cascade ML Van')
        ml = MileageLog.objects.create(vehicle=v, log_date=date.today(), miles_driven=0)
        ml_id = ml.id
        v.delete()
        self.assertFalse(MileageLog.objects.filter(id=ml_id).exists())


# ─── VehicleInventory ─────────────────────────────────────────────────────────

class VehicleInventoryTest(SDTATestCase):

    def test_create(self):
        v = self.make_vehicle()
        product = self.make_product(name='VI Product')
        vi = VehicleInventory.objects.create(
            vehicle=v, product=product, quantity_on_hand=10
        )
        self.assertEqual(float(vi.quantity_on_hand), 10.0)

    def test_str(self):
        v = self.make_vehicle(name='VI Van', vehicle_number='VI-01')
        product = self.make_product(name='VI Str Product')
        vi = VehicleInventory.objects.create(
            vehicle=v, product=product, quantity_on_hand=5
        )
        result = str(vi)
        self.assertIn('VI Str Product', result)
        self.assertIn('5', result)

    def test_default_quantities(self):
        v = self.make_vehicle()
        product = self.make_product(name='Default VI Product')
        vi = VehicleInventory.objects.create(vehicle=v, product=product)
        self.assertEqual(float(vi.quantity_on_hand), 0.0)
        self.assertEqual(float(vi.reorder_point), 0.0)

    def test_reorder_point(self):
        v = self.make_vehicle()
        product = self.make_product(name='Reorder VI Product')
        vi = VehicleInventory.objects.create(
            vehicle=v, product=product,
            quantity_on_hand='20', reorder_point='5',
        )
        vi.refresh_from_db()
        self.assertEqual(float(vi.reorder_point), 5.0)

    def test_update_quantity(self):
        v = self.make_vehicle()
        product = self.make_product(name='Qty VI Product')
        vi = VehicleInventory.objects.create(
            vehicle=v, product=product, quantity_on_hand=8
        )
        vi.quantity_on_hand = 12
        vi.save()
        vi.refresh_from_db()
        self.assertEqual(float(vi.quantity_on_hand), 12.0)

    def test_delete(self):
        v = self.make_vehicle()
        product = self.make_product(name='Del VI Product')
        vi = VehicleInventory.objects.create(vehicle=v, product=product)
        vi_id = vi.id
        vi.delete()
        self.assertFalse(VehicleInventory.objects.filter(id=vi_id).exists())

    def test_cascade_delete_with_vehicle(self):
        """VehicleInventory deleted when parent Vehicle is deleted."""
        v = Vehicle.objects.create(name='Cascade VI Van')
        product = self.make_product(name='Cascade VI Product')
        vi = VehicleInventory.objects.create(vehicle=v, product=product)
        vi_id = vi.id
        v.delete()
        self.assertFalse(VehicleInventory.objects.filter(id=vi_id).exists())
