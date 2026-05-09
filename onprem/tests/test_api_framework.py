# tests/test_api_framework.py
# Tests for API serializers, permissions, exception handler, and pagination.

import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase, RequestFactory, override_settings
from rest_framework import status as drf_status
from rest_framework.exceptions import (
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError as DRFValidationError,
)
from rest_framework.test import APIRequestFactory

from api.exceptions import sdta_exception_handler, _status_to_code, _get_message
from api.pagination import StandardPagination, LargePagination, SmallPagination
from api.permissions import IsTenantUser, IsReadOnly, IsTenantAdmin
from api.base import (
    TenantModelSerializer,
    ReadOnlyTenantSerializer,
    ImmutableModelSerializer,
)
from config.tenant_context import set_current_tenant_id, clear_current_tenant_id


# ═══════════════════════════════════════════════════════════════════════════════
# Permissions
# ═══════════════════════════════════════════════════════════════════════════════

class IsTenantUserPermissionTest(TestCase):
    """IsTenantUser requires authenticated user with tenant context."""

    def setUp(self):
        self.permission = IsTenantUser()
        self.factory = APIRequestFactory()

    def test_anonymous_denied(self):
        request = self.factory.get('/fake/')
        request.user = MagicMock(is_authenticated=False)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_authenticated_without_tenant_context_denied(self):
        clear_current_tenant_id()
        request = self.factory.get('/fake/')
        request.user = MagicMock(is_authenticated=True)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_authenticated_with_tenant_context_allowed(self):
        set_current_tenant_id(str(uuid.uuid4()))
        try:
            request = self.factory.get('/fake/')
            request.user = MagicMock(is_authenticated=True)
            self.assertTrue(self.permission.has_permission(request, None))
        finally:
            clear_current_tenant_id()


class IsReadOnlyPermissionTest(TestCase):
    """IsReadOnly allows only GET, HEAD, OPTIONS."""

    def setUp(self):
        self.permission = IsReadOnly()
        self.factory = APIRequestFactory()

    def test_get_allowed(self):
        request = self.factory.get('/fake/')
        self.assertTrue(self.permission.has_permission(request, None))

    def test_head_allowed(self):
        request = self.factory.head('/fake/')
        self.assertTrue(self.permission.has_permission(request, None))

    def test_options_allowed(self):
        request = self.factory.options('/fake/')
        self.assertTrue(self.permission.has_permission(request, None))

    def test_post_denied(self):
        request = self.factory.post('/fake/')
        self.assertFalse(self.permission.has_permission(request, None))

    def test_put_denied(self):
        request = self.factory.put('/fake/')
        self.assertFalse(self.permission.has_permission(request, None))

    def test_patch_denied(self):
        request = self.factory.patch('/fake/')
        self.assertFalse(self.permission.has_permission(request, None))

    def test_delete_denied(self):
        request = self.factory.delete('/fake/')
        self.assertFalse(self.permission.has_permission(request, None))


class IsTenantAdminPermissionTest(TestCase):
    """IsTenantAdmin requires is_tenant_admin attribute on user."""

    def setUp(self):
        self.permission = IsTenantAdmin()
        self.factory = APIRequestFactory()

    def test_anonymous_denied(self):
        request = self.factory.get('/fake/')
        request.user = MagicMock(is_authenticated=False)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_non_admin_denied(self):
        request = self.factory.get('/fake/')
        request.user = MagicMock(is_authenticated=True, is_tenant_admin=False)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_admin_allowed(self):
        request = self.factory.get('/fake/')
        request.user = MagicMock(is_authenticated=True, is_tenant_admin=True)
        self.assertTrue(self.permission.has_permission(request, None))

    def test_user_without_attribute_denied(self):
        request = self.factory.get('/fake/')
        user = MagicMock(is_authenticated=True, spec=[])
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))


# ═══════════════════════════════════════════════════════════════════════════════
# Exception handler
# ═══════════════════════════════════════════════════════════════════════════════

