# notes/tests.py
# Source: Note & Document Implementation Specification V1
#
# Comprehensive tests for Note and Document models using SDTATestCase.

import uuid
from django.core.exceptions import ValidationError
from django.test import TestCase

from tests.base import SDTATestCase
from .models import (
    Note, Document, FileUploadLog, FileDownloadLog,
    NoteType, ScanStatus, PARENT_FK_FIELDS, ExclusiveArcMixin
)
from .services import create_note, get_notes_for_entity, get_documents_for_entity


# ==============================================================================
# Test ExclusiveArcMixin.clean() validation
# ==============================================================================

class NoteExclusiveArcTestCase(SDTATestCase):
    """Test Note exclusive arc constraint validation."""

    def test_note_creation_with_single_parent_fk(self):
        """Note should be created successfully with exactly one parent FK set."""
        customer = self.make_customer()
        note = Note.objects.create(
            tenant_id=self.tenant_id,
            note_type=NoteType.INTERNAL_NOTE,
            body="Test note",
            customer=customer,
            created_by="Test User",
            updated_by="Test User",
        )
        self.assertIsNotNone(note.pk)
        self.assertEqual(note.customer_id, customer.id)

    def test_note_fails_with_no_parent_fk(self):
        """Note creation should fail if no parent FK is set."""
        with self.assertRaises(ValidationError) as ctx:
            Note.objects.create(
                tenant_id=self.tenant_id,
                note_type=NoteType.INTERNAL_NOTE,
                body="Test note",
                created_by="Test User",
                updated_by="Test User",
            )
        self.assertIn("must be attached to exactly one parent entity", str(ctx.exception))

    def test_note_fails_with_multiple_parent_fks(self):
        """Note creation should fail if multiple parent FKs are set."""
        customer = self.make_customer()
        contact = self.make_contact()

        with self.assertRaises(ValidationError) as ctx:
            Note.objects.create(
                tenant_id=self.tenant_id,
                note_type=NoteType.INTERNAL_NOTE,
                body="Test note",
                customer=customer,
                contact=contact,
                created_by="Test User",
                updated_by="Test User",
            )
        self.assertIn("cannot be attached to multiple parent entities", str(ctx.exception))

    def test_note_type_enum_values(self):
        """Test all NoteType enum values are correctly defined."""
        expected = {
            'internal_note': 'Internal Note',
            'call': 'Call',
            'email': 'Email',
            'site_visit': 'Site Visit',
            'customer_comment': 'Customer Comment',
            'reminder': 'Reminder',
        }
        for value, label in expected.items():
            self.assertIn(value, NoteType.values)
            self.assertEqual(NoteType.choices_dict[value], label)

    def test_note_with_work_order_parent(self):
        """Test Note can be attached to work_order."""
        work_order = self.make_work_order()
        note = Note.objects.create(
            tenant_id=self.tenant_id,
            note_type=NoteType.CALL,
            body="Customer called about delays",
            work_order=work_order,
            created_by="Support Agent",
            updated_by="Support Agent",
        )
        self.assertEqual(note.work_order_id, work_order.id)

    def test_note_with_user_parent(self):
        """Test Note can be attached to user."""
        user = self.make_user()
        note = Note.objects.create(
            tenant_id=self.tenant_id,
            note_type=NoteType.REMINDER,
            body="Follow up with this user",
            user=user,
            created_by="System",
            updated_by="System",
        )
        self.assertEqual(note.user_id, user.id)

    def test_note_with_vendor_parent(self):
        """Test Note can be attached to vendor."""
        vendor = self.make_vendor()
        note = Note.objects.create(
            tenant_id=self.tenant_id,
            note_type=NoteType.INTERNAL_NOTE,
            body="Vendor performance review",
            vendor=vendor,
            created_by="Manager",
            updated_by="Manager",
        )
        self.assertEqual(note.vendor_id, vendor.id)


# ==============================================================================
# Test Document file metadata immutability
# ==============================================================================

