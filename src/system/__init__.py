"""
System Module - Production Features
Các tính năng hệ thống cho production deployment

Modules:
- config_manager: Quản lý cấu hình tập trung
- update_manager: Tự động cập nhật từ GitHub Releases  
- crash_reporter: Báo cáo lỗi và logging tự động
"""

from .config_manager import ConfigManager, get_config_manager, ConfigValidator
from .update_manager import UpdateManager, Version, ReleaseInfo
from .crash_reporter import (
    LogManager,
    CrashReporter,
    setup_exception_handler,
    get_log_manager,
    get_crash_reporter
)

__all__ = [
    # Config Manager
    'ConfigManager',
    'get_config_manager',
    'ConfigValidator',
    
    # Update Manager
    'UpdateManager',
    'Version',
    'ReleaseInfo',
    
    # Crash Reporter
    'LogManager',
    'CrashReporter',
    'setup_exception_handler',
    'get_log_manager',
    'get_crash_reporter',
]

__version__ = '2.0.0'
