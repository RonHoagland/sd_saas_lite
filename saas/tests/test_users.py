# tests/test_users.py
# CRUD and basic functionality tests for all models in the users app.

import uuid
from datetime import date, datetime, timezone

from django.test import TestCase

from tests.base import SDTATestCase
from users.models import (
    Department, EmployeePosition, EmployeePreference, EmployeeRole,
    EmployeeZone, LoginAttemptLog, Position, Role, RolePermission, SessionLog,
    TenantPreference, User,
)


# ─── Department ───────────────────────────────────────────────────────────────

class DepartmentTest(SDTATestCase):

    def test_create(self):
        dept = Department.objects.create(name='Engineering')
        self.assertIsNotNone(dept.id)
        self.assertEqual(dept.name, 'Engineering')
        self.assertEqual(dept.status, 'Active')
        self.assertEqual(dept.tenant_id, self.tenant_id)

    def test_str(self):
        dept = Department.objects.create(name='HR')
        self.assertEqual(str(dept), 'HR')

    def test_read(self):
        dept = Department.objects.create(name='Finance')
        fetched = Department.objects.get(id=dept.id)
        self.assertEqual(fetched.name, 'Finance')

    def test_update(self):
        dept = Department.objects.create(name='Ops')
        dept.name = 'Operations'
        dept.save()
        dept.refresh_from_db()
        self.assertEqual(dept.name, 'Operations')

    def test_delete(self):
        dept = Department.objects.create(name='Temp Dept')
        dept_id = dept.id
        dept.delete()
        self.assertFalse(Department.objects.filter(id=dept_id).exists())

    def test_status_choices(self):
        dept = Department.objects.create(name='Old Dept', status='Inactive')
        dept.refresh_from_db()
        self.assertEqual(dept.status, 'Inactive')

    def test_audit_fields(self):
        dept = Department.objects.create(name='Audit Dept')
        self.assertIsNotNone(dept.created_on)
        self.assertIsNotNone(dept.updated_on)


# ─── Position ─────────────────────────────────────────────────────────────────

class PositionTest(SDTATestCase):

    def test_create(self):
        dept = self.make_department()
        pos = Position.objects.create(department=dept, title='Lead Tech')
        self.assertIsNotNone(pos.id)
        self.assertEqual(pos.title, 'Lead Tech')
        self.assertEqual(pos.department, dept)

    def test_str(self):
        dept = self.make_department()
        pos = Position.objects.create(department=dept, title='Manager')
        self.assertEqual(str(pos), 'Manager')

    def test_read_and_fk(self):
        dept = self.make_department(name='Field Ops')
        pos = Position.objects.create(department=dept, title='Technician')
        fetched = Position.objects.get(id=pos.id)
        self.assertEqual(fetched.department.name, 'Field Ops')

    def test_update(self):
        dept = self.make_department()
        pos = Position.objects.create(department=dept, title='Junior Dev')
        pos.title = 'Senior Dev'
        pos.save()
        pos.refresh_from_db()
        self.assertEqual(pos.title, 'Senior Dev')

    def test_delete(self):
        dept = self.make_department()
        pos = Position.objects.create(department=dept, title='Temp Role')
        pos_id = pos.id
        pos.delete()
        self.assertFalse(Position.objects.filter(id=pos_id).exists())

    def test_description_blank(self):
        dept = self.make_department()
        pos = Position.objects.create(department=dept, title='No Desc')
        self.assertEqual(pos.description, '')


# ─── Role ─────────────────────────────────────────────────────────────────────

class RoleTest(SDTATestCase):

    def test_create(self):
        role = Role.objects.create(name='Admin')
        self.assertEqual(role.name, 'Admin')
        self.assertFalse(role.is_custom)

    def test_str(self):
        role = Role.objects.create(name='Viewer')
        self.assertEqual(str(role), 'Viewer')

    def test_custom_role(self):
        role = Role.objects.create(name='Custom Role', is_custom=True)
        role.refresh_from_db()
        self.assertTrue(role.is_custom)

    def test_update(self):
        role = Role.objects.create(name='Old Role')
        role.name = 'New Role'
        role.save()
        role.refresh_from_db()
        self.assertEqual(role.name, 'New Role')

    def test_delete(self):
        role = Role.objects.create(name='Temp Role')
        role_id = role.id
        role.delete()
        self.assertFalse(Role.objects.filter(id=role_id).exists())


# ─── User ─────────────────────────────────────────────────────────────────────

