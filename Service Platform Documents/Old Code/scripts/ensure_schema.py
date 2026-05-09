import os
import sys
import django
from django.db import connection

# Setup paths like manage.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_core.settings")
django.setup()

def ensure_user_schema():
    print("--- Ensuring User Schema 'brixa' Exists ---")
    with connection.cursor() as cursor:
        try:
            # Try public first just in case
            cursor.execute("CREATE SCHEMA IF NOT EXISTS public;")
            print("Success: 'public' schema exists/created.")
        except Exception as e:
            print(f"Public schema access failed: {e}")
            
        try:
            # Fallback to user schema
            cursor.execute("CREATE SCHEMA IF NOT EXISTS brixa AUTHORIZATION brixa;")
            print("Success: 'brixa' schema exists/created.")
        except Exception as e:
            print(f"User schema creation failed: {e}")

if __name__ == "__main__":
    ensure_user_schema()
