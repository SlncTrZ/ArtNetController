# 🚀 V2.0 Integration Plan

**Date**: 2025-11-04  
**Base**: V1.0.0 (stable, verified working)  
**Target**: V2.0.0 with enhanced features

---

## ✅ PHASE 1: Foundation Restoration (COMPLETED)

### Status: ✅ DONE
- [x] Restored main.py from V1.0.0
- [x] Restored src/gui/ from V1.0.0
- [x] Verified app launches successfully
- [x] Confirmed license system works (trial mode)
- [x] Confirmed Art-Net starts correctly
- [x] Confirmed webserver runs on port 8080

### Test Results:
```
✅ License: Trial 7 days remaining
✅ Art-Net: Started on 0.0.0.0:6454
✅ Webserver: Started on http://192.168.1.171:8080
✅ IP detection: 192.168.1.171
✅ Main window: Initialized
```

---

## 🔧 PHASE 2: Core V2.0 Integration

### Step 1: Enhanced Logging System
**File**: main.py  
**Changes**:
```python
# Before (V1.0):
from utils.logger import setup_logging
setup_logging()

# After (V2.0):
from system.crash_reporter import setup_logging, setup_exception_handler
setup_logging()  # Now with log rotation + compression
setup_exception_handler()  # Global error handling
```

**Risk**: LOW  
**Test**: Check logs/ folder for rotating files

---

### Step 2: Config Manager V2
**File**: src/gui/main_window.py  
**Changes**:
```python
# In MainWindow.__init__():

# After license check, BEFORE loading config
from system.config_manager import get_config_manager, migrate_v1_to_v2

# Migrate old config if needed
if not os.path.exists('config/config.json'):
    migrate_v1_to_v2()

# Use V2 config manager
self.config_v2 = get_config_manager()

# Keep V1 config for compatibility
self.config_manager = ConfigManager()

# Sync V2 → V1 for modules that still use old config
self._sync_configs()
```

**Method to add**:
```python
def _sync_configs(self):
    """Sync V2 config to V1 config for backward compatibility"""
    try:
        # Get values from V2
        artnet_ip = self.config_v2.get('artnet.ip', '127.0.0.1')
        artnet_port = self.config_v2.get('artnet.port', 6454)
        universes = self.config_v2.get('artnet.universes', 1)
        
        # Set to V1 config
        self.config_manager.set('artnet_ip', artnet_ip)
        self.config_manager.set('artnet_port', artnet_port)
        self.config_manager.set('universes', universes)
        
        logger.info("Config synced: V2 → V1")
    except Exception as e:
        logger.error(f"Config sync failed: {e}")
```

**Risk**: MEDIUM  
**Test**: Check config migration, verify existing settings preserved

---

### Step 3: Add Update Menu
**File**: src/gui/main_window.py  
**Changes in `_create_menu()`**:

```python
# In Help menu (after "About"):
help_menu.addSeparator()

# Update check menu item
update_action = QAction("Check for Updates...", self)
update_action.setShortcut("Ctrl+U")
update_action.triggered.connect(self._check_for_updates)
help_menu.addAction(update_action)

# View logs menu item
logs_action = QAction("View Logs Folder", self)
logs_action.triggered.connect(self._open_logs_folder)
help_menu.addAction(logs_action)
```

