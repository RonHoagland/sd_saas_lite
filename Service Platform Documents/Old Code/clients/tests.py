from django.test import TestCase
from django.utils import timezone
from core.test_base import CoreTestCase
from clients.models import Client
from numbering.models import NumberingRule, NumberSequence
from value_lists.models import ValueList, ValueItem

class ClientModelTest(CoreTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        
        # Setup Value Lists
        cls.status_list = cls.create_value_list('Client Status', 'client_status', ['Active', 'Inactive'])
        cls.type_list = cls.create_value_list('Client Type', 'client_type', ['Commercial', 'Residential'])
        
        # Setup Numbering Rule
        cls.rule = NumberingRule.objects.create(
            entity_type='clients',
            prefix='AC',
            include_year=True,
            year_format='YY', # Force 2-digit year to match ACYYNNN (9 chars)
            sequence_length=3,
            created_by=cls.admin_user,
            updated_by=cls.admin_user
        )
        NumberSequence.objects.create(rule=cls.rule, current_value=0)

    def test_client_instantiation_account_number(self):
        """Test that account number is generated on instantiation (init)"""
        client = Client(
            name="Test Client Init",
            client_type="Commercial",
            created_by=self.worker_user,
            updated_by=self.worker_user
        )
        # Should have a temp or real number? 
        # Implementation Plan says "Generated at Instantiation". 
        # If it calls numbering engine, it might consume a number immediately.
        # Let's verify it HAS a number.
        self.assertTrue(client.account_number.startswith('AC-'))
        self.assertEqual(len(client.account_number), 9) # AC-26-001 = 9 chars

    def test_client_defaults(self):
        """Test default values for date_started and status"""
        client = Client.objects.create(
            name="Defaults Client",
            client_type="Residential",
            created_by=self.worker_user,
            updated_by=self.worker_user
        )
        client.refresh_from_db() # Ensure we get Date (not DateTime from defaults)
        self.assertEqual(client.status, 'Active')
        self.assertEqual(client.date_started, timezone.now().date())
        
    def test_account_number_uniqueness(self):
        """Test that sequential clients get unique numbers"""
        c1 = Client.objects.create(name="C1", client_type="Commercial", created_by=self.worker_user, updated_by=self.worker_user)
        c2 = Client.objects.create(name="C2", client_type="Commercial", created_by=self.worker_user, updated_by=self.worker_user)
        
        self.assertNotEqual(c1.account_number, c2.account_number)
        # Assuming sequential:
        # If C1 is ...001, C2 should be ...002. 
        # Note: 'test_client_instantiation_account_number' might have consumed 001 if not saved? 
        # Wait, if generated on __init__ and NOT saved, is the number lost? 
        # If so, C1 might be 002. We just check flow.
        n1 = int(c1.account_number.split('-')[-1])
        n2 = int(c2.account_number.split('-')[-1])
        self.assertTrue(n2 > n1)

    def test_invalid_dates(self):
        """Edge Case: Future date started?"""
        # Implementation doesn't strictly forbid verification plan says "Verify". 
        # If it allows it, test passes. If it blocks, update test.
        future_date = timezone.now().date() + timezone.timedelta(days=365)
        client = Client.objects.create(
            name="Future Client",
            client_type="Commercial",
            date_started=future_date,
            created_by=self.worker_user,
            updated_by=self.worker_user
        )
        self.assertEqual(client.date_started, future_date)

