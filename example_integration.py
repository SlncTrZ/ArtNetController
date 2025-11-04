"""
Example: Tích hợp Production Features vào Main Application
Demonstrates how to use all V2.0 production features
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import production system modules
from system import (
    get_config_manager,
    UpdateManager,
    setup_exception_handler,
    get_log_manager
)


def initialize_application():
    """
    Initialize tất cả production features
    Gọi function này đầu tiên trong main()
    """
    
    print("=" * 80)
    print("ArtNetController V2.0 - Initializing...")
    print("=" * 80)
    
    # 1. Load Configuration
    print("\n[1/4] Loading configuration...")
    config = get_config_manager()
    
    print(f"  ✅ Config loaded: v{config.get('version')}")
    print(f"  📁 Config file: {config.config_file}")
    print(f"  🌐 Network: {config.get('network.artnet_ip')}:{config.get('network.artnet_port')}")
    print(f"  🎬 Recording: {config.get('recording.fps')} FPS, {config.get('recording.format')} format")
    print(f"  🎨 UI: {config.get('ui.theme')} theme, {config.get('ui.language')} language")
    
    # 2. Setup Logging
    print("\n[2/4] Setting up logging system...")
    log_manager = get_log_manager(config)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("ArtNetController V2.0 Starting...")
    logger.info("=" * 80)
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Python: {sys.version}")
    
    print(f"  ✅ Logging configured")
    print(f"  📝 Log file: {log_manager.log_file}")
    print(f"  📊 Log level: {log_manager.log_level}")
    
    # 3. Setup Exception Handler
    print("\n[3/4] Installing exception handler...")
    setup_exception_handler(config)
    
    crash_enabled = config.get('crash_reporting.enabled')
    crash_anonymous = config.get('crash_reporting.anonymous')
    
    print(f"  ✅ Exception handler installed")
    print(f"  🛡️  Crash reporting: {'Enabled' if crash_enabled else 'Disabled'}")
    print(f"  🔒 Privacy: {'Anonymous' if crash_anonymous else 'Full details'}")
    
    # 4. Check for Updates
    print("\n[4/4] Checking for updates...")
    
    auto_check = config.get('updates.auto_check')
    
    if auto_check:
        try:
            update_manager = UpdateManager(config)
            
            logger.info("Checking for updates from GitHub...")
            release = update_manager.check_for_updates()
            
            if release:
                print(f"  🎉 Update available: v{release.version}")
                print(f"  📅 Published: {release.published_at}")
                print(f"  📦 Assets: {len(release.assets)} files")
                
                logger.info(f"Update available: v{release.version}")
                
                # Ask user to update (in real app, show dialog)
                # For now, just log
                logger.info("User should be prompted to update")
                
            else:
                print(f"  ✅ Already on latest version")
                logger.info("No updates available")
                
        except Exception as e:
            print(f"  ⚠️  Could not check for updates: {e}")
            logger.warning(f"Update check failed: {e}")
    else:
        print(f"  ⏭️  Auto-check disabled")
        logger.info("Auto-update check is disabled")
    
    print("\n" + "=" * 80)
    print("✅ Initialization complete!")
    print("=" * 80 + "\n")
    
    logger.info("Application initialized successfully")
    
    return config, log_manager


def validate_license(config):
    """Validate license key"""
    logger = logging.getLogger(__name__)
    
    license_key = config.get_license_key()
    license_type = config.get('license.type')
    expires_at = config.get('license.expires_at')
    
    if not license_key:
        logger.warning("No license key found - running in TRIAL mode")
        print("\n⚠️  WARNING: No license key found")
        print("Application running in TRIAL mode")
        print("Some features may be limited\n")
        return False
    
    logger.info(f"License: {license_type}")
    logger.info(f"Expires: {expires_at}")
    
    print(f"\n✅ License validated")
    print(f"Type: {license_type}")
    print(f"Expires: {expires_at}\n")
    
    return True


def demo_configuration_access(config):
    """Demonstrate configuration access"""
    logger = logging.getLogger(__name__)
    
    logger.info("Configuration demo...")
    
    # Get values
    print("\n📖 Configuration Values:")
    print(f"  Network IP: {config.get('network.artnet_ip')}")
    print(f"  Art-Net Port: {config.get('network.artnet_port')}")
    print(f"  Recording FPS: {config.get('recording.fps')}")
    print(f"  UI Theme: {config.get('ui.theme')}")
    
    # Set values (example)
    # config.set('recording.fps', 120)
    # config.set('ui.theme', 'light')
    
    # Get structured config
    network_cfg = config.get_network_config()
    print(f"\n  Network config: {network_cfg}")


def demo_logging():
    """Demonstrate logging"""
    logger = logging.getLogger(__name__)
    
    print("\n📝 Logging Demo:")
    
    logger.debug("This is a DEBUG message (only in debug mode)")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    print("  ✅ Log messages written to logs/artnet_controller.log")


def demo_crash_report():
    """Demonstrate crash reporting (without actually crashing)"""
    logger = logging.getLogger(__name__)
    
    print("\n🛡️  Crash Reporting Demo:")
    print("  Exception handler is installed")
    print("  Any uncaught exception will be automatically reported")
    print("  Try: raise ValueError('Test error') to test it")
    
    # Example: Caught exception (won't trigger crash report)
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error(f"Caught exception: {e}", exc_info=True)
        print(f"  ⚠️  Caught and logged: {e}")


def demo_update_system(config):
    """Demonstrate update system"""
    logger = logging.getLogger(__name__)
    
    print("\n🔄 Update System Demo:")
    
    try:
        update_manager = UpdateManager(config)
        
        print(f"  Current version: v{update_manager.current_version}")
        print(f"  Platform: {update_manager.platform}")
        
        # Manual check (already done in initialization)
        # release = update_manager.check_for_updates()
        
        print("  ✅ Update system ready")
        print("  To update: use UI menu or call auto_update()")
        
    except Exception as e:
        logger.error(f"Update demo error: {e}")
        print(f"  ❌ Error: {e}")


def main():
    """
    Main application entry point
    """
    
    # Initialize production features
    config, log_manager = initialize_application()
    
    # Validate license
    validate_license(config)
    
    # Demonstrate features
    demo_configuration_access(config)
    demo_logging()
    demo_crash_report()
    demo_update_system(config)
    
    # From here, start your actual application
    print("\n" + "=" * 80)
    print("🚀 Ready to start main application")
    print("=" * 80)
    
    # Example: Start PyQt6 GUI
    # from PyQt6.QtWidgets import QApplication
    # from ui.main_window import MainWindow
    # 
    # app = QApplication(sys.argv)
    # window = MainWindow(config)
    # window.show()
    # sys.exit(app.exec())
    
    print("\n✅ Example integration complete!")
    print("See logs/artnet_controller.log for detailed logs")


if __name__ == "__main__":
    main()