**Methods to add**:
```python
def _check_for_updates(self):
    """Check for updates and show update dialog"""
    try:
        from system.update_manager import UpdateManager
        from PyQt6.QtWidgets import QProgressDialog, QMessageBox
        
        # Show progress dialog
        progress = QProgressDialog("Checking for updates...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        # Initialize update manager
        updater = UpdateManager(
            repo_owner="your-github-username",
            repo_name="ArtNetController",
            current_version="2.0.0"
        )
        
        # Check for updates
        QApplication.processEvents()  # Keep UI responsive
        update_info = updater.check_for_updates()
        
        progress.close()
        
        if update_info:
            # New version available
            msg = QMessageBox(self)
            msg.setWindowTitle("Update Available")
            msg.setText(f"Version {update_info['version']} is available!")
            msg.setInformativeText(
                f"Current version: {updater.current_version}\n"
                f"New version: {update_info['version']}\n\n"
                f"Release notes:\n{update_info['body'][:200]}..."
            )
            msg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg.setDefaultButton(QMessageBox.StandardButton.Yes)
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                self._download_and_install_update(updater, update_info)
        else:
            # Already latest
            QMessageBox.information(
                self,
                "No Updates",
                "You are already using the latest version!"
            )
            
    except Exception as e:
        logger.error(f"Update check failed: {e}")
        QMessageBox.warning(
            self,
            "Update Check Failed",
            f"Could not check for updates:\n{str(e)}"
        )

def _download_and_install_update(self, updater, update_info):
    """Download and install update with progress"""
    from PyQt6.QtWidgets import QProgressDialog
    
    # Show download progress
    progress = QProgressDialog("Downloading update...", "Cancel", 0, 100, self)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    
    def progress_callback(downloaded, total):
        if total > 0:
            percent = int((downloaded / total) * 100)
            progress.setValue(percent)
            QApplication.processEvents()
    
    try:
        # Download
        installer_path = updater.download_update(
            update_info,
            progress_callback=progress_callback
        )
        
        progress.close()
        
        # Ask to install
        msg = QMessageBox.question(
            self,
            "Install Update",
            "Download complete! Install now?\n"
            "(Application will restart)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if msg == QMessageBox.StandardButton.Yes:
            # Backup and install
            updater.backup_current_version()
            updater.install_update(installer_path, silent=True)
            
            # Close app (installer will restart)
            QApplication.quit()
            
    except Exception as e:
        logger.error(f"Update installation failed: {e}")
        progress.close()
        QMessageBox.critical(
            self,
            "Update Failed",
            f"Failed to install update:\n{str(e)}\n\n"
            "You can download manually from GitHub."
        )

def _open_logs_folder(self):
    """Open logs folder in file explorer"""
    import os
    import subprocess
    
    logs_dir = os.path.abspath('logs')
    
    if os.path.exists(logs_dir):
        if os.name == 'nt':  # Windows
            os.startfile(logs_dir)
        else:  # Linux/Mac
            subprocess.run(['xdg-open', logs_dir])
    else:
        QMessageBox.warning(
            self,
            "Logs Not Found",
            f"Logs folder does not exist:\n{logs_dir}"
        )
```

**Risk**: LOW  
**Test**: Click menu items, check update dialog appears

---

### Step 4: Startup Update Check
**File**: src/gui/main_window.py  
**Changes in `__init__()`** (at end):

```python
# After main window setup:

# Check for updates on startup (background, non-blocking)
self._startup_update_check()

def _startup_update_check(self):
    """Non-blocking update check on startup"""
    from PyQt6.QtCore import QTimer
    
    # Check if user enabled auto-check
    auto_check = self.config_v2.get('updates.auto_check', True)
    
    if not auto_check:
        return
    
    # Delay check by 5 seconds to not slow down startup
    QTimer.singleShot(5000, self._background_update_check)

def _background_update_check(self):
    """Silent update check in background"""
    try:
        from system.update_manager import UpdateManager
        
        updater = UpdateManager(
            repo_owner="your-github-username",
            repo_name="ArtNetController",
            current_version="2.0.0"
        )
        
        update_info = updater.check_for_updates()
        
        if update_info:
            # Show notification in status bar
            self.statusBar().showMessage(
                f"Update available: v{update_info['version']} - Click Help → Check for Updates",
                10000  # 10 seconds
            )
            logger.info(f"Update available: {update_info['version']}")
        else:
            logger.info("App is up to date")
            
    except Exception as e:
        # Silent fail - don't bother user on startup
        logger.debug(f"Background update check failed: {e}")
```

**Risk**: LOW  
**Test**: Launch app, wait 5 seconds, check status bar

---

## 🎨 PHASE 3: RecordTab Enhancement

### Step 5: Add "Disable Output" Toggle
**File**: src/gui/tabs/record.py  
**Changes in `_create_ui()`**:

```python
# In control panel, after record button:

# Disable output checkbox
self.disable_output_checkbox = QCheckBox("Disable Output During Record")
self.disable_output_checkbox.setChecked(False)
self.disable_output_checkbox.setToolTip(
    "When enabled, DMX output will be paused during recording\n"
    "to prevent affecting live fixtures"
)
control_layout.addWidget(self.disable_output_checkbox)
```