class DocumentFileMetadataTestCase(SDTATestCase):
    """Test Document model file metadata immutability."""

    def test_document_creation_with_file_metadata(self):
        """Document should be created with file metadata."""
        customer = self.make_customer()
        doc = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="contract.pdf",
            file_key="s3://bucket/path/contract.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            sha256_hash="abc123def456",
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )
        self.assertEqual(doc.original_filename, "contract.pdf")
        self.assertEqual(doc.file_key, "s3://bucket/path/contract.pdf")
        self.assertEqual(doc.file_size_bytes, 102400)
        self.assertEqual(doc.mime_type, "application/pdf")
        self.assertEqual(doc.sha256_hash, "abc123def456")

    def test_document_file_key_immutable_after_save(self):
        """file_key cannot be modified after creation."""
        customer = self.make_customer()
        doc = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="contract.pdf",
            file_key="s3://bucket/path/contract.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            sha256_hash="abc123def456",
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )

        # Try to modify file_key
        doc.file_key = "s3://bucket/path/different.pdf"
        with self.assertRaises(ValidationError) as ctx:
            doc.save()
        self.assertIn("Cannot modify file_key", str(ctx.exception))

    def test_document_original_filename_immutable_after_save(self):
        """original_filename cannot be modified after creation."""
        customer = self.make_customer()
        doc = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="contract.pdf",
            file_key="s3://bucket/path/contract.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            sha256_hash="abc123def456",
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )

        # Try to modify original_filename
        doc.original_filename = "different.pdf"
        with self.assertRaises(ValidationError) as ctx:
            doc.save()
        self.assertIn("Cannot modify original_filename", str(ctx.exception))

    def test_document_file_size_bytes_immutable_after_save(self):
        """file_size_bytes cannot be modified after creation."""
        customer = self.make_customer()
        doc = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="contract.pdf",
            file_key="s3://bucket/path/contract.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            sha256_hash="abc123def456",
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )

        # Try to modify file_size_bytes
        doc.file_size_bytes = 204800
        with self.assertRaises(ValidationError) as ctx:
            doc.save()
        self.assertIn("Cannot modify file_size_bytes", str(ctx.exception))

    def test_document_mime_type_immutable_after_save(self):
        """mime_type cannot be modified after creation."""
        customer = self.make_customer()
        doc = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="contract.pdf",
            file_key="s3://bucket/path/contract.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            sha256_hash="abc123def456",
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )

        # Try to modify mime_type
        doc.mime_type = "text/plain"
        with self.assertRaises(ValidationError) as ctx:
            doc.save()
        self.assertIn("Cannot modify mime_type", str(ctx.exception))

    def test_document_sha256_hash_immutable_after_save(self):
        """sha256_hash cannot be modified after creation."""
        customer = self.make_customer()
        doc = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="contract.pdf",
            file_key="s3://bucket/path/contract.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            sha256_hash="abc123def456",
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )

        # Try to modify sha256_hash
        doc.sha256_hash = "xyz789new"
        with self.assertRaises(ValidationError) as ctx:
            doc.save()
        self.assertIn("Cannot modify sha256_hash", str(ctx.exception))

    def test_document_scan_status_can_be_updated(self):
        """scan_status is mutable and can be updated after creation."""
        customer = self.make_customer()
        doc = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="contract.pdf",
            file_key="s3://bucket/path/contract.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            sha256_hash="abc123def456",
            scan_status=ScanStatus.PENDING,
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )
        self.assertEqual(doc.scan_status, ScanStatus.PENDING)

        # Update scan_status — this should succeed
        doc.scan_status = ScanStatus.CLEAN
        doc.save()

        # Verify the update persisted
        doc_refreshed = Document.objects.get(pk=doc.pk)
        self.assertEqual(doc_refreshed.scan_status, ScanStatus.CLEAN)


# ==============================================================================
# Test FileUploadLog model
# ==============================================================================

