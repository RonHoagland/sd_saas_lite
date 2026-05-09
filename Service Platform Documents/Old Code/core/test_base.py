from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command
from value_lists.models import ValueList, ValueItem

User = get_user_model()

class CoreTestCase(TestCase):
    """
    Base Test Case for Brixa Platform Core.
    Provides standardized setup for Users (Admin/Worker) and common utilities.
    """
    
    @classmethod
    def setUpTestData(cls):
        # Create Admin User (Superuser)
        cls.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='password123'
        )
        
        # Create Worker User (Standard)
        cls.worker_user = User.objects.create_user(
            username='worker_test',
            email='worker@test.com',
            password='password123'
        )

    @classmethod
    def create_value_list(cls, name, key, items=[]):
        """Helper to create a Value List with items."""
        # ValueList uses 'slug', not 'key'. No audit fields.
        vl = ValueList.objects.create(name=name, slug=key)
        for item_value in items:
            ValueItem.objects.create(
                value_list=vl,
                value=item_value,
                # ValueItem has no audit fields either
            )
        return vl
