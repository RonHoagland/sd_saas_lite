# tests/test_middleware_full.py
# Comprehensive tests for TenantMiddleware, AdminBypassMiddleware,
# and InternalAPIKeyMiddleware.

import json
import uuid
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory, TestCase, override_settings

from config.middleware import (
    AdminBypassMiddleware,
    InternalAPIKeyMiddleware,
    TenantMiddleware,
)
from config.tenant_context import (
    clear_current_tenant_id,
    get_current_tenant_id,
    set_current_tenant_id,
)
from infrastructure.models import TenantState
from staff.models import StaffUser
from tests.base import SDTATestCase


# ═══════════════════════════════════════════════════════════════════════════════
# TenantMiddleware — extended
# ═══════════════════════════════════════════════════════════════════════════════

class TenantMiddlewareExtendedTest(SDTATestCase):
    """Beyond basic behavior — edge cases for staff, superuser, anon, and SQL locals."""

    databases = ('default', 'worker')

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def _make_middleware(self, inner=None):
        return TenantMiddleware(inner or (lambda req: HttpResponse('ok')))

    def test_no_user_attribute_does_not_crash(self):
        """Requests where user is missing (e.g., early middleware) pass through."""
        clear_current_tenant_id()
        request = self.factory.get('/api/v1/fake/')
        request.user = AnonymousUser()
        mw = self._make_middleware()
        resp = mw(request)
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(get_current_tenant_id())
        set_current_tenant_id(str(self.tenant_id))

    def test_authenticated_staff_skips_tenant_scope(self):
        """Staff users (is_staff=True) bypass tenant scoping entirely."""
        clear_current_tenant_id()
        request = self.factory.get('/api/v1/fake/')
        request.user = self.staff_user
        mw = self._make_middleware()
        resp = mw(request)
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(get_current_tenant_id())

    def test_authenticated_superuser_skips_tenant_scope(self):
        """Superusers bypass tenant scoping."""
        clear_current_tenant_id()
        su = StaffUser.objects.create_superuser(
            email='super-mw@serviz.com', name='SU MW', password='Pass1!'
        )
        request = self.factory.get('/test/')
        request.user = su
        mw = self._make_middleware()
        resp = mw(request)
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(get_current_tenant_id())

    def test_tenant_user_sets_and_clears_context(self):
        user = self.make_user(email='mw-tenant@test.com')
        request = self.factory.get('/test/')
        request.user = user
        mw = self._make_middleware()
        resp = mw(request)
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(get_current_tenant_id())

    def test_tenant_user_sets_sql_local(self):
        """Verify SET LOCAL app.current_tenant_id is called for tenant users."""
        user = self.make_user(email='mw-sql@test.com')
        request = self.factory.get('/test/')
        request.user = user

        with patch('config.middleware.connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
            mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            mw = self._make_middleware()
            mw(request)

    def test_context_cleared_on_exception(self):
        """Even if the view raises, tenant context is cleared."""
        user = self.make_user(email='mw-exc@test.com')
        request = self.factory.get('/test/')
        request.user = user

        def boom(req):
            raise RuntimeError('view error')

        mw = self._make_middleware(inner=boom)
        with self.assertRaises(RuntimeError):
            mw(request)
        self.assertIsNone(get_current_tenant_id())


# ═══════════════════════════════════════════════════════════════════════════════
# AdminBypassMiddleware
# ═══════════════════════════════════════════════════════════════════════════════

class AdminBypassMiddlewareTest(TestCase):
    """AdminBypassMiddleware is a pass-through for all paths."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_admin_path_passes_through(self):
        inner = lambda req: HttpResponse('admin ok')
        mw = AdminBypassMiddleware(inner)
        request = self.factory.get('/admin/')
        resp = mw(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'admin ok')

    def test_non_admin_path_passes_through(self):
        inner = lambda req: HttpResponse('api ok')
        mw = AdminBypassMiddleware(inner)
        request = self.factory.get('/api/v1/crm/customers/')
        resp = mw(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'api ok')


# ═══════════════════════════════════════════════════════════════════════════════
# InternalAPIKeyMiddleware
# ═══════════════════════════════════════════════════════════════════════════════

class InternalAPIKeyMiddlewareTest(TestCase):
    """InternalAPIKeyMiddleware validates shared secret on /internal/api/."""

    def setUp(self):
        self.factory = RequestFactory()

    def _make_mw(self):
        return InternalAPIKeyMiddleware(lambda req: HttpResponse('internal ok'))

    @override_settings(INTERNAL_API_KEY='secret-key-abc')
    def test_valid_key_passes(self):
        mw = self._make_mw()
        request = self.factory.get('/internal/api/v1/check/',
                                   HTTP_AUTHORIZATION='Bearer secret-key-abc')
        resp = mw(request)
        self.assertEqual(resp.status_code, 200)

    @override_settings(INTERNAL_API_KEY='secret-key-abc')
    def test_wrong_key_returns_401(self):
        mw = self._make_mw()
        request = self.factory.get('/internal/api/v1/check/',
                                   HTTP_AUTHORIZATION='Bearer wrong-key')
        resp = mw(request)
        self.assertEqual(resp.status_code, 401)
        body = json.loads(resp.content)
        self.assertIn('Invalid', body['error'])

    @override_settings(INTERNAL_API_KEY='secret-key-abc')
    def test_missing_auth_header_returns_401(self):
        mw = self._make_mw()
        request = self.factory.get('/internal/api/v1/check/')
        resp = mw(request)
        self.assertEqual(resp.status_code, 401)

    @override_settings(INTERNAL_API_KEY='secret-key-abc')
    def test_non_bearer_auth_returns_401(self):
        mw = self._make_mw()
        request = self.factory.get('/internal/api/v1/check/',
                                   HTTP_AUTHORIZATION='Basic dXNlcjpwYXNz')
        resp = mw(request)
        self.assertEqual(resp.status_code, 401)

    @override_settings(INTERNAL_API_KEY='')
    def test_unconfigured_key_returns_503(self):
        mw = self._make_mw()
        request = self.factory.get('/internal/api/v1/check/',
                                   HTTP_AUTHORIZATION='Bearer anything')
        resp = mw(request)
        self.assertEqual(resp.status_code, 503)
        body = json.loads(resp.content)
        self.assertIn('not configured', body['error'])

    @override_settings(INTERNAL_API_KEY='secret-key-abc')
    def test_non_internal_path_ignored(self):
        """Non-internal paths are not checked."""
        mw = self._make_mw()
        request = self.factory.get('/api/v1/crm/customers/')
        resp = mw(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'internal ok')

    @override_settings(INTERNAL_API_KEY='s3cr3t')
    def test_timing_safe_comparison(self):
        """Ensures secrets.compare_digest is used (no timing oracle)."""
        mw = self._make_mw()
        with patch('config.middleware.secrets.compare_digest', return_value=False) as mock_cmp:
            request = self.factory.get('/internal/api/v1/test/',
                                       HTTP_AUTHORIZATION='Bearer guess')
            resp = mw(request)
            self.assertEqual(resp.status_code, 401)
            mock_cmp.assert_called_once_with('guess', 's3cr3t')
