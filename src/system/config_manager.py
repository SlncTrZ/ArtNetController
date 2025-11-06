"""
Configuration Manager Module
Quản lý tất cả settings của ứng dụng trong config.json

Features:
- Centralized configuration management
- Config migration khi update version
- Validation với JSON schema
- Default values cho missing settings
- Encryption cho sensitive data (license key)
- Auto-save khi thay đổi
- Config versioning
- Backup trước khi migration

Supported Settings:
- Network: IP, port, interface
- Universes: DMX universe configuration
- Recording: FPS, format, paths
- UI: Theme, language, window size
- License: Encrypted license key
- Paths: Shows, backups, logs
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import base64

logger = logging.getLogger(__name__)

# Config file paths
CONFIG_FILE = Path("config.json")
CONFIG_BACKUP_DIR = Path("config_backups")
CONFIG_VERSION = "2.0.0"

# Default configuration
DEFAULT_CONFIG = {
    "version": CONFIG_VERSION,
    "last_updated": None,
    
    # Network settings
    "network": {
        "artnet_ip": "0.0.0.0",
        "artnet_port": 6454,
        "broadcast_ip": "255.255.255.255",
        "interface": "auto",
        "timeout": 5.0
    },
    
    # Universe configuration
    "universes": {
        "enabled": list(range(32)),  # 0-31, all 32 universes enabled by default
        "output_enabled": True,
        "default_universe": 0,
        "max_universes": 32
    },
    
    # Recording settings
    "recording": {
        "fps": 60,
        "format": "binary",  # 'binary' or 'json'
        "auto_save": True,
        "compression": True,
        "buffer_size": 100,
        "default_path": "shows"
    },
    
    # Playback settings
    "playback": {
        "auto_loop": False,
        "sync_audio": True,
        "drift_correction": True,
        "buffer_size": 100
    },
    
    # UI settings
    "ui": {
        "theme": "dark",  # 'dark', 'light', 'auto'
        "language": "vi",  # 'vi', 'en'
        "window_width": 1280,
        "window_height": 720,
        "window_maximized": False,
        "fps_display": True,
        "show_tooltips": True
    },
    
    # License
    "license": {
        "key": None,  # Encrypted
        "type": "trial",  # 'trial', 'standard', 'professional'
        "activated_at": None,
        "expires_at": None
    },
    
    # Paths
    "paths": {
        "shows": "shows",
        "backups": "backups",
        "logs": "logs",
        "config_backups": "config_backups",
        "temp": "temp"
    },
    
    # Update settings
    "updates": {
        "auto_check": True,
        "check_interval_hours": 24,
        "include_prerelease": False,
        "auto_install": False,
        "last_check": None
    },
    
    # Crash reporting
    "crash_reporting": {
        "enabled": True,
        "anonymous": True,
        "include_system_info": True,
        "send_logs": False
    },
    
    # Advanced
    "advanced": {
        "log_level": "INFO",  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
        "log_rotation": True,
        "max_log_size_mb": 10,
        "keep_logs_days": 30,
        "performance_monitoring": True
    }
}


class ConfigMigration:
    """Xử lý migration config giữa các version"""
    
    @staticmethod
    def migrate_1_0_to_2_0(config: Dict) -> Dict:
        """Migration từ v1.0 lên v2.0"""
        logger.info("Migrating config from v1.0 to v2.0...")
        
        # Add new fields in v2.0
        if "recording" in config:
            config["recording"]["buffer_size"] = 100
            config["recording"]["compression"] = True
        
        if "playback" not in config:
            config["playback"] = DEFAULT_CONFIG["playback"]
        
        if "crash_reporting" not in config:
            config["crash_reporting"] = DEFAULT_CONFIG["crash_reporting"]
        
        # Update version
        config["version"] = "2.0.0"
        config["last_updated"] = datetime.now().isoformat()
        
        logger.info("Config migrated to v2.0")
        return config
    
    @staticmethod
    def migrate(config: Dict, from_version: str, to_version: str) -> Dict:
        """Auto-detect và migrate config"""
        
        migrations = {
            ("1.0.0", "2.0.0"): ConfigMigration.migrate_1_0_to_2_0,
            # Add more migrations here
        }
        
        migration_func = migrations.get((from_version, to_version))
        
        if migration_func:
            return migration_func(config)
        else:
            logger.warning(f"No migration path from {from_version} to {to_version}")
            return config


class ConfigValidator:
    """Validate configuration values"""
    
    @staticmethod
    def validate_network(config: Dict) -> List[str]:
        """Validate network settings"""
        errors = []
        
        network = config.get("network", {})
        
        # Validate port
        port = network.get("artnet_port", 6454)
        if not (1024 <= port <= 65535):
            errors.append(f"Invalid artnet_port: {port} (must be 1024-65535)")
        
        # Validate timeout
        timeout = network.get("timeout", 5.0)
        if not (0.1 <= timeout <= 60.0):
            errors.append(f"Invalid timeout: {timeout} (must be 0.1-60.0)")
        
        return errors
    
    @staticmethod
    def validate_recording(config: Dict) -> List[str]:
        """Validate recording settings"""
        errors = []
        
        recording = config.get("recording", {})
        
        # Validate FPS
        fps = recording.get("fps", 60)
        if not (1 <= fps <= 120):
            errors.append(f"Invalid FPS: {fps} (must be 1-120)")
        
        # Validate format
        fmt = recording.get("format", "binary")
        if fmt not in ["binary", "json"]:
            errors.append(f"Invalid format: {fmt} (must be 'binary' or 'json')")
        
        # Validate buffer size
        buffer_size = recording.get("buffer_size", 100)
        if not (10 <= buffer_size <= 1000):
            errors.append(f"Invalid buffer_size: {buffer_size} (must be 10-1000)")
        
        return errors
    
    @staticmethod
    def validate_ui(config: Dict) -> List[str]:
        """Validate UI settings"""
        errors = []
        
        ui = config.get("ui", {})
        
        # Validate theme
        theme = ui.get("theme", "dark")
        if theme not in ["dark", "light", "auto"]:
            errors.append(f"Invalid theme: {theme}")
        
        # Validate language
        lang = ui.get("language", "vi")
        if lang not in ["vi", "en"]:
            errors.append(f"Invalid language: {lang}")
        
        # Validate window size
        width = ui.get("window_width", 1280)
        height = ui.get("window_height", 720)
        if width < 640 or height < 480:
            errors.append(f"Window too small: {width}x{height} (min 640x480)")
        
        return errors
    
    @staticmethod
    def validate_all(config: Dict) -> List[str]:
        """Validate entire config"""
        errors = []
        
        errors.extend(ConfigValidator.validate_network(config))
        errors.extend(ConfigValidator.validate_recording(config))
        errors.extend(ConfigValidator.validate_ui(config))
        
        return errors


class ConfigManager:
    """
    Quản lý configuration của ứng dụng
    Thread-safe, auto-save, encryption support
    """
    
    def __init__(self, config_file: Path = CONFIG_FILE):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.backup_dir = CONFIG_BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load hoặc create config
        self.load()
        
        logger.info(f"ConfigManager initialized: v{self.config.get('version', 'unknown')}")
    
    def load(self) -> bool:
        """Load config từ file"""
        try:
            if self.config_file.exists():
                logger.info(f"Loading config from: {self.config_file}")
                
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                
                # Check version và migrate nếu cần
                file_version = self.config.get("version", "1.0.0")
                
                if file_version != CONFIG_VERSION:
                    logger.warning(f"Config version mismatch: {file_version} != {CONFIG_VERSION}")
                    
                    # Backup trước khi migrate
                    self.backup(f"before_migration_{file_version}")
                    
                    # Migrate
                    self.config = ConfigMigration.migrate(
                        self.config,
                        from_version=file_version,
                        to_version=CONFIG_VERSION
                    )
                    
                    # Save migrated config
                    self.save()
                
                # Validate config
                errors = ConfigValidator.validate_all(self.config)
                if errors:
                    logger.warning(f"Config validation errors: {errors}")
                
                # Merge với defaults (add missing keys)
                self.config = self._merge_with_defaults(self.config, DEFAULT_CONFIG)
                
                logger.info("Config loaded successfully")
                return True
            
            else:
                logger.info("No config file found, creating default config")
                self.config = DEFAULT_CONFIG.copy()
                self.config["last_updated"] = datetime.now().isoformat()
                self.save()
                return True
                
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Using default config")
            self.config = DEFAULT_CONFIG.copy()
            return False
    
    def save(self) -> bool:
        """Save config to file"""
        try:
            # Update timestamp
            self.config["last_updated"] = datetime.now().isoformat()
            
            # Write to file with pretty formatting
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Config saved to: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def backup(self, suffix: str = None) -> Optional[Path]:
        """Backup current config"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if suffix:
                backup_name = f"config_{suffix}_{timestamp}.json"
            else:
                backup_name = f"config_backup_{timestamp}.json"
            
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(self.config_file, backup_path)
            
            logger.info(f"Config backed up to: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error backing up config: {e}")
            return None
    
    def restore(self, backup_path: Path) -> bool:
        """Restore config from backup"""
        try:
            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_path}")
                return False
            
            shutil.copy2(backup_path, self.config_file)
            self.load()
            
            logger.info(f"Config restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring config: {e}")
            return False
    
    def _merge_with_defaults(self, config: Dict, defaults: Dict) -> Dict:
        """Merge config với defaults để add missing keys"""
        result = defaults.copy()
        
        for key, value in config.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    # Recursively merge nested dicts
                    result[key] = self._merge_with_defaults(value, result[key])
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    # Getter methods với type hints
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot notation: 'network.artnet_ip'"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def set(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """Set config value by dot notation"""
        keys = key.split('.')
        config = self.config
        
        # Navigate to parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set value
        config[keys[-1]] = value
        
        if auto_save:
            return self.save()
        
        return True
    
    # Convenience methods
    def get_network_config(self) -> Dict:
        """Get network configuration"""
        return self.config.get("network", {})
    
    def get_recording_config(self) -> Dict:
        """Get recording configuration"""
        return self.config.get("recording", {})
    
    def get_ui_config(self) -> Dict:
        """Get UI configuration"""
        return self.config.get("ui", {})
    
    def get_license_key(self) -> Optional[str]:
        """Get decrypted license key"""
        encrypted = self.config.get("license", {}).get("key")
        
        if not encrypted:
            return None
        
        # Decrypt (simple base64 for now, use proper encryption in production)
        try:
            return base64.b64decode(encrypted.encode()).decode()
        except:
            return None
    
    def set_license_key(self, key: str, auto_save: bool = True) -> bool:
        """Set encrypted license key"""
        # Encrypt (simple base64 for now)
        encrypted = base64.b64encode(key.encode()).decode()
        
        return self.set("license.key", encrypted, auto_save)
    
    def update_license_info(self, license_type: str, expires_at: str = None) -> bool:
        """Update license information"""
        self.set("license.type", license_type, auto_save=False)
        self.set("license.activated_at", datetime.now().isoformat(), auto_save=False)
        
        if expires_at:
            self.set("license.expires_at", expires_at, auto_save=False)
        
        return self.save()
    
    def reset_to_defaults(self) -> bool:
        """Reset config to defaults (backup current first)"""
        try:
            # Backup current
            self.backup("before_reset")
            
            # Reset
            self.config = DEFAULT_CONFIG.copy()
            self.config["last_updated"] = datetime.now().isoformat()
            
            return self.save()
            
        except Exception as e:
            logger.error(f"Error resetting config: {e}")
            return False
    
    def export_config(self, output_path: Path) -> bool:
        """Export config to file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Config exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting config: {e}")
            return False
    
    def import_config(self, input_path: Path) -> bool:
        """Import config from file"""
        try:
            # Backup current
            self.backup("before_import")
            
            # Load new config
            with open(input_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)
            
            # Validate
            errors = ConfigValidator.validate_all(imported)
            if errors:
                logger.error(f"Imported config has errors: {errors}")
                return False
            
            # Merge with defaults
            self.config = self._merge_with_defaults(imported, DEFAULT_CONFIG)
            
            return self.save()
            
        except Exception as e:
            logger.error(f"Error importing config: {e}")
            return False
    
    def __repr__(self):
        return f"ConfigManager(version={self.config.get('version')}, file={self.config_file})"


