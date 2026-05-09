# tests/test_automation_equipment.py
# CRUD and basic functionality tests for equipment-related models in the automation app.

from datetime import date, datetime, timezone
from tests.base import SDTATestCase
from automation.models import Equipment, CheckInOut, CreditCard, EmployeePurchase


# ─── Equipment ────────────────────────────────────────────────────────────

class EquipmentTest(SDTATestCase):

    def test_create(self):
        eq = Equipment.objects.create(name='Power Drill')
        self.assertEqual(eq.name, 'Power Drill')
        self.assertEqual(eq.category, 'Other')
        self.assertEqual(eq.status, 'Available')

    def test_str(self):
        eq = Equipment.objects.create(
            name='Str Equipment', equipment_number='EQ-001'
        )
        result = str(eq)
        self.assertIn('EQ-001', result)
        self.assertIn('Str Equipment', result)

    def test_category_choices(self):
        for category in ('Power Tool', 'Hand Tool', 'Diagnostic', 'Safety', 'Other'):
            eq = Equipment.objects.create(name=f'Cat {category}', category=category)
            eq.refresh_from_db()
            self.assertEqual(eq.category, category)
            eq.delete()

    def test_status_choices(self):
        for status in ('Available', 'Checked Out', 'In Repair', 'Decommissioned'):
            eq = Equipment.objects.create(name=f'Status {status}', status=status)
            eq.refresh_from_db()
            self.assertEqual(eq.status, status)
            eq.delete()

    def test_serial_number_optional(self):
        eq = Equipment.objects.create(name='No Serial')
        self.assertEqual(eq.serial_number, '')

    def test_serial_number_set(self):
        eq = Equipment.objects.create(name='With Serial', serial_number='SN-123456')
        eq.refresh_from_db()
        self.assertEqual(eq.serial_number, 'SN-123456')

    def test_purchase_date_optional(self):
        eq = Equipment.objects.create(name='No Date')
        self.assertIsNone(eq.purchase_date)

    def test_purchase_cost_default_zero(self):
        eq = Equipment.objects.create(name='No Cost')
        self.assertEqual(float(eq.purchase_cost), 0.0)

    def test_purchase_cost_set(self):
        eq = Equipment.objects.create(name='With Cost', purchase_cost='199.99')
        eq.refresh_from_db()
        self.assertEqual(float(eq.purchase_cost), 199.99)

    def test_notes_optional(self):
        eq = Equipment.objects.create(name='No Notes')
        self.assertEqual(eq.notes, '')

    def test_update_status(self):
        eq = Equipment.objects.create(name='Upd Equipment')
        eq.status = 'In Repair'
        eq.save()
        eq.refresh_from_db()
        self.assertEqual(eq.status, 'In Repair')

    def test_delete(self):
        eq = Equipment.objects.create(name='Del Equipment')
        eq_id = eq.id
        eq.delete()
        self.assertFalse(Equipment.objects.filter(id=eq_id).exists())


# ─── CheckInOut ───────────────────────────────────────────────────────────

