from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

def verify_user_deletion():
    # 1. Create Admin Client
    admin = User.objects.get(username='admin')
    client = Client()
    client.force_login(admin)
    
    # 2. Create Target User (Virgin, no logs)
    target_user, created = User.objects.get_or_create(username='test_del_virgin')
    target_user.set_password('pass')
    target_user.save()
    print(f"Created virgin user: {target_user.username} (ID: {target_user.id})")
    
    # 3. GET Confirmation Page
    url = reverse('user_delete', args=[target_user.id])
    print(f"GET {url}")
    resp = client.get(url)
    if resp.status_code == 200:
        print("SUCCESS: Confirmation page loaded.")
    else:
        print(f"FAILURE: Confirmation page returned {resp.status_code}")
        return

    # 4. POST Delete
    print(f"POST {url}")
    resp = client.post(url, follow=True)
    
    # 5. Verify Deletion
    if not User.objects.filter(id=target_user.id).exists():
        print("SUCCESS: User deleted.")
    else:
        print("FAILURE: User still exists.")
        
    # 6. Verify Self-Delete Protection
    print("Testing Self-Delete Protection...")
    url_self = reverse('user_delete', args=[admin.id])
    resp = client.post(url_self, follow=True) # Should fail
    if User.objects.filter(id=admin.id).exists():
        print("SUCCESS: Admin (self) was NOT deleted.")
    else:
        print("FAILURE: Admin deleted themselves! (Bad)")

if __name__ == "__main__":
    try:
        verify_user_deletion()
    except Exception as e:
        print(f"ERROR: {e}")