class UserTest(SDTATestCase):

    def test_create_via_manager(self):
        user = self.make_user(username='alice', email='alice@acme.com')
        self.assertEqual(user.username, 'alice')
        self.assertEqual(user.email, 'alice@acme.com')
        self.assertEqual(user.tenant_id, self.tenant_id)
        self.assertTrue(user.is_active)

    def test_create_user_requires_email(self):
        from users.models import User
        with self.assertRaises(ValueError) as ctx:
            User.objects.create_user(
                'noemail',
                tenant_id=self.tenant_id,
                password='TestPass123!',
                email='',
                person=self.make_person(),
            )
        self.assertIn('Email is required', str(ctx.exception))

    def test_username_must_not_contain_at(self):
        from users.models import User
        with self.assertRaises(ValueError) as ctx:
            User.objects.create_user(
                'bad@name',
                tenant_id=self.tenant_id,
                password='TestPass123!',
                email='ok@acme.com',
                person=self.make_person(),
            )
        self.assertIn('@', str(ctx.exception))

    def test_str(self):
        user = self.make_user(username='bob_acme', email='bob@acme.com')
        self.assertIn('bob_acme', str(user))

    def test_read(self):
        user = self.make_user(email='carol@acme.com')
        fetched = User.all_objects.get(id=user.id)
        self.assertEqual(fetched.email, 'carol@acme.com')

    def test_update_status(self):
        user = self.make_user(email='dave@acme.com')
        user.status = 'Inactive'
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.status, 'Inactive')

    def test_delete(self):
        user = self.make_user(email='eve@acme.com')
        user_id = user.id
        user.delete()
        self.assertFalse(User.all_objects.filter(id=user_id).exists())

    def test_password_hashed(self):
        user = self.make_user(email='frank@acme.com')
        self.assertFalse(user.check_password('wrong'))
        self.assertTrue(user.check_password('TestPass123!'))

    def test_unique_email_per_tenant(self):
        from django.db import IntegrityError
        self.make_user(email='dup@acme.com')
        with self.assertRaises(IntegrityError):
            self.make_user(email='dup@acme.com')

    def test_user_manager_filters_by_tenant(self):
        user = self.make_user(email='filtered@acme.com')
        emails = list(User.objects.values_list('email', flat=True))
        self.assertIn('filtered@acme.com', emails)

    def test_person_fk(self):
        person = self.make_person(first_name='Grace', last_name='H')
        user = self.make_user(person=person, email='grace@acme.com')
        self.assertEqual(user.person.first_name, 'Grace')


# ─── EmployeeRole ─────────────────────────────────────────────────────────────

class EmployeeRoleTest(SDTATestCase):

    def test_create(self):
        user = self.make_user()
        role = self.make_role()
        er = EmployeeRole.objects.create(employee=user, role=role)
        self.assertIsNotNone(er.id)

    def test_str(self):
        user = self.make_user(email='emp_role@acme.com')
        role = Role.objects.create(name='FieldTech')
        er = EmployeeRole.objects.create(employee=user, role=role)
        self.assertIn('FieldTech', str(er))

    def test_unique_per_tenant_employee_role(self):
        from django.db import IntegrityError
        user = self.make_user(email='unique_er@acme.com')
        role = self.make_role(name='UniqueRole')
        EmployeeRole.objects.create(employee=user, role=role)
        with self.assertRaises(IntegrityError):
            EmployeeRole.objects.create(employee=user, role=role)

    def test_delete(self):
        user = self.make_user(email='del_er@acme.com')
        role = self.make_role(name='DelRole')
        er = EmployeeRole.objects.create(employee=user, role=role)
        er_id = er.id
        er.delete()
        self.assertFalse(EmployeeRole.objects.filter(id=er_id).exists())


# ─── EmployeePosition ─────────────────────────────────────────────────────────

class EmployeePositionTest(SDTATestCase):

    def test_create(self):
        user = self.make_user()
        pos = self.make_position()
        ep = EmployeePosition.objects.create(employee=user, position=pos)
        self.assertIsNotNone(ep.id)
        self.assertFalse(ep.is_primary)

    def test_str(self):
        user = self.make_user(email='ep_str@acme.com')
        pos = self.make_position(title='Field Eng')
        ep = EmployeePosition.objects.create(employee=user, position=pos)
        self.assertIn('Field Eng', str(ep))

    def test_primary_flag(self):
        user = self.make_user(email='primary_ep@acme.com')
        pos = self.make_position()
        ep = EmployeePosition.objects.create(employee=user, position=pos, is_primary=True)
        ep.refresh_from_db()
        self.assertTrue(ep.is_primary)

    def test_delete(self):
        user = self.make_user(email='del_ep@acme.com')
        pos = self.make_position()
        ep = EmployeePosition.objects.create(employee=user, position=pos)
        ep_id = ep.id
        ep.delete()
        self.assertFalse(EmployeePosition.objects.filter(id=ep_id).exists())


# ─── RolePermission ───────────────────────────────────────────────────────────

