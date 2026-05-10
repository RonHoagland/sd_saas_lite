# tests/test_api_auth.py
# Tests for API authentication views: CSRF, Login, Logout, Me.
# Covers workspace-based login per LITE_DECISIONS §N + cross-tenant isolation,
# StaffUser fallback, and the schema-safe session backends.

import uuid

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from config.tenant_context import set_current_tenant_id, clear_current_tenant_id
from infrastructure.models import TenantState
from staff.backends import StaffUserBackend
from staff.models import StaffUser
from users.models import User, SessionLog
from crm.models import Person


def _make_tenant(prefix='t', status_value=None, tier=None):
    return TenantState.objects.create(
        subdomain=f'{prefix}-{uuid.uuid4().hex[:8]}',
        company_name=f'{prefix.title()} Corp',
        owner_email=f'owner@{prefix}.com',
        status=status_value or TenantState.StatusChoices.ACTIVE,
        tier=tier or TenantState.TierChoices.LITE,
    )


def _make_user(tenant, username, password, email=None):
    set_current_tenant_id(str(tenant.id))
    try:
        person = Person.objects.create(first_name=username.title(), last_name='User')
        return User.objects.create_user(
            username,
            tenant_id=tenant.id,
            password=password,
            email=email or f'{username}@test.com',
            person=person,
        )
    finally:
        clear_current_tenant_id()


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
    """POST /api/v1/auth/login/ — workspace-scoped tenant user login."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=False)
        self.tenant = _make_tenant('login')
        self.user = _make_user(self.tenant, 'auth_user', 'SecurePass123!',
                               email='auth@test.com')

    def test_successful_login_sets_session_and_returns_workspace(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'username': 'auth_user',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['email'], 'auth@test.com')
        self.assertEqual(data['tenant_id'], str(self.tenant.id))
        self.assertEqual(data['workspace'], self.tenant.subdomain)
        self.assertIn('csrfToken', data)
        # Session must carry the tenant context for middleware on subsequent calls.
        self.assertEqual(
            self.client.session.get('active_tenant_id'), str(self.tenant.id),
        )
        self.assertEqual(
            self.client.session.get('active_tenant_subdomain'),
            self.tenant.subdomain,
        )
        self.assertIsNotNone(self.client.session.get('sdta_session_record_id'))
        sl = SessionLog.all_objects.get(
            pk=self.client.session['sdta_session_record_id'],
        )
        self.assertEqual(sl.tier_at_login, TenantState.TierChoices.LITE)
        self.assertEqual(sl.user_id, self.user.pk)

    def test_login_records_tenant_tier_snapshot(self):
        self.tenant.tier = TenantState.TierChoices.PRO
        self.tenant.save(update_fields=['tier'])
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'username': 'auth_user',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        sl = SessionLog.all_objects.get(
            pk=self.client.session['sdta_session_record_id'],
        )
        self.assertEqual(sl.tier_at_login, TenantState.TierChoices.PRO)

    def test_workspace_mixed_case_normalises(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain.upper(),
            'username': 'AUTH_USER',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 200)

    def test_wrong_password_returns_generic_401(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'username': 'auth_user',
            'password': 'wrong',
        }, format='json')
        self.assertEqual(resp.status_code, 401)
        self.assertIn('Invalid', resp.json()['detail'])

    def test_missing_credentials_returns_400(self):
        resp = self.client.post('/api/v1/auth/login/', {}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_missing_password_returns_400(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'username': 'auth_user',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_missing_workspace_returns_400(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'username': 'auth_user',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_email_instead_of_username_returns_400(self):
        """Posting `email` only (no `username`) is a contract violation."""
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'email': 'auth@test.com',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_nonexistent_user_returns_generic_401(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'username': 'no_such_user',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 401)
        self.assertIn('Invalid', resp.json()['detail'])

    def test_inactive_user_returns_generic_401(self):
        """Inactive accounts must not be enumerable via status code."""
        set_current_tenant_id(str(self.tenant.id))
        try:
            self.user.is_active = False
            self.user.save(update_fields=['is_active'])
        finally:
            clear_current_tenant_id()

        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'username': 'auth_user',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 401)


@override_settings(SECURE_SSL_REDIRECT=False)
class SessionLoginWorkspaceResolutionTest(TestCase):
    """Workspace must exist AND be ACTIVE."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=False)

    def test_unknown_workspace_returns_generic_401(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': 'no-such-workspace',
            'username': 'whoever',
            'password': 'whatever',
        }, format='json')
        self.assertEqual(resp.status_code, 401)
        self.assertIn('Invalid', resp.json()['detail'])

    def test_suspended_workspace_returns_generic_401(self):
        suspended = _make_tenant(
            'sus', status_value=TenantState.StatusChoices.SUSPENDED,
        )
        _make_user(suspended, 'sus_user', 'pw1234567')

        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': suspended.subdomain,
            'username': 'sus_user',
            'password': 'pw1234567',
        }, format='json')
        self.assertEqual(resp.status_code, 401)


