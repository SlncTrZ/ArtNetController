# Changelog - Version 1.3.0: License Tiers & 512 Universe Support

## Release Date: 2025-11-09

---

## 🎯 Major Changes

### 1. License Tiers System
**FREE Version (4 Universes)**
- Limited to Universe 0-3 (2,048 DMX channels)
- Perfect for small installations, home use, evaluation
- 7-day trial period before requiring activation
- All core features available within universe limit

**LICENSED Version (512 Universes)**
- Full 512 universes (U0-U511 = 261,632 DMX channels)
- Professional-grade for large venues and commercial use
- Perpetual license (hardware-bound, offline validation)
- Art-Net full specification support (Net 0-7, Subnet 0-15, Universe 0-15)

### 2. Universe Limit Enforcement
**License Manager (`src/utils/license.py`)**
- Added `get_max_universes()` → Returns 4 (FREE) or 512 (LICENSED)
- Added `get_license_tier()` → Returns "FREE" or "LICENSED"
- Added `validate_universe(universe)` → Validates if universe is within limit

**Art-Net Controller (`src/artnet/controller.py`)**
- Send/Receive validation: Blocks universes beyond license limit
- PollReply optimization: Sends 1 reply (FREE) or 128 replies (LICENSED)
- Auto-adjusts universe mapping based on license tier
- Logs license status on startup

**Serial Controller (`src/serial/serial_controller.py`)**
- Validates universe before sending to IOBoard
- Silently drops DMX data for universes beyond limit
- License check on initialization

**DMX Recorder (`src/show/dmx_recorder.py`)**
- Recording: Drops frames for universes beyond limit
- Playback: Skips frames for universes beyond limit
- Transparent operation (no errors shown to user)

### 3. GUI Updates
**Main Window (`src/gui/main_window.py`)**
- Status bar shows license tier: `🆓 FREE Version - 4 Universes` or `✓ LICENSED - 512 Universes`
- Auto-updates on license activation (no restart required for display)

**DMX View Tab (`src/gui/tabs/dmx_view.py`)**
- Universe dropdown auto-adjusts to license limit (0-3 or 0-511)
- Tooltip shows license tier and max universes
- Cannot select universes beyond limit

### 4. Art-Net PollReply Enhancement
**Multi-Packet Broadcast (LICENSED Version)**
- Sends 128 PollReply packets (4 universes each = 512 total)
- Subnet-based mapping for compatibility with Depence/Resolume/MADRIX
- Each packet reports correct SwIn for 4 consecutive universes
- Formula: `Universe = (Subnet << 4) | SwIn`

**Example Mapping:**
```
Packet 1:  Subnet 0, SwIn [0,1,2,3]   → Universe 0-3
Packet 2:  Subnet 0, SwIn [4,5,6,7]   → Universe 4-7
Packet 33: Subnet 2, SwIn [0,1,2,3]   → Universe 32-35
Packet 128: Subnet 7, SwIn [12,13,14,15] → Universe 508-511
```

---

## 📝 Technical Details

### License Validation Flow
1. **On Startup**: Load license from `config/license.lic` (AES-encrypted)
2. **Offline Validation**: RSA-2048 signature + hardware ID check
3. **Universe Limit**: Query `get_max_universes()` from license manager
4. **Runtime Enforcement**: Validate at all output layers:
   - Art-Net send/receive
   - Serial DMX output
   - Recording frames
   - Playback frames

### Security Measures
- ✅ **Hardware Binding**: License tied to MAC + CPU Serial (SHA-256 hash)
- ✅ **RSA Signatures**: Cannot forge license without private key
- ✅ **AES Encryption**: Cannot edit license file
- ✅ **Multi-layer Validation**: Enforced at controller, recorder, player, serial
- ✅ **No Bypass**: UI and backend both check license

### Performance Impact
- **FREE Version**: No performance impact (single PollReply packet)
- **LICENSED Version**: Minimal impact (128 PollReply packets on startup only)
- **Recording/Playback**: No overhead (validation is O(1) lookup)

---

## 🔧 Files Modified

### Core License System
- `src/utils/license.py` (+65 lines)
  - `get_max_universes()` method
  - `get_license_tier()` method
  - `validate_universe()` method

