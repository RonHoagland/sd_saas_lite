# tests/test_workforce.py
# CRUD and basic functionality tests for all models in the workforce app.

from datetime import date
from tests.base import SDTATestCase
from workforce.models import (
    WGDivision, WGTRole, WorkGroup, WorkGroupAsset, WorkGroupTeam,
    Skill, EmployeeSkill,
)


# ─── WGDivision ───────────────────────────────────────────────────────────────

class WGDivisionTest(SDTATestCase):

    def test_create(self):
        div = WGDivision.objects.create(name='Field Operations')
        self.assertEqual(div.name, 'Field Operations')
        self.assertEqual(div.status, 'Active')

    def test_str(self):
        div = WGDivision.objects.create(name='HVAC Division')
        self.assertEqual(str(div), 'HVAC Division')

    def test_inactive_status(self):
        div = WGDivision.objects.create(name='Retired Div', status='Inactive')
        div.refresh_from_db()
        self.assertEqual(div.status, 'Inactive')

    def test_update_name(self):
        div = WGDivision.objects.create(name='Old Division')
        div.name = 'New Division'
        div.save()
        div.refresh_from_db()
        self.assertEqual(div.name, 'New Division')

    def test_description_optional(self):
        div = WGDivision.objects.create(name='No Desc Div')
        self.assertEqual(div.description, '')

    def test_delete(self):
        div = WGDivision.objects.create(name='Del Division')
        div_id = div.id
        div.delete()
        self.assertFalse(WGDivision.objects.filter(id=div_id).exists())


# ─── WorkGroup ────────────────────────────────────────────────────────────────

class WorkGroupTest(SDTATestCase):

    def test_create(self):
        wg = WorkGroup.objects.create(name='Crew Alpha')
        self.assertEqual(wg.name, 'Crew Alpha')
        self.assertEqual(wg.status, 'Active')

    def test_str(self):
        wg = WorkGroup.objects.create(name='Str WorkGroup')
        self.assertEqual(str(wg), 'Str WorkGroup')

    def test_division_fk_optional(self):
        wg = WorkGroup.objects.create(name='No Div WG')
        self.assertIsNone(wg.division)

    def test_division_fk(self):
        div = WGDivision.objects.create(name='WG FK Div')
        wg = WorkGroup.objects.create(name='WG With Div', division=div)
        self.assertEqual(wg.division.name, 'WG FK Div')

    def test_manager_fk_optional(self):
        wg = WorkGroup.objects.create(name='No Mgr WG')
        self.assertIsNone(wg.manager)

    def test_manager_fk(self):
        mgr = self.make_user(email='wg_mgr@acme.com')
        wg = WorkGroup.objects.create(name='Managed WG', manager=mgr)
        self.assertEqual(wg.manager.email, 'wg_mgr@acme.com')

    def test_inactive_status(self):
        wg = WorkGroup.objects.create(name='Inactive WG', status='Inactive')
        wg.refresh_from_db()
        self.assertEqual(wg.status, 'Inactive')

    def test_update_name(self):
        wg = WorkGroup.objects.create(name='Old WG')
        wg.name = 'Updated WG'
        wg.save()
        wg.refresh_from_db()
        self.assertEqual(wg.name, 'Updated WG')

    def test_delete(self):
        wg = WorkGroup.objects.create(name='Del WG')
        wg_id = wg.id
        wg.delete()
        self.assertFalse(WorkGroup.objects.filter(id=wg_id).exists())

    def test_set_null_on_division_delete(self):
        """WorkGroup.division is SET_NULL when division is deleted."""
        div = WGDivision.objects.create(name='Deletable Div')
        wg = WorkGroup.objects.create(name='Orphan WG', division=div)
        div.delete()
        wg.refresh_from_db()
        self.assertIsNone(wg.division)


# ─── WGTRole ──────────────────────────────────────────────────────────────────

class WGTRoleTest(SDTATestCase):

    def test_create(self):
        wg = self.make_work_group()
        role = WGTRole.objects.create(work_group=wg, name='Lead Technician')
        self.assertEqual(role.name, 'Lead Technician')

    def test_str(self):
        wg = WorkGroup.objects.create(name='Role WG')
        role = WGTRole.objects.create(work_group=wg, name='Helper')
        result = str(role)
        self.assertIn('Role WG', result)
        self.assertIn('Helper', result)

    def test_description_optional(self):
        wg = self.make_work_group()
        role = WGTRole.objects.create(work_group=wg, name='No Desc Role')
        self.assertEqual(role.description, '')

    def test_update_name(self):
        wg = self.make_work_group()
        role = WGTRole.objects.create(work_group=wg, name='Old Role')
        role.name = 'New Role'
        role.save()
        role.refresh_from_db()
        self.assertEqual(role.name, 'New Role')

    def test_delete(self):
        wg = self.make_work_group()
        role = WGTRole.objects.create(work_group=wg, name='Del Role')
        role_id = role.id
        role.delete()
        self.assertFalse(WGTRole.objects.filter(id=role_id).exists())

    def test_cascade_delete_with_work_group(self):
        """WGTRole deleted when parent WorkGroup is deleted."""
        wg = WorkGroup.objects.create(name='Cascade WG')
        role = WGTRole.objects.create(work_group=wg, name='Cascade Role')
        role_id = role.id
        wg.delete()
        self.assertFalse(WGTRole.objects.filter(id=role_id).exists())


