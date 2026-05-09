import os
import sys
import django
from pathlib import Path
from django.core.exceptions import ValidationError

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_core.settings")
django.setup()

from django.contrib.auth.models import User

# Check current count
count = User.objects.count()
print(f"Current user count: {count}")

try:
    print("Attempting to create overflow user...")
    # Using User.objects.create() which calls save(), enabling signals
    User.objects.create(username="overflow_user", email="overflow@test.com")
    print("FAIL: User created despite limit!")
except ValidationError as e:
    print(f"PASS: Caught expected error: {e}")
except Exception as e:
    print(f"FAIL: Caught unexpected error: {type(e).__name__}: {e}")