class CheckInOutTest(SDTATestCase):

    def test_create(self):
        eq = self.make_equipment()
        employee = self.make_user(email='checker@acme.com')
        now = datetime.now(tz=timezone.utc)
        cio = CheckInOut.objects.create(
            equipment=eq,
            employee=employee,
            checked_out_at=now,
        )
        self.assertEqual(cio.equipment, eq)
        self.assertEqual(cio.condition_out, 'Good')
        self.assertIsNone(cio.checked_in_at)

    def test_str(self):
        eq = self.make_equipment(name='Str Equipment')
        employee = self.make_user(email='str_cio@acme.com')
        now = datetime.now(tz=timezone.utc)
        cio = CheckInOut.objects.create(
            equipment=eq, employee=employee, checked_out_at=now
        )
        result = str(cio)
        self.assertIn('Str Equipment', result)

    def test_condition_out_choices(self):
        eq = self.make_equipment()
        employee = self.make_user(email='cond_test@acme.com')
        now = datetime.now(tz=timezone.utc)
        for condition in ('Good', 'Fair', 'Needs Repair'):
            cio = CheckInOut.objects.create(
                equipment=eq, employee=employee, checked_out_at=now,
                condition_out=condition
            )
            cio.refresh_from_db()
            self.assertEqual(cio.condition_out, condition)
            cio.delete()

    def test_condition_in_optional(self):
        eq = self.make_equipment()
        employee = self.make_user(email='no_cond_in@acme.com')
        now = datetime.now(tz=timezone.utc)
        cio = CheckInOut.objects.create(
            equipment=eq, employee=employee, checked_out_at=now
        )
        self.assertEqual(cio.condition_in, '')

    def test_condition_in_set(self):
        eq = self.make_equipment()
        employee = self.make_user(email='with_cond_in@acme.com')
        now = datetime.now(tz=timezone.utc)
        cio = CheckInOut.objects.create(
            equipment=eq, employee=employee, checked_out_at=now,
            checked_in_at=now, condition_in='Damaged'
        )
        cio.refresh_from_db()
        self.assertEqual(cio.condition_in, 'Damaged')

    def test_notes_optional(self):
        eq = self.make_equipment()
        employee = self.make_user(email='no_notes@acme.com')
        now = datetime.now(tz=timezone.utc)
        cio = CheckInOut.objects.create(
            equipment=eq, employee=employee, checked_out_at=now
        )
        self.assertEqual(cio.notes, '')

    def test_update_checked_in(self):
        eq = self.make_equipment()
        employee = self.make_user(email='update_cio@acme.com')
        now = datetime.now(tz=timezone.utc)
        cio = CheckInOut.objects.create(
            equipment=eq, employee=employee, checked_out_at=now
        )
        cio.checked_in_at = now
        cio.condition_in = 'Good'
        cio.save()
        cio.refresh_from_db()
        self.assertIsNotNone(cio.checked_in_at)
        self.assertEqual(cio.condition_in, 'Good')

    def test_delete(self):
        eq = self.make_equipment()
        employee = self.make_user(email='del_cio@acme.com')
        now = datetime.now(tz=timezone.utc)
        cio = CheckInOut.objects.create(
            equipment=eq, employee=employee, checked_out_at=now
        )
        cio_id = cio.id
        cio.delete()
        self.assertFalse(CheckInOut.objects.filter(id=cio_id).exists())


# ─── CreditCard ───────────────────────────────────────────────────────────

class CreditCardTest(SDTATestCase):

    def test_create(self):
        employee = self.make_user(email='cc_employee@acme.com')
        cc = CreditCard.objects.create(
            employee=employee,
            last_four='1234',
            expiration_date=date(2026, 12, 31),
        )
        self.assertEqual(cc.employee, employee)
        self.assertEqual(cc.last_four, '1234')
        self.assertEqual(cc.card_type, 'Visa')
        self.assertEqual(cc.status, 'Active')

    def test_str(self):
        employee = self.make_user(email='cc_str@acme.com')
        cc = CreditCard.objects.create(
            employee=employee,
            card_type='Mastercard',
            last_four='5678',
            expiration_date=date(2026, 12, 31),
        )
        result = str(cc)
        self.assertIn('5678', result)
        self.assertIn('Mastercard', result)

    def test_card_type_choices(self):
        employee = self.make_user(email='cc_type@acme.com')
        for card_type in ('Visa', 'Mastercard', 'Amex', 'Other'):
            cc = CreditCard.objects.create(
                employee=employee,
                card_type=card_type,
                last_four='0000',
                expiration_date=date(2026, 12, 31),
            )
            cc.refresh_from_db()
            self.assertEqual(cc.card_type, card_type)
            cc.delete()

    def test_status_choices(self):
        employee = self.make_user(email='cc_status@acme.com')
        for status in ('Active', 'Suspended', 'Cancelled'):
            cc = CreditCard.objects.create(
                employee=employee,
                last_four='0000',
                expiration_date=date(2026, 12, 31),
                status=status,
            )
            cc.refresh_from_db()
            self.assertEqual(cc.status, status)
            cc.delete()

    def test_issuing_bank_optional(self):
        cc = self.make_credit_card()
        self.assertEqual(cc.issuing_bank, '')

    def test_issuing_bank_set(self):
        employee = self.make_user(email='cc_bank@acme.com')
        cc = CreditCard.objects.create(
            employee=employee,
            last_four='1234',
            expiration_date=date(2026, 12, 31),
            issuing_bank='Chase Bank',
        )
        cc.refresh_from_db()
        self.assertEqual(cc.issuing_bank, 'Chase Bank')

    def test_credit_limit_default_zero(self):
        cc = self.make_credit_card()
        self.assertEqual(float(cc.credit_limit), 0.0)

    def test_credit_limit_set(self):
        employee = self.make_user(email='cc_limit@acme.com')
        cc = CreditCard.objects.create(
            employee=employee,
            last_four='1234',
            expiration_date=date(2026, 12, 31),
            credit_limit='5000.00',
        )
        cc.refresh_from_db()
        self.assertEqual(float(cc.credit_limit), 5000.0)

    def test_notes_optional(self):
        cc = self.make_credit_card()
        self.assertEqual(cc.notes, '')

    def test_update_status(self):
        cc = self.make_credit_card()
        cc.status = 'Suspended'
        cc.save()
        cc.refresh_from_db()
        self.assertEqual(cc.status, 'Suspended')

    def test_delete(self):
        cc = self.make_credit_card()
        cc_id = cc.id
        cc.delete()
        self.assertFalse(CreditCard.objects.filter(id=cc_id).exists())


