from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory

from config.middleware import TenantMiddleware
from config.tenant_context import clear_current_tenant_id, get_current_tenant_id
from tests.base import SDTATestCase


class TenantMiddlewareBehaviorTest(SDTATestCase):
    """Middleware must scope tenant users but not force context for staff/anon."""

    databases = ('default', 'worker')

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def _build_request(self, user):
        request = self.factory.get('/test/')
        request.user = user
        return request

    def test_sets_and_clears_context_for_tenant_user(self):
        tenant_user = self.make_user(email='tenant-mw@test.com')
        request = self._build_request(tenant_user)
        middleware = TenantMiddleware(lambda req: HttpResponse('ok'))

        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(get_current_tenant_id())

    def test_does_not_open_atomic_for_staff_user(self):
        clear_current_tenant_id()
        request = self._build_request(self.staff_user)
        middleware = TenantMiddleware(lambda req: HttpResponse('ok'))

        with patch('config.middleware.transaction.atomic') as atomic_mock:
            response = middleware(request)

        self.assertEqual(response.status_code, 200)
        atomic_mock.assert_not_called()
        self.assertIsNone(get_current_tenant_id())

    def test_does_not_open_atomic_for_anonymous_user(self):
        clear_current_tenant_id()
        request = self._build_request(AnonymousUser())
        middleware = TenantMiddleware(lambda req: HttpResponse('ok'))

        with patch('config.middleware.transaction.atomic') as atomic_mock:
            response = middleware(request)

        self.assertEqual(response.status_code, 200)
        atomic_mock.assert_not_called()
        self.assertIsNone(get_current_tenant_id())
