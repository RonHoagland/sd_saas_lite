"""
Tests for the database-level CHECK constraint enforcing the 25-FK
exclusive arc on Note and Document.

Until the constraint landed, the exclusive arc was only enforced in
Python (`ExclusiveArcMixin.clean()`). A raw INSERT or any code path
that bypassed `.save() -> .full_clean()` could create rows with zero
or multiple parents. These tests use `transaction.atomic()` savepoints
+ raw SQL / `bulk_create` to confirm the database now rejects bad rows
even when Python validation is bypassed.

Per Note & Document Implementation Specification V1 §2.2 / §3.2.
"""

import uuid

from django.db import IntegrityError, connection, transaction

from crm.models import Person, Customer
from documents.models import Document, ScanStatus
from notes.models import Note, NoteType
from tests.base import SDTATestCase


class NoteExclusiveArcDbConstraintTest(SDTATestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Keep tenant context set so model saves work for the valid case.
        cls.person = Person.all_objects.create(
            tenant_id=cls.tenant_id,
            first_name='Arc', last_name='Test',
        )
        cls.customer = Customer.all_objects.create(
            tenant_id=cls.tenant_id,
            company_name='Arc Corp',
            primary_person=cls.person,
        )
        cls.contact = None  # not needed for these tests

    def _insert_note_raw(self, **fk_kwargs):
        """Insert a note via raw SQL, bypassing ExclusiveArcMixin.clean().

        fk_kwargs maps FK column name (e.g. 'customer_id') to UUID.
        Columns not supplied are left NULL.
        """
        fk_columns = sorted(fk_kwargs.keys())
        cols = ['id', 'tenant_id', 'note_type', 'body',
                'created_by', 'created_on', 'updated_by', 'updated_on',
                *fk_columns]
        placeholders = ','.join(['%s'] * len(cols))
        params = [
            str(uuid.uuid4()),                 # id
            str(self.tenant_id),               # tenant_id
            NoteType.INTERNAL_NOTE,            # note_type
            'arc test',                        # body
            'system', 'now()', 'system', 'now()',
            *(str(fk_kwargs[c]) for c in fk_columns),
        ]
        # Build a parameterised SQL fragment. We have to use NOW() for
        # the timestamp columns rather than %s because we're constructing
        # raw SQL; the simplest way is to inline them.
        col_list = ','.join(cols)
        sql = (
            f'INSERT INTO notes_note ({col_list}) '
            f'VALUES ({placeholders})'
        )
        # Replace the literal 'now()' string params with SQL-side defaults.
        # Easiest path: use a different INSERT shape per row.
        with connection.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO notes_note "
                f"(id, tenant_id, note_type, body, "
                f"created_by, created_on, updated_by, updated_on"
                + (',' + ','.join(fk_columns) if fk_columns else '') +
                f") VALUES (%s, %s, %s, %s, %s, NOW(), %s, NOW()"
                + (',' + ','.join(['%s'] * len(fk_columns)) if fk_columns else '') +
                f")",
                [
                    str(uuid.uuid4()),
                    str(self.tenant_id),
                    NoteType.INTERNAL_NOTE,
                    'arc test',
                    'system',
                    'system',
                    *(str(fk_kwargs[c]) for c in fk_columns),
                ],
            )

    def test_zero_parents_rejected_by_db(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._insert_note_raw()

    def test_two_parents_rejected_by_db(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._insert_note_raw(
                    customer_id=self.customer.id,
                    asset_id=uuid.uuid4(),
                )

    def test_three_parents_rejected_by_db(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._insert_note_raw(
                    customer_id=self.customer.id,
                    asset_id=uuid.uuid4(),
                    invoice_id=uuid.uuid4(),
                )

    def test_exactly_one_parent_accepted(self):
        # No exception expected.
        self._insert_note_raw(customer_id=self.customer.id)
        self.assertTrue(
            Note.all_objects.filter(
                customer=self.customer, body='arc test',
            ).exists(),
        )

    def test_orm_save_with_one_parent_still_works(self):
        """The constraint must coexist with the normal model save path."""
        note = Note.objects.create(
            customer=self.customer,
            note_type=NoteType.INTERNAL_NOTE,
            body='via ORM',
        )
        self.assertEqual(note.customer_id, self.customer.id)


class DocumentExclusiveArcDbConstraintTest(SDTATestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.person = Person.all_objects.create(
            tenant_id=cls.tenant_id,
            first_name='Arc', last_name='Doc',
        )
        cls.customer = Customer.all_objects.create(
            tenant_id=cls.tenant_id,
            company_name='Doc Arc Corp',
            primary_person=cls.person,
        )

    def _insert_doc_raw(self, **fk_kwargs):
        fk_columns = sorted(fk_kwargs.keys())
        with connection.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO documents_document "
                f"(id, tenant_id, original_filename, file_key, "
                f"file_size_bytes, mime_type, sha256_hash, scan_status, "
                f"created_by, created_on, updated_by, updated_on"
                + (',' + ','.join(fk_columns) if fk_columns else '') +
                f") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, NOW()"
                + (',' + ','.join(['%s'] * len(fk_columns)) if fk_columns else '') +
                f")",
                [
                    str(uuid.uuid4()),
                    str(self.tenant_id),
                    'arc.pdf',
                    f'{self.tenant_id}/customer/{uuid.uuid4()}/abc.pdf',
                    10,
                    'application/pdf',
                    'a' * 64,
                    ScanStatus.CLEAN,
                    'system',
                    'system',
                    *(str(fk_kwargs[c]) for c in fk_columns),
                ],
            )

    def test_zero_parents_rejected_by_db(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._insert_doc_raw()

    def test_two_parents_rejected_by_db(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._insert_doc_raw(
                    customer_id=self.customer.id,
                    asset_id=uuid.uuid4(),
                )

    def test_exactly_one_parent_accepted(self):
        self._insert_doc_raw(customer_id=self.customer.id)
        self.assertTrue(
            Document.all_objects.filter(
                customer=self.customer, original_filename='arc.pdf',
            ).exists(),
        )

    def test_orm_save_with_one_parent_still_works(self):
        doc = Document.objects.create(
            customer=self.customer,
            original_filename='ok.pdf',
            file_key=f'{self.tenant_id}/customer/{self.customer.id}/ok.pdf',
            file_size_bytes=10,
            mime_type='application/pdf',
            sha256_hash='b' * 64,
            scan_status=ScanStatus.CLEAN,
        )
        self.assertEqual(doc.customer_id, self.customer.id)
