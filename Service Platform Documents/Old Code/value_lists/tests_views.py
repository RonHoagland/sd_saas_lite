from django.urls import reverse
from core.test_base import CoreTestCase
from value_lists.models import ValueList, ValueItem

class ValueListAdminUITest(CoreTestCase):

    def test_crud_workflow(self):
        """Test full CRUD workflow via UI."""
        self.client.force_login(self.admin_user)
        
        # 1. Create List
        create_url = reverse('value_list_create')
        response = self.client.post(create_url, {
            'name': 'UI Test List',
            'description': 'Created via Test'
        })
        self.assertRedirects(response, reverse('value_list_list'))
        
        vl = ValueList.objects.get(name='UI Test List')
        self.assertEqual(vl.slug, 'ui-test-list')
        
        # 2. Add Item
        add_item_url = reverse('value_item_create', kwargs={'slug': vl.slug})
        response = self.client.post(add_item_url, {
            'value': 'Option A',
            'sort_order': 1,
            'is_active': True
        })
        self.assertRedirects(response, reverse('value_list_detail', kwargs={'slug': vl.slug}))
        self.assertEqual(vl.items.count(), 1)
        
        # 3. Update Item
        item = vl.items.first()
        update_item_url = reverse('value_item_update', kwargs={'slug': vl.slug, 'pk': item.id})
        response = self.client.post(update_item_url, {
            'value': 'Option A Changed',
            'sort_order': 2,
            'is_active': True
        })
        item.refresh_from_db()
        self.assertEqual(item.value, 'Option A Changed')
        
        # 4. Delete Item
        delete_item_url = reverse('value_item_delete', kwargs={'slug': vl.slug, 'pk': item.id})
        response = self.client.post(delete_item_url) # method=POST to confirm
        self.assertEqual(vl.items.count(), 0)
        
        # 5. Delete List
        delete_list_url = reverse('value_list_delete', kwargs={'slug': vl.slug})
        response = self.client.post(delete_list_url)
        self.assertFalse(ValueList.objects.filter(name='UI Test List').exists())

    def test_access_denied_worker(self):
        """Worker cannot access Value Lists."""
        self.client.force_login(self.worker_user)
        response = self.client.get(reverse('value_list_list'))
        # AdminRequiredMixin -> AccessDenied/LoginRedirect
        self.assertNotEqual(response.status_code, 200)
