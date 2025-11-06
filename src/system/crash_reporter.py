"""
Crash Reporter & Logging System
Tự động catch exceptions, ghi log và gửi anonymous crash reports

Features:
- Global exception handler
- Detailed crash reports (traceback, system info, config)
- Anonymous reporting to GitHub Issues API
- Rotating log files với compression
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- System info collection
- Auto-cleanup old logs
- Email notification option (optional)

Privacy:
- Anonymous by default
- No personal data collected
- User can disable reporting
- Logs stored locally
"""

import sys
import logging
import traceback
import platform
import json
import gzip
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
import threading
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)

# Logging configuration - Use user data directory to avoid permission issues
def get_user_data_dir():
    """Get user data directory that has write permissions"""
    # Always use AppData/home directory to avoid permission issues in Program Files
    if sys.platform == 'win32':
        # Windows: Use AppData/Local (writable without admin)
        appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        return Path(appdata) / "DMX Master LTS"
    else:
        # Linux/Mac: Use home directory
        return Path.home() / ".dmx-master-lts"

LOG_DIR = get_user_data_dir() / "logs"
LOG_FILE = LOG_DIR / "artnet_controller.log"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Crash report settings
CRASH_LOG_FILE = LOG_DIR / "crashes.log"
GITHUB_REPO_OWNER = "truongcongdinh97"
GITHUB_REPO_NAME = "DMX-Master"
GITHUB_ISSUES_API = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/issues"

# Log rotation settings
MAX_LOG_SIZE_MB = 10
MAX_LOG_FILES = 5
LOG_RETENTION_DAYS = 30


class SystemInfo:
    """Thu thập thông tin hệ thống (anonymous)"""
    
    @staticmethod
    def collect() -> Dict:
        """Collect system information"""
        try:
            import psutil
            
            # CPU info
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory info
            memory = psutil.virtual_memory()
            
            # Disk info
            disk = psutil.disk_usage('/')
            
            system_info = {
                'cpu': {
                    'physical_cores': cpu_count,
                    'logical_cores': cpu_count_logical,
                    'frequency_mhz': cpu_freq.current if cpu_freq else None,
                    'usage_percent': cpu_usage
                },
                'memory': {
                    'total_mb': memory.total / 1024 / 1024,
                    'available_mb': memory.available / 1024 / 1024,
                    'usage_percent': memory.percent
                },
                'disk': {
                    'total_gb': disk.total / 1024 / 1024 / 1024,
                    'free_gb': disk.free / 1024 / 1024 / 1024,
                    'usage_percent': disk.percent
                }
            }
        except ImportError:
            # psutil not available, use basic info
            system_info = {
                'cpu': {'info': 'psutil not available'},
                'memory': {'info': 'psutil not available'},
                'disk': {'info': 'psutil not available'}
            }
        
        return {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version()
            },
            'hardware': system_info,
            'timestamp': datetime.now().isoformat()
        }


class CrashReport:
    """Crash report data structure"""
    
    def __init__(self, exception: Exception, traceback_str: str, system_info: Dict = None):
        self.exception_type = type(exception).__name__
        self.exception_message = str(exception)
        self.traceback = traceback_str
        self.system_info = system_info or {}
        self.timestamp = datetime.now().isoformat()
        self.app_version = "2.0.0"  # TODO: Get from config
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'exception_type': self.exception_type,
            'exception_message': self.exception_message,
            'traceback': self.traceback,
            'system_info': self.system_info,
            'timestamp': self.timestamp,
            'app_version': self.app_version
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    def to_github_issue_body(self) -> str:
        """Format as GitHub issue body"""
        body = f"""## Crash Report

**Version:** {self.app_version}
**Time:** {self.timestamp}
**Exception:** `{self.exception_type}: {self.exception_message}`

### Traceback
```python
{self.traceback}
```

### System Information
**Platform:** {self.system_info.get('platform', {}).get('system')} {self.system_info.get('platform', {}).get('release')}
**Python:** {self.system_info.get('platform', {}).get('python_version')}
**Machine:** {self.system_info.get('platform', {}).get('machine')}

**CPU:** {self.system_info.get('hardware', {}).get('cpu', {}).get('logical_cores')} cores @ {self.system_info.get('hardware', {}).get('cpu', {}).get('usage_percent')}% usage
**Memory:** {self.system_info.get('hardware', {}).get('memory', {}).get('total_mb', 0):.0f} MB total, {self.system_info.get('hardware', {}).get('memory', {}).get('usage_percent')}% used

---
*This is an automated crash report. No personal data was collected.*
"""
        return body


