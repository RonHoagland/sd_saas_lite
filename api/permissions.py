# api/permissions.py
# Custom permissions for SDTA API endpoints.
# Source: Technical Architecture V2, Section 7.

from rest_framework.permissions import BasePermission, IsAuthenticated


class IsTenantUser(BasePermission):
    """
    Allows access only to authenticated users with a valid tenant context.

    This is the default permission for all tenant-scoped endpoints.
    TenantMiddleware must have set the tenant context before the view runs.
    """
    message = 'Authentication required with valid tenant context.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        from config.tenant_context import get_current_tenant_id
        context_tenant = get_current_tenant_id()
        return context_tenant is not None


class IsReadOnly(BasePermission):
    """
    Allows only safe (read-only) methods: GET, HEAD, OPTIONS.
    """
    def has_permission(self, request, view):
        return request.method in ('GET', 'HEAD', 'OPTIONS')


class IsTenantAdmin(BasePermission):
    """
    Allows access only to users with tenant admin privileges.

    Used for sensitive operations like lifecycle rule management,
    numbering configuration, and value list administration.
    """
    message = 'Tenant administrator privileges required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Check for is_tenant_admin attribute or role-based check.
        # This integrates with the User model's role system.
        return getattr(request.user, 'is_tenant_admin', False)
