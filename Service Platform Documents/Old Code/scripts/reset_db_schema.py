import os
import django
import sys
from django.db import connection

# Add parent directory to path so we can import platform_core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_core.settings")
django.setup()

def reset_schema():
    from django.conf import settings
    print(f"DB Config: {settings.DATABASES['default']}")
    print(f"DB Vendor: {connection.vendor}")
    
    print("--- Resetting PostgreSQL Public Schema (Table Drop Method) ---")
    with connection.cursor() as cursor:
        try:
            cursor.execute("SELECT count(*) FROM django_migrations")
            print(f"django_migrations count: {cursor.fetchone()[0]}")
        except Exception as e:
            print(f"django_migrations query failed: {e}")
            
        # Get all table names in the current schema
        cursor.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        """)
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found to drop.")
            return

        print(f"Found {len(tables)} tables to drop.")
        for schema, table in tables:
            print(f"Dropping table: {schema}.{table}")
            cursor.execute(f'DROP TABLE IF EXISTS "{schema}"."{table}" CASCADE;')
            
    print("--- Table Drop Complete ---")

if __name__ == "__main__":
    reset_schema()
