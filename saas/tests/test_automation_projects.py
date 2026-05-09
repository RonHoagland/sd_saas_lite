# tests/test_automation_projects.py
# CRUD and basic functionality tests for project management models in the automation app.

from datetime import date
from tests.base import SDTATestCase
from automation.models import (
    Portfolio, PortfolioProject, PortfolioMember, Sprint, SprintMember, SprintTask,
    Milestone, MilestoneTask, TerritoryZone,
)


# ─── Portfolio ────────────────────────────────────────────────────────────

class PortfolioTest(SDTATestCase):

    def test_create(self):
        p = Portfolio.objects.create(name='Infrastructure')
        self.assertEqual(p.name, 'Infrastructure')
        self.assertEqual(p.status, 'Active')

    def test_str(self):
        p = Portfolio.objects.create(name='Str Portfolio')
        self.assertEqual(str(p), 'Str Portfolio')

    def test_status_choices(self):
        for status in ('Active', 'Archived'):
            p = Portfolio.objects.create(name=f'Status {status}', status=status)
            p.refresh_from_db()
            self.assertEqual(p.status, status)
            p.delete()

    def test_description_optional(self):
        p = Portfolio.objects.create(name='No Desc')
        self.assertEqual(p.description, '')

    def test_update_status(self):
        p = Portfolio.objects.create(name='Upd Portfolio')
        p.status = 'Archived'
        p.save()
        p.refresh_from_db()
        self.assertEqual(p.status, 'Archived')

    def test_delete(self):
        p = Portfolio.objects.create(name='Del Portfolio')
        p_id = p.id
        p.delete()
        self.assertFalse(Portfolio.objects.filter(id=p_id).exists())


# ─── PortfolioProject ────────────────────────────────────────────────────

class PortfolioProjectTest(SDTATestCase):

    def test_create(self):
        portfolio = self.make_portfolio()
        project = self.make_work_group(name='PP Project')
        pp = PortfolioProject.objects.create(portfolio=portfolio, project=project)
        self.assertEqual(pp.portfolio, portfolio)
        self.assertEqual(pp.project, project)

    def test_str(self):
        portfolio = self.make_portfolio(name='Str Portfolio')
        project = self.make_work_group(name='Str Project')
        pp = PortfolioProject.objects.create(portfolio=portfolio, project=project)
        result = str(pp)
        self.assertIn('Str Portfolio', result)
        self.assertIn('Str Project', result)

    def test_unique_portfolio_project(self):
        from django.db import IntegrityError
        portfolio = self.make_portfolio()
        project = self.make_work_group()
        PortfolioProject.objects.create(portfolio=portfolio, project=project)
        with self.assertRaises(IntegrityError):
            PortfolioProject.objects.create(portfolio=portfolio, project=project)

    def test_delete(self):
        portfolio = self.make_portfolio()
        project = self.make_work_group()
        pp = PortfolioProject.objects.create(portfolio=portfolio, project=project)
        pp_id = pp.id
        pp.delete()
        self.assertFalse(PortfolioProject.objects.filter(id=pp_id).exists())


# ─── PortfolioMember ──────────────────────────────────────────────────────

class PortfolioMemberTest(SDTATestCase):

    def test_create(self):
        portfolio = self.make_portfolio()
        employee = self.make_user(email='pm_employee@acme.com')
        pm = PortfolioMember.objects.create(portfolio=portfolio, employee=employee)
        self.assertEqual(pm.portfolio, portfolio)
        self.assertEqual(pm.employee, employee)

    def test_str(self):
        portfolio = self.make_portfolio(name='Str Portfolio')
        employee = self.make_user(email='pm_str@acme.com')
        pm = PortfolioMember.objects.create(portfolio=portfolio, employee=employee)
        result = str(pm)
        self.assertIn('Str Portfolio', result)

    def test_unique_portfolio_employee(self):
        from django.db import IntegrityError
        portfolio = self.make_portfolio()
        employee = self.make_user(email='pm_unique@acme.com')
        PortfolioMember.objects.create(portfolio=portfolio, employee=employee)
        with self.assertRaises(IntegrityError):
            PortfolioMember.objects.create(portfolio=portfolio, employee=employee)

    def test_delete(self):
        portfolio = self.make_portfolio()
        employee = self.make_user(email='pm_del@acme.com')
        pm = PortfolioMember.objects.create(portfolio=portfolio, employee=employee)
        pm_id = pm.id
        pm.delete()
        self.assertFalse(PortfolioMember.objects.filter(id=pm_id).exists())


# ─── Sprint ───────────────────────────────────────────────────────────────

