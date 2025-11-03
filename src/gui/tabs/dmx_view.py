"""
DMX View Tab - Tab hiển thị trạng thái DMX
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLabel, QComboBox, QGroupBox, QScrollArea,
                           QSpinBox, QPushButton, QCheckBox, QProgressBar)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette

logger = logging.getLogger(__name__)

class ChannelWidget(QLabel):
    """Widget hiển thị một channel DMX"""
    
    def __init__(self, channel: int):
        super().__init__()
        self.channel = channel
        self.value = 0
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo UI"""
        self.setFixedSize(35, 45)  # Thu nhỏ từ 60x80 -> 35x45
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #555555;
                background-color: #2b2b2b;
                color: white;
                font-size: 7px;
            }
        """)
        self.update_display()
    
    def set_value(self, value: int):
        """Set channel value"""
        self.value = value
        self.update_display()
    
    def update_display(self):
        """Update display"""
        # Color based on value
        if self.value == 0:
            bg_color = "#2b2b2b"
            text_color = "#888888"
        elif self.value < 64:
            bg_color = "#1a3d1a"  # Dark green
            text_color = "#ffffff"
        elif self.value < 128:
            bg_color = "#3d3d1a"  # Dark yellow
            text_color = "#ffffff"
        elif self.value < 192:
            bg_color = "#3d1a1a"  # Dark red
            text_color = "#ffffff"
        else:
            bg_color = "#ff4444"  # Bright red
            text_color = "#ffffff"
        
        self.setStyleSheet(f"""
            QLabel {{
                border: 1px solid #555555;
                background-color: {bg_color};
                color: {text_color};
                font-size: 7px;
                font-weight: bold;
            }}
        """)
        
        # Text content - Thu gọn text
        self.setText(f"{self.channel}\n{self.value}")

class DMXViewTab(QWidget):
    """Tab DMX View"""
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.current_universe = 0
        self.channel_widgets = {}
        self.dmx_data = bytes(512)
        self.received_data = {}  # universe -> (data, source_ip, timestamp)
        self.artnet_controller = None  # Will be set by main_window
        
        self.init_ui()
        self.init_timer()
    
    def init_ui(self):
        """Khởi tạo UI"""
        layout = QVBoxLayout(self)
        
        # Control panel
        self.create_control_panel(layout)
        
        # DMX display
        self.create_dmx_display(layout)
        
        # Statistics panel
        self.create_statistics_panel(layout)
    
    def create_control_panel(self, parent_layout):
        """Tạo control panel"""
        control_group = QGroupBox("Display Control")
        control_layout = QHBoxLayout(control_group)
        
        # Universe selection
        control_layout.addWidget(QLabel("Universe:"))
        self.universe_combo = QComboBox()
        self.universe_combo.addItems([str(i) for i in range(16)])
        self.universe_combo.currentTextChanged.connect(self.on_universe_changed)
        control_layout.addWidget(self.universe_combo)
        
        control_layout.addWidget(QLabel(" | "))
        
        # Auto-Forward checkbox
        self.auto_forward_checkbox = QCheckBox("Auto-Forward to Nodes")
        self.auto_forward_checkbox.setChecked(False)
        self.auto_forward_checkbox.toggled.connect(self.on_auto_forward_toggled)
        self.auto_forward_checkbox.setToolTip("Forward received Art-Net data to configured nodes")
        control_layout.addWidget(self.auto_forward_checkbox)
        
        control_layout.addWidget(QLabel(" | "))
        
        # View options
        self.zero_channels_checkbox = QCheckBox("Show Zero Channels")
        self.zero_channels_checkbox.setChecked(True)
        self.zero_channels_checkbox.toggled.connect(self.update_display)
        control_layout.addWidget(self.zero_channels_checkbox)
        
        self.percentage_checkbox = QCheckBox("Show Percentage")
        self.percentage_checkbox.setChecked(True)
        self.percentage_checkbox.toggled.connect(self.update_display)
        control_layout.addWidget(self.percentage_checkbox)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_display)
        control_layout.addWidget(self.refresh_button)
        
        control_layout.addStretch()
        parent_layout.addWidget(control_group)
    
    def create_dmx_display(self, parent_layout):
        """Tạo DMX display"""
        display_group = QGroupBox("DMX Channels (1-512)")
        display_layout = QVBoxLayout(display_group)
        
        # Scroll area - Đặt chiều cao vừa đủ
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(600)  # Tăng chiều cao để chứa 32 hàng
        
        # Grid widget
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(1)  # Giảm spacing từ 2 -> 1
        self.grid_layout.setContentsMargins(2, 2, 2, 2)  # Giảm margins
        
        self.scroll_area.setWidget(self.grid_widget)
        display_layout.addWidget(self.scroll_area)
        
        # Initial display
        self.update_display_range()
        
        parent_layout.addWidget(display_group)
    
    def create_statistics_panel(self, parent_layout):
        """Tạo statistics panel"""
        stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout(stats_group)
        
        # Left side - Channel stats
        left_layout = QVBoxLayout()
        
        self.active_channels_label = QLabel("Active Channels: 0")
        left_layout.addWidget(self.active_channels_label)
        
        self.max_value_label = QLabel("Max Value: 0")
        left_layout.addWidget(self.max_value_label)
        
        self.avg_value_label = QLabel("Avg Value: 0")
        left_layout.addWidget(self.avg_value_label)
        
        stats_layout.addLayout(left_layout)
        
        # Right side - Data source
        right_layout = QVBoxLayout()
        
        self.data_source_label = QLabel("Source: Local")
        right_layout.addWidget(self.data_source_label)
        
        self.last_update_label = QLabel("Last Update: -")
        right_layout.addWidget(self.last_update_label)
        
        self.update_rate_label = QLabel("Update Rate: 0 Hz")
        right_layout.addWidget(self.update_rate_label)
        
        stats_layout.addLayout(right_layout)
        
        # Data rate indicator
        self.data_rate_progress = QProgressBar()
        self.data_rate_progress.setRange(0, 44)  # Max Art-Net rate
        self.data_rate_progress.setValue(0)
        self.data_rate_progress.setFormat("DMX Rate: %v Hz")
        stats_layout.addWidget(self.data_rate_progress)
        
        parent_layout.addWidget(stats_group)
    
    def init_timer(self):
        """Khởi tạo timer"""
        # Display update timer
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_statistics)
        self.display_timer.start(1000)  # Update every second
        
        # Rate calculation
        self.last_update_time = 0
        self.update_count = 0
        self.update_rate = 0
    
    def update_display_range(self):
        """Update display range - Show all 512 channels"""
        # Clear existing widgets
        for widget in self.channel_widgets.values():
            widget.setParent(None)
        self.channel_widgets.clear()
        
        # Create widgets for all 512 channels
        cols = 32  # Tăng từ 16 -> 32 cột để giảm số hàng
        
        for channel in range(1, 513):  # Channels 1-512
            widget = ChannelWidget(channel)
            
            row = (channel - 1) // cols
            col = (channel - 1) % cols
            self.grid_layout.addWidget(widget, row, col)
            
            self.channel_widgets[channel] = widget
        
        # Update values
        self.update_display()
    
    def update_display(self):
        """Update display with current DMX data"""
        for channel, widget in self.channel_widgets.items():
            if 1 <= channel <= 512:
                # Bounds checking để tránh IndexError
                if channel - 1 < len(self.dmx_data):
                    value = self.dmx_data[channel - 1]
                else:
                    value = 0  # Channel ngoài range = 0
                
                # Hide zero channels if option is disabled
                if not self.zero_channels_checkbox.isChecked() and value == 0:
                    widget.hide()
                else:
                    widget.show()
                    widget.set_value(value)
    
    def refresh_display(self):
        """Refresh display"""
        self.update_display_range()
    
    def on_universe_changed(self, universe_str: str):
        """Handle universe change"""
        self.current_universe = int(universe_str)
        
        # Load data for this universe
        if self.current_universe in self.received_data:
            data, source_ip, timestamp = self.received_data[self.current_universe]
            self.dmx_data = data
            self.data_source_label.setText(f"Source: {source_ip}")
        else:
            self.dmx_data = bytes(512)
            self.data_source_label.setText("Source: No Data")
        
        self.update_display()
    
    def on_auto_forward_toggled(self, checked: bool):
        """Handle auto-forward checkbox toggle"""
        if self.artnet_controller:
            success = self.artnet_controller.set_auto_forward(checked)
            if not success:
                # Tắt checkbox nếu không thành công (không có nodes)
                from PyQt6.QtWidgets import QMessageBox
                self.auto_forward_checkbox.setChecked(False)
                QMessageBox.warning(
                    self,
                    "Cannot Enable Auto-Forward",
                    "No nodes configured in Hardware Manager.\n\n"
                    "Please add nodes in Hardware Manager tab first."
                )
                logger.warning("Auto-forward toggle failed: No nodes configured")
            else:
                status = "enabled" if checked else "disabled"
                logger.info(f"Auto-forward {status} by user")
    
    def set_artnet_controller(self, controller):
        """Set reference to ArtNet controller"""
        self.artnet_controller = controller
    
    def update_dmx_data(self, universe: int, dmx_data: bytes):
        """Update DMX data from Live Control"""
        if universe == self.current_universe:
            self.dmx_data = dmx_data
            self.data_source_label.setText("Source: Live Control")
            self.update_display()
            
        # Update rate calculation
        import time
        current_time = time.time()
        self.update_count += 1
        
        if current_time - self.last_update_time >= 1.0:
            self.update_rate = self.update_count
            self.update_count = 0
            self.last_update_time = current_time
    
    def update_received_dmx(self, universe: int, dmx_data: bytes, source_ip: str):
        """Update received DMX data from Art-Net"""
        import time
        timestamp = time.time()
        
        self.received_data[universe] = (dmx_data, source_ip, timestamp)
        
        if universe == self.current_universe:
            self.dmx_data = dmx_data
            self.data_source_label.setText(f"Source: {source_ip}")
            self.update_display()
        
        # Update rate calculation
        self.update_count += 1
        
        if time.time() - self.last_update_time >= 1.0:
            self.update_rate = self.update_count
            self.update_count = 0
            self.last_update_time = time.time()
    
    def update_statistics(self):
        """Update statistics"""
        if not self.dmx_data:
            return
        
        # Calculate stats
        active_channels = sum(1 for value in self.dmx_data if value > 0)
        max_value = max(self.dmx_data) if self.dmx_data else 0
        avg_value = sum(self.dmx_data) / len(self.dmx_data) if self.dmx_data else 0
        
        # Update labels
        self.active_channels_label.setText(f"Active Channels: {active_channels}")
        self.max_value_label.setText(f"Max Value: {max_value}")
        self.avg_value_label.setText(f"Avg Value: {avg_value:.1f}")
        
        # Update rate
        self.update_rate_label.setText(f"Update Rate: {self.update_rate} Hz")
        self.data_rate_progress.setValue(min(self.update_rate, 44))
        
        # Update last update time
        import time
        if self.current_universe in self.received_data:
            _, _, timestamp = self.received_data[self.current_universe]
            last_update = time.strftime("%H:%M:%S", time.localtime(timestamp))
            self.last_update_label.setText(f"Last Update: {last_update}")
        else:
            self.last_update_label.setText("Last Update: -")