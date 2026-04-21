## Network Adapter Selection Feature (V2.1)

### 概述 (Overview)
Cho phép người dùng chọn network adapter trên tab Settings → System, ảnh hưởng đến địa chỉ IP dùng để nhận Art-Net.

**Tính năng mới:**
- Danh sách combobox hiển thị tất cả available network adapters
- Hiển thị IP address của adapter được chọn
- Lưu lựa chọn vào config và apply khi khởi động lại app
- Support auto-detect primary interface hoặc specific adapter selection
- Ảnh hưởng đến Hardware Manager - chỉ hiển thị devices từ adapter được chọn

### Các File Đã Thay Đổi

#### 1. `src/utils/network_utils.py` (NEW)
Module mới cung cấp utilities để lấy network adapters:
- `get_network_adapters()`: Trả về dict {adapter_name: ip_address}
- `get_primary_ip()`: Auto-detect primary IP (non-loopback)
- `validate_ip_address()`: Validate IP string

```python
# Example usage:
from src.utils.network_utils import get_network_adapters
adapters = get_network_adapters()
# Returns: {
#   "Ethernet": "192.168.1.10",
#   "WiFi": "192.168.1.20",
#   "Loopback": "127.0.0.1",
#   "Broadcast": "0.0.0.0"
# }
```

#### 2. `src/gui/tabs/settings.py` (MODIFIED)
Thêm Network Adapter Selection group vào System tab:
- Combobox để chọn adapter: `self.network_adapter_combo`
- Label hiển thị IP: `self.adapter_ip_label`
- Signal handler: `on_adapter_changed()`
- Helper methods:
  - `_refresh_network_adapters()`: Populate combobox từ system
  - `_get_default_adapter_ip()`: Lấy default IP
  - `_update_adapter_ip_display()`: Update display label

**Load/Save Config:**
- Load: `artnet.bind_ip` từ config (V2.1)
- Save: Lưu selected adapter IP vào `artnet.bind_ip`

#### 3. `src/artnet/controller.py` (MODIFIED)
Cải thiện socket binding cho Windows:
- Nhận `bind_ip` parameter trong `__init__()`
- Support "auto" mode: auto-detect primary interface
- Support specific IP mode: bind to selected adapter
- Tạo second socket trên localhost (127.0.0.1) để support same-machine apps (Depence, Resolume)
- Cleanup loopback socket trong `stop()`

**Logic binding (Windows-specific fix):**
```python
# Windows: bind(0.0.0.0) only receives broadcast, not unicast
# Fix: Bind to specific IP để receive cả broadcast + unicast
if bind_ip == "0.0.0.0" or bind_ip == "auto":
    # Auto-detect primary IP
    bind_ip = detect_primary_interface()
elif bind_ip == "127.0.0.1":
    # Loopback only (local Depence/Resolume)
    pass
else:
    # Use specified adapter IP
    pass
```

#### 4. `src/gui/main_window.py` (MODIFIED)
Update ArtNetController initialization:
```python
def init_artnet_controller(self):
    bind_ip = self.config_manager.get_app_config('artnet.bind_ip', '0.0.0.0')
    self.artnet_controller = ArtNetController(bind_ip=bind_ip)
```

### User Workflow

1. **Mở Settings Tab**
   - Chọn "System" tab
   - Tìm "Network Adapter Selection (V2.1)" group

2. **Chọn Network Adapter**
   - Combobox hiển thị: `Ethernet (<IP thực tế>)`, `WiFi (<IP thực tế>)`, v.v.
   - Adapter IP label cập nhật realtime: hiển thị IP thế của adapter được chọn
   - Mô tả: "Selected adapter will receive incoming Art-Net packets"

3. **Lưu và Restart**
   - Click "Apply" hoặc "Save Settings"
   - Popup: "Settings have been saved successfully. Please restart the application for network adapter changes to take effect."
   - Restart app để apply

4. **Verify trong Hardware Manager**
   - Devices được discover từ selected adapter
   - IP addresses hiển thị matches selected adapter

### Config Storage
```json
{
  "artnet": {
    "port": 6454,
    "bind_ip": "<địa chỉ IP thực tế của adapter được chọn>"  // Thêm mới (V2.1)
  }
}
```

### Deployment Notes

**khách hàng có 2 NICs (Ethernet 192.168.1.13 + Loopback 169.254.114.170):**
1. Mở Settings → System
2. Chọn "Ethernet (192.168.1.13)" hoặc "Primary Network (auto-detect)"
3. Click Apply, restart app
4. Test recording từ Depence unicast (không phải broadcast 255.255.255.255)

**Benefits:**
- ✅ Recording works với unicast (Depence, Resolume)
- ✅ Device discovery works trên correct interface
- ✅ Support same-machine loopback (127.0.0.1)
- ✅ Config persisted across restarts
- ✅ User-friendly interface

### Technical Details

**Windows UDP Socket Behaviors:**
- `bind(0.0.0.0)`: Nhận broadcast NHƯNG không nhận unicast to specific IPs (khác Linux)
- `bind(specific_ip)`: Nhận cả broadcast + unicast trên interface đó
- `bind(127.0.0.1)`: Loopback only, không thể receive từ network

**Socket Options:**
```python
socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
```

**Secondary loopback socket:**
Nếu primary adapter không phải 127.0.0.1, tạo second socket trên loopback để support Depence running cùng machine.

### Testing Checklist
- [ ] Settings → System tab loads network adapters
- [ ] Adapter combobox display format: "Ethernet (192.168.1.10)"
- [ ] IP label updates khi chọn adapter khác
- [ ] Save/Apply lưu config
- [ ] Restart app loads saved adapter
- [ ] Hardware Manager discover devices từ correct interface
- [ ] Recording works với unicast IPs (test với Depence)
- [ ] Loopback adapter (127.0.0.1) option available

### Toàn Bộ Flow

```
User Settings → Network Adapter Selection
                        ↓
                  Save to config
                        ↓
                  Restart application
                        ↓
            ArtNetController.__init__(bind_ip=config)
                        ↓
         socket.bind((bind_ip, 6454))
            ↓                      ↓
      Broadcast            Unicast packets
         receive            received ✅
                        ↓
            Hardware Manager displays
            devices from adapter
```

### Future Enhancements
- [ ] Hot-swap network adapter (bez restart)
- [ ] Per-universe binding (advanced mode)
- [ ] Network interface statistics (bandwidth, packet loss)
- [ ] Auto-failover nếu adapter down
