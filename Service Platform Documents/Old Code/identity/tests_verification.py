from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class LastAdminSafetyTest(TestCase):
    
    def setUp(self):
        # Create one admin
        self.admin = User.objects.create_superuser(username='admin', password='password')
        
    def test_delete_last_admin_fails(self):
        """Deleting the only admin should fail."""
        with self.assertRaisesMessage(ValidationError, "Cannot delete the last administrator."):
             self.admin.delete()
             
    def test_deactivate_last_admin_fails(self):
        """Deactivating the only admin should fail."""
        self.admin.is_active = False
        with self.assertRaisesMessage(ValidationError, "Cannot deactivate or demote the last administrator."):
            self.admin.save()
            
    def test_demote_last_admin_fails(self):
        """Demoting the only admin should fail."""
        self.admin.is_superuser = False
        with self.assertRaisesMessage(ValidationError, "Cannot deactivate or demote the last administrator."):
            self.admin.save()
            
    def test_delete_admin_succeeds_if_another_exists(self):
        """Deleting an admin should work if another exists."""
        User.objects.create_superuser(username='admin2', password='password')
        try:
            self.admin.delete() # Should succeed
        except ValidationError:
            self.fail("Should be able to delete admin if backup exists.")