**Changes in `_start_recording()`**:
```python
def _start_recording(self):
    """Start DMX recording"""
    # Check if should disable output
    if self.disable_output_checkbox.isChecked():
        # Pause Art-Net output
        self.artnet_controller.pause_output()
        logger.info("Art-Net output paused for recording")
        
        # Show warning
        self.statusBar().showMessage(
            "⚠️ DMX OUTPUT DISABLED - Recording mode",
            0  # Persistent
        )
    
    # Start recording...
    self.is_recording = True
    # ... rest of recording code
```

**Changes in `_stop_recording()`**:
```python
def _stop_recording(self):
    """Stop DMX recording"""
    # Resume Art-Net if it was paused
    if self.disable_output_checkbox.isChecked():
        self.artnet_controller.resume_output()
        logger.info("Art-Net output resumed")
        self.statusBar().clearMessage()
    
    # Stop recording...
    self.is_recording = False
    # ... rest of code
```

**Add to ArtNetController**:
```python
# In src/artnet/controller.py:

def pause_output(self):
    """Pause DMX output without stopping controller"""
    self.output_paused = True
    logger.info("DMX output paused")

def resume_output(self):
    """Resume DMX output"""
    self.output_paused = False
    logger.info("DMX output resumed")

# In send_dmx():
def send_dmx(self, universe, data):
    """Send DMX data to Art-Net"""
    if hasattr(self, 'output_paused') and self.output_paused:
        return  # Skip sending if paused
    
    # ... rest of send code
```

**Risk**: LOW  
**Test**: Enable checkbox, record, verify no DMX sent to hardware

---

### Step 6: Binary Recorder Integration
**File**: src/gui/tabs/record.py  
**Changes in `_create_ui()`**:

```python
# Add format selector
format_group = QGroupBox("Recording Format")
format_layout = QHBoxLayout()

self.format_json = QRadioButton("JSON (V1.0 - Compatible)")
self.format_binary = QRadioButton("Binary (V2.0 - Recommended)")
self.format_binary.setChecked(True)  # Default to V2

format_layout.addWidget(self.format_json)
format_layout.addWidget(self.format_binary)
format_group.setLayout(format_layout)

control_layout.addWidget(format_group)
```

**Changes in `_save_recording()`**:
```python
def _save_recording(self):
    """Save recording in selected format"""
    if self.format_binary.isChecked():
        self._save_binary_format()
    else:
        self._save_json_format()

def _save_binary_format(self):
    """Save using V2.0 binary recorder"""
    from show.dmx_recorder import DMXRecorder
    
    # Create recorder
    recorder = DMXRecorder()
    
    # Add metadata
    recorder.set_metadata(
        show_name=self.show_name,
        audio_file=self.audio_file_path,
        duration=self.audio_duration,
        universes=self.universe_count
    )
    
    # Add frames
    for frame in self.recorded_frames:
        recorder.add_frame(
            timestamp=frame['timestamp'],
            universe=frame['universe'],
            data=frame['data']
        )
    
    # Save
    filename = f"shows/{self.show_name}.dmxrec"
    recorder.save(filename)
    
    logger.info(f"Saved binary recording: {filename}")
    QMessageBox.information(
        self,
        "Recording Saved",
        f"Saved as: {filename}\n"
        f"Format: Binary V2.0\n"
        f"Size: {os.path.getsize(filename) / 1024:.1f} KB"
    )

def _save_json_format(self):
    """Save using V1.0 JSON format (existing code)"""
    # ... existing V1.0 save code
```

**Risk**: MEDIUM  
**Test**: Record in both formats, verify playback works

---

## 📦 PHASE 4: Build System Update

### Step 7: Update PyInstaller Spec
**File**: build/ArtNetController.spec  
**Changes**:

```python
# Add new V2.0 modules to hiddenimports
hiddenimports=[
    # ... existing imports
    'system.update_manager',
    'system.config_manager',
    'system.crash_reporter',
    'show.dmx_recorder',
],

# Add data files for V2.0
datas=[
    # ... existing data files
    ('config/config.json', 'config'),  # Default V2 config
    ('logs', 'logs'),  # Empty logs folder
],
```

### Step 8: Update Build Script
**File**: build_windows.py  
**Changes**:

```python
# Update version number
VERSION = "2.0.0"

# Add V2.0 changelog to installer
CHANGELOG = """
V2.0.0 Changes:
- ✅ Auto-update system (check from GitHub)
- ✅ Enhanced logging with rotation
- ✅ Crash reporting to GitHub Issues
- ✅ Binary recording format (12x smaller)
- ✅ Improved config management
- ✅ "Disable Output" option in Record tab
- ✅ All V1.0 features preserved
"""
```