class SprintTest(SDTATestCase):

    def test_create(self):
        project = self.make_work_group()
        sprint = Sprint.objects.create(
            project=project,
            name='Sprint 1',
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 14),
        )
        self.assertEqual(sprint.project, project)
        self.assertEqual(sprint.name, 'Sprint 1')
        self.assertEqual(sprint.status, 'Planned')

    def test_str(self):
        project = self.make_work_group(name='Str Project')
        sprint = self.make_sprint(project=project, name='Str Sprint')
        result = str(sprint)
        self.assertIn('Str Project', result)
        self.assertIn('Str Sprint', result)

    def test_status_choices(self):
        project = self.make_work_group()
        for status in ('Planned', 'Active', 'Completed', 'Cancelled'):
            sprint = Sprint.objects.create(
                project=project,
                name=f'Sprint {status}',
                start_date=date.today(),
                end_date=date.today(),
                status=status,
            )
            sprint.refresh_from_db()
            self.assertEqual(sprint.status, status)
            sprint.delete()

    def test_goal_optional(self):
        sprint = self.make_sprint()
        self.assertEqual(sprint.goal, '')

    def test_goal_set(self):
        project = self.make_work_group()
        sprint = Sprint.objects.create(
            project=project,
            name='Sprint Goal',
            start_date=date.today(),
            end_date=date.today(),
            goal='Complete core features',
        )
        sprint.refresh_from_db()
        self.assertEqual(sprint.goal, 'Complete core features')

    def test_update_status(self):
        sprint = self.make_sprint()
        sprint.status = 'Active'
        sprint.save()
        sprint.refresh_from_db()
        self.assertEqual(sprint.status, 'Active')

    def test_delete(self):
        sprint = self.make_sprint()
        sprint_id = sprint.id
        sprint.delete()
        self.assertFalse(Sprint.objects.filter(id=sprint_id).exists())


# ─── SprintMember ────────────────────────────────────────────────────────

class SprintMemberTest(SDTATestCase):

    def test_create(self):
        sprint = self.make_sprint()
        employee = self.make_user(email='sm_employee@acme.com')
        sm = SprintMember.objects.create(sprint=sprint, employee=employee)
        self.assertEqual(sm.sprint, sprint)
        self.assertEqual(sm.employee, employee)

    def test_str(self):
        sprint = self.make_sprint()
        employee = self.make_user(email='sm_str@acme.com')
        sm = SprintMember.objects.create(sprint=sprint, employee=employee)
        result = str(sm)
        self.assertIn(employee.username, result)

    def test_unique_sprint_employee(self):
        from django.db import IntegrityError
        sprint = self.make_sprint()
        employee = self.make_user(email='sm_unique@acme.com')
        SprintMember.objects.create(sprint=sprint, employee=employee)
        with self.assertRaises(IntegrityError):
            SprintMember.objects.create(sprint=sprint, employee=employee)

    def test_delete(self):
        sprint = self.make_sprint()
        employee = self.make_user(email='sm_del@acme.com')
        sm = SprintMember.objects.create(sprint=sprint, employee=employee)
        sm_id = sm.id
        sm.delete()
        self.assertFalse(SprintMember.objects.filter(id=sm_id).exists())


# ─── SprintTask ───────────────────────────────────────────────────────────

class SprintTaskTest(SDTATestCase):

    def test_create(self):
        sprint = self.make_sprint()
        task = self.make_task(title='ST Task')
        st = SprintTask.objects.create(sprint=sprint, task=task)
        self.assertEqual(st.sprint, sprint)
        self.assertEqual(st.task, task)

    def test_str(self):
        sprint = self.make_sprint()
        task = self.make_task(title='Str Task')
        st = SprintTask.objects.create(sprint=sprint, task=task)
        result = str(st)
        self.assertIn('Str Task', result)

    def test_unique_sprint_task(self):
        from django.db import IntegrityError
        sprint = self.make_sprint()
        task = self.make_task()
        SprintTask.objects.create(sprint=sprint, task=task)
        with self.assertRaises(IntegrityError):
            SprintTask.objects.create(sprint=sprint, task=task)

    def test_delete(self):
        sprint = self.make_sprint()
        task = self.make_task()
        st = SprintTask.objects.create(sprint=sprint, task=task)
        st_id = st.id
        st.delete()
        self.assertFalse(SprintTask.objects.filter(id=st_id).exists())


# ─── Milestone ────────────────────────────────────────────────────────────