class FileUploadLogTestCase(SDTATestCase):
    """Test FileUploadLog model."""

    def test_file_upload_log_success(self):
        """FileUploadLog can record a successful upload."""
        customer = self.make_customer()
        doc = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="contract.pdf",
            file_key="s3://bucket/path/contract.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            sha256_hash="abc123def456",
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )

        log = FileUploadLog.objects.create(
            tenant_id=self.tenant_id,
            document=doc,
            entity_type='customer',
            entity_id=customer.id,
            original_filename="contract.pdf",
            file_size_bytes=102400,
            status=FileUploadLog.StatusChoices.SUCCESS,
            created_by="Admin",
            updated_by="Admin",
        )
        self.assertEqual(log.status, FileUploadLog.StatusChoices.SUCCESS)
        self.assertEqual(log.document, doc)

    def test_file_upload_log_failure(self):
        """FileUploadLog can record a failed upload."""
        customer = self.make_customer()

        log = FileUploadLog.objects.create(
            tenant_id=self.tenant_id,
            document=None,
            entity_type='customer',
            entity_id=customer.id,
            original_filename="corrupted.pdf",
            file_size_bytes=None,
            status=FileUploadLog.StatusChoices.FAILED,
            failure_reason="File was corrupted during upload",
            ip_address="192.168.1.1",
            created_by="System",
            updated_by="System",
        )
        self.assertEqual(log.status, FileUploadLog.StatusChoices.FAILED)
        self.assertIn("corrupted", log.failure_reason)


# ==============================================================================
# Test FileDownloadLog immutability
# ==============================================================================

class FileDownloadLogImmutabilityTestCase(SDTATestCase):
    """Test FileDownloadLog immutability."""

    def test_file_download_log_immutable(self):
        """FileDownloadLog cannot be modified after creation."""
        customer = self.make_customer()
        doc = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="contract.pdf",
            file_key="s3://bucket/path/contract.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            sha256_hash="abc123def456",
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )

        log = FileDownloadLog.objects.create(
            tenant_id=self.tenant_id,
            user_id=uuid.uuid4(),
            user_display="John Doe",
            document=doc,
            entity_type='customer',
            entity_id=customer.id,
            ip_address="192.168.1.1",
        )

        # Try to modify — should raise
        log.user_display = "Jane Doe"
        with self.assertRaises(ValidationError) as ctx:
            log.save()
        self.assertIn("immutable", str(ctx.exception))

    def test_file_download_log_cannot_be_deleted(self):
        """FileDownloadLog cannot be deleted."""
        customer = self.make_customer()
        doc = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="contract.pdf",
            file_key="s3://bucket/path/contract.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            sha256_hash="abc123def456",
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )

        log = FileDownloadLog.objects.create(
            tenant_id=self.tenant_id,
            user_id=uuid.uuid4(),
            user_display="John Doe",
            document=doc,
            entity_type='customer',
            entity_id=customer.id,
            ip_address="192.168.1.1",
        )

        # Try to delete — should raise
        with self.assertRaises(ValidationError) as ctx:
            log.delete()
        self.assertIn("immutable", str(ctx.exception))


# ==============================================================================
# Test service functions
# ==============================================================================

class CreateNoteServiceTestCase(SDTATestCase):
    """Test create_note service function."""

    def test_create_note_service_with_customer(self):
        """create_note should create a Note with customer FK."""
        customer = self.make_customer()

        note = create_note(
            tenant_id=self.tenant_id,
            note_type=NoteType.CALL,
            body="Customer called about account",
            parent_field='customer',
            parent_id=customer.id,
            user_display="Support Agent",
        )

        self.assertIsNotNone(note.pk)
        self.assertEqual(note.customer_id, customer.id)
        self.assertEqual(note.created_by, "Support Agent")

    def test_create_note_service_with_work_order(self):
        """create_note should create a Note with work_order FK."""
        work_order = self.make_work_order()

        note = create_note(
            tenant_id=self.tenant_id,
            note_type=NoteType.INTERNAL_NOTE,
            body="Technician will arrive at 10am",
            parent_field='work_order',
            parent_id=work_order.id,
            user_display="Dispatcher",
        )

        self.assertIsNotNone(note.pk)
        self.assertEqual(note.work_order_id, work_order.id)

    def test_create_note_service_with_invalid_parent_field(self):
        """create_note should raise ValidationError for invalid parent_field."""
        customer = self.make_customer()

        with self.assertRaises(ValidationError) as ctx:
            create_note(
                tenant_id=self.tenant_id,
                note_type=NoteType.CALL,
                body="Test",
                parent_field='invalid_entity',
                parent_id=customer.id,
            )
        self.assertIn("Invalid parent_field", str(ctx.exception))

    def test_create_note_service_normalizes_parent_field(self):
        """create_note should strip '_id' suffix from parent_field."""
        customer = self.make_customer()

        note = create_note(
            tenant_id=self.tenant_id,
            note_type=NoteType.INTERNAL_NOTE,
            body="Test note",
            parent_field='customer_id',  # With _id suffix
            parent_id=customer.id,
        )

        self.assertEqual(note.customer_id, customer.id)