# ─── WorkGroupTeam ────────────────────────────────────────────────────────────

class WorkGroupTeamTest(SDTATestCase):

    def test_create(self):
        wg = self.make_work_group()
        user = self.make_user(email='wgt_user@acme.com')
        member = WorkGroupTeam.objects.create(work_group=wg, user=user)
        self.assertFalse(member.is_lead)
        self.assertIsNone(member.role)

    def test_str(self):
        wg = WorkGroup.objects.create(name='WGT Str WG')
        user = self.make_user(email='wgt_str@acme.com')
        member = WorkGroupTeam.objects.create(work_group=wg, user=user)
        result = str(member)
        self.assertIn('WGT Str WG', result)

    def test_is_lead(self):
        wg = self.make_work_group()
        user = self.make_user(email='lead@acme.com')
        member = WorkGroupTeam.objects.create(work_group=wg, user=user, is_lead=True)
        member.refresh_from_db()
        self.assertTrue(member.is_lead)

    def test_role_fk_optional(self):
        wg = self.make_work_group()
        user = self.make_user(email='no_role@acme.com')
        member = WorkGroupTeam.objects.create(work_group=wg, user=user)
        self.assertIsNone(member.role)

    def test_role_fk(self):
        wg = self.make_work_group()
        role = WGTRole.objects.create(work_group=wg, name='Field Tech')
        user = self.make_user(email='with_role@acme.com')
        member = WorkGroupTeam.objects.create(work_group=wg, user=user, role=role)
        self.assertEqual(member.role.name, 'Field Tech')

    def test_unique_work_group_user(self):
        from django.db import IntegrityError
        wg = self.make_work_group()
        user = self.make_user(email='dup_wgt@acme.com')
        WorkGroupTeam.objects.create(work_group=wg, user=user)
        with self.assertRaises(IntegrityError):
            WorkGroupTeam.objects.create(work_group=wg, user=user, is_lead=True)

    def test_delete(self):
        wg = self.make_work_group()
        user = self.make_user(email='del_wgt@acme.com')
        member = WorkGroupTeam.objects.create(work_group=wg, user=user)
        member_id = member.id
        member.delete()
        self.assertFalse(WorkGroupTeam.objects.filter(id=member_id).exists())

    def test_cascade_delete_with_work_group(self):
        """WorkGroupTeam deleted when parent WorkGroup is deleted."""
        wg = WorkGroup.objects.create(name='Cascade WGT WG')
        user = self.make_user(email='cascade_wgt@acme.com')
        member = WorkGroupTeam.objects.create(work_group=wg, user=user)
        member_id = member.id
        wg.delete()
        self.assertFalse(WorkGroupTeam.objects.filter(id=member_id).exists())


# ─── WorkGroupAsset ───────────────────────────────────────────────────────────

class WorkGroupAssetTest(SDTATestCase):

    def test_create(self):
        wg = self.make_work_group()
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        wga = WorkGroupAsset.objects.create(work_group=wg, asset=asset)
        self.assertEqual(wga.work_group, wg)
        self.assertEqual(wga.asset, asset)

    def test_str(self):
        wg = WorkGroup.objects.create(name='WGA Str WG')
        customer = self.make_customer()
        asset = self.make_asset(name='WGA Str Asset', customer=customer)
        wga = WorkGroupAsset.objects.create(work_group=wg, asset=asset)
        result = str(wga)
        self.assertIn('WGA Str WG', result)
        self.assertIn('WGA Str Asset', result)

    def test_notes_optional(self):
        wg = self.make_work_group()
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        wga = WorkGroupAsset.objects.create(work_group=wg, asset=asset)
        self.assertEqual(wga.notes, '')

    def test_unique_work_group_asset(self):
        from django.db import IntegrityError
        wg = self.make_work_group()
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        WorkGroupAsset.objects.create(work_group=wg, asset=asset)
        with self.assertRaises(IntegrityError):
            WorkGroupAsset.objects.create(work_group=wg, asset=asset, notes='Dup')

    def test_delete(self):
        wg = self.make_work_group()
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        wga = WorkGroupAsset.objects.create(work_group=wg, asset=asset)
        wga_id = wga.id
        wga.delete()
        self.assertFalse(WorkGroupAsset.objects.filter(id=wga_id).exists())

    def test_cascade_delete_with_work_group(self):
        """WorkGroupAsset deleted when parent WorkGroup is deleted."""
        wg = WorkGroup.objects.create(name='Cascade WGA WG')
        customer = self.make_customer()
        asset = self.make_asset(customer=customer)
        wga = WorkGroupAsset.objects.create(work_group=wg, asset=asset)
        wga_id = wga.id
        wg.delete()
        self.assertFalse(WorkGroupAsset.objects.filter(id=wga_id).exists())


