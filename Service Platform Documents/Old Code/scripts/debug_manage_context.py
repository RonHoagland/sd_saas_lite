import os
import sys
import django
from django.db import connection

# Setup paths like manage.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_core.settings")
django.setup()

def debug_connection():
    print("--- Debugging Active DB Connection ---")
    from django.conf import settings
    print(f"Settings DB Name: {settings.DATABASES['default']['NAME']}")
    print(f"Settings DB Host: {settings.DATABASES['default']['HOST']}")
    
    # Force connection
    with connection.cursor() as cursor:
        try:
            # Psycopg2 connection object has a 'dsn' attribute
            # or 'get_dsn_parameters()'
            conn = connection.connection
            if hasattr(conn, 'dsn'):
                print(f"Active Connection DSN: {conn.dsn}")
            elif hasattr(conn, 'get_dsn_parameters'):
                print(f"Active Connection Params: {conn.get_dsn_parameters()}")
            else:
                print(f"Connection Object: {conn}")
                
            # Query current DB name from SQL to be triple sure
            cursor.execute("SELECT current_database();")
            print(f"SQL SELECT current_database(): {cursor.fetchone()[0]}")
            
            # Query current User
            cursor.execute("SELECT current_user;")
            print(f"SQL SELECT current_user: {cursor.fetchone()[0]}")
            
            # Check migrations table
            cursor.execute("SELECT count(*) FROM django_migrations")
            print(f"django_migrations count: {cursor.fetchone()[0]}")
            
        except Exception as e:
            print(f"Error inspecting connection: {e}")

if __name__ == "__main__":
    debug_connection()
