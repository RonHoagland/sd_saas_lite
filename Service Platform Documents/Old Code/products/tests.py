from django.test import TestCase
from core.test_base import CoreTestCase
from products.models import Product
from value_lists.models import ValueList, ValueItem
from audit.models import UserTransaction, Session

class ProductModelTest(CoreTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.status_list = cls.create_value_list('Product Status', 'product_status', ['Active', 'Discontinued'])
        cls.type_list = cls.create_value_list('Product Type', 'product_type', ['Part', 'Service'])

    def test_product_defaults(self):
        """Test default status is Active"""
        prod = Product.objects.create(
            name="Test Part",
            product_type="Part",
            sku="SKU-123",
            created_by=self.worker_user,
            updated_by=self.worker_user
        )
        self.assertEqual(prod.status, 'Active')
        self.assertEqual(prod.quantity_on_hand, 0) # Default 0?

    def test_qoh_audit(self):
        """Test changing QOH triggers audit"""
        # Create Session for worker user (required for audit)
        Session.objects.create(
            user=self.worker_user,
            auth_result='success',
            ip_address='127.0.0.1'
        )
        
        prod = Product.objects.create(
            name="Test Part Audit",
            product_type="Part",
            sku="SKU-AUDIT",
            quantity_on_hand=10,
            created_by=self.worker_user,
            updated_by=self.worker_user,
            # Explicitly set updated_by so signal fallback works if middleware fails
        )
        
        # Change QOH
        prod.quantity_on_hand = 15
        prod.updated_by = self.worker_user # Ensure user is set
        prod.save()
        
        # Verify Audit Log
        audit_exists = UserTransaction.objects.filter(
            entity_type="Product",
            event_type="update",
            entity_id=prod.id,
            user=self.worker_user
        ).exists()
        
        self.assertTrue(audit_exists, "Audit log for QOH update was not created.")
