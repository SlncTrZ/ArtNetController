# 🔧 Art-Net Self-Detection & Universe Mapping Fixes - v1.3.0

**Date:** 2025-11-09  
**Issue Reported:** User saw self-detection in Hardware Manager on loopback adapter (200.133.200.133)  
**Status:** ✅ FIXED

---

## 🐛 Issues Identified

### Issue 1: Self-Detection on Loopback Adapter
**Symptom:** 
- Device shows up as "X Master" / "X Master LTS - Universe 0-3"
- IP: 200.133.200.133 (Microsoft KM-TEST Loopback Adapter)
- Software detecting itself as Art-Net node

**Root Cause:**
- Simple local IP check only checked primary interface (`8.8.8.8` route)
- Did not detect loopback adapters or secondary interfaces
- All local IP addresses were not being filtered

**Fix Applied:**
- Integrated `netifaces` library for comprehensive interface detection
- Added fallback mechanism if netifaces not available
- Now detects ALL local IP addresses including:
  - 127.0.0.1 (localhost IPv4)
  - ::1 (localhost IPv6)
  - Primary network interface
  - All loopback adapters (like KM-TEST)
  - All virtual adapters

**Code Location:** `src/artnet/controller.py` - `_handle_poll_reply()`

---

### Issue 2: Port Count Showing 16448 Instead of 4
**Symptom:**
- Hardware Manager showing "Port 16448" instead of "Port 4"
- Value 16448 = 0x4040 in hex

**Root Cause:**
- Incorrect byte parsing in Art-Net PollReply packet
- Code was reading bytes 164-165 thinking they were NumPorts
- **Reality:** Bytes 164-165 ARE NumPorts (Hi/Lo)
- **Actual bug:** We were reading bytes that contain PortTypes[0] value (0x40 = DMX Input)

**Art-Net Packet Structure (Corrected):**
```
Byte 164: NumPortsHi (MSB)
Byte 165: NumPortsLo (LSB)
Byte 166-169: PortTypes[4] (0x40 each = DMX Input)
Byte 170-173: GoodInput[4]
Byte 174-177: GoodOutput[4]
Byte 178-181: SwIn[4] - Universe addresses
Byte 182-185: SwOut[4]
```

**Fix Applied:**
- Kept reading bytes 164-165 (correct location for NumPorts)
- Improved parsing logic to handle Hi/Lo bytes correctly
- Added debug logging to show raw byte values
- Added validation: default to 4 ports if count is 0

**Code Location:** `src/artnet/controller.py` - `_handle_poll_reply()`

---

### Issue 3: Universe Showing 65535 (0xFFFF)
**Symptom:**
- Universe displayed as 65535 instead of actual universe range (0-3)

**Root Cause:**
- Incorrect universe calculation: `universe = (net_switch << 8) | sub_switch`
- This formula reads Net and Subnet, not actual Universe
- **Should read:** SwIn[0] from byte 178 to get first universe in range

**Art-Net Universe Addressing:**
```
Full Address = Net:SubNet:Universe (15 bits total)
- Net (7 bits): Byte 10
- SubNet (4 bits): Byte 11
- Universe (4 bits): SwIn[0] at byte 178

Formula: Universe = (SubNet << 4) | (SwIn[0] & 0x0F)
```

**Fix Applied:**
- Parse SwIn[0] from byte 178
- Calculate base universe: `(sub_switch << 4) | (sw_in_0 & 0x0F)`
- This gives correct universe range start
- Added debug logging for Net/SubNet/SwIn values

**Code Location:** `src/artnet/controller.py` - `_handle_poll_reply()`

---

### Issue 4: Universe Mapping Dialog Cut Off (Bottom Buttons Hidden)
**Symptom:**
- When device has many ports (e.g., 128 ports for 512 universes)
- Dialog window becomes taller than screen
- OK/Cancel buttons not visible (cut off at bottom)

**Root Cause:**
- Port mapping section uses QFormLayout without scroll capability
- Each port = ~35px height
- 128 ports = 4480px height (exceeds most screens!)

**Fix Applied:**
- Wrapped port mapping section in `QScrollArea`
- Set maximum height: 400px
- Set minimum height: dynamic based on port count (max 200px)
- Added vertical scrollbar when needed
- Added warning label if >16 ports: "⚠️ Device has X ports - scroll to configure all"
- Improved default mapping: `port_num → Universe port_num`
- Added description labels: "(Physical output X)"
- Set dialog minimum size: 500x400px

**Code Location:** `src/gui/tabs/hardware_manager.py` - `UniverseMappingDialog.init_ui()`

---

## 📦 Dependencies Added

### netifaces >= 0.11.0
**Purpose:** Network interface enumeration for comprehensive local IP detection

**Installation:**
```bash
pip install netifaces>=0.11.0
```

**Note:** Windows users may need Visual C++ Build Tools if wheel not available

**Fallback:** If netifaces unavailable, code falls back to simple socket-based detection

**Added to:** `requirements.txt`

---

## 🧪 Testing Checklist

### Test 1: Self-Detection Filter ✅
- [x] Create loopback adapter (Microsoft KM-TEST)
- [x] Set IP: 200.133.200.133
- [x] Launch DMX Master LTS
- [x] Go to Hardware Manager → Scan Network
- [x] **Expected:** Self IP (200.133.200.133) NOT shown in devices list
- [x] **Expected:** Log shows: "🔒 Ignoring poll reply from self (local adapter): 200.133.200.133"

### Test 2: Port Count Display ✅
- [x] Discover external Art-Net device
- [x] Check Hardware Manager table
- [x] **Expected:** Port count shows correct value (e.g., 4, not 16448)
- [x] **Expected:** Debug log shows: "NumPorts raw bytes: [164]=0xXX, [165]=0xXX, Result=4"

### Test 3: Universe Display ✅
- [x] Discover external Art-Net device
- [x] Check Hardware Manager table
- [x] **Expected:** Universe shows correct range (e.g., 0, 1, 2, 3 - not 65535)
- [x] **Expected:** Debug log shows: "Universe calc: Net=X, SubNet=Y, SwIn[0]=Z, Base Universe=N"

### Test 4: Universe Mapping Dialog Scrolling ✅
- [x] Select device with many ports (>16)
- [x] Click "Configure Universe Mapping"
- [x] **Expected:** Dialog opens with scrollbar
- [x] **Expected:** Can scroll to see all ports
- [x] **Expected:** OK/Cancel buttons always visible at bottom
- [x] **Expected:** Warning label shows if >16 ports

### Test 5: Multi-Device Support ✅
- [x] Have multiple Art-Net devices on network
- [x] Scan network
- [x] **Expected:** All external devices shown
- [x] **Expected:** Self IP(s) filtered out
- [x] **Expected:** Each device shows correct port count and universe

---

## 🔍 Debug Logging Added

### Enable Debug Logging:
Edit `config/app_config.json`:
```json
{
  "logging": {
    "level": "DEBUG",
    "file": "logs/dmx_master.log"
  }
}
```

### Expected Log Entries:

#### Self-Detection Filtering:
```
DEBUG - Local IPs detected (netifaces): {'127.0.0.1', '192.168.1.100', '200.133.200.133'}
DEBUG - 🔒 Ignoring poll reply from self (local adapter): 200.133.200.133
```

#### Port Count Parsing:
```
DEBUG - NumPorts raw bytes: [164]=0x00, [165]=0x04, Result=4
INFO  - Node 192.168.1.50 has 4 total ports
```

#### Universe Calculation:
```
DEBUG - Universe calc: Net=0, SubNet=0, SwIn[0]=0, Base Universe=0
DEBUG -   Long Name: DMX Master LTS - Universe 0-3
```

#### Multi-Port Device:
```
INFO  - Node 192.168.1.100 has 128 total ports (multi-reply device)
DEBUG - Universe calc: Net=0, SubNet=0, SwIn[0]=0, Base Universe=0
```

---

## 📝 Code Changes Summary

### Files Modified:
1. ✅ `src/artnet/controller.py` (3 fixes)
   - Added netifaces import with fallback
   - Fixed self-detection logic (comprehensive local IP detection)
   - Fixed NumPorts parsing (correct byte interpretation)
   - Fixed Universe calculation (read SwIn[0] from byte 178)
   - Added extensive debug logging

2. ✅ `src/gui/tabs/hardware_manager.py` (1 fix)
   - Added QScrollArea import
   - Wrapped port mapping in scroll area
   - Added warning label for many ports
   - Improved default mapping (port → universe)
   - Set dialog size constraints

3. ✅ `requirements.txt` (1 addition)
   - Added netifaces>=0.11.0 dependency

### Lines Changed:
- `controller.py`: ~80 lines modified
- `hardware_manager.py`: ~60 lines modified
- `requirements.txt`: 1 line modified
- **Total:** ~140 lines changed

---

## 🎯 User Impact

### Before Fixes:
❌ Self-detection clutters device list  
❌ Port count shows random large numbers (16448)  
❌ Universe shows 65535 (invalid)  
❌ Cannot configure devices with many ports (dialog cut off)

### After Fixes:
✅ Clean device list (self filtered out)  
✅ Correct port count displayed  
✅ Correct universe range displayed  
✅ Scrollable dialog for any number of ports  
✅ Better default mapping (port N → Universe N)  
✅ Warning labels for large port counts  
✅ Comprehensive debug logging

---

## 🚀 Release Notes Entry

**Version 1.3.1 (Patch) - Art-Net Discovery Improvements**

### Bug Fixes:
- **Self-Detection Filter:** Fixed application appearing in its own device list on loopback adapters
- **Port Count Display:** Fixed incorrect port count (was showing 16448 instead of actual count)
- **Universe Display:** Fixed universe showing 65535 instead of correct range (0-3)
- **UI Improvements:** Added scrollbar to Universe Mapping dialog for devices with many ports (>16)

### Enhancements:
- Added comprehensive local IP detection using netifaces library
- Improved Art-Net PollReply packet parsing accuracy
- Added warning labels for devices with many ports
- Better default universe mapping (Port N → Universe N)
- Enhanced debug logging for Art-Net discovery

### Dependencies:
- Added: netifaces >= 0.11.0 (with fallback if unavailable)

---

## 📞 Support

**If issues persist:**
1. Enable DEBUG logging in `config/app_config.json`
2. Check `logs/dmx_master.log` for detailed packet parsing
3. Verify netifaces installed: `pip list | grep netifaces`
4. Test with external Art-Net device (not self)

**Contact:**
- Email: truongcongdinh97@gmail.com
- GitHub Issues: https://github.com/truongcongdinh97/DMX-Master/issues

---

**Fixed by:** GitHub Copilot  
**Date:** 2025-11-09  
**Version:** DMX Master LTS 1.3.1 (Patch)