# ─── EmployeePurchase ────────────────────────────────────────────────────

class EmployeePurchaseTest(SDTATestCase):

    def test_create(self):
        employee = self.make_user(email='purchase_emp@acme.com')
        cc = self.make_credit_card(employee=employee)
        purchase = EmployeePurchase.objects.create(
            credit_card=cc,
            employee=employee,
            amount='99.99',
            purchase_date=date.today(),
            description='Gas for van',
        )
        self.assertEqual(float(purchase.amount), 99.99)
        self.assertEqual(purchase.category, 'Other')
        self.assertEqual(purchase.status, 'Pending')

    def test_str(self):
        employee = self.make_user(email='purchase_str@acme.com')
        cc = self.make_credit_card(employee=employee)
        purchase = EmployeePurchase.objects.create(
            credit_card=cc,
            employee=employee,
            amount='50.00',
            purchase_date=date.today(),
            description='Str Purchase',
        )
        result = str(purchase)
        self.assertIn('50', result)

    def test_category_choices(self):
        employee = self.make_user(email='purchase_cat@acme.com')
        cc = self.make_credit_card(employee=employee)
        for category in ('Fuel', 'Parts', 'Tools', 'Travel', 'Other'):
            purchase = EmployeePurchase.objects.create(
                credit_card=cc,
                employee=employee,
                amount='10.00',
                purchase_date=date.today(),
                description=f'Cat {category}',
                category=category,
            )
            purchase.refresh_from_db()
            self.assertEqual(purchase.category, category)
            purchase.delete()

    def test_status_choices(self):
        employee = self.make_user(email='purchase_status@acme.com')
        cc = self.make_credit_card(employee=employee)
        for status in ('Pending', 'Approved', 'Rejected'):
            purchase = EmployeePurchase.objects.create(
                credit_card=cc,
                employee=employee,
                amount='25.00',
                purchase_date=date.today(),
                description=f'Status {status}',
                status=status,
            )
            purchase.refresh_from_db()
            self.assertEqual(purchase.status, status)
            purchase.delete()

    def test_receipt_document_optional(self):
        employee = self.make_user(email='purchase_no_receipt@acme.com')
        cc = self.make_credit_card(employee=employee)
        purchase = EmployeePurchase.objects.create(
            credit_card=cc,
            employee=employee,
            amount='15.00',
            purchase_date=date.today(),
            description='No Receipt',
        )
        self.assertIsNone(purchase.receipt_document)

    def test_notes_optional(self):
        employee = self.make_user(email='purchase_no_notes@acme.com')
        cc = self.make_credit_card(employee=employee)
        purchase = EmployeePurchase.objects.create(
            credit_card=cc,
            employee=employee,
            amount='30.00',
            purchase_date=date.today(),
            description='No Notes',
        )
        self.assertEqual(purchase.notes, '')

    def test_update_status(self):
        employee = self.make_user(email='purchase_upd@acme.com')
        cc = self.make_credit_card(employee=employee)
        purchase = EmployeePurchase.objects.create(
            credit_card=cc,
            employee=employee,
            amount='45.00',
            purchase_date=date.today(),
            description='Update Status',
        )
        purchase.status = 'Approved'
        purchase.save()
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, 'Approved')

    def test_delete(self):
        employee = self.make_user(email='purchase_del@acme.com')
        cc = self.make_credit_card(employee=employee)
        purchase = EmployeePurchase.objects.create(
            credit_card=cc,
            employee=employee,
            amount='20.00',
            purchase_date=date.today(),
            description='Delete',
        )
        purchase_id = purchase.id
        purchase.delete()
        self.assertFalse(EmployeePurchase.objects.filter(id=purchase_id).exists())
