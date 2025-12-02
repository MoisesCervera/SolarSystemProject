# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# --- OS Detection ---
is_win = sys.platform.startswith('win')
is_mac = sys.platform.startswith('darwin')

# --- Configuration ---
# Assets: Map local 'assets' folder to 'assets' in the bundle
# Ensure 'assets' folder exists in the same directory as this spec file
added_files = [('assets', 'assets')]

# Icons
if is_win:
    icon_path = 'icon.ico'
elif is_mac:
    icon_path = 'icon.icns'
else:
    icon_path = None

# Check if icon exists
if icon_path and not os.path.exists(icon_path):
    print(f"Warning: Icon file '{icon_path}' not found. Building with default icon.")
    icon_path = None

# Excludes (Optional cleanup of common unused heavy libraries)
excluded_modules = ['tkinter', 'matplotlib', 'scipy', 'pandas', 'notebook', 'ipython']

# --- Analysis ---
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# --- EXE (One-File Build) ---
# We bundle everything into the EXE for a single-file distribution on Windows.
# On macOS, this EXE is placed inside the .app bundle.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SolarSystemProject',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

# --- BUNDLE (macOS Only) ---
if is_mac:
    app = BUNDLE(
        exe,
        name='SolarSystemProject.app',
        icon=icon_path,
        bundle_identifier='com.moisescervera.solarsystem',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
            'CFBundleDisplayName': 'Solar System Project',
            'CFBundleName': 'SolarSystemProject',
            'CFBundleShortVersionString': '1.0.0',
        },
    )
