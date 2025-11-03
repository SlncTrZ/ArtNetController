"""
Status Widget - Widget hiển thị trạng thái hệ thống
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QBrush

class StatusWidget(QWidget):
    """Widget hiển thị trạng thái trong status bar"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        # Art-Net status
        self.artnet_status_label = QLabel("Art-Net: ")
        self.artnet_indicator = QLabel()
        self.artnet_indicator.setFixedSize(12, 12)
        
        # Node count
        self.node_count_label = QLabel("Nodes: 0")
        
        # Universe info  
        self.universe_label = QLabel("Universes: -")
        
        # IP address info
        self.ip_label = QLabel("IP: Detecting...")
        self.ip_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        
        # Add to layout
        layout.addWidget(self.artnet_status_label)
        layout.addWidget(self.artnet_indicator)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.node_count_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.universe_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.ip_label)
        
        # Initial state
        self.set_artnet_status(False)
    
    def set_artnet_status(self, active: bool):
        """Set Art-Net status"""
        self.artnet_status_label.setText(f"Art-Net: {'Online' if active else 'Offline'}")
        
        # Create status indicator
        pixmap = QPixmap(12, 12)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if active:
            painter.setBrush(QBrush(Qt.GlobalColor.green))
        else:
            painter.setBrush(QBrush(Qt.GlobalColor.red))
        
        painter.drawEllipse(1, 1, 10, 10)
        painter.end()
        
        self.artnet_indicator.setPixmap(pixmap)
    
    def set_node_count(self, count: int):
        """Set node count"""
        self.node_count_label.setText(f"Nodes: {count}")
    
    def set_active_universes(self, universes: list):
        """Set active universes"""
        if universes:
            universe_str = ", ".join(map(str, sorted(universes)))
            self.universe_label.setText(f"Universes: {universe_str}")
        else:
            self.universe_label.setText("Universes: -")
    
    def set_ip_address(self, ip: str):
        """Set IP address"""
        self.ip_label.setText(f"IP: {ip}")