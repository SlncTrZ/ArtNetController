"""
Utility functions and classes
"""

import sys
import logging
import json
import os
from pathlib import Path
from typing import Dict, Any

def get_config_dir():
    """Get config directory that has write permissions"""
    if sys.platform == 'win32':
        # Windows: Use AppData/Local
        appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        config_dir = Path(appdata) / "DMX Master LTS" / "config"
    else:
        # Linux/Mac: Use home directory
        config_dir = Path.home() / ".dmx-master-lts" / "config"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

class ConfigManager:
    """Quản lý cấu hình ứng dụng"""
    
    def __init__(self, config_dir: str = None):
        # Use AppData config directory if not specified
        if config_dir is None:
            self.config_dir = get_config_dir()
        else:
            self.config_dir = Path(config_dir)
        
        self.app_config = {}
        self.network_config = {}
        
        self.load_configs()
    
    def load_configs(self):
        """Load tất cả config files"""
        try:
            # Load app config
            app_config_path = self.config_dir / "app_config.json"
            if app_config_path.exists():
                with open(app_config_path, 'r', encoding='utf-8') as f:
                    self.app_config = json.load(f)
            
            # Load network config
            network_config_path = self.config_dir / "network_config.json"
            if network_config_path.exists():
                with open(network_config_path, 'r', encoding='utf-8') as f:
                    self.network_config = json.load(f)
                    
        except Exception as e:
            logging.error(f"Failed to load configs: {e}")
    
    def save_configs(self):
        """Lưu tất cả config files"""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(exist_ok=True)
            
            # Save app config
            app_config_path = self.config_dir / "app_config.json"
            with open(app_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.app_config, f, indent=2, ensure_ascii=False)
            
            # Save network config
            network_config_path = self.config_dir / "network_config.json"
            with open(network_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.network_config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logging.error(f"Failed to save configs: {e}")
    
    def get_app_config(self, key: str = None, default=None):
        """Lấy app config"""
        if key is None:
            return self.app_config
        
        keys = key.split('.')
        value = self.app_config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set_app_config(self, key: str, value: Any):
        """Set app config"""
        keys = key.split('.')
        config = self.app_config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_network_config(self, key: str = None, default=None):
        """Lấy network config"""
        if key is None:
            return self.network_config
        
        keys = key.split('.')
        value = self.network_config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set_network_config(self, key: str, value: Any):
        """Set network config"""
        keys = key.split('.')
        config = self.network_config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value