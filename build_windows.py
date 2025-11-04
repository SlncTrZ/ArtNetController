#!/usr/bin/env python3
import os, sys, shutil, subprocess
from pathlib import Path
from datetime import datetime

VERSION = '2.0.0'
APP_NAME = 'ArtNetController'
ROOT_DIR = Path(__file__).parent
BUILD_DIR = ROOT_DIR / 'build'
DIST_DIR = ROOT_DIR / 'dist'
SPEC_FILE = BUILD_DIR / f'{APP_NAME}.spec'

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
    if not run_cmd([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', str(SPEC_FILE)], 'PyInstaller'): return False
    exe = DIST_DIR / APP_NAME / f'{APP_NAME}.exe'
    if exe.exists():
        print(f'[OK] Exe: {exe.stat().st_size / (1024*1024):.2f} MB')
        return True
    return False

def main():
    clean()
    if not build(): return 1
    print('[OK] Build complete!')
    return 0

if __name__ == '__main__':
    sys.exit(main())
