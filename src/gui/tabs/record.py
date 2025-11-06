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
                           QCheckBox, QSplitter, QDialog, QLineEdit)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

# Import timecode system
from src.system.timecode_receiver import (
    TimecodeManager, NetTimecodeReceiver, ArtNet4TimecodeReceiver
)
from src.system.crash_reporter import get_user_data_dir

logger = logging.getLogger(__name__)

# Binary DMX Recording Format Functions
def write_dmxrec_file(file_path: Path, dmx_data_list: list):
    """
    Write DMX data to binary .dmxrec file
    Format: [frame_count][frame1][frame2]...[frameN]
    Frame format: [timestamp_ms(4bytes)][universe(2bytes)][channel_count(2bytes)][data(Nbytes)]
    """
    with open(file_path, 'wb') as f:
        # Write frame count (4 bytes)
        frame_count = len(dmx_data_list)
        f.write(struct.pack('<I', frame_count))
        
        for frame in dmx_data_list:
            # timestamp_ms (4 bytes, unsigned int)
            timestamp_ms = int(frame['timestamp'] * 1000)
            f.write(struct.pack('<I', timestamp_ms))
            
            # universe (2 bytes, unsigned short)
            f.write(struct.pack('<H', frame['universe']))
            
            # channel_count (2 bytes, unsigned short)
            channel_count = len(frame['data'])
            f.write(struct.pack('<H', channel_count))
            
            # DMX data (N bytes, each channel is 1 byte)
            f.write(bytes(frame['data']))
    
    logger.info(f"Binary DMX file written: {file_path} ({frame_count} frames)")