# ─── Skill ────────────────────────────────────────────────────────────────

class SkillTest(SDTATestCase):

    def test_create(self):
        skill = Skill.objects.create(name='HVAC Certification')
        self.assertEqual(skill.name, 'HVAC Certification')
        self.assertEqual(skill.category, 'Competency')
        self.assertEqual(skill.status, 'Active')

    def test_str(self):
        skill = Skill.objects.create(name='Str Skill')
        self.assertEqual(str(skill), 'Str Skill')

    def test_category_choices(self):
        for category in ('Certification', 'License', 'Training', 'Competency'):
            skill = Skill.objects.create(name=f'Skill {category}', category=category)
            skill.refresh_from_db()
            self.assertEqual(skill.category, category)
            skill.delete()

    def test_status_choices(self):
        for status in ('Active', 'Inactive'):
            skill = Skill.objects.create(name=f'Skill {status}', status=status)
            skill.refresh_from_db()
            self.assertEqual(skill.status, status)
            skill.delete()

    def test_update_status(self):
        skill = self.make_skill()
        skill.status = 'Inactive'
        skill.save()
        skill.refresh_from_db()
        self.assertEqual(skill.status, 'Inactive')

    def test_delete(self):
        skill = self.make_skill()
        skill_id = skill.id
        skill.delete()
        self.assertFalse(Skill.objects.filter(id=skill_id).exists())


# ─── EmployeeSkill ────────────────────────────────────────────────────────

class EmployeeSkillTest(SDTATestCase):

    def test_create(self):
        employee = self.make_user(email='es_employee@acme.com')
        skill = self.make_skill()
        es = EmployeeSkill.objects.create(
            employee=employee,
            skill=skill,
            date_earned=date(2024, 1, 15),
        )
        self.assertEqual(es.employee, employee)
        self.assertEqual(es.skill, skill)
        self.assertEqual(es.status, 'Active')

    def test_str(self):
        employee = self.make_user(email='es_str@acme.com')
        skill = self.make_skill(name='Str Skill')
        es = EmployeeSkill.objects.create(
            employee=employee, skill=skill, date_earned=date.today()
        )
        result = str(es)
        self.assertIn('Str Skill', result)

    def test_expiration_date_optional(self):
        employee = self.make_user(email='es_no_exp@acme.com')
        skill = self.make_skill()
        es = EmployeeSkill.objects.create(
            employee=employee, skill=skill, date_earned=date.today()
        )
        self.assertIsNone(es.expiration_date)

    def test_expiration_date_set(self):
        employee = self.make_user(email='es_with_exp@acme.com')
        skill = self.make_skill()
        es = EmployeeSkill.objects.create(
            employee=employee,
            skill=skill,
            date_earned=date(2024, 1, 15),
            expiration_date=date(2026, 1, 15),
        )
        es.refresh_from_db()
        self.assertEqual(es.expiration_date, date(2026, 1, 15))

    def test_status_choices(self):
        employee = self.make_user(email='es_status@acme.com')
        skill = self.make_skill()
        for status in ('Active', 'Expired'):
            es = EmployeeSkill.objects.create(
                employee=employee, skill=skill, date_earned=date.today(), status=status
            )
            es.refresh_from_db()
            self.assertEqual(es.status, status)
            es.delete()

    def test_unique_employee_skill(self):
        from django.db import IntegrityError
        employee = self.make_user(email='es_unique@acme.com')
        skill = self.make_skill()
        EmployeeSkill.objects.create(
            employee=employee, skill=skill, date_earned=date.today()
        )
        with self.assertRaises(IntegrityError):
            EmployeeSkill.objects.create(
                employee=employee, skill=skill, date_earned=date.today()
            )

    def test_update_status(self):
        employee = self.make_user(email='es_upd@acme.com')
        skill = self.make_skill()
        es = EmployeeSkill.objects.create(
            employee=employee, skill=skill, date_earned=date.today()
        )
        es.status = 'Expired'
        es.save()
        es.refresh_from_db()
        self.assertEqual(es.status, 'Expired')

    def test_delete(self):
        employee = self.make_user(email='es_del@acme.com')
        skill = self.make_skill()
        es = EmployeeSkill.objects.create(
            employee=employee, skill=skill, date_earned=date.today()
        )
        es_id = es.id
        es.delete()
        self.assertFalse(EmployeeSkill.objects.filter(id=es_id).exists())
