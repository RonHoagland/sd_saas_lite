# tests/test_api_auth.py
# Tests for API authentication views: CSRF, Login, Logout, Me.
# Also covers StaffUserBackend and SchemaSafeSessionBackend.

import uuid

from django.test import TestCase, RequestFactory, override_settings
from rest_framework.test import APIClient

from config.tenant_context import set_current_tenant_id, clear_current_tenant_id
from infrastructure.models import TenantState
from staff.backends import StaffUserBackend
from staff.models import StaffUser
from users.models import User
from crm.models import Person


@override_settings(SECURE_SSL_REDIRECT=False)
class CSRFTokenViewTest(TestCase):
    """GET /api/v1/auth/csrf/ returns a CSRF token."""

    def setUp(self):
        self.client = APIClient()

    def test_returns_csrf_token(self):
        resp = self.client.get('/api/v1/auth/csrf/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('csrfToken', resp.json())
        self.assertTrue(len(resp.json()['csrfToken']) > 0)

    def test_allows_unauthenticated(self):
        resp = self.client.get('/api/v1/auth/csrf/')
        self.assertEqual(resp.status_code, 200)


@override_settings(SECURE_SSL_REDIRECT=False)
class SessionLoginViewTest(TestCase):
    """POST /api/v1/auth/login/ authenticates a tenant user."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=False)
        self.tenant = TenantState.objects.create(
            subdomain=f'login-{uuid.uuid4().hex[:8]}',
            company_name='Login Corp',
            owner_email='owner@login.com',
            status=TenantState.StatusChoices.ACTIVE,
            tier=TenantState.TierChoices.LITE,
        )
        set_current_tenant_id(str(self.tenant.id))
        person = Person.objects.create(first_name='Auth', last_name='Tester')
        self.user = User.objects.create_user(
            'auth_user',
            tenant_id=self.tenant.id,
            password='SecurePass123!',
            email='auth@test.com',
            person=person,
        )
        clear_current_tenant_id()

    def test_successful_login(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'username': 'auth_user',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['email'], 'auth@test.com')
        self.assertEqual(data['tenant_id'], str(self.tenant.id))
        self.assertIn('csrfToken', data)

    def test_wrong_password(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'username': 'auth_user',
            'password': 'wrong',
        }, format='json')
        self.assertEqual(resp.status_code, 401)

    def test_missing_credentials(self):
        resp = self.client.post('/api/v1/auth/login/', {}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_missing_password(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'username': 'auth_user',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_email_instead_of_username_rejected(self):
        """Email must not be accepted as the login identifier."""
        resp = self.client.post('/api/v1/auth/login/', {
            'email': 'auth@test.com',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_nonexistent_user(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'username': 'no_such_user',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 401)

    def test_inactive_user_denied(self):
        set_current_tenant_id(str(self.tenant.id))
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        clear_current_tenant_id()

        resp = self.client.post('/api/v1/auth/login/', {
            'username': 'auth_user',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 403)


@override_settings(SECURE_SSL_REDIRECT=False)
class SessionLogoutViewTest(TestCase):
    """POST /api/v1/auth/logout/ logs out the user."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=False)
        self.tenant = TenantState.objects.create(
            subdomain=f'logout-{uuid.uuid4().hex[:8]}',
            company_name='Logout Corp',
            owner_email='owner@logout.com',
            status=TenantState.StatusChoices.ACTIVE,
            tier=TenantState.TierChoices.LITE,
        )
        set_current_tenant_id(str(self.tenant.id))
        person = Person.objects.create(first_name='Log', last_name='Out')
        self.user = User.objects.create_user(
            'logout_user',
            tenant_id=self.tenant.id,
            password='SecurePass123!',
            email='logout@test.com',
            person=person,
        )
        clear_current_tenant_id()

    def test_logout_requires_authentication(self):
        resp = self.client.post('/api/v1/auth/logout/')
        self.assertIn(resp.status_code, [401, 403])

    def test_logout_succeeds(self):
        login_resp = self.client.post('/api/v1/auth/login/', {
            'username': 'logout_user',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(login_resp.status_code, 200)
        self.client.credentials(HTTP_COOKIE=login_resp.cookies.output(header='', sep='; '))
        self.client.force_authenticate(user=self.user)
        resp = self.client.post('/api/v1/auth/logout/')
        self.assertEqual(resp.status_code, 204)


@override_settings(SECURE_SSL_REDIRECT=False)
class SessionMeViewTest(TestCase):
    """GET /api/v1/auth/me/ returns current user info."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=False)
        self.tenant = TenantState.objects.create(
            subdomain=f'me-{uuid.uuid4().hex[:8]}',
            company_name='Me Corp',
            owner_email='owner@me.com',
            status=TenantState.StatusChoices.ACTIVE,
            tier=TenantState.TierChoices.LITE,
        )
        set_current_tenant_id(str(self.tenant.id))
        person = Person.objects.create(first_name='Me', last_name='User')
        self.user = User.objects.create_user(
            'me_user',
            tenant_id=self.tenant.id,
            password='SecurePass123!',
            email='me@test.com',
            person=person,
        )
        clear_current_tenant_id()

    def test_me_requires_authentication(self):
        resp = self.client.get('/api/v1/auth/me/')
        self.assertIn(resp.status_code, [401, 403])

    def test_me_returns_user_data(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get('/api/v1/auth/me/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['email'], 'me@test.com')
        self.assertEqual(data['tenant_id'], str(self.tenant.id))
        self.assertTrue(data['is_active'])


# ── StaffUserBackend ──────────────────────────────────────────────────────────

class StaffUserBackendTest(TestCase):
    """Tests for StaffUserBackend.authenticate() and .get_user()."""

    def setUp(self):
        self.backend = StaffUserBackend()
        self.staff = StaffUser.objects.create_superuser(
            email='admin@serviz.com', name='Admin', password='AdminPass1!'
        )

    def test_authenticate_success(self):
        user = self.backend.authenticate(None, username='admin@serviz.com', password='AdminPass1!')
        self.assertEqual(user, self.staff)

    def test_authenticate_wrong_password(self):
        user = self.backend.authenticate(None, username='admin@serviz.com', password='wrong')
        self.assertIsNone(user)

    def test_authenticate_nonexistent_user(self):
        user = self.backend.authenticate(None, username='nobody@serviz.com', password='pass')
        self.assertIsNone(user)

    def test_authenticate_no_credentials(self):
        self.assertIsNone(self.backend.authenticate(None, username=None, password=None))
        self.assertIsNone(self.backend.authenticate(None, username='admin@serviz.com', password=None))
        self.assertIsNone(self.backend.authenticate(None, username=None, password='pass'))

    def test_authenticate_inactive_staff(self):
        self.staff.is_active = False
        self.staff.save()
        user = self.backend.authenticate(None, username='admin@serviz.com', password='AdminPass1!')
        self.assertIsNone(user)

    def test_get_user_existing(self):
        user = self.backend.get_user(self.staff.pk)
        self.assertEqual(user, self.staff)

    def test_get_user_nonexistent(self):
        user = self.backend.get_user(uuid.uuid4())
        self.assertIsNone(user)


# ── SchemaSafeSessionBackend ──────────────────────────────────────────────────

class SchemaSafeSessionBackendTest(TestCase):
    """Tests for SchemaSafeSessionBackend.get_user()."""

    def setUp(self):
        from api.backends import SchemaSafeSessionBackend
        self.backend = SchemaSafeSessionBackend()
        self.tenant = TenantState.objects.create(
            subdomain=f'ssb-{uuid.uuid4().hex[:8]}',
            company_name='SSB Corp',
            owner_email='owner@ssb.com',
            status=TenantState.StatusChoices.ACTIVE,
            tier=TenantState.TierChoices.LITE,
        )
        set_current_tenant_id(str(self.tenant.id))
        person = Person.objects.create(first_name='SSB', last_name='User')
        self.user = User.objects.create_user(
            'ssb_user',
            tenant_id=self.tenant.id,
            password='TestPass123!',
            email='ssb@test.com',
            person=person,
        )
        clear_current_tenant_id()

    def test_get_user_returns_user(self):
        user = self.backend.get_user(self.user.pk)
        self.assertEqual(user.pk, self.user.pk)
        self.assertEqual(user.email, 'ssb@test.com')

    def test_get_user_nonexistent(self):
        user = self.backend.get_user(uuid.uuid4())
        self.assertIsNone(user)
