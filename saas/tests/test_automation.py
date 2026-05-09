# tests/test_automation.py
# CRUD and basic functionality tests for all models in the automation app.

from tests.base import SDTATestCase
from automation.models import (
    CommunicationTemplate, CommunicationTrigger, TriggerLog, TriggerTemplate,
)


# ─── CommunicationTrigger ─────────────────────────────────────────────────────

class CommunicationTriggerTest(SDTATestCase):

    def test_create(self):
        ct = CommunicationTrigger.objects.create(
            name='WO Status Changed',
            event_name='work_order.status_changed',
        )
        self.assertEqual(ct.name, 'WO Status Changed')
        self.assertEqual(ct.status, 'Active')
        self.assertEqual(ct.conditions, {})

    def test_str(self):
        ct = CommunicationTrigger.objects.create(
            name='Str Trigger',
            event_name='invoice.sent',
        )
        result = str(ct)
        self.assertIn('Str Trigger', result)
        self.assertIn('invoice.sent', result)

    def test_inactive_status(self):
        ct = CommunicationTrigger.objects.create(
            name='Inactive Trigger',
            event_name='test.event',
            status='Inactive',
        )
        ct.refresh_from_db()
        self.assertEqual(ct.status, 'Inactive')

    def test_conditions_default_empty(self):
        ct = CommunicationTrigger.objects.create(
            name='No Cond Trigger', event_name='test.no_cond'
        )
        self.assertEqual(ct.conditions, {})

    def test_conditions_set(self):
        conditions = {'status': 'Completed', 'amount_gt': 100}
        ct = CommunicationTrigger.objects.create(
            name='Cond Trigger', event_name='test.cond',
            conditions=conditions,
        )
        ct.refresh_from_db()
        self.assertEqual(ct.conditions['status'], 'Completed')
        self.assertEqual(ct.conditions['amount_gt'], 100)

    def test_description_optional(self):
        ct = CommunicationTrigger.objects.create(
            name='No Desc', event_name='test.nodesc'
        )
        self.assertEqual(ct.description, '')

    def test_update_event_name(self):
        ct = CommunicationTrigger.objects.create(
            name='Upd Trigger', event_name='old.event'
        )
        ct.event_name = 'new.event'
        ct.save()
        ct.refresh_from_db()
        self.assertEqual(ct.event_name, 'new.event')

    def test_delete(self):
        ct = CommunicationTrigger.objects.create(
            name='Del Trigger', event_name='del.event'
        )
        ct_id = ct.id
        ct.delete()
        self.assertFalse(CommunicationTrigger.objects.filter(id=ct_id).exists())


# ─── CommunicationTemplate ────────────────────────────────────────────────────

class CommunicationTemplateTest(SDTATestCase):

    def test_create(self):
        tmpl = CommunicationTemplate.objects.create(
            name='WO Completed Email',
            body='Your work order {{wo_number}} has been completed.',
        )
        self.assertEqual(tmpl.name, 'WO Completed Email')
        self.assertEqual(tmpl.channel, 'Email')
        self.assertEqual(tmpl.status, 'Active')

    def test_str(self):
        tmpl = CommunicationTemplate.objects.create(
            name='Str Template', body='Test body'
        )
        result = str(tmpl)
        self.assertIn('Str Template', result)
        self.assertIn('Email', result)

    def test_channel_choices(self):
        for channel in ('Email', 'SMS', 'Push', 'In-App'):
            t = CommunicationTemplate.objects.create(
                name=f'Ch {channel}', channel=channel, body=f'{channel} body'
            )
            t.refresh_from_db()
            self.assertEqual(t.channel, channel)
            t.delete()

    def test_inactive_status(self):
        tmpl = CommunicationTemplate.objects.create(
            name='Inactive Tmpl', body='Body', status='Inactive'
        )
        tmpl.refresh_from_db()
        self.assertEqual(tmpl.status, 'Inactive')

    def test_subject_optional(self):
        tmpl = CommunicationTemplate.objects.create(
            name='No Subject', body='SMS body', channel='SMS'
        )
        self.assertEqual(tmpl.subject, '')

    def test_from_fields_optional(self):
        tmpl = CommunicationTemplate.objects.create(name='No From', body='Body')
        self.assertEqual(tmpl.from_name, '')
        self.assertEqual(tmpl.from_email, '')

    def test_from_fields_set(self):
        tmpl = CommunicationTemplate.objects.create(
            name='From Fields',
            body='Body',
            from_name='ACME Corp',
            from_email='no-reply@acme.com',
        )
        tmpl.refresh_from_db()
        self.assertEqual(tmpl.from_name, 'ACME Corp')
        self.assertEqual(tmpl.from_email, 'no-reply@acme.com')

    def test_update_body(self):
        tmpl = CommunicationTemplate.objects.create(name='Upd Tmpl', body='Old body')
        tmpl.body = 'New body content'
        tmpl.save()
        tmpl.refresh_from_db()
        self.assertEqual(tmpl.body, 'New body content')

    def test_delete(self):
        tmpl = CommunicationTemplate.objects.create(name='Del Tmpl', body='Del body')
        tmpl_id = tmpl.id
        tmpl.delete()
        self.assertFalse(CommunicationTemplate.objects.filter(id=tmpl_id).exists())


# ─── TriggerTemplate ──────────────────────────────────────────────────────────

