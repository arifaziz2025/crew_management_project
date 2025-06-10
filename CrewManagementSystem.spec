# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, copy_metadata, get_package_paths

block_cipher = None


a = Analysis(
    ['run_app.py'],
    pathex=['.'], # Ensure this points to your project root where run_app.py and this spec file are
    binaries=[],
    datas=[
        ('staticfiles', 'static_assets'), # Source: local 'staticfiles' folder, Dest: 'static_assets' inside bundle
        (r'C:\Users\arifa\Documents\DevProjects\crew_management_system\venv\Lib\site-packages\waitress', 'waitress'), # Explicitly copy waitress package

        # --- NEW: Explicitly copy template directories ---
        # Copy 'crew_management/templates' to 'crew_management/templates' inside the bundle
        ('crew_management/templates', 'crew_management/templates'),
        # Copy 'users/templates' to 'users/templates' inside the bundle
        ('users/templates', 'users/templates'),
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
        'waitress', # Keep waitress in hiddenimports too
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
        'http.server', # Keep http.server in hiddenimports as it's a standard lib module
        'ssl',
        'json',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        '_tkinter', 'PyQt5', 'PyQt4', 'Tkinter',
        'distutils',
        'setuptools',
        'test',
        'unittest',
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
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Set to False for a windowed (no console) application
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