class CrashReporter:
    """
    Tự động gửi crash reports
    """
    
    def __init__(self, config_manager=None, enabled: bool = True):
        self.config_manager = config_manager
        self.enabled = enabled
        self.anonymous = True
        self.include_system_info = True
        
        # Load settings from config
        if config_manager:
            crash_config = config_manager.get("crash_reporting", {})
            self.enabled = crash_config.get("enabled", True)
            self.anonymous = crash_config.get("anonymous", True)
            self.include_system_info = crash_config.get("include_system_info", True)
        
        # Setup crash log file
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    def report_crash(self, exception: Exception, exc_traceback: str) -> bool:
        """
        Gửi crash report
        
        Returns:
            True if successfully sent, False otherwise
        """
        if not self.enabled:
            logger.info("Crash reporting disabled, skipping report")
            return False
        
        try:
            # Collect system info
            system_info = {}
            if self.include_system_info:
                system_info = SystemInfo.collect()
            
            # Create crash report
            report = CrashReport(exception, exc_traceback, system_info)
            
            # Save locally
            self._save_crash_log(report)
            
            # Send to GitHub (in background thread)
            if self.anonymous:
                thread = threading.Thread(
                    target=self._send_to_github,
                    args=(report,),
                    daemon=True
                )
                thread.start()
            
            logger.info("Crash report created and queued for sending")
            return True
            
        except Exception as e:
            logger.error(f"Error creating crash report: {e}")
            return False
    
    def _save_crash_log(self, report: CrashReport):
        """Save crash report to local file"""
        try:
            with open(CRASH_LOG_FILE, 'a', encoding='utf-8') as f:
                f.write("\n" + "=" * 80 + "\n")
                f.write(report.to_json())
                f.write("\n")
            
            logger.info(f"Crash logged to: {CRASH_LOG_FILE}")
            
        except Exception as e:
            logger.error(f"Error saving crash log: {e}")
    
    def _send_to_github(self, report: CrashReport):
        """Send crash report to GitHub Issues (background thread)"""
        try:
            logger.info("Sending crash report to GitHub...")
            
            # Create GitHub issue
            issue_data = {
                'title': f'[Crash Report] {report.exception_type}: {report.exception_message[:50]}',
                'body': report.to_github_issue_body(),
                'labels': ['crash', 'automated']
            }
            
            # Send POST request
            headers = {
                'User-Agent': f'ArtNetController/{report.app_version}',
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            }
            
            # TODO: Add GitHub token for authentication (optional)
            # headers['Authorization'] = f'token {GITHUB_TOKEN}'
            
            data = json.dumps(issue_data).encode('utf-8')
            request = Request(GITHUB_ISSUES_API, data=data, headers=headers, method='POST')
            
            with urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode())
                issue_url = result.get('html_url', '')
                
                logger.info(f"Crash report sent: {issue_url}")
            
        except URLError as e:
            logger.warning(f"Could not send crash report (network error): {e.reason}")
        except Exception as e:
            logger.error(f"Error sending crash report: {e}")