class MilestoneTest(SDTATestCase):

    def test_create(self):
        project = self.make_work_group()
        ms = Milestone.objects.create(project=project, name='Phase 1')
        self.assertEqual(ms.project, project)
        self.assertEqual(ms.name, 'Phase 1')
        self.assertEqual(ms.status, 'Pending')

    def test_str(self):
        project = self.make_work_group(name='Str Project')
        ms = self.make_milestone(project=project, name='Str Milestone')
        result = str(ms)
        self.assertIn('Str Project', result)
        self.assertIn('Str Milestone', result)

    def test_status_choices(self):
        project = self.make_work_group()
        for status in ('Pending', 'In Progress', 'Completed', 'Missed'):
            ms = Milestone.objects.create(
                project=project, name=f'Status {status}', status=status
            )
            ms.refresh_from_db()
            self.assertEqual(ms.status, status)
            ms.delete()

    def test_due_date_optional(self):
        ms = self.make_milestone()
        self.assertIsNone(ms.due_date)

    def test_due_date_set(self):
        project = self.make_work_group()
        ms = Milestone.objects.create(
            project=project, name='Dated MS', due_date=date(2026, 6, 30)
        )
        ms.refresh_from_db()
        self.assertEqual(ms.due_date, date(2026, 6, 30))

    def test_description_optional(self):
        ms = self.make_milestone()
        self.assertEqual(ms.description, '')

    def test_update_status(self):
        ms = self.make_milestone()
        ms.status = 'In Progress'
        ms.save()
        ms.refresh_from_db()
        self.assertEqual(ms.status, 'In Progress')

    def test_delete(self):
        ms = self.make_milestone()
        ms_id = ms.id
        ms.delete()
        self.assertFalse(Milestone.objects.filter(id=ms_id).exists())


# ─── MilestoneTask ────────────────────────────────────────────────────────

class MilestoneTaskTest(SDTATestCase):

    def test_create(self):
        milestone = self.make_milestone()
        task = self.make_task(title='MT Task')
        mt = MilestoneTask.objects.create(milestone=milestone, task=task)
        self.assertEqual(mt.milestone, milestone)
        self.assertEqual(mt.task, task)

    def test_str(self):
        milestone = self.make_milestone()
        task = self.make_task(title='Str Task')
        mt = MilestoneTask.objects.create(milestone=milestone, task=task)
        result = str(mt)
        self.assertIn('Str Task', result)

    def test_unique_milestone_task(self):
        from django.db import IntegrityError
        milestone = self.make_milestone()
        task = self.make_task()
        MilestoneTask.objects.create(milestone=milestone, task=task)
        with self.assertRaises(IntegrityError):
            MilestoneTask.objects.create(milestone=milestone, task=task)

    def test_delete(self):
        milestone = self.make_milestone()
        task = self.make_task()
        mt = MilestoneTask.objects.create(milestone=milestone, task=task)
        mt_id = mt.id
        mt.delete()
        self.assertFalse(MilestoneTask.objects.filter(id=mt_id).exists())


# ─── TerritoryZone ───────────────────────────────────────────────────────

class TerritoryZoneTest(SDTATestCase):

    def test_create(self):
        tz = TerritoryZone.objects.create(name='North Region')
        self.assertEqual(tz.name, 'North Region')
        self.assertEqual(tz.status, 'Active')

    def test_str(self):
        tz = TerritoryZone.objects.create(name='Str Zone')
        self.assertEqual(str(tz), 'Str Zone')

    def test_status_choices(self):
        for status in ('Active', 'Inactive'):
            tz = TerritoryZone.objects.create(name=f'Status {status}', status=status)
            tz.refresh_from_db()
            self.assertEqual(tz.status, status)
            tz.delete()

    def test_employee_fk_optional(self):
        tz = TerritoryZone.objects.create(name='No Manager')
        self.assertIsNone(tz.employee)

    def test_employee_fk(self):
        employee = self.make_user(email='zone_mgr@acme.com')
        tz = TerritoryZone.objects.create(name='Managed Zone', employee=employee)
        self.assertEqual(tz.employee.email, 'zone_mgr@acme.com')

    def test_description_optional(self):
        tz = TerritoryZone.objects.create(name='No Desc')
        self.assertEqual(tz.description, '')

    def test_description_set(self):
        tz = TerritoryZone.objects.create(
            name='Described Zone', description='Covers metro area'
        )
        tz.refresh_from_db()
        self.assertEqual(tz.description, 'Covers metro area')

    def test_update_status(self):
        tz = self.make_territory_zone()
        tz.status = 'Inactive'
        tz.save()
        tz.refresh_from_db()
        self.assertEqual(tz.status, 'Inactive')

    def test_delete(self):
        tz = self.make_territory_zone()
        tz_id = tz.id
        tz.delete()
        self.assertFalse(TerritoryZone.objects.filter(id=tz_id).exists())
