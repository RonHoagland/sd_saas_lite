# tests/test_automation_workflow.py
# CRUD and basic functionality tests for workflow-related models in the automation app.

from datetime import timedelta
from tests.base import SDTATestCase
from automation.models import (
    WorkFlow, WFStep, WFStepToDo, WFTool, WFInventory, WFSafetyForm,
)


# ─── WorkFlow ──────────────────────────────────────────────────────────────

class WorkFlowTest(SDTATestCase):

    def test_create(self):
        wf = WorkFlow.objects.create(name='AC Maintenance')
        self.assertEqual(wf.name, 'AC Maintenance')
        self.assertEqual(wf.status, 'Active')

    def test_str(self):
        wf = WorkFlow.objects.create(name='Str Workflow', work_order_type='Maintenance')
        result = str(wf)
        self.assertIn('Str Workflow', result)

    def test_status_choices(self):
        for status in ('Active', 'Inactive', 'Draft'):
            wf = WorkFlow.objects.create(name=f'Status {status}', status=status)
            wf.refresh_from_db()
            self.assertEqual(wf.status, status)
            wf.delete()

    def test_description_optional(self):
        wf = WorkFlow.objects.create(name='No Desc WF')
        self.assertEqual(wf.description, '')

    def test_work_order_type_optional(self):
        wf = WorkFlow.objects.create(name='No WOT WF')
        self.assertEqual(wf.work_order_type, '')

    def test_update_name(self):
        wf = WorkFlow.objects.create(name='Old Name')
        wf.name = 'New Name'
        wf.save()
        wf.refresh_from_db()
        self.assertEqual(wf.name, 'New Name')

    def test_delete(self):
        wf = WorkFlow.objects.create(name='Del WF')
        wf_id = wf.id
        wf.delete()
        self.assertFalse(WorkFlow.objects.filter(id=wf_id).exists())


# ─── WFStep ───────────────────────────────────────────────────────────────

class WFStepTest(SDTATestCase):

    def test_create(self):
        wf = self.make_workflow(name='WFStep WF')
        step = WFStep.objects.create(
            workflow=wf,
            step_name='Inspect Unit',
            sort_order=1,
        )
        self.assertEqual(step.step_name, 'Inspect Unit')
        self.assertEqual(step.sort_order, 1)

    def test_str(self):
        wf = self.make_workflow(name='Str WF')
        step = WFStep.objects.create(workflow=wf, step_name='Str Step', sort_order=2)
        result = str(step)
        self.assertIn('Str WF', result)
        self.assertIn('Str Step', result)

    def test_estimated_duration(self):
        wf = self.make_workflow()
        duration = timedelta(hours=1, minutes=30)
        step = WFStep.objects.create(
            workflow=wf, step_name='Dur Step', estimated_duration=duration
        )
        step.refresh_from_db()
        self.assertEqual(step.estimated_duration, duration)

    def test_description_optional(self):
        wf = self.make_workflow()
        step = WFStep.objects.create(workflow=wf, step_name='No Desc Step')
        self.assertEqual(step.description, '')

    def test_delete(self):
        wf = self.make_workflow()
        step = WFStep.objects.create(workflow=wf, step_name='Del Step')
        step_id = step.id
        step.delete()
        self.assertFalse(WFStep.objects.filter(id=step_id).exists())

    def test_cascade_delete_with_workflow(self):
        """WFStep deleted when parent WorkFlow is deleted."""
        wf = self.make_workflow()
        step = WFStep.objects.create(workflow=wf, step_name='Cascade Step')
        step_id = step.id
        wf.delete()
        self.assertFalse(WFStep.objects.filter(id=step_id).exists())


# ─── WFStepToDo ───────────────────────────────────────────────────────────

class WFStepToDoTest(SDTATestCase):

    def test_create(self):
        wf = self.make_workflow()
        step = WFStep.objects.create(workflow=wf, step_name='Step 1')
        todo = WFStepToDo.objects.create(
            wf_step=step, label='Turn off power', sort_order=1
        )
        self.assertEqual(todo.label, 'Turn off power')
        self.assertFalse(todo.is_required)

    def test_str(self):
        wf = self.make_workflow()
        step = WFStep.objects.create(workflow=wf, step_name='Str Step')
        todo = WFStepToDo.objects.create(wf_step=step, label='Str To-Do', sort_order=1)
        self.assertEqual(str(todo), 'Str To-Do')

    def test_is_required(self):
        wf = self.make_workflow()
        step = WFStep.objects.create(workflow=wf, step_name='Step 2')
        todo = WFStepToDo.objects.create(
            wf_step=step, label='Required Task', is_required=True
        )
        todo.refresh_from_db()
        self.assertTrue(todo.is_required)

    def test_delete(self):
        wf = self.make_workflow()
        step = WFStep.objects.create(workflow=wf, step_name='Step 3')
        todo = WFStepToDo.objects.create(wf_step=step, label='Del Todo')
        todo_id = todo.id
        todo.delete()
        self.assertFalse(WFStepToDo.objects.filter(id=todo_id).exists())

    def test_cascade_delete_with_step(self):
        """WFStepToDo deleted when parent WFStep is deleted."""
        wf = self.make_workflow()
        step = WFStep.objects.create(workflow=wf, step_name='Cascade Step')
        todo = WFStepToDo.objects.create(wf_step=step, label='Cascade Todo')
        todo_id = todo.id
        step.delete()
        self.assertFalse(WFStepToDo.objects.filter(id=todo_id).exists())