class ExceptionHandlerTest(TestCase):
    """sdta_exception_handler wraps errors in consistent format."""

    def test_django_validation_error_message_dict(self):
        exc = DjangoValidationError({'name': ['Required.']})
        resp = sdta_exception_handler(exc, {})
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(resp.data['error'])
        self.assertEqual(resp.data['code'], 'validation_error')
        self.assertIn('name', resp.data['details'])

    def test_django_validation_error_messages_list(self):
        exc = DjangoValidationError(['Something failed.'])
        resp = sdta_exception_handler(exc, {})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Something failed', resp.data['message'])

    def test_drf_not_found(self):
        exc = NotFound()
        resp = sdta_exception_handler(exc, {})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.data['code'], 'not_found')
        self.assertTrue(resp.data['error'])

    def test_drf_not_authenticated(self):
        exc = NotAuthenticated()
        resp = sdta_exception_handler(exc, {})
        self.assertEqual(resp.status_code, 401 if hasattr(exc, 'status_code') and exc.status_code == 401 else 403)
        self.assertTrue(resp.data['error'])

    def test_drf_permission_denied(self):
        exc = PermissionDenied()
        resp = sdta_exception_handler(exc, {})
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.data['code'], 'forbidden')

    def test_drf_throttled(self):
        exc = Throttled(wait=30)
        resp = sdta_exception_handler(exc, {})
        self.assertEqual(resp.status_code, 429)
        self.assertEqual(resp.data['code'], 'throttled')

    def test_unhandled_exception_returns_none(self):
        resp = sdta_exception_handler(RuntimeError('boom'), {})
        self.assertIsNone(resp)

    def test_status_to_code_known(self):
        self.assertEqual(_status_to_code(400), 'bad_request')
        self.assertEqual(_status_to_code(401), 'unauthorized')
        self.assertEqual(_status_to_code(403), 'forbidden')
        self.assertEqual(_status_to_code(404), 'not_found')
        self.assertEqual(_status_to_code(405), 'method_not_allowed')
        self.assertEqual(_status_to_code(409), 'conflict')
        self.assertEqual(_status_to_code(429), 'throttled')
        self.assertEqual(_status_to_code(500), 'internal_error')

    def test_status_to_code_unknown(self):
        self.assertEqual(_status_to_code(418), 'error_418')

    def test_get_message_dict_with_detail(self):
        self.assertEqual(_get_message({'detail': 'Not found.'}), 'Not found.')

    def test_get_message_dict_field_errors(self):
        msg = _get_message({'name': ['Required.'], 'email': ['Invalid.']})
        self.assertIn('Required.', msg)
        self.assertIn('Invalid.', msg)

    def test_get_message_list(self):
        msg = _get_message(['Error 1', 'Error 2'])
        self.assertIn('Error 1', msg)

    def test_get_message_string(self):
        self.assertEqual(_get_message('plain'), 'plain')


# ═══════════════════════════════════════════════════════════════════════════════
# Pagination
# ═══════════════════════════════════════════════════════════════════════════════

class PaginationConfigTest(TestCase):
    """Verify page size defaults and max limits on all pagination classes."""

    def test_standard_pagination(self):
        p = StandardPagination()
        self.assertEqual(p.page_size, 25)
        self.assertEqual(p.max_page_size, 100)
        self.assertEqual(p.page_size_query_param, 'page_size')

    def test_large_pagination(self):
        p = LargePagination()
        self.assertEqual(p.page_size, 100)
        self.assertEqual(p.max_page_size, 500)

    def test_small_pagination(self):
        p = SmallPagination()
        self.assertEqual(p.page_size, 10)
        self.assertEqual(p.max_page_size, 50)


# ═══════════════════════════════════════════════════════════════════════════════
# Serializers
# ═══════════════════════════════════════════════════════════════════════════════

class ImmutableModelSerializerTest(TestCase):
    """ImmutableModelSerializer blocks create/update."""

    def test_create_raises(self):
        s = ImmutableModelSerializer()
        with self.assertRaises(DRFValidationError):
            s.create({})

    def test_update_raises(self):
        s = ImmutableModelSerializer()
        with self.assertRaises(DRFValidationError):
            s.update(None, {})

    def test_meta_fields(self):
        self.assertEqual(ImmutableModelSerializer.Meta.fields, ['id'])


class TenantModelSerializerMetaTest(TestCase):
    """TenantModelSerializer Meta has audit fields read-only."""

    def test_read_only_fields(self):
        expected = ['id', 'tenant_id', 'created_by', 'created_on', 'updated_by', 'updated_on']
        self.assertEqual(TenantModelSerializer.Meta.read_only_fields, expected)

    def test_fields(self):
        self.assertEqual(TenantModelSerializer.Meta.fields, TenantModelSerializer.Meta.read_only_fields)


class ReadOnlyTenantSerializerMetaTest(TestCase):
    """ReadOnlyTenantSerializer marks all standard fields read-only."""

    def test_all_fields_are_read_only(self):
        self.assertEqual(
            ReadOnlyTenantSerializer.Meta.fields,
            ReadOnlyTenantSerializer.Meta.read_only_fields,
        )