@override_settings(SECURE_SSL_REDIRECT=False)
class SessionLoginCrossTenantIsolationTest(TestCase):
    """B1 regression: two tenants with the same username must not collide."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=False)
        self.tenant_a = _make_tenant('xta')
        self.tenant_b = _make_tenant('xtb')
        # Same username in both tenants — uniqueness is per (tenant_id, username).
        _make_user(self.tenant_a, 'admin', 'PassA12345', email='admin-a@x.com')
        _make_user(self.tenant_b, 'admin', 'PassB12345', email='admin-b@x.com')

    def test_username_in_workspace_a_authenticates_to_tenant_a(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant_a.subdomain,
            'username': 'admin',
            'password': 'PassA12345',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['tenant_id'], str(self.tenant_a.id))
        self.assertEqual(resp.json()['email'], 'admin-a@x.com')

    def test_password_from_b_does_not_authenticate_in_a(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant_a.subdomain,
            'username': 'admin',
            'password': 'PassB12345',
        }, format='json')
        self.assertEqual(resp.status_code, 401)

    def test_tenant_b_login_does_not_resolve_to_tenant_a(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant_b.subdomain,
            'username': 'admin',
            'password': 'PassB12345',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['tenant_id'], str(self.tenant_b.id))


@override_settings(SECURE_SSL_REDIRECT=False)
class SessionLoginStaffFallbackTest(TestCase):
    """StaffUser may sign into any active workspace via the same endpoint."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=False)
        self.tenant = _make_tenant('staff')
        self.staff = StaffUser.objects.create_superuser(
            email='ops@serviz.com', name='Ops', password='OpsPass123!',
            username='opshandle',
        )

    def test_staff_login_by_email(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'username': 'ops@serviz.com',
            'password': 'OpsPass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['email'], 'ops@serviz.com')
        self.assertEqual(data['tenant_id'], str(self.tenant.id))
        self.assertTrue(data['is_tenant_admin'])
        # Session carries the chosen tenant — StaffUser has no tenant_id.
        self.assertEqual(
            self.client.session.get('active_tenant_id'), str(self.tenant.id),
        )

    def test_staff_login_by_username_handle(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'username': 'opshandle',
            'password': 'OpsPass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['is_tenant_admin'])

    def test_staff_login_wrong_password(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'username': 'ops@serviz.com',
            'password': 'wrong',
        }, format='json')
        self.assertEqual(resp.status_code, 401)

    def test_inactive_staff_returns_generic_401(self):
        self.staff.is_active = False
        self.staff.save()
        resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'username': 'ops@serviz.com',
            'password': 'OpsPass123!',
        }, format='json')
        self.assertEqual(resp.status_code, 401)


@override_settings(SECURE_SSL_REDIRECT=False)
class SessionLogoutViewTest(TestCase):
    """POST /api/v1/auth/logout/ logs out the user."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=False)
        self.tenant = _make_tenant('logout')
        self.user = _make_user(self.tenant, 'logout_user', 'SecurePass123!',
                               email='logout@test.com')

    def test_logout_requires_authentication(self):
        resp = self.client.post('/api/v1/auth/logout/')
        self.assertIn(resp.status_code, [401, 403])

    def test_logout_succeeds(self):
        login_resp = self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'username': 'logout_user',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(login_resp.status_code, 200)
        record_pk = self.client.session.get('sdta_session_record_id')
        self.assertIsNotNone(record_pk)
        resp = self.client.post('/api/v1/auth/logout/')
        self.assertEqual(resp.status_code, 204)
        sl = SessionLog.all_objects.get(pk=record_pk)
        self.assertIsNotNone(sl.logout_at)


@override_settings(SECURE_SSL_REDIRECT=False)
class SessionMeViewTest(TestCase):
    """GET /api/v1/auth/me/ returns current user info."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=False)
        self.tenant = _make_tenant('me')
        self.user = _make_user(self.tenant, 'me_user', 'SecurePass123!',
                               email='me@test.com')

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

    def test_me_returns_workspace_when_session_has_active_tenant(self):
        """`/me/` surfaces session-stored active_tenant_subdomain (e.g. for
        StaffUsers, who have no own tenant_id)."""
        self.client.force_authenticate(user=self.user)
        session = self.client.session
        session['active_tenant_id'] = str(self.tenant.id)
        session['active_tenant_subdomain'] = self.tenant.subdomain
        session.save()

        resp = self.client.get('/api/v1/auth/me/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['workspace'], self.tenant.subdomain)


@override_settings(SECURE_SSL_REDIRECT=False)
class SessionIdleTimeoutApiTest(TestCase):
    """Sliding idle timeout enforced via SessionIdleTimeoutMiddleware."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=False)
        self.tenant = _make_tenant('idle')
        self.user = _make_user(self.tenant, 'idle_user', 'SecurePass123!',
                               email='idle@test.com')

    def test_request_after_idle_deadline_returns_401(self):
        self.client.post('/api/v1/auth/login/', {
            'workspace': self.tenant.subdomain,
            'username': 'idle_user',
            'password': 'SecurePass123!',
        }, format='json')
        session = self.client.session
        session['sdta_idle_deadline_ts'] = 1.0
        session.save()

        resp = self.client.get('/api/v1/auth/me/')
        self.assertEqual(resp.status_code, 401)


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
        self.tenant = _make_tenant('ssb')
        self.user = _make_user(self.tenant, 'ssb_user', 'TestPass123!',
                               email='ssb@test.com')

    def test_get_user_returns_user(self):
        user = self.backend.get_user(self.user.pk)
        self.assertEqual(user.pk, self.user.pk)
        self.assertEqual(user.email, 'ssb@test.com')

    def test_get_user_nonexistent(self):
        user = self.backend.get_user(uuid.uuid4())
        self.assertIsNone(user)