def read_dmxrec_file(file_path: Path):
    """
    Read DMX data from binary .dmxrec file
    Returns list of DMX frames
    """
    dmx_frames = []
    
    with open(file_path, 'rb') as f:
        # Read frame count
        frame_count_data = f.read(4)
        if len(frame_count_data) != 4:
            raise ValueError("Invalid .dmxrec file: missing frame count")
        
        frame_count = struct.unpack('<I', frame_count_data)[0]
        logger.info(f"Reading {frame_count} frames from {file_path}")
        
        for i in range(frame_count):
            # Read timestamp (4 bytes)
            timestamp_data = f.read(4)
            if len(timestamp_data) != 4:
                logger.warning(f"Incomplete frame {i}: missing timestamp")
                break
            timestamp_ms = struct.unpack('<I', timestamp_data)[0]
            
            # Read universe (2 bytes)
            universe_data = f.read(2)
            if len(universe_data) != 2:
                logger.warning(f"Incomplete frame {i}: missing universe")
                break
            universe = struct.unpack('<H', universe_data)[0]
            
            # Read channel count (2 bytes)
            channel_count_data = f.read(2)
            if len(channel_count_data) != 2:
                logger.warning(f"Incomplete frame {i}: missing channel count")
                break
            channel_count = struct.unpack('<H', channel_count_data)[0]
            
            # Read DMX data (N bytes)
            dmx_data = f.read(channel_count)
            if len(dmx_data) != channel_count:
                logger.warning(f"Incomplete frame {i}: expected {channel_count} channels, got {len(dmx_data)}")
                break
            
            dmx_frames.append({
                'timestamp': timestamp_ms / 1000.0,
                'universe': universe,
                'data': list(dmx_data)
            })
    
    logger.info(f"Successfully read {len(dmx_frames)} frames from {file_path}")
    return dmx_frames

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
        self.auto_trim_checkbox.setChecked(True)
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
        self.timecode_sync_checkbox.setChecked(False)  # OFF by default (V2.0.2 - Manual control preferred)
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
        self.timecode_source_combo.setEnabled(True)  # Enabled by default since timecode is ON
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
        self.silence_threshold_slider.setValue(5)
        self.silence_threshold_slider.valueChanged.connect(self.update_threshold_label)
        threshold_layout.addWidget(self.silence_threshold_slider)
        
        self.threshold_label = QLabel("5")
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
        self.midi_device_combo.setEnabled(checked)
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
        
        # If recording is active, consider stopping (optional)
        # For now, let recording continue even if timecode stops

    def stop_recording(self):
        """Dừng recording"""
        self.is_recording_active = False
        self.is_waiting_for_timecode = False  # Reset waiting state
        
        # V2.0.2: Reset timecode tracking state
        self.last_timecode_value = None
        self.timecode_running = False
        
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
                
                # 1. Save binary DMX data (.dmxrec)
                write_dmxrec_file(dmxrec_path, data_to_save)
                
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
                
                # File size
                size_mb = file_path.stat().st_size / (1024 * 1024)
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
            self.delete_recording_button.setEnabled(True)
        else:
            self.load_recording_button.setEnabled(False)
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
                file_path.unlink()
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
        """Create a show from recording with MP3 assignment"""
        if not self.recorded_data:
            QMessageBox.warning(self, "No Data", "No recording data to create show from.")
            return
        
        dialog = CreateShowDialog(self, self.recorded_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            show_data = dialog.get_show_data()
            try:
                self.save_show_file(show_data)
                QMessageBox.information(
                    self,
                    "Show Created",
                    f"Show '{show_data['metadata']['name']}' created successfully!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to create show: {str(e)}"
                )
    
    def save_show_file(self, show_data):
        """Save show data to shows directory with binary format"""
        # V2.0.2: Use AppData for shows (not Program Files)
        shows_dir = get_user_data_dir() / "data" / "shows"
        shows_dir.mkdir(parents=True, exist_ok=True)
        
        show_name = show_data['metadata']['name'].replace(' ', '_')
        base_path = shows_dir / show_name
        
        # Save binary DMX data (.dmxrec)
        dmxrec_path = base_path.with_suffix('.dmxrec')
        write_dmxrec_file(dmxrec_path, show_data['data'])
        
        # Save show metadata (.json) - without DMX data
        show_metadata = show_data.copy()
        show_metadata['metadata']['binary_file'] = dmxrec_path.name
        show_metadata['format_version'] = '2.0'
        del show_metadata['data']  # Remove data from JSON (now in binary file)
        
        json_path = base_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(show_metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Show saved with binary format: {dmxrec_path} + {json_path}")
    
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


class CreateShowDialog(QDialog):
    """Dialog for creating a show from recording"""
    
    def __init__(self, parent, recorded_data):
        super().__init__(parent)
        self.recorded_data = recorded_data
        self.setWindowTitle("Create Show from Recording")
        self.setFixedSize(500, 400)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        
        # Show information
        info_group = QGroupBox("Show Information")
        info_layout = QVBoxLayout(info_group)
        
        # Show name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Show Name:"))
        self.name_input = QLineEdit()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.name_input.setText(f"Light Show {timestamp}")
        name_layout.addWidget(self.name_input)
        info_layout.addLayout(name_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.desc_input = QLineEdit()
        self.desc_input.setText("Light show created from DMX recording")
        desc_layout.addWidget(self.desc_input)
        info_layout.addLayout(desc_layout)
        
        # Author
        author_layout = QHBoxLayout()
        author_layout.addWidget(QLabel("Author:"))
        self.author_input = QLineEdit()
        self.author_input.setText("Art-Net Studio")
        author_layout.addWidget(self.author_input)
        info_layout.addLayout(author_layout)
        
        layout.addWidget(info_group)
        
        # MP3 Assignment
        music_group = QGroupBox("Music Assignment")
        music_layout = QVBoxLayout(music_group)
        
        # MP3 file selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("MP3 File:"))
        self.mp3_path_input = QLineEdit()
        file_layout.addWidget(self.mp3_path_input)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_mp3)
        file_layout.addWidget(self.browse_button)
        music_layout.addLayout(file_layout)
        
        # Song details
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Song Title:"))
        self.title_input = QLineEdit()
        title_layout.addWidget(self.title_input)
        music_layout.addLayout(title_layout)
        
        artist_layout = QHBoxLayout()
        artist_layout.addWidget(QLabel("Artist:"))
        self.artist_input = QLineEdit()
        artist_layout.addWidget(self.artist_input)
        music_layout.addLayout(artist_layout)
        
        # Duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (seconds):"))
        self.duration_input = QSpinBox()
        self.duration_input.setMaximum(3600)  # Max 1 hour
        if self.recorded_data:
            recording_duration = self.recorded_data[-1]['timestamp'] if self.recorded_data else 0
            self.duration_input.setValue(int(recording_duration + 10))  # Add 10s buffer
        duration_layout.addWidget(self.duration_input)
        music_layout.addLayout(duration_layout)
        
        layout.addWidget(music_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("Create Show")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def browse_mp3(self):
        """Browse for MP3 file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select MP3 File",
            "data/music",
            "MP3 Files (*.mp3);;All Files (*)"
        )
        
        if file_path:
            self.mp3_path_input.setText(file_path)
            # Auto-fill title from filename if empty
            if not self.title_input.text():
                filename = Path(file_path).stem
                self.title_input.setText(filename.replace('_', ' ').title())
    
    def accept(self):
        """Accept dialog and validate inputs"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a show name.")
            return
        
        super().accept()
        
    def reject(self):
        """Reject dialog"""
        super().reject()
    
    def get_show_data(self):
        """Get show data from dialog inputs"""
        # Convert recording data to scenes
        scenes = self.convert_recording_to_scenes()
        
        # Get unique universes
        universes = list(set(point['universe'] for point in self.recorded_data))
        
        # Create playlist if MP3 is selected
        playlist = []
        if self.mp3_path_input.text():
            playlist.append({
                "file_path": self.mp3_path_input.text(),
                "title": self.title_input.text() or "Untitled",
                "artist": self.artist_input.text() or "Unknown Artist",
                "duration": float(self.duration_input.value()),
                "start_time": 0.0,
                "fade_in": 2.0,
                "fade_out": 3.0,
                "loop": False
            })
        
        # Calculate total duration
        duration = self.recorded_data[-1]['timestamp'] if self.recorded_data else 0
        
        return {
            "metadata": {
                "name": self.name_input.text(),
                "description": self.desc_input.text(),
                "author": self.author_input.text(),
                "created_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "modified_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "version": "1.0",
                "duration": duration,
                "bpm": 120.0,  # Default BPM
                "universes": universes
            },
            "playlist": playlist,
            "scenes": scenes,
            "data": self.recorded_data  # V2.0.2: Include DMX recording data for binary file
        }
    
    def convert_recording_to_scenes(self):
        """Convert recording data points to scenes"""
        scenes = []
        
        if not self.recorded_data:
            return scenes
        
        # Group data points by time intervals (every 5 seconds)
        interval = 5.0
        current_time = 0.0
        scene_counter = 1
        
        while current_time < self.recorded_data[-1]['timestamp']:
            # Find data points in this time interval
            interval_data = [
                point for point in self.recorded_data
                if current_time <= point['timestamp'] < current_time + interval
            ]
            
            if interval_data:
                # Average the DMX values in this interval
                channels = {}
                universes_in_interval = set()
                
                for point in interval_data:
                    universes_in_interval.add(point['universe'])
                    for i, value in enumerate(point['data']):
                        if value > 0:  # Only include non-zero channels
                            channel_key = str(i + 1)
                            if channel_key not in channels:
                                channels[channel_key] = []
                            channels[channel_key].append(value)
                
                # Average the channel values
                averaged_channels = {}
                for channel, values in channels.items():
                    averaged_channels[channel] = int(sum(values) / len(values))
                
                # Create scene for each universe in this interval
                for universe in universes_in_interval:
                    scene = {
                        "name": f"Scene {scene_counter}",
                        "universe": universe,
                        "channels": averaged_channels,
                        "timestamp": current_time,
                        "duration": interval,
                        "fade_time": 1.0
                    }
                    scenes.append(scene)
                    scene_counter += 1
            
            current_time += interval
        
        return scenes