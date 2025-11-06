#!/usr/bin/env python3
import os, sys, shutil, subprocess
from pathlib import Path
from datetime import datetime

VERSION = '1.0.5'
APP_NAME = 'DMXMaster-LTS'
ROOT_DIR = Path(__file__).parent
BUILD_DIR = ROOT_DIR / 'build'
DIST_DIR = ROOT_DIR / 'dist'
# Use the version-specific spec file
SPEC_FILE = ROOT_DIR / 'DMXMaster-LTS-1.0.5.spec'

def run_cmd(cmd, desc):
    print(f'[RUN] {desc}')
    try:
        subprocess.run(cmd, cwd=ROOT_DIR, check=True)
        print(f'[OK] {desc}')
        return True
    except: return False

def clean():
    print('[CLEAN] Removing old artifacts...')
    for d in [DIST_DIR, BUILD_DIR / 'ArtNetController']:
        if d.exists(): shutil.rmtree(d)
    print('[OK] Clean complete')

def build():
    print(f'[BUILD] Building {APP_NAME} V{VERSION}...')
    if not SPEC_FILE.exists():
        print(f'[ERROR] Spec not found: {SPEC_FILE}')
        return False
    if not run_cmd([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', str(SPEC_FILE)], 'PyInstaller'):
        return False
    # Find built exe generically under dist/
    exes = sorted(DIST_DIR.rglob('*.exe'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not exes:
        print('[ERROR] No .exe found in dist/')
        return False
    main_exe = exes[0]
    size_mb = main_exe.stat().st_size / (1024*1024)
    print(f'[OK] Exe: {main_exe} ({size_mb:.2f} MB)')
    return True

def main():
    clean()
    if not build(): return 1
    print('[OK] Build complete!')
    return 0

if __name__ == '__main__':
    sys.exit(main())
