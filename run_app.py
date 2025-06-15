import os
import sys
from django.core.wsgi import get_wsgi_application
from waitress import serve
import webbrowser
import time
from django.core.management import call_command
from pathlib import Path
from django.db.utils import OperationalError

# --- Crucial: Set up Django environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cms_project.settings')

if getattr(sys, 'frozen', False):
    base_dir = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(os.path.dirname(sys.executable))
    
    # Ensure sys.path includes paths to your Django project and apps within the bundle
    sys.path.append(str(base_dir))
    sys.path.append(str(base_dir / 'cms_project'))
    sys.path.append(str(base_dir / 'crew_management'))
    sys.path.append(str(base_dir / 'users'))

application = get_wsgi_application()

# --- Database Initialization Logic ---
from django.conf import settings
db_path = settings.DATABASES['default']['NAME']

db_dir = Path(db_path).parent
os.makedirs(db_dir, exist_ok=True)

# Check if the database file exists and is not empty.
# If an empty DB file exists (e.g., from a previous failed run), remove it to force re-migration.
db_exists_and_not_empty = os.path.exists(db_path) and os.path.getsize(db_path) > 0

if not db_exists_and_not_empty:
    print("Database not found or is empty. Initializing database and applying migrations...")
    try:
        # Delete any potentially corrupted empty db.sqlite3 before migrating
        if os.path.exists(db_path):
            os.remove(db_path)
        
        call_command('migrate', interactive=False, verbosity=1)
        print("Database migrations applied successfully.")

        # --- IMPORTANT: No superuser creation here. You will provide a pre-configured DB. ---
        print("\n---------------------------------------------------------")
        print("  Database setup complete. Ready to run.                ")
        print("---------------------------------------------------------\n")

    except OperationalError as e:
        print(f"OperationalError during database initialization: {e}")
        print("This often means SQLite is locked or permissions issue. Retrying may help.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during database initialization: {e}")
        sys.exit(1)
else:
    print("Database found. Starting application...")


# --- Web Server Configuration ---
host = '127.0.0.1'
port = 8000
server_address = f"http://{host}:{port}"

print(f"Starting Django application at {server_address}...")
print("This window will close when the application stops.")

webbrowser.open_new_tab(server_address)

serve(application, host=host, port=port)
