from django.http import HttpResponseForbidden
from django.urls import reverse

class RolePermissionMiddleware:
    """
    Strictly enforces permissions for System Roles:
    1. Read-Only: Blocks all unsafe methods (POST, PUT, DELETE) globally.
    2. Worker: Blocks access to Admin Area (/admin-area/).
    3. Administrator: Full access.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Get User's Roles
        # Optimize by fetching keys list directly
        # Note: If high traffic, cache this in session
        user_roles = list(request.user.user_roles.values_list('role__key', flat=True))
        
        # 1. READ-ONLY Enforcement
        # If user has 'read_only' AND NOT 'administrator' or 'worker' (hierarchical check)
        # Assuming roles are exclusive or additive. If additive, Admin trumps Read-Only.
        is_admin = 'administrator' in user_roles
        is_worker = 'worker' in user_roles
        is_read_only = 'read_only' in user_roles

        if is_read_only and not (is_admin or is_worker):
            # Block unsafe methods
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                # Allow Login/Logout explicitly just in case (though usually they are exempt by not having roles yet or via separate auth flow)
                if request.path.startswith('/accounts/'): # Django default auth
                    pass
                else:
                    return HttpResponseForbidden("Read-Only users cannot modify data.")

        # 2. WORKER Enforcement
        # Worker cannot access Admin Area
        if is_worker and not is_admin:
            if request.path.startswith('/admin-area/') or request.path.startswith('/identity/') or request.path.startswith('/preferences/'):
                 # Note: Identity/Preferences are part of Admin Area in this architecture
                 return HttpResponseForbidden("Workers cannot access the Administration Area.")

        return self.get_response(request)
