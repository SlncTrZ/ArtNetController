"""
Hardware Manager Tab - Tab quản lý thiết bị Art-Net
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                           QTableWidgetItem, QPushButton, QGroupBox, QLabel,
                           QLineEdit, QSpinBox, QComboBox, QHeaderView,
                           QMessageBox, QProgressBar, QDialog, QFormLayout,
                           QDialogButtonBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

class UniverseMappingDialog(QDialog):
    """Dialog để cấu hình Universe mapping cho ArtNet node"""
    
    def __init__(self, node, current_mapping: dict, parent=None):
        super().__init__(parent)
        self.node = node
        self.current_mapping = current_mapping.copy()
        self.port_spinboxes = {}
        
        self.setWindowTitle(f"Universe Mapping - {node.short_name}")
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Device info
        info_group = QGroupBox("Device Information")
        info_layout = QFormLayout(info_group)
        info_layout.addRow("IP Address:", QLabel(self.node.ip_address))
        info_layout.addRow("Short Name:", QLabel(self.node.short_name))
        info_layout.addRow("Long Name:", QLabel(self.node.long_name))
        info_layout.addRow("Port Count:", QLabel(str(self.node.port_count)))
        layout.addWidget(info_group)
        
        # Port mapping
        mapping_group = QGroupBox("Port → Universe Mapping")
        mapping_layout = QFormLayout(mapping_group)
        
        for port_num in range(self.node.port_count):
            port_layout = QHBoxLayout()
            
            # Universe spinbox
            universe_spin = QSpinBox()
            universe_spin.setRange(0, 32767)  # ArtNet universe range
            universe_spin.setValue(self.current_mapping.get(port_num, 0))
            universe_spin.setPrefix("Universe ")
            self.port_spinboxes[port_num] = universe_spin
            port_layout.addWidget(universe_spin)
            
            port_layout.addStretch()
            
            mapping_layout.addRow(f"Port {port_num}:", port_layout)
        
        layout.addWidget(mapping_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_mapping(self) -> dict:
        """Get the configured mapping"""
        mapping = {}
        for port_num, spinbox in self.port_spinboxes.items():
            universe = spinbox.value()
            if universe > 0:  # Chỉ lưu port được gán universe
                mapping[port_num] = universe
        return mapping

class HardwareManagerTab(QWidget):
    """Tab Hardware Manager"""
    
    device_selected = pyqtSignal(dict)  # Device info
    universe_mapping_changed = pyqtSignal(dict)  # Universe mapping changed
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.discovered_nodes = {}
        self.is_scanning = False
        self.scan_start_timer = None
        
        # Admin access control
        self._is_admin = False
        
        # Universe mapping: {ip_address: {port_number: universe}}
        self.universe_mapping = self._load_universe_mapping()
        
        self.init_ui()
        self.init_timer()
    
    def set_admin_mode(self, is_admin: bool):
        """Set admin mode and update UI accordingly"""
        self._is_admin = is_admin
        self._update_admin_ui()
        logger.info(f"Hardware Manager admin mode: {is_admin}")
    
    def _update_admin_ui(self):
        """Update UI based on admin status"""
        # Check if buttons exist before updating
        if not hasattr(self, 'configure_universe_button'):
            return
        
        # Configure Universe button
        if self._is_admin:
            # Enable if a device is selected
            selected = len(self.devices_table.selectionModel().selectedRows()) > 0
            self.configure_universe_button.setEnabled(selected)
            self.configure_universe_button.setToolTip("Configure universe mapping for selected device")
        else:
            self.configure_universe_button.setEnabled(False)
            self.configure_universe_button.setToolTip("🔒 Admin access required to configure universe mapping")
        
        # Clear button
        if hasattr(self, 'clear_button'):
            self.clear_button.setEnabled(self._is_admin)
            if not self._is_admin:
                self.clear_button.setToolTip("🔒 Admin access required to clear devices")
            else:
                self.clear_button.setToolTip("Clear all discovered devices")
        
        # Update status message
        if not self._is_admin:
            logger.debug("👀 Hardware Manager in VIEW-ONLY mode (non-admin user)")
        else:
            logger.debug("✏️  Hardware Manager in EDIT mode (admin user)")
    
    def init_ui(self):
        """Khởi tạo UI"""
        layout = QVBoxLayout(self)
        
        # Network scan section
        self.create_scan_section(layout)
        
        # Discovered devices table
        self.create_devices_table(layout)
        
        # Device details section
        self.create_device_details(layout)
    
    def create_scan_section(self, parent_layout):
        """Tạo network scan section"""
        scan_group = QGroupBox("Network Discovery")
        scan_layout = QHBoxLayout(scan_group)
        
        # Scan button
        self.scan_button = QPushButton("Scan Network")
        self.scan_button.clicked.connect(self.scan_network)
        scan_layout.addWidget(self.scan_button)
        
        # Auto scan checkbox
        from PyQt6.QtWidgets import QCheckBox
        self.auto_scan_checkbox = QCheckBox("Auto Scan")
        self.auto_scan_checkbox.setChecked(False)  # Mặc định OFF
        scan_layout.addWidget(self.auto_scan_checkbox)
        
        # Progress bar
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        scan_layout.addWidget(self.scan_progress)
        
        # Status label
        self.scan_status = QLabel("Ready to scan")
        scan_layout.addWidget(self.scan_status)
        
        scan_layout.addStretch()
        parent_layout.addWidget(scan_group)
    
    def create_devices_table(self, parent_layout):
        """Tạo devices table"""
        devices_group = QGroupBox("Discovered Devices")
        devices_layout = QVBoxLayout(devices_group)
        
        # Table
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(7)
        self.devices_table.setHorizontalHeaderLabels([
            "IP Address", "Short Name", "Long Name", "Universe", "Ports", "Mapped", "Status"
        ])
        
        # Set column widths
        header = self.devices_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        # Selection behavior
        self.devices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.devices_table.itemSelectionChanged.connect(self.on_device_selected)
        
        devices_layout.addWidget(self.devices_table)
        
        # Table controls
        table_controls = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_devices)
        table_controls.addWidget(self.refresh_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_devices)
        table_controls.addWidget(self.clear_button)
        
        table_controls.addStretch()
        
        self.device_count_label = QLabel("Devices: 0")
        table_controls.addWidget(self.device_count_label)
        
        devices_layout.addLayout(table_controls)
        parent_layout.addWidget(devices_group)
    
    def create_device_details(self, parent_layout):
        """Tạo device details section"""
        details_group = QGroupBox("Device Details")
        details_layout = QVBoxLayout(details_group)
        
        # Device info grid
        info_layout = QHBoxLayout()
        
        # Left column
        left_layout = QVBoxLayout()
        
        left_layout.addWidget(QLabel("IP Address:"))
        self.ip_label = QLabel("-")
        self.ip_label.setFont(QFont("monospace"))
        left_layout.addWidget(self.ip_label)
        
        left_layout.addWidget(QLabel("Short Name:"))
        self.short_name_label = QLabel("-")
        left_layout.addWidget(self.short_name_label)
        
        left_layout.addWidget(QLabel("Long Name:"))
        self.long_name_label = QLabel("-")
        left_layout.addWidget(self.long_name_label)
        
        info_layout.addLayout(left_layout)
        
        # Right column
        right_layout = QVBoxLayout()
        
        right_layout.addWidget(QLabel("Universe:"))
        self.universe_label = QLabel("-")
        right_layout.addWidget(self.universe_label)
        
        right_layout.addWidget(QLabel("Port Count:"))
        self.port_count_label = QLabel("-")
        right_layout.addWidget(self.port_count_label)
        
        right_layout.addWidget(QLabel("Last Seen:"))
        self.last_seen_label = QLabel("-")
        right_layout.addWidget(self.last_seen_label)
        
        info_layout.addLayout(right_layout)
        
        details_layout.addLayout(info_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.configure_universe_button = QPushButton("Configure Universe Mapping")
        self.configure_universe_button.setEnabled(False)
        self.configure_universe_button.clicked.connect(self.configure_universe_mapping)
        action_layout.addWidget(self.configure_universe_button)
        
        self.ping_device_button = QPushButton("Ping Device")
        self.ping_device_button.setEnabled(False)
        self.ping_device_button.clicked.connect(self.ping_device)
        action_layout.addWidget(self.ping_device_button)
        
        action_layout.addStretch()
        details_layout.addLayout(action_layout)
        
        parent_layout.addWidget(details_group)
    
    def init_timer(self):
        """Khởi tạo timer"""
        # Auto scan timer
        self.auto_scan_timer = QTimer()
        self.auto_scan_timer.timeout.connect(self.auto_scan)
        self.auto_scan_timer.start(30000)  # Auto scan every 30 seconds
        
        # Update timer for last seen
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_last_seen)
        self.update_timer.start(1000)  # Update every second
    
    def scan_network(self):
        """Scan network for Art-Net devices"""
        if self.is_scanning:
            # Đang quét, bấm để dừng
            self.stop_scanning()
        else:
            # Bắt đầu quét
            self.start_scanning()
    
    def start_scanning(self):
        """Bắt đầu quét mạng"""
        self.is_scanning = True
        self.scan_button.setText("Scanning...")
        self.scan_button.setEnabled(False)  # Tạm thời disable trong 5 giây đầu
        self.scan_progress.setVisible(True)
        self.scan_progress.setRange(0, 0)  # Indeterminate progress
        self.scan_status.setText("Scanning network...")
        
        # Emit scan signal to main window
        from PyQt6.QtCore import QMetaObject, Q_ARG
        main_window = self.window()
        if hasattr(main_window, 'scan_network'):
            main_window.scan_network()
        
        # Sau 5 giây, đổi nút thành "Stop Scanning" và cho phép dừng
        self.scan_start_timer = QTimer()
        self.scan_start_timer.setSingleShot(True)
        self.scan_start_timer.timeout.connect(self.enable_stop_button)
        self.scan_start_timer.start(5000)  # 5 giây
    
    def enable_stop_button(self):
        """Sau 5 giây, cho phép dừng quét"""
        if self.is_scanning:
            self.scan_button.setText("Stop Scanning")
            self.scan_button.setEnabled(True)
            self.scan_status.setText(f"Scanning... Found {len(self.discovered_nodes)} devices")
    
    def stop_scanning(self):
        """Dừng quét mạng"""
        self.is_scanning = False
        self.scan_button.setText("Scan Network")
        self.scan_button.setEnabled(True)
        self.scan_progress.setVisible(False)
        self.scan_status.setText(f"Scan stopped - Found {len(self.discovered_nodes)} devices")
        
        # Hủy timer nếu đang chạy
        if self.scan_start_timer and self.scan_start_timer.isActive():
            self.scan_start_timer.stop()
    
    def scan_complete(self):
        """Called when scan is complete"""
        if self.is_scanning:
            self.stop_scanning()
    
    def auto_scan(self):
        """Auto scan if enabled"""
        if self.auto_scan_checkbox.isChecked():
            self.scan_network()
    
    def add_discovered_node(self, node):
        """Add discovered Art-Net node to table"""
        self.discovered_nodes[node.ip_address] = node
        self.refresh_devices()
        
        # Cập nhật trạng thái nếu đang quét
        if self.is_scanning:
            self.scan_status.setText(f"Scanning... Found {len(self.discovered_nodes)} devices")
    
    def refresh_devices(self):
        """Refresh devices table"""
        self.devices_table.setRowCount(len(self.discovered_nodes))
        
        for row, (ip, node) in enumerate(self.discovered_nodes.items()):
            # IP Address
            self.devices_table.setItem(row, 0, QTableWidgetItem(node.ip_address))
            
            # Short Name
            self.devices_table.setItem(row, 1, QTableWidgetItem(node.short_name))
            
            # Long Name
            self.devices_table.setItem(row, 2, QTableWidgetItem(node.long_name))
            
            # Universe
            self.devices_table.setItem(row, 3, QTableWidgetItem(str(node.universe)))
            
            # Ports
            self.devices_table.setItem(row, 4, QTableWidgetItem(str(node.port_count)))
            
            # Mapped Universes
            mapped_info = self._get_mapped_info(node.ip_address)
            mapped_item = QTableWidgetItem(mapped_info)
            self.devices_table.setItem(row, 5, mapped_item)
            
            # Status
            import time
            age = time.time() - node.last_seen
            if age < 60:
                status = "Online"
            elif age < 300:
                status = "Recent"
            else:
                status = "Offline"
            
            status_item = QTableWidgetItem(status)
            if status == "Online":
                status_item.setBackground(Qt.GlobalColor.green)
            elif status == "Recent":
                status_item.setBackground(Qt.GlobalColor.yellow)
            else:
                status_item.setBackground(Qt.GlobalColor.red)
            
            self.devices_table.setItem(row, 6, status_item)
        
        # Update count
        self.device_count_label.setText(f"Devices: {len(self.discovered_nodes)}")
    
    def clear_devices(self):
        """Clear devices table"""
        # Check admin permission
        if not self._is_admin:
            QMessageBox.warning(
                self,
                "Access Denied",
                "🔒 Admin access required to clear devices.\n\n"
                "Please log in as admin to modify hardware configuration."
            )
            logger.warning("⚠️  User attempted to clear devices without admin permission")
            return
        
        reply = QMessageBox.question(
            self,
            "Clear Devices",
            "Are you sure you want to clear all discovered devices?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.discovered_nodes.clear()
            self.devices_table.setRowCount(0)
            self.clear_device_details()
            self.device_count_label.setText("Devices: 0")
            logger.info("Hardware devices cleared by admin")
    
    def on_device_selected(self):
        """Handle device selection in table"""
        selected_rows = self.devices_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            ip_item = self.devices_table.item(row, 0)
            
            if ip_item:
                ip_address = ip_item.text()
                node = self.discovered_nodes.get(ip_address)
                
                if node:
                    self.show_device_details(node)
                    # Only enable if admin
                    self.configure_universe_button.setEnabled(self._is_admin)
                    self.ping_device_button.setEnabled(True)
                    
                    # Update tooltips
                    if not self._is_admin:
                        self.configure_universe_button.setToolTip("🔒 Admin access required")
        else:
            self.clear_device_details()
            self.configure_universe_button.setEnabled(False)
            self.ping_device_button.setEnabled(False)
    
    def show_device_details(self, node):
        """Show device details"""
        self.ip_label.setText(node.ip_address)
        self.short_name_label.setText(node.short_name)
        self.long_name_label.setText(node.long_name)
        self.universe_label.setText(str(node.universe))
        self.port_count_label.setText(str(node.port_count))
        
        import time
        last_seen = time.strftime("%H:%M:%S", time.localtime(node.last_seen))
        self.last_seen_label.setText(last_seen)
    
    def clear_device_details(self):
        """Clear device details"""
        self.ip_label.setText("-")
        self.short_name_label.setText("-")
        self.long_name_label.setText("-")
        self.universe_label.setText("-")
        self.port_count_label.setText("-")
        self.last_seen_label.setText("-")
    
    def configure_universe_mapping(self):
        """Configure Universe mapping for selected device"""
        # Check admin permission
        if not self._is_admin:
            QMessageBox.warning(
                self,
                "Access Denied",
                "🔒 Admin access required to configure universe mapping.\n\n"
                "Please log in as admin to modify hardware configuration."
            )
            logger.warning("⚠️  User attempted to configure universe mapping without admin permission")
            return
        
        selected_rows = self.devices_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            ip_item = self.devices_table.item(row, 0)
            
            if ip_item:
                ip_address = ip_item.text()
                node = self.discovered_nodes.get(ip_address)
                
                if node:
                    dialog = UniverseMappingDialog(node, self.universe_mapping.get(ip_address, {}), self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        # Lưu mapping
                        self.universe_mapping[ip_address] = dialog.get_mapping()
                        self._save_universe_mapping()
                        self.refresh_devices()
                        
                        # Emit signal để cập nhật vào controller
                        self.universe_mapping_changed.emit(self.universe_mapping)
                        
                        QMessageBox.information(
                            self,
                            "Universe Mapping Saved",
                            f"Universe mapping for {node.short_name} has been saved."
                        )
                        logger.info(f"Admin configured universe mapping for {node.short_name}")
    
    def _get_mapped_info(self, ip_address: str) -> str:
        """Get mapped universe info for display"""
        mapping = self.universe_mapping.get(ip_address, {})
        if not mapping:
            return "-"
        
        mapped_ports = [f"P{port}→U{uni}" for port, uni in sorted(mapping.items())]
        return ", ".join(mapped_ports) if mapped_ports else "-"
    
    def _load_universe_mapping(self) -> dict:
        """Load universe mapping from config"""
        if self.config_manager:
            return self.config_manager.get_app_config('artnet.universe_mapping', {})
        return {}
    
    def _save_universe_mapping(self):
        """Save universe mapping to config"""
        if self.config_manager:
            self.config_manager.set_app_config('artnet.universe_mapping', self.universe_mapping)
    
    def get_universe_mapping(self) -> dict:
        """Get current universe mapping for external use"""
        return self.universe_mapping.copy()
    
    def ping_device(self):
        """Ping selected device"""
        selected_rows = self.devices_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            ip_item = self.devices_table.item(row, 0)
            
            if ip_item:
                ip_address = ip_item.text()
                
                # Simple ping using OS command
                import subprocess
                import platform
                
                try:
                    if platform.system().lower() == "windows":
                        result = subprocess.run(
                            ["ping", "-n", "1", ip_address],
                            capture_output=True,
                            timeout=5
                        )
                    else:
                        result = subprocess.run(
                            ["ping", "-c", "1", ip_address],
                            capture_output=True,
                            timeout=5
                        )
                    
                    if result.returncode == 0:
                        QMessageBox.information(
                            self,
                            "Ping Result",
                            f"Device {ip_address} is reachable"
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Ping Result",
                            f"Device {ip_address} is not reachable"
                        )
                        
                except subprocess.TimeoutExpired:
                    QMessageBox.warning(
                        self,
                        "Ping Result",
                        f"Ping to {ip_address} timed out"
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Ping Error",
                        f"Failed to ping {ip_address}: {str(e)}"
                    )
    
    def update_last_seen(self):
        """Update last seen times in table"""
        # Refresh table to update status colors
        if self.discovered_nodes:
            self.refresh_devices()