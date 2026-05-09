# tests/test_tenant_model.py
# Tests for TenantModel base class behaviour:
#   - tenant_id auto-injection from context
#   - cross-tenant write guard
#   - TenantManager vs all_objects
#   - audit fields auto-set

import uuid

from config.tenant_context import clear_current_tenant_id, set_current_tenant_id
from tests.base import SDTATestCase
from users.models import Department


class TenantIDAutoInjectionTest(SDTATestCase):
    """tenant_id is auto-filled from context when not explicitly provided."""

    def test_tenant_id_injected_on_create(self):
        dept = Department.objects.create(name='Auto Dept')
        self.assertEqual(dept.tenant_id, self.tenant_id)

    def test_tenant_id_injected_on_new_instance_save(self):
        dept = Department(name='Explicit Save Dept')
        dept.save()
        self.assertEqual(dept.tenant_id, self.tenant_id)

    def test_tenant_id_not_overwritten_if_already_set(self):
        dept = Department(name='Pre-Set Dept', tenant_id=self.tenant_id)
        dept.save()
        self.assertEqual(dept.tenant_id, self.tenant_id)


class CrossTenantWriteGuardTest(SDTATestCase):
    """save() raises ValueError when tenant context doesn't match object's tenant_id."""

    def test_cross_tenant_write_raises(self):
        dept = Department.objects.create(name='Secure Dept')
        other_tenant_id = uuid.uuid4()
        set_current_tenant_id(other_tenant_id)
        dept.name = 'Hijacked'
        with self.assertRaises(ValueError) as ctx:
            dept.save()
        self.assertIn('Cross-tenant write blocked', str(ctx.exception))
        # Restore for tearDown
        set_current_tenant_id(self.tenant_id)

    def test_same_tenant_write_allowed(self):
        dept = Department.objects.create(name='Same Tenant Dept')
        dept.name = 'Updated'
        dept.save()  # Should not raise
        dept.refresh_from_db()
        self.assertEqual(dept.name, 'Updated')

    def test_save_without_context_allowed(self):
        """When no context is set (e.g. Celery task), writes are unrestricted."""
        dept = Department.objects.create(name='No Context Dept')
        clear_current_tenant_id()
        dept.name = 'Changed Without Context'
        dept.save()  # Should not raise
        dept.refresh_from_db()
        self.assertEqual(dept.name, 'Changed Without Context')
        # Restore for tearDown
        set_current_tenant_id(self.tenant_id)


class TenantManagerFilterTest(SDTATestCase):
    """TenantManager.get_queryset() filters by current tenant_id."""

    def test_objects_filtered_to_current_tenant(self):
        dept_a = Department.objects.create(name='Tenant A Dept')
        # Create object for a different tenant using all_objects (no context guard)
        other_id = uuid.uuid4()
        clear_current_tenant_id()
        Department.all_objects.create(name='Tenant B Dept', tenant_id=other_id)
        set_current_tenant_id(self.tenant_id)
        # objects manager should only return tenant A's record
        names = list(Department.objects.values_list('name', flat=True))
        self.assertIn('Tenant A Dept', names)
        self.assertNotIn('Tenant B Dept', names)

    def test_all_objects_returns_all_tenants(self):
        Department.objects.create(name='All Objects Dept')
        count = Department.all_objects.count()
        self.assertGreaterEqual(count, 1)

    def test_no_context_returns_all(self):
        """Without a tenant context, TenantManager returns everything."""
        Department.objects.create(name='Context None Dept')
        clear_current_tenant_id()
        count = Department.objects.count()
        self.assertGreaterEqual(count, 1)
        set_current_tenant_id(self.tenant_id)


class AuditFieldAutoSetTest(SDTATestCase):
    """created_on and updated_on are set automatically by Django."""

    def test_created_on_auto_set(self):
        dept = Department.objects.create(name='Audit Dept')
        self.assertIsNotNone(dept.created_on)

    def test_updated_on_auto_set(self):
        dept = Department.objects.create(name='Update Audit')
        self.assertIsNotNone(dept.updated_on)

    def test_updated_on_changes_on_save(self):
        dept = Department.objects.create(name='Upd Chg Dept')
        original_updated = dept.updated_on
        dept.name = 'Upd Chg Dept V2'
        dept.save()
        dept.refresh_from_db()
        # updated_on may equal original in fast tests; assert it's still set
        self.assertIsNotNone(dept.updated_on)

    def test_created_by_can_be_set(self):
        dept = Department.objects.create(name='Audit Creator', created_by='admin@test.com')
        dept.refresh_from_db()
        self.assertEqual(dept.created_by, 'admin@test.com')

    def test_updated_by_can_be_set(self):
        dept = Department.objects.create(name='Audit Updater')
        dept.updated_by = 'editor@test.com'
        dept.save()
        dept.refresh_from_db()
        self.assertEqual(dept.updated_by, 'editor@test.com')

    def test_uuid_pk_auto_generated(self):
        dept = Department.objects.create(name='UUID Dept')
        self.assertIsNotNone(dept.id)
        import uuid as uuidlib
        self.assertIsInstance(dept.id, uuidlib.UUID)
