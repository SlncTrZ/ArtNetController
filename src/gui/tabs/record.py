"""
Record Tab - Tab ghi và chỉnh sửa DMX (chỉ admin)
V2.0: Added Timecode Sync Recording support
"""

import logging
import time
import json
import struct
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                           QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                           QProgressBar, QSlider, QSpinBox, QTextEdit,
                           QFileDialog, QMessageBox, QHeaderView, QComboBox,
                           QCheckBox, QSplitter, QDialog, QLineEdit, QInputDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

# Import timecode system
from src.system.timecode_receiver import (
    TimecodeManager, NetTimecodeReceiver, ArtNet4TimecodeReceiver
)
from src.system.crash_reporter import get_user_data_dir
from src.show.dmx_recorder import DMXRecorder
from src.gui.dialogs.create_show_dialog import CreateShowDialog

logger = logging.getLogger(__name__)

class RecordTab(QWidget):
    """Tab Record - Chỉ dành cho admin"""
    
    # Signal for thread-safe UI updates
    preview_update_signal = pyqtSignal(str)
    
    def __init__(self, config_manager, artnet_controller=None):
        super().__init__()
        self.config_manager = config_manager
        self.artnet_controller = artnet_controller  # V2.0: for pause/resume output
        self.is_recording_active = False
        self.recorded_data = []
        self.start_time = None
        self.current_recording = None
        
        # ═══════════════════════════════════════════════════════════════
        # TIMECODE SYNC RECORDING - V2.0 State Variables
        # ═══════════════════════════════════════════════════════════════
        self.is_waiting_for_timecode = False
        self.recording_start_timecode = None
        self.recording_fps = 30
        self.recording_timecode_source = None
        
        # V2.0.2: Timecode start detection state
        self.last_timecode_value = None  # Last received timecode in seconds
        self.timecode_running = False     # Whether timecode is currently running
        
        # V2.0.3: Auto-stop on timecode end
        self.last_timecode_update_time = None  # Timestamp of last timecode update
        self.timecode_timeout_seconds = 3.0    # Detect timeout after 3 seconds
        self.timecode_auto_trim_seconds = 3.0  # Auto-trim this many seconds after stop
        self.timecode_watchdog_timer = None    # Timer to check timecode timeout
        
        # Initialize timecode system
        self.timecode_manager = TimecodeManager()
        self.active_timecode_receivers = []
        
        self.init_ui()
        self.init_timer()
        
        # Connect signal to slot
        self.preview_update_signal.connect(self.update_preview_ui)
    
    def set_artnet_controller(self, artnet_controller):
        """Set Art-Net controller and restart timecode monitoring if needed"""
        logger.info(f"Setting Art-Net controller: {artnet_controller}")
        self.artnet_controller = artnet_controller
        
        # If timecode sync is enabled and we have an Art-Net controller, restart monitoring
        if self.timecode_sync_checkbox.isChecked() and artnet_controller is not None:
            logger.info("Restarting timecode monitoring with Art-Net controller...")
            self._start_timecode_monitoring()
    
    def init_ui(self):
        """Khởi tạo UI"""
        layout = QVBoxLayout(self)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Recording controls
        left_panel = QWidget()
        self.create_recording_controls(left_panel)
        splitter.addWidget(left_panel)
        
        # Right panel - Recording management
        right_panel = QWidget()
        self.create_recording_management(right_panel)
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([400, 600])
    
    def create_recording_controls(self, parent):
        """Tạo recording controls"""
        layout = QVBoxLayout(parent)
        
        # Recording status
        status_group = QGroupBox("Recording Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Ready to Record")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        status_layout.addWidget(self.status_label)
        
        self.time_label = QLabel("00:00:00")
        self.time_label.setFont(QFont("monospace", 14))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.time_label)
        
        self.data_count_label = QLabel("Data Points: 0")
        status_layout.addWidget(self.data_count_label)
        
        layout.addWidget(status_group)
        
        # Recording controls
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Main buttons
        button_layout = QHBoxLayout()
        
        self.record_button = QPushButton("START RECORDING")
        self.record_button.setMinimumHeight(50)
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
        """)
        self.record_button.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_button)
        
        self.pause_button = QPushButton("PAUSE")
        self.pause_button.setMinimumHeight(50)
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_recording)
        button_layout.addWidget(self.pause_button)
        
        controls_layout.addLayout(button_layout)
        
        # Save/Clear buttons
        action_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Recording")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_recording)
        action_layout.addWidget(self.save_button)
        
        self.create_show_button = QPushButton("Create Show")
        self.create_show_button.setEnabled(False)
        self.create_show_button.clicked.connect(self.create_show)
        action_layout.addWidget(self.create_show_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_recording)
        action_layout.addWidget(self.clear_button)
        
        controls_layout.addLayout(action_layout)
        
        layout.addWidget(controls_group)
        
        # Recording settings
        settings_group = QGroupBox("Recording Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Universe filter
        universe_layout = QHBoxLayout()
        universe_layout.addWidget(QLabel("Record Universe:"))
        self.universe_combo = QComboBox()
        # Respect admin-configured max universes from unified system config
        try:
            from system.config_manager import get_config_manager
            _max_universes = int(get_config_manager().get('universes.max_universes', 32))
        except Exception:
            _max_universes = 32
        _max_universes = max(1, min(512, _max_universes))

        self.universe_combo.addItem("All", -1)
        for i in range(_max_universes):
            self.universe_combo.addItem(f"Universe {i}", i)
        universe_layout.addWidget(self.universe_combo)
        settings_layout.addLayout(universe_layout)
        
        # Auto trim silence
        self.auto_trim_checkbox = QCheckBox("Auto Trim Silence")
        self.auto_trim_checkbox.setChecked(False)  # OFF by default (timecode recording handles timing)
        self.auto_trim_checkbox.setToolTip(
            "Automatically remove silence at start/end of recording.\n"
            "Not needed when using timecode sync."
        )
        settings_layout.addWidget(self.auto_trim_checkbox)
        
        # Disable DMX output during recording (V2.0 - Safety feature)
        self.disable_output_checkbox = QCheckBox("Disable DMX Output During Record (Recommended)")
        self.disable_output_checkbox.setChecked(True)  # ON by default for safety
        self.disable_output_checkbox.setToolTip(
            "When enabled, DMX output will be paused during recording\n"
            "to prevent affecting live fixtures. This is recommended\n"
            "when testing or creating new shows."
        )
        self.disable_output_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                color: #ff9800;
            }
        """)
        settings_layout.addWidget(self.disable_output_checkbox)

        # ═══════════════════════════════════════════════════════════════
        # TIMECODE SYNC RECORDING - V2.0 Professional Feature
        # ═══════════════════════════════════════════════════════════════
        
        # Timecode Sync Recording
        timecode_group = QGroupBox("⏱️ Timecode Sync Recording")
        timecode_layout = QVBoxLayout(timecode_group)
        
        # Enable/Disable Timecode Sync
        self.timecode_sync_checkbox = QCheckBox("⏸️ Wait for Timecode Signal Before Recording")
        self.timecode_sync_checkbox.setChecked(True)  # ON by default - wait for timecode
        self.timecode_sync_checkbox.setToolTip(
            "⏸️ TIMECODE SYNC MODE:\n"
            "When enabled, clicking START RECORDING will NOT begin immediately.\n"
            "Instead, recording will wait for a timecode signal from Depence/Resolume/MADRIX.\n\n"
            "📍 USE CASE: Perfect sync with external show software\n"
            "⚡ MANUAL MODE (unchecked): Record immediately when clicked\n\n"
            "DEFAULT: OFF for quick manual recording"
        )
        self.timecode_sync_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                color: #2196F3;
                font-size: 11pt;
            }
        """)
        timecode_layout.addWidget(self.timecode_sync_checkbox)
        
        # Timecode source selection
        timecode_source_layout = QHBoxLayout()
        timecode_source_layout.addWidget(QLabel("Timecode Source:"))
        self.timecode_source_combo = QComboBox()
        self.timecode_source_combo.addItems([
            "Art-Net 4 Timecode (Depence) - Variable fps",
            "Net-timecode (Network) - 25fps"
        ])
        self.timecode_source_combo.setCurrentText("Art-Net 4 Timecode (Depence) - Variable fps")
        self.timecode_source_combo.setEnabled(True)  # Enabled by default since timecode checkbox is ON
        timecode_source_layout.addWidget(self.timecode_source_combo)
        timecode_layout.addLayout(timecode_source_layout)
        
        # Timecode settings
        timecode_settings_layout = QHBoxLayout()
        
        # Net-timecode port
        timecode_settings_layout.addWidget(QLabel("Network Port:"))
        self.timecode_port_spinbox = QSpinBox()
        self.timecode_port_spinbox.setRange(1024, 65535)
        self.timecode_port_spinbox.setValue(3040)  # Standard Net-timecode port
        self.timecode_port_spinbox.setEnabled(False)
        timecode_settings_layout.addWidget(self.timecode_port_spinbox)
        
        timecode_layout.addLayout(timecode_settings_layout)
        
        # Timecode status display
        self.timecode_status_label = QLabel("Timecode: Not connected")
        self.timecode_status_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 5px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
        """)
        timecode_layout.addWidget(self.timecode_status_label)
        
        # Connect checkbox to enable/disable controls
        self.timecode_sync_checkbox.toggled.connect(self._on_timecode_sync_toggled)
        
        # V2.0.2: Don't start timecode monitoring by default (checkbox is OFF)
        # User must manually enable timecode sync when needed for Depence workflow
        
        settings_layout.addWidget(timecode_group)

        # Silence threshold
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Silence Threshold:"))
        self.silence_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.silence_threshold_slider.setRange(0, 255)
        self.silence_threshold_slider.setValue(0)  # 0 by default (timecode handles timing)
        self.silence_threshold_slider.setToolTip(
            "DMX value threshold for detecting silence.\n"
            "Only used when Auto Trim is enabled."
        )
        self.silence_threshold_slider.valueChanged.connect(self.update_threshold_label)
        threshold_layout.addWidget(self.silence_threshold_slider)
        
        self.threshold_label = QLabel("0")
        threshold_layout.addWidget(self.threshold_label)
        settings_layout.addLayout(threshold_layout)
        
        # Min silence duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Min Silence (sec):"))
        self.min_silence_spin = QSpinBox()
        self.min_silence_spin.setRange(1, 60)
        self.min_silence_spin.setValue(2)
        duration_layout.addWidget(self.min_silence_spin)
        settings_layout.addLayout(duration_layout)
        
        layout.addWidget(settings_group)
        
        # Preview
        preview_group = QGroupBox("Live Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setFont(QFont("monospace", 8))
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        layout.addWidget(preview_group)
        
        layout.addStretch()
    
    def create_recording_management(self, parent):
        """Tạo recording management"""
        layout = QVBoxLayout(parent)
        
        # Recordings list
        recordings_group = QGroupBox("Saved Recordings")
        recordings_layout = QVBoxLayout(recordings_group)
        
        # Table
        self.recordings_table = QTableWidget()
        self.recordings_table.setColumnCount(6)
        self.recordings_table.setHorizontalHeaderLabels([
            "Name", "Date", "Duration", "Data Points", "Universes", "Size"
        ])
        
        # Set column widths
        header = self.recordings_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.recordings_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.recordings_table.itemSelectionChanged.connect(self.on_recording_selected)
        
        recordings_layout.addWidget(self.recordings_table)
        
        # Table controls
        table_controls = QHBoxLayout()
        
        self.refresh_recordings_button = QPushButton("Refresh")
        self.refresh_recordings_button.clicked.connect(self.refresh_recordings)
        table_controls.addWidget(self.refresh_recordings_button)
        
        self.load_recording_button = QPushButton("Load")
        self.load_recording_button.setEnabled(False)
        self.load_recording_button.clicked.connect(self.load_recording)
        table_controls.addWidget(self.load_recording_button)
        
        self.move_to_shows_button = QPushButton("📤 Move to Shows")
        self.move_to_shows_button.setEnabled(False)
        self.move_to_shows_button.setToolTip("Move recording to Show Manager library")
        self.move_to_shows_button.clicked.connect(self.move_recording_to_shows)
        table_controls.addWidget(self.move_to_shows_button)
        
        self.delete_recording_button = QPushButton("Delete")
        self.delete_recording_button.setEnabled(False)
        self.delete_recording_button.clicked.connect(self.delete_recording)
        table_controls.addWidget(self.delete_recording_button)
        
        table_controls.addStretch()
        recordings_layout.addLayout(table_controls)
        
        layout.addWidget(recordings_group)
        
        # Recording editor
        editor_group = QGroupBox("Recording Editor")
        editor_layout = QVBoxLayout(editor_group)
        
        # Editor controls
        editor_controls = QHBoxLayout()
        
        self.play_button = QPushButton("Play")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.play_recording)
        editor_controls.addWidget(self.play_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_playback)
        editor_controls.addWidget(self.stop_button)
        
        editor_controls.addWidget(QLabel("Speed:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1.0x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        editor_controls.addWidget(self.speed_combo)
        
        editor_controls.addStretch()
        editor_layout.addLayout(editor_controls)
        
        # Timeline
        timeline_layout = QHBoxLayout()
        timeline_layout.addWidget(QLabel("Timeline:"))
        
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setEnabled(False)
        self.timeline_slider.valueChanged.connect(self.seek_recording)
        timeline_layout.addWidget(self.timeline_slider)
        
        self.position_label = QLabel("00:00 / 00:00")
        timeline_layout.addWidget(self.position_label)
        editor_layout.addLayout(timeline_layout)
        
        # Editing tools
        edit_tools = QHBoxLayout()
        
        self.trim_start_button = QPushButton("Trim Start")
        self.trim_start_button.setEnabled(False)
        self.trim_start_button.clicked.connect(self.trim_start)
        edit_tools.addWidget(self.trim_start_button)
        
        self.trim_end_button = QPushButton("Trim End")
        self.trim_end_button.setEnabled(False)
        self.trim_end_button.clicked.connect(self.trim_end)
        edit_tools.addWidget(self.trim_end_button)
        
        self.auto_trim_button = QPushButton("Auto Trim Silence")
        self.auto_trim_button.setEnabled(False)
        self.auto_trim_button.clicked.connect(self.auto_trim_silence)
        edit_tools.addWidget(self.auto_trim_button)
        
        edit_tools.addStretch()
        editor_layout.addLayout(edit_tools)
        
        layout.addWidget(editor_group)
        
        # Load recordings
        self.refresh_recordings()
    
    def init_timer(self):
        """Khởi tạo timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(100)  # Update every 100ms
    
    def _on_timecode_sync_toggled(self, checked: bool):
        """Handle timecode sync checkbox toggle"""
        # Enable/disable timecode controls
        self.timecode_source_combo.setEnabled(checked)
        self.timecode_port_spinbox.setEnabled(checked)
        
        if checked:
            # Start timecode monitoring
            self.timecode_status_label.setText("Timecode: Waiting for signal...")
            self.timecode_status_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3e0;
                    border: 1px solid #ff9800;
                    color: #e65100;
                    padding: 5px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                    font-weight: bold;
                }
            """)
            logger.info("Timecode sync enabled - waiting for signal")
            
            # TODO: Start timecode receivers based on selected source
            self._start_timecode_monitoring()
        else:
            # Stop timecode monitoring
            self.timecode_status_label.setText("Timecode: Not connected")
            self.timecode_status_label.setStyleSheet("""
                QLabel {
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    padding: 5px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }
            """)
            logger.info("Timecode sync disabled")
            
            # TODO: Stop timecode receivers
            self._stop_timecode_monitoring()
    
    def _start_timecode_monitoring(self):
        """Start timecode monitoring based on selected source"""
        source = self.timecode_source_combo.currentText()
        logger.info(f"Starting timecode monitoring, source: {source}")
        logger.info(f"Art-Net controller available: {self.artnet_controller is not None}")
        
        # Stop any existing receivers first
        self._stop_timecode_monitoring()
        
        success_count = 0
        
        if "Net-timecode" in source:
            port = self.timecode_port_spinbox.value()
            net_receiver = self.timecode_manager.create_net_timecode_receiver(port)
            net_receiver.set_callbacks(self.on_timecode_received, self.on_timecode_stopped)
            if net_receiver.start():
                self.active_timecode_receivers.append("net-timecode")
                success_count += 1
                logger.info(f"Net-timecode receiver started on port {port}")
        
        if "Art-Net 4" in source:
            logger.info(f"Creating Art-Net 4 Timecode receiver with controller: {self.artnet_controller}")
            artnet4_receiver = self.timecode_manager.create_artnet4_timecode_receiver(
                artnet_controller=self.artnet_controller  # Pass Art-Net controller for shared socket
            )
            logger.info(f"Setting callbacks: on_timecode_received={self.on_timecode_received}")
            artnet4_receiver.set_callbacks(self.on_timecode_received, self.on_timecode_stopped)
            logger.info("Starting Art-Net 4 Timecode receiver...")
            if artnet4_receiver.start():
                self.active_timecode_receivers.append("artnet4-timecode")
                success_count += 1
                logger.info("Art-Net 4 Timecode receiver started (Depence compatible)")
            else:
                logger.warning("Art-Net 4 Timecode receiver failed to start")
                logger.warning("This may be due to port conflict with main Art-Net controller")
                logger.warning("For Depence: Ensure timecode is being sent to Art-Net universe")
        
        if success_count > 0:
            active_list = ", ".join(self.active_timecode_receivers)
            logger.info(f"Timecode monitoring active: {active_list}")
            self.timecode_status_label.setText(f"Listening: {active_list}")
        else:
            logger.warning("No timecode receivers could be started")
            logger.warning("For Depence integration:")
            logger.warning("   1. Ensure python-rtmidi is installed")
            logger.warning("   2. Check MIDI interface connection")
            logger.warning("   3. Verify Depence MTC output settings")
            self.timecode_status_label.setText("Error: No receivers (check MIDI setup)")
            self.timecode_status_label.setStyleSheet("""
                QLabel {
                    background-color: #ffebee;
                    border: 1px solid #f44336;
                    color: #c62828;
                    padding: 5px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }
            """)
    
    def _stop_timecode_monitoring(self):
        """Stop all timecode monitoring"""
        try:
            self.timecode_manager.stop_all()
            self.active_timecode_receivers.clear()
            logger.info("All timecode receivers stopped")
        except Exception as e:
            logger.error(f"Error stopping timecode receivers: {e}")
    
    def _start_mtc_receiver(self):
        """Start MTC (MIDI Time Code) receiver - DEPRECATED, use _start_timecode_monitoring"""
        logger.info("Use _start_timecode_monitoring instead")
        
    def _start_net_timecode_receiver(self):
        """Start Net-timecode receiver - DEPRECATED, use _start_timecode_monitoring"""
        logger.info("Use _start_timecode_monitoring instead")
        
    def _start_ltc_receiver(self):
        """Start LTC (Linear Time Code) receiver - DEPRECATED, use _start_timecode_monitoring"""
        logger.info("🎧 Use _start_timecode_monitoring instead")

    def toggle_recording(self):
        """Toggle recording state"""
        if not self.is_recording_active:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Bắt đầu recording với timecode sync support"""
        # CRITICAL: Ensure Art-Net controller is available for timecode sync
        if self.timecode_sync_checkbox.isChecked() and not self.artnet_controller:
            QMessageBox.warning(
                self,
                "Art-Net Not Started",
                "Art-Net must be running to receive timecode signals.\n\n"
                "Please start Art-Net in Control tab first."
            )
            logger.warning("Cannot start recording: Art-Net not running (needed for timecode)")
            return
        
        # Check if timecode sync is enabled
        if self.timecode_sync_checkbox.isChecked():
            # Timecode sync mode - don't start recording immediately
            self.is_waiting_for_timecode = True
            self.is_recording_active = False  # Not recording yet, just waiting
            
            self.record_button.setText("WAITING FOR TIMECODE...")
            self.record_button.setStyleSheet("""
                QPushButton {
                    background-color: #ff9800;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                    border: 2px solid #ff6f00;
                }
                QPushButton:hover {
                    background-color: #f57c00;
                    border: 2px solid #e65100;
                }
            """)
            
            # Enable CANCEL RECORDING button
            self.pause_button.setText("CANCEL RECORDING")
            self.pause_button.setEnabled(True)
            self.pause_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            
            # Update status and timecode display
            if self.disable_output_checkbox.isChecked() and self.artnet_controller:
                self.artnet_controller.pause_output()
                logger.info("DMX output PAUSED for recording (safety mode)")
                self.status_label.setText("⏸️ Waiting for timecode from START (00:00:00:00)... (DMX OUTPUT DISABLED)")
                self.status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
            else:
                self.status_label.setText("⏸️ Waiting for timecode from START (00:00:00:00)...")
                self.status_label.setStyleSheet("color: #2196F3; font-weight: bold;")
            
            self.timecode_status_label.setText("⏸️ Waiting: Play show from beginning in Depence/Resolume")
            self.timecode_status_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3e0;
                    border: 2px solid #ff9800;
                    color: #e65100;
                    padding: 8px;
                    border-radius: 5px;
                    font-family: 'Courier New', monospace;
                    font-weight: bold;
                }
            """)
            
            logger.info("⏸️ Recording armed - waiting for timecode from START (< 2 seconds)")
            logger.info("💡 Please play your show from the beginning in Depence/Resolume")
            return
        
        # Normal recording mode (immediate start)
        self._start_recording_immediately()
    
    def _start_recording_immediately(self):
        """Start recording immediately (called from start_recording or timecode trigger)"""
        self.is_recording_active = True
        self.is_waiting_for_timecode = False
        self.recorded_data = []
        self.start_time = time.time()
        
        # V2.0: Pause DMX output if checkbox is enabled  
        if self.disable_output_checkbox.isChecked() and self.artnet_controller:
            self.artnet_controller.pause_output()
            logger.info("DMX output PAUSED for recording (safety mode)")
            self.status_label.setText("Recording... (DMX OUTPUT DISABLED)")
            self.status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
        else:
            self.status_label.setText("Recording...")
            self.status_label.setStyleSheet("")

        self.record_button.setText("STOP RECORDING")
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #4caf50;
            }
        """)
        
        # Reset PAUSE button to normal PAUSE functionality
        self.pause_button.setText("PAUSE")
        self.pause_button.setEnabled(True)
        self.pause_button.setStyleSheet("")  # Reset to default style
        self.status_label.setText("Recording...")
        
        logger.info("DMX recording started")
    
    def on_timecode_received(self, timecode_data: dict):
        """Called when timecode signal is received from external source"""
        # Debug: log receipt and payload shape to help trace crashes
        try:
            logger.debug(f"RecordTab.on_timecode_received payload: {timecode_data}, is_waiting={getattr(self, 'is_waiting_for_timecode', False)}")
        except Exception:
            logger.debug("RecordTab.on_timecode_received received payload (unserializable)")
        timecode_string = timecode_data.get('timecode', '00:00:00:00')
        fps = timecode_data.get('fps', 30)
        source = timecode_data.get('source', 'Unknown')
        
        # Parse timecode to seconds for watchdog detection
        try:
            tc_parts = timecode_string.split(':')
            if len(tc_parts) == 4:
                hours = int(tc_parts[0])
                minutes = int(tc_parts[1])
                seconds = int(tc_parts[2])
                frames = int(tc_parts[3])
                current_tc_seconds = hours * 3600 + minutes * 60 + seconds + (frames / fps)
            else:
                current_tc_seconds = 0.0
        except:
            current_tc_seconds = 0.0
        
        # V2.0.3: Update watchdog timer ONLY if timecode VALUE changed
        # This prevents false updates when Depence keeps sending same timecode after show ends
        import time
        last_tc_value = getattr(self, '_watchdog_last_tc_value', None)
        if last_tc_value is None or abs(current_tc_seconds - last_tc_value) > 0.01:
            # Timecode changed - update timestamp and value
            self.last_timecode_update_time = time.time()
            self._watchdog_last_tc_value = current_tc_seconds
            logger.debug(f"Watchdog: Timecode changed to {current_tc_seconds:.2f}s - reset timer")
        else:
            # Timecode stuck - don't update timestamp
            logger.debug(f"Watchdog: Timecode stuck at {current_tc_seconds:.2f}s - not resetting timer")
        
        # Start watchdog timer if recording
        if self.is_recording_active and self.timecode_watchdog_timer is None:
            self._start_timecode_watchdog()
        
        # Update timecode display
        self.timecode_status_label.setText(f"Timecode: {timecode_string} ({fps}fps) - {source}")
        self.timecode_status_label.setStyleSheet("""
            QLabel {
                background-color: #e8f5e8;
                border: 2px solid #4caf50;
                color: #2e7d32;
                padding: 8px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-weight: bold;
            }
        """)
        
        # If waiting for timecode to start recording, detect START event
        if getattr(self, 'is_waiting_for_timecode', False):
            # Parse timecode to seconds for comparison
            # Format: HH:MM:SS:FF (hours:minutes:seconds:frames)
            try:
                tc_parts = timecode_string.split(':')
                if len(tc_parts) == 4:
                    hours = int(tc_parts[0])
                    minutes = int(tc_parts[1])
                    seconds = int(tc_parts[2])
                    frames = int(tc_parts[3])
                    
                    # Calculate total seconds
                    current_tc_seconds = hours * 3600 + minutes * 60 + seconds + (frames / fps)
                    
                    # Detect START event:
                    # 1. Timecode jumped backward (reset/restart) - e.g., from 30s → 0s
                    # 2. Timecode started from near zero after being stopped
                    # 3. First timecode received and it's near start
                    
                    timecode_started = False
                    start_reason = ""
                    
                    if self.last_timecode_value is None:
                        # First timecode received
                        if current_tc_seconds < 2.0:
                            timecode_started = True
                            start_reason = "First timecode at beginning"
                            logger.info(f"🎬 FIRST TIMECODE at {timecode_string} ({current_tc_seconds:.2f}s)")
                        else:
                            logger.info(f"⏸️ First timecode at {timecode_string} ({current_tc_seconds:.2f}s) - waiting for restart")
                    else:
                        # Subsequent timecode - detect reset/restart
                        time_delta = current_tc_seconds - self.last_timecode_value
                        
                        # Case 1: Timecode jumped backward (reset) - e.g., 30s → 0s
                        if time_delta < -1.0:  # Jumped back more than 1 second
                            if current_tc_seconds < 2.0:
                                timecode_started = True
                                start_reason = f"Timecode RESET detected (from {self.last_timecode_value:.2f}s → {current_tc_seconds:.2f}s)"
                                logger.info(f"🔄 {start_reason}")
                            else:
                                logger.debug(f"Timecode jumped back but not to start: {self.last_timecode_value:.2f}s → {current_tc_seconds:.2f}s")
                        
                        # Case 2: Timecode was stopped (no change), now started from beginning
                        elif abs(time_delta) < 0.1 and current_tc_seconds < 2.0:
                            # Timecode hasn't changed much and is near start - likely a fresh start
                            if not self.timecode_running:
                                timecode_started = True
                                start_reason = "Timecode started from beginning"
                                logger.info(f"▶️ {start_reason}")
                        
                        # Update running state (timecode is running if it's changing)
                        self.timecode_running = abs(time_delta) > 0.05
                    
                    # Update last timecode value
                    self.last_timecode_value = current_tc_seconds
                    
                    # START RECORDING if timecode start event detected
                    if timecode_started:
                        logger.info(f"✅ Timecode START event - Beginning recording at {timecode_string}")
                        logger.info(f"   Reason: {start_reason}")
                        logger.debug(f"   Timecode: {timecode_string} at {fps}fps from {source}")

                        # Store timecode sync info
                        self.recording_start_timecode = timecode_string
                        self.recording_fps = fps
                        self.recording_timecode_source = source

                        # Start actual recording
                        try:
                            self._start_recording_immediately()
                        except Exception as e:
                            logger.error(f"Exception while starting recording from timecode: {e}", exc_info=True)

                        # Update timecode status to show recording
                        self.timecode_status_label.setText(f"🔴 Recording synced: {timecode_string} ({fps}fps) - {source}")
                        self.timecode_status_label.setStyleSheet("""
                            QLabel {
                                background-color: #e8f5e8;
                                border: 2px solid #4caf50;
                                color: #2e7d32;
                                padding: 8px;
                                border-radius: 5px;
                                font-family: 'Courier New', monospace;
                                font-weight: bold;
                            }
                        """)
                    else:
                        # Keep waiting - update status with current timecode
                        logger.debug(f"⏸️ Timecode at {current_tc_seconds:.2f}s - Waiting for show restart")
                        self.timecode_status_label.setText(f"⏸️ Waiting for START: {timecode_string} (restart show from beginning)")
                        self.timecode_status_label.setStyleSheet("""
                            QLabel {
                                background-color: #fff3e0;
                                border: 2px solid #ff9800;
                                color: #e65100;
                                padding: 8px;
                                border-radius: 5px;
                                font-family: 'Courier New', monospace;
                                font-weight: bold;
                            }
                        """)
            except Exception as e:
                logger.error(f"Failed to parse timecode {timecode_string}: {e}")
                # If parsing fails, don't start recording
    
    def on_timecode_stopped(self):
        """Called when timecode signal stops"""
        logger.warning("Timecode signal lost")
        
        # Reset timecode tracking state
        self.last_timecode_value = None
        self.timecode_running = False
        
        self.timecode_status_label.setText("Timecode: Signal lost!")
        self.timecode_status_label.setStyleSheet("""
            QLabel {
                background-color: #ffebee;
                border: 2px solid #f44336;
                color: #c62828;
                padding: 8px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-weight: bold;
            }
        """)
        
        # V2.0.3: Auto-stop recording if timecode stopped during recording
        if self.is_recording_active:
            logger.warning("⚠️ Timecode stopped during recording - will auto-stop if not resumed")
    
    def _start_timecode_watchdog(self):
        """Start watchdog timer to detect timecode timeout"""
        if self.timecode_watchdog_timer is not None:
            logger.debug("Timecode watchdog already running")
            return  # Already running
        
        from PyQt6.QtCore import QTimer
        self.timecode_watchdog_timer = QTimer(self)
        self.timecode_watchdog_timer.timeout.connect(self._check_timecode_timeout)
        self.timecode_watchdog_timer.start(500)  # Check every 500ms
        self._last_watchdog_log = -1  # Reset log throttling
        logger.info("⏱️ Timecode watchdog started - will auto-stop after 3s timeout")
        logger.info(f"⏱️ Watchdog config: timeout={self.timecode_timeout_seconds}s, check_interval=500ms")
    
    def _stop_timecode_watchdog(self):
        """Stop watchdog timer"""
        if self.timecode_watchdog_timer is not None:
            self.timecode_watchdog_timer.stop()
            self.timecode_watchdog_timer = None
            logger.info("⏹️ Timecode watchdog stopped")
    
    def _check_timecode_timeout(self):
        """Check if timecode has timed out and auto-stop recording"""
        try:
            if not self.is_recording_active:
                logger.debug("Recording stopped - stopping watchdog")
                self._stop_timecode_watchdog()
                return
            
            # Only auto-stop if recording with timecode sync
            if not self.timecode_sync_checkbox.isChecked():
                return
            
            # Check if timecode has timed out
            if self.last_timecode_update_time is not None:
                import time
                time_since_update = time.time() - self.last_timecode_update_time
                
                # Log only significant events (every 1 second when > 1s)
                if time_since_update >= 1.0:
                    current_log_tick = int(time_since_update)
                    if current_log_tick != getattr(self, '_last_watchdog_log', -1):
                        logger.info(f"⏱️ Watchdog: {time_since_update:.1f}s since last timecode change | timeout={self.timecode_timeout_seconds}s")
                        self._last_watchdog_log = current_log_tick
                
                if time_since_update > self.timecode_timeout_seconds:
                    logger.warning(f"⏹️ Timecode timeout detected ({time_since_update:.1f}s) - Auto-stopping recording")
                    logger.info("💡 Show has ended in playback software - will auto-trim and save")
                    
                    # Auto-trim the last 3 seconds (the timeout period) BEFORE stopping
                    # This ensures the trimmed data is ready
                    trimmed_seconds = self._auto_trim_recording_end()
                    
                    # Auto-stop recording
                    self.stop_recording()
                    
                    # Auto-save the recording
                    saved_path = self._auto_save_recording()
                    
                    # Show notification
                    from PyQt6.QtWidgets import QMessageBox
                    if saved_path:
                        QMessageBox.information(
                            self,
                            "Recording Auto-Stopped & Saved",
                            f"✅ Recording automatically stopped, trimmed, and saved!\n\n"
                            f"• Show ended in playback software\n"
                            f"• Last {trimmed_seconds:.0f} seconds auto-trimmed\n"
                            f"• Saved to: {saved_path.name}\n\n"
                            f"💡 Your recording now matches the exact show duration."
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Recording Auto-Stopped",
                            f"✅ Recording automatically stopped and trimmed!\n\n"
                            f"• Last {trimmed_seconds:.0f} seconds auto-trimmed\n"
                            f"⚠️ Auto-save failed - please save manually"
                        )
            else:
                logger.debug("Watchdog: last_timecode_update_time is None - waiting for first timecode")
                
        except Exception as e:
            logger.error(f"❌ Watchdog error: {e}", exc_info=True)
    
    def _auto_trim_recording_end(self):
        """Auto-trim the last N seconds from recording (timeout period)
        
        Returns:
            float: Number of seconds trimmed
        """
        if not self.recorded_data or len(self.recorded_data) == 0:
            logger.warning("No recorded data to trim")
            return 0.0
        
        try:
            # Get last timestamp
            if self.recorded_data:
                last_timestamp = self.recorded_data[-1]['timestamp']
                trim_cutoff = last_timestamp - self.timecode_auto_trim_seconds
                
                if trim_cutoff <= 0:
                    logger.warning(f"Recording too short to trim {self.timecode_auto_trim_seconds}s")
                    return 0.0
                
                # Count original data points
                original_count = len(self.recorded_data)
                
                # Remove data points after cutoff
                self.recorded_data = [dp for dp in self.recorded_data if dp['timestamp'] <= trim_cutoff]
                
                trimmed_count = original_count - len(self.recorded_data)
                new_duration = self.recorded_data[-1]['timestamp'] if self.recorded_data else 0
                actual_trimmed_seconds = last_timestamp - new_duration
                
                logger.info(f"✂️ Auto-trimmed {trimmed_count} data points ({actual_trimmed_seconds:.1f}s)")
                logger.info(f"   Original: {original_count} points, {last_timestamp:.1f}s")
                logger.info(f"   Trimmed:  {len(self.recorded_data)} points, {new_duration:.1f}s")
                
                return actual_trimmed_seconds
                
        except Exception as e:
            logger.error(f"Error auto-trimming recording: {e}")
            return 0.0
    
    def _auto_save_recording(self):
        """Auto-save recording without prompting user
        
        Returns:
            Path: Path to saved file, or None if failed
        """
        if not self.recorded_data:
            logger.warning("No recorded data to save")
            return None
        
        try:
            # Generate auto filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            default_name = f"DMX_Recording_{timestamp}"
            
            # V2.0.2: Use AppData for recordings
            recordings_dir = get_user_data_dir() / "data" / "recordings"
            recordings_dir.mkdir(parents=True, exist_ok=True)
            
            base_path = recordings_dir / default_name
            dmxrec_path = base_path.with_suffix('.dmxrec')
            json_path = base_path.with_suffix('.json')
            
            # Data already trimmed by _auto_trim_recording_end()
            data_to_save = self.recorded_data.copy()
            
            # 1. Save binary DMX data (.dmxrec) using DMXRecorder V2.0 format
            recorder = DMXRecorder(str(dmxrec_path))
            recorder.start_recording(fps=40.0)
            
            for frame in data_to_save:
                recorder.write_frame(
                    universe=frame['universe'],
                    dmx_data=bytes(frame['data'])
                )
            
            stats = recorder.stop_recording()
            logger.info(f"Binary recording saved: {dmxrec_path} ({stats.get('frame_count', 0)} frames, {stats.get('duration', 0):.2f}s)")
            
            # 2. Save metadata (.json)
            metadata = {
                'metadata': {
                    'name': base_path.stem,
                    'created': time.time(),
                    'duration': data_to_save[-1]['timestamp'] if data_to_save else 0,
                    'data_points': len(data_to_save),
                    'universes': list(set(point['universe'] for point in data_to_save)),
                    'binary_file': dmxrec_path.name,
                    'timecode_sync': True,  # Mark as timecode recording
                    'auto_stopped': True,   # Mark as auto-stopped
                    'settings': {
                        'universe_filter': self.universe_combo.currentText(),
                        'auto_trim': False,  # Already trimmed
                        'silence_threshold': 0,
                        'timecode_source': getattr(self, 'recording_timecode_source', 'Unknown')
                    }
                },
                'format_version': '2.0',
                'audio_file': None
            }
            
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Auto-saved recording: {dmxrec_path} + {json_path}")
            
            # Refresh recordings list
            self.refresh_recordings()
            
            return dmxrec_path
            
        except Exception as e:
            logger.error(f"Failed to auto-save recording: {e}")
            return None

    def stop_recording(self):
        """Dừng recording"""
        self.is_recording_active = False
        self.is_waiting_for_timecode = False  # Reset waiting state
        
        # V2.0.2: Reset timecode tracking state
        self.last_timecode_value = None
        self.timecode_running = False
        
        # V2.0.3: Stop timecode watchdog
        self._stop_timecode_watchdog()
        self.last_timecode_update_time = None
        
        # V2.0: Resume DMX output if it was paused
        if self.disable_output_checkbox.isChecked() and self.artnet_controller:
            self.artnet_controller.resume_output()
            logger.info("DMX output RESUMED after recording")

        self.record_button.setText("START RECORDING")
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
        """)
        
        # Reset PAUSE button
        self.pause_button.setText("PAUSE")
        self.pause_button.setEnabled(False)
        self.pause_button.setStyleSheet("")  # Reset to default style
        
        # Update buttons
        self.save_button.setEnabled(len(self.recorded_data) > 0)
        self.create_show_button.setEnabled(len(self.recorded_data) > 0)
        self.status_label.setText("Recording Stopped")
        self.status_label.setStyleSheet("")  # Reset status label style
        
        logger.info(f"DMX recording stopped - {len(self.recorded_data)} data points recorded")
    
    def pause_recording(self):
        """Tạm dừng recording hoặc hủy recording khi đang chờ timecode"""
        # Check if we're waiting for timecode (CANCEL RECORDING mode)
        if hasattr(self, 'is_waiting_for_timecode') and self.is_waiting_for_timecode:
            # Cancel the waiting for timecode
            self.is_waiting_for_timecode = False
            self.is_recording_active = False
            
            # V2.0.2: Reset timecode tracking state
            self.last_timecode_value = None
            self.timecode_running = False
            
            # Resume DMX output if it was paused
            if self.disable_output_checkbox.isChecked() and self.artnet_controller:
                self.artnet_controller.resume_output()
                logger.info("DMX output RESUMED after canceling recording")
            
            # Reset buttons to initial state
            self.record_button.setText("START RECORDING")
            self.record_button.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #f44336;
                }
            """)
            
            self.pause_button.setText("PAUSE")
            self.pause_button.setEnabled(False)
            self.pause_button.setStyleSheet("")  # Reset to default style
            
            # Reset status
            self.status_label.setText("Recording Canceled")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
            
            # Reset timecode status
            self.timecode_status_label.setText("Timecode: Not connected")
            self.timecode_status_label.setStyleSheet("""
                QLabel {
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    padding: 5px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }
            """)
            
            logger.info("Recording canceled while waiting for timecode")
            return
        
        # Normal PAUSE/RESUME functionality for active recording
        if self.is_recording_active:
            self.is_recording_active = False
            self.pause_button.setText("RESUME")
            self.status_label.setText("Recording Paused")
        else:
            self.is_recording_active = True
            self.pause_button.setText("PAUSE")
            self.status_label.setText("Recording...")
    
    def clear_recording(self):
        """Xóa recording hiện tại"""
        if self.recorded_data:
            reply = QMessageBox.question(
                self,
                "Clear Recording",
                "Are you sure you want to clear the current recording?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.recorded_data = []
                self.save_button.setEnabled(False)
                self.create_show_button.setEnabled(False)
                self.preview_text.clear()
                self.data_count_label.setText("Data Points: 0")
    
    def record_dmx_data(self, universe: int, dmx_data: bytes):
        """Record DMX data point"""
        # Don't record if not in recording mode (either waiting for timecode or actively recording)
        if not self.is_recording_active and not self.is_waiting_for_timecode:
            return
        
        # If waiting for timecode, don't record yet - wait for timecode trigger
        if self.is_waiting_for_timecode:
            return
        
        # Check universe filter
        universe_filter = self.universe_combo.currentText()
        if universe_filter != "All" and universe != int(universe_filter):
            return
        
        # Record data point
        timestamp = time.time() - self.start_time
        data_point = {
            'timestamp': timestamp,
            'universe': universe,
            'data': list(dmx_data)  # Convert bytes to list for JSON serialization
        }
        
        self.recorded_data.append(data_point)
        
        # Update preview
        self.update_preview(data_point)
    
    def update_preview(self, data_point):
        """Update live preview - thread safe"""
        # Only show non-zero channels
        non_zero_channels = []
        for i, value in enumerate(data_point['data']):
            if value > 0:
                non_zero_channels.append(f"Ch{i+1}:{value}")
        
        if non_zero_channels:
            preview_line = f"[{data_point['timestamp']:.2f}s] U{data_point['universe']}: {', '.join(non_zero_channels[:10])}"
            if len(non_zero_channels) > 10:
                preview_line += "..."
        else:
            preview_line = f"[{data_point['timestamp']:.2f}s] U{data_point['universe']}: All Zero"
        
        # Emit signal instead of direct UI update
        self.preview_update_signal.emit(preview_line)
    
    def update_preview_ui(self, preview_line):
        """Update preview UI in main thread"""
        self.preview_text.append(preview_line)
        
        # Keep only last 50 lines
        text = self.preview_text.toPlainText().split('\n')
        if len(text) > 50:
            self.preview_text.setText('\n'.join(text[-50:]))
        
        # Scroll to bottom
        cursor = self.preview_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.preview_text.setTextCursor(cursor)
    
    def update_display(self):
        """Update display elements"""
        if self.is_recording_active and self.start_time:
            elapsed = time.time() - self.start_time
            self.time_label.setText(self.format_time(elapsed))
        
        self.data_count_label.setText(f"Data Points: {len(self.recorded_data)}")
    
    def format_time(self, seconds):
        """Format time as HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def save_recording(self):
        """Lưu recording với binary format (.dmxrec + .json)"""
        if not self.recorded_data:
            return
        
        # Get file name (without extension)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"DMX_Recording_{timestamp}"
        
        # V2.0.2: Use AppData for recordings (not Program Files)
        recordings_dir = get_user_data_dir() / "data" / "recordings"
        recordings_dir.mkdir(parents=True, exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Recording",
            str(recordings_dir / default_name),
            "DMX Recording (*.dmxrec);;All Files (*)"
        )
        
        if file_path:
            try:
                # Apply auto trim if enabled
                data_to_save = self.recorded_data.copy()
                if self.auto_trim_checkbox.isChecked():
                    data_to_save = self.apply_auto_trim(data_to_save)
                
                # Get paths for both files
                base_path = Path(file_path)
                if base_path.suffix == '.dmxrec':
                    base_path = base_path.with_suffix('')
                
                dmxrec_path = base_path.with_suffix('.dmxrec')
                json_path = base_path.with_suffix('.json')
                
                # 1. Save binary DMX data (.dmxrec) using DMXRecorder V2.0 format
                recorder = DMXRecorder(str(dmxrec_path))
                recorder.start_recording(fps=40.0)
                
                for frame in data_to_save:
                    recorder.write_frame(
                        universe=frame['universe'],
                        dmx_data=bytes(frame['data'])
                    )
                
                stats = recorder.stop_recording()
                logger.info(f"Binary recording saved: {dmxrec_path} ({stats.get('frame_count', 0)} frames, {stats.get('duration', 0):.2f}s)")
                
                # 2. Save metadata (.json)
                metadata = {
                    'metadata': {
                        'name': base_path.stem,
                        'created': time.time(),
                        'duration': data_to_save[-1]['timestamp'] if data_to_save else 0,
                        'data_points': len(data_to_save),
                        'universes': list(set(point['universe'] for point in data_to_save)),
                        'binary_file': dmxrec_path.name,  # Reference to binary file
                        'settings': {
                            'universe_filter': self.universe_combo.currentText(),
                            'auto_trim': self.auto_trim_checkbox.isChecked(),
                            'silence_threshold': self.silence_threshold_slider.value(),
                            'min_silence_duration': self.min_silence_spin.value()
                        }
                    },
                    'format_version': '2.0',  # Binary format version
                    'audio_file': None  # Will be set when creating show
                }
                
                with open(json_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                QMessageBox.information(
                    self,
                    "Recording Saved",
                    f"Recording saved successfully:\n- Binary: {dmxrec_path}\n- Metadata: {json_path}"
                )
                
                logger.info(f"Recording saved in binary format: {dmxrec_path} + {json_path}")
                
                # Refresh recordings list
                self.refresh_recordings()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to save recording: {str(e)}"
                )
                logger.error(f"Failed to save recording: {e}")
    
    def apply_auto_trim(self, data):
        """Apply auto trim silence"""
        if not data:
            return data
        
        threshold = self.silence_threshold_slider.value()
        min_duration = self.min_silence_spin.value()
        
        # Find silence periods
        silence_start = None
        trimmed_data = []
        
        for point in data:
            # Check if this point is "silent" (all values below threshold)
            is_silent = all(value <= threshold for value in point['data'])
            
            if is_silent:
                if silence_start is None:
                    silence_start = point['timestamp']
            else:
                if silence_start is not None:
                    # End of silence period
                    silence_duration = point['timestamp'] - silence_start
                    if silence_duration < min_duration:
                        # Keep this short silence
                        trimmed_data.append(point)
                    silence_start = None
                else:
                    trimmed_data.append(point)
        
        return trimmed_data
    
    def refresh_recordings(self):
        """Refresh recordings list"""
        # V2.0.2: Use AppData for recordings (not Program Files)
        recording_path = get_user_data_dir() / "data" / "recordings"
        
        if not recording_path.exists():
            recording_path.mkdir(parents=True, exist_ok=True)
        
        # Clear table
        self.recordings_table.setRowCount(0)
        
        # Load recordings
        json_files = list(recording_path.glob("*.json"))
        self.recordings_table.setRowCount(len(json_files))
        
        for row, file_path in enumerate(json_files):
            try:
                with open(file_path, 'r') as f:
                    recording_data = json.load(f)
                
                metadata = recording_data.get('metadata', {})
                
                # Name
                self.recordings_table.setItem(row, 0, QTableWidgetItem(metadata.get('name', file_path.stem)))
                
                # Date
                created = metadata.get('created', 0)
                date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(created))
                self.recordings_table.setItem(row, 1, QTableWidgetItem(date_str))
                
                # Duration
                duration = metadata.get('duration', 0)
                duration_str = self.format_time(duration)
                self.recordings_table.setItem(row, 2, QTableWidgetItem(duration_str))
                
                # Data points
                data_points = metadata.get('data_points', 0)
                self.recordings_table.setItem(row, 3, QTableWidgetItem(str(data_points)))
                
                # Universes
                universes = metadata.get('universes', [])
                universes_str = ", ".join(map(str, sorted(universes)))
                self.recordings_table.setItem(row, 4, QTableWidgetItem(universes_str))
                
                # File size - show KB for files < 1MB
                size_bytes = file_path.stat().st_size
                if size_bytes < 1024 * 1024:  # < 1MB
                    size_kb = size_bytes / 1024
                    size_str = f"{size_kb:.2f} KB"
                else:
                    size_mb = size_bytes / (1024 * 1024)
                    size_str = f"{size_mb:.2f} MB"
                self.recordings_table.setItem(row, 5, QTableWidgetItem(size_str))
                
                # Store file path in first item
                name_item = self.recordings_table.item(row, 0)
                name_item.setData(Qt.ItemDataRole.UserRole, str(file_path))
                
            except Exception as e:
                logger.error(f"Failed to load recording {file_path}: {e}")
    
    def on_recording_selected(self):
        """Handle recording selection"""
        selected_rows = self.recordings_table.selectionModel().selectedRows()
        
        if selected_rows:
            self.load_recording_button.setEnabled(True)
            self.move_to_shows_button.setEnabled(True)
            self.delete_recording_button.setEnabled(True)
        else:
            self.load_recording_button.setEnabled(False)
            self.move_to_shows_button.setEnabled(False)
            self.delete_recording_button.setEnabled(False)
    
    def load_recording(self):
        """Load selected recording"""
        selected_rows = self.recordings_table.selectionModel().selectedRows()
        
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        name_item = self.recordings_table.item(row, 0)
        file_path = name_item.data(Qt.ItemDataRole.UserRole)
        
        try:
            with open(file_path, 'r') as f:
                recording_data = json.load(f)
            
            self.current_recording = recording_data
            
            # Enable editor controls
            self.play_button.setEnabled(True)
            self.timeline_slider.setEnabled(True)
            self.trim_start_button.setEnabled(True)
            self.trim_end_button.setEnabled(True)
            self.auto_trim_button.setEnabled(True)
            
            # Update timeline
            data = recording_data.get('data', [])
            if data:
                max_time = data[-1]['timestamp']
                self.timeline_slider.setRange(0, int(max_time * 10))  # 0.1s resolution
                self.timeline_slider.setValue(0)
                self.position_label.setText(f"00:00 / {self.format_time(max_time)}")
            
            QMessageBox.information(
                self,
                "Recording Loaded",
                f"Recording loaded successfully: {recording_data.get('metadata', {}).get('name', 'Unknown')}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load recording: {str(e)}"
            )
    
    def delete_recording(self):
        """Delete selected recording"""
        selected_rows = self.recordings_table.selectionModel().selectedRows()
        
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        name_item = self.recordings_table.item(row, 0)
        file_path = Path(name_item.data(Qt.ItemDataRole.UserRole))
        
        reply = QMessageBox.question(
            self,
            "Delete Recording",
            f"Are you sure you want to delete recording '{file_path.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Delete both .json and .dmxrec files
                json_path = file_path
                dmxrec_path = file_path.with_suffix('.dmxrec')
                
                json_path.unlink(missing_ok=True)
                dmxrec_path.unlink(missing_ok=True)
                
                logger.info(f"Deleted recording files: {json_path.name} + {dmxrec_path.name}")
                
                self.refresh_recordings()
                
                QMessageBox.information(
                    self,
                    "Recording Deleted",
                    "Recording deleted successfully"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Delete Error",
                    f"Failed to delete recording: {str(e)}"
                )
    
    def move_recording_to_shows(self):
        """Move selected recording to Show Manager library with full show creation dialog"""
        selected_rows = self.recordings_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "⚠️ Please select a recording to move to shows")
            return
        
        row = selected_rows[0].row()
        name_item = self.recordings_table.item(row, 0)
        recording_json_path = Path(name_item.data(Qt.ItemDataRole.UserRole))
        
        try:
            # Load recording
            with open(recording_json_path, 'r', encoding='utf-8') as f:
                recording_data = json.load(f)
            
            # Get recording metadata
            metadata = recording_data.get('metadata', {})
            recording_name = metadata.get('name', recording_json_path.stem)
            duration = metadata.get('duration', 0)
            
            # Open create show dialog with recording name as default
            dialog = CreateShowDialog(
                self,
                default_name=recording_name,
                recording_duration=duration
            )
            
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return  # User cancelled
            
            show_info = dialog.get_show_data()
            show_name = show_info['name']
            
            # Prepare paths
            recordings_dir = get_user_data_dir() / "data" / "recordings"
            shows_dir = get_user_data_dir() / "data" / "shows"
            shows_dir.mkdir(parents=True, exist_ok=True)
            
            # Source files (recording)
            recording_dmxrec = recording_json_path.with_suffix('.dmxrec')
            
            # Destination files (show)
            show_base = shows_dir / show_name.replace(' ', '_')
            show_json = show_base.with_suffix('.json')
            show_dmxrec = show_base.with_suffix('.dmxrec')
            
            # Check if show already exists
            if show_json.exists():
                reply = QMessageBox.question(
                    self,
                    "Overwrite Show",
                    f"⚠️ Show '{show_name}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Copy/move files
            import shutil
            
            # Move .dmxrec file
            if recording_dmxrec.exists():
                shutil.move(str(recording_dmxrec), str(show_dmxrec))
            else:
                raise FileNotFoundError(f"Recording binary file not found: {recording_dmxrec}")
            
            # Update metadata for show format
            show_data = recording_data.copy()
            show_data['format_version'] = '2.0'
            show_data['metadata']['name'] = show_name
            show_data['metadata']['description'] = show_info['description']
            show_data['metadata']['binary_file'] = show_dmxrec.name
            show_data['audio_file'] = show_info['audio_file']
            
            # Remove 'data' field if exists (binary format)
            if 'data' in show_data:
                del show_data['data']
            
            # Save show JSON
            with open(show_json, 'w', encoding='utf-8') as f:
                json.dump(show_data, f, indent=2, ensure_ascii=False)
            
            # Delete original recording JSON
            recording_json_path.unlink()
            
            # Refresh recordings list
            self.refresh_recordings()
            
            # Reload Show Manager
            self._reload_show_manager()
            
            logger.info(f"Recording moved to shows: {recording_name} → {show_name}")
            
            QMessageBox.information(
                self,
                "Success",
                f"✅ Recording '{recording_name}' has been moved to Show Manager as '{show_name}'!\n\n"
                f"📂 Duration: {duration:.1f}s\n"
                f"🎵 Audio: {'Assigned' if show_info['audio_file'] else 'None'}\n\n"
                f"💡 The show is now available in Show Manager library."
            )
            
        except Exception as e:
            logger.error(f"Failed to move recording to shows: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"❌ Failed to move recording to shows:\n{str(e)}"
            )
    
    def play_recording(self):
        """Play loaded recording"""
        # TODO: Implement playback functionality
        QMessageBox.information(self, "Playback", "Playback functionality will be implemented")
    
    def stop_playback(self):
        """Stop playback"""
        # TODO: Implement stop playback
        pass
    
    def seek_recording(self, value):
        """Seek to position in recording"""
        if self.current_recording:
            time_pos = value / 10.0  # Convert back to seconds
            data = self.current_recording.get('data', [])
            if data:
                max_time = data[-1]['timestamp']
                self.position_label.setText(f"{self.format_time(time_pos)} / {self.format_time(max_time)}")
    
    def trim_start(self):
        """Trim start of recording"""
        # TODO: Implement trim start
        QMessageBox.information(self, "Trim", "Trim functionality will be implemented")
    
    def trim_end(self):
        """Trim end of recording"""
        # TODO: Implement trim end
        QMessageBox.information(self, "Trim", "Trim functionality will be implemented")
    
    def auto_trim_silence(self):
        """Auto trim silence from recording"""
        if not self.current_recording:
            return
        
        data = self.current_recording.get('data', [])
        if not data:
            return
        
        try:
            trimmed_data = self.apply_auto_trim(data)
            
            # Update current recording
            self.current_recording['data'] = trimmed_data
            self.current_recording['metadata']['data_points'] = len(trimmed_data)
            
            if trimmed_data:
                self.current_recording['metadata']['duration'] = trimmed_data[-1]['timestamp']
            
            QMessageBox.information(
                self,
                "Auto Trim",
                f"Trimmed from {len(data)} to {len(trimmed_data)} data points"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Trim Error",
                f"Failed to trim recording: {str(e)}"
            )
    
    def update_threshold_label(self, value):
        """Update silence threshold label"""
        self.threshold_label.setText(str(value))
    
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self.is_recording_active
    
    def set_admin_mode(self, is_admin: bool):
        """Set admin mode - in Record tab this doesn't change much since recording is always available"""
        # Record functionality is available to all users
        # Admin mode could control advanced features in future
        pass
    
    def create_show(self):
        """Create a show from current recording data"""
        if not self.recorded_data:
            QMessageBox.warning(self, "No Data", "⚠️ No recording data to create show from.\n\nPlease record something first!")
            return
        
        # Calculate duration
        duration = self.recorded_data[-1]['timestamp'] if self.recorded_data else 0
        
        # Open dialog
        dialog = CreateShowDialog(
            self, 
            default_name=f"Light Show {time.strftime('%Y%m%d_%H%M%S')}", 
            recording_duration=duration
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            show_info = dialog.get_show_data()
            try:
                # Prepare show data
                show_data = {
                    'metadata': {
                        'name': show_info['name'],
                        'description': show_info['description'],
                        'created': time.time(),
                        'duration': duration,
                        'data_points': len(self.recorded_data),
                        'universes': list(set(point['universe'] for point in self.recorded_data)),
                    },
                    'audio_file': show_info['audio_file'],
                    'data': self.recorded_data.copy()
                }
                
                # Save show
                self.save_show_file(show_data)
                
                # Reload Show Manager
                self._reload_show_manager()
                
                QMessageBox.information(
                    self,
                    "Show Created",
                    f"✅ Show '{show_info['name']}' created successfully!\n\n"
                    f"📂 Duration: {duration:.1f}s\n"
                    f"📊 Data points: {len(self.recorded_data)}\n"
                    f"🎵 Audio: {'Assigned' if show_info['audio_file'] else 'None'}\n\n"
                    f"💡 The show is now available in Show Manager library."
                )
                
                logger.info(f"Show created from current recording: {show_info['name']}")
                
            except Exception as e:
                logger.error(f"Failed to create show: {e}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Create Show Error",
                    f"❌ Failed to create show:\n{str(e)}"
                )
    
    def save_show_file(self, show_data):
        """Save show data to shows directory with binary format"""
        # V2.0.2: Use AppData for shows (not Program Files)
        shows_dir = get_user_data_dir() / "data" / "shows"
        shows_dir.mkdir(parents=True, exist_ok=True)
        
        show_name = show_data['metadata']['name'].replace(' ', '_')
        base_path = shows_dir / show_name
        
        # Save binary DMX data (.dmxrec) using DMXRecorder V2.0 format
        dmxrec_path = base_path.with_suffix('.dmxrec')
        recorder = DMXRecorder(str(dmxrec_path))
        recorder.start_recording(fps=40.0)
        
        for frame in show_data['data']:
            recorder.write_frame(
                universe=frame['universe'],
                dmx_data=bytes(frame['data'])
            )
        
        stats = recorder.stop_recording()
        logger.info(f"Binary show saved: {dmxrec_path} ({stats.get('frame_count', 0)} frames, {stats.get('duration', 0):.2f}s)")
        
        # Save show metadata (.json) - without DMX data
        show_metadata = show_data.copy()
        show_metadata['metadata']['binary_file'] = dmxrec_path.name
        show_metadata['format_version'] = '2.0'
        del show_metadata['data']  # Remove data from JSON (now in binary file)
        
        json_path = base_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(show_metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Show saved with binary format: {dmxrec_path} + {json_path}")
    
    def _reload_show_manager(self):
        """Reload Show Manager library after creating a show"""
        try:
            # Get main window reference
            main_window = self.window()
            if hasattr(main_window, 'show_manager_tab'):
                if hasattr(main_window.show_manager_tab, 'reload_shows'):
                    main_window.show_manager_tab.reload_shows()
                    logger.info("✅ Show Manager library reloaded")
                else:
                    logger.warning("ShowManagerTab does not have reload_shows method")
            else:
                logger.warning("Main window does not have show_manager_tab")
        except Exception as e:
            logger.error(f"Failed to reload Show Manager: {e}")
    
    def closeEvent(self, event):
        """Clean up when tab is closed"""
        try:
            # Stop any active recordings
            if self.is_recording_active:
                self.stop_recording()
            
            # Stop timecode monitoring
            self._stop_timecode_monitoring()
            
            logger.info("🧹 RecordTab cleanup completed")
        except Exception as e:
            logger.error(f"Error during RecordTab cleanup: {e}")
        
        # Call parent closeEvent
        super().closeEvent(event)
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self._stop_timecode_monitoring()
        except:
            pass