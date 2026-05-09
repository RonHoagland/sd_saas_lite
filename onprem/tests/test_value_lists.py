# tests/test_value_lists.py
# Tests for the value_lists app: ValueList, ValueListItem.

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from tests.base import SDTATestCase
from value_lists.models import ValueList, ValueListItem


# ═══════════════════════════════════════════════════════════════════════════════
# ValueList tests
# ═══════════════════════════════════════════════════════════════════════════════

class ValueListTest(SDTATestCase):

    def test_create(self):
        vl = self.make_value_list(name='Lead Sources', slug='lead_source')
        self.assertEqual(vl.name, 'Lead Sources')
        self.assertEqual(vl.slug, 'lead_source')
        self.assertFalse(vl.is_system)

    def test_str(self):
        vl = self.make_value_list(name='Lead Sources', slug='lead_source')
        self.assertEqual(str(vl), 'Lead Sources')

    def test_create_system_list(self):
        vl = self.make_value_list(name='Payment Methods', slug='payment_method', is_system=True)
        self.assertTrue(vl.is_system)

    def test_read(self):
        vl = self.make_value_list(name='WO Types', slug='wo_type')
        fetched = ValueList.objects.get(pk=vl.pk)
        self.assertEqual(fetched.name, 'WO Types')

    def test_update(self):
        vl = self.make_value_list(name='Old Name', slug='old_name')
        vl.name = 'New Name'
        vl.save()
        vl.refresh_from_db()
        self.assertEqual(vl.name, 'New Name')

    def test_delete_custom(self):
        vl = self.make_value_list(name='Custom List', slug='custom')
        pk = vl.pk
        vl.delete()
        self.assertFalse(ValueList.objects.filter(pk=pk).exists())

    def test_delete_system_raises(self):
        vl = self.make_value_list(name='System List', slug='system', is_system=True)
        with self.assertRaises(ValidationError):
            vl.delete()

    def test_unique_slug_per_tenant(self):
        self.make_value_list(name='List A', slug='unique_slug')
        with self.assertRaises(IntegrityError):
            self.make_value_list(name='List B', slug='unique_slug')

    def test_tenant_isolation(self):
        vl = self.make_value_list(name='Tenant List', slug='tenant_list')
        self.assertEqual(vl.tenant_id, self.tenant_id)


# ═══════════════════════════════════════════════════════════════════════════════
# ValueListItem tests
# ═══════════════════════════════════════════════════════════════════════════════

class ValueListItemTest(SDTATestCase):

    def test_create(self):
        vl = self.make_value_list(name='Lead Sources', slug='lead_source')
        item = self.make_value_list_item(value_list=vl, label='Referral', value='referral')
        self.assertEqual(item.label, 'Referral')
        self.assertEqual(item.value, 'referral')
        self.assertEqual(item.value_list, vl)
        self.assertTrue(item.is_active)
        self.assertFalse(item.is_default)

    def test_str(self):
        vl = self.make_value_list(name='Sources', slug='sources')
        item = self.make_value_list_item(value_list=vl, label='Web Search', value='web_search')
        self.assertEqual(str(item), 'Web Search (web_search)')

    def test_read(self):
        item = self.make_value_list_item(label='Test Item', value='test_item')
        fetched = ValueListItem.objects.get(pk=item.pk)
        self.assertEqual(fetched.label, 'Test Item')

    def test_update(self):
        item = self.make_value_list_item(label='Old Label', value='old')
        item.label = 'New Label'
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.label, 'New Label')

    def test_delete(self):
        item = self.make_value_list_item(label='Delete Me', value='delete_me')
        pk = item.pk
        item.delete()
        self.assertFalse(ValueListItem.objects.filter(pk=pk).exists())

    def test_deactivate(self):
        item = self.make_value_list_item(label='Deactivate', value='deactivate')
        item.is_active = False
        item.save()
        item.refresh_from_db()
        self.assertFalse(item.is_active)

    def test_sort_order(self):
        vl = self.make_value_list(name='Ordered', slug='ordered')
        item3 = self.make_value_list_item(value_list=vl, label='C', value='c', sort_order=3)
        item1 = self.make_value_list_item(value_list=vl, label='A', value='a', sort_order=1)
        item2 = self.make_value_list_item(value_list=vl, label='B', value='b', sort_order=2)
        items = list(vl.items.all())
        self.assertEqual(items[0].pk, item1.pk)
        self.assertEqual(items[1].pk, item2.pk)
        self.assertEqual(items[2].pk, item3.pk)

    def test_unique_value_per_list(self):
        vl = self.make_value_list(name='Unique Test', slug='unique_test')
        self.make_value_list_item(value_list=vl, label='First', value='same_value')
        with self.assertRaises(IntegrityError):
            self.make_value_list_item(value_list=vl, label='Second', value='same_value')

    def test_same_value_different_lists(self):
        vl1 = self.make_value_list(name='List 1', slug='list_1')
        vl2 = self.make_value_list(name='List 2', slug='list_2')
        item1 = self.make_value_list_item(value_list=vl1, label='Same', value='shared')
        item2 = self.make_value_list_item(value_list=vl2, label='Same', value='shared')
        self.assertNotEqual(item1.pk, item2.pk)

    def test_default_validation(self):
        vl = self.make_value_list(name='Default Test', slug='default_test')
        self.make_value_list_item(value_list=vl, label='Default', value='default', is_default=True)
        with self.assertRaises(ValidationError):
            self.make_value_list_item(value_list=vl, label='Also Default', value='also', is_default=True)

    def test_cascade_delete(self):
        vl = self.make_value_list(name='Cascade', slug='cascade')
        vl_id = vl.id
        self.make_value_list_item(value_list=vl, label='Item', value='item')
        self.assertEqual(ValueListItem.objects.filter(value_list=vl).count(), 1)
        vl.delete()
        self.assertEqual(ValueListItem.objects.filter(value_list_id=vl_id).count(), 0)

    def test_is_default_flag(self):
        vl = self.make_value_list(name='Defaults', slug='defaults')
        item = self.make_value_list_item(value_list=vl, label='The Default', value='the_default', is_default=True)
        self.assertTrue(item.is_default)

    def test_reverse_relation(self):
        vl = self.make_value_list(name='Reverse', slug='reverse')
        self.make_value_list_item(value_list=vl, label='A', value='a')
        self.make_value_list_item(value_list=vl, label='B', value='b')
        self.assertEqual(vl.items.count(), 2)
