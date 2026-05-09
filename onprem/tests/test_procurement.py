# tests/test_procurement.py
# CRUD and basic functionality tests for all models in the procurement app.

from datetime import date
from tests.base import SDTATestCase
from procurement.models import (
    LotInfo, PurchaseOrder, PurchaseOrderLine, Receiving, RMA,
    Requisition, RequisitionLine, Vendor, VendorBill,
)


# ─── Vendor ───────────────────────────────────────────────────────────────────

class VendorTest(SDTATestCase):

    def test_create(self):
        v = Vendor.objects.create(name='Acme Supplies')
        self.assertEqual(v.name, 'Acme Supplies')
        self.assertEqual(v.status, 'Active')

    def test_str(self):
        v = Vendor.objects.create(name='Str Vendor', vendor_number='V-001')
        self.assertIn('V-001', str(v))
        self.assertIn('Str Vendor', str(v))

    def test_update_status(self):
        v = Vendor.objects.create(name='Old Vendor')
        v.status = 'Inactive'
        v.save()
        v.refresh_from_db()
        self.assertEqual(v.status, 'Inactive')

    def test_tags_default_empty(self):
        v = Vendor.objects.create(name='Tag Vendor')
        self.assertEqual(v.tags, [])

    def test_delete(self):
        v = Vendor.objects.create(name='Del Vendor')
        v_id = v.id
        v.delete()
        self.assertFalse(Vendor.objects.filter(id=v_id).exists())


# ─── PurchaseOrder ────────────────────────────────────────────────────────────

class PurchaseOrderTest(SDTATestCase):

    def test_create(self):
        vendor = self.make_vendor()
        po = PurchaseOrder.objects.create(vendor=vendor)
        self.assertEqual(po.status, 'Draft')
        self.assertEqual(po.vendor, vendor)

    def test_str(self):
        vendor = self.make_vendor()
        po = PurchaseOrder.objects.create(vendor=vendor, po_number='PO-001')
        result = str(po)
        self.assertIn('PO-001', result)

    def test_update_status(self):
        vendor = self.make_vendor()
        po = PurchaseOrder.objects.create(vendor=vendor)
        po.status = 'Ordered'
        po.save()
        po.refresh_from_db()
        self.assertEqual(po.status, 'Ordered')

    def test_totals_default_zero(self):
        vendor = self.make_vendor()
        po = PurchaseOrder.objects.create(vendor=vendor)
        self.assertEqual(float(po.subtotal), 0.0)
        self.assertEqual(float(po.total), 0.0)

    def test_delete(self):
        vendor = self.make_vendor()
        po = PurchaseOrder.objects.create(vendor=vendor)
        po_id = po.id
        po.delete()
        self.assertFalse(PurchaseOrder.objects.filter(id=po_id).exists())


# ─── PurchaseOrderLine ────────────────────────────────────────────────────────

class PurchaseOrderLineTest(SDTATestCase):

    def test_create(self):
        vendor = self.make_vendor()
        po = self.make_purchase_order(vendor=vendor)
        product = self.make_product(name='POL Product')
        line = PurchaseOrderLine.objects.create(
            purchase_order=po, product=product,
            quantity_ordered=10, unit_cost='5.00',
        )
        self.assertEqual(float(line.quantity_ordered), 10.0)
        self.assertEqual(float(line.quantity_received), 0.0)

    def test_str(self):
        vendor = self.make_vendor()
        po = PurchaseOrder.objects.create(vendor=vendor, po_number='PO-STR')
        product = self.make_product(name='POL Str Product')
        line = PurchaseOrderLine.objects.create(
            purchase_order=po, product=product,
            quantity_ordered=1, unit_cost='1.00',
        )
        result = str(line)
        self.assertIn('POL Str Product', result)

    def test_update_received_qty(self):
        vendor = self.make_vendor()
        po = self.make_purchase_order(vendor=vendor)
        product = self.make_product(name='POL Recv Product')
        line = PurchaseOrderLine.objects.create(
            purchase_order=po, product=product,
            quantity_ordered=20, unit_cost='2.00',
        )
        line.quantity_received = 10
        line.save()
        line.refresh_from_db()
        self.assertEqual(float(line.quantity_received), 10.0)

    def test_delete(self):
        vendor = self.make_vendor()
        po = self.make_purchase_order(vendor=vendor)
        product = self.make_product(name='POL Del Product')
        line = PurchaseOrderLine.objects.create(
            purchase_order=po, product=product,
            quantity_ordered=1, unit_cost='1.00',
        )
        line_id = line.id
        line.delete()
        self.assertFalse(PurchaseOrderLine.objects.filter(id=line_id).exists())


# ─── Receiving ────────────────────────────────────────────────────────────────

