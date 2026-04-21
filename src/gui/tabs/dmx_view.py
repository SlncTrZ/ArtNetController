"""
DMX View Tab - Tab hiển thị trạng thái DMX
"""

import logging
from collections import deque
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLabel, QComboBox, QGroupBox, QScrollArea,
                           QSpinBox, QPushButton, QCheckBox, QProgressBar)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QPainter, QBrush, QColor

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
                font-weight: bold;
            }
        """)
        self.update_display()
    
    def set_value(self, value: int):
        """Set channel value"""
        self.value = value
        self.update()  # Trigger paintEvent
    
    def paintEvent(self, event):
        """Custom paint event to draw fill effect"""
        painter = QPainter(self)
        
        # Get widget dimensions
        width = self.width() - 2  # Account for border
        height = self.height() - 2  # Account for border
        
        # Calculate fill height based on value
        fill_height = int((self.value / 255) * height)
        
        # Draw background
        painter.fillRect(1, 1, width, height, QColor("#2b2b2b"))
        
        # Draw fill if value > 0
        if self.value > 0:
            fill_color = QColor("#4444ff")  # Blue color
            fill_rect_y = height - fill_height + 1  # Fill from bottom
            painter.fillRect(1, fill_rect_y, width, fill_height, fill_color)
        
        # Draw border
        painter.setPen(QColor("#555555"))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        
        # Draw text
        painter.setPen(QColor("#ffffff" if self.value > 0 else "#888888"))
        painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        text = f"{self.channel}\n{self.value}"
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)
    
    def update_display(self):
        """Update display - now just triggers repaint"""
        self.update()  # Trigger paintEvent

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
        self.packet_timestamps = {}  # universe -> deque[timestamp]
        self.rate_window_seconds = 2.0  # Sliding window for stable rate display
        self.last_packet_time = 0.0
        self.last_packet_time_by_universe = {}
        
        # Rate limiting for UI updates (prevent UI freeze)
        self.last_ui_update = 0
        self.update_interval = 0.05  # Max 20 FPS (50ms between updates)
        self.pending_update = False
        
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
        self.universe_combo.setEditable(True)  # Allow typing universe number
        
        # V1.3.0: Load max universes from license (4 or 512)
        try:
            from src.utils.license import get_license_manager
            license_manager = get_license_manager()
            max_universes = license_manager.get_max_universes()
            tier = license_manager.get_license_tier()
            logger.info(f"DMX View: {tier} version - {max_universes} universes")
        except Exception as e:
            logger.warning(f"License check failed, defaulting to 4 universes: {e}")
            max_universes = 4
            tier = "FREE"
        
        self.universe_combo.addItems([str(i) for i in range(max_universes)])
        self.universe_combo.currentTextChanged.connect(self.on_universe_changed)
        self.universe_combo.setToolTip(f"Select universe (0-{max_universes-1}) - {tier} Version")
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
        
        control_layout.addWidget(QLabel(" | "))
        
        # Auto-clear timeout option with configurable value
        self.auto_clear_checkbox = QCheckBox("Auto-Clear Timeout:")
        self.auto_clear_checkbox.setChecked(True)  # Enabled by default
        self.auto_clear_checkbox.setToolTip(
            "Clear display when no DMX packets are received across all universes.\n"
            "Stable/static DMX values are treated as valid active signal."
        )
        control_layout.addWidget(self.auto_clear_checkbox)
        
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(1, 600)  # 0.1s to 60s (stored as deciseconds)
        self.timeout_spinbox.setValue(5)  # Default 0.5s (5 deciseconds)
        self.timeout_spinbox.setSuffix(" × 0.1s")
        self.timeout_spinbox.setToolTip("Timeout in 0.1s increments (e.g., 5 = 0.5s)")
        control_layout.addWidget(self.timeout_spinbox)
        
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
        self.data_rate_progress.setRange(0, 50)  # Visual cap for displayed rate
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
        
        # Pending update timer (for rate limiting)
        self.pending_timer = QTimer()
        self.pending_timer.timeout.connect(self.process_pending_update)
        self.pending_timer.start(50)  # Check every 50ms (20 FPS max)
        
        # Timeout detection timer (check for stale data)
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.check_data_timeout)
        self.timeout_timer.start(1000)  # Check every second
        
        # Rate calculation (sliding window)
        self.update_rate = 0.0
        
        # Timeout settings - packet-based detection
        # Trigger timeout only when no packets arrive across all universes
        self.timeout_cleared = False  # Flag to prevent spam logging

    def _record_packet_activity(self, universe: int, timestamp: float):
        """Record packet timestamp for timeout and rate calculations."""
        packet_queue = self.packet_timestamps.setdefault(universe, deque())
        packet_queue.append(timestamp)

        cutoff = timestamp - self.rate_window_seconds
        while packet_queue and packet_queue[0] < cutoff:
            packet_queue.popleft()

        self.last_packet_time = timestamp
        self.last_packet_time_by_universe[universe] = timestamp

    def _calculate_universe_rate(self, universe: int, timestamp: float) -> float:
        """Calculate smoothed packet rate using sliding window."""
        packet_queue = self.packet_timestamps.get(universe)
        if not packet_queue:
            return 0.0

        if len(packet_queue) == 1:
            return 1.0

        window_span = max(timestamp - packet_queue[0], 0.1)
        return len(packet_queue) / window_span
    
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
        try:
            self.current_universe = int(universe_str)
        except ValueError:
            logger.warning(f"Invalid universe number: {universe_str}")
            return

        # Validate range
        if not (0 <= self.current_universe <= 32767):
            logger.warning(f"Universe {self.current_universe} out of range (0-32767)")
            return

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
    
    def process_pending_update(self):
        """Process pending UI updates (called by timer) - PREVENTS UI FREEZE"""
        import time
        if self.pending_update:
            current_time = time.time()
            if current_time - self.last_ui_update >= self.update_interval:
                self.update_display()
                self.last_ui_update = current_time
                self.pending_update = False
    
    def check_data_timeout(self):
        """Clear display only when packet stream is inactive for longer than timeout."""
        # Skip timeout check if auto-clear is disabled
        if not self.auto_clear_checkbox.isChecked():
            return
        
        import time
        current_time = time.time()
        
        # Get timeout value from spinbox (in deciseconds, convert to seconds)
        timeout_seconds = self.timeout_spinbox.value() * 0.1
        
        # If no data has ever arrived, nothing to clear.
        if self.last_packet_time <= 0:
            return

        time_since_packet = current_time - self.last_packet_time
        if time_since_packet > timeout_seconds:
            if not self.timeout_cleared:
                logger.info(
                    f"No DMX packets for {time_since_packet:.1f}s "
                    f"(timeout={timeout_seconds}s) - clearing all universes"
                )
                self.received_data.clear()
                self.packet_timestamps.clear()
                self.last_packet_time_by_universe.clear()
                self.dmx_data = bytes(512)
                self.data_source_label.setText("Source: No Data (Packet Timeout)")
                self.update_display()
                self.update_rate = 0.0
                self.timeout_cleared = True
        else:
            self.timeout_cleared = False
    
    def set_artnet_controller(self, controller):
        """Set reference to ArtNet controller"""
        self.artnet_controller = controller
    
    def update_dmx_data(self, universe: int, dmx_data: bytes):
        """Update DMX data from Live Control or Show Playback"""
        import time
        timestamp = time.time()
        
        # Update received_data with timestamp (for timeout detection)
        self.received_data[universe] = (dmx_data, "Show Playback", timestamp)
        self._record_packet_activity(universe, timestamp)
        
        if universe == self.current_universe:
            self.dmx_data = dmx_data
            self.data_source_label.setText("Source: Show Playback")
            self.update_display()
            
            # Reset timeout flag when receiving new data
            self.timeout_cleared = False
            self.update_rate = self._calculate_universe_rate(universe, timestamp)
            
        else:
            self.update_rate = self._calculate_universe_rate(self.current_universe, timestamp)
    
    def update_received_dmx(self, universe: int, dmx_data: bytes, source_ip: str):
        """Update received DMX data from Art-Net - WITH RATE LIMITING"""
        import time
        timestamp = time.time()
        
        logger.debug(f"🎯 DMX View received data: Universe {universe}, {len(dmx_data)} channels from {source_ip}")
        
        # ALWAYS store data (no rate limiting for data storage)
        self.received_data[universe] = (dmx_data, source_ip, timestamp)
        self._record_packet_activity(universe, timestamp)
        
        # Auto-add universe to combo if not exists
        universe_str = str(universe)
        if self.universe_combo.findText(universe_str) == -1:
            self.universe_combo.addItem(universe_str)
            logger.info(f"➕ Added universe {universe} to combo box")
        
        if universe == self.current_universe:
            logger.debug(f"🎯 Processing universe {universe} (current: {self.current_universe})")
            # Validate and clip channel count to 512 max
            dmx_data = dmx_data[:512] if len(dmx_data) > 512 else dmx_data
            self.dmx_data = dmx_data
            self.update_rate = self._calculate_universe_rate(universe, timestamp)
            
            # Reset timeout flag when receiving new data
            self.timeout_cleared = False
            
            # RATE LIMITED UI UPDATE (prevent UI freeze)
            current_time = timestamp
            if current_time - self.last_ui_update >= self.update_interval:
                logger.debug(f"🔄 Updating UI display for universe {universe}")
                self.data_source_label.setText(f"Source: {source_ip}")
                self.update_display()
                self.last_ui_update = current_time
                self.pending_update = False
                logger.debug(f"UI updated successfully")
            else:
                # Mark that we have a pending update
                self.pending_update = True
                logger.debug(f"⏳ UI update delayed (rate limited)")
        else:
            self.update_rate = self._calculate_universe_rate(self.current_universe, timestamp)
            logger.debug(f"⏭️ Skipping universe {universe} (not current: {self.current_universe})")
    
    def update_statistics(self):
        """Update statistics"""
        import time

        last_packet = self.last_packet_time_by_universe.get(self.current_universe, 0.0)
        if last_packet > 0 and (time.time() - last_packet) > self.rate_window_seconds:
            self.update_rate = 0.0

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
        self.update_rate_label.setText(f"Update Rate: {self.update_rate:.1f} Hz")
        # Use actual update rate instead of fixed 44Hz, but cap progress bar at 50Hz max
        displayed_rate = min(int(round(self.update_rate)), 50)
        self.data_rate_progress.setValue(displayed_rate)
        self.data_rate_progress.setFormat(f"DMX Rate: {self.update_rate:.1f} Hz")
        
        # Update last update time
        if self.current_universe in self.received_data:
            _, _, timestamp = self.received_data[self.current_universe]
            last_update = time.strftime("%H:%M:%S", time.localtime(timestamp))
            self.last_update_label.setText(f"Last Update: {last_update}")
        else:
            self.last_update_label.setText("Last Update: -")