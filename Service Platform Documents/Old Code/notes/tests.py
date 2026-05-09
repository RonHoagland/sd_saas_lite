from django.test import TestCase
from django.core.exceptions import ValidationError
from core.test_base import CoreTestCase
from notes.models import Note, NoteLink
from clients.models import Client
from value_lists.models import ValueList

from numbering.models import NumberingRule, NumberSequence

class NoteModelTest(CoreTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.note_type_list = cls.create_value_list('Note Type', 'note_type', ['General', 'Meeting'])
        
        # Setup Numbering Rule for Client creation
        cls.rule = NumberingRule.objects.create(
            entity_type='clients',
            prefix='AC',
            include_year=True,
            sequence_length=3,
            created_by=cls.admin_user,
            updated_by=cls.admin_user
        )
        NumberSequence.objects.create(rule=cls.rule, current_value=0)
        
        # Need a client to link to
        cls.linked_client = Client.objects.create(
            name="Linked Client",
            client_type="Commercial",
             created_by=cls.worker_user,
            updated_by=cls.worker_user
        )

    def test_link_constraints_one_parent(self):
        """Test NoteLink must have exactly one parent (Client OR Contact)"""
        note = Note.objects.create(note_text="Orphan Link", note_type="General", created_by=self.worker_user, updated_by=self.worker_user)
        
        # 0 Parents -> Fail
        link = NoteLink(note=note, created_by=self.worker_user, updated_by=self.worker_user)
        with self.assertRaises(ValidationError):
            link.clean()
            
        # 1 Parent -> Success
        link.client = self.linked_client
        link.clean() # Should pass
        link.save()
        
    def test_multiple_links_per_note(self):
        """
        Verify multiple links ARE possible at Model level (Pro Runway).
        Lite restriction is UI/Logic level.
        """
        note = Note.objects.create(note_text="Multi Link", note_type="General", created_by=self.worker_user, updated_by=self.worker_user)
        
        # Link 1
        NoteLink.objects.create(note=note, client=self.linked_client, created_by=self.worker_user, updated_by=self.worker_user)
        
        # Link 2 (to same client? or different? NoteLink allows linking to same parent multiple times?
        # Unique constraints might prevent same parent. 
        # But different parent (e.g. Contact) is definitely allowed.
        # Since I don't have a contact easily, I'll attempt another link to the SAME client?
        # Model doesn't have unique_together yet.
        
        link2 = NoteLink(note=note, client=self.linked_client, created_by=self.worker_user, updated_by=self.worker_user)
        try:
            link2.save() # Should succeed
        except Exception as e:
            self.fail(f"Model prevented multiple links: {e}")
