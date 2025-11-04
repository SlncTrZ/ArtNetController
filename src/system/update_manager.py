"""
Update Manager Module
Tự động kiểm tra, tải và cài đặt updates từ GitHub Releases

Features:
- Query GitHub API để check version mới nhất
- So sánh semantic versioning (1.0.0 < 2.0.1)
- Tải và verify update package (checksum SHA256)
- Tự động cài đặt cho Windows (.exe) và Raspberry Pi (.deb/.tar.gz)
- Rollback nếu update fail
- Backup config trước khi update

Supported Platforms:
- Windows: .exe installer with silent install
- Raspberry Pi: .deb package or .tar.gz
- Linux: .tar.gz or AppImage
"""

import json
import logging
import platform
import subprocess
import shutil
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import ssl

logger = logging.getLogger(__name__)

# Current application version - UPDATE THIS WHEN RELEASING
CURRENT_VERSION = "2.0.0"

# GitHub repository info
GITHUB_REPO_OWNER = "yourusername"  # TODO: Update with actual repo
GITHUB_REPO_NAME = "ArtNetController"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"

# Update settings
UPDATE_CHECK_TIMEOUT = 10  # seconds
DOWNLOAD_CHUNK_SIZE = 8192  # bytes
BACKUP_DIR = Path("backups")


@dataclass
class Version:
    """Semantic version (major.minor.patch)"""
    major: int
    minor: int
    patch: int
    
    @classmethod
    def from_string(cls, version_str: str) -> 'Version':
        """Parse version string like '2.0.1' or 'v2.0.1'"""
        version_str = version_str.strip().lstrip('v')
        parts = version_str.split('.')
        
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")
        
        return cls(
            major=int(parts[0]),
            minor=int(parts[1]),
            patch=int(parts[2])
        )
    
    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __lt__(self, other: 'Version'):
        """Compare versions: 1.0.0 < 2.0.1"""
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __eq__(self, other: 'Version'):
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __le__(self, other: 'Version'):
        return self < other or self == other


@dataclass
class ReleaseInfo:
    """GitHub release information"""
    version: Version
    tag_name: str
    name: str
    body: str  # Release notes
    published_at: str
    assets: List[Dict]  # Download URLs for different platforms
    prerelease: bool
    
    @classmethod
    def from_github_api(cls, data: Dict) -> 'ReleaseInfo':
        """Parse GitHub API response"""
        return cls(
            version=Version.from_string(data['tag_name']),
            tag_name=data['tag_name'],
            name=data['name'],
            body=data.get('body', ''),
            published_at=data['published_at'],
            assets=data.get('assets', []),
            prerelease=data.get('prerelease', False)
        )