# ─── WFTool ───────────────────────────────────────────────────────────────

class WFToolTest(SDTATestCase):

    def test_create(self):
        wf = self.make_workflow()
        equipment = self.make_equipment(name='Multimeter')
        tool = WFTool.objects.create(workflow=wf, equipment=equipment)
        self.assertEqual(tool.workflow, wf)
        self.assertEqual(tool.equipment, equipment)

    def test_str(self):
        wf = self.make_workflow(name='Str WF')
        equipment = self.make_equipment(name='Str Equipment')
        tool = WFTool.objects.create(workflow=wf, equipment=equipment)
        result = str(tool)
        self.assertIn('Str WF', result)
        self.assertIn('Str Equipment', result)

    def test_unique_workflow_equipment(self):
        from django.db import IntegrityError
        wf = self.make_workflow()
        equipment = self.make_equipment()
        WFTool.objects.create(workflow=wf, equipment=equipment)
        with self.assertRaises(IntegrityError):
            WFTool.objects.create(workflow=wf, equipment=equipment)

    def test_delete(self):
        wf = self.make_workflow()
        equipment = self.make_equipment()
        tool = WFTool.objects.create(workflow=wf, equipment=equipment)
        tool_id = tool.id
        tool.delete()
        self.assertFalse(WFTool.objects.filter(id=tool_id).exists())


# ─── WFInventory ──────────────────────────────────────────────────────────

class WFInventoryTest(SDTATestCase):

    def test_create(self):
        wf = self.make_workflow()
        product = self.make_product(name='Filter')
        inv = WFInventory.objects.create(
            workflow=wf, product=product, quantity_required=5
        )
        self.assertEqual(float(inv.quantity_required), 5.0)

    def test_str(self):
        wf = self.make_workflow()
        product = self.make_product(name='Str Product')
        inv = WFInventory.objects.create(workflow=wf, product=product, quantity_required=2)
        result = str(inv)
        self.assertIn('Str Product', result)
        self.assertIn('2', result)

    def test_quantity_default_one(self):
        wf = self.make_workflow()
        product = self.make_product()
        inv = WFInventory.objects.create(workflow=wf, product=product)
        self.assertEqual(float(inv.quantity_required), 1.0)

    def test_unique_workflow_product(self):
        from django.db import IntegrityError
        wf = self.make_workflow()
        product = self.make_product()
        WFInventory.objects.create(workflow=wf, product=product)
        with self.assertRaises(IntegrityError):
            WFInventory.objects.create(workflow=wf, product=product, quantity_required=2)

    def test_delete(self):
        wf = self.make_workflow()
        product = self.make_product()
        inv = WFInventory.objects.create(workflow=wf, product=product)
        inv_id = inv.id
        inv.delete()
        self.assertFalse(WFInventory.objects.filter(id=inv_id).exists())


# ─── WFSafetyForm ────────────────────────────────────────────────────────

class WFSafetyFormTest(SDTATestCase):

    def test_create(self):
        wf = self.make_workflow()
        form = self.make_safety_form(form_name='Pre-Work Safety')
        wf_form = WFSafetyForm.objects.create(workflow=wf, safety_form=form)
        self.assertEqual(wf_form.workflow, wf)
        self.assertEqual(wf_form.safety_form, form)

    def test_str(self):
        wf = self.make_workflow(name='Str WF')
        form = self.make_safety_form(form_name='Str Form')
        wf_form = WFSafetyForm.objects.create(workflow=wf, safety_form=form)
        result = str(wf_form)
        self.assertIn('Str WF', result)
        self.assertIn('Str Form', result)

    def test_unique_workflow_safety_form(self):
        from django.db import IntegrityError
        wf = self.make_workflow()
        form = self.make_safety_form()
        WFSafetyForm.objects.create(workflow=wf, safety_form=form)
        with self.assertRaises(IntegrityError):
            WFSafetyForm.objects.create(workflow=wf, safety_form=form)

    def test_delete(self):
        wf = self.make_workflow()
        form = self.make_safety_form()
        wf_form = WFSafetyForm.objects.create(workflow=wf, safety_form=form)
        wf_form_id = wf_form.id
        wf_form.delete()
        self.assertFalse(WFSafetyForm.objects.filter(id=wf_form_id).exists())
