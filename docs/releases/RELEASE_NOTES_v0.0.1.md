# DMX Master LTS v0.0.1 - Release Notes

**Release Date:** March 10, 2026  
**Version:** 0.0.1  
**Status:** Early Release / Beta

---

## 🎉 What's New in V0.0.1

### ✨ Major Feature: Network Adapter Selection (V2.1)

#### Problem Solved
Recording chỉ hoạt động với broadcast (255.255.255.255), không nhận unicast từ Depence.

**Root Cause:** Windows UDP socket binding to 0.0.0.0 chỉ nhận broadcast, không nhận unicast packets.

#### Solution Implemented
- ✅ **Network Adapter Selection UI** trong Settings → System tab
- ✅ **Dynamic Adapter Detection** - Tự động phát hiện tất cả available adapters
- ✅ **Bind to Specific Interface** - Bind socket vào adapter cụ thể (không 0.0.0.0)
- ✅ **Dual Socket Support** - Primary socket + secondary loopback socket (127.0.0.1)
- ✅ **Config Persistence** - Lựa chọn được lưu vào config json

#### How to Use
1. Mở **Settings** → Chọn tab **System**
2. Tìm group **"Network Adapter Selection (V2.1)"**
3. Chọn adapter từ combobox (VD: Ethernet, WiFi, Loopback, Broadcast)
4. IP của adapter được chọn hiển thị realtime
5. Click **"Save Settings"** → Popup yêu cầu restart
6. Restart app → Binding được apply
7. Test recording hoặc hardware manager → Devices được discover từ adapter đó

#### Technical Details
```
Windows UDP Socket Fix:
- Trước: socket.bind(("0.0.0.0", 6454)) → Chỉ nhận broadcast
- Sau:  socket.bind(("192.168.1.13", 6454)) → Nhận cả broadcast + unicast

Secondary Socket:
- Nếu primary adapter ≠ 127.0.0.1, tạo second socket trên loopback
- Purpose: Support Depence running trên same machine

Auto-detect:
- Nếu user chọn "0.0.0.0" hoặc "auto", app tự detect primary interface
- Method: socket.connect() trick (non-intrusive, không send packets)
```

### 📄 New Files Added
- `src/utils/network_utils.py` - Network adapter utilities (80 lines)
- `DMXMaster-LTS-0.0.1.spec` - PyInstaller spec file for v0.0.1

### 📋 Modified Files
- `src/gui/tabs/settings.py` - Added Network Adapter Selection group to System tab
- `src/artnet/controller.py` - Bind to specific adapter instead of 0.0.0.0
- `src/gui/main_window.py` - Load bind_ip from config during initialization
- `build_windows.py` - Updated VERSION to 0.0.1
- `main.py` - Updated app version to 0.0.1
- `ArtNetController.iss` - Updated installer config to v0.0.1

### 📚 Documentation Added
- `HUONG_DAN_CHON_NETWORK_ADAPTER_V2_1.md` - Vietnamese user guide
- `FEATURE_NETWORK_ADAPTER_V2_1.md` - Feature overview
- `TECHNICAL_ARCHITECTURE_NETWORK_ADAPTER_V2_1.md` - Deep technical docs
- `UI_LAYOUT_NETWORK_ADAPTER_V2_1.md` - UI/UX mockups

---

## ✅ Installation

### Các yêu cầu hệ thống
- **OS:** Windows 10 / 11 (64-bit)
- **Python:** 3.10+ (nếu chạy from source)
- **Network:** Kết nối mạng hoặc loopback adapter
- **Admin Rights:** Yêu cầu để cài đặt và chạy

### Cài đặt từ Installer
1. Download: `DMX-Master-LTS-0.0.1-Setup.exe`
2. Double-click để chạy installer
3. Theo hướng dẫn installation wizard
4. Chọn destination folder (default: Program Files)
5. Chọn create desktop shortcut (tuỳ chọn)
6. Kết thúc installation

### Cài đặt từ Portable EXE
1. Download: `DMXMaster-LTS-0.0.1.exe`
2. Copy folder chứa executable vào vị trí muốn
3. Double-click để chạy trực tiếp (không cần installation)
4. Portable mode: Config được lưu vào %APPDATA%\DMX Master LTS

### First Run
1. Khởi động ứng dụng
2. Nếu yêu cầu, đăng nhập hoặc skip
3. Có thể cần admin privileges lần đầu
4. Vào Settings → System → chọn Network Adapter
5. Restart app để apply settings

---

## 🔧 Configuration

### Network Adapter Selection

#### Available Options
```
✓ Ethernet (<IP thực tế>)  - Card mạng vật lý chính
  WiFi (<IP thực tế>)      - WiFi adapter (nếu có)
  Loopback (127.0.0.1)     - Local machine communication
  Broadcast (0.0.0.0)      - Legacy broadcast mode (Windows limitation)
```

