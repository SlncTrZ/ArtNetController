"""
Serial Manager Tab - Quản lý kết nối IOBoard
Hỗ trợ nhiều DMX Master IO boards với auto-mapping
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                           QTableWidgetItem, QPushButton, QGroupBox, QLabel,
                           QComboBox, QHeaderView, QMessageBox, QCheckBox,
                           QSpinBox, QFormLayout, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

logger = logging.getLogger(__name__)


class ManualMappingDialog(QDialog):
    """Dialog để cấu hình manual universe mapping cho board"""
    
    def __init__(self, board_number: int, current_universes: list, parent=None):
        super().__init__(parent)
        self.board_number = board_number
        self.universe_spinboxes = []
        
        self.setWindowTitle(f"Universe Mapping - Board #{board_number}")
        self.setModal(True)
        self.init_ui(current_universes)
    
    def init_ui(self, current_universes):
        layout = QVBoxLayout(self)
        
        # Info
        info = QLabel(
            f"Configure universe mapping for Board #{self.board_number}\n"
            "You can assign up to 4 universes per board."
        )
        layout.addWidget(info)
        
        # Universe inputs
        universe_group = QGroupBox("Universes")
        universe_layout = QFormLayout(universe_group)
        
        for i in range(4):
            spinbox = QSpinBox()
            spinbox.setRange(-1, 255)  # -1 = disabled
            spinbox.setSpecialValueText("Disabled")
            
            if i < len(current_universes):
                spinbox.setValue(current_universes[i])
            else:
                spinbox.setValue(-1)
            
            self.universe_spinboxes.append(spinbox)
            universe_layout.addRow(f"Universe {i+1}:", spinbox)
        
        layout.addWidget(universe_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_universes(self) -> list:
        """Get configured universes (excluding -1)"""
        universes = []
        for spinbox in self.universe_spinboxes:
            value = spinbox.value()
            if value >= 0:
                universes.append(value)
        return universes


class SerialManagerTab(QWidget):
    """Tab Serial/IOBoard Manager"""
    
    # Signals
    board_connected = pyqtSignal(int)  # board_number
    board_disconnected = pyqtSignal(int)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.serial_controller = None  # Will be set by main window
        
        # Admin mode
        self._is_admin = False
        
        self.init_ui()
        self.init_timer()
    
    def set_admin_mode(self, is_admin: bool):
        """Set admin mode"""
        self._is_admin = is_admin
        self._update_admin_ui()
    
    def _update_admin_ui(self):
        """Update UI based on admin status"""
        # Scan button always enabled
        # Connect/Disconnect buttons enabled if board selected
        # Manual mapping only for admin
        
        if hasattr(self, 'manual_mapping_button'):
            self.manual_mapping_button.setEnabled(self._is_admin)
            if not self._is_admin:
                self.manual_mapping_button.setToolTip("🔒 Admin access required")
            else:
                self.manual_mapping_button.setToolTip("Configure manual universe mapping")
    
    def init_ui(self):
        """Khởi tạo UI"""
        layout = QVBoxLayout(self)
        
        # Control section
        self.create_control_section(layout)
        
        # IOBoard table
        self.create_board_table(layout)
        
        # Statistics section
        self.create_statistics_section(layout)
    
    def create_control_section(self, parent_layout):
        """Tạo control section"""
        control_group = QGroupBox("IOBoard Control")
        control_layout = QHBoxLayout(control_group)
        
        # Scan button
        self.scan_button = QPushButton("Scan IOBoards")
        self.scan_button.clicked.connect(self.scan_boards)
        self.scan_button.setToolTip("Scan COM ports for DMX Master IO boards")
        control_layout.addWidget(self.scan_button)
        
        # Connect All button
        self.connect_all_button = QPushButton("Connect All")
        self.connect_all_button.clicked.connect(self.connect_all_boards)
        self.connect_all_button.setEnabled(False)
        control_layout.addWidget(self.connect_all_button)
        
        # Disconnect All button
        self.disconnect_all_button = QPushButton("Disconnect All")
        self.disconnect_all_button.clicked.connect(self.disconnect_all_boards)
        self.disconnect_all_button.setEnabled(False)
        control_layout.addWidget(self.disconnect_all_button)
        
        control_layout.addStretch()
        
        # Auto-mapping checkbox
        self.auto_mapping_checkbox = QCheckBox("Auto-Mapping")
        self.auto_mapping_checkbox.setChecked(True)
        self.auto_mapping_checkbox.setToolTip(
            "Automatic universe mapping:\n"
            "Board #1 → Universe 0, 1\n"
            "Board #2 → Universe 2, 3\n"
            "Board #3 → Universe 4, 5\n"
            "..."
        )
        self.auto_mapping_checkbox.stateChanged.connect(self.on_auto_mapping_changed)
        control_layout.addWidget(self.auto_mapping_checkbox)
        
        # Status label
        self.status_label = QLabel("Ready to scan")
        self.status_label.setStyleSheet("color: #666;")
        control_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(control_group)
    
    def create_board_table(self, parent_layout):
        """Tạo IOBoard table"""
        table_group = QGroupBox("Detected IOBoards")
        table_layout = QVBoxLayout(table_group)
        
        # Table
        self.board_table = QTableWidget()
        self.board_table.setColumnCount(7)
        self.board_table.setHorizontalHeaderLabels([
            "Board #", "Port", "Device Name", "Universes", "Status", "Packets", "Errors"
        ])
        
        # Set column widths
        header = self.board_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        # Selection
        self.board_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.board_table.itemSelectionChanged.connect(self.on_board_selected)
        
        table_layout.addWidget(self.board_table)
        
        # Table controls
        controls = QHBoxLayout()
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_selected_board)
        self.connect_button.setEnabled(False)
        controls.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_selected_board)
        self.disconnect_button.setEnabled(False)
        controls.addWidget(self.disconnect_button)
        
        self.manual_mapping_button = QPushButton("Manual Mapping")
        self.manual_mapping_button.clicked.connect(self.configure_manual_mapping)
        self.manual_mapping_button.setEnabled(False)
        controls.addWidget(self.manual_mapping_button)
        
        controls.addStretch()
        
        self.board_count_label = QLabel("Boards: 0")
        controls.addWidget(self.board_count_label)
        
        table_layout.addLayout(controls)
        parent_layout.addWidget(table_group)
    
    def create_statistics_section(self, parent_layout):
        """Tạo statistics section"""
        stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout(stats_group)
        
        # Left stats
        left_layout = QFormLayout()
        
        self.total_boards_label = QLabel("0")
        left_layout.addRow("Total Boards:", self.total_boards_label)
        
        self.connected_boards_label = QLabel("0")
        left_layout.addRow("Connected:", self.connected_boards_label)
        
        stats_layout.addLayout(left_layout)
        
        # Right stats
        right_layout = QFormLayout()
        
        self.total_packets_label = QLabel("0")
        right_layout.addRow("Total Packets:", self.total_packets_label)
        
        self.total_errors_label = QLabel("0")
        right_layout.addRow("Errors:", self.total_errors_label)
        
        stats_layout.addLayout(right_layout)
        stats_layout.addStretch()
        
        parent_layout.addWidget(stats_group)
    
    def init_timer(self):
        """Khởi tạo update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_statistics)
        self.update_timer.start(1000)  # Update every second
    
    def set_serial_controller(self, controller):
        """Set serial controller reference"""
        self.serial_controller = controller
        
        if controller:
            # Set callbacks
            controller.set_connection_status_callback(self.on_connection_status_changed)
            controller.set_error_callback(self.on_serial_error)
    
    def scan_boards(self):
        """Scan for IOBoards"""
        if not self.serial_controller or not self.serial_controller.is_available():
            QMessageBox.warning(
                self,
                "Serial Not Available",
                "pyserial is not installed.\n\n"
                "Install: pip install pyserial"
            )
            return
        
        self.status_label.setText("Scanning...")
        self.scan_button.setEnabled(False)
        
        try:
            # Import here to check availability
            from src.serial.port_scanner import PortScanner
            
            # Scan
            boards = PortScanner.scan_ports()
            
            # Clear table
            self.board_table.setRowCount(0)
            
            # Add boards to table
            for board in boards:
                self.add_board_to_table(board)
            
            # Update count
            self.board_count_label.setText(f"Boards: {len(boards)}")
            
            if boards:
                self.status_label.setText(f"Found {len(boards)} board(s)")
                self.connect_all_button.setEnabled(True)
                
                logger.info(f"Scan complete: {len(boards)} IOBoard(s) detected")
            else:
                self.status_label.setText("No boards detected")
                logger.warning("No IOBoards detected")
            
        except Exception as e:
            logger.error(f"Scan error: {e}")
            QMessageBox.critical(
                self,
                "Scan Error",
                f"Failed to scan IOBoards:\n{str(e)}"
            )
            self.status_label.setText("Scan failed")
        
        finally:
            self.scan_button.setEnabled(True)
    
    def add_board_to_table(self, board_info):
        """Add board to table"""
        row = self.board_table.rowCount()
        self.board_table.insertRow(row)
        
        # Board #
        self.board_table.setItem(row, 0, QTableWidgetItem(str(board_info.board_number)))
        
        # Port
        self.board_table.setItem(row, 1, QTableWidgetItem(board_info.port))
        
        # Device Name
        self.board_table.setItem(row, 2, QTableWidgetItem(board_info.device_name))
        
        # Universes (empty until connected)
        self.board_table.setItem(row, 3, QTableWidgetItem("-"))
        
        # Status
        status_item = QTableWidgetItem("Disconnected")
        status_item.setBackground(QColor(200, 200, 200))
        self.board_table.setItem(row, 4, status_item)
        
        # Packets
        self.board_table.setItem(row, 5, QTableWidgetItem("0"))
        
        # Errors
        self.board_table.setItem(row, 6, QTableWidgetItem("0"))
    
    def connect_all_boards(self):
        """Connect to all detected boards"""
        if not self.serial_controller:
            return
        
        self.status_label.setText("Connecting to all boards...")
        
        try:
            count = self.serial_controller.scan_and_connect_all()
            
            if count > 0:
                self.status_label.setText(f"Connected to {count} board(s)")
                self.disconnect_all_button.setEnabled(True)
                self.refresh_table()
                
                logger.info(f"Connected to {count} IOBoard(s)")
            else:
                self.status_label.setText("No boards connected")
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to connect to boards:\n{str(e)}"
            )
    
    def disconnect_all_boards(self):
        """Disconnect from all boards"""
        if not self.serial_controller:
            return
        
        reply = QMessageBox.question(
            self,
            "Disconnect All",
            "Disconnect from all IOBoards?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.serial_controller.disconnect_all()
            self.refresh_table()
            self.status_label.setText("All boards disconnected")
            self.disconnect_all_button.setEnabled(False)
    
    def connect_selected_board(self):
        """Connect to selected board"""
        board_number = self.get_selected_board_number()
        if board_number is None:
            return
        
        if not self.serial_controller:
            return
        
        try:
            if self.serial_controller.connect_board(board_number):
                self.status_label.setText(f"Connected to Board #{board_number}")
                self.refresh_table()
            else:
                QMessageBox.warning(
                    self,
                    "Connection Failed",
                    f"Failed to connect to Board #{board_number}"
                )
        except Exception as e:
            logger.error(f"Connection error: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Connection error:\n{str(e)}"
            )
    
    def disconnect_selected_board(self):
        """Disconnect from selected board"""
        board_number = self.get_selected_board_number()
        if board_number is None:
            return
        
        if not self.serial_controller:
            return
        
        self.serial_controller.disconnect_board(board_number)
        self.refresh_table()
        self.status_label.setText(f"Disconnected from Board #{board_number}")
    
    def configure_manual_mapping(self):
        """Configure manual universe mapping"""
        if not self._is_admin:
            QMessageBox.warning(
                self,
                "Access Denied",
                "🔒 Admin access required to configure manual mapping"
            )
            return
        
        board_number = self.get_selected_board_number()
        if board_number is None:
            return
        
        if not self.serial_controller:
            return
        
        # Get current mapping
        mapping = self.serial_controller.get_universe_mapping()
        current_universes = mapping.get(board_number, [])
        
        # Show dialog
        dialog = ManualMappingDialog(board_number, current_universes, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_universes = dialog.get_universes()
            
            # Apply mapping
            self.serial_controller.set_manual_mapping(board_number, new_universes)
            
            # Disable auto-mapping if manual mapping used
            if new_universes:
                self.auto_mapping_checkbox.setChecked(False)
            
            self.refresh_table()
            
            QMessageBox.information(
                self,
                "Mapping Updated",
                f"Board #{board_number} → Universes {new_universes}"
            )
    
    def on_auto_mapping_changed(self, state):
        """Handle auto-mapping checkbox change"""
        if not self.serial_controller:
            return
        
        enabled = (state == Qt.CheckState.Checked.value)
        self.serial_controller.auto_mapping_enabled = enabled
        
        if enabled:
            # Apply auto-mapping
            self.serial_controller.apply_auto_mapping()
            self.refresh_table()
            self.status_label.setText("Auto-mapping applied")
            logger.info("Auto-mapping enabled")
        else:
            self.status_label.setText("Auto-mapping disabled (use manual mapping)")
            logger.info("Auto-mapping disabled")
    
    def get_selected_board_number(self) -> int:
        """Get selected board number from table"""
        selected = self.board_table.selectionModel().selectedRows()
        if not selected:
            return None
        
        row = selected[0].row()
        item = self.board_table.item(row, 0)
        if item:
            try:
                return int(item.text())
            except:
                return None
        return None
    
    def on_board_selected(self):
        """Handle board selection"""
        board_number = self.get_selected_board_number()
        
        if board_number is not None:
            # Check if connected
            if self.serial_controller:
                connected = board_number in self.serial_controller.get_connected_boards()
                
                self.connect_button.setEnabled(not connected)
                self.disconnect_button.setEnabled(connected)
                self.manual_mapping_button.setEnabled(connected and self._is_admin)
        else:
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(False)
            self.manual_mapping_button.setEnabled(False)
    
    def refresh_table(self):
        """Refresh table with latest info"""
        if not self.serial_controller:
            return
        
        mapping = self.serial_controller.get_universe_mapping()
        connected_boards = self.serial_controller.get_connected_boards()
        
        for row in range(self.board_table.rowCount()):
            board_num_item = self.board_table.item(row, 0)
            if not board_num_item:
                continue
            
            try:
                board_number = int(board_num_item.text())
            except:
                continue
            
            # Update universes
            universes = mapping.get(board_number, [])
            uni_str = ", ".join(str(u) for u in universes) if universes else "-"
            self.board_table.setItem(row, 3, QTableWidgetItem(uni_str))
            
            # Update status
            if board_number in connected_boards:
                status_item = QTableWidgetItem("Connected")
                status_item.setBackground(QColor(0, 255, 0))
                
                # Update stats
                stats = self.serial_controller.get_board_statistics(board_number)
                if stats:
                    self.board_table.setItem(row, 5, QTableWidgetItem(str(stats['packets_sent'])))
                    self.board_table.setItem(row, 6, QTableWidgetItem(str(stats['errors'])))
            else:
                status_item = QTableWidgetItem("Disconnected")
                status_item.setBackground(QColor(200, 200, 200))
            
            self.board_table.setItem(row, 4, status_item)
    
    def update_statistics(self):
        """Update statistics display"""
        if not self.serial_controller:
            return
        
        stats = self.serial_controller.get_all_statistics()
        
        self.total_boards_label.setText(str(stats['total_boards']))
        self.connected_boards_label.setText(str(stats['connected_boards']))
        self.total_packets_label.setText(str(stats['total_packets_sent']))
        self.total_errors_label.setText(str(stats['total_errors']))
        
        # Refresh table periodically
        self.refresh_table()
    
    def on_connection_status_changed(self, board_number: int, connected: bool):
        """Callback when connection status changes"""
        status = "connected" if connected else "disconnected"
        logger.info(f"Board #{board_number} {status}")
        
        # Emit signal
        if connected:
            self.board_connected.emit(board_number)
        else:
            self.board_disconnected.emit(board_number)
        
        # Refresh table
        self.refresh_table()
    
    def on_serial_error(self, board_number: int, error_msg: str):
        """Callback when serial error occurs"""
        logger.error(f"Serial error on Board #{board_number}: {error_msg}")
        
        # Could show notification to user
        # For now just log it
