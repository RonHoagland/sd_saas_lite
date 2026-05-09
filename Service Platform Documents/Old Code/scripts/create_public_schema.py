import os
import sys
import django
from django.db import connection

# Setup paths like manage.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_core.settings")
django.setup()

def create_public_schema():
    print("--- Creating Public Schema ---")
    with connection.cursor() as cursor:
        try:
            cursor.execute("CREATE SCHEMA public;")
            print("Success: Created 'public' schema.")
            cursor.execute("GRANT ALL ON SCHEMA public TO public;")
            print("Success: Granted permissions.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    create_public_schema()
