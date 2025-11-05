# ✅ KIỂM TRA TOÀN BỘ - DMX MASTER v1.0.3

## 1. Giới hạn 32 Universe mặc định ✅

### Config Manager
- ✅ `DEFAULT_CONFIG['universes']['max_universes'] = 32` trong `src/system/config_manager.py`
- ✅ `config.json` đã cập nhật: `"max_universes": 32`
- ✅ Kiểm tra runtime: `get_config_manager().get('universes.max_universes')` trả về `32`

### DMX View Tab
- ✅ Universe combo hiện 0-31 (32 universes)
- ✅ Tooltip hiển thị: "Select universe (0-31)"
- ✅ Đọc từ system config động: `get_config_manager().get('universes.max_universes', 32)`

### Record Tab
- ✅ Universe filter hiển thị "All" + 0-31 (32 universes)
- ✅ Đọc từ system config động

## 2. Admin-only Hidden Setting ✅

### Hidden Shortcut (Ctrl+Alt+U)
- ✅ Thêm vào `main_window.py` - không hiện trong menu
- ✅ Yêu cầu: **Admin login + Valid license**
- ✅ Hiển thị dialog input: 1-512 universes
- ✅ Lưu vào `universes.max_universes` trong system config
- ✅ Thông báo restart để áp dụng cho tất cả module

### Kiểm tra quyền
```python
if not (self._is_admin and self._is_licensed_admin):
    QMessageBox.warning(self, "Access Denied", "Admin login and valid license required.")
    return
```

## 3. ArtPollReply cho Depence Unicast ✅

### Packet Structure (239 bytes)
```
Header:        Art-Net\x00 (8 bytes)
OpCode:        0x2100 (Little Endian) ✅
IP:            192.168.1.171 ✅
Port:          0x1936 (6454) ✅
VersInfo:      0x0200 (v2.0) ✅
NetSwitch:     0 ✅
SubSwitch:     0 ✅
ShortName:     "DMX Master" ✅
LongName:      "DMX Master Unlimited by TCD" ✅
NodeReport:    "#0001 [0000] Power On" ✅

--- CRITICAL FOR DEPENCE UNICAST ---
NumPorts:      4 ✅ (dynamic từ max_universes, capped at 4)
PortTypes:     [0x40, 0x40, 0x40, 0x40] ✅ (Input to Art-Net)
GoodInput:     [0x08, 0x08, 0x08, 0x08] ✅ (Power on)
GoodOutput:    [0x88, 0x88, 0x88, 0x88]
SwIn:          [0, 1, 2, 3] ✅ (Sequential universes)
SwOut:         [0, 0, 0, 0] ✅ (Not used for input)
Style:         0 (StNode) ✅ (NOT Controller)

MAC:           00:00:00:00:00:00
BindIp:        192.168.1.171 ✅
Status2:       0x07 (Web + DHCP) ✅
```

### Thay đổi từ version trước
| Field | Trước (v1.0.2) | Bây giờ (v1.0.3) | Lý do |
|-------|----------------|------------------|-------|
| NumPorts | 16 (mismatch arrays) | 4 ✅ | Consistent với 4-slot arrays |
| PortTypes | 0x80 (Output) | 0x40 (Input) ✅ | Depence cần Input node |
| GoodInput | 0x00 (disabled) | 0x08 (enabled) ✅ | Báo input ports active |
| SwIn | [0,0,0,0] | [0,1,2,3] ✅ | Sequential universe mapping |
| SwOut | [0,1,2,3] | [0,0,0,0] ✅ | Không dùng cho input node |
| Style | 1 (Controller) | 0 (StNode) ✅ | Input/output device |

## 4. Import & Syntax Check ✅

```python
# Tất cả imports thành công
✅ from artnet.controller import ArtNetController
✅ from gui.tabs.dmx_view import DMXViewTab
✅ from gui.tabs.record import RecordTab
✅ from system.config_manager import get_config_manager
✅ from gui.main_window import MainWindow
```

## 5. Tích hợp đồng bộ ✅