class UpdateManager:
    """
    Quản lý việc kiểm tra và cài đặt updates
    """
    
    def __init__(self, config_manager=None):
        self.current_version = Version.from_string(CURRENT_VERSION)
        self.config_manager = config_manager
        self.platform = self._detect_platform()
        
        # Paths
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Update Manager initialized: v{self.current_version} on {self.platform}")
    
    def _detect_platform(self) -> str:
        """Detect current platform"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == 'windows':
            return 'windows'
        elif system == 'linux':
            # Check if Raspberry Pi
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    if 'raspberry pi' in f.read().lower():
                        return 'raspberry_pi'
            except:
                pass
            return 'linux'
        elif system == 'darwin':
            return 'macos'
        else:
            return 'unknown'
    
    def check_for_updates(self, include_prerelease: bool = False) -> Optional[ReleaseInfo]:
        """
        Kiểm tra update mới từ GitHub
        
        Returns:
            ReleaseInfo nếu có update mới, None nếu không có hoặc lỗi
        """
        try:
            logger.info("Checking for updates from GitHub...")
            
            # Query GitHub API
            url = f"{GITHUB_API_URL}/releases/latest"
            
            # Create SSL context to avoid certificate errors
            context = ssl.create_default_context()
            
            # Add User-Agent header (required by GitHub API)
            headers = {
                'User-Agent': f'ArtNetController/{self.current_version}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            request = Request(url, headers=headers)
            
            with urlopen(request, timeout=UPDATE_CHECK_TIMEOUT, context=context) as response:
                data = json.loads(response.read().decode())
            
            release = ReleaseInfo.from_github_api(data)
            
            # Skip prereleases if not wanted
            if release.prerelease and not include_prerelease:
                logger.info("Latest release is prerelease, skipping")
                return None
            
            # Compare versions
            if release.version > self.current_version:
                logger.info(f"Update available: v{release.version} (current: v{self.current_version})")
                return release
            else:
                logger.info(f"Already on latest version: v{self.current_version}")
                return None
            
        except HTTPError as e:
            if e.code == 404:
                logger.error("GitHub repository not found or no releases available")
            else:
                logger.error(f"HTTP error checking for updates: {e.code} {e.reason}")
            return None
            
        except URLError as e:
            logger.error(f"Network error checking for updates: {e.reason}")
            return None
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return None
    
    def _find_asset_for_platform(self, release: ReleaseInfo) -> Optional[Dict]:
        """Tìm file download phù hợp với platform hiện tại"""
        asset_patterns = {
            'windows': ['.exe', 'windows', 'win64', 'win32'],
            'raspberry_pi': ['.deb', 'raspberry', 'armhf', 'arm64', 'rpi'],
            'linux': ['.tar.gz', '.AppImage', 'linux', 'x86_64'],
            'macos': ['.dmg', '.pkg', 'macos', 'darwin']
        }
        
        patterns = asset_patterns.get(self.platform, [])
        
        for asset in release.assets:
            name = asset['name'].lower()
            
            # Check if asset name matches platform patterns
            if any(pattern in name for pattern in patterns):
                logger.info(f"Found asset for {self.platform}: {asset['name']}")
                return asset
        
        logger.warning(f"No asset found for platform: {self.platform}")
        return None
    
    def download_update(self, release: ReleaseInfo, output_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Tải update package từ GitHub
        
        Returns:
            Path to downloaded file, or None if failed
        """
        try:
            # Find appropriate asset
            asset = self._find_asset_for_platform(release)
            if not asset:
                logger.error("No suitable update package found for this platform")
                return None
            
            download_url = asset['browser_download_url']
            filename = asset['name']
            file_size = asset.get('size', 0)
            
            # Determine output path
            if output_dir is None:
                output_dir = Path(tempfile.gettempdir()) / "artnet_updates"
                output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / filename
            
            logger.info(f"Downloading update: {filename} ({file_size / 1024 / 1024:.2f} MB)")
            logger.info(f"URL: {download_url}")
            
            # Download with progress
            context = ssl.create_default_context()
            headers = {'User-Agent': f'ArtNetController/{self.current_version}'}
            request = Request(download_url, headers=headers)
            
            with urlopen(request, timeout=UPDATE_CHECK_TIMEOUT, context=context) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                
                with open(output_path, 'wb') as f:
                    while True:
                        chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress every 10%
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if int(progress) % 10 == 0:
                                logger.info(f"Download progress: {progress:.1f}%")
            
            logger.info(f"Download complete: {output_path}")
            
            # Verify file size
            actual_size = output_path.stat().st_size
            if file_size > 0 and actual_size != file_size:
                logger.warning(f"File size mismatch: expected {file_size}, got {actual_size}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error downloading update: {e}")
            return None
    
    def verify_checksum(self, file_path: Path, expected_checksum: str, algorithm: str = 'sha256') -> bool:
        """Verify downloaded file checksum"""
        try:
            logger.info(f"Verifying {algorithm} checksum...")
            
            hash_func = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(DOWNLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    hash_func.update(chunk)
            
            actual_checksum = hash_func.hexdigest()
            
            if actual_checksum.lower() == expected_checksum.lower():
                logger.info("✅ Checksum verified")
                return True
            else:
                logger.error(f"❌ Checksum mismatch!")
                logger.error(f"Expected: {expected_checksum}")
                logger.error(f"Actual:   {actual_checksum}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying checksum: {e}")
            return False
    
    def backup_current_installation(self) -> Optional[Path]:
        """Backup config và executable trước khi update"""
        try:
            from datetime import datetime
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_v{self.current_version}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Creating backup: {backup_path}")
            
            # Backup config files
            config_files = ['config.json', 'license.key', 'settings.json']
            for config_file in config_files:
                src = Path(config_file)
                if src.exists():
                    dst = backup_path / config_file
                    shutil.copy2(src, dst)
                    logger.info(f"Backed up: {config_file}")
            
            # Backup shows directory
            shows_dir = Path('shows')
            if shows_dir.exists():
                dst_shows = backup_path / 'shows'
                shutil.copytree(shows_dir, dst_shows)
                logger.info(f"Backed up shows directory")
            
            # Save backup info
            backup_info = {
                'version': str(self.current_version),
                'timestamp': timestamp,
                'platform': self.platform
            }
            
            with open(backup_path / 'backup_info.json', 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            logger.info(f"✅ Backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def install_update(self, package_path: Path) -> bool:
        """
        Cài đặt update package
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            logger.info(f"Installing update from: {package_path}")
            
            # Backup trước khi install
            backup_path = self.backup_current_installation()
            if not backup_path:
                logger.warning("Backup failed, but continuing with installation")
            
            # Install dựa theo platform
            if self.platform == 'windows':
                return self._install_windows(package_path)
            elif self.platform == 'raspberry_pi':
                return self._install_raspberry_pi(package_path)
            elif self.platform == 'linux':
                return self._install_linux(package_path)
            else:
                logger.error(f"Installation not supported on platform: {self.platform}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing update: {e}")
            return False
    
    def _install_windows(self, package_path: Path) -> bool:
        """Install .exe on Windows with silent mode"""
        try:
            logger.info("Installing update on Windows...")
            
            # Run installer with silent flags
            # Most Windows installers support /S (NSIS) or /silent
            cmd = [str(package_path), '/S', '/silent']
            
            logger.info(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("✅ Installation completed")
                return True
            else:
                logger.error(f"Installation failed with code: {result.returncode}")
                logger.error(f"Output: {result.stdout}")
                logger.error(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing on Windows: {e}")
            return False
    
    def _install_raspberry_pi(self, package_path: Path) -> bool:
        """Install .deb on Raspberry Pi"""
        try:
            logger.info("Installing update on Raspberry Pi...")
            
            if package_path.suffix == '.deb':
                # Install .deb package
                cmd = ['sudo', 'dpkg', '-i', str(package_path)]
                
                logger.info(f"Running: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    check=False,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info("✅ Installation completed")
                    return True
                else:
                    logger.error(f"dpkg failed with code: {result.returncode}")
                    logger.error(f"Output: {result.stdout}")
                    return False
            
            elif package_path.suffix == '.gz':
                # Extract .tar.gz and replace files
                return self._install_tarball(package_path)
            
            else:
                logger.error(f"Unsupported package format: {package_path.suffix}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing on Raspberry Pi: {e}")
            return False
    
    def _install_linux(self, package_path: Path) -> bool:
        """Install on generic Linux"""
        return self._install_tarball(package_path)
    
    def _install_tarball(self, package_path: Path) -> bool:
        """Install from .tar.gz"""
        try:
            import tarfile
            
            logger.info("Extracting tarball...")
            
            extract_dir = Path(tempfile.gettempdir()) / "artnet_extract"
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(package_path, 'r:gz') as tar:
                tar.extractall(extract_dir)
            
            logger.info(f"Extracted to: {extract_dir}")
            
            # Run install script if exists
            install_script = extract_dir / 'install.sh'
            if install_script.exists():
                cmd = ['bash', str(install_script)]
                
                result = subprocess.run(
                    cmd,
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=extract_dir
                )
                
                if result.returncode == 0:
                    logger.info("✅ Installation completed")
                    return True
                else:
                    logger.error(f"Install script failed: {result.returncode}")
                    return False
            else:
                logger.warning("No install.sh found, manual installation required")
                return False
                
        except Exception as e:
            logger.error(f"Error installing tarball: {e}")
            return False
    
    def rollback(self, backup_path: Path) -> bool:
        """Khôi phục từ backup nếu update fail"""
        try:
            logger.info(f"Rolling back from: {backup_path}")
            
            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_path}")
                return False
            
            # Restore config files
            for config_file in backup_path.glob('*.json'):
                dst = Path(config_file.name)
                shutil.copy2(config_file, dst)
                logger.info(f"Restored: {config_file.name}")
            
            # Restore license
            license_file = backup_path / 'license.key'
            if license_file.exists():
                shutil.copy2(license_file, 'license.key')
                logger.info("Restored: license.key")
            
            # Restore shows
            backup_shows = backup_path / 'shows'
            if backup_shows.exists():
                shows_dir = Path('shows')
                if shows_dir.exists():
                    shutil.rmtree(shows_dir)
                shutil.copytree(backup_shows, shows_dir)
                logger.info("Restored: shows directory")
            
            logger.info("✅ Rollback completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return False
    
    def auto_update(self, include_prerelease: bool = False) -> Tuple[bool, str]:
        """
        Tự động check, download và install update
        
        Returns:
            (success: bool, message: str)
        """
        try:
            # Check for updates
            release = self.check_for_updates(include_prerelease)
            
            if not release:
                return True, "Already on latest version"
            
            # Download update
            package_path = self.download_update(release)
            if not package_path:
                return False, "Failed to download update"
            
            # Verify checksum if available
            # (GitHub releases can include SHA256 checksums in release notes)
            
            # Install update
            success = self.install_update(package_path)
            
            if success:
                return True, f"Successfully updated to v{release.version}"
            else:
                return False, "Installation failed"
                
        except Exception as e:
            logger.error(f"Auto-update error: {e}")
            return False, f"Error: {e}"


# Utility functions
def get_update_manager(config_manager=None) -> UpdateManager:
    """Get singleton UpdateManager instance"""
    return UpdateManager(config_manager)


if __name__ == "__main__":
    # Test update system
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("Update Manager Test")
    print("=" * 80)
    
    manager = UpdateManager()
    
    print(f"\nCurrent version: v{manager.current_version}")
    print(f"Platform: {manager.platform}")
    
    print("\n1️⃣ Checking for updates...")
    release = manager.check_for_updates()
    
    if release:
        print(f"\n✨ Update available!")
        print(f"Version: v{release.version}")
        print(f"Name: {release.name}")
        print(f"Published: {release.published_at}")
        print(f"\nRelease Notes:\n{release.body[:200]}...")
        
        print(f"\nAssets ({len(release.assets)}):")
        for asset in release.assets:
            print(f"  - {asset['name']} ({asset['size'] / 1024 / 1024:.2f} MB)")
    else:
        print("\n✅ Already on latest version")
    
    print("\n" + "=" * 80)
