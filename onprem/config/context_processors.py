# config/context_processors.py
"""Template context shared across the ServizDesk UI."""

from django.conf import settings


def servizdesk_ui(request):
    """Expose theme/asset version and active workspace info to all templates.

    Tenant context resolution mirrors TenantMiddleware (LITE_DECISIONS.md §N):
      - Tenant Users: tenant from request.user.tenant_id.
      - StaffUsers: tenant from session['active_tenant_id'] (workspace
        selected at login).
    """
    from staff.models import StaffUser
    from infrastructure.models import TenantState
    from users.models import TenantPreference

    user = getattr(request, 'user', None)
    is_authenticated = bool(user and user.is_authenticated)
    is_system_user = bool(is_authenticated and isinstance(user, StaffUser))

    # Session may not be present on every request path (e.g. internal API).
    session = getattr(request, 'session', None)

    tenant_id = None
    if is_authenticated:
        tenant_id = getattr(user, 'tenant_id', None)
        if not tenant_id and session is not None:
            tenant_id = session.get('active_tenant_id')

    tenant_name = ''
    workspace_subdomain = ''
    if is_authenticated and session is not None:
        workspace_subdomain = session.get('active_tenant_subdomain', '')
    if tenant_id:
        try:
            prefs = TenantPreference.all_objects.filter(tenant_id=tenant_id).first()
            if prefs and prefs.company_name:
                tenant_name = prefs.company_name
            if not tenant_name:
                # Fall back to TenantState.company_name if no tenant prefs yet.
                ts = TenantState.objects.filter(id=tenant_id).first()
                if ts:
                    tenant_name = ts.company_name
                    if not workspace_subdomain:
                        workspace_subdomain = ts.subdomain
        except Exception:
            pass
    if not tenant_name:
        tenant_name = 'ServizDesk'

    return {
        'SERVIZDESK_UI_ASSET_VERSION': getattr(
            settings,
            'SERVIZDESK_UI_ASSET_VERSION',
            '1',
        ),
        'is_system_user': is_system_user,
        'tenant_name': tenant_name,
        'workspace_subdomain': workspace_subdomain,
    }
