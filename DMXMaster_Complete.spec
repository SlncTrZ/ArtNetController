# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# All data files
datas = [
    ('assets', 'assets'),
    ('src', 'src'),
    ('config', 'config'),
    ('data', 'data'),
]

# Binary files (if any)
binaries = []

# Hidden imports - ALL required modules
hiddenimports = [
    # Logging
    'logging',
    'logging.handlers',
    
    # Standard library
    'platform',
    'socket',
    'subprocess',
    'threading',
    'time',
    'json',
    'os',
    'sys',
    'hashlib',
    'uuid',
    'base64',
    'shutil',
    'pathlib',
    'datetime',
    'typing',
    'struct',
    're',
    'copy',
    'collections',
    'functools',
    'itertools',
    'operator',
    'io',
    'pickle',
    'tempfile',
    'glob',
    'traceback',
    
    # PyQt6 - GUI framework
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtNetwork',
    'PyQt6.sip',
    
    # Flask - Web server
    'flask',
    'flask_cors',
    'werkzeug',
    'werkzeug.serving',
    'werkzeug.utils',
    'jinja2',
    'jinja2.ext',
    'click',
    'itsdangerous',
    'markupsafe',
    
    # Cryptography - License system
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.asymmetric',
    'cryptography.hazmat.primitives.asymmetric.rsa',
    'cryptography.hazmat.primitives.asymmetric.padding',
    'cryptography.hazmat.primitives.hashes',
    'cryptography.hazmat.primitives.serialization',
    'cryptography.hazmat.primitives.ciphers',
    'cryptography.hazmat.primitives.ciphers.aead',
    'cryptography.hazmat.primitives.kdf',
    'cryptography.hazmat.primitives.kdf.pbkdf2',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.backends.openssl',
    
    # Pygame - Audio
    'pygame',
    'pygame.mixer',
    
    # Other dependencies
    'tzdata',
    'tzdata.zoneinfo',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'mutagen',
    'lxml',
    'psutil',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',  # Exclude if not needed
        'matplotlib',  # Exclude if not needed
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DMXMaster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (windowed mode)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets\\DMXMaster.ico',
)
