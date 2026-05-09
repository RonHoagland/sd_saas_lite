from django.test import TestCase
from core.test_base import CoreTestCase
from value_lists.models import ValueList, ValueItem

class ValueListModelTest(CoreTestCase):

    def test_value_list_creation(self):
        """Test creating a value list and items"""
        vl = ValueList.objects.create(
            name="Test List",
            slug="test.list"
            # No audit fields
        )
        item1 = ValueItem.objects.create(
            value_list=vl,
            value="Item 1"
            # No audit fields
        )
        item2 = ValueItem.objects.create(
            value_list=vl,
            value="Item 2",
            sort_order=2
            # No audit fields
        )
        
        self.assertEqual(vl.items.count(), 2)
        self.assertEqual(str(item1), "Item 1")
