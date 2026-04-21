# DMX Master LTS v1.0.2 - Release Notes

**Release Date:** November 5, 2025  
**Build:** 2025.11.05.3  
**Type:** Production Release

## 🚨 Critical Fixes

### 🔧 Art-Net Packet Parsing Fixed
- **FIXED:** Major Art-Net DMX packet parsing bug that caused empty callbacks
- **FIXED:** Incorrect payload offset in `ArtNetDMX.unpack_dmx()` method
- **RESULT:** DMX callbacks now receive correct 512-byte data instead of 0 bytes

### 🌍 Depence Universe Mapping
- **NEW:** Full support for Depence universe numbering (starts from 1)
- **MAPPING:** Depence Universe 1 → DMX Master Universe 0
- **MAPPING:** Depence Universe 2 → DMX Master Universe 1
- **GUI:** Added universe mapping indicator "📍 Depence U1→U0" in DMX View

## 📋 Improvements

### 🎯 Enhanced Documentation
- **NEW:** `DEPENCE_ARTNET_SETUP.md` - Complete Depence integration guide
- **NEW:** Universe mapping explanations and troubleshooting
- **UPDATED:** All test scripts with correct Depence universe settings

### 🧪 New Test Tools
- **NEW:** `test_universe_mapping.py` - Verify Depence→DMX Master mapping
- **NEW:** `debug_dmx_parsing.py` - Debug Art-Net packet parsing issues
- **UPDATED:** `test_depence_artnet.py` with correct universe instructions

### 🎨 GUI Enhancements
- **NEW:** Universe mapping tooltip in DMX View
- **NEW:** Visual indicator for Depence users
- **IMPROVED:** Better user guidance for Art-Net configuration

## 🔍 Technical Details

### Art-Net Protocol Fixes
```python
# Before (BROKEN):
sequence = payload[0]
physical = payload[1]
universe = struct.unpack('<H', payload[2:4])[0]

# After (FIXED):
version = struct.unpack('<H', payload[0:2])[0]
sequence = payload[2]
physical = payload[3]
universe = struct.unpack('<H', payload[4:6])[0]
```

### Universe Mapping
- **Art-Net Standard:** Universe 0-32767
- **Depence Software:** Universe 1-32768
- **DMX Master LTS:** Universe 0-32767 (Art-Net compliant)

## 🎭 Depence Integration

### Configuration for Depence:
```
✅ Enable Art-Net Output: ON
🎯 Target IP: 192.168.1.171 (or 127.0.0.1)
🌍 Universe: 1 (appears as Universe 0 in DMX Master)
📡 Port: 6454 (default Art-Net)
```

### Test Commands:
```powershell
# Test universe mapping
python test_universe_mapping.py

# Debug Art-Net parsing
python debug_dmx_parsing.py

# Test Depence communication
python test_depence_artnet.py
```

## 🚀 Upgrade Path

### From v1.0.1 to v1.0.2:
1. **Backup your configuration** (automatic backup created)
2. **Install new version** 
3. **Configure Depence with Universe 1** (not 0)
4. **Test Art-Net reception** in DMX View tab

### Breaking Changes:
- **Depence users:** Change universe from 0 to 1 in Depence settings
- **Art-Net applications:** No changes needed (standard compliant)

## 📊 Verification

### Test Art-Net Reception:
1. Start DMX Master LTS v1.0.2
2. Configure Depence with Universe 1
3. Move faders in Depence
4. Verify data appears in DMX Master Universe 0
5. Check for "📦 DMX packet received" in logs

### Expected Log Output:
```
✅ Art-Net controller started on 0.0.0.0:6454
📦 DMX packet received from 192.168.1.171
🔍 DMX Parse Debug: Universe=0, Length=512
🔄 Calling DMX callback for Universe 0, 512 channels
✅ DMX callback completed successfully
```

## 🏗️ Build Information

### Executable Details:
- **File:** `DMXMaster-LTS-1.0.2-Build3.exe`
- **Size:** ~77 MB (with all dependencies)
- **Architecture:** Windows x64
- **Framework:** PyQt6 + Python 3.13.7

### New Dependencies:
- Enhanced Art-Net parsing with proper offset handling
- Universe mapping utilities
- Improved debug logging system

---

**Note:** This release primarily fixes critical Art-Net communication issues with Depence and other lighting software. All users experiencing Art-Net reception problems should upgrade immediately.

**Support:** For issues, check the troubleshooting guides or create an issue on GitHub.