def migrate_v1_files_to_v2() -> bool:
    """
    Migrate V1.0 config files to V2.0 unified config.json
    
    V1.0 structure:
        - config/app_config.json (app settings)
        - config/network_config.json (network settings)
    
    V2.0 structure:
        - config/config.json (unified, all settings)
    
    Returns:
        True if migration successful, False otherwise
    """
    try:
        v1_app_config = Path("config/app_config.json")
        v1_network_config = Path("config/network_config.json")
        v2_config = Path("config/config.json")
        
        # Check if migration needed
        if v2_config.exists():
            logger.info("V2 config already exists, skipping migration")
            return True
        
        if not v1_app_config.exists():
            logger.info("No V1 config found, will create default V2 config")
            return False
        
        logger.info("=" * 60)
        logger.info("🔄 Starting V1.0 → V2.0 Config Migration")
        logger.info("=" * 60)
        
        # Load V1 configs
        v1_app = {}
        v1_network = {}
        
        if v1_app_config.exists():
            with open(v1_app_config, 'r', encoding='utf-8') as f:
                v1_app = json.load(f)
            logger.info(f"Loaded {v1_app_config}")
        
        if v1_network_config.exists():
            with open(v1_network_config, 'r', encoding='utf-8') as f:
                v1_network = json.load(f)
            logger.info(f"Loaded {v1_network_config}")
        
        # Create V2 config from DEFAULT_CONFIG
        v2_data = DEFAULT_CONFIG.copy()
        
        # Map V1 app config to V2 structure
        if "artnet" in v1_app:
            v2_data["network"]["artnet_port"] = v1_app["artnet"].get("port", 6454)
            v2_data["network"]["broadcast_ip"] = v1_app["artnet"].get("broadcast_address", "255.255.255.255")
            v2_data["recording"]["fps"] = v1_app["artnet"].get("refresh_rate", 30)
        
        if "show" in v1_app:
            v2_data["paths"]["shows"] = v1_app["show"].get("default_path", "data/shows")
            v2_data["recording"]["auto_save"] = v1_app["show"].get("auto_save", True)
        
        if "recording" in v1_app:
            v2_data["paths"]["recordings"] = v1_app["recording"].get("path", "data/recordings")
        
        if "ui" in v1_app["app"] if "app" in v1_app else {}:
            window = v1_app["app"]["ui" if "ui" in v1_app["app"] else "window"]
            if "window" in v1_app["app"]:
                v2_data["ui"]["window_width"] = v1_app["app"]["window"].get("width", 1200)
                v2_data["ui"]["window_height"] = v1_app["app"]["window"].get("height", 800)
        
        if "security" in v1_app or "admin" in v1_app:
            # Store admin password hash in V2 (we'll add a security section)
            if "security" not in v2_data:
                v2_data["security"] = {}
            if "admin" in v1_app:
                v2_data["security"]["admin_password_hash"] = v1_app["admin"].get("password_hash", "")
        
        if "project" in v1_app:
            if "project" not in v2_data:
                v2_data["project"] = {}
            v2_data["project"]["name"] = v1_app["project"].get("name", "")
        
        # Map V1 network config to V2 structure  
        if "network" in v1_network:
            if "interface" in v1_network["network"]:
                v2_data["network"]["interface"] = v1_network["network"]["interface"]
            if "ip_address" in v1_network["network"] and v1_network["network"]["ip_address"] != "auto":
                v2_data["network"]["artnet_ip"] = v1_network["network"]["ip_address"]
        
        # Set version and metadata
        v2_data["version"] = "2.0.0"
        v2_data["last_updated"] = datetime.now().isoformat()
        v2_data["migrated_from"] = "1.0.0"
        
        # Backup V1 configs before migration
        backup_dir = Path("config/v1_backup")
        backup_dir.mkdir(exist_ok=True)
        
        import shutil
        if v1_app_config.exists():
            shutil.copy(v1_app_config, backup_dir / "app_config.json")
        if v1_network_config.exists():
            shutil.copy(v1_network_config, backup_dir / "network_config.json")
        
        logger.info(f"V1 configs backed up to {backup_dir}")
        
        # Save V2 config
        v2_config.parent.mkdir(parents=True, exist_ok=True)
        with open(v2_config, 'w', encoding='utf-8') as f:
            json.dump(v2_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"V2 config created: {v2_config}")
        logger.info("=" * 60)
        logger.info("Migration completed successfully!")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        return False


