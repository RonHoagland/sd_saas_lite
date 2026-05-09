import os
import sys
import django
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_core.settings")
django.setup()

from core.models import Preference
from backup.models import BackupSettings

# Path validation
PROJECT_ROOT = Path(os.getcwd())
# Use sibling directory to avoid "inside app dir" validation error
SAFE_BACKUP_PATH = PROJECT_ROOT.parent / "Brixa_Backups"
SAFE_BACKUP_PATH.mkdir(exist_ok=True)

print(f"Setting safe backup path: {SAFE_BACKUP_PATH}")

# 1. Update Core Preference (REMOVED - Backup settings are now exclusive to BackupSettings model)
# previously updated 'backup_storage_path' preference


# 2. Update BackupSettings (Singleton)
try:
    settings = BackupSettings.get_settings()
    settings.backup_path = str(SAFE_BACKUP_PATH)
    settings.save()
    print("✓ Updated BackupSettings singleton")
except Exception as e:
    print(f"✗ Failed to update BackupSettings: {e}")

# Verify
print(f"Current Backup Configuration: {BackupSettings.get_settings().backup_path}")
