"""
Build Script for Raspberry Pi
Creates .deb package for Debian/Raspberry Pi OS
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Build configuration
APP_NAME = "artnetcontroller"
APP_VERSION = "2.0.0"
MAINTAINER = "Your Name <your.email@example.com>"
DESCRIPTION = "Professional DMX Art-Net Controller for Raspberry Pi"
HOMEPAGE = "https://yourwebsite.com"

DIST_DIR = Path("dist")
BUILD_DIR = Path("build_deb")

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

def check_platform():
    """Check if running on Linux"""
    if sys.platform != "linux":
        print_warning("This script should be run on Linux/Raspberry Pi")
        print_warning(f"Current platform: {sys.platform}")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    return True

def check_dependencies():
    """Check if required tools are installed"""
    print_step("Checking Dependencies")
    
    # Check for dpkg-deb
    try:
        subprocess.run(["dpkg-deb", "--version"], capture_output=True, check=True)
        print_success("dpkg-deb installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("dpkg-deb not found")
        print("Install with: sudo apt-get install dpkg-dev")
        return False
    
    # Check Python packages
    packages = ['PyQt6', 'psutil']
    missing = []
    
    for package in packages:
        try:
            __import__(package)
            print_success(f"{package} installed")
        except ImportError:
            print_error(f"{package} not found")
            missing.append(package)
    
    if missing:
        print_error(f"Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    return True

def clean_build():
    """Clean previous build artifacts"""
    print_step("Cleaning Build Directory")
    
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print_success(f"Removed: {BUILD_DIR}")
    
    # Clean old .deb files
    for deb in DIST_DIR.glob(f"{APP_NAME}_*.deb"):
        deb.unlink()
        print_success(f"Removed: {deb}")

def create_directory_structure():
    """Create Debian package directory structure"""
    print_step("Creating Package Structure")
    
    dirs = [
        BUILD_DIR / "DEBIAN",
        BUILD_DIR / "usr" / "local" / "bin",
        BUILD_DIR / "usr" / "local" / "lib" / APP_NAME,
        BUILD_DIR / "usr" / "share" / "applications",
        BUILD_DIR / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps",
        BUILD_DIR / "etc" / "systemd" / "system",
        BUILD_DIR / "var" / "log" / APP_NAME,
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path}")
    
    print_success("Directory structure created")

def create_control_file():
    """Create DEBIAN/control file"""
    print_step("Creating Control File")
    
    # Detect architecture
    try:
        result = subprocess.run(
            ["dpkg", "--print-architecture"],
            capture_output=True,
            text=True,
            check=True
        )
        arch = result.stdout.strip()
    except:
        arch = "armhf"  # Default for Raspberry Pi
    
    control_content = f"""Package: {APP_NAME}
Version: {APP_VERSION}
Section: electronics
Priority: optional
Architecture: {arch}
Depends: python3 (>= 3.9), python3-pyqt6, python3-psutil
Maintainer: {MAINTAINER}
Description: {DESCRIPTION}
 Professional DMX Art-Net Controller with recording and playback
 capabilities. Supports multiple universes, configuration management,
 automatic updates, and crash reporting.
 .
 Features:
  - Real-time DMX control via Art-Net protocol
  - Record and playback shows
  - Multi-universe support (up to 16 universes)
  - Web-based remote control
  - Automatic updates from GitHub
  - Comprehensive logging and crash reporting
Homepage: {HOMEPAGE}
"""
    
    control_file = BUILD_DIR / "DEBIAN" / "control"
    
    with open(control_file, 'w') as f:
        f.write(control_content)
    
    print_success(f"Created: {control_file}")
    print(f"  Architecture: {arch}")

def create_postinst_script():
    """Create DEBIAN/postinst script"""
    
    script_content = """#!/bin/bash
set -e

# Create log directory with correct permissions
mkdir -p /var/log/artnetcontroller
chown root:adm /var/log/artnetcontroller
chmod 755 /var/log/artnetcontroller

# Create config directory for users
mkdir -p /etc/artnetcontroller

# Reload systemd
systemctl daemon-reload

# Enable service (but don't start automatically)
# systemctl enable artnetcontroller.service

echo "ArtNetController installed successfully!"
echo "To start the service: sudo systemctl start artnetcontroller"
echo "To enable auto-start: sudo systemctl enable artnetcontroller"

exit 0
"""
    
    script_file = BUILD_DIR / "DEBIAN" / "postinst"
    
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    # Make executable
    script_file.chmod(0o755)
    
    print_success(f"Created: {script_file}")

def create_prerm_script():
    """Create DEBIAN/prerm script"""
    
    script_content = """#!/bin/bash
set -e

# Stop service if running
if systemctl is-active --quiet artnetcontroller; then
    systemctl stop artnetcontroller
fi

# Disable service
if systemctl is-enabled --quiet artnetcontroller; then
    systemctl disable artnetcontroller
fi

exit 0
"""
    
    script_file = BUILD_DIR / "DEBIAN" / "prerm"
    
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    script_file.chmod(0o755)
    
    print_success(f"Created: {script_file}")

def create_systemd_service():
    """Create systemd service file"""
    
    service_content = f"""[Unit]
Description=ArtNetController - DMX Art-Net Controller
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/usr/local/lib/{APP_NAME}
ExecStart=/usr/bin/python3 /usr/local/lib/{APP_NAME}/main.py
Restart=on-failure
RestartSec=5s

# Environment
Environment="DISPLAY=:0"
Environment="PYTHONUNBUFFERED=1"

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier={APP_NAME}

