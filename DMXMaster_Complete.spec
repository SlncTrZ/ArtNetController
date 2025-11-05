# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Get the root directory
root_dir = Path.cwd()

block_cipher = None

# Define data files to include
added_files = [
    ('assets', 'assets'),
    ('config', 'config'),
    ('data', 'data'),
    ('docs', 'docs'),
    ('src', 'src'),
    ('requirements.txt', '.'),
    ('README.md', '.'),
    ('CHANGELOG.md', '.'),
    ('LICENSE.txt', '.'),
]

# Hidden imports for PyQt6 and other modules
hidden_imports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui', 
    'PyQt6.QtWidgets',
    'PyQt6.QtNetwork',
    'PyQt6.QtMultimedia',
    'flask',
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.asymmetric',
    'cryptography.hazmat.primitives.asymmetric.rsa',
    'cryptography.hazmat.primitives.serialization',
    'cryptography.hazmat.primitives.hashes',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.backends.openssl',
    'netifaces',
    'psutil',
    'zoneinfo',
    'src.version',
    'src.gui.main_window',
    'src.artnet.controller',
    'src.utils.license',
    'src.system.config_manager',
    'src.show.dmx_recorder',
    'src.show.manager',
    'src.webserver.server',
]

a = Analysis(
    ['main.py'],
    pathex=[str(root_dir)],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy.testing',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
        'ipython',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove unnecessary files
def remove_file(files_list, pattern):
    return [(name, dest, kind) for name, dest, kind in files_list 
            if not name.lower().endswith(pattern.lower())]

# Clean up unnecessary files
a.datas = remove_file(a.datas, '.pyc')
a.datas = remove_file(a.datas, '.pyo')
a.datas = remove_file(a.datas, '__pycache__')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DMXMaster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for windowed application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/app_icon.ico' if os.path.exists('assets/icons/app_icon.ico') else None,
    version='file_version_info.txt' if os.path.exists('file_version_info.txt') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DMXMaster'
)