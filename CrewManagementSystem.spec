# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# --- MANUALLY SPECIFY PATH TO WAITRESS ---
# !!! IMPORTANT !!! REPLACE THIS WITH THE ACTUAL ABSOLUTE PATH FOUND VIA 'pip show waitress'
# Example: r'C:\Users\arifa\Documents\DevProjects\crew_management_system\venv\Lib\site-packages\waitress'
# First, activate your venv and run: pip show waitress
# Then, copy the "Location:" path and append '\waitress' to it.
waitress_package_path = r'C:\Users\arifa\Documents\DevProjects\crew_management_system\venv\Lib\site-packages\waitress' # <--- REPLACE THIS LINE WITH YOUR ACTUAL PATH


# --- MANUALLY SPECIFY PATHS TO TEMPLATES ---
# These paths are relative to your project root where the .spec file is.
crew_management_app_path = 'crew_management' # Path to your crew_management app folder
users_app_path = 'users' # Path to your users app folder


a = Analysis(
    ['run_app.py'],
    pathex=['.'], # Ensure this points to your project root where run_app.py and this spec file are
    binaries=[],
    datas=[
        # --- Static files (bundled read-only) ---
        ('staticfiles', 'static_assets'), # Your collected static files

        # --- Explicitly copy waitress package ---
        # Source: Absolute path to your waitress installation
        # Destination: 'waitress' subfolder inside the bundle's root
        (waitress_package_path, 'waitress'),

        # --- Explicitly copy template directories for each app ---
        # Django's template loader (TEMPLATES['DIRS'] in settings.py) will look here.
        # This copies 'crew_management/templates' to 'crew_management/templates' inside the bundle
        (os.path.join(crew_management_app_path, 'templates'), os.path.join(crew_management_app_path, 'templates')),
        # This copies 'users/templates' to 'users/templates' inside the bundle
        (os.path.join(users_app_path, 'templates'), os.path.join(users_app_path, 'templates')),
    ],
    hiddenimports=[
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.forms',
        'django.db.backends.sqlite3',
        'waitress', # Keep in hiddenimports too for robustness
        'dj_database_url',
        'whitenoise.middleware',
        'django.db.backends.signals',
        'pytz',
        'PIL',
        'PIL.Image',
        'webbrowser',
        'csv',
        'io',
        'datetime',
        'mimetypes',
        'socket',
        'collections',
        'http.server',
        'ssl',
        'json',
        'base64', # Common hidden import for PyInstaller with Python 3.11+
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        '_tkinter', 'PyQt5', 'PyQt4', 'Tkinter',
        'distutils', 'setuptools', 'test', 'unittest',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CrewManagementSystem',
    debug=False, # Set to False for production executable
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # Set to False for a windowed (no console) application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas, # Ensure a.datas is listed here to include static files and collected modules
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CrewManagementSystem',
)
