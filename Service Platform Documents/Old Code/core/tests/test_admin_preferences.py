from django.urls import reverse
from core.test_base import CoreTestCase
from core.models import Preference

class PreferenceAdminUITest(CoreTestCase):
    
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Create a test preference
        cls.pref = Preference.objects.create(
            key='test.ui_pref',
            name='UI Test Preference',
            value='Old Value',
            data_type='string',
            created_by=cls.admin_user,
            updated_by=cls.admin_user
        )

    def test_access_control(self):
        """Worker should not access preferences."""
        self.client.force_login(self.worker_user)
        response = self.client.get(reverse('preference_list'))
        # Should redirect to login or returned 403 depending on configuration.
        # user_passes_test usually redirects to login if false.
        self.assertNotEqual(response.status_code, 200) 
        
    def test_admin_access_list(self):
        """Admin should see the list."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('preference_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'UI Test Preference')

    def test_admin_update_preference(self):
        """Admin can update a preference via UI."""
        self.client.force_login(self.admin_user)
        url = reverse('preference_update', args=[self.pref.id])
        
        # GET form
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # POST update
        response = self.client.post(url, {'value': 'New Value'})
        self.assertEqual(response.status_code, 302) # Redirects on success
        
        self.pref.refresh_from_db()
        self.assertEqual(self.pref.value, 'New Value')

    def test_locked_preference(self):
        """Locked preference should return 403 on update attempt."""
        locked_pref = Preference.objects.create(
            key='locked.pref', name='Locked', value='X', is_editable=False,
            created_by=self.admin_user, updated_by=self.admin_user
        )
        self.client.force_login(self.admin_user)
        url = reverse('preference_update', args=[locked_pref.id])
        
        response = self.client.post(url, {'value': 'Y'})
        self.assertEqual(response.status_code, 403)