[Install]
WantedBy=multi-user.target
"""
    
    service_file = BUILD_DIR / "etc" / "systemd" / "system" / f"{APP_NAME}.service"
    
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print_success(f"Created: {service_file}")

def create_desktop_entry():
    """Create .desktop file for application menu"""
    
    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=ArtNetController
Comment={DESCRIPTION}
Exec=/usr/local/bin/{APP_NAME}
Icon={APP_NAME}
Terminal=false
Categories=AudioVideo;Audio;Electronics;
Keywords=DMX;ArtNet;Lighting;Controller;
"""
    
    desktop_file = BUILD_DIR / "usr" / "share" / "applications" / f"{APP_NAME}.desktop"
    
    with open(desktop_file, 'w') as f:
        f.write(desktop_content)
    
    print_success(f"Created: {desktop_file}")

def copy_application_files():
    """Copy application files to package"""
    print_step("Copying Application Files")
    
    lib_dir = BUILD_DIR / "usr" / "local" / "lib" / APP_NAME
    
    # Files and directories to copy
    items_to_copy = [
        ("src", lib_dir / "src"),
        ("config.json", lib_dir / "config.json"),
        ("main.py", lib_dir / "main.py"),  # Your main entry point
    ]
    
    for src, dst in items_to_copy:
        src_path = Path(src)
        
        if not src_path.exists():
            print_warning(f"Source not found: {src}")
            continue
        
        if src_path.is_dir():
            shutil.copytree(src_path, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst)
        
        print(f"  Copied: {src} → {dst}")
    
    # Create launcher script
    launcher_script = BUILD_DIR / "usr" / "local" / "bin" / APP_NAME
    
    launcher_content = f"""#!/bin/bash
cd /usr/local/lib/{APP_NAME}
python3 main.py "$@"
"""
    
    with open(launcher_script, 'w') as f:
        f.write(launcher_content)
    
    launcher_script.chmod(0o755)
    
    print_success("Application files copied")

def build_deb_package():
    """Build .deb package"""
    print_step("Building .deb Package")
    
    # Package filename
    result = subprocess.run(
        ["dpkg", "--print-architecture"],
        capture_output=True,
        text=True
    )
    arch = result.stdout.strip() if result.returncode == 0 else "armhf"
    
    deb_filename = f"{APP_NAME}_{APP_VERSION}_{arch}.deb"
    deb_path = DIST_DIR / deb_filename
    
    # Create dist directory
    DIST_DIR.mkdir(exist_ok=True)
    
    # Build package
    cmd = [
        "dpkg-deb",
        "--build",
        "--root-owner-group",
        str(BUILD_DIR),
        str(deb_path)
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
        print_success(f"Package created: {deb_path}")
        
        # Show size
        size_mb = deb_path.stat().st_size / 1024 / 1024
        print(f"  Size: {size_mb:.2f} MB")
        
        return deb_path
        
    except subprocess.CalledProcessError as e:
        print_error("Package build failed")
        print(e.stdout)
        print(e.stderr)
        return None

def verify_package(deb_path):
    """Verify .deb package"""
    print_step("Verifying Package")
    
    # Show package info
    cmd = ["dpkg-deb", "--info", str(deb_path)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        print_success("Package verification passed")
        return True
    except subprocess.CalledProcessError as e:
        print_error("Package verification failed")
        print(e.stderr)
        return False

def generate_checksum(deb_path):
    """Generate SHA256 checksum"""
    print_step("Generating Checksum")
    
    import hashlib
    
    sha256 = hashlib.sha256()
    
    with open(deb_path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            sha256.update(chunk)
    
    checksum = sha256.hexdigest()
    
    print(f"  {deb_path.name}")
    print(f"    SHA256: {checksum}")
    
    # Save to file
    checksum_file = DIST_DIR / f"{deb_path.stem}.sha256"
    
    with open(checksum_file, 'w') as f:
        f.write(f"{checksum}  {deb_path.name}\n")
    
    print_success(f"Checksum saved to: {checksum_file}")

def build_summary(deb_path):
    """Print build summary"""
    print_step("Build Summary")
    
    print(f"Build completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nPackage: {deb_path.absolute()}")
    
    size_mb = deb_path.stat().st_size / 1024 / 1024
    print(f"Size: {size_mb:.2f} MB")
    
    print("\nInstallation:")
    print(f"  sudo dpkg -i {deb_path.name}")
    print(f"  sudo apt-get install -f  # Fix dependencies if needed")
    
    print("\nUsage:")
    print(f"  {APP_NAME}  # Run application")
    print(f"  sudo systemctl start {APP_NAME}  # Start service")
    print(f"  sudo systemctl enable {APP_NAME}  # Enable auto-start")
    
    print("\n" + "="*80)
    print_success("BUILD COMPLETE!")
    print("="*80)

def main():
    """Main build process"""
    
    print(f"""
{Colors.BOLD}{'='*80}
{APP_NAME.upper()} v{APP_VERSION} - Raspberry Pi Build Script
{'='*80}{Colors.END}
""")
    
    # Step 1: Check platform
    if not check_platform():
        return 1
    
    # Step 2: Check dependencies
    if not check_dependencies():
        print_error("Dependency check failed")
        return 1
    
    # Step 3: Clean build
    clean_build()
    
    # Step 4: Create directory structure
    create_directory_structure()
    
    # Step 5: Create control files
    create_control_file()
    create_postinst_script()
    create_prerm_script()
    
    # Step 6: Create systemd service
    create_systemd_service()
    
    # Step 7: Create desktop entry
    create_desktop_entry()
    
    # Step 8: Copy application files
    copy_application_files()
    
    # Step 9: Build package
    deb_path = build_deb_package()
    
    if not deb_path:
        print_error("Build failed")
        return 1
    
    # Step 10: Verify package
    verify_package(deb_path)
    
    # Step 11: Generate checksum
    generate_checksum(deb_path)
    
    # Step 12: Summary
    build_summary(deb_path)
    
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