# ==============================================================================
# Test get_notes_for_entity service function
# ==============================================================================

class GetNotesForEntityTestCase(SDTATestCase):
    """Test get_notes_for_entity service function."""

    def test_get_notes_for_customer(self):
        """get_notes_for_entity should return all notes for a customer."""
        customer = self.make_customer()

        # Create multiple notes for same customer
        note1 = create_note(
            tenant_id=self.tenant_id,
            note_type=NoteType.CALL,
            body="First call",
            parent_field='customer',
            parent_id=customer.id,
        )
        note2 = create_note(
            tenant_id=self.tenant_id,
            note_type=NoteType.EMAIL,
            body="Follow-up email",
            parent_field='customer',
            parent_id=customer.id,
        )

        notes = get_notes_for_entity('customer', customer.id, self.tenant_id)
        self.assertEqual(notes.count(), 2)
        self.assertIn(note1, notes)
        self.assertIn(note2, notes)

    def test_get_notes_for_entity_ordered_by_created_on_desc(self):
        """get_notes_for_entity should return notes ordered by created_on desc."""
        customer = self.make_customer()

        note1 = create_note(
            tenant_id=self.tenant_id,
            note_type=NoteType.CALL,
            body="First",
            parent_field='customer',
            parent_id=customer.id,
        )
        note2 = create_note(
            tenant_id=self.tenant_id,
            note_type=NoteType.EMAIL,
            body="Second",
            parent_field='customer',
            parent_id=customer.id,
        )

        notes = list(get_notes_for_entity('customer', customer.id, self.tenant_id))
        # note2 created after note1, so should appear first in descending order
        self.assertEqual(notes[0].id, note2.id)
        self.assertEqual(notes[1].id, note1.id)

    def test_get_notes_for_entity_invalid_type(self):
        """get_notes_for_entity should raise for invalid entity_type."""
        customer = self.make_customer()

        with self.assertRaises(ValidationError) as ctx:
            get_notes_for_entity('invalid_type', customer.id, self.tenant_id)
        self.assertIn("Invalid entity_type", str(ctx.exception))


# ==============================================================================
# Test get_documents_for_entity service function
# ==============================================================================

class GetDocumentsForEntityTestCase(SDTATestCase):
    """Test get_documents_for_entity service function."""

    def test_get_clean_documents_for_entity(self):
        """get_documents_for_entity should return only CLEAN documents."""
        customer = self.make_customer()

        # Create documents with different scan statuses
        doc_clean = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="contract.pdf",
            file_key="s3://bucket/contract.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            sha256_hash="abc123",
            scan_status=ScanStatus.CLEAN,
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )
        doc_pending = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="pending.pdf",
            file_key="s3://bucket/pending.pdf",
            file_size_bytes=51200,
            mime_type="application/pdf",
            sha256_hash="def456",
            scan_status=ScanStatus.PENDING,
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )
        doc_infected = Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="infected.pdf",
            file_key="s3://bucket/infected.pdf",
            file_size_bytes=204800,
            mime_type="application/pdf",
            sha256_hash="ghi789",
            scan_status=ScanStatus.INFECTED,
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )

        docs = get_documents_for_entity('customer', customer.id, self.tenant_id)
        self.assertEqual(docs.count(), 1)
        self.assertEqual(docs[0].id, doc_clean.id)

    def test_get_documents_for_entity_empty_when_no_clean(self):
        """get_documents_for_entity should return empty if no CLEAN documents."""
        customer = self.make_customer()

        # Create only non-clean documents
        Document.objects.create(
            tenant_id=self.tenant_id,
            original_filename="pending.pdf",
            file_key="s3://bucket/pending.pdf",
            file_size_bytes=51200,
            mime_type="application/pdf",
            sha256_hash="def456",
            scan_status=ScanStatus.PENDING,
            customer=customer,
            created_by="Admin",
            updated_by="Admin",
        )

        docs = get_documents_for_entity('customer', customer.id, self.tenant_id)
        self.assertEqual(docs.count(), 0)
