"""
Art-Net Controller - Main Entry Point
Phần mềm điều khiển Art-Net với GUI đầy đủ tính năng
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.gui.main_window import MainWindow
from src.system.crash_reporter import setup_logging, setup_exception_handler
from src.utils.config import ConfigManager

def main():
    """Main entry point của ứng dụng"""

    # Ensure logs folder exists in dist (for exe build)
    logs_path = Path(__file__).parent / "logs"
    if not logs_path.exists():
        try:
            logs_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Cannot create logs folder: {logs_path} - {e}")

    # Setup enhanced logging (V2.0 - with rotation & compression)
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Setup global exception handler (V2.0 - crash reporting)
    setup_exception_handler()

    try:
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("DMX Master")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("ArtNet Studio")
        
        # Set application style
        app.setStyle('Fusion')
        
        # Load configuration
        config_manager = ConfigManager()
        
        # Create and show main window
        main_window = MainWindow()
        main_window.show()
        
        logger.info("Art-Net Controller started successfully")
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()