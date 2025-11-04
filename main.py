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
from gui.main_window import MainWindow
from system.crash_reporter import setup_logging, setup_exception_handler
from utils.config import ConfigManager

def main():
    """Main entry point của ứng dụng"""

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