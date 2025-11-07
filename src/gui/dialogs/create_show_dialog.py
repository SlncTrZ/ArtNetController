"""
Create Show Dialog - Unified dialog for creating shows from recordings
Used by both "Create Show" and "Move to Shows" functions
"""

import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QMessageBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class CreateShowDialog(QDialog):
    """Dialog for creating a show with metadata and audio assignment"""
    
    def __init__(self, parent=None, default_name="", recording_duration=0):
        super().__init__(parent)
        self.setWindowTitle("Create Show")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.recording_duration = recording_duration
        self.audio_file_path = None
        
        self._init_ui(default_name)
        
    def _init_ui(self, default_name):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        
        # Show Information Group
        info_group = QGroupBox("📝 Show Information")
        info_layout = QFormLayout()
        
        # Show Name
        self.name_edit = QLineEdit(default_name)
        self.name_edit.setPlaceholderText("Enter show name...")
        info_layout.addRow("Show Name:", self.name_edit)
        
        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional description...")
        info_layout.addRow("Description:", self.description_edit)
        
        # Duration (read-only)
        duration_label = QLabel(f"{self.recording_duration:.1f}s")
        duration_label.setStyleSheet("color: #666; font-style: italic;")
        info_layout.addRow("Duration:", duration_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Audio Assignment Group
        audio_group = QGroupBox("🎵 Audio Assignment (Optional)")
        audio_layout = QVBoxLayout()
        
        # Audio file selection
        audio_row = QHBoxLayout()
        self.audio_path_label = QLabel("No audio file selected")
        self.audio_path_label.setStyleSheet("color: #666; font-style: italic;")
        audio_row.addWidget(self.audio_path_label)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_audio)
        audio_row.addWidget(browse_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_audio)
        audio_row.addWidget(clear_btn)
        
        audio_layout.addLayout(audio_row)
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("✅ Create Show")
        create_btn.setDefault(True)
        create_btn.clicked.connect(self._validate_and_accept)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_layout.addWidget(create_btn)
        
        layout.addLayout(btn_layout)
        
    def _browse_audio(self):
        """Browse for audio file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "Audio Files (*.mp3 *.wav *.m4a *.flac *.aac);;All Files (*)"
        )
        
        if file_path:
            self.audio_file_path = file_path
            self.audio_path_label.setText(Path(file_path).name)
            self.audio_path_label.setStyleSheet("color: #000; font-style: normal;")
            
    def _clear_audio(self):
        """Clear audio file selection"""
        self.audio_file_path = None
        self.audio_path_label.setText("No audio file selected")
        self.audio_path_label.setStyleSheet("color: #666; font-style: italic;")
        
    def _validate_and_accept(self):
        """Validate input and accept dialog"""
        show_name = self.name_edit.text().strip()
        
        if not show_name:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "⚠️ Please enter a show name"
            )
            self.name_edit.setFocus()
            return
            
        self.accept()
        
    def get_show_data(self):
        """Get show data from dialog
        
        Returns:
            dict: Show metadata and audio path
        """
        return {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.text().strip(),
            'audio_file': self.audio_file_path
        }