#### Config File Location
```
%LOCALAPPDATA%\DMX Master LTS\config\app_config.json

{
  "artnet": {
    "port": 6454,
    "bind_ip": "192.168.1.13"  // Selected adapter IP
  }
}
```

#### Recommended Setup

**Depence on Same Machine:**
- Select: Loopback (127.0.0.1)
- Depence config: Output → Loopback / 127.0.0.1

**Depence on LAN (Recommended):**
- Select: Ethernet (<adapter IP>)
- Depence config: Output → Unicast to adapter IP
- Example: Ethernet (192.168.1.13) → Depence sends to 192.168.1.13

**Resolume / Media Servers:**
- Select: Broadcast (0.0.0.0) or specific adapter
- Note: Broadcast mode has Windows limitation (may only receive broadcast, not unicast)

---

## 🧷 Known Limitations & Workarounds

### Limitation 1: Windows UDP Binding
**Issue:** Binding to 0.0.0.0 on Windows only receives broadcast, not unicast.

**Workaround:** Select specific adapter instead of Broadcast mode.

**Status:** ✅ Fixed in v0.0.1 by introducing adapter selection.

### Limitation 2: Requires Restart After Adapter Change
**Issue:** Socket binding happens at startup, not hotswappable.

**Workaround:** Close and restart application.

**Reason:** UDP sockets must be recreated to change binding address.

**Future:** May implement hot-swap in v1.0.0.

### Limitation 3: Depence Unicast Configuration
**Issue:** Depence must be explicitly configured for unicast mode.

**Workaround:** In Depence settings, set "Output Mode" to "Unicast" and specify target IP.

**Note:** Default Depence mode is often broadcast-only.

---

## 🚀 Getting Started

### Quick Start: Record from Depence (Unicast)

**Steps:**
1. **Depence Setup:**
   - Open Depence 3D
   - Go to Output Settings → Art-Net
   - Set Mode to **Unicast**
   - Set Target IP to **192.168.1.13** (your adapter IP)
   - Enable output

2. **DMX Master Setup:**
   - Open DMX Master LTS
   - Settings → System → Network Adapter Selection
   - Select **Ethernet (192.168.1.13)**
   - Click **Save Settings** → Restart app

3. **Start Recording:**
   - Open **Record** tab
   - Click **"Start Recording"**
   - In Depence: Click **Play**
   - DMX data should appear in Recording

4. **Verify:**
   - Open **Hardware Manager** tab
   - Click **"Ping Device"** → Should find device
   - Or check **DMX View** tab → Channels should show values

---

## 📊 Build Information

**Build Date:** March 10, 2026  
**Build Tool:** PyInstaller 6.16.0  
**Python Version:** 3.13.7  
**PyQt6 Version:** 6.x  
**Installer Tool:** Inno Setup 6.5.4  

**Build Artifacts:**
- Executable: `DMXMaster-LTS-0.0.1.exe` (244 MB)
- Installer: `DMX-Master-LTS-0.0.1-Setup.exe` (240 MB)

---

## 📞 Support & Feedback

### Issues
- Recording still not working? → Check adapter selection matches Depence output IP
- Hardware Manager shows no devices? → Verify firewall allows port 6454
- Permission errors? → Run as Administrator
- Crash on startup? → Check antivirus (may block PyInstaller-compiled executables)

### Troubleshooting

```powershell
# Check which process is binding port 6454
netstat -ano | findstr 6454

# Check firewall rules for port 6454
netsh advfirewall firewall show rule name=all | findstr 6454

# Check network adapters
ipconfig /all
```

### Contact
- Report Issues: GitHub Issues (if available)
- Email: truongcongdinh97@gmail.com
- Phone: (Vietnamese customer support available)

---

## 📝 Version History

**v0.0.1 (March 10, 2026)** - Initial Release
- Network Adapter Selection feature
- Windows UDP socket fix
- Dual socket support (primary + loopback)

**Previous: v1.3.0 (November 9, 2025)**
- License Tiers System (FREE/LICENSED)
- Hardware-bound license validation

**Previous: v1.2.0**
- IOBoard Serial Integration

**Previous: v1.1.x**
- Various UI/UX improvements

---

## ⚖️ License

DMX Master LTS v0.0.1 is distributed under:
- **FREE Tier:** 4 universes max (no registration required)
- **LICENSED Tier:** 512 universes (requires license key)

See LICENSE.txt for full license details.

---

**© 2026 Cong Dinh Truong**  
**All Rights Reserved**

---

## Checklist for End User

- [ ] Downloaded installer or executable
- [ ] Windows 10/11 (64-bit) system
- [ ] Administrator account available
- [ ] Network adapter visible in Network Settings
- [ ] Depence configured for Unicast (if applicable)
- [ ] Firewall allows port 6454
- [ ] App started successfully
- [ ] Settings → System → Network Adapter visible
- [ ] Recording test passed
- [ ] Hardware Manager shows devices

---

**Thank You for Using DMX Master LTS v0.0.1!**

For updates and new releases, check: https://github.com/truongcongdinh97/DMX-Master