class RolePermissionTest(SDTATestCase):

    def test_create(self):
        role = self.make_role(name='Perm Role')
        rp = RolePermission.objects.create(
            role=role, resource_key='work_orders',
            can_view=True, can_create=True,
        )
        self.assertTrue(rp.can_view)
        self.assertTrue(rp.can_create)
        self.assertFalse(rp.can_delete)

    def test_str(self):
        role = self.make_role(name='Perm2 Role')
        rp = RolePermission.objects.create(role=role, resource_key='invoices')
        self.assertIn('invoices', str(rp))

    def test_unique_role_resource(self):
        from django.db import IntegrityError
        role = self.make_role(name='Perm3 Role')
        RolePermission.objects.create(role=role, resource_key='quotes')
        with self.assertRaises(IntegrityError):
            RolePermission.objects.create(role=role, resource_key='quotes')

    def test_update_permissions(self):
        role = self.make_role(name='Perm4 Role')
        rp = RolePermission.objects.create(role=role, resource_key='customers')
        rp.can_edit = True
        rp.save()
        rp.refresh_from_db()
        self.assertTrue(rp.can_edit)

    def test_delete(self):
        role = self.make_role(name='Perm5 Role')
        rp = RolePermission.objects.create(role=role, resource_key='assets')
        rp_id = rp.id
        rp.delete()
        self.assertFalse(RolePermission.objects.filter(id=rp_id).exists())


# ─── TenantPreference ─────────────────────────────────────────────────────────

class TenantPreferenceTest(SDTATestCase):

    def test_create(self):
        tp = TenantPreference.objects.create(
            tenant_id=self.tenant_id,
            company_name='Acme Corp',
        )
        self.assertEqual(tp.company_name, 'Acme Corp')
        self.assertEqual(tp.default_currency, 'USD')
        self.assertEqual(tp.tenant_id, self.tenant_id)

    def test_str(self):
        tp = TenantPreference.objects.create(
            tenant_id=self.tenant_id,
            company_name='Prefs Inc',
        )
        self.assertIn('prefs', str(tp).lower())

    def test_unique_per_tenant(self):
        from django.db import IntegrityError
        TenantPreference.objects.create(
            tenant_id=self.tenant_id,
            company_name='First Pref',
        )
        with self.assertRaises(IntegrityError):
            TenantPreference.objects.create(
                tenant_id=self.tenant_id,
                company_name='Second Pref',
            )

    def test_update_timezone(self):
        tp = TenantPreference.objects.create(
            tenant_id=self.tenant_id,
            company_name='TZ Test',
        )
        tp.timezone = 'America/New_York'
        tp.save()
        tp.refresh_from_db()
        self.assertEqual(tp.timezone, 'America/New_York')

    def test_delete(self):
        tp = TenantPreference.objects.create(
            tenant_id=self.tenant_id,
            company_name='Del Pref',
        )
        tp_id = tp.id
        tp.delete()
        self.assertFalse(TenantPreference.objects.filter(id=tp_id).exists())


# ─── EmployeePreference ───────────────────────────────────────────────────────

class EmployeePreferenceTest(SDTATestCase):

    def test_create(self):
        user = self.make_user(email='pref_user@acme.com')
        ep = EmployeePreference.objects.create(user=user, ui_theme='Dark')
        self.assertEqual(ep.ui_theme, 'Dark')

    def test_str(self):
        user = self.make_user(username='pref_str_user', email='pref_str@acme.com')
        ep = EmployeePreference.objects.create(user=user)
        self.assertIn(user.username, str(ep))

    def test_one_to_one_constraint(self):
        from django.db import IntegrityError
        user = self.make_user(email='oto_pref@acme.com')
        EmployeePreference.objects.create(user=user)
        with self.assertRaises(IntegrityError):
            EmployeePreference.objects.create(user=user)

    def test_update_theme(self):
        user = self.make_user(email='theme_update@acme.com')
        ep = EmployeePreference.objects.create(user=user, ui_theme='Light')
        ep.ui_theme = 'System'
        ep.save()
        ep.refresh_from_db()
        self.assertEqual(ep.ui_theme, 'System')


# ─── SessionLog ───────────────────────────────────────────────────────────────

class SessionLogTest(SDTATestCase):

    def _make_session(self, user=None, **kwargs):
        if user is None:
            user = self.make_user(email=f'sess-{uuid.uuid4().hex[:5]}@acme.com')
        now = datetime.now(tz=timezone.utc)
        defaults = {
            'user': user,
            'tier_at_login': 'Lite',
            'login_at': now,
            'expiration_at': now,
            'ip_address': '127.0.0.1',
            'user_agent': 'TestBrowser/1.0',
        }
        defaults.update(kwargs)
        return SessionLog.objects.create(**defaults)

    def test_create(self):
        sl = self._make_session()
        self.assertIsNotNone(sl.id)

    def test_str(self):
        sl = self._make_session()
        self.assertIn(str(sl.id)[:8], str(sl))

    def test_update_logout(self):
        sl = self._make_session()
        now = datetime.now(tz=timezone.utc)
        sl.logout_at = now
        sl.save()
        sl.refresh_from_db()
        self.assertIsNotNone(sl.logout_at)

    def test_delete(self):
        sl = self._make_session()
        sl_id = sl.id
        sl.delete()
        self.assertFalse(SessionLog.objects.filter(id=sl_id).exists())


