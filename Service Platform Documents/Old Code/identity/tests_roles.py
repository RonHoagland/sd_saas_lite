import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db import transaction
from identity.models import Role, UserRole


User = get_user_model()

@pytest.mark.django_db
class TestStrictRoles:
    
    @pytest.fixture
    def setup_roles(self):
        # Create separate attribution user for roles to avoid circular issues
        # But we need roles first for the signal to work on system_user!
        # Create a dummy user for role creation attribution? Or use None if model allows? 
        # Model requires created_by.
        # Let's create a "root" user purely for creation, then delete it? No, protected.
        # Let's just create roles using a temporary obj or None if we can hack it, but strict mode...
        # Loophole: created_by=sys_user (but sys_user not created yet).
        # We can create sys_user WITHOUT roles? Signal handles specific count logic.
        
        # Correct approach:
        # 1. Create 'root' user (superuser). Signal runs -> count=1 -> tries Admin role (fails, no role yet).
        # 2. Create Roles (attributed to root).
        # 3. Create 'system_test' user. Signal runs -> count=2 -> tries Worker role.
        # Wait, we want 'system_test' to be Admin (first user logically for the test suite?).
        # If we rely on specific "Last Admin" logic, we need to know who is admin.
        
        # Let's keep it simple:
        # Create 'setup_user' (count=1). Signal -> No Role.
        # Create Roles (using setup_user).
        # Manually assign Admin to 'setup_user' to bootstrap.
        
        setup_user = User.objects.create_superuser(username='setup_admin', password='password')
        
        # Create mandatory roles
        admin_role = Role.objects.create(key='administrator', name='Admin', is_system=True, created_by=setup_user, updated_by=setup_user)
        worker_role = Role.objects.create(key='worker', name='Worker', is_system=True, created_by=setup_user, updated_by=setup_user)
        read_only_role = Role.objects.create(key='read_only', name='Read Only', is_system=True, created_by=setup_user, updated_by=setup_user)
        
        # Bootstrap 'setup_user' as Admin
        UserRole.objects.create(user=setup_user, role=admin_role, created_by=setup_user, updated_by=setup_user)
        
        return admin_role, worker_role, read_only_role

    def test_last_admin_protection(self, setup_roles):
        admin_role = setup_roles[0]
        setup_user = User.objects.get(username='setup_admin')
        
        # Ensure setup_user is the ONLY admin currently
        assert UserRole.objects.filter(role__key='administrator').count() == 1
        
        # Create a new user (will get Worker by signal)
        creator = User.objects.create_superuser(username='creator', password='password')
        # We want 'u1' to be an Admin to test deletion.
        # Creator has Worker (count=2).
        
        u1 = User.objects.create_user(username='admin1')
        # u1 has Worker (count=3).
        
        # Promote u1 to Admin (Remove Worker first)
        UserRole.objects.filter(user=u1).delete()
        ur1 = UserRole.objects.create(user=u1, role=admin_role, created_by=creator, updated_by=creator)
        
        # Now we have 2 Admins (setup_user, u1).
        # We want to test "Last Admin" protection.
        # We need to remove setup_user's admin role so u1 is the last one.
        # We can delete setup_user's role.
        
        # Use transaction due to potential signal checks
        with transaction.atomic():
            UserRole.objects.filter(user=setup_user, role=admin_role).delete()
        
        # Now u1 is the Last Admin.
        
        # Try to delete user -> Should Fail
        # Note: ur1.created_by is 'creator', not u1. So ProtectedError shouldn't happen on self-ref.
        with transaction.atomic():
            with pytest.raises(ValidationError, match="Cannot remove the last active Administrator"):
                u1.delete()
        
        # Try to delete role assignment -> Should Fail
        with transaction.atomic():
            with pytest.raises(ValidationError, match="Cannot remove the last active Administrator"):
                ur1.delete()
            
        # Add another admin to allow deletion
        u2 = User.objects.create_user(username='admin2') # gets Worker
        UserRole.objects.filter(user=u2).delete() # remove Worker
        ur2 = UserRole.objects.create(user=u2, role=admin_role, created_by=creator, updated_by=creator)
        
        # Now deleting u1 should succeed
        ur1.delete() # Success
        
    def test_read_only_middleware(self, client, setup_roles):
        read_only_role = setup_roles[2]
        
        u = User.objects.create_user(username='readonly', password='password')
        # u has Worker. Switch to ReadOnly.
        UserRole.objects.filter(user=u).delete()
        UserRole.objects.create(user=u, role=read_only_role, created_by=u, updated_by=u)
        
        client.force_login(u)
        
        # Try POST to any URL
        response = client.post('/any/url/', {'data': 'test'})
        assert response.status_code == 403
        assert b"Read-Only users cannot modify data" in response.content

    def test_worker_admin_area_block(self, client, setup_roles):
        # worker_role = setup_roles[1]
        
        u = User.objects.create_user(username='worker', password='password')
        # u already has Worker role by default signal
        
        client.force_login(u)
        
        # Try accessing Admin Area
        response = client.get('/admin-area/')
        assert response.status_code == 403
        assert b"Workers cannot access the Administration Area" in response.content
        
        # Try accessing Preferences
        response = client.get('/preferences/')
        assert response.status_code == 403

    def test_default_role_assignment(self, setup_roles):
        # setup_roles fixture creates 'setup_admin' (Admin).
        
        # Verify setup_admin has administrator role
        setup_user = User.objects.get(username='setup_admin')
        assert setup_user.user_roles.filter(role__key='administrator').exists()
        
        # Create new user -> Should be Worker
        u2 = User.objects.create_user(username='user_default')
        assert u2.user_roles.filter(role__key='worker').exists()
        assert not u2.user_roles.filter(role__key='administrator').exists()



    def test_last_admin_deactivation_protection(self, setup_roles):
        # setup_admin is the only admin
        setup_user = User.objects.get(username='setup_admin')
        
        # Try to deactivate -> Should Fail
        # If this test fails (i.e., no error raised), protection is missing.
        with pytest.raises(ValidationError, match="Cannot deactivate the last Administrator"):
            setup_user.is_active = False
            setup_user.save()
