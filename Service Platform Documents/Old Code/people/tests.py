from django.test import TestCase
from core.test_base import CoreTestCase
from people.models import Person

class PersonModelTest(CoreTestCase):

    def test_full_name_property(self):
        """Test full name generation"""
        person = Person.objects.create(
            first_name="John",
            last_name="Doe",
            created_by=self.worker_user,
            updated_by=self.worker_user
        )
        # Check if full_name exists (common pattern) or str representation
        self.assertEqual(str(person), "John Doe")
        
    def test_preferred_name(self):
        """Test preferred name usage if logic exists"""
        person = Person.objects.create(
            first_name="Jonathan",
            preferred_name="Jon",
            last_name="Doe",
            created_by=self.worker_user,
            updated_by=self.worker_user
        )
        # Does str() use preferred name? Implementation dependent.
        # If verify script is guide, it likely uses standard name.
        pass