class ReceivingTest(SDTATestCase):

    def test_create(self):
        vendor = self.make_vendor()
        po = self.make_purchase_order(vendor=vendor)
        product = self.make_product(name='Recv Product')
        line = PurchaseOrderLine.objects.create(
            purchase_order=po, product=product,
            quantity_ordered=10, unit_cost='5.00',
        )
        recv = Receiving.objects.create(
            purchase_order=po,
            po_line=line,
            product=product,
            quantity_received=5,
            received_date=date.today(),
        )
        self.assertEqual(float(recv.quantity_received), 5.0)

    def test_str(self):
        vendor = self.make_vendor()
        po = self.make_purchase_order(vendor=vendor)
        product = self.make_product(name='Recv Str Product')
        line = PurchaseOrderLine.objects.create(
            purchase_order=po, product=product,
            quantity_ordered=10, unit_cost='1.00',
        )
        recv = Receiving.objects.create(
            purchase_order=po, po_line=line, product=product,
            quantity_received=3, received_date=date.today(),
        )
        result = str(recv)
        self.assertIn('Recv Str Product', result)
        self.assertIn('3', result)

    def test_delete(self):
        vendor = self.make_vendor()
        po = self.make_purchase_order(vendor=vendor)
        product = self.make_product(name='Del Recv Product')
        line = PurchaseOrderLine.objects.create(
            purchase_order=po, product=product,
            quantity_ordered=5, unit_cost='1.00',
        )
        recv = Receiving.objects.create(
            purchase_order=po, po_line=line, product=product,
            quantity_received=2, received_date=date.today(),
        )
        recv_id = recv.id
        recv.delete()
        self.assertFalse(Receiving.objects.filter(id=recv_id).exists())


# ─── LotInfo ──────────────────────────────────────────────────────────────────

class LotInfoTest(SDTATestCase):

    def _make_receiving(self):
        vendor = self.make_vendor()
        po = self.make_purchase_order(vendor=vendor)
        product = self.make_product(name=f'Lot Product')
        line = PurchaseOrderLine.objects.create(
            purchase_order=po, product=product,
            quantity_ordered=100, unit_cost='1.00',
        )
        return Receiving.objects.create(
            purchase_order=po, po_line=line, product=product,
            quantity_received=50, received_date=date.today(),
        ), product

    def test_create(self):
        recv, product = self._make_receiving()
        lot = LotInfo.objects.create(
            receiving=recv, product=product,
            lot_number='LOT-001', quantity=50,
        )
        self.assertEqual(lot.lot_number, 'LOT-001')

    def test_str(self):
        recv, product = self._make_receiving()
        lot = LotInfo.objects.create(
            receiving=recv, product=product,
            lot_number='LOT-STR', quantity=10,
        )
        self.assertIn('LOT-STR', str(lot))

    def test_expiration_optional(self):
        recv, product = self._make_receiving()
        lot = LotInfo.objects.create(
            receiving=recv, product=product,
            lot_number='LOT-NO-EXP', quantity=10,
        )
        self.assertIsNone(lot.expiration_date)

    def test_delete(self):
        recv, product = self._make_receiving()
        lot = LotInfo.objects.create(
            receiving=recv, product=product,
            lot_number='LOT-DEL', quantity=5,
        )
        lot_id = lot.id
        lot.delete()
        self.assertFalse(LotInfo.objects.filter(id=lot_id).exists())


# ─── VendorBill ───────────────────────────────────────────────────────────────

class VendorBillTest(SDTATestCase):

    def test_create(self):
        vendor = self.make_vendor()
        bill = VendorBill.objects.create(vendor=vendor)
        self.assertEqual(bill.status, 'Draft')
        self.assertEqual(float(bill.total), 0.0)

    def test_str(self):
        vendor = self.make_vendor()
        bill = VendorBill.objects.create(vendor=vendor, bill_number='BILL-001')
        self.assertIn('BILL-001', str(bill))

    def test_update_status(self):
        vendor = self.make_vendor()
        bill = VendorBill.objects.create(vendor=vendor)
        bill.status = 'Approved'
        bill.save()
        bill.refresh_from_db()
        self.assertEqual(bill.status, 'Approved')

    def test_delete(self):
        vendor = self.make_vendor()
        bill = VendorBill.objects.create(vendor=vendor)
        bill_id = bill.id
        bill.delete()
        self.assertFalse(VendorBill.objects.filter(id=bill_id).exists())


# ─── Requisition ──────────────────────────────────────────────────────────────