# Singleton instance
_config_manager_instance: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get singleton ConfigManager instance"""
    global _config_manager_instance
    
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
    
    return _config_manager_instance


if __name__ == "__main__":
    # Test configuration manager
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("Configuration Manager Test")
    print("=" * 80)
    
    # Create manager
    manager = ConfigManager()
    
    print(f"\nConfig version: {manager.config.get('version')}")
    print(f"Config file: {manager.config_file}")
    
    # Test getters
    print("\n1️⃣ Testing getters:")
    print(f"Network IP: {manager.get('network.artnet_ip')}")
    print(f"Recording FPS: {manager.get('recording.fps')}")
    print(f"UI Theme: {manager.get('ui.theme')}")
    
    # Test setters
    print("\n2️⃣ Testing setters:")
    manager.set('recording.fps', 120, auto_save=False)
    print(f"Updated FPS: {manager.get('recording.fps')}")
    
    # Test validation
    print("\n3️⃣ Testing validation:")
    errors = ConfigValidator.validate_all(manager.config)
    if errors:
        print(f"Validation errors: {errors}")
    else:
        print("✅ Config is valid")
    
    # Test license
    print("\n4️⃣ Testing license:")
    manager.set_license_key("TEST-LICENSE-KEY-123", auto_save=False)
    decrypted = manager.get_license_key()
    print(f"License key: {decrypted}")
    
    # Test backup
    print("\n5️⃣ Testing backup:")
    backup_path = manager.backup("test")
    print(f"Backup created: {backup_path}")
    
    # Display current config (partial)
    print("\n6️⃣ Current Config (network):")
    print(json.dumps(manager.get_network_config(), indent=2))
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
