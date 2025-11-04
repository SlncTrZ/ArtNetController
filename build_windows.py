"""
Build Script for Windows
Creates standalone .exe with PyInstaller and optional installer with Inno Setup
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Build configuration
APP_NAME = "ArtNetController"
APP_VERSION = "2.0.0"
BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
SPEC_FILE = BUILD_DIR / f"{APP_NAME}.spec"

# Colors for console output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_step(message):
    """Print step header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def check_dependencies():
    """Check if required build tools are installed"""
    print_step("Checking Dependencies")
    
    dependencies = {
        'pyinstaller': 'PyInstaller',
        'PyQt6': 'PyQt6',
    }
    
    missing = []
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            print_success(f"{name} installed")
        except ImportError:
            print_error(f"{name} not found")
            missing.append(name)
    
    if missing:
        print_error(f"Missing dependencies: {', '.join(missing)}")
        print(f"\nInstall with: pip install {' '.join(missing)}")
        return False
    
    return True

def clean_build():
    """Clean previous build artifacts"""
    print_step("Cleaning Build Directory")
    
    dirs_to_clean = [
        DIST_DIR,
        BUILD_DIR / "ArtNetController",
        Path("__pycache__"),
    ]
    
    files_to_clean = [
        BUILD_DIR / f"{APP_NAME}.spec.backup",
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print_success(f"Removed: {dir_path}")
    
    for file_path in files_to_clean:
        if file_path.exists():
            file_path.unlink()
            print_success(f"Removed: {file_path}")

def build_exe():
    """Build .exe with PyInstaller"""
    print_step("Building Executable with PyInstaller")
    
    if not SPEC_FILE.exists():
        print_error(f"Spec file not found: {SPEC_FILE}")
        return False
    
    # Build command
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        print_success("PyInstaller build completed")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error("PyInstaller build failed")
        print(e.stdout)
        print(e.stderr)
        return False

def create_installer():
    """Create Windows installer with Inno Setup (optional)"""
    print_step("Creating Windows Installer (Optional)")
    
    # Check if Inno Setup is installed
    inno_paths = [
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
    ]
    
    iscc_exe = None
    for path in inno_paths:
        if path.exists():
            iscc_exe = path
            break
    
    if not iscc_exe:
        print_warning("Inno Setup not found - skipping installer creation")
        print("Download from: https://jrsoftware.org/isdl.php")
        return False
    
    # Create Inno Setup script
    iss_file = create_inno_script()
    
    if not iss_file:
        return False
    
    # Compile installer
    cmd = [str(iscc_exe), str(iss_file)]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        print_success("Installer created")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error("Installer creation failed")
        print(e.stderr)
        return False

def create_inno_script():
    """Create Inno Setup script"""
    
    iss_content = f"""
; Inno Setup Script for {APP_NAME}

[Setup]
AppName={APP_NAME}
AppVersion={APP_VERSION}
AppPublisher=Your Company
AppPublisherURL=https://yourwebsite.com
DefaultDirName={{autopf}}\\{APP_NAME}
DefaultGroupName={APP_NAME}
OutputDir=dist
OutputBaseFilename={APP_NAME}-{APP_VERSION}-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={{app}}\\{APP_NAME}.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "vietnamese"; MessagesFile: "compiler:Languages\\Vietnamese.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"
Name: "startmenu"; Description: "Create Start Menu shortcut"; GroupDescription: "{{cm:AdditionalIcons}}"

[Files]
Source: "dist\\{APP_NAME}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"
Name: "{{autodesktop}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{APP_NAME}.exe"; Description: "{{cm:LaunchProgram,{APP_NAME}}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{{app}}\\logs"
Type: filesandordirs; Name: "{{app}}\\config_backups"
Type: filesandordirs; Name: "{{app}}\\shows"
"""
    
    iss_file = BUILD_DIR / f"{APP_NAME}.iss"
    
    try:
        with open(iss_file, 'w', encoding='utf-8') as f:
            f.write(iss_content)
        
        print_success(f"Created Inno Setup script: {iss_file}")
        return iss_file
        
    except Exception as e:
        print_error(f"Failed to create Inno Setup script: {e}")
        return None

def package_portable():
    """Create portable .zip package"""
    print_step("Creating Portable Package")
    
    app_dir = DIST_DIR / APP_NAME
    
    if not app_dir.exists():
        print_error(f"App directory not found: {app_dir}")
        return False
    
    # Create README for portable version
    readme = app_dir / "README.txt"
    
    readme_content = f"""
{APP_NAME} v{APP_VERSION} - Portable Edition

INSTALLATION:
1. Extract this folder anywhere on your computer
2. Run {APP_NAME}.exe
3. Your configuration and shows will be saved in this folder

REQUIREMENTS:
- Windows 10 or later
- No additional software required

SUPPORT:
Visit: https://yourwebsite.com
Email: support@yourwebsite.com

Copyright (c) 2025 Your Company
"""
    
    try:
        with open(readme, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print_success(f"Created README: {readme}")
        
        # Create .zip
        import zipfile
        
        zip_name = DIST_DIR / f"{APP_NAME}-{APP_VERSION}-Portable.zip"
        
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in app_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(DIST_DIR)
                    zipf.write(file_path, arcname)
                    print(f"  Added: {arcname}")
        
        print_success(f"Created portable package: {zip_name}")
        
        # Show size
        size_mb = zip_name.stat().st_size / 1024 / 1024
        print(f"  Size: {size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to create portable package: {e}")
        return False

def generate_checksums():
    """Generate SHA256 checksums for release files"""
    print_step("Generating Checksums")
    
    import hashlib
    
    files_to_hash = list(DIST_DIR.glob("*.exe")) + list(DIST_DIR.glob("*.zip"))
    
    checksums = []
    
    for file_path in files_to_hash:
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)
        
        checksum = sha256.hexdigest()
        checksums.append(f"{checksum}  {file_path.name}")
        
        print(f"  {file_path.name}")
        print(f"    SHA256: {checksum}")
    
    # Save to file
    checksum_file = DIST_DIR / "SHA256SUMS.txt"
    
    with open(checksum_file, 'w') as f:
        f.write('\n'.join(checksums))
    
    print_success(f"Checksums saved to: {checksum_file}")
    
    return True

def build_summary():
    """Print build summary"""
    print_step("Build Summary")
    
    print(f"Build completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nOutput files in: {DIST_DIR.absolute()}")
    print("\nFiles created:")
    
    for file_path in sorted(DIST_DIR.glob("*")):
        if file_path.is_file():
            size_mb = file_path.stat().st_size / 1024 / 1024
            print(f"  📦 {file_path.name} ({size_mb:.2f} MB)")
    
    print("\n" + "="*80)
    print_success("BUILD COMPLETE!")
    print("="*80)

def main():
    """Main build process"""
    
    print(f"""
{Colors.BOLD}{'='*80}
{APP_NAME} v{APP_VERSION} - Windows Build Script
{'='*80}{Colors.END}
""")
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print_error("Dependency check failed")
        return 1
    
    # Step 2: Clean build
    clean_build()
    
    # Step 3: Build .exe
    if not build_exe():
        print_error("Build failed")
        return 1
    
    # Step 4: Create installer (optional)
    create_installer()  # Don't fail if this doesn't work
    
    # Step 5: Create portable package
    package_portable()
    
    # Step 6: Generate checksums
    generate_checksums()
    
    # Step 7: Summary
    build_summary()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warning("\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