**Risk**: LOW  
**Test**: Build exe, verify all V2.0 modules included

---

## 🧪 PHASE 5: Testing

### Test Plan

#### Test 1: Fresh Install
- [ ] Install V2.0 on clean machine
- [ ] Verify license trial starts
- [ ] Verify all tabs load
- [ ] Verify Art-Net starts
- [ ] Check for updates works

#### Test 2: Upgrade from V1.0
- [ ] Install V1.0 first
- [ ] Add some shows
- [ ] Configure Art-Net settings
- [ ] Install V2.0 over V1.0
- [ ] Verify shows preserved
- [ ] Verify settings migrated
- [ ] Verify license still valid

#### Test 3: V2.0 Features
- [ ] Check for updates (mock GitHub release)
- [ ] Download update
- [ ] View logs folder
- [ ] Record with "Disable Output" enabled
- [ ] Record in binary format
- [ ] Play binary recording
- [ ] Crash reporting (trigger exception)

#### Test 4: Backward Compatibility
- [ ] Load V1.0 JSON shows in V2.0
- [ ] Export V2.0 show as JSON
- [ ] Verify V1.0 can load it

---

## 📋 INTEGRATION CHECKLIST

### Pre-Integration
- [x] V1.0 app restored and verified working
- [x] V2.0 modules created and tested individually
- [x] Integration plan documented
- [ ] Backup V1.0 completely (git tag)

### Core Integration
- [ ] Step 1: Enhanced logging (main.py)
- [ ] Step 2: Config Manager V2 (main_window.py)
- [ ] Step 3: Update menu items (main_window.py)
- [ ] Step 4: Startup update check (main_window.py)

### Feature Integration
- [ ] Step 5: Disable output toggle (record.py)
- [ ] Step 6: Binary recorder (record.py)

### Build Integration
- [ ] Step 7: Update PyInstaller spec
- [ ] Step 8: Update build scripts

### Testing
- [ ] Test 1: Fresh install
- [ ] Test 2: Upgrade from V1.0
- [ ] Test 3: V2.0 features
- [ ] Test 4: Backward compatibility

### Documentation
- [ ] Update README.md with V2.0 features
- [ ] Update LICENSE_GUIDE.md (no changes needed)
- [ ] Create CHANGELOG.md
- [ ] Update BUILD_GUIDE.md

### Release
- [ ] Build V2.0.0 installer
- [ ] Test installer on Windows
- [ ] Create GitHub Release v2.0.0
- [ ] Upload installer + portable
- [ ] Test auto-update from V1.0 → V2.0

---

## ⚠️ CRITICAL RULES

### DO NOT MODIFY:
- ❌ src/utils/license.py (license system)
- ❌ tools/license_*.py (license tools)
- ❌ License validation logic
- ❌ RSA key handling
- ❌ Trial period mechanism

### ALWAYS TEST:
- ✅ License system after any change
- ✅ Art-Net output after GUI changes
- ✅ All tabs after MainWindow changes
- ✅ Config loading after config changes

### PRESERVE:
- ✅ All V1.0 keyboard shortcuts
- ✅ All V1.0 menu structure
- ✅ All V1.0 workflows
- ✅ All V1.0 file formats (add new, don't remove)

---

## 📊 RISK MATRIX

| Component | Risk | Impact | Mitigation |
|-----------|------|--------|------------|
| License System | CRITICAL | App unusable | Don't touch, test thoroughly |
| Config Migration | MEDIUM | Settings lost | Backup config, test migration |
| Binary Recorder | LOW | Can fallback to JSON | Keep both formats |
| Update System | LOW | Optional feature | Fail gracefully |
| Logging | LOW | Non-critical | Silent fail if error |

---

## 🎯 SUCCESS CRITERIA

V2.0 is ready for release when:
- [x] V1.0 app runs perfectly
- [ ] All V2.0 modules integrated
- [ ] Exe builds without errors
- [ ] Fresh install works
- [ ] Upgrade from V1.0 works
- [ ] License system works
- [ ] All tabs functional
- [ ] Auto-update tested
- [ ] Documentation updated
- [ ] GitHub Release created

---

**Status**: Phase 1 complete, ready for Phase 2  
**Next**: Integrate enhanced logging (Step 1)  
**ETA**: 2-3 hours for full integration
