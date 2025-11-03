#!/usr/bin/env python3
"""
Simple test for Art-Net Controller
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Art-Net Controller - Simple Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Title label
        title = QLabel("Art-Net Controller - Test Version")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Status label
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_artnet_btn = QPushButton("Test Art-Net Import")
        self.test_artnet_btn.clicked.connect(self.test_artnet_import)
        button_layout.addWidget(self.test_artnet_btn)
        
        self.test_webserver_btn = QPushButton("Test Webserver Import")
        self.test_webserver_btn.clicked.connect(self.test_webserver_import)
        button_layout.addWidget(self.test_webserver_btn)
        
        self.test_gui_btn = QPushButton("Test GUI Components")
        self.test_gui_btn.clicked.connect(self.test_gui_components)
        button_layout.addWidget(self.test_gui_btn)
        
        layout.addLayout(button_layout)
        
        # Apply dark theme
        self.apply_dark_theme()
        
        logger.info("Simple test window initialized")
    
    def apply_dark_theme(self):
        """Apply dark theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
                padding: 5px;
            }
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
    
    def test_artnet_import(self):
        """Test Art-Net module import"""
        try:
            from artnet.controller import ArtNetController
            self.status_label.setText("Status: Art-Net module imported successfully ✓")
            logger.info("Art-Net controller import successful")
        except Exception as e:
            self.status_label.setText(f"Status: Art-Net import failed: {str(e)}")
            logger.error(f"Art-Net import failed: {e}")
    
    def test_webserver_import(self):
        """Test webserver module import"""
        try:
            from webserver.server import MP3UploadServer
            self.status_label.setText("Status: Webserver module imported successfully ✓")
            logger.info("Webserver import successful")
        except Exception as e:
            self.status_label.setText(f"Status: Webserver import failed: {str(e)}")
            logger.error(f"Webserver import failed: {e}")
    
    def test_gui_components(self):
        """Test GUI components import"""
        try:
            from gui.tabs.live_control import LiveControlTab
            from gui.tabs.hardware_manager import HardwareManagerTab
            from gui.tabs.dmx_view import DMXViewTab
            from gui.tabs.settings import SettingsTab
            from gui.tabs.record import RecordTab
            self.status_label.setText("Status: All GUI components imported successfully ✓")
            logger.info("GUI components import successful")
        except Exception as e:
            self.status_label.setText(f"Status: GUI components import failed: {str(e)}")
            logger.error(f"GUI components import failed: {e}")

def main():
    """Main function"""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Art-Net Controller Test")
    app.setApplicationVersion("1.0")
    
    # Create main window
    window = SimpleTestWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()