import os
import sys
import django
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_core.settings")
django.setup()

from backup.models import Backup

# Get the most recent backup
latest = Backup.objects.all().order_by('-created_at').first()

if latest:
    print(f"Backup ID: {latest.backup_id}")
    print(f"Status: {latest.status}")
    print(f"Path: {latest.backup_path}")
    # Assuming there might be a field for error message or we can infer it
    # If standard fields don't have it, we might need to look at logs.
    # But often 'status' might be 'failed: reason' or there is a note.
    # Let's dump all fields just in case
    print(f"All Fields: {latest.__dict__}")
else:
    print("No backups found.")