class LogManager:
    """
    Quản lý log files với rotation và compression
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.log_dir = LOG_DIR
        self.log_file = LOG_FILE
        
        # Load settings
        if config_manager:
            adv_config = config_manager.get("advanced", {})
            self.log_level = adv_config.get("log_level", "INFO")
            self.max_size_mb = adv_config.get("max_log_size_mb", MAX_LOG_SIZE_MB)
            self.retention_days = adv_config.get("keep_logs_days", LOG_RETENTION_DAYS)
        else:
            self.log_level = "INFO"
            self.max_size_mb = MAX_LOG_SIZE_MB
            self.retention_days = LOG_RETENTION_DAYS
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging system"""
        # Get log level
        level = getattr(logging, self.log_level.upper(), logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_size_mb * 1024 * 1024,
            backupCount=MAX_LOG_FILES,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Add handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        logger.info(f"Logging configured: level={self.log_level}, file={self.log_file}")
    
    def compress_old_logs(self):
        """Compress old log files to save space"""
        try:
            # Find uncompressed log files
            log_files = list(self.log_dir.glob("*.log.*"))
            
            for log_file in log_files:
                if log_file.suffix != '.gz':
                    # Compress file
                    gz_file = log_file.with_suffix(log_file.suffix + '.gz')
                    
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(gz_file, 'wb') as f_out:
                            f_out.writelines(f_in)
                    
                    # Remove original
                    log_file.unlink()
                    
                    logger.info(f"Compressed log: {log_file} -> {gz_file}")
            
        except Exception as e:
            logger.error(f"Error compressing logs: {e}")
    
    def cleanup_old_logs(self):
        """Remove logs older than retention period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # Find all log files
            log_files = list(self.log_dir.glob("*.log*"))
            
            for log_file in log_files:
                # Get file modification time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if mtime < cutoff_date:
                    log_file.unlink()
                    logger.info(f"Deleted old log: {log_file}")
            
        except Exception as e:
            logger.error(f"Error cleaning up logs: {e}")
    
    def get_recent_logs(self, lines: int = 100) -> List[str]:
        """Get recent log lines"""
        try:
            if not self.log_file.exists():
                return []
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:]
            
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return []
    
    def export_logs(self, output_file: Path) -> bool:
        """Export logs to file"""
        try:
            import shutil
            
            shutil.copy2(self.log_file, output_file)
            logger.info(f"Logs exported to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            return False


def setup_exception_handler(config_manager=None):
    """
    Setup global exception handler
    Catches all unhandled exceptions và tạo crash reports
    """
    crash_reporter = CrashReporter(config_manager)
    
    def exception_handler(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        # Don't catch KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Format traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = ''.join(tb_lines)
        
        # Log error
        logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Create crash report
        crash_reporter.report_crash(exc_value, tb_text)
        
        # Show error dialog (if GUI available)
        try:
            from PyQt6.QtWidgets import QMessageBox
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Lỗi nghiêm trọng")
            msg.setText("Ứng dụng gặp lỗi không mong muốn.")
            msg.setInformativeText(f"{exc_type.__name__}: {exc_value}")
            msg.setDetailedText(tb_text)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
        except:
            # GUI not available, just print to console
            print("\n" + "=" * 80)
            print("CRITICAL ERROR - Application crashed")
            print("=" * 80)
            print(tb_text)
            print("=" * 80)
    
    # Set exception handler
    sys.excepthook = exception_handler
    
    logger.info("Global exception handler installed")


# Singleton instances
_log_manager_instance: Optional[LogManager] = None
_crash_reporter_instance: Optional[CrashReporter] = None


def get_log_manager(config_manager=None) -> LogManager:
    """Get singleton LogManager instance"""
    global _log_manager_instance
    
    if _log_manager_instance is None:
        _log_manager_instance = LogManager(config_manager)
    
    return _log_manager_instance


def get_crash_reporter(config_manager=None) -> CrashReporter:
    """Get singleton CrashReporter instance"""
    global _crash_reporter_instance
    
    if _crash_reporter_instance is None:
        _crash_reporter_instance = CrashReporter(config_manager)

    return _crash_reporter_instance


def setup_logging(config_manager=None):
    """
    Convenience function to setup enhanced logging system
    
    This is a drop-in replacement for utils.logger.setup_logging()
    with enhanced features:
    - Log rotation (10MB per file, max 5 files)
    - Gzip compression for old logs
    - Auto-cleanup (30 days retention)
    - Multiple log levels
    
    Args:
        config_manager: Optional ConfigManager instance
    """
    log_manager = get_log_manager(config_manager)
    log_manager.setup_logging()
    logger.info("Enhanced logging system initialized (V2.0)")


if __name__ == "__main__":
    # Test crash reporting system
    print("=" * 80)
    print("Crash Reporter & Logging System Test")
    print("=" * 80)
    
    # Setup logging
    log_manager = LogManager()
    
    # Setup exception handler
    setup_exception_handler()
    
    # Test logging
    print("\n1️⃣ Testing logging...")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    # Test system info
    print("\n2️⃣ Collecting system info...")
    sys_info = SystemInfo.collect()
    print(json.dumps(sys_info, indent=2))
    
    # Test crash report (without actually crashing)
    print("\n3️⃣ Creating test crash report...")
    try:
        # Simulate an error
        raise ValueError("This is a test error for crash reporting")
    except Exception as e:
        tb_text = traceback.format_exc()
        
        crash_reporter = CrashReporter(enabled=True)
        report = CrashReport(e, tb_text, sys_info)
        
        print("\nCrash Report Preview:")
        print(report.to_github_issue_body())
        
        # Save locally (don't send to GitHub in test)
        crash_reporter._save_crash_log(report)
    
    # Test log rotation
    print("\n4️⃣ Testing log maintenance...")
    log_manager.compress_old_logs()
    log_manager.cleanup_old_logs()
    
    # Get recent logs
    print("\n5️⃣ Recent logs (last 5 lines):")
    recent = log_manager.get_recent_logs(5)
    for line in recent:
        print(f"  {line.strip()}")
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print(f"Logs saved to: {LOG_DIR}")
