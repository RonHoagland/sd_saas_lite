# tests/test_automation_safety.py
# CRUD and basic functionality tests for safety-related models in the automation app.

from datetime import datetime, timezone
from tests.base import SDTATestCase
from automation.models import SafetyForm, WOSFAnswer


# ─── SafetyForm ───────────────────────────────────────────────────────────

class SafetyFormTest(SDTATestCase):

    def test_create(self):
        sf = SafetyForm.objects.create(form_name='Site Safety Checklist')
        self.assertEqual(sf.form_name, 'Site Safety Checklist')
        self.assertEqual(sf.status, 'Active')
        self.assertFalse(sf.required_before_work)

    def test_str(self):
        sf = SafetyForm.objects.create(form_name='Str Form')
        self.assertEqual(str(sf), 'Str Form')

    def test_status_choices(self):
        for status in ('Active', 'Inactive', 'Draft'):
            sf = SafetyForm.objects.create(form_name=f'Status {status}', status=status)
            sf.refresh_from_db()
            self.assertEqual(sf.status, status)
            sf.delete()

    def test_required_before_work(self):
        sf = SafetyForm.objects.create(
            form_name='Required Form', required_before_work=True
        )
        sf.refresh_from_db()
        self.assertTrue(sf.required_before_work)

    def test_description_optional(self):
        sf = SafetyForm.objects.create(form_name='No Desc Form')
        self.assertEqual(sf.description, '')

    def test_form_definition_optional(self):
        sf = SafetyForm.objects.create(form_name='No Def Form')
        self.assertEqual(sf.form_definition, {})

    def test_form_definition_json(self):
        form_def = {'fields': ['hazard', 'ppe', 'sign_off']}
        sf = SafetyForm.objects.create(form_name='Def Form', form_definition=form_def)
        sf.refresh_from_db()
        self.assertEqual(sf.form_definition['fields'][0], 'hazard')

    def test_update_status(self):
        sf = SafetyForm.objects.create(form_name='Upd Form')
        sf.status = 'Inactive'
        sf.save()
        sf.refresh_from_db()
        self.assertEqual(sf.status, 'Inactive')

    def test_delete(self):
        sf = SafetyForm.objects.create(form_name='Del Form')
        sf_id = sf.id
        sf.delete()
        self.assertFalse(SafetyForm.objects.filter(id=sf_id).exists())


# ─── WOSFAnswer ───────────────────────────────────────────────────────────

class WOSFAnswerTest(SDTATestCase):

    def test_create(self):
        wo = self.make_work_order()
        form = self.make_safety_form()
        answer = WOSFAnswer.objects.create(
            work_order=wo,
            safety_form=form,
        )
        self.assertEqual(answer.work_order, wo)
        self.assertEqual(answer.safety_form, form)
        self.assertEqual(answer.answers, {})

    def test_str(self):
        wo = self.make_work_order()
        form = self.make_safety_form(form_name='Str Form')
        answer = WOSFAnswer.objects.create(work_order=wo, safety_form=form)
        result = str(answer)
        self.assertIn('Str Form', result)

    def test_employee_fk_optional(self):
        wo = self.make_work_order()
        form = self.make_safety_form()
        answer = WOSFAnswer.objects.create(work_order=wo, safety_form=form)
        self.assertIsNone(answer.employee)

    def test_employee_fk(self):
        wo = self.make_work_order()
        form = self.make_safety_form()
        employee = self.make_user(email='answer_user@acme.com')
        answer = WOSFAnswer.objects.create(
            work_order=wo, safety_form=form, employee=employee
        )
        self.assertEqual(answer.employee.email, 'answer_user@acme.com')

    def test_answers_json(self):
        wo = self.make_work_order()
        form = self.make_safety_form()
        answers_data = {'hazard_present': True, 'ppe_provided': True}
        answer = WOSFAnswer.objects.create(
            work_order=wo, safety_form=form, answers=answers_data
        )
        answer.refresh_from_db()
        self.assertTrue(answer.answers['hazard_present'])

    def test_completed_at_optional(self):
        wo = self.make_work_order()
        form = self.make_safety_form()
        answer = WOSFAnswer.objects.create(work_order=wo, safety_form=form)
        self.assertIsNone(answer.completed_at)

    def test_completed_at_set(self):
        wo = self.make_work_order()
        form = self.make_safety_form()
        now = datetime.now(tz=timezone.utc)
        answer = WOSFAnswer.objects.create(
            work_order=wo, safety_form=form, completed_at=now
        )
        answer.refresh_from_db()
        self.assertIsNotNone(answer.completed_at)

    def test_notes_optional(self):
        wo = self.make_work_order()
        form = self.make_safety_form()
        answer = WOSFAnswer.objects.create(work_order=wo, safety_form=form)
        self.assertEqual(answer.notes, '')

    def test_notes_set(self):
        wo = self.make_work_order()
        form = self.make_safety_form()
        answer = WOSFAnswer.objects.create(
            work_order=wo, safety_form=form, notes='All passed'
        )
        answer.refresh_from_db()
        self.assertEqual(answer.notes, 'All passed')

    def test_update_answers(self):
        wo = self.make_work_order()
        form = self.make_safety_form()
        answer = WOSFAnswer.objects.create(work_order=wo, safety_form=form)
        answer.answers = {'verified': True}
        answer.save()
        answer.refresh_from_db()
        self.assertTrue(answer.answers['verified'])

    def test_delete(self):
        wo = self.make_work_order()
        form = self.make_safety_form()
        answer = WOSFAnswer.objects.create(work_order=wo, safety_form=form)
        answer_id = answer.id
        answer.delete()
        self.assertFalse(WOSFAnswer.objects.filter(id=answer_id).exists())

    def test_cascade_delete_with_work_order(self):
        """WOSFAnswer deleted when parent WorkOrder is deleted."""
        wo = self.make_work_order()
        form = self.make_safety_form()
        answer = WOSFAnswer.objects.create(work_order=wo, safety_form=form)
        answer_id = answer.id
        wo.delete()
        self.assertFalse(WOSFAnswer.objects.filter(id=answer_id).exists())