class TriggerTemplateTest(SDTATestCase):

    def _make_trigger_and_template(self, suffix=''):
        trigger = CommunicationTrigger.objects.create(
            name=f'TT Trigger{suffix}', event_name=f'tt.event{suffix}'
        )
        template = CommunicationTemplate.objects.create(
            name=f'TT Template{suffix}', body='Body'
        )
        return trigger, template

    def test_create(self):
        trigger, template = self._make_trigger_and_template()
        tt = TriggerTemplate.objects.create(trigger=trigger, template=template)
        self.assertTrue(tt.is_active)
        self.assertEqual(tt.delay_minutes, 0)

    def test_str(self):
        trigger, template = self._make_trigger_and_template(suffix=' Str')
        tt = TriggerTemplate.objects.create(trigger=trigger, template=template)
        result = str(tt)
        self.assertIn('TT Trigger Str', result)
        self.assertIn('TT Template Str', result)

    def test_delay_minutes(self):
        trigger, template = self._make_trigger_and_template(suffix=' Delay')
        tt = TriggerTemplate.objects.create(
            trigger=trigger, template=template, delay_minutes=30
        )
        tt.refresh_from_db()
        self.assertEqual(tt.delay_minutes, 30)

    def test_inactive(self):
        trigger, template = self._make_trigger_and_template(suffix=' Inactive')
        tt = TriggerTemplate.objects.create(
            trigger=trigger, template=template, is_active=False
        )
        tt.refresh_from_db()
        self.assertFalse(tt.is_active)

    def test_unique_trigger_template(self):
        from django.db import IntegrityError
        trigger, template = self._make_trigger_and_template(suffix=' Dup')
        TriggerTemplate.objects.create(trigger=trigger, template=template)
        with self.assertRaises(IntegrityError):
            TriggerTemplate.objects.create(trigger=trigger, template=template, delay_minutes=5)

    def test_delete(self):
        trigger, template = self._make_trigger_and_template(suffix=' Del')
        tt = TriggerTemplate.objects.create(trigger=trigger, template=template)
        tt_id = tt.id
        tt.delete()
        self.assertFalse(TriggerTemplate.objects.filter(id=tt_id).exists())

    def test_cascade_delete_with_trigger(self):
        """TriggerTemplate deleted when parent CommunicationTrigger is deleted."""
        trigger, template = self._make_trigger_and_template(suffix=' Cascade')
        tt = TriggerTemplate.objects.create(trigger=trigger, template=template)
        tt_id = tt.id
        trigger.delete()
        self.assertFalse(TriggerTemplate.objects.filter(id=tt_id).exists())


# ─── TriggerLog ───────────────────────────────────────────────────────────────

class TriggerLogTest(SDTATestCase):

    def _make_trigger_template(self):
        trigger = CommunicationTrigger.objects.create(
            name='Log Trigger', event_name='log.event'
        )
        template = CommunicationTemplate.objects.create(
            name='Log Template', body='Log body'
        )
        return TriggerTemplate.objects.create(trigger=trigger, template=template)

    def test_create(self):
        tt = self._make_trigger_template()
        log = TriggerLog.objects.create(
            trigger_template=tt, recipient='customer@example.com'
        )
        self.assertEqual(log.status, 'Pending')
        self.assertEqual(log.recipient, 'customer@example.com')

    def test_str(self):
        tt = self._make_trigger_template()
        log = TriggerLog.objects.create(
            trigger_template=tt, recipient='str@example.com', status='Sent'
        )
        result = str(log)
        self.assertIn('str@example.com', result)
        self.assertIn('Sent', result)

    def test_status_choices(self):
        tt = self._make_trigger_template()
        for status in ('Pending', 'Sent', 'Failed', 'Skipped'):
            log = TriggerLog.objects.create(
                trigger_template=tt, recipient='test@example.com', status=status
            )
            log.refresh_from_db()
            self.assertEqual(log.status, status)
            log.delete()

    def test_trigger_template_optional(self):
        """TriggerLog can exist without a TriggerTemplate (SET_NULL)."""
        tt = self._make_trigger_template()
        log = TriggerLog.objects.create(trigger_template=tt, recipient='orphan@example.com')
        tt.delete()
        log.refresh_from_db()
        self.assertIsNone(log.trigger_template)

    def test_sent_at_optional(self):
        tt = self._make_trigger_template()
        log = TriggerLog.objects.create(trigger_template=tt, recipient='test@example.com')
        self.assertIsNone(log.sent_at)

    def test_error_message_optional(self):
        tt = self._make_trigger_template()
        log = TriggerLog.objects.create(trigger_template=tt, recipient='test@example.com')
        self.assertEqual(log.error_message, '')

    def test_context_snapshot_default_empty(self):
        tt = self._make_trigger_template()
        log = TriggerLog.objects.create(trigger_template=tt, recipient='test@example.com')
        self.assertEqual(log.context_snapshot, {})

    def test_context_snapshot_set(self):
        tt = self._make_trigger_template()
        ctx = {'wo_number': 'WO-0001', 'customer': 'ACME'}
        log = TriggerLog.objects.create(
            trigger_template=tt, recipient='ctx@example.com', context_snapshot=ctx
        )
        log.refresh_from_db()
        self.assertEqual(log.context_snapshot['wo_number'], 'WO-0001')

    def test_update_status(self):
        tt = self._make_trigger_template()
        log = TriggerLog.objects.create(trigger_template=tt, recipient='upd@example.com')
        log.status = 'Failed'
        log.error_message = 'SMTP timeout'
        log.save()
        log.refresh_from_db()
        self.assertEqual(log.status, 'Failed')
        self.assertEqual(log.error_message, 'SMTP timeout')

    def test_delete(self):
        tt = self._make_trigger_template()
        log = TriggerLog.objects.create(trigger_template=tt, recipient='del@example.com')
        log_id = log.id
        log.delete()
        self.assertFalse(TriggerLog.objects.filter(id=log_id).exists())