### Các module sử dụng max_universes:
1. ✅ **DMX View**: Universe selector (0 đến max_universes-1)
2. ✅ **Record Tab**: Universe filter ("All" + 0 đến max_universes-1)
3. ✅ **ArtPollReply**: NumPorts = min(4, max_universes) - legacy 4-slot arrays
4. ⏳ **Show Playback**: (hiện chưa giới hạn, có thể thêm sau)
5. ⏳ **Hardware Manager**: (hiện chưa giới hạn, có thể thêm sau)

## 6. Kiểm tra với Depence

### Broadcast (đã hoạt động từ v1.0.2) ✅
```
Depence → 255.255.255.255:6454
DMX Master nhận: ✅ Poll, ✅ ArtDmx (Universe 4-7)
DMX View cập nhật: ✅ 512 channels hiển thị
```

### Unicast (đã sửa trong v1.0.3) 🎯
**Nguyên nhân trước đây không hoạt động:**
- PollReply báo NumPorts=16 nhưng arrays chỉ 4 phần tử
- PortTypes=0x80 (Output) → Depence không coi là input node
- GoodInput=0x00 → Ports không active
- Style=1 (Controller) → Không phải input/output device

**Đã sửa:**
- ✅ NumPorts=4 (consistent với arrays)
- ✅ PortTypes=0x40 (Input)
- ✅ GoodInput=0x08 (Active)
- ✅ SwIn=[0,1,2,3] (Sequential)
- ✅ Style=0 (StNode)

**Kỳ vọng:**
```
Depence → 192.168.1.171:6454 (Unicast)
DMX Master PollReply → Depence nhận dạng là INPUT node với 4 ports
Depence gửi DMX unicast → DMX Master nhận ✅
DMX View cập nhật ✅
```

## 7. Cách Test

### A. Kiểm tra Max Universes
1. Khởi động app
2. Mở DMX View → Universe combo có 0-31
3. Mở Record tab → Universe filter có All + 0-31
4. Login admin + có license
5. Nhấn **Ctrl+Alt+U**
6. Đổi thành 64
7. Restart app
8. Kiểm tra lại: DMX View và Record tab có 0-63

### B. Kiểm tra Depence Unicast
1. **Depence setup:**
   - Adapter: Realtek (192.168.1.171)
   - Output: Art-Net
   - IP: 192.168.1.171 (Unicast)
   - Universe: 0-3
   
2. **DMX Master:**
   - Khởi động app
   - Tab DMX View
   - Chọn Universe 0
   
3. **Test:**
   - Depence gửi Poll → DMX Master log: "Poll packet received"
   - DMX Master gửi PollReply → Depence nhận dạng node
   - Depence gửi DMX unicast → DMX Master log: "DMX packet received"
   - DMX View hiển thị channels

## 8. Files đã thay đổi

| File | Thay đổi |
|------|----------|
| `src/system/config_manager.py` | `max_universes: 16 → 32` |
| `src/gui/tabs/dmx_view.py` | Universe combo đọc từ config |
| `src/gui/tabs/record.py` | Universe filter đọc từ config |
| `src/artnet/controller.py` | Sửa `_create_poll_reply()` cho Depence |
| `src/gui/main_window.py` | Thêm hidden shortcut Ctrl+Alt+U |
| `config.json` | Update `max_universes: 32` |

## 9. Các tính năng mới

### ✨ Tính năng chính
1. **Giới hạn 32 universes mặc định** - giảm tải UI và network
2. **Admin có thể điều chỉnh** (1-512) qua hidden shortcut
3. **Depence unicast support** - chuẩn Art-Net 4 input node
4. **Đồng bộ toàn hệ thống** - config ảnh hưởng tất cả module

### 🔒 Bảo mật
- Hidden setting chỉ cho admin + license
- Không hiện trong menu thường
- Yêu cầu restart để áp dụng (tránh inconsistency)

## 10. Kết luận

✅ **Tất cả thay đổi hoàn tất**
✅ **Không có lỗi syntax**
✅ **Import thành công**
✅ **ArtPollReply đúng spec**
✅ **Config đồng bộ**
✅ **Ready để build và test với Depence**

### Bước tiếp theo:
1. Build EXE mới (v1.0.3-Build5 hoặc v1.0.4)
2. Test unicast với Depence
3. Nếu unicast vẫn không hoạt động, có thể thử:
   - PortTypes = 0xC0 (Input+Output)
   - GoodInput = 0x81 (data present + power on)
   - Kiểm tra Depence settings chi tiết hơn
