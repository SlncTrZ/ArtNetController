# 🎭 DMX Master LTS 1.3.0 - Professional Art-Net Controller

[![Version](https://img.shields.io/badge/version-1.3.0%20LTS-brightgreen.svg)](https://github.com/truongcongdinh97/DMX-Master/releases)
[![License](https://img.shields.io/badge/license-Dual%20Tier-blue.svg)](LICENSE_TIERS.md)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Raspberry%20Pi-blue.svg)](README.md)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![Release](https://img.shields.io/badge/release-Production%20Ready-success.svg)](https://github.com/truongcongdinh97/DMX-Master/releases)

> **🚀 NOW WITH LICENSE TIERS!** Professional DMX/Art-Net lighting control software. **FREE Version**: 4 universes | **LICENSED Version**: 512 universes. Choose the tier that fits your needs!

---

## 🌟 **What's New in v1.3.0**

### 📦 **License Tiers System**
- **FREE Version** - 4 universes (U0-U3), perfect for small installations
- **LICENSED Version** - 512 universes (U0-U511), professional-grade
- **7-day trial** - Full FREE version features before activation required
- **Seamless upgrade** - Activate license without reinstalling

### � **512 Universe Support**
- **Art-Net mapping** - Net 0-7, Subnet 0-15, Universe 0-15 (full spec)
- **Smart PollReply** - 128 packets (4 universes each) for full capability report
- **License-based filtering** - Auto-block universes beyond tier limit
- **Backward compatible** - Existing shows work with both tiers

### 🔌 **IOBoard Serial Integration**
- **Background operation** - Auto-detect and connect on startup
- **Multi-board support** - Board #1→U0-1, Board #2→U2-3, etc.
- **Concurrent output** - Art-Net + Serial DMX simultaneously
- **DMX512 protocol** - 517-byte packets with XOR checksum (500000 baud)

### 🔒 **Enhanced License System**
- **Universe validation** - Enforced at all output layers (Art-Net/Serial/Recording/Playback)
- **Status bar display** - Real-time license tier indicator
- **Transparent operation** - Universe dropdown auto-adjusts to tier limit
- **Secure enforcement** - Cannot bypass through UI or API

---

## ✨ **Core Features**

### 🎛️ **Professional Controls**
- **Art-Net protocol** - Industry-standard DMX over Ethernet
- **4-512 Universe support** - Scale from small to massive installations (license-based)
- **Web remote control** - Control from any device on network
- **Live DMX monitoring** - Real-time channel visualization

### 📊 **License Tiers**
- **FREE Version**: 4 universes (U0-U3) - [See comparison](LICENSE_TIERS.md)
- **LICENSED Version**: 512 universes (U0-U511) - Full professional capabilities
- **Trial period**: 7 days - Full FREE version features before activation required
- **Flexible upgrade**: Activate license anytime without reinstalling

### 🔒 **Enterprise Security**
- **RSA-2048 signatures** - Cryptographically secure licensing
- **Hardware binding** - One license per device protection
- **AES-256 encryption** - Protected configuration files
- **Offline validation** - Works without internet connection

### 📱 **Modern Interface**
- **PyQt6 GUI** - Native performance, professional appearance
- **Responsive design** - Works on tablets and touch screens
- **Dark/Light themes** - Customizable appearance
- **Multi-language ready** - Internationalization support

---

## 🚀 **Quick Start**

### **Option 1: Download Release (Recommended)**
```bash
# Download from GitHub Releases
https://github.com/truongcongdinh97/DMX-Master/releases/tag/v1.0.0

# Extract and run
DMX-Master-LTS-1.0.0.exe  # Windows
./dmx-master              # Linux
```

### **Option 2: Build from Source**
```bash
# Clone repository
git clone https://github.com/truongcongdinh97/DMX-Master.git
cd DMX-Master

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### **Quick Demo**
1. **Launch** DMX Master LTS 1.0.0
2. **Go to Show Manager** tab
3. **Select** "Default_Rainbow_Show"
4. **Click** "Play Single" button
5. **Watch** 3 minutes of beautiful rainbow effects! 🌈

---

## 📋 **System Requirements**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10, Linux, Raspberry Pi OS | Windows 11, Ubuntu 22.04+ |
| **Python** | 3.8+ | 3.11+ |
| **RAM** | 2GB | 4GB+ |
| **Storage** | 500MB | 2GB+ |
| **Network** | Ethernet/WiFi | Gigabit Ethernet |

---

## 📚 **Documentation**

| Guide | Description |
|-------|-------------|
| **[🚀 Quick Start](docs/QUICK_START.md)** | Get started in 5 minutes |
| **[📖 User Guide](docs/USER_GUIDE.md)** | Complete user manual |
| **[🔧 Build Guide](docs/BUILD_QUICK_GUIDE.md)** | Build from source |
| **[🔑 License Guide](docs/LICENSE_ACTIVATION_GUIDE.md)** | Activate your license |
| **[🌈 Rainbow Effects](docs/RAINBOW_EFFECTS.md)** | Create stunning light shows |
| **[📁 Full Index](docs/INDEX.md)** | All documentation |

---

## 🎯 **Use Cases**

### 🎪 **Live Events**
- **Concerts & Festivals** - Multi-universe stage lighting
- **Theater Productions** - Synchronized lighting and audio
- **DJ Performances** - Real-time reactive lighting
- **Corporate Events** - Professional presentation lighting

### 🏠 **Installation Projects**
- **Architectural Lighting** - Building facade effects
- **Restaurant/Bar Ambiance** - Mood lighting control
- **Retail Displays** - Product showcase lighting
- **Home Automation** - Smart home integration

### 🎓 **Education & Research**
- **Lighting Design Courses** - Learn professional tools
- **Technology Demonstrations** - Art-Net protocol education
- **Research Projects** - DMX control experiments
- **Student Productions** - Budget-friendly solutions

---

## 💝 **Pricing & Licensing**

### 🆓 **Trial Version**
- **Duration:** 7 days full access
- **Features:** All professional features unlocked
- **No restrictions:** Full universe count, all effects
- **No credit card:** Download and start immediately

### 💎 **Professional License**
- **Price:** Contact for pricing
- **Type:** Perpetual license (buy once, use forever)
- **Devices:** One license per device/computer
- **Support:** Lifetime email support included
- **Updates:** Free updates within major version

### 🏢 **Enterprise Options**
- **Multi-device licensing** available
- **Custom integrations** and modifications
- **On-site training** and installation
- **Priority support** and custom features

---

## 🛠️ **Building from Source**

### **Prerequisites**
- **Python 3.8+** installed (Python 3.13+ recommended)
- **Git** for cloning repository
- **PyInstaller** for building executable
- **Inno Setup** (optional, for creating Windows installer)

### **Step 1: Clone Repository**
```bash
git clone https://github.com/truongcongdinh97/DMX-Master.git
cd DMX-Master
```

### **Step 2: Install Dependencies**
```bash
# Install all required packages
pip install -r requirements.txt

# Verify PyInstaller installed
pyinstaller --version
# Should show: 6.16.0 or higher
```

### **Step 3: Build Executable**

#### **Windows (Automated)**
```cmd
# Method 1: Quick build with Python script
python build_windows.py

# Method 2: Legacy batch script
build.bat

# Both methods produce: dist/DMXMaster-LTS-1.3.0.exe
```

#### **Windows (Manual)**
```cmd
# Clean previous builds
rmdir /s /q build
rmdir /s /q dist

# Build with PyInstaller
pyinstaller --clean DMXMaster-LTS-1.3.0.spec

# Output: dist/DMXMaster-LTS-1.3.0.exe (~100-150 MB)
```

#### **Linux/Raspberry Pi**
```bash
# Make build script executable
chmod +x build.sh

# Run build
./build.sh

# Or use Python script
python build_raspberry.py

# Output: dist/DMXMaster-LTS-1.3.0
```

### **Step 4: Test Executable**
```bash
# Navigate to dist folder
cd dist

# Windows - Run executable
DMXMaster-LTS-1.3.0.exe

# Linux - Run executable
./DMXMaster-LTS-1.3.0

# Verify:
# ✓ Application launches
# ✓ Status bar shows "🆓 FREE Version - 4 Universes"
# ✓ Main window displays correctly
# ✓ No error dialogs appear
```

### **Step 5: Create Windows Installer (Optional)**

#### **Install Inno Setup**
1. Download from: https://jrsoftware.org/isdl.php
2. Install Inno Setup 6.5.4 or higher
3. Verify: `iscc /?` shows help

#### **Build Installer**
```cmd
# Method 1: Automated script
scripts\build_installer.bat

# Method 2: Manual compile
iscc ArtNetController.iss

# Output: installer_output/DMX-Master-LTS-1.3.0-Setup.exe
```

#### **Installer Features**
- ✅ Auto-installs to Program Files
- ✅ Creates Start Menu shortcuts
- ✅ Desktop shortcut (optional)
- ✅ Uninstaller included
- ✅ Version detection (prevents downgrades)
- ✅ ~50 MB installer size

### **Build Configuration Files**

#### **DMXMaster-LTS-1.3.0.spec**
PyInstaller specification file defining:
- **Entry point:** `main.py`
- **Included data:** `assets/`, `config/`, `data/`, `src/`
- **Hidden imports:** PyQt6, serial modules, all src packages
- **Icon:** `assets/DMXMaster.ico`
- **Output:** Single-file executable (no console)
- **Compression:** UPX enabled

#### **ArtNetController.iss**
Inno Setup installer script defining:
- **AppId:** `{DMX-MASTER-LTS-130-2025-11-09}`
- **Version:** 1.3.0
- **Output filename:** `DMX-Master-LTS-1.3.0-Setup.exe`
- **Install directory:** `{autopf}\DMX Master LTS`
- **Uninstall support:** Full uninstaller

#### **build_windows.py**
Python build automation script:
- **VERSION:** `1.3.0`
- **SPEC_FILE:** `DMXMaster-LTS-1.3.0.spec`
- **Clean function:** Removes old build artifacts
- **Build function:** Runs PyInstaller with spec file
- **Error handling:** Captures build failures

### **Troubleshooting Build Issues**

#### **Problem: ModuleNotFoundError during build**
```bash
# Solution: Install missing module
pip install <missing-module-name>

# Or reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

#### **Problem: PyInstaller not found**
```bash
# Solution: Install PyInstaller
pip install pyinstaller==6.16.0

# Verify installation
pyinstaller --version
```

#### **Problem: Build succeeds but executable crashes**
```bash
# Check for missing hidden imports
# Edit DMXMaster-LTS-1.3.0.spec
# Add missing modules to hiddenimports list
hiddenimports = [
    'PyQt6.QtCore',
    'your.missing.module',  # Add here
]
```

#### **Problem: Icon missing in executable**
```bash
# Verify icon file exists
dir assets\DMXMaster.ico

# If missing, regenerate icon
python scripts\create_default_icon.py
```

#### **Problem: Executable size too large (>200 MB)**
```bash
# Solution: Disable UPX compression
# Edit DMXMaster-LTS-1.3.0.spec
upx=False,  # Change from True to False
```

#### **Problem: Inno Setup compiler not found**
```cmd
# Solution: Add Inno Setup to PATH
set PATH=%PATH%;C:\Program Files (x86)\Inno Setup 6

# Or use full path
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" ArtNetController.iss
```

### **Development Workflow**

#### **1. Setup Development Environment**
```bash
# Install all dependencies including dev tools
pip install -r requirements.txt

# Optional: Install dev tools
pip install black pylint pytest
```

#### **2. Run Tests**
```bash
# Run license tiers tests
python tests/test_license_tiers.py

# Run all tests (if pytest installed)
pytest tests/

# Expected: All tests pass ✓
```

#### **3. Make Changes**
```bash
# Edit source files in src/
# Test changes by running directly
python main.py
```

#### **4. Build and Test**
```bash
# Build new executable
python build_windows.py

# Test executable
cd dist
DMXMaster-LTS-1.3.0.exe
```

#### **5. Create Release**
```bash
# Create installer
iscc ArtNetController.iss

# Test installer
cd installer_output
DMX-Master-LTS-1.3.0-Setup.exe
```

### **Build Artifacts Locations**

| File Type | Location | Description |
|-----------|----------|-------------|
| **Executable** | `dist/DMXMaster-LTS-1.3.0.exe` | Standalone application |
| **Installer** | `installer_output/DMX-Master-LTS-1.3.0-Setup.exe` | Windows installer |
| **Build cache** | `build/` | PyInstaller temporary files |
| **Spec file** | `DMXMaster-LTS-1.3.0.spec` | Build configuration |
| **Build log** | `build_log.txt` | Build output log |

### **Clean Build (Fresh Start)**
```bash
# Remove all build artifacts
python build_windows.py clean

# Or manually
rmdir /s /q build dist __pycache__ installer_output
del /q *.spec

# Then rebuild
python build_windows.py
```

### **Advanced Build Options**

#### **Debug Build (with console output)**
```python
# Edit DMXMaster-LTS-1.3.0.spec
console=True,  # Change from False to True
debug=True,    # Enable debug mode
```

#### **Multi-file Build (faster startup)**
```python
# Change exe = EXE(...) to exe = COLLECT(...)
# See PyInstaller documentation for details
```

#### **Custom Icon**
```python
# Replace icon in spec file
icon=['path/to/your/icon.ico'],
```

### **For Developers**

#### **Development Setup**
```bash
# Install dev dependencies (if available)
pip install -r requirements-dev.txt

# Code quality checks
black src/          # Format code
pylint src/         # Lint code
mypy src/           # Type check
```

#### **Contributing**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/YourFeature`)
3. Commit changes (`git commit -m 'Add YourFeature'`)
4. Push to branch (`git push origin feature/YourFeature`)
5. Open Pull Request

#### **Version Management**
- **Version file:** `src/version.py`
- **Build file:** `build_windows.py`
- **Spec file:** `DMXMaster-LTS-{VERSION}.spec`
- **Installer:** `ArtNetController.iss`

**Update all 4 files when changing version!**

---

## 📞 **Support & Contact**

### 📧 **Get Help**
- **Email:** truongcongdinh97@gmail.com
- **GitHub Issues:** [Report bugs & request features](https://github.com/truongcongdinh97/DMX-Master/issues)
- **Documentation:** [Complete guides](docs/INDEX.md)

### 💬 **Sales & Licensing**
- **Commercial licensing:** truongcongdinh97@gmail.com
- **Enterprise inquiries:** Custom pricing available
- **Partnership opportunities:** Welcome!

### 🔄 **Updates & News**
- **GitHub Releases:** [Latest versions](https://github.com/truongcongdinh97/DMX-Master/releases)
- **Star this repo** to stay updated! ⭐

---

## 👨‍💻 **Author**

**Trương Công Định** 🇻🇳
- **GitHub:** [@truongcongdinh97](https://github.com/truongcongdinh97)
- **Email:** truongcongdinh97@gmail.com
- **LinkedIn:** [Connect with me](https://linkedin.com/in/truongcongdinh)

---

<div align="center">

## 🌟 **Ready for Production Use!**

**DMX Master LTS 1.0.0** is now available for public release!

[⬇️ **Download Now**](https://github.com/truongcongdinh97/DMX-Master/releases/tag/v1.0.0) | [📖 **Documentation**](docs/INDEX.md) | [🆓 **Try Free**](mailto:truongcongdinh97@gmail.com)

---

**Made with ❤️ in Vietnam** 🇻🇳

*Professional lighting control for everyone* ✨

**⭐ Star this repository if you find it useful!**

</div>

---

##  Requirements

- **OS:** Windows 10+, Linux, Raspberry Pi OS
- **Python:** 3.8+
- **RAM:** 2GB minimum
- **Network:** Ethernet/WiFi for Art-Net

---

##  Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started in 5 minutes
- **[User Guide](docs/USER_GUIDE.md)** - Complete user manual
- **[Build Guide](docs/BUILD_QUICK_GUIDE.md)** - Build from source
- **[License Activation](docs/LICENSE_ACTIVATION_GUIDE.md)** - Activate your license
- **[Full Documentation Index](docs/INDEX.md)** - All documentation

---

##  Project Structure

``
DMX-Master/
 src/                # Source code
    gui/           # PyQt6 GUI components
    core/          # Core DMX/Art-Net logic
    license/       # License management
    utils/         # Utilities
 assets/            # Icons, images, resources
 config/            # Configuration files
 docs/              #  Documentation
 scripts/           #  Build & deployment scripts
 tests/             # Unit tests
 tools/             # Admin tools (license generator)
 main.py            # Application entry point
 README.md          # This file
``

---

##  License

**Proprietary Software** - Copyright  2025 Trương Công Định

### Trial Mode
- 7 days full-featured trial
- No credit card required

### Purchase
- **Email:** truongcongdinh97@gmail.com
- **License:** Perpetual, one device
- **Support:** Lifetime email support



---

##  Support

- **Email:** truongcongdinh97@gmail.com
- **Issues:** [GitHub Issues](https://github.com/truongcongdinh97/DMX-Master/issues)
- **Documentation:** [docs/INDEX.md](docs/INDEX.md)

---

##  Author

**Trương Công Định**
- GitHub: [@truongcongdinh97](https://github.com/truongcongdinh97)
- Email: truongcongdinh97@gmail.com

---

<div align="center">

**Made with  in Vietnam** 

*Professional lighting control for everyone* 

</div>