# ─── LoginAttemptLog ──────────────────────────────────────────────────────────

class LoginAttemptLogTest(SDTATestCase):

    def test_create_success(self):
        log = LoginAttemptLog.objects.create(
            user_email='login@acme.com',
            ip_address='10.0.0.1',
            user_agent='Mozilla/5.0',
            success=True,
        )
        self.assertTrue(log.success)
        self.assertEqual(log.user_email, 'login@acme.com')

    def test_create_failure(self):
        log = LoginAttemptLog.objects.create(
            user_email='bad@acme.com',
            ip_address='10.0.0.2',
            user_agent='Mozilla/5.0',
            success=False,
            failure_reason='invalid_password',
        )
        self.assertFalse(log.success)
        self.assertEqual(log.failure_reason, 'invalid_password')

    def test_str(self):
        log = LoginAttemptLog.objects.create(
            user_email='str@acme.com',
            ip_address='10.0.0.3',
            user_agent='Bot/1.0',
            success=False,
        )
        self.assertIn('str@acme.com', str(log))

    def test_attempted_at_auto_set(self):
        log = LoginAttemptLog.objects.create(
            user_email='ts@acme.com',
            ip_address='10.0.0.4',
            user_agent='Agent/1.0',
            success=True,
        )
        self.assertIsNotNone(log.attempted_at)

    def test_delete(self):
        log = LoginAttemptLog.objects.create(
            user_email='del@acme.com',
            ip_address='10.0.0.5',
            user_agent='Del/1.0',
            success=True,
        )
        log_id = log.id
        log.delete()
        self.assertFalse(LoginAttemptLog.objects.filter(id=log_id).exists())


# ─── EmployeeZone ────────────────────────────────────────────────────────

class EmployeeZoneTest(SDTATestCase):

    def test_create(self):
        zone = self.make_territory_zone(name='North Zone')
        employee = self.make_user(email='ez_employee@acme.com')
        ez = EmployeeZone.objects.create(zone=zone, employee=employee)
        self.assertEqual(ez.zone, zone)
        self.assertEqual(ez.employee, employee)

    def test_str(self):
        zone = self.make_territory_zone(name='Str Zone')
        employee = self.make_user(email='ez_str@acme.com')
        ez = EmployeeZone.objects.create(zone=zone, employee=employee)
        result = str(ez)
        self.assertIn('Str Zone', result)

    def test_unique_zone_employee(self):
        from django.db import IntegrityError
        zone = self.make_territory_zone()
        employee = self.make_user(email='ez_unique@acme.com')
        EmployeeZone.objects.create(zone=zone, employee=employee)
        with self.assertRaises(IntegrityError):
            EmployeeZone.objects.create(zone=zone, employee=employee)

    def test_multiple_employees_in_zone(self):
        """Multiple employees can be assigned to the same zone."""
        zone = self.make_territory_zone()
        emp1 = self.make_user(email='emp1_zone@acme.com')
        emp2 = self.make_user(email='emp2_zone@acme.com')
        ez1 = EmployeeZone.objects.create(zone=zone, employee=emp1)
        ez2 = EmployeeZone.objects.create(zone=zone, employee=emp2)
        self.assertEqual(ez1.zone, zone)
        self.assertEqual(ez2.zone, zone)
        self.assertNotEqual(ez1.employee, ez2.employee)

    def test_employee_multiple_zones(self):
        """One employee can be assigned to multiple zones."""
        zone1 = self.make_territory_zone(name='Zone 1')
        zone2 = self.make_territory_zone(name='Zone 2')
        employee = self.make_user(email='multi_zone_emp@acme.com')
        ez1 = EmployeeZone.objects.create(zone=zone1, employee=employee)
        ez2 = EmployeeZone.objects.create(zone=zone2, employee=employee)
        self.assertEqual(ez1.employee, employee)
        self.assertEqual(ez2.employee, employee)
        self.assertNotEqual(ez1.zone, ez2.zone)

    def test_delete(self):
        zone = self.make_territory_zone()
        employee = self.make_user(email='ez_del@acme.com')
        ez = EmployeeZone.objects.create(zone=zone, employee=employee)
        ez_id = ez.id
        ez.delete()
        self.assertFalse(EmployeeZone.objects.filter(id=ez_id).exists())
