"""
Main Window cho DMX Master
PyQt6 GUI với 5 tabs chính và tích hợp DMX Master
"""

import sys
import os
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
from src.gui.tabs.show_manager import ShowManagerTab
from src.gui.tabs.hardware_manager import HardwareManagerTab  
from src.gui.tabs.dmx_view import DMXViewTab
from src.gui.tabs.settings import SettingsTab
from src.gui.tabs.record import RecordTab

# Import components
from src.gui.widgets.status_widget import StatusWidget
from src.gui.widgets.ip_info_widget import IPInfoWidget
from src.artnet.controller import ArtNetController
from src.webserver.server import MP3UploadServer
from src.show.manager import ShowManager
from src.utils.config import ConfigManager

# Import version info
try:
    from src.version import __version__, __build__, __author__, __email__, __github_repo__, __update_url__
except ImportError:
    __version__ = "1.0.0"
    __build__ = "Unknown"
    __author__ = "Unknown"
    __email__ = "support@example.com"
    __github_repo__ = "https://github.com"
    __update_url__ = ""

# Import license manager
from src.utils.license import LicenseManager
from src.gui.dialogs.license_dialog import LicenseDialog

logger = logging.getLogger(__name__)

# Import IOBoard Serial Controller (background operation)
try:
    from src.serial.serial_controller import SerialController
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    logger.warning("Serial module not available - IOBoard features disabled")

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
        
        # Initialize ShowManager with AppData path
        shows_path = self.get_app_data_dir() / "shows"
        shows_path.mkdir(parents=True, exist_ok=True)
        
        # Copy default shows from installation directory on first run
        self._copy_default_shows()
        
        self.show_manager = ShowManager(str(shows_path))
        
        self.artnet_controller = None
        self.webserver = None
        
        # IOBoard Serial Controller (background, auto-connect)
        self.serial_controller = None
        
        # License manager
        self.license_manager = LicenseManager()
        
        # Admin authentication
        self._is_admin = False
        self._init_admin_password()
        
        # Check license before starting
        if not self._check_license():
            return
        
        # Get admin status from license (licensed users = admin)
        self._is_licensed_admin = self.license_manager.is_admin() if self.license_manager else False
        
        # Setup UI
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.apply_dark_theme()
        
        # Initialize components
        self.init_artnet_controller()
        self.init_serial_controller()  # Auto-init IOBoard (background)
        
        # Connect signals for thread-safe DMX updates
        self.dmx_data_updated.connect(self.on_dmx_data_updated_slot)
        
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
        self.setWindowTitle(f"DMX Master v{__version__}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set application icon
        from PyQt6.QtGui import QIcon
        icon_path = Path(__file__).parent.parent.parent / "assets" / "DMXMaster.ico"
        if Path(icon_path).exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
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
        self.show_manager_tab = ShowManagerTab(
            config_manager=self.config_manager,
            artnet_controller=self.artnet_controller,
            is_admin=self._is_licensed_admin  # Only licensed users can delete/edit shows
        )
        self.show_manager_tab.dmx_changed.connect(self.update_dmx_output)
        self.tab_widget.addTab(self.show_manager_tab, "Show Manager")
        
        # Hardware Manager Tab
        self.hardware_manager_tab = HardwareManagerTab(self.config_manager)
        self.hardware_manager_tab.universe_mapping_changed.connect(self.on_universe_mapping_changed)
        self.hardware_manager_tab.set_admin_mode(self._is_admin)  # Initialize with current admin status
        self.tab_widget.addTab(self.hardware_manager_tab, "Hardware Manager")
        
        # DMX View Tab
        self.dmx_view_tab = DMXViewTab(self.config_manager)
        self.tab_widget.addTab(self.dmx_view_tab, "DMX View")
        
        # Settings Tab
        self.settings_tab = SettingsTab(self.config_manager)
        self.settings_tab.settings_changed.connect(self.apply_settings)
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Record Tab (only for admin users with valid license)
        self.record_tab = RecordTab(self.config_manager, self.artnet_controller)
        # TEMP: Always show Record tab for testing timecode
     #   self.tab_widget.addTab(self.record_tab, "Record")
     #   logger.info("📼 Record tab added (TEMP: admin check bypassed for testing)")
    
    def setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        reload_shows_action = QAction("🔄 &Reload Shows", self)
        reload_shows_action.setShortcut(QKeySequence("F5"))
        reload_shows_action.triggered.connect(self.reload_shows)
        file_menu.addAction(reload_shows_action)
        
        file_menu.addSeparator()
        
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
        # System submenu
        system_submenu = setting_menu.addMenu("S&ystem")
        
        # System Settings action - dẫn đến tab System trong Settings
        system_settings_action = QAction("System &Settings...", self)
        system_settings_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        system_settings_action.triggered.connect(self.show_system_settings)
        system_submenu.addAction(system_settings_action)
        
        system_submenu.addSeparator()
        
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
        
        # Debug menu (for testing)
        debug_menu = menubar.addMenu("&Debug")
        
        # Test DMX output
        test_dmx_action = QAction("🧪 Test DMX Output", self)
        test_dmx_action.triggered.connect(self.test_dmx_output)
        debug_menu.addAction(test_dmx_action)
        
        license_action = QAction("📝 &License Activation...", self)
        license_action.triggered.connect(self.show_license_dialog)
        help_menu.addAction(license_action)
        
        help_menu.addSeparator()
        
        check_update_action = QAction("Check for &Updates...", self)
        check_update_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(check_update_action)
        
        view_logs_action = QAction("📁 View &Logs Folder", self)
        view_logs_action.triggered.connect(self._open_logs_folder)
        help_menu.addAction(view_logs_action)

        help_menu.addSeparator()
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        help_menu.addSeparator()
        
        restart_action = QAction("🔄 &Restart Application", self)
        restart_action.setShortcut(QKeySequence("Ctrl+R"))
        restart_action.triggered.connect(self.restart_app)
        help_menu.addAction(restart_action)

        # Hidden admin shortcut: Adjust max universes (Ctrl+Alt+U)
        # Not shown in menus; requires admin login + valid license
        try:
            from PyQt6.QtGui import QShortcut
            shortcut = QShortcut(QKeySequence("Ctrl+Alt+U"), self)
            shortcut.activated.connect(self._admin_set_max_universes)
        except Exception:
            pass

    def _admin_set_max_universes(self):
        """Hidden admin action to set max universes (requires admin + license)"""
        if not (self._is_admin and self._is_licensed_admin):
            QMessageBox.warning(self, "Access Denied", "Admin login and valid license required.")
            return

        # Read current from unified system config
        try:
            from system.config_manager import get_config_manager
            sys_cfg = get_config_manager()
            current = int(sys_cfg.get('universes.max_universes', 32))
        except Exception:
            sys_cfg = None
            current = 32

        # Ask for new value
        new_value, ok = QInputDialog.getInt(
            self,
            "Set Max Art-Net Universes",
            "Enter max universes (1-512):",
            value=current,
            min=1,
            max=512
        )
        if not ok:
            return

        # Save to unified system config
        try:
            if sys_cfg is None:
                from system.config_manager import get_config_manager as _get
                sys_cfg = _get()
            sys_cfg.set('universes.max_universes', int(new_value))
            sys_cfg.save()
            QMessageBox.information(
                self,
                "Max Universes Updated",
                "Change saved. Please restart the application to apply to all modules (Record/Playback/PollReply)."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save setting: {e}")
    
    def get_app_data_dir(self):
        """Get application data directory (consistent across dev/build)"""
        # Always use AppData to avoid permission issues in Program Files
        if sys.platform == 'win32':
            appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
            app_dir = Path(appdata) / "DMX Master LTS"
        else:
            app_dir = Path.home() / ".dmx-master-lts"
        
        data_dir = app_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    def _copy_default_shows(self):
        """Copy default shows from installation directory to AppData on first run"""
        import shutil
        
        # Destination: AppData shows directory
        dest_shows_dir = self.get_app_data_dir() / "shows"
        dest_shows_dir.mkdir(parents=True, exist_ok=True)
        
        # Source: Installation directory (where the exe is located)
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            install_dir = Path(sys.executable).parent
        else:
            # Running from source
            install_dir = Path(__file__).parent.parent.parent
        
        source_shows_dir = install_dir / "data" / "shows"
        
        if not source_shows_dir.exists():
            logger.warning(f"Default shows directory not found: {source_shows_dir}")
            return
        
        # Copy default shows if they don't exist in AppData (only files, not directories)
        copied_count = 0
        for show_file in source_shows_dir.glob("Default_*"):
            if not show_file.is_file():  # Skip directories
                continue
            dest_file = dest_shows_dir / show_file.name
            if not dest_file.exists():
                try:
                    shutil.copy2(show_file, dest_file)
                    logger.info(f"Copied default show: {show_file.name}")
                    copied_count += 1
                except Exception as e:
                    logger.error(f"Failed to copy {show_file.name}: {e}")
        
        if copied_count > 0:
            logger.info(f"Copied {copied_count} default show file(s) to AppData")
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = self.statusBar()
        
        # V1.3.0: License status label
        self.license_status_label = QLabel()
        self._update_license_status_label()
        self.status_bar.addWidget(self.license_status_label)
        
        # Status widget
        self.status_widget = StatusWidget()
        self.status_bar.addPermanentWidget(self.status_widget)
        
        self.status_bar.showMessage("Ready")
    
    def _update_license_status_label(self):
        """Update license status label in status bar"""
        try:
            tier = self.license_manager.get_license_tier()
            max_universes = self.license_manager.get_max_universes()
            
            if tier == "FREE":
                self.license_status_label.setText(f"🆓 FREE Version - {max_universes} Universes")
                self.license_status_label.setStyleSheet("color: orange; padding: 5px; font-weight: bold;")
            else:
                self.license_status_label.setText(f"✓ LICENSED - {max_universes} Universes")
                self.license_status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
        except Exception as e:
            logger.error(f"Failed to update license status: {e}")
            self.license_status_label.setText("License: Unknown")
            self.license_status_label.setStyleSheet("color: gray; padding: 5px;")
    
    def init_artnet_controller(self):
        """Initialize DMX Master"""
        try:
            # V2.1: Get bind_ip from config
            bind_ip = self.config_manager.get_app_config('artnet.bind_ip', '0.0.0.0')
            logger.info(f"Initializing ArtNetController with bind_ip: {bind_ip}")
            
            self.artnet_controller = ArtNetController(bind_ip=bind_ip)
            
            # Set callbacks
            self.artnet_controller.dmx_received_callback = self.on_dmx_received
            self.artnet_controller.node_discovered_callback = self.on_node_discovered
            
            # Pass controller to DMX View tab
            self.dmx_view_tab.set_artnet_controller(self.artnet_controller)
            
            logger.info("DMX Master initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DMX Master: {e}")
            QMessageBox.warning(self, "Warning", f"Failed to initialize DMX Master: {e}")
    
    def init_serial_controller(self):
        """
        Initialize IOBoard Serial Controller (Background Operation)
        - Auto-detect DMX Master IO boards
        - Auto-connect all boards
        - Auto-mapping universes (Board #1→U0,1, Board #2→U2,3, etc.)
        - Silent operation (logs only)
        """
        if not SERIAL_AVAILABLE:
            logger.info("Serial features not available (pyserial not installed)")
            return
        
        try:
            # Check if serial is enabled in config
            serial_enabled = self.config_manager.get_app_config('serial.enabled', False)
            if not serial_enabled:
                logger.info("IOBoard serial output disabled in config")
                return
            
            # Get baudrate from config
            baudrate = self.config_manager.get_app_config('serial.baudrate', 500000)
            
            # Create serial controller
            self.serial_controller = SerialController(baudrate=baudrate)
            
            # Check if pyserial is available
            if not self.serial_controller.is_available():
                logger.warning("pyserial not installed - IOBoard features disabled")
                self.serial_controller = None
                return
            
            # Auto-scan and connect to all IOBoards (background)
            logger.info("Scanning for IOBoard devices...")
            connected_count = self.serial_controller.scan_and_connect_all()
            
            if connected_count > 0:
                # Success - log board mapping
                mapping = self.serial_controller.get_universe_mapping()
                logger.info(f"✅ IOBoard: Connected to {connected_count} board(s)")
                for board_num, universes in mapping.items():
                    logger.info(f"   Board #{board_num} → Universes {universes}")
            else:
                # No boards found - not an error, just log info
                logger.info("No IOBoard devices detected (this is normal if no boards connected)")
                self.serial_controller = None
            
        except Exception as e:
            logger.error(f"IOBoard initialization error: {e}")
            self.serial_controller = None
    
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
            
            # Notify Record tab that Art-Net controller is now available
            if hasattr(self, 'record_tab') and self.record_tab:
                logger.info("📼 Updating Record tab with Art-Net controller...")
                self.record_tab.set_artnet_controller(self.artnet_controller)
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
        """Callback when DMX data received - THREAD SAFE VERSION"""
        logger.debug(f"DMX received callback: Universe {universe}, {len(dmx_data)} channels from {source_ip}")
        
        # Store source_ip for signal
        self._last_source_ip = source_ip
        
        # ONLY emit signal - let slot handle UI updates in main thread
        self.dmx_data_updated.emit(universe, dmx_data)
        
        # Record if enabled (safe from any thread)
        if hasattr(self, 'record_tab') and self.record_tab.is_recording():
            try:
                self.record_tab.record_dmx_data(universe, dmx_data)
            except Exception as e:
                logger.error(f"Error recording DMX data: {e}")
    
    def on_dmx_data_updated_slot(self, universe: int, dmx_data: bytes):
        """SLOT: Handle DMX data updates in main GUI thread - THREAD SAFE"""
        try:
            source_ip = getattr(self, '_last_source_ip', 'Unknown')
            logger.debug(f"DMX slot received: Universe {universe}, {len(dmx_data)} channels from {source_ip}")
            
            # Update DMX View tab safely in main thread
            if hasattr(self, 'dmx_view_tab'):
                self.dmx_view_tab.update_received_dmx(universe, dmx_data, source_ip)
            else:
                logger.warning(f"⚠️ DMX View tab not found!")
                
        except Exception as e:
            logger.error(f"❌ Error updating DMX view: {e}")
    
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

        # Debug logging for show playback
        non_zero_channels = sum(1 for x in dmx_data if x > 0) if dmx_data else 0
        logger.info(f"Show output: Universe {universe}, {len(dmx_data) if dmx_data else 0} channels, {non_zero_channels} active")

        # Send to Art-Net (network)
        if self.artnet_controller and self.artnet_controller.running:
            if dmx_data:
                # Sử dụng send_dmx_with_mapping để gửi theo cấu hình
                self.artnet_controller.send_dmx_with_mapping(universe, dmx_data)
                self.dmx_data_updated.emit(universe, dmx_data)
                
                # LUÔN update DMX View khi phát show (dù có hoặc không có nodes)
                self.dmx_view_tab.update_dmx_data(universe, dmx_data)
                logger.debug(f"Updated DMX View with universe {universe} data")
        else:
            logger.warning(f"Cannot send DMX: Art-Net controller not running")
        
        # Send to IOBoard (serial) - Background operation, silent
        if self.serial_controller and self.serial_controller.is_connected():
            try:
                # Auto-route DMX to correct board based on universe mapping
                success = self.serial_controller.send_dmx(universe, dmx_data)
                if success:
                    logger.debug(f"IOBoard: Sent Universe {universe} to serial")
                # No error logging if send fails - handled in serial_controller
            except Exception as e:
                # Log error but don't show to user
                logger.error(f"IOBoard send error (Universe {universe}): {e}")
    
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
        <h2>DMX Master</h2>
        <p><b>Version:</b> {__version__}<br>
        <b>Build:</b> {__build__}<br>
        <b>Author:</b> {__author__}<br>
        <b>Email:</b> <a href="mailto:{__email__}">{__email__}</a></p>
        
        <p><b>Professional Art-Net DMX Controller</b></p>

        
        <p>© 2025 DMX Master Team. All rights reserved.</p>
        """
        
        QMessageBox.about(self, "About DMX Master", about_text)
    
    def reload_shows(self):
        """Reload all shows from storage"""
        reply = QMessageBox.question(
            self,
            "Reload Shows",
            "🔄 Reload all shows from storage?\n\nThis will refresh the show library.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Reload shows in Show Manager tab
                if hasattr(self, 'show_manager_tab'):
                    if hasattr(self.show_manager_tab, 'reload_shows'):
                        self.show_manager_tab.reload_shows()
                    else:
                        logger.warning("ShowManagerTab does not have reload_shows method")
                        
                    self.status_bar.showMessage("✅ Shows reloaded successfully", 3000)
                    logger.info("Shows reloaded from storage")
                    
                    QMessageBox.information(
                        self,
                        "Success",
                        "✅ All shows have been reloaded successfully!"
                    )
            except Exception as e:
                logger.error(f"Failed to reload shows: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"❌ Failed to reload shows:\n{e}"
                )
    
    def test_dmx_output(self):
        """Test DMX output manually"""
        logger.info("Manual DMX test initiated")
        
        # Create test DMX data: first 10 channels at 255, rest at 0
        test_data = bytearray(512)
        for i in range(10):
            test_data[i] = 255
        
        # Send to universe 0
        universe = 0
        dmx_data = bytes(test_data)
        
        logger.info(f"Sending test DMX: Universe {universe}, 10 channels at 255")
        self.update_dmx_output(universe, dmx_data)
    
    def restart_app(self):
        """Restart the application"""
        reply = QMessageBox.question(
            self,
            "Restart Application",
            "🔄 Restart DMX Master?\n\nThe application will close and restart.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("Restarting application...")
            
            # Get the current executable path
            import sys
            import subprocess
            
            try:
                # Close current app
                QApplication.quit()
                
                # Restart with same Python interpreter
                subprocess.Popen([sys.executable, "main.py"], 
                               cwd=Path(__file__).parent.parent.parent)
            except Exception as e:
                logger.error(f"Failed to restart: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"❌ Failed to restart application:\n{e}\n\nPlease restart manually."
                )
                self.close()
    
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
            req.add_header('User-Agent', f'DMXMaster/{__version__}')
            
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
                    
                    <p>You are running the latest version of DMX Master.</p>"""
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
    
    def _open_logs_folder(self):
        """Open logs folder in file explorer"""
        import os
        import subprocess
        from src.system.crash_reporter import LOG_DIR
        
        logs_dir = LOG_DIR
        
        if logs_dir.exists():
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(logs_dir)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', str(logs_dir)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(logs_dir)])
                
                logger.info(f"Opened logs folder: {logs_dir}")
            except Exception as e:
                logger.error(f"Failed to open logs folder: {e}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to open logs folder:\n{str(e)}\n\nPath: {logs_dir}"
                )
        else:
            QMessageBox.warning(
                self,
                "Logs Not Found",
                f"Logs folder does not exist:\n{logs_dir}\n\nLogs will be created when the app runs."
            )

    def closeEvent(self, event):
        """Handle application close"""
        # Stop Art-Net
        if self.artnet_controller:
            self.artnet_controller.stop()
        
        # Disconnect IOBoard (serial)
        if self.serial_controller:
            try:
                self.serial_controller.disconnect_all()
                logger.info("IOBoard serial connections closed")
            except Exception as e:
                logger.error(f"Error closing IOBoard: {e}")
        
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
        
        # Update Hardware Manager tab admin mode
        self.hardware_manager_tab.set_admin_mode(is_admin)
        
        # Update menu actions
        self.login_action.setEnabled(not is_admin)
        self.logout_action.setEnabled(is_admin)
        self.change_password_action.setEnabled(is_admin)
        self.edit_project_action.setEnabled(is_admin)
        
        # Update Record tab visibility (requires both admin login AND license)
        self._update_record_tab_visibility()
    
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
                
                <p>To continue using DMX Master, please purchase a license key.</p>
                
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
                    "Trial Expired - DMX Master",
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
                    "Application will now close.\n\nPlease activate a license to continue using DMX Master."
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
        
        <p>You are using the trial version of DMX Master.</p>
        
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
        
        # Update UI based on new license status
        self._update_ui_for_license_status()
    
    def _update_ui_for_license_status(self):
        """Update UI elements based on license status"""
        # Update admin flag
        old_admin_status = self._is_licensed_admin
        self._is_licensed_admin = self.license_manager.is_admin()
        
        # If license status changed, update Record tab visibility
        if old_admin_status != self._is_licensed_admin:
            self._update_record_tab_visibility()
    
    def _update_record_tab_visibility(self):
        """Update Record tab visibility based on admin login AND license status"""
        # Record tab should be visible only if:
        # 1. Admin is logged in (_is_admin)
        # 2. License is activated (_is_licensed_admin)
        should_show = self._is_admin and self._is_licensed_admin
        
        # Find Record tab index
        record_tab_index = -1
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == self.record_tab:
                record_tab_index = i
                break
        
        if should_show and record_tab_index == -1:
            # Add Record tab (after Settings tab)
            settings_index = -1
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "Settings":
                    settings_index = i
                    break
            
            if settings_index != -1:
                self.tab_widget.insertTab(settings_index + 1, self.record_tab, "Record")
                logger.info("Record tab added (admin logged in + licensed)")
        
        elif not should_show and record_tab_index != -1:
            # Remove Record tab
            self.tab_widget.removeTab(record_tab_index)
            logger.info("Record tab removed (not admin or not licensed)")
    
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
        """Show system settings - Open Settings tab and switch to System"""
        # Switch to Settings tab
        self.tab_widget.setCurrentWidget(self.settings_tab)
        
        # Switch to System tab within Settings
        if hasattr(self.settings_tab, 'settings_tabs'):
            # Find System tab index
            for i in range(self.settings_tab.settings_tabs.count()):
                if self.settings_tab.settings_tabs.tabText(i) == "System":
                    self.settings_tab.settings_tabs.setCurrentIndex(i)
                    logger.info("Opened System Settings tab")
                    return
        
        logger.warning("System Settings tab not found")
    
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