class RequisitionTest(SDTATestCase):

    def test_create(self):
        req = Requisition.objects.create()
        self.assertEqual(req.status, 'Draft')

    def test_str(self):
        req = Requisition.objects.create(requisition_number='REQ-001')
        result = str(req)
        self.assertIn('REQ-001', result)
        self.assertIn('Draft', result)

    def test_update_status(self):
        req = Requisition.objects.create()
        req.status = 'Approved'
        req.save()
        req.refresh_from_db()
        self.assertEqual(req.status, 'Approved')

    def test_delete(self):
        req = Requisition.objects.create()
        req_id = req.id
        req.delete()
        self.assertFalse(Requisition.objects.filter(id=req_id).exists())


# ─── RequisitionLine ──────────────────────────────────────────────────────────

class RequisitionLineTest(SDTATestCase):

    def test_create(self):
        req = Requisition.objects.create()
        product = self.make_product(name='Req Line Product')
        line = RequisitionLine.objects.create(
            requisition=req, product=product, quantity_requested=5,
        )
        self.assertEqual(float(line.quantity_requested), 5.0)

    def test_str(self):
        req = Requisition.objects.create(requisition_number='RL-STR')
        product = self.make_product(name='RL Str Product')
        line = RequisitionLine.objects.create(
            requisition=req, product=product, quantity_requested=3,
        )
        result = str(line)
        self.assertIn('RL Str Product', result)

    def test_delete(self):
        req = Requisition.objects.create()
        product = self.make_product(name='RL Del Product')
        line = RequisitionLine.objects.create(
            requisition=req, product=product, quantity_requested=1,
        )
        line_id = line.id
        line.delete()
        self.assertFalse(RequisitionLine.objects.filter(id=line_id).exists())


# ─── RMA ──────────────────────────────────────────────────────────────────

class RMATest(SDTATestCase):

    def test_create(self):
        product = self.make_product(name='RMA Product')
        vendor = self.make_vendor(name='RMA Vendor')
        rma = RMA.objects.create(product=product, vendor=vendor)
        self.assertEqual(rma.product, product)
        self.assertEqual(rma.vendor, vendor)
        self.assertEqual(rma.status, 'Initiated')
        self.assertEqual(rma.reason, 'Other')

    def test_str(self):
        product = self.make_product(name='Str RMA Product')
        vendor = self.make_vendor()
        rma = RMA.objects.create(
            product=product, vendor=vendor, rma_number='RMA-001'
        )
        result = str(rma)
        self.assertIn('RMA-001', result)
        self.assertIn('Str RMA Product', result)

    def test_status_choices(self):
        product = self.make_product()
        vendor = self.make_vendor()
        for status in ('Initiated', 'Shipped', 'Received by Vendor', 'Credited', 'Closed', 'Denied'):
            rma = RMA.objects.create(product=product, vendor=vendor, status=status)
            rma.refresh_from_db()
            self.assertEqual(rma.status, status)
            rma.delete()

    def test_reason_choices(self):
        product = self.make_product()
        vendor = self.make_vendor()
        for reason in ('Defective', 'Wrong Item', 'Damaged', 'Overstock', 'Other'):
            rma = RMA.objects.create(product=product, vendor=vendor, reason=reason)
            rma.refresh_from_db()
            self.assertEqual(rma.reason, reason)
            rma.delete()

    def test_po_line_optional(self):
        rma = self.make_rma()
        self.assertIsNone(rma.po_line)

    def test_quantity_default_one(self):
        rma = self.make_rma()
        self.assertEqual(float(rma.quantity), 1.0)

    def test_quantity_set(self):
        product = self.make_product()
        vendor = self.make_vendor()
        rma = RMA.objects.create(product=product, vendor=vendor, quantity=5)
        rma.refresh_from_db()
        self.assertEqual(float(rma.quantity), 5.0)

    def test_credit_amount_default_zero(self):
        rma = self.make_rma()
        self.assertEqual(float(rma.credit_amount), 0.0)

    def test_credit_amount_set(self):
        product = self.make_product()
        vendor = self.make_vendor()
        rma = RMA.objects.create(product=product, vendor=vendor, credit_amount='150.00')
        rma.refresh_from_db()
        self.assertEqual(float(rma.credit_amount), 150.0)

    def test_notes_optional(self):
        rma = self.make_rma()
        self.assertEqual(rma.notes, '')

    def test_notes_set(self):
        product = self.make_product()
        vendor = self.make_vendor()
        rma = RMA.objects.create(
            product=product, vendor=vendor, notes='Defective unit'
        )
        rma.refresh_from_db()
        self.assertEqual(rma.notes, 'Defective unit')

    def test_update_status(self):
        rma = self.make_rma()
        rma.status = 'Shipped'
        rma.save()
        rma.refresh_from_db()
        self.assertEqual(rma.status, 'Shipped')

    def test_delete(self):
        rma = self.make_rma()
        rma_id = rma.id
        rma.delete()
        self.assertFalse(RMA.objects.filter(id=rma_id).exists())
