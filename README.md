#  DMX-Master - Professional Art-Net Controller

[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE.txt)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Raspberry%20Pi-blue.svg)](README.md)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)

> Professional DMX/Art-Net lighting control software with advanced show management and secure licensing system.

---

##  Features

###  Show Management
- **Spotify-style UI** - Modern, intuitive interface
- **Multi-format support** - MP3, WAV, DMX, Art-Net
- **Timeline editor** - Visual DMX timeline with waveform
- **Auto-sync** - Music synchronized lighting effects

###  Network Control
- **Art-Net protocol** - Industry-standard DMX over IP
- **Multiple universes** - Support up to 16 universes
- **Node discovery** - Auto-scan Art-Net nodes
- **Web interface** - Remote control via browser

###  Advanced License System
- **RSA-2048 signatures** - Cryptographically secure
- **Hardware binding** - One license per device
- **AES-256 encryption** - Protected license files
- **7-day trial** - Full-featured trial period

---

##  Quick Start

``bash
# Clone repository
git clone https://github.com/truongcongdinh97/DMX-Master.git
cd DMX-Master

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
``

** For detailed guides, see [Documentation Index](docs/INDEX.md)**

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

##  For Developers

### Build Executable
``cmd
# Windows
build.bat

# Linux
./build.sh
``

### Create Installer
``cmd
# Requires Inno Setup 6.5.4+
scripts\build_installer.bat
``

**See [scripts/README.md](scripts/README.md) for all build options**

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
