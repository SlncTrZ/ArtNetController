"""
Main Window - Cửa sổ chính của ứng dụng
"""

import logging
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, 
                           QHBoxLayout, QWidget, QMenuBar, QStatusBar,
                           QMessageBox, QApplication)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

from .tabs.live_control import LiveControlTab
from .tabs.hardware_manager import HardwareManagerTab
from .tabs.dmx_view import DMXViewTab
from .tabs.settings import SettingsTab
from .tabs.record import RecordTab
from .widgets.status_widget import StatusWidget

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main window của Art-Net Controller"""
    
    # Signals
    artnet_status_changed = pyqtSignal(bool)
    dmx_data_updated = pyqtSignal(int, bytes)  # universe, data
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.artnet_controller = None
        
        self.init_ui()
        self.init_artnet()
        self.init_timers()
        
        logger.info("Main window initialized")
    
    def init_ui(self):
        """Khởi tạo giao diện người dùng"""
        self.setWindowTitle("Art-Net Controller v1.0")
        
        # Set window size from config
        app_config = self.config_manager.get_app_config()
        window_config = app_config.get('window', {})
        
        self.resize(
            window_config.get('width', 1200),
            window_config.get('height', 800)
        )
        self.setMinimumSize(
            window_config.get('min_width', 1000),
            window_config.get('min_height', 600)
        )
        
        # Center window
        self.center_on_screen()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create tab widget
        self.create_tabs()
        
        # Create status bar
        self.create_status_bar()
        
        # Apply dark theme
        self.apply_dark_theme()
    
    def create_menu_bar(self):
        """Tạo menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        new_show_action = QAction('&New Show', self)
        new_show_action.setShortcut('Ctrl+N')
        new_show_action.triggered.connect(self.new_show)
        file_menu.addAction(new_show_action)
        
        open_show_action = QAction('&Open Show', self)
        open_show_action.setShortcut('Ctrl+O')
        open_show_action.triggered.connect(self.open_show)
        file_menu.addAction(open_show_action)
        
        save_show_action = QAction('&Save Show', self)
        save_show_action.setShortcut('Ctrl+S')
        save_show_action.triggered.connect(self.save_show)
        file_menu.addAction(save_show_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Art-Net menu
        artnet_menu = menubar.addMenu('&Art-Net')
        
        start_artnet_action = QAction('&Start Art-Net', self)
        start_artnet_action.triggered.connect(self.start_artnet)
        artnet_menu.addAction(start_artnet_action)
        
        stop_artnet_action = QAction('St&op Art-Net', self)
        stop_artnet_action.triggered.connect(self.stop_artnet)
        artnet_menu.addAction(stop_artnet_action)
        
        artnet_menu.addSeparator()
        
        scan_network_action = QAction('&Scan Network', self)
        scan_network_action.triggered.connect(self.scan_network)
        artnet_menu.addAction(scan_network_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        webserver_action = QAction('Start &Web Server', self)
        webserver_action.triggered.connect(self.toggle_webserver)
        tools_menu.addAction(webserver_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_tabs(self):
        """Tạo tab widget và các tab"""
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # Live Control tab
        self.live_control_tab = LiveControlTab(self.config_manager)
        self.tab_widget.addTab(self.live_control_tab, "Live Control")
        
        # Hardware Manager tab
        self.hardware_manager_tab = HardwareManagerTab(self.config_manager)
        self.tab_widget.addTab(self.hardware_manager_tab, "Hardware Manager")
        
        # DMX View tab
        self.dmx_view_tab = DMXViewTab(self.config_manager)
        self.tab_widget.addTab(self.dmx_view_tab, "DMX View")
        
        # Settings tab
        self.settings_tab = SettingsTab(self.config_manager)
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Record tab (admin only)
        if self.config_manager.get_app_config('security.admin_mode', False):
            self.record_tab = RecordTab(self.config_manager)
            self.tab_widget.addTab(self.record_tab, "Record")
        
        # Connect tab signals
        self.connect_tab_signals()
    
    def create_status_bar(self):
        """Tạo status bar"""
        self.status_bar = self.statusBar()
        
        # Status widget
        self.status_widget = StatusWidget()
        self.status_bar.addPermanentWidget(self.status_widget)
        
        # Initial status
        self.status_bar.showMessage("Ready")
        self.status_widget.set_artnet_status(False)
    
    def connect_tab_signals(self):
        """Kết nối signals giữa các tab"""
        # Live Control -> DMX View
        self.live_control_tab.dmx_changed.connect(self.dmx_view_tab.update_dmx_data)
        
        # Hardware Manager -> Live Control
        self.hardware_manager_tab.device_selected.connect(
            self.live_control_tab.set_selected_device
        )
        
        # Settings -> All tabs
        self.settings_tab.settings_changed.connect(self.apply_settings)
    
    def init_artnet(self):
        """Khởi tạo Art-Net controller"""
        from artnet import ArtNetController
        from show import ShowManager
        from webserver import MP3UploadServer
        
        artnet_config = self.config_manager.get_app_config('artnet', {})
        
        self.artnet_controller = ArtNetController(
            port=artnet_config.get('port', 6454)
        )
        
        # Set callbacks
        self.artnet_controller.set_dmx_received_callback(self.on_dmx_received)
        self.artnet_controller.set_node_discovered_callback(self.on_node_discovered)
        
        # Initialize show manager
        self.show_manager = ShowManager(
            self.config_manager.get_app_config('show.default_path', 'data/shows')
        )
        
        # Initialize webserver
        self.webserver = MP3UploadServer(self.config_manager, self.show_manager)
        
        # Auto start if enabled
        if artnet_config.get('auto_start', True):
            self.start_artnet()
        
        # Auto start webserver if enabled
        if self.config_manager.get_app_config('webserver.enabled', True):
            self.start_webserver()
    
    def init_timers(self):
        """Khởi tạo timers"""
        # DMX update timer
        self.dmx_timer = QTimer()
        self.dmx_timer.timeout.connect(self.update_dmx_output)
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update every second
        
        # Network cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_network)
        self.cleanup_timer.start(30000)  # Cleanup every 30 seconds
    
    def center_on_screen(self):
        """Center window trên màn hình"""
        screen = QApplication.primaryScreen().geometry()
        window = self.geometry()
        
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        
        self.move(x, y)
    
    def apply_dark_theme(self):
        """Apply dark theme cho ứng dụng"""
        dark_stylesheet = """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #3c3c3c;
        }
        
        QTabBar::tab {
            background-color: #2b2b2b;
            color: #ffffff;
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid #555555;
        }
        
        QTabBar::tab:selected {
            background-color: #0078d4;
        }
        
        QTabBar::tab:hover {
            background-color: #404040;
        }
        
        QMenuBar {
            background-color: #2b2b2b;
            color: #ffffff;
            border-bottom: 1px solid #555555;
        }
        
        QMenuBar::item:selected {
            background-color: #0078d4;
        }
        
        QMenu {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
        }
        
        QMenu::item:selected {
            background-color: #0078d4;
        }
        
        QStatusBar {
            background-color: #2b2b2b;
            color: #ffffff;
            border-top: 1px solid #555555;
        }
        """
        
        self.setStyleSheet(dark_stylesheet)
    
    # Art-Net methods
    def start_artnet(self):
        """Khởi động Art-Net"""
        if self.artnet_controller and self.artnet_controller.start():
            self.artnet_status_changed.emit(True)
            self.status_widget.set_artnet_status(True)
            self.status_bar.showMessage(\"Art-Net started\")
            
            # Start DMX timer
            refresh_rate = self.config_manager.get_app_config('artnet.refresh_rate', 30)
            self.dmx_timer.start(1000 // refresh_rate)  # Convert Hz to ms
            
            logger.info(\"Art-Net started successfully\")
        else:
            self.status_bar.showMessage(\"Failed to start Art-Net\")
            logger.error(\"Failed to start Art-Net\")
    
    def stop_artnet(self):
        """Dừng Art-Net"""
        if self.artnet_controller:
            self.artnet_controller.stop()
            self.artnet_status_changed.emit(False)
            self.status_widget.set_artnet_status(False)
            self.status_bar.showMessage(\"Art-Net stopped\")
            
            # Stop DMX timer
            self.dmx_timer.stop()
            
            logger.info(\"Art-Net stopped\")
    
    def scan_network(self):
        """Scan network cho Art-Net nodes"""
        if self.artnet_controller:
            self.artnet_controller.poll_network()
            self.status_bar.showMessage(\"Scanning network...\")
            logger.info(\"Network scan initiated\")
    
    def on_dmx_received(self, universe: int, dmx_data: bytes, source_ip: str):
        """Callback khi nhận DMX data"""
        self.dmx_data_updated.emit(universe, dmx_data)
        
        # Update tabs
        self.dmx_view_tab.update_received_dmx(universe, dmx_data, source_ip)
        
        # Record if enabled
        if hasattr(self, 'record_tab') and self.record_tab.is_recording():
            self.record_tab.record_dmx_data(universe, dmx_data)
    
    def on_node_discovered(self, node):
        """Callback khi discover Art-Net node"""
        self.hardware_manager_tab.add_discovered_node(node)
        logger.info(f\"Discovered Art-Net node: {node.ip_address}\")
    
    def update_dmx_output(self):
        """Update DMX output từ Live Control"""
        if self.artnet_controller and self.artnet_controller.running:
            # Get DMX data from Live Control tab
            universe, dmx_data = self.live_control_tab.get_dmx_output()
            
            if dmx_data:
                self.artnet_controller.send_dmx(universe, dmx_data)
                self.dmx_data_updated.emit(universe, dmx_data)
    
    def update_status(self):
        """Update status bar và widgets"""
        if self.artnet_controller:
            # Update node count
            nodes = self.artnet_controller.get_discovered_nodes()
            self.status_widget.set_node_count(len(nodes))
            
            # Update universe info
            universes = list(self.artnet_controller.dmx_universe_data.keys())
            if universes:
                self.status_widget.set_active_universes(universes)
    
    def cleanup_network(self):
        """Cleanup old Art-Net nodes"""
        if self.artnet_controller:
            self.artnet_controller.cleanup_old_nodes()
    
    # Menu actions
    def new_show(self):
        """Tạo show mới"""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, 'New Show', 'Enter show name:')
        if ok and name.strip():
            show = self.show_manager.create_new_show(name.strip())
            if show:
                self.status_bar.showMessage(f"New show created: {name}")
                logger.info(f"New show created: {name}")
            else:
                self.status_bar.showMessage("Failed to create show")
    
    def open_show(self):
        """Mở show"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Show",
            str(Path(self.config_manager.get_app_config('show.default_path', 'data/shows'))),
            "Show Files (*.json *.xml);;JSON Files (*.json);;XML Files (*.xml);;All Files (*)"
        )
        
        if file_path:
            show = self.show_manager.load_show(file_path)
            if show:
                self.status_bar.showMessage(f"Show opened: {show.metadata.name}")
                logger.info(f"Show opened: {file_path}")
            else:
                self.status_bar.showMessage("Failed to open show")
    
    def save_show(self):
        """Lưu show"""
        if self.show_manager.current_show:
            if self.show_manager.save_show(self.show_manager.current_show):
                self.status_bar.showMessage(f"Show saved: {self.show_manager.current_show.metadata.name}")
            else:
                self.status_bar.showMessage("Failed to save show")
        else:
            self.status_bar.showMessage("No show to save")
    
    def toggle_webserver(self):
        """Toggle web server"""
        if hasattr(self, 'webserver'):
            if self.webserver.is_running:
                self.webserver.stop_server()
                self.status_bar.showMessage("Web server stopped")
            else:
                if self.webserver.start_server():
                    url = self.webserver.get_server_url()
                    self.status_bar.showMessage(f"Web server started: {url}")
                else:
                    self.status_bar.showMessage("Failed to start web server")
        else:
            self.status_bar.showMessage("Web server not available")
    
    def start_webserver(self):
        """Start web server"""
        if hasattr(self, 'webserver') and not self.webserver.is_running:
            if self.webserver.start_server():
                url = self.webserver.get_server_url()
                logger.info(f"Web server started: {url}")
                return True
        return False
    
    def apply_settings(self):
        """Apply settings changes"""
        self.config_manager.save_configs()
        self.status_bar.showMessage(\"Settings applied\")
    
    def show_about(self):
        """Hiển thị About dialog"""
        QMessageBox.about(
            self,
            \"About Art-Net Controller\",
            \"\"\"<h2>Art-Net Controller v1.0</h2>
            <p>Phần mềm điều khiển Art-Net chuyên nghiệp</p>
            <p>Hỗ trợ Windows và Raspberry Pi</p>
            <p><b>Tính năng:</b></p>
            <ul>
            <li>Live DMX Control</li>
            <li>Hardware Management</li>
            <li>DMX Visualization</li>
            <li>Show Recording & Playback</li>
            <li>Web-based MP3 Upload</li>
            </ul>
            <p>Developed with PyQt6 and Art-Net 4 protocol</p>\"\"\"
        )
    
    def closeEvent(self, event):
        """Handle close event"""
        # Stop Art-Net
        self.stop_artnet()
        
        # Stop webserver
        if hasattr(self, 'webserver') and self.webserver.is_running:
            self.webserver.stop_server()
        
        # Save current show if exists
        if hasattr(self, 'show_manager') and self.show_manager.current_show:
            if self.config_manager.get_app_config('show.auto_save', True):
                self.show_manager.save_show(self.show_manager.current_show)
        
        # Save window geometry
        window_config = {
            'width': self.width(),
            'height': self.height()
        }
        self.config_manager.set_app_config('window', window_config)
        self.config_manager.save_configs()
        
        logger.info("Application closing")
        event.accept()