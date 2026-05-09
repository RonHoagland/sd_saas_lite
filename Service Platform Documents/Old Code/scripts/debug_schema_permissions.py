import os
import sys
import django
from django.db import connection

# Setup paths like manage.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_core.settings")
django.setup()

def debug_permissions():
    print("--- Debugging Schema Permissions ---")
    with connection.cursor() as cursor:
        try:
            # Check search_path
            cursor.execute("SHOW search_path;")
            print(f"Current search_path: {cursor.fetchone()[0]}")
            
            # Check current schemas
            cursor.execute("SELECT current_schemas(true);")
            print(f"Effective schemas: {cursor.fetchone()[0]}")
            
            # Check if public schema exists
            cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'public';")
            result = cursor.fetchone()
            print(f"Public schema exists: {result is not None}")
            
            # Try to create a table in public
            print("Attempting to create table 'test_permission' in public...")
            cursor.execute("CREATE TABLE public.test_permission (id serial PRIMARY KEY);")
            print("Success: Created table.")
            cursor.execute("DROP TABLE public.test_permission;")
            print("Success: Dropped table.")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    debug_permissions()
