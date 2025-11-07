"""
Settings Tab - Tab cấu hình hệ thống
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QGroupBox, QLabel, QLineEdit, QSpinBox, QCheckBox,
                           QComboBox, QPushButton, QTabWidget, QTextEdit,
                           QFileDialog, QMessageBox, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

class SettingsTab(QWidget):
    """Tab Settings"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Khởi tạo UI"""
        layout = QVBoxLayout(self)
        
        # Settings tabs - Network Info, Shows, and System (V2.2)
        self.settings_tabs = QTabWidget()
        layout.addWidget(self.settings_tabs)
        
        # Create setting tabs
        self.create_network_info()
        self.create_show_settings()
        self.create_system_settings()  # V2.2: New tab
        
        # Buttons
        self.create_buttons(layout)
    
    def create_network_info(self):
        """Tạo Network Info tab"""
        from gui.widgets.ip_info_widget import IPInfoWidget
        
        network_info_widget = QWidget()
        layout = QVBoxLayout(network_info_widget)
        
        # Add IP info widget
        self.ip_info_widget = IPInfoWidget()
        layout.addWidget(self.ip_info_widget)
        
        # Add to settings tabs
        self.settings_tabs.addTab(network_info_widget, "Network Info")
    
    def create_artnet_settings(self):
        """Tạo Art-Net settings"""
        artnet_widget = QWidget()
        layout = QVBoxLayout(artnet_widget)
        
        # Network settings
        network_group = QGroupBox("Network Configuration")
        network_layout = QFormLayout(network_group)
        
        self.artnet_port_spin = QSpinBox()
        self.artnet_port_spin.setRange(1, 65535)
        self.artnet_port_spin.setValue(6454)
        network_layout.addRow("Art-Net Port:", self.artnet_port_spin)
        
        self.universe_spin = QSpinBox()
        self.universe_spin.setRange(0, 32767)
        self.universe_spin.setValue(0)
        network_layout.addRow("Default Universe:", self.universe_spin)
        
        self.refresh_rate_spin = QSpinBox()
        self.refresh_rate_spin.setRange(1, 44)
        self.refresh_rate_spin.setValue(30)
        self.refresh_rate_spin.setSuffix(" Hz")
        network_layout.addRow("Refresh Rate:", self.refresh_rate_spin)
        
        self.broadcast_edit = QLineEdit("255.255.255.255")
        network_layout.addRow("Broadcast Address:", self.broadcast_edit)
        
        layout.addWidget(network_group)
        
        # Discovery settings
        discovery_group = QGroupBox("Device Discovery")
        discovery_layout = QFormLayout(discovery_group)
        
        self.auto_discovery_checkbox = QCheckBox()
        self.auto_discovery_checkbox.setChecked(True)
        discovery_layout.addRow("Auto Discovery:", self.auto_discovery_checkbox)
        
        self.discovery_interval_spin = QSpinBox()
        self.discovery_interval_spin.setRange(5, 300)
        self.discovery_interval_spin.setValue(30)
        self.discovery_interval_spin.setSuffix(" seconds")
        discovery_layout.addRow("Discovery Interval:", self.discovery_interval_spin)
        
        layout.addWidget(discovery_group)
        
        self.settings_tabs.addTab(artnet_widget, "Art-Net")
    
    def create_webserver_settings(self):
        """Tạo Webserver settings"""
        webserver_widget = QWidget()
        layout = QVBoxLayout(webserver_widget)
        
        # Server settings
        server_group = QGroupBox("Web Server Configuration")
        server_layout = QFormLayout(server_group)
        
        self.webserver_enabled_checkbox = QCheckBox()
        self.webserver_enabled_checkbox.setChecked(True)
        server_layout.addRow("Enable Web Server:", self.webserver_enabled_checkbox)
        
        self.webserver_port_spin = QSpinBox()
        self.webserver_port_spin.setRange(1, 65535)
        self.webserver_port_spin.setValue(8080)
        server_layout.addRow("Web Server Port:", self.webserver_port_spin)
        
        self.webserver_host_edit = QLineEdit("0.0.0.0")
        server_layout.addRow("Host Address:", self.webserver_host_edit)
        
        layout.addWidget(server_group)
        
        # Upload settings
        upload_group = QGroupBox("File Upload")
        upload_layout = QFormLayout(upload_group)
        
        upload_path_layout = QHBoxLayout()
        self.upload_path_edit = QLineEdit("data/music")
        upload_path_layout.addWidget(self.upload_path_edit)
        
        self.upload_path_button = QPushButton("Browse")
        self.upload_path_button.clicked.connect(self.browse_upload_path)
        upload_path_layout.addWidget(self.upload_path_button)
        
        upload_layout.addRow("Upload Path:", upload_path_layout)
        
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(1, 500)
        self.max_file_size_spin.setValue(50)
        self.max_file_size_spin.setSuffix(" MB")
        upload_layout.addRow("Max File Size:", self.max_file_size_spin)
        
        layout.addWidget(upload_group)
        
        self.settings_tabs.addTab(webserver_widget, "Web Server")
    
    def create_show_settings(self):
        """Tạo Show settings"""
        show_widget = QWidget()
        layout = QVBoxLayout(show_widget)
        
        # Show management
        show_group = QGroupBox("Show Management")
        show_layout = QFormLayout(show_group)
        
        show_path_layout = QHBoxLayout()
        
        # Get actual AppData path for shows
        if hasattr(self.parent(), 'get_app_data_dir'):
            data_dir = self.parent().get_app_data_dir()
            default_shows_path = str(data_dir / "shows")
        else:
            default_shows_path = "data/shows"
        
        self.show_path_edit = QLineEdit(default_shows_path)
        self.show_path_edit.setReadOnly(True)  # Read-only to prevent user changes
        self.show_path_edit.setToolTip("Shows are stored in AppData for better permissions")
        show_path_layout.addWidget(self.show_path_edit)
        
        self.show_path_button = QPushButton("Browse")
        self.show_path_button.clicked.connect(self.browse_show_path)
        show_path_layout.addWidget(self.show_path_button)
        
        show_layout.addRow("Shows Path:", show_path_layout)
        
        self.auto_save_checkbox = QCheckBox()
        self.auto_save_checkbox.setChecked(True)
        show_layout.addRow("Auto Save:", self.auto_save_checkbox)
        
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 20)
        self.backup_count_spin.setValue(5)
        show_layout.addRow("Backup Count:", self.backup_count_spin)
        
        layout.addWidget(show_group)
        
        # Playlist settings
        playlist_group = QGroupBox("Playlist")
        playlist_layout = QFormLayout(playlist_group)
        
        self.shuffle_checkbox = QCheckBox()
        playlist_layout.addRow("Shuffle by Default:", self.shuffle_checkbox)
        
        self.repeat_checkbox = QCheckBox()
        playlist_layout.addRow("Repeat by Default:", self.repeat_checkbox)
        
        self.crossfade_spin = QSpinBox()
        self.crossfade_spin.setRange(0, 10)
        self.crossfade_spin.setValue(2)
        self.crossfade_spin.setSuffix(" seconds")
        playlist_layout.addRow("Crossfade Duration:", self.crossfade_spin)
        
        layout.addWidget(playlist_group)
        
        self.settings_tabs.addTab(show_widget, "Shows")
    
    def create_system_settings(self):
        """Create System settings tab (V2.2)"""
        system_widget = QWidget()
        layout = QVBoxLayout(system_widget)
        
        # Startup settings (Admin only)
        startup_group = QGroupBox("Startup Settings (Administrator Only)")
        startup_layout = QFormLayout(startup_group)
        
        self.start_with_windows_checkbox = QCheckBox()
        self.start_with_windows_checkbox.setChecked(False)
        self.start_with_windows_checkbox.setToolTip(
            "Automatically start DMX Master when Windows starts.\n"
            "Requires Administrator privileges to modify."
        )
        self.start_with_windows_checkbox.setEnabled(self._is_admin())
        self.start_with_windows_checkbox.stateChanged.connect(self.on_start_with_windows_changed)
        startup_layout.addRow("Start with Windows:", self.start_with_windows_checkbox)
        
        if not self._is_admin():
            admin_warning = QLabel("⚠️ Run as Administrator to enable this feature")
            admin_warning.setStyleSheet("color: orange; font-style: italic;")
            startup_layout.addRow("", admin_warning)
        
        layout.addWidget(startup_group)
        
        # Logging settings (Admin only)
        logging_group = QGroupBox("Logging Settings (Administrator Only)")
        logging_layout = QFormLayout(logging_group)
        
        self.enable_logging_checkbox = QCheckBox()
        self.enable_logging_checkbox.setChecked(True)
        self.enable_logging_checkbox.setToolTip("Enable/disable application logging")
        self.enable_logging_checkbox.setEnabled(self._is_admin())
        logging_layout.addRow("Enable Logging:", self.enable_logging_checkbox)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")
        self.log_level_combo.setEnabled(self._is_admin())
        logging_layout.addRow("Log Level:", self.log_level_combo)
        
        if not self._is_admin():
            admin_warning2 = QLabel("⚠️ Run as Administrator to modify logging settings")
            admin_warning2.setStyleSheet("color: orange; font-style: italic;")
            logging_layout.addRow("", admin_warning2)
        
        layout.addWidget(logging_group)
        
        # ArtNet Timecode settings
        timecode_group = QGroupBox("ArtNet Timecode")
        timecode_layout = QFormLayout(timecode_group)
        
        # Enable/Disable timecode broadcasting
        self.artnet_timecode_enabled_checkbox = QCheckBox()
        self.artnet_timecode_enabled_checkbox.setChecked(True)  # Enabled by default
        self.artnet_timecode_enabled_checkbox.setToolTip(
            "Enable sending ArtNet Timecode packets during show playback.\n"
            "Disable this if you don't need to sync external devices."
        )
        timecode_layout.addRow("Send Timecode During Playback:", self.artnet_timecode_enabled_checkbox)
        
        # Timecode format (for future)
        timecode_info = QLabel(
            "When enabled, DMX Master will broadcast ArtNet Timecode (OpCode 0x9700)\n"
            "to all devices on the network during show playback.\n\n"
            "This allows external devices (lighting consoles, media servers, etc.)\n"
            "to synchronize with the show timeline."
        )
        timecode_info.setStyleSheet("color: #666; padding: 10px;")
        timecode_info.setWordWrap(True)
        timecode_layout.addRow("", timecode_info)
        
        layout.addWidget(timecode_group)
        
        # Performance settings
        performance_group = QGroupBox("Performance")
        performance_layout = QFormLayout(performance_group)
        
        self.buffer_size_spin = QSpinBox()
        self.buffer_size_spin.setRange(10, 500)
        self.buffer_size_spin.setValue(100)
        self.buffer_size_spin.setSuffix(" frames")
        self.buffer_size_spin.setToolTip("Buffer size for DMX playback (higher = smoother, more memory)")
        performance_layout.addRow("Playback Buffer:", self.buffer_size_spin)
        
        layout.addWidget(performance_group)
        
        # Add spacer
        layout.addStretch()
        
        self.settings_tabs.addTab(system_widget, "System")
    
    def create_recording_settings(self):
        """Tạo Recording settings"""
        recording_widget = QWidget()
        layout = QVBoxLayout(recording_widget)
        
        # Recording settings
        recording_group = QGroupBox("DMX Recording")
        recording_layout = QFormLayout(recording_group)
        
        recording_path_layout = QHBoxLayout()
        
        # Get actual AppData path for recordings
        if hasattr(self.parent(), 'get_app_data_dir'):
            data_dir = self.parent().get_app_data_dir()
            default_recordings_path = str(data_dir / "recordings")
        else:
            default_recordings_path = "data/recordings"
        
        self.recording_path_edit = QLineEdit(default_recordings_path)
        self.recording_path_edit.setReadOnly(True)  # Read-only to prevent user changes
        self.recording_path_edit.setToolTip("Recordings are stored in AppData for better permissions")
        recording_path_layout.addWidget(self.recording_path_edit)
        
        self.recording_path_button = QPushButton("Browse")
        self.recording_path_button.clicked.connect(self.browse_recording_path)
        recording_path_layout.addWidget(self.recording_path_button)
        
        recording_layout.addRow("Recording Path:", recording_path_layout)
        
        self.auto_trim_checkbox = QCheckBox()
        self.auto_trim_checkbox.setChecked(True)
        recording_layout.addRow("Auto Trim Silence:", self.auto_trim_checkbox)
        
        # Silence threshold slider
        silence_layout = QHBoxLayout()
        self.silence_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.silence_threshold_slider.setRange(-60, 0)
        self.silence_threshold_slider.setValue(-40)
        self.silence_threshold_slider.valueChanged.connect(self.update_silence_label)
        silence_layout.addWidget(self.silence_threshold_slider)
        
        self.silence_threshold_label = QLabel("-40 dB")
        silence_layout.addWidget(self.silence_threshold_label)
        
        recording_layout.addRow("Silence Threshold:", silence_layout)
        
        self.min_silence_spin = QSpinBox()
        self.min_silence_spin.setRange(1, 10)
        self.min_silence_spin.setValue(5)
        self.min_silence_spin.setSuffix(" seconds")
        recording_layout.addRow("Min Silence Duration:", self.min_silence_spin)
        
        layout.addWidget(recording_group)
        
        # Format settings
        format_group = QGroupBox("Recording Format")
        format_layout = QFormLayout(format_group)
        
        self.recording_format_combo = QComboBox()
        self.recording_format_combo.addItems(["JSON", "XML", "Binary"])
        recording_layout.addRow("Data Format:", self.recording_format_combo)
        
        self.compression_checkbox = QCheckBox()
        self.compression_checkbox.setChecked(True)
        format_layout.addRow("Use Compression:", self.compression_checkbox)
        
        layout.addWidget(format_group)
        
        self.settings_tabs.addTab(recording_widget, "Recording")
    
    def create_security_settings(self):
        """Tạo Security settings"""
        security_widget = QWidget()
        layout = QVBoxLayout(security_widget)
        
        # Admin mode
        admin_group = QGroupBox("Administrator Mode")
        admin_layout = QFormLayout(admin_group)
        
        self.admin_mode_checkbox = QCheckBox()
        self.admin_mode_checkbox.toggled.connect(self.on_admin_mode_changed)
        admin_layout.addRow("Enable Admin Mode:", self.admin_mode_checkbox)
        
        self.require_password_checkbox = QCheckBox()
        admin_layout.addRow("Require Password:", self.require_password_checkbox)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        admin_layout.addRow("Admin Password:", self.password_edit)
        
        layout.addWidget(admin_group)
        
        # Access control
        access_group = QGroupBox("Access Control")
        access_layout = QFormLayout(access_group)
        
        self.web_auth_checkbox = QCheckBox()
        access_layout.addRow("Web Server Authentication:", self.web_auth_checkbox)
        
        self.recording_protection_checkbox = QCheckBox()
        self.recording_protection_checkbox.setChecked(True)
        access_layout.addRow("Protect Recording Tab:", self.recording_protection_checkbox)
        
        layout.addWidget(access_group)
        
        self.settings_tabs.addTab(security_widget, "Security")
    
    def create_system_settings(self):
        """Tạo System settings"""
        system_widget = QWidget()
        layout = QVBoxLayout(system_widget)
        
        # Application settings
        app_group = QGroupBox("Application")
        app_layout = QFormLayout(app_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        app_layout.addRow("Theme:", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Tiếng Việt"])
        app_layout.addRow("Language:", self.language_combo)
        
        self.startup_checkbox = QCheckBox()
        app_layout.addRow("Start with Windows:", self.startup_checkbox)
        
        layout.addWidget(app_group)
        
        # Logging settings
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout(logging_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        logging_layout.addRow("Log Level:", self.log_level_combo)
        
        self.log_to_file_checkbox = QCheckBox()
        self.log_to_file_checkbox.setChecked(True)
        logging_layout.addRow("Log to File:", self.log_to_file_checkbox)
        
        self.max_log_size_spin = QSpinBox()
        self.max_log_size_spin.setRange(1, 100)
        self.max_log_size_spin.setValue(10)
        self.max_log_size_spin.setSuffix(" MB")
        logging_layout.addRow("Max Log Size:", self.max_log_size_spin)
        
        layout.addWidget(logging_group)
        
        # Performance settings
        performance_group = QGroupBox("Performance")
        performance_layout = QFormLayout(performance_group)
        
        self.gui_refresh_spin = QSpinBox()
        self.gui_refresh_spin.setRange(10, 60)
        self.gui_refresh_spin.setValue(30)
        self.gui_refresh_spin.setSuffix(" FPS")
        performance_layout.addRow("GUI Refresh Rate:", self.gui_refresh_spin)
        
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(100, 2000)
        self.memory_limit_spin.setValue(512)
        self.memory_limit_spin.setSuffix(" MB")
        performance_layout.addRow("Memory Limit:", self.memory_limit_spin)
        
        layout.addWidget(performance_group)
        
        self.settings_tabs.addTab(system_widget, "System")
    
    def create_buttons(self, parent_layout):
        """Tạo buttons"""
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        self.load_button = QPushButton("Load Settings")
        self.load_button.clicked.connect(self.load_settings)
        button_layout.addWidget(self.load_button)
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)
        
        parent_layout.addLayout(button_layout)
    
    def load_settings(self):
        """Load settings from config"""
        try:
            # Art-Net settings (only if widgets exist)
            if hasattr(self, 'artnet_port_spin'):
                self.artnet_port_spin.setValue(
                    self.config_manager.get_app_config('artnet.port', 6454)
                )
            if hasattr(self, 'universe_spin'):
                self.universe_spin.setValue(
                    self.config_manager.get_app_config('artnet.universe', 0)
                )
            if hasattr(self, 'refresh_rate_spin'):
                self.refresh_rate_spin.setValue(
                    self.config_manager.get_app_config('artnet.refresh_rate', 30)
                )
            if hasattr(self, 'broadcast_edit'):
                self.broadcast_edit.setText(
                    self.config_manager.get_app_config('artnet.broadcast_address', '255.255.255.255')
                )
            if hasattr(self, 'auto_discovery_checkbox'):
                self.auto_discovery_checkbox.setChecked(
                    self.config_manager.get_app_config('artnet.auto_discovery', True)
                )
            
            # Webserver settings (only if widgets exist)
            if hasattr(self, 'webserver_enabled_checkbox'):
                self.webserver_enabled_checkbox.setChecked(
                    self.config_manager.get_app_config('webserver.enabled', True)
                )
            if hasattr(self, 'webserver_port_spin'):
                self.webserver_port_spin.setValue(
                    self.config_manager.get_app_config('webserver.port', 8080)
                )
            if hasattr(self, 'webserver_host_edit'):
                self.webserver_host_edit.setText(
                    self.config_manager.get_app_config('webserver.host', '0.0.0.0')
                )
            if hasattr(self, 'upload_path_edit'):
                self.upload_path_edit.setText(
                    self.config_manager.get_app_config('webserver.upload_path', 'data/music')
                )
            if hasattr(self, 'max_file_size_spin'):
                self.max_file_size_spin.setValue(
                    self.config_manager.get_app_config('webserver.max_file_size', 50)
                )
            
            # Show settings
            if hasattr(self, 'show_path_edit'):
                self.show_path_edit.setText(
                    self.config_manager.get_app_config('show.default_path', 'data/shows')
                )
            if hasattr(self, 'auto_save_checkbox'):
                self.auto_save_checkbox.setChecked(
                    self.config_manager.get_app_config('show.auto_save', True)
                )
            if hasattr(self, 'backup_count_spin'):
                self.backup_count_spin.setValue(
                    self.config_manager.get_app_config('show.backup_count', 5)
                )
            
            # Recording settings (only if widgets exist)
            if hasattr(self, 'recording_path_edit'):
                self.recording_path_edit.setText(
                    self.config_manager.get_app_config('recording.path', 'data/recordings')
                )
            if hasattr(self, 'auto_trim_checkbox'):
                self.auto_trim_checkbox.setChecked(
                    self.config_manager.get_app_config('recording.auto_trim_silence', True)
                )
            if hasattr(self, 'silence_threshold_slider'):
                self.silence_threshold_slider.setValue(
                    self.config_manager.get_app_config('recording.silence_threshold', -40)
                )
            if hasattr(self, 'min_silence_spin'):
                self.min_silence_spin.setValue(
                    int(self.config_manager.get_app_config('recording.min_silence_duration', 0.5))
                )
            
            # Security settings (only if widgets exist)
            if hasattr(self, 'admin_mode_checkbox'):
                self.admin_mode_checkbox.setChecked(
                    self.config_manager.get_app_config('security.admin_mode', False)
                )
            if hasattr(self, 'require_password_checkbox'):
                self.require_password_checkbox.setChecked(
                    self.config_manager.get_app_config('security.require_password', False)
                )
            
            # V2.2: System settings
            if hasattr(self, 'artnet_timecode_enabled_checkbox'):
                self.artnet_timecode_enabled_checkbox.setChecked(
                    self.config_manager.get_app_config('system.artnet_timecode_enabled', True)
                )
            if hasattr(self, 'buffer_size_spin'):
                self.buffer_size_spin.setValue(
                    self.config_manager.get_app_config('system.playback_buffer_size', 100)
                )
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            QMessageBox.warning(self, "Load Error", f"Failed to load settings: {e}")
    
    def save_settings(self):
        """Save settings to config"""
        try:
            # Art-Net settings (only if widgets exist)
            if hasattr(self, 'artnet_port_spin'):
                self.config_manager.set_app_config('artnet.port', self.artnet_port_spin.value())
            if hasattr(self, 'universe_spin'):
                self.config_manager.set_app_config('artnet.universe', self.universe_spin.value())
            if hasattr(self, 'refresh_rate_spin'):
                self.config_manager.set_app_config('artnet.refresh_rate', self.refresh_rate_spin.value())
            if hasattr(self, 'broadcast_edit'):
                self.config_manager.set_app_config('artnet.broadcast_address', self.broadcast_edit.text())
            if hasattr(self, 'auto_discovery_checkbox'):
                self.config_manager.set_app_config('artnet.auto_discovery', self.auto_discovery_checkbox.isChecked())
            
            # Webserver settings (only if widgets exist)
            if hasattr(self, 'webserver_enabled_checkbox'):
                self.config_manager.set_app_config('webserver.enabled', self.webserver_enabled_checkbox.isChecked())
            if hasattr(self, 'webserver_port_spin'):
                self.config_manager.set_app_config('webserver.port', self.webserver_port_spin.value())
            if hasattr(self, 'webserver_host_edit'):
                self.config_manager.set_app_config('webserver.host', self.webserver_host_edit.text())
            if hasattr(self, 'upload_path_edit'):
                self.config_manager.set_app_config('webserver.upload_path', self.upload_path_edit.text())
            if hasattr(self, 'max_file_size_spin'):
                self.config_manager.set_app_config('webserver.max_file_size', self.max_file_size_spin.value())
            
            # Show settings (only if widgets exist)
            if hasattr(self, 'show_path_edit'):
                self.config_manager.set_app_config('show.default_path', self.show_path_edit.text())
            if hasattr(self, 'auto_save_checkbox'):
                self.config_manager.set_app_config('show.auto_save', self.auto_save_checkbox.isChecked())
            if hasattr(self, 'backup_count_spin'):
                self.config_manager.set_app_config('show.backup_count', self.backup_count_spin.value())
            
            # Recording settings (only if widgets exist)
            if hasattr(self, 'recording_path_edit'):
                self.config_manager.set_app_config('recording.path', self.recording_path_edit.text())
            if hasattr(self, 'auto_trim_checkbox'):
                self.config_manager.set_app_config('recording.auto_trim_silence', self.auto_trim_checkbox.isChecked())
            if hasattr(self, 'silence_threshold_slider'):
                self.config_manager.set_app_config('recording.silence_threshold', self.silence_threshold_slider.value())
            if hasattr(self, 'min_silence_spin'):
                self.config_manager.set_app_config('recording.min_silence_duration', self.min_silence_spin.value())
            
            # Security settings (only if widgets exist)
            if hasattr(self, 'admin_mode_checkbox'):
                self.config_manager.set_app_config('security.admin_mode', self.admin_mode_checkbox.isChecked())
            if hasattr(self, 'require_password_checkbox'):
                self.config_manager.set_app_config('security.require_password', self.require_password_checkbox.isChecked())
            
            # V2.2: System settings
            if hasattr(self, 'artnet_timecode_enabled_checkbox'):
                self.config_manager.set_app_config('system.artnet_timecode_enabled', 
                                                   self.artnet_timecode_enabled_checkbox.isChecked())
            if hasattr(self, 'buffer_size_spin'):
                self.config_manager.set_app_config('system.playback_buffer_size', 
                                                   self.buffer_size_spin.value())
            if hasattr(self, 'start_with_windows_checkbox'):
                self.config_manager.set_app_config('system.start_with_windows',
                                                   self.start_with_windows_checkbox.isChecked())
            if hasattr(self, 'enable_logging_checkbox'):
                self.config_manager.set_app_config('system.enable_logging',
                                                   self.enable_logging_checkbox.isChecked())
            if hasattr(self, 'log_level_combo'):
                self.config_manager.set_app_config('system.log_level',
                                                   self.log_level_combo.currentText())
            
            # Save to file
            self.config_manager.save_configs()
            
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save settings: {e}")
    
    def apply_settings(self):
        """Apply settings without saving"""
        self.save_settings()
        self.settings_changed.emit()
    
    def reset_settings(self):
        """Reset to default settings"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset to defaults
            self.artnet_port_spin.setValue(6454)
            self.universe_spin.setValue(0)
            self.refresh_rate_spin.setValue(30)
            self.broadcast_edit.setText("255.255.255.255")
            self.auto_discovery_checkbox.setChecked(True)
            
            self.webserver_enabled_checkbox.setChecked(True)
            self.webserver_port_spin.setValue(8080)
            self.webserver_host_edit.setText("0.0.0.0")
            self.upload_path_edit.setText("data/music")
            self.max_file_size_spin.setValue(50)
            
            self.show_path_edit.setText("data/shows")
            self.auto_save_checkbox.setChecked(True)
            self.backup_count_spin.setValue(5)
            
            self.recording_path_edit.setText("data/recordings")
            self.auto_trim_checkbox.setChecked(True)
            self.silence_threshold_slider.setValue(-40)
            self.min_silence_spin.setValue(5)
            
            self.admin_mode_checkbox.setChecked(False)
            self.require_password_checkbox.setChecked(False)
            self.password_edit.clear()
    
    def browse_upload_path(self):
        """Browse for upload path"""
        path = QFileDialog.getExistingDirectory(self, "Select Upload Directory")
        if path:
            self.upload_path_edit.setText(path)
    
    def browse_show_path(self):
        """Browse for show path"""
        path = QFileDialog.getExistingDirectory(self, "Select Shows Directory")
        if path:
            self.show_path_edit.setText(path)
    
    def browse_recording_path(self):
        """Browse for recording path"""
        path = QFileDialog.getExistingDirectory(self, "Select Recording Directory")
        if path:
            self.recording_path_edit.setText(path)
    
    def update_silence_label(self, value):
        """Update silence threshold label"""
        self.silence_threshold_label.setText(f"{value} dB")
    
    def _is_admin(self):
        """Check if running as Administrator"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def on_start_with_windows_changed(self, state):
        """Handle start with Windows checkbox change"""
        if not self._is_admin():
            QMessageBox.warning(
                self,
                "Administrator Required",
                "⚠️ Administrator privileges required to modify startup settings.\n\n"
                "Please restart the application as Administrator."
            )
            return
        
        enabled = (state == Qt.CheckState.Checked.value)
        
        try:
            import winreg
            import sys
            import os
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "DMXMasterLTS"
            exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
                QMessageBox.information(
                    self,
                    "Startup Enabled",
                    "✅ DMX Master will now start with Windows."
                )
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    QMessageBox.information(
                        self,
                        "Startup Disabled",
                        "⛔ DMX Master will no longer start with Windows."
                    )
                except FileNotFoundError:
                    pass  # Key doesn't exist, already disabled
            
            winreg.CloseKey(key)
            
        except Exception as e:
            logger.error(f"Failed to modify startup setting: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to modify startup setting:\n{e}"
            )
    
    def on_admin_mode_changed(self, enabled):
        """Handle admin mode change"""
        if enabled:
            QMessageBox.information(
                self,
                "Admin Mode",
                "Admin mode enabled. Recording tab will be available after restart."
            )
        else:
            QMessageBox.information(
                self,
                "Admin Mode",
                "Admin mode disabled. Recording tab will be hidden after restart."
            )