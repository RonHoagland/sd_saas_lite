"""
Regression tests for /api/v1/documents/ endpoints.

These guard the security invariant that `file_key` (the raw storage path) is
NEVER exposed in API responses, per:

  - File Upload Specification V1, §5.3
  - Note & Document Implementation Specification V1, §3.5

Clients receive download URLs from the storage layer; they must never see or
construct storage paths themselves.
"""

import uuid

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from config.tenant_context import set_current_tenant_id, clear_current_tenant_id
from crm.models import Person, Customer
from documents.api import DocumentSerializer
from documents.models import Document, ScanStatus
from infrastructure.models import TenantState
from users.models import User


def _make_tenant(prefix='docapi'):
    return TenantState.objects.create(
        subdomain=f'{prefix}-{uuid.uuid4().hex[:8]}',
        company_name=f'{prefix.title()} Corp',
        owner_email=f'owner@{prefix}.com',
        status=TenantState.StatusChoices.ACTIVE,
        tier=TenantState.TierChoices.LITE,
    )


@override_settings(SECURE_SSL_REDIRECT=False)
class DocumentApiFileKeyExposureTest(TestCase):
    """`file_key` must never appear in any /api/v1/documents/ response."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = _make_tenant()

        set_current_tenant_id(str(cls.tenant.id))
        try:
            person = Person.objects.create(first_name='Doc', last_name='Owner')
            cls.user = User.objects.create_user(
                'docowner',
                tenant_id=cls.tenant.id,
                password='DocPass123!',
                email='doc@test.com',
                person=person,
            )
            customer = Customer.objects.create(
                company_name='Test Customer',
                primary_person=person,
            )
            cls.document = Document.objects.create(
                customer=customer,
                original_filename='contract.pdf',
                file_key=f'{cls.tenant.id}/customer/{customer.id}/abc123_contract.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                sha256_hash='a' * 64,
                scan_status=ScanStatus.CLEAN,
            )
        finally:
            clear_current_tenant_id()

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=False)
        self.client.force_authenticate(user=self.user)
        # Establish tenant context so the viewset's queryset can find the document.
        set_current_tenant_id(str(self.tenant.id))

    def tearDown(self):
        clear_current_tenant_id()

    def test_list_endpoint_does_not_expose_file_key(self):
        resp = self.client.get('/api/v1/documents/documents/')
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        # Pagination wrapper {"results": [...]} or raw list — handle either.
        rows = body.get('results', body) if isinstance(body, dict) else body
        self.assertTrue(rows, 'expected at least one document in the list')
        for row in rows:
            self.assertNotIn(
                'file_key', row,
                f'file_key leaked in list response: {row}',
            )

    def test_detail_endpoint_does_not_expose_file_key(self):
        resp = self.client.get(f'/api/v1/documents/documents/{self.document.id}/')
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertNotIn(
            'file_key', body,
            f'file_key leaked in detail response: {body}',
        )

    def test_serializer_class_does_not_declare_file_key(self):
        """Belt-and-braces: contract test against the class itself."""
        self.assertNotIn('file_key', DocumentSerializer.Meta.fields)
        self.assertNotIn('file_key', DocumentSerializer.Meta.read_only_fields)

    def test_detail_response_includes_safe_metadata(self):
        """Removing file_key must not have removed the legitimate metadata."""
        resp = self.client.get(f'/api/v1/documents/documents/{self.document.id}/')
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for safe_field in (
            'id', 'tenant_id', 'original_filename', 'file_size_bytes',
            'mime_type', 'sha256_hash', 'scan_status', 'parent_entity',
        ):
            self.assertIn(safe_field, body, f'expected {safe_field} in response')
