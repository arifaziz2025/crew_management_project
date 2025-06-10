import os
import sys
from django.core.wsgi import get_wsgi_application
from waitress import serve
import webbrowser # To open the browser automatically

    # --- Crucial: Set up Django environment ---
    # This needs to point to your project's settings module.
    # Replace 'cms_project.settings' with your actual project's settings path if different.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cms_project.settings')

    # Ensure Django is set up
application = get_wsgi_application()

    # --- Define paths for PyInstaller ---
    # When PyInstaller bundles, it creates a temporary environment.
    # We need to ensure paths to static/media are relative to the executable.
    # This logic often needs fine-tuning after first build.
if getattr(sys, 'frozen', False): # Check if running as a PyInstaller executable
        # If frozen, set BASE_DIR to the directory containing the executable
        # This assumes your 'db.sqlite3', 'media', 'staticfiles' are relative to the executable.
        # This is a common pattern, adjust if your deployment structure is different.
        os.environ['DJANGO_SETTINGS_MODULE'] = 'cms_project.settings' # Re-confirm settings module
        
        # Modify Django's BASE_DIR to point to the executable's directory
        # This is a bit tricky as BASE_DIR is usually defined in settings.py
        # You might need to adjust settings.py to read an environment variable for BASE_DIR
        # or use a more sophisticated path handling in settings.py
        
        # For a simple local deployment, PyInstaller puts everything relative.
        # So, we usually just need to ensure static/media paths are handled relative
        # to where the executable is launched.
        pass # Actual path adjustments for media/static will primarily be in settings.py

    # --- Web Server Configuration ---
    # Use 0.0.0.0 to listen on all available network interfaces,
    # or 127.0.0.1 for local-only access.
    # Port 8000 is default, change if it conflicts.
host = '127.0.0.1'
port = 8000
server_address = f"http://{host}:{port}"

print(f"Starting Django application at {server_address}...")
print("This window will close when the application stops.")

    # Automatically open the default web browser to the application URL
    # This is a good user experience for a standalone app.
webbrowser.open_new_tab(server_address)

    # Serve the Django application using Waitress
serve(application, host=host, port=port)
    