"""
Run script for Art-Net Controller
Usage: python run.py [--port PORT] [--debug]
"""

import sys
import argparse
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Main entry point with command line arguments"""
    parser = argparse.ArgumentParser(description='Art-Net Controller')
    parser.add_argument('--port', type=int, default=6454, help='Art-Net port (default: 6454)')
    parser.add_argument('--webport', type=int, default=8080, help='Web server port (default: 8080)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-artnet', action='store_true', help='Disable Art-Net on startup')
    parser.add_argument('--no-webserver', action='store_true', help='Disable web server on startup')
    
    args = parser.parse_args()
    
    # Import after adding src to path
    from PyQt6.QtWidgets import QApplication
    from gui.main_window import MainWindow
    from utils.logger import setup_logging
    from utils.config import ConfigManager
    
    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logging(log_level)
    
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
        
        # Override config with command line arguments
        if args.port != 6454:
            config_manager.set_app_config('artnet.port', args.port)
        
        if args.webport != 8080:
            config_manager.set_app_config('webserver.port', args.webport)
        
        if args.no_artnet:
            config_manager.set_app_config('artnet.auto_start', False)
        
        if args.no_webserver:
            config_manager.set_app_config('webserver.enabled', False)
        
        # Create and show main window
        main_window = MainWindow(config_manager)
        main_window.show()
        
        logger.info(f"Art-Net Controller started successfully")
        logger.info(f"Art-Net port: {config_manager.get_app_config('artnet.port', 6454)}")
        logger.info(f"Web server port: {config_manager.get_app_config('webserver.port', 8080)}")
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()