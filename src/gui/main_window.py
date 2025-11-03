"""
Main Window cho Art-Net Controller
PyQt6 GUI với 5 tabs chính và tích hợp Art-Net controller
"""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QTabWidget, QMenuBar, QMenu, QStatusBar, QLabel,
    QMessageBox, QApplication, QInputDialog, QLineEdit, QDialog
)
from PyQt6.QtCore import QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QKeySequence
import hashlib

# Import tabs
from gui.tabs.show_manager import ShowManagerTab
from gui.tabs.hardware_manager import HardwareManagerTab  
from gui.tabs.dmx_view import DMXViewTab
from gui.tabs.settings import SettingsTab
from gui.tabs.record import RecordTab

# Import components
from gui.widgets.status_widget import StatusWidget
from gui.widgets.ip_info_widget import IPInfoWidget
from artnet.controller import ArtNetController
from webserver.server import MP3UploadServer
from show.manager import ShowManager
from utils.config import ConfigManager

# Import version info
try:
    from version import __version__, __build__, __author__, __github_repo__, __update_url__
except ImportError:
    __version__ = "1.0.0"
    __build__ = "Unknown"
    __author__ = "Unknown"
    __github_repo__ = "https://github.com"
    __update_url__ = ""

# Import license manager
from utils.license import LicenseManager
from gui.dialogs.license_dialog import LicenseDialog

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals
    artnet_status_changed = pyqtSignal(bool)
    dmx_data_updated = pyqtSignal(int, bytes)  # universe, data
    node_discovered = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.show_manager = ShowManager()
        self.artnet_controller = None
        self.webserver = None
        
        # License manager
        self.license_manager = LicenseManager()
        
        # Admin authentication
        self._is_admin = False
        self._init_admin_password()
        
        # Check license before starting
        if not self._check_license():
            return
        
        # Setup UI
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.apply_dark_theme()
        
        # Initialize components
        self.init_artnet_controller()
        self.init_webserver()
        
        # Setup timers first
        self.setup_timers()
        
        # Setup IP monitoring
        self.setup_ip_monitoring()
        
        # Auto-start Art-Net after timers are ready
        self.start_artnet()
        
        # Load và apply universe mapping từ Hardware Manager
        self.load_universe_mapping()
        
        # Center window
        self.center_on_screen()
        
        logger.info("Main window initialized")
    
    def setup_ui(self):
        """Setup main UI structure"""
        self.setWindowTitle(f"Art-Net Controller v{__version__}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_tabs()
        
    def create_tabs(self):
        """Create all tabs"""
        # Show Manager Tab (formerly Live Control)
        self.show_manager_tab = ShowManagerTab(self.config_manager)
        self.show_manager_tab.dmx_changed.connect(self.update_dmx_output)
        self.tab_widget.addTab(self.show_manager_tab, "Show Manager")
        
        # Hardware Manager Tab
        self.hardware_manager_tab = HardwareManagerTab(self.config_manager)
        self.hardware_manager_tab.universe_mapping_changed.connect(self.on_universe_mapping_changed)
        self.tab_widget.addTab(self.hardware_manager_tab, "Hardware Manager")
        
        # DMX View Tab
        self.dmx_view_tab = DMXViewTab(self.config_manager)
        self.tab_widget.addTab(self.dmx_view_tab, "DMX View")
        
        # Settings Tab
        self.settings_tab = SettingsTab(self.config_manager)
        self.settings_tab.settings_changed.connect(self.apply_settings)
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Record Tab
        self.record_tab = RecordTab(self.config_manager)
        self.tab_widget.addTab(self.record_tab, "Record")
    
    def setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        self.edit_project_action = QAction("Edit &Project Name", self)
        self.edit_project_action.setShortcut(QKeySequence("Ctrl+P"))
        self.edit_project_action.triggered.connect(self.edit_project_name)
        self.edit_project_action.setEnabled(False)  # Enabled only when admin
        file_menu.addAction(self.edit_project_action)
        
        # Setting menu
        setting_menu = menubar.addMenu("&Setting")
        
        # Art-Net submenu
        artnet_submenu = setting_menu.addMenu("&Art-Net")
        
        start_action = QAction("&Start Art-Net", self)
        start_action.setShortcut(QKeySequence("Ctrl+S"))
        start_action.triggered.connect(self.start_artnet)
        artnet_submenu.addAction(start_action)
        
        stop_action = QAction("St&op Art-Net", self)
        stop_action.setShortcut(QKeySequence("Ctrl+T"))
        stop_action.triggered.connect(self.stop_artnet)
        artnet_submenu.addAction(stop_action)
        
        scan_action = QAction("&Scan Network", self)
        scan_action.setShortcut(QKeySequence("Ctrl+N"))
        scan_action.triggered.connect(self.scan_network)
        artnet_submenu.addAction(scan_action)
        
        # Display & Appearance submenu
        display_submenu = setting_menu.addMenu("&Display && Appearance")
        
        # Timezone submenu (dropdown list)
        timezone_submenu = display_submenu.addMenu("&Timezone")
        self.timezone_actions = []
        timezones = ['UTC', 'Asia/Ho_Chi_Minh', 'Asia/Bangkok', 'Europe/London', 'America/New_York']
        for tz in timezones:
            tz_action = QAction(tz, self, checkable=True)
            tz_action.triggered.connect(lambda checked, t=tz: self.set_timezone(t))
            timezone_submenu.addAction(tz_action)
            self.timezone_actions.append(tz_action)
        
        # Set current timezone checked
        current_tz = self.config_manager.get_app_config('ui.timezone', 'UTC') if self.config_manager else 'UTC'
        for action in self.timezone_actions:
            if action.text() == current_tz:
                action.setChecked(True)
                break
        
        ntp_sync_action = QAction("&Sync Time (NTP)", self)
        ntp_sync_action.triggered.connect(self.sync_ntp_time)
        display_submenu.addAction(ntp_sync_action)
        
        background_action = QAction("Change &Background", self)
        background_action.triggered.connect(self.change_background)
        display_submenu.addAction(background_action)
        
        # Theme submenu (dropdown list)
        theme_submenu = display_submenu.addMenu("T&heme")
        self.theme_actions = []
        themes = ['Dark', 'Light', 'System']
        for theme in themes:
            theme_action = QAction(theme, self, checkable=True)
            theme_action.triggered.connect(lambda checked, t=theme: self.set_theme(t))
            theme_submenu.addAction(theme_action)
            self.theme_actions.append(theme_action)
        
        # Set Dark as default
        self.theme_actions[0].setChecked(True)
        
        # Webserver submenu
        webserver_submenu = setting_menu.addMenu("&Web Server")
        
        self.webserver_enabled_action = QAction("&Enable Web Server", self, checkable=True)
        self.webserver_enabled_action.setChecked(True)
        self.webserver_enabled_action.triggered.connect(self.toggle_webserver)
        webserver_submenu.addAction(self.webserver_enabled_action)
        
        webserver_submenu.addSeparator()
        
        webserver_settings_action = QAction("Web Server &Settings...", self)
        webserver_settings_action.triggered.connect(self.show_webserver_settings)
        webserver_submenu.addAction(webserver_settings_action)
        
        # Recording submenu
        recording_submenu = setting_menu.addMenu("&Recording")
        
        recording_settings_action = QAction("Recording &Settings...", self)
        recording_settings_action.triggered.connect(self.show_recording_settings)
        recording_submenu.addAction(recording_settings_action)
        
        # System submenu
        system_submenu = setting_menu.addMenu("S&ystem")
        
        # Language submenu
        language_submenu = system_submenu.addMenu("&Language")
        self.language_actions = []
        languages = [('English', 'en'), ('Tiếng Việt', 'vi')]
        for lang_name, lang_code in languages:
            lang_action = QAction(lang_name, self, checkable=True)
            lang_action.triggered.connect(lambda checked, code=lang_code: self.set_language(code))
            language_submenu.addAction(lang_action)
            self.language_actions.append(lang_action)
        
        # Set English as default
        self.language_actions[0].setChecked(True)
        
        system_submenu.addSeparator()
        
        system_settings_action = QAction("System &Settings...", self)
        system_settings_action.triggered.connect(self.show_system_settings)
        system_submenu.addAction(system_settings_action)
        
        setting_menu.addSeparator()
        
        # Admin section
        setting_menu.addSection("Admin")
        
        self.login_action = QAction("&Login as Admin", self)
        self.login_action.setShortcut(QKeySequence("Ctrl+A"))
        self.login_action.triggered.connect(self.admin_login)
        setting_menu.addAction(self.login_action)
        
        self.logout_action = QAction("&Logout", self)
        self.logout_action.triggered.connect(self.admin_logout)
        self.logout_action.setEnabled(False)
        setting_menu.addAction(self.logout_action)
        
        self.change_password_action = QAction("Change &Password", self)
        self.change_password_action.triggered.connect(self.change_admin_password)
        self.change_password_action.setEnabled(False)
        setting_menu.addAction(self.change_password_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        license_action = QAction("📝 &License Activation...", self)
        license_action.triggered.connect(self.show_license_dialog)
        help_menu.addAction(license_action)
        
        help_menu.addSeparator()
        
        check_update_action = QAction("Check for &Updates...", self)
        check_update_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(check_update_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        help_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        help_menu.addAction(exit_action)
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = self.statusBar()
        
        # Status widget
        self.status_widget = StatusWidget()
        self.status_bar.addPermanentWidget(self.status_widget)
        
        self.status_bar.showMessage("Ready")
    
    def init_artnet_controller(self):
        """Initialize Art-Net controller"""
        try:
            self.artnet_controller = ArtNetController()
            
            # Set callbacks
            self.artnet_controller.dmx_received_callback = self.on_dmx_received
            self.artnet_controller.node_discovered_callback = self.on_node_discovered
            
            logger.info("Art-Net controller initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Art-Net controller: {e}")
            QMessageBox.warning(self, "Warning", f"Failed to initialize Art-Net controller: {e}")
    
    def init_webserver(self):
        """Initialize webserver"""
        try:
            self.webserver = MP3UploadServer(self.config_manager, self.show_manager)
            
            # Start webserver in background
            self.webserver.start_server()
            logger.info("Webserver initialized and started")
        except Exception as e:
            logger.error(f"Failed to initialize webserver: {e}")
            QMessageBox.warning(self, "Warning", f"Failed to initialize webserver: {e}")
    
    def setup_ip_monitoring(self):
        """Setup IP monitoring"""
        from utils.network import get_primary_ip
        
        # Update initial IP
        try:
            ip = get_primary_ip()
            self.status_widget.set_ip_address(ip)
            logger.info(f"Initial IP address: {ip}")
        except Exception as e:
            logger.warning(f"Could not get initial IP: {e}")
    
    def setup_timers(self):
        """Setup timers"""
        # DMX output timer
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
        """Center window on screen"""
        screen = QApplication.primaryScreen().geometry()
        window = self.geometry()
        
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        self.move(x, y)
    
    def apply_dark_theme(self):
        """Apply dark theme"""
        dark_stylesheet = """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QWidget {
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
        """Start Art-Net"""
        if self.artnet_controller and self.artnet_controller.start():
            self.artnet_status_changed.emit(True)
            self.status_widget.set_artnet_status(True)
            self.status_bar.showMessage("Art-Net started")
            
            # Start DMX timer
            refresh_rate = self.config_manager.get_app_config('artnet.refresh_rate', 30)
            self.dmx_timer.start(1000 // refresh_rate)  # Convert Hz to ms
            
            logger.info("Art-Net started successfully")
        else:
            self.status_bar.showMessage("Failed to start Art-Net")
            logger.error("Failed to start Art-Net")
    
    def stop_artnet(self):
        """Stop Art-Net"""
        if self.artnet_controller:
            self.artnet_controller.stop()
            self.artnet_status_changed.emit(False)
            self.status_widget.set_artnet_status(False)
            self.status_bar.showMessage("Art-Net stopped")
            
            # Stop DMX timer
            self.dmx_timer.stop()
            
            logger.info("Art-Net stopped")
    
    def scan_network(self):
        """Scan network for Art-Net nodes"""
        if self.artnet_controller:
            self.artnet_controller.poll_network()
            self.status_bar.showMessage("Scanning network...")
            logger.info("Network scan initiated")
    
    def on_dmx_received(self, universe: int, dmx_data: bytes, source_ip: str):
        """Callback when DMX data received"""
        self.dmx_data_updated.emit(universe, dmx_data)
        
        # Update tabs
        self.dmx_view_tab.update_received_dmx(universe, dmx_data, source_ip)
        
        # Record if enabled
        if hasattr(self, 'record_tab') and self.record_tab.is_recording():
            self.record_tab.record_dmx_data(universe, dmx_data)
    
    def on_node_discovered(self, node):
        """Callback when Art-Net node discovered"""
        self.hardware_manager_tab.add_discovered_node(node)
        logger.info(f"Discovered Art-Net node: {node.ip_address}")
    
    def on_universe_mapping_changed(self, mapping: dict):
        """Callback when universe mapping changed in Hardware Manager"""
        if self.artnet_controller:
            self.artnet_controller.set_universe_mapping(mapping)
            logger.info(f"Universe mapping updated from Hardware Manager: {len(mapping)} nodes configured")
    
    def load_universe_mapping(self):
        """Load universe mapping from config at startup"""
        if self.artnet_controller:
            mapping = self.hardware_manager_tab.get_universe_mapping()
            self.artnet_controller.set_universe_mapping(mapping)
            logger.info(f"Universe mapping loaded from config: {len(mapping)} nodes configured")
    
    def update_universe_mapping(self):
        """Update universe mapping from Hardware Manager to ArtNet Controller"""
        if self.artnet_controller:
            mapping = self.hardware_manager_tab.get_universe_mapping()
            self.artnet_controller.set_universe_mapping(mapping)
            logger.info(f"Universe mapping updated: {mapping}")
    
    def update_dmx_output(self, universe: int | None = None, dmx_data: bytes | None = None):
        """Send DMX frames to Art-Net.

        Can be called in two ways:
        - From Show Manager signal: with (universe, dmx_data)
        - From QTimer tick: without args (ignored)
        """
        # Ignore timer-driven calls without args for now
        if universe is None or dmx_data is None:
            return

        if self.artnet_controller and self.artnet_controller.running:
            if dmx_data:
                # Sử dụng send_dmx_with_mapping để gửi theo cấu hình
                self.artnet_controller.send_dmx_with_mapping(universe, dmx_data)
                self.dmx_data_updated.emit(universe, dmx_data)
    
    def update_status(self):
        """Update status bar and widgets"""
        if self.artnet_controller:
            # Update node count
            nodes = self.artnet_controller.get_discovered_nodes()
            self.status_widget.set_node_count(len(nodes))
            
            # Update universe info
            universes = list(self.artnet_controller.dmx_universe_data.keys())
            self.status_widget.set_active_universes(universes)
        
        # Update IP address
        try:
            from utils.network import get_primary_ip
            ip = get_primary_ip()
            self.status_widget.set_ip_address(ip)
        except Exception as e:
            logger.warning(f"Could not update IP: {e}")
    
    def cleanup_network(self):
        """Cleanup old Art-Net nodes"""
        if self.artnet_controller:
            self.artnet_controller.cleanup_old_nodes()
    
    def apply_settings(self):
        """Apply settings changes"""
        self.config_manager.save_configs()
        self.status_bar.showMessage("Settings applied")
    
    def show_about(self):
        """Show About dialog"""
        about_text = f"""
        <h2>Art-Net Controller</h2>
        <p><b>Version:</b> {__version__}<br>
        <b>Build:</b> {__build__}<br>
        <b>Author:</b> {__author__}</p>
        
        <p><b>Professional Art-Net DMX Controller</b></p>
        
        <p>Tính năng chính:</p>
        <ul>
        <li>✨ Show Manager với Spotify-style player</li>
        <li>🎛️ Live DMX control với faders</li>
        <li>🌐 Art-Net node discovery và universe mapping</li>
        <li>📊 DMX data visualization</li>
        <li>🎵 Show recording và playback</li>
        <li>☁️ MP3 upload webserver</li>
        <li>🔐 Admin authentication system</li>
        <li>🌍 Multi-timezone support</li>
        <li>💻 Cross-platform (Windows/Linux/Mac)</li>
        </ul>
        
        <p><b>Technology Stack:</b><br>
        PyQt6, Art-Net 4 Protocol, Flask, Python 3.11+</p>
        
        <p><b>GitHub:</b> <a href="{__github_repo}">{__github_repo}</a></p>
        
        <p>© 2025 {__author__}. All rights reserved.</p>
        """
        
        QMessageBox.about(self, "About Art-Net Controller", about_text)
    
    def check_for_updates(self):
        """Check for updates from GitHub"""
        from PyQt6.QtWidgets import QProgressDialog
        from PyQt6.QtCore import Qt
        import urllib.request
        import json
        
        # Show progress dialog
        progress = QProgressDialog("Checking for updates...", "Cancel", 0, 0, self)
        progress.setWindowTitle("Update Check")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        try:
            # Fetch latest release info from GitHub API
            if not __update_url__:
                QMessageBox.warning(self, "Update Check", "Update URL not configured.")
                return
            
            QApplication.processEvents()
            
            req = urllib.request.Request(__update_url__)
            req.add_header('User-Agent', f'ArtNetController/{__version__}')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            progress.close()
            
            # Parse version info
            latest_version = data.get('tag_name', '').lstrip('v')
            release_name = data.get('name', 'Unknown')
            release_url = data.get('html_url', __github_repo__)
            release_notes = data.get('body', 'No release notes available.')
            published_at = data.get('published_at', 'Unknown')
            
            # Compare versions
            current_parts = __version__.split('.')
            latest_parts = latest_version.split('.')
            
            is_newer = False
            try:
                for i in range(max(len(current_parts), len(latest_parts))):
                    current = int(current_parts[i]) if i < len(current_parts) else 0
                    latest = int(latest_parts[i]) if i < len(latest_parts) else 0
                    if latest > current:
                        is_newer = True
                        break
                    elif latest < current:
                        break
            except ValueError:
                # Can't parse version numbers
                is_newer = latest_version != __version__
            
            # Show result
            if is_newer:
                msg = f"""
                <h3>🎉 New Version Available!</h3>
                
                <p><b>Current Version:</b> {__version__}<br>
                <b>Latest Version:</b> {latest_version}<br>
                <b>Release Name:</b> {release_name}<br>
                <b>Published:</b> {published_at}</p>
                
                <p><b>Release Notes:</b></p>
                <p>{release_notes[:500]}...</p>
                
                <p><b>Download:</b> <a href="{release_url}">{release_url}</a></p>
                
                <p>Would you like to open the download page?</p>
                """
                
                reply = QMessageBox.question(
                    self,
                    "Update Available",
                    msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    import webbrowser
                    webbrowser.open(release_url)
            else:
                QMessageBox.information(
                    self,
                    "No Updates",
                    f"""<h3>✅ You're up to date!</h3>
                    
                    <p><b>Current Version:</b> {__version__}<br>
                    <b>Latest Version:</b> {latest_version}</p>
                    
                    <p>You are running the latest version of Art-Net Controller.</p>"""
                )
            
            logger.info(f"Update check completed. Current: {__version__}, Latest: {latest_version}")
            
        except urllib.error.HTTPError as e:
            progress.close()
            if e.code == 404:
                QMessageBox.warning(
                    self,
                    "Update Check Failed",
                    "No releases found on GitHub.\n\nThis might be a development version."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Update Check Failed",
                    f"HTTP Error {e.code}: {e.reason}\n\nPlease try again later."
                )
            logger.warning(f"Update check failed: HTTP {e.code}")
            
        except urllib.error.URLError as e:
            progress.close()
            QMessageBox.warning(
                self,
                "Update Check Failed",
                f"Network error: {e.reason}\n\nPlease check your internet connection."
            )
            logger.warning(f"Update check failed: {e.reason}")
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Update Check Failed",
                f"An unexpected error occurred:\n\n{str(e)}"
            )
            logger.error(f"Update check failed: {e}", exc_info=True)
    
    def closeEvent(self, event):
        """Handle application close"""
        # Stop Art-Net
        if self.artnet_controller:
            self.artnet_controller.stop()
        
        # Stop webserver
        if self.webserver:
            self.webserver.stop_server()
        
        # Save configuration
        self.config_manager.save_configs()
        
        logger.info("Application closed")
        event.accept()
    
    def set_admin_mode(self, is_admin: bool):
        """Set admin mode for Show Manager"""
        self._is_admin = is_admin
        self.show_manager_tab.set_admin_mode(is_admin)
        
        # Update Record tab admin mode too
        self.record_tab.set_admin_mode(is_admin)
        
        # Update menu actions
        self.login_action.setEnabled(not is_admin)
        self.logout_action.setEnabled(is_admin)
        self.change_password_action.setEnabled(is_admin)
        self.edit_project_action.setEnabled(is_admin)
    
    def _init_admin_password(self):
        """Initialize admin password from config or set default"""
        # Get stored password hash
        stored_hash = self.config_manager.get_app_config('admin.password_hash', None)
        
        if stored_hash is None:
            # Set default password: CC03@DinhTC
            default_password = "CC03@DinhTC"
            password_hash = self._hash_password(default_password)
            self.config_manager.set_app_config('admin.password_hash', password_hash)
            self.config_manager.save_configs()
            logger.info("Default admin password set")
    
    def _check_license(self) -> bool:
        """
        Check license validity on startup
        Returns False if should exit application
        """
        is_valid, message = self.license_manager.is_valid()
        
        if is_valid:
            logger.info(f"License valid: {message}")
            return True
        else:
            # License invalid or trial expired
            info = self.license_manager.get_license_info()
            
            if info['type'] == 'trial' and info.get('days_remaining', 0) <= 0:
                # Trial expired
                msg = f"""
                <h2>⚠️ Trial Period Expired</h2>
                
                <p>Your 7-day trial period has ended.</p>
                
                <p>To continue using Art-Net Controller, please purchase a license key.</p>
                
                <p><b>Features include:</b></p>
                <ul>
                <li>✨ Unlimited show playback</li>
                <li>🌐 Art-Net universe mapping</li>
                <li>🎛️ Live DMX control</li>
                <li>📊 Advanced visualization</li>
                <li>🔐 Admin features</li>
                </ul>
                
                <p>Would you like to activate a license now?</p>
                """
                
                reply = QMessageBox.question(
                    None,
                    "Trial Expired - Art-Net Controller",
                    msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Show license dialog before main window
                    dialog = LicenseDialog(self.license_manager, None)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        # Check if activated
                        is_valid, _ = self.license_manager.is_valid()
                        if is_valid:
                            QMessageBox.information(None, "Success", "License activated! Starting application...")
                            return True
                
                # Still not activated - exit
                QMessageBox.warning(
                    None,
                    "Application Closed",
                    "Application will now close.\n\nPlease activate a license to continue using Art-Net Controller."
                )
                return False
            else:
                # Trial still valid - show warning
                days_remaining = info.get('days_remaining', 0)
                logger.info(f"Running in trial mode: {days_remaining} days remaining")
                
                # Show trial notice (non-blocking)
                QTimer.singleShot(2000, lambda: self._show_trial_notice(days_remaining))
                return True
    
    def _show_trial_notice(self, days_remaining: int):
        """Show trial notice after main window loads"""
        msg = f"""
        <h3>📅 Trial Version</h3>
        
        <p>You are using the trial version of Art-Net Controller.</p>
        
        <p><b>Days Remaining:</b> {days_remaining}</p>
        
        <p>To unlock all features permanently, please activate a license key.</p>
        
        <p>Click "License Activation" in the Help menu to activate.</p>
        """
        
        QMessageBox.information(self, "Trial Version", msg)
    
    def show_license_dialog(self):
        """Show license activation dialog"""
        dialog = LicenseDialog(self.license_manager, self)
        dialog.exec()
        
        # Check if license status changed
        is_valid, message = self.license_manager.is_valid()
        logger.info(f"License status after dialog: {message}")
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def _verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        stored_hash = self.config_manager.get_app_config('admin.password_hash', '')
        return self._hash_password(password) == stored_hash
    
    def admin_login(self):
        """Admin login with password"""
        if self._is_admin:
            QMessageBox.information(self, "Admin", "Already logged in as Admin")
            return
        
        password, ok = QInputDialog.getText(
            self, 
            "Admin Login", 
            "Enter admin password:",
            QLineEdit.EchoMode.Password
        )
        
        if ok and password:
            if self._verify_password(password):
                self.set_admin_mode(True)
                self.status_bar.showMessage("Admin login successful", 3000)
                logger.info("Admin logged in")
            else:
                QMessageBox.warning(self, "Login Failed", "Incorrect password")
                logger.warning("Failed admin login attempt")
    
    def admin_logout(self):
        """Admin logout"""
        if not self._is_admin:
            return
        
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.set_admin_mode(False)
            self.status_bar.showMessage("Admin logged out", 3000)
            logger.info("Admin logged out")
    
    def change_admin_password(self):
        """Change admin password (requires current password)"""
        if not self._is_admin:
            QMessageBox.warning(self, "Access Denied", "Please login as admin first")
            return
        
        # Ask for current password
        current_password, ok = QInputDialog.getText(
            self,
            "Change Password",
            "Enter current password:",
            QLineEdit.EchoMode.Password
        )
        
        if not ok or not current_password:
            return
        
        if not self._verify_password(current_password):
            QMessageBox.warning(self, "Error", "Current password is incorrect")
            return
        
        # Ask for new password
        new_password, ok = QInputDialog.getText(
            self,
            "Change Password",
            "Enter new password:",
            QLineEdit.EchoMode.Password
        )
        
        if not ok or not new_password:
            return
        
        if len(new_password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters")
            return
        
        # Confirm new password
        confirm_password, ok = QInputDialog.getText(
            self,
            "Change Password",
            "Confirm new password:",
            QLineEdit.EchoMode.Password
        )
        
        if not ok or not confirm_password:
            return
        
        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return
        
        # Save new password
        password_hash = self._hash_password(new_password)
        self.config_manager.set_app_config('admin.password_hash', password_hash)
        self.config_manager.save_configs()
        
        QMessageBox.information(self, "Success", "Password changed successfully")
        logger.info("Admin password changed")
    
    def set_timezone(self, timezone: str):
        """Set timezone from menu selection"""
        if hasattr(self.show_manager_tab, '_set_timezone'):
            self.show_manager_tab._set_timezone(timezone)
            
            # Update checked state
            for action in self.timezone_actions:
                action.setChecked(action.text() == timezone)
            
            logger.info(f"Timezone set to: {timezone}")
    
    def change_timezone(self):
        """Change timezone setting (deprecated - kept for compatibility)"""
        if hasattr(self.show_manager_tab, '_cycle_timezone'):
            self.show_manager_tab._cycle_timezone()
            current_tz = self.show_manager_tab._timezones[self.show_manager_tab._tz_index]
            QMessageBox.information(self, "Timezone Changed", f"Timezone set to: {current_tz}")
    
    def set_theme(self, theme: str):
        """Set theme from menu selection"""
        # Update checked state
        for action in self.theme_actions:
            action.setChecked(action.text() == theme)
        
        if theme == "Dark":
            self.apply_dark_theme()
        elif theme == "Light":
            self.apply_light_theme()
        else:  # System
            self.apply_system_theme()
        
        logger.info(f"Theme set to: {theme}")
    
    def set_language(self, language_code: str):
        """Set language from menu selection"""
        # Update checked state
        lang_names = {'en': 'English', 'vi': 'Tiếng Việt'}
        for action in self.language_actions:
            action.setChecked(action.text() == lang_names.get(language_code, 'English'))
        
        # TODO: Implement actual language switching
        QMessageBox.information(self, "Language", f"Language switching will be implemented soon.\nSelected: {language_code}")
        logger.info(f"Language set to: {language_code}")
    
    def toggle_webserver(self, enabled: bool):
        """Toggle webserver on/off"""
        if enabled:
            if self.webserver:
                self.webserver.start_server()
                logger.info("Webserver enabled")
        else:
            if self.webserver:
                self.webserver.stop_server()
                logger.info("Webserver disabled")
    
    def show_webserver_settings(self):
        """Show webserver settings dialog"""
        from PyQt6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Web Server Settings")
        layout = QFormLayout(dialog)
        
        from PyQt6.QtWidgets import QSpinBox, QLineEdit
        port_spin = QSpinBox()
        port_spin.setRange(1, 65535)
        port_spin.setValue(self.config_manager.get_app_config('webserver.port', 8080) if self.config_manager else 8080)
        layout.addRow("Port:", port_spin)
        
        host_edit = QLineEdit(self.config_manager.get_app_config('webserver.host', '0.0.0.0') if self.config_manager else '0.0.0.0')
        layout.addRow("Host:", host_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if self.config_manager:
                self.config_manager.set_app_config('webserver.port', port_spin.value())
                self.config_manager.set_app_config('webserver.host', host_edit.text())
                self.config_manager.save_configs()
            QMessageBox.information(self, "Settings Saved", "Webserver settings saved. Restart required to apply changes.")
    
    def show_recording_settings(self):
        """Show recording settings dialog"""
        QMessageBox.information(self, "Recording Settings", "Recording settings dialog will be implemented soon.")
    
    def show_system_settings(self):
        """Show system settings dialog"""
        QMessageBox.information(self, "System Settings", "System settings dialog will be implemented soon.")
    
    def apply_light_theme(self):
        """Apply light theme"""
        self.setStyleSheet("")  # Reset to default light theme
        logger.info("Light theme applied")
    
    def apply_system_theme(self):
        """Apply system theme"""
        # TODO: Detect and apply system theme
        self.apply_dark_theme()  # Default to dark for now
        logger.info("System theme applied")
    
    def sync_ntp_time(self):
        """Sync time with NTP server"""
        if hasattr(self.show_manager_tab, '_sync_ntp_once'):
            self.show_manager_tab._sync_ntp_once()
    
    def change_background(self):
        """Change background image"""
        if hasattr(self.show_manager_tab, '_select_background'):
            self.show_manager_tab._select_background()
    
    def edit_project_name(self):
        """Edit project name (admin only)"""
        if not self._is_admin:
            QMessageBox.warning(self, "Access Denied", "Please login as admin first")
            return
        
        if hasattr(self.show_manager_tab, '_edit_project_name'):
            self.show_manager_tab._edit_project_name()
    
    def toggle_admin_mode(self):
        """Deprecated - kept for compatibility"""
        self.admin_login()