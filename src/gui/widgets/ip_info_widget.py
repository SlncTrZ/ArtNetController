"""
IP Information Widget
Hiển thị thông tin IP và hướng dẫn kết nối Art-Net cho external devices
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QTextEdit, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QClipboard

from src.utils.network import get_artnet_connection_info, get_primary_ip

logger = logging.getLogger(__name__)

class IPInfoWidget(QWidget):
    """Widget hiển thị thông tin IP và kết nối Art-Net"""
    
    ip_changed = pyqtSignal(str)  # Emit when IP changes
    
    def __init__(self):
        super().__init__()
        self.current_ip = ""
        self.init_ui()
        self.setup_timer()
        self.update_ip_info()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        
        # Main group box
        self.group_box = QGroupBox("Art-Net Connection Info")
        group_layout = QVBoxLayout(self.group_box)
        
        # Primary IP display
        ip_layout = QHBoxLayout()
        
        self.ip_label = QLabel("IP Address:")
        self.ip_label.setStyleSheet("font-weight: bold; color: #0078d4;")
        ip_layout.addWidget(self.ip_label)
        
        self.ip_value = QLabel("Detecting...")
        self.ip_value.setStyleSheet("font-family: 'Courier New'; font-size: 14px; background-color: #3c3c3c; padding: 5px; border: 1px solid #555; border-radius: 3px;")
        self.ip_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        ip_layout.addWidget(self.ip_value)
        
        self.copy_ip_btn = QPushButton("Copy IP")
        self.copy_ip_btn.setMaximumWidth(80)
        self.copy_ip_btn.clicked.connect(self.copy_ip_to_clipboard)
        ip_layout.addWidget(self.copy_ip_btn)
        
        ip_layout.addStretch()
        group_layout.addLayout(ip_layout)
        
        # Port info
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Art-Net Port:"))
        port_value = QLabel("6454")
        port_value.setStyleSheet("font-family: 'Courier New'; font-weight: bold;")
        port_layout.addWidget(port_value)
        port_layout.addStretch()
        group_layout.addLayout(port_layout)
        
        # Instructions
        instructions_label = QLabel("Instructions for External Software:")
        instructions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        group_layout.addWidget(instructions_label)
        
        self.instructions_text = QTextEdit()
        self.instructions_text.setMaximumHeight(120)
        self.instructions_text.setReadOnly(True)
        self.instructions_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe UI';
                font-size: 11px;
            }
        """)
        group_layout.addWidget(self.instructions_text)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh IP")
        self.refresh_btn.clicked.connect(self.update_ip_info)
        button_layout.addWidget(self.refresh_btn)
        
        self.copy_all_btn = QPushButton("📋 Copy All Info")
        self.copy_all_btn.clicked.connect(self.copy_all_info)
        button_layout.addWidget(self.copy_all_btn)
        
        button_layout.addStretch()
        group_layout.addLayout(button_layout)
        
        layout.addWidget(self.group_box)
        layout.addStretch()
        
        # Apply styling
        self.apply_styling()
    
    def apply_styling(self):
        """Apply widget styling"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
                background-color: #3c3c3c;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            
            QLabel {
                color: #ffffff;
                padding: 2px;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
    
    def setup_timer(self):
        """Setup timer to check for IP changes"""
        self.ip_timer = QTimer()
        self.ip_timer.timeout.connect(self.check_ip_change)
        self.ip_timer.start(10000)  # Check every 10 seconds
    
    def update_ip_info(self):
        """Update IP information display"""
        try:
            connection_info = get_artnet_connection_info()
            
            # Update IP display
            primary_ip = connection_info["primary_ip"]
            self.ip_value.setText(primary_ip)
            
            # Check if IP changed
            if primary_ip != self.current_ip:
                self.current_ip = primary_ip
                self.ip_changed.emit(primary_ip)
                logger.info(f"IP address updated: {primary_ip}")
            
            # Update instructions
            instructions = self.format_instructions(connection_info)
            self.instructions_text.setPlainText(instructions)
            
        except Exception as e:
            logger.error(f"Failed to update IP info: {e}")
            self.ip_value.setText("Error")
            self.instructions_text.setPlainText("Failed to detect network information")
    
    def format_instructions(self, connection_info):
        """Format instructions text"""
        primary_ip = connection_info["primary_ip"]
        all_ips = connection_info["all_ips"]
        
        instructions = f"""Setup cho External Software (Depence, Resolume, Madrix5, etc.):

1. Art-Net Output Settings:
   • IP Address: {primary_ip}
   • Port: 6454 (Art-Net standard)
   • Protocol: Art-Net v4
   • Universe: 0-32767 (tùy theo thiết lập)

2. Network Setup:
   • Đảm bảo cùng mạng LAN/WiFi với máy này
   • Tắt Firewall hoặc cho phép port 6454
   • Kiểm tra không có software khác dùng port 6454

3. Available IP addresses:"""
        
        for i, ip in enumerate(all_ips):
            status = " (Primary)" if ip == primary_ip else " (Alternative)" if ip != "127.0.0.1" else " (Localhost only)"
            instructions += f"\n   • {ip}{status}"
        
        return instructions
    
    def check_ip_change(self):
        """Check if IP address has changed"""
        new_ip = get_primary_ip()
        if new_ip != self.current_ip:
            self.update_ip_info()
    
    def copy_ip_to_clipboard(self):
        """Copy IP address to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.current_ip)
        
        # Show temporary message
        self.copy_ip_btn.setText("Copied!")
        QTimer.singleShot(2000, lambda: self.copy_ip_btn.setText("Copy IP"))
    
    def copy_all_info(self):
        """Copy all connection info to clipboard"""
        try:
            connection_info = get_artnet_connection_info()
            
            text = f"""Art-Net Connection Information
IP Address: {connection_info['primary_ip']}
Port: {connection_info['artnet_port']}
Connection String: {connection_info['connection_string']}

Instructions:
""" + "\n".join(connection_info['instructions'])
            
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            
            # Show temporary message
            self.copy_all_btn.setText("Copied!")
            QTimer.singleShot(2000, lambda: self.copy_all_btn.setText("📋 Copy All Info"))
            
        except Exception as e:
            logger.error(f"Failed to copy info: {e}")
            QMessageBox.warning(self, "Error", f"Failed to copy information: {e}")
    
    def get_current_ip(self):
        """Get current IP address"""
        return self.current_ip