import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Preference

User = get_user_model()

@pytest.mark.django_db
class TestPreferenceViews:
    
    @pytest.fixture
    def admin_user(self, client):
        user = User.objects.create_superuser(username="admin", password="password")
        client.force_login(user)
        return user

    def test_preference_list_password_masking(self, client, admin_user):
        """Verify that password type preferences are masked in the list view"""
        Preference.objects.create(
            key="smtp_password",
            name="SMTP Password",
            data_type="password",
            value="supersecret123",
            default_value="",
            created_by=admin_user,
            updated_by=admin_user
        )
        
        response = client.get(reverse("preference_list"))
        content = response.content.decode()
        
        assert "******" in content
        assert "supersecret123" not in content

    def test_locked_preference_protection(self, client, admin_user):
        """Verify that locked preferences cannot be edited via POST"""
        pref = Preference.objects.create(
            key="system_path",
            name="System Path",
            data_type="path",
            value="/tmp",
            is_editable=False,
            created_by=admin_user,
            updated_by=admin_user
        )
        
        url = reverse("preference_update", kwargs={"pk": pref.pk})
        
        # Determine status code by making a request
        response = client.post(url, {"value": "/new/path"})
        
        # Should be 403 Forbidden
        assert response.status_code == 403
        
        # Verify value didn't change
        pref.refresh_from_db()
        assert pref.value == "/tmp"

    def test_dashboard_path_validation(self, client, admin_user):
        """Verify dashboard warns about missing paths"""
        # Create a path preference pointing to a non-existent location
        Preference.objects.create(
            key="backup_path",
            name="Backup Path",
            data_type="path",
            value="/non/existent/path/12345", 
            created_by=admin_user,
            updated_by=admin_user
        )
        
        response = client.get(reverse("dashboard"))
        content = response.content.decode()
        
        assert "Critical Path Missing" in content
        assert "/non/existent/path/12345" in content
