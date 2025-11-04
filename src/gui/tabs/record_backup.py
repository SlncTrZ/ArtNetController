"""
Record Tab - Tab ghi và chỉnh sửa DMX (chỉ admin)
"""

import logging
import time
import json
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                           QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                           QProgressBar, QSlider, QSpinBox, QTextEdit,
                           QFileDialog, QMessageBox, QHeaderView, QComboBox,
                           QCheckBox, QSplitter, QDialog, QLineEdit)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

class RecordTab(QWidget):
    """Tab Record - Chỉ dành cho admin"""
    
    # Signal for thread-safe UI updates
    preview_update_signal = pyqtSignal(str)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.is_recording_active = False
        self.recorded_data = []
        self.start_time = None
        self.current_recording = None
        
        self.init_ui()
        self.init_timer()
        
        # Connect signal to slot
        self.preview_update_signal.connect(self.update_preview_ui)
    
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
        self.universe_combo.addItems(["All"] + [str(i) for i in range(16)])
        universe_layout.addWidget(self.universe_combo)
        settings_layout.addLayout(universe_layout)
        
        # Auto trim silence
        self.auto_trim_checkbox = QCheckBox("Auto Trim Silence")
        self.auto_trim_checkbox.setChecked(True)
        settings_layout.addWidget(self.auto_trim_checkbox)
        
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
    
    def toggle_recording(self):
        """Toggle recording state"""
        if not self.is_recording_active:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Bắt đầu recording"""
        self.is_recording_active = True
        self.recorded_data = []
        self.start_time = time.time()
        
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
        
        self.pause_button.setEnabled(True)
        self.status_label.setText("Recording...")
        
        logger.info("DMX recording started")
    
    def stop_recording(self):
        """Dừng recording"""
        self.is_recording_active = False
        
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
        
        self.pause_button.setEnabled(False)
        # Update buttons
        self.save_button.setEnabled(len(self.recorded_data) > 0)
        self.create_show_button.setEnabled(len(self.recorded_data) > 0)
        self.status_label.setText("Recording Stopped")
        
        logger.info(f"DMX recording stopped - {len(self.recorded_data)} data points recorded")
    
    def pause_recording(self):
        """Tạm dừng recording"""
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
        if not self.is_recording_active:
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
        """Lưu recording"""
        if not self.recorded_data:
            return
        
        # Get file name
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"DMX_Recording_{timestamp}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Recording",
            str(Path(self.config_manager.get_app_config('recording.path', 'data/recordings')) / default_name),
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                # Apply auto trim if enabled
                data_to_save = self.recorded_data.copy()
                if self.auto_trim_checkbox.isChecked():
                    data_to_save = self.apply_auto_trim(data_to_save)
                
                # Create recording metadata
                recording_data = {
                    'metadata': {
                        'name': Path(file_path).stem,
                        'created': time.time(),
                        'duration': data_to_save[-1]['timestamp'] if data_to_save else 0,
                        'data_points': len(data_to_save),
                        'universes': list(set(point['universe'] for point in data_to_save)),
                        'settings': {
                            'universe_filter': self.universe_combo.currentText(),
                            'auto_trim': self.auto_trim_checkbox.isChecked(),
                            'silence_threshold': self.silence_threshold_slider.value(),
                            'min_silence_duration': self.min_silence_spin.value()
                        }
                    },
                    'data': data_to_save
                }
                
                # Save to file
                with open(file_path, 'w') as f:
                    json.dump(recording_data, f, indent=2)
                
                QMessageBox.information(
                    self,
                    "Recording Saved",
                    f"Recording saved successfully to {file_path}"
                )
                
                # Refresh recordings list
                self.refresh_recordings()
                
                logger.info(f"Recording saved: {file_path}")
                
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
        recording_path = Path(self.config_manager.get_app_config('recording.path', 'data/recordings'))
        
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
        """Save show data to shows directory"""
        shows_dir = Path("data/shows")
        shows_dir.mkdir(exist_ok=True)
        
        filename = f"{show_data['metadata']['name'].replace(' ', '_')}.json"
        file_path = shows_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(show_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Show saved: {file_path}")


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
            "scenes": scenes
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