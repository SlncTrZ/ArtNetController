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
from utils.logger import setup_logging
from utils.config import ConfigManager

def main():
    """Main entry point của ứng dụng"""
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("Art-Net Controller")
        app.setApplicationVersion("1.0.0")
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
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()