### Art-Net Controller
- `src/artnet/controller.py` (+45 lines)
  - License manager integration in `__init__`
  - Universe validation in `send_dmx()`, `send_dmx_with_mapping()`, `_handle_dmx_packet()`
  - PollReply count based on `_max_universes` (1 or 128 packets)

### Serial Controller
- `src/serial/serial_controller.py` (+18 lines)
  - License manager integration in `__init__`
  - Universe validation in `send_dmx()`

### Show Recording/Playback
- `src/show/dmx_recorder.py` (+30 lines)
  - License manager integration in `DMXRecorder.__init__` and `DMXPlayer.__init__`
  - Universe validation in `write_frame()` (recording)
  - Universe validation in `get_next_frame()` (playback)

### GUI
- `src/gui/main_window.py` (+25 lines)
  - License status label in status bar
  - `_update_license_status_label()` method
- `src/gui/tabs/dmx_view.py` (+15 lines)
  - Universe dropdown population based on license tier
  - Tooltip shows license tier

### Documentation
- `LICENSE_TIERS.md` (NEW, 300 lines)
  - Complete guide to FREE vs LICENSED versions
  - Feature comparison table
  - Upgrade instructions
  - Technical implementation details
- `README.md` (modified)
  - Updated version to 1.3.0
  - Added license tiers section
  - Updated feature list

---

## 🧪 Testing Recommendations

### FREE Version Testing
1. ✅ Start application → Status bar shows "FREE Version - 4 Universes"
2. ✅ DMX View → Universe dropdown shows 0-3 only
3. ✅ Try sending Universe 4+ → Should be blocked (logged)
4. ✅ Record show with Universe 0-3 → Should work
5. ✅ Play show with Universe 4+ frames → Should skip frames silently
6. ✅ IOBoard Board #2 (U2-U3) → Should be blocked

### LICENSED Version Testing
1. ✅ Activate license → Status bar shows "LICENSED - 512 Universes"
2. ✅ DMX View → Universe dropdown shows 0-511
3. ✅ Send Universe 0-511 → Should work
4. ✅ Record show with all 512 universes → Should work
5. ✅ Play show with 512 universes → Should work
6. ✅ Art-Net Poll → Should receive 128 PollReply packets
7. ✅ IOBoard multiple boards → All boards should work

### Edge Cases
- ✅ Switch from FREE → LICENSED without restart
- ✅ Invalid license file → Default to FREE (4 universes)
- ✅ Corrupted license → Default to FREE with warning
- ✅ Universe 511 → Should work in LICENSED, blocked in FREE

---

## 📊 Metrics

### Code Changes
- **8 files modified** (license.py, controller.py, serial_controller.py, dmx_recorder.py, main_window.py, dmx_view.py)
- **2 files created** (LICENSE_TIERS.md, CHANGELOG_v1.3.0.md)
- **~198 lines added** (excluding documentation)
- **0 lines removed** (backward compatible)

### Feature Coverage
- ✅ License tier detection (FREE/LICENSED)
- ✅ Universe validation (Art-Net, Serial, Recording, Playback)
- ✅ GUI updates (status bar, universe dropdown)
- ✅ PollReply optimization (1 or 128 packets)
- ✅ Documentation (LICENSE_TIERS.md, README.md)

---

## 🚀 Upgrade Path

### For Existing Users (v1.2.x → v1.3.0)
1. **Backup** current installation
2. **Install** v1.3.0 (overwrites existing)
3. **First launch** → Defaults to FREE version (4 universes)
4. **Activate license** → Unlock 512 universes
5. **Verify** status bar shows correct tier

### For New Users
1. **Install** v1.3.0
2. **Trial mode** → 7 days full FREE version
3. **After trial** → FREE version (4 universes) continues working
4. **Purchase license** → Upgrade to 512 universes anytime

---

## 🐛 Known Issues
- None reported

---

## 📮 Feedback

Please report issues or suggestions:
- **GitHub Issues**: https://github.com/truongcongdinh97/DMX-Master/issues
- **Email**: [Your Email]

---

**DMX Master LTS v1.3.0** - Professional Art-Net Lighting Controller with License Tiers
Released: 2025-11-09
