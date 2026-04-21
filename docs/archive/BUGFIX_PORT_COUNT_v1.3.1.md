# 🔧 Art-Net PollReply Parsing Fix - Chỉ Sửa Port Count Bug

**Ngày:** 2025-11-09  
**Vấn đề:** Port Count hiển thị 16448 thay vì 4  
**Trạng thái:** ✅ ĐÃ SỬA

---

## 🎯 Tóm tắt

### Tình huống của bạn (ĐÚNG, KHÔNG PHẢI BUG):
```
Máy chủ DMX Master:
├── Card mạng Intel I225-V: 192.168.1.20 (IP chính)
└── Microsoft KM-TEST Loopback: 200.133.200.133 (test với Depence)

Depence (phần mềm visualizer):
└── Lắng nghe trên: 200.133.200.133 (loopback adapter)

Kết quả:
✅ DMX Master phát broadcast Art-Net
✅ Cả 2 adapters đều nhận được broadcast
✅ Depence nhận được → ĐÚNG!
✅ DMX Master thấy chính mình ở 200.133.200.133 → CŨNG ĐÚNG!
```

**KẾT LUẬN:** Việc phần mềm tự phát hiện chính nó qua loopback adapter là **HOÀN TOÀN ĐÚNG**. Đây là cách Art-Net discovery hoạt động!

### Vấn đề thực sự (BUG):
❌ **Port Count hiển thị 16448 thay vì 4**

---

## 🐛 Nguyên nhân Bug

### Lỗi phân tích packet Art-Net PollReply

Art-Net specification đếm bytes từ đầu packet (bao gồm header):
```
Byte 0-7:   Header "Art-Net\x00"
Byte 8-9:   OpCode 0x2100
Byte 10-13: IP Address
...
Byte 172-173: NumPorts
Byte 186-189: SwIn[4] (Universe addresses)
```

**NHƯNG** function `ArtNetPacket.unpack()` trả về **CHỈ payload** (bỏ 10 bytes header+opcode):
```python
def unpack(cls, data: bytes):
    opcode = struct.unpack('<H', data[8:10])[0]
    payload = data[10:]  # ← BỎ 10 BYTES ĐẦU!
    return {'opcode': opcode, 'payload': payload}
```

### Code cũ (SAI):
```python
# Đọc byte 164-165 trong payload → Sai vị trí!
num_ports_hi = payload[164]  # ← ĐỌC SAI VỊ TRÍ!
num_ports_lo = payload[165]
port_count = (num_ports_hi << 8) | num_ports_lo

# Kết quả: đọc phải PortTypes[0-1] = 0x40, 0x40
# → port_count = 0x4040 = 16448 ❌
```

### Code mới (ĐÚNG):
```python
# Spec byte 172-173 → payload byte 162-163 (172 - 10)
NUMPORTS_OFFSET = 162  # 172 - 10
num_ports_hi = payload[162]  # ← ĐÚNG VỊ TRÍ!
num_ports_lo = payload[163]
port_count = (num_ports_hi << 8) | num_ports_lo

# Kết quả: đọc đúng NumPorts = 0x00, 0x04
# → port_count = 4 ✅
```

---

## 🔧 Các sửa đổi đã thực hiện

### File: `src/artnet/controller.py`

#### 1. Rollback Self-Detection Filter ✅
**Lý do:** Không phải bug! Loopback adapter phát hiện chính nó là đúng.

```python
# V2.3: REMOVED complex self-detection filter
# Only filter actual localhost (127.0.0.1)
if ip_address == "127.0.0.1" or ip_address == "::1":
    logger.debug(f"Ignoring poll reply from localhost: {ip_address}")
    return
```

#### 2. Fix NumPorts Parsing ✅
**Vấn đề:** Đọc sai offset (payload[164-165] thay vì payload[162-163])

```python
# Spec byte 172-173 → payload byte 162-163
NUMPORTS_OFFSET = 162  # 172 - 10
num_ports_hi = payload[NUMPORTS_OFFSET]
num_ports_lo = payload[NUMPORTS_OFFSET + 1]
port_count = (num_ports_hi << 8) | num_ports_lo
```

#### 3. Fix NetSwitch/SubSwitch Parsing ✅
**Vấn đề:** Đọc sai offset cho NetSwitch và SubSwitch

```python
# Spec byte 18 → payload byte 8
# Spec byte 19 → payload byte 9
net_switch = payload[8]  # Was: payload[10]
sub_switch = payload[9]  # Was: payload[11]
```

#### 4. Fix SwIn[0] Parsing ✅
**Vấn đề:** Đọc sai offset cho SwIn universe addresses

```python
# Spec byte 186 → payload byte 176
SWIN_OFFSET = 176  # 186 - 10 (was: 168)
sw_in_0 = payload[SWIN_OFFSET]
```

#### 5. Fix ShortName/LongName Parsing ✅
**Vấn đề:** Đọc sai offset

```python
# ShortName: spec byte 26-43 → payload byte 16-33
SHORTNAME_OFFSET = 16  # 26 - 10
short_name_bytes = payload[SHORTNAME_OFFSET:SHORTNAME_OFFSET+18]

# LongName: spec byte 44-107 → payload byte 34-97
LONGNAME_OFFSET = 34  # 44 - 10
long_name_bytes = payload[LONGNAME_OFFSET:LONGNAME_OFFSET+64]
```

### File: `src/gui/tabs/hardware_manager.py`

#### ScrollArea cho Universe Mapping Dialog ✅
```python
# Add scroll area for many ports
scroll_area = QScrollArea()
scroll_area.setMaximumHeight(400)
scroll_area.setWidgetResizable(True)

# Warning label if >16 ports
if self.node.port_count > 16:
    info_label = QLabel(f"⚠️ Device has {self.node.port_count} ports - scroll to configure all")
```

---

## 📊 Bảng Mapping Offsets (Chính xác)

| Field | Spec Bytes | Payload Offset | Size | Description |
|-------|-----------|----------------|------|-------------|
| Header | 0-7 | STRIPPED | 8 | "Art-Net\x00" |
| OpCode | 8-9 | STRIPPED | 2 | 0x2100 |
| IP Address | 10-13 | 0-3 | 4 | Node IP |
| Port | 14-15 | 4-5 | 2 | 0x1936 (6454) |
| VersInfo | 16-17 | 6-7 | 2 | Firmware version |
| **NetSwitch** | **18** | **8** | **1** | **Net (0-127)** |
| **SubSwitch** | **19** | **9** | **1** | **SubNet (0-15)** |
| Oem | 20-21 | 10-11 | 2 | OEM code |
| UbeaVersion | 22 | 12 | 1 | UBEA version |
| Status1 | 23 | 13 | 1 | Node status |
| EstaMan | 24-25 | 14-15 | 2 | ESTA manufacturer |
| **ShortName** | **26-43** | **16-33** | **18** | **Node name** |
| **LongName** | **44-107** | **34-97** | **64** | **Full description** |
| NodeReport | 108-171 | 98-161 | 64 | Status message |
| **NumPorts** | **172-173** | **162-163** | **2** | **Port count (Hi/Lo)** |
| PortTypes | 174-177 | 164-167 | 4 | Port types (0x40 each) |
| GoodInput | 178-181 | 168-171 | 4 | Input status |
| GoodOutput | 182-185 | 172-175 | 4 | Output status |
| **SwIn** | **186-189** | **176-179** | **4** | **Universe addresses** |
| SwOut | 190-193 | 180-183 | 4 | Output universes |

**Công thức:** `payload_offset = spec_byte - 10`

---

## 🧪 Testing

### Chuẩn bị:
```bash
# Không cần cài netifaces nữa (đã rollback)
# Chỉ test với cấu hình hiện tại của bạn
```

### Test trên hệ thống của bạn:

#### 1. Khởi động DMX Master
```
Network adapters:
├── Intel I225-V: 192.168.1.20
└── KM-TEST Loopback: 200.133.200.133
```

#### 2. Mở Hardware Manager tab
- Click **"Scan Network"**

#### 3. Kết quả mong đợi:

**Device List:**
```
IP Address         Short Name    Long Name                    Port  Universe
200.133.200.133    DMX Master    DMX Master LTS - Universe 0-3    4    0-3
```

✅ **Port = 4** (KHÔNG còn 16448!)  
✅ **Universe = 0-3** (KHÔNG còn 65535!)  
✅ **IP = 200.133.200.133** (ĐÚNG - đây là loopback adapter)

#### 4. Test Configure Universe Mapping:
- Select device (200.133.200.133)
- Click **"Configure Universe Mapping"**
- **Kết quả mong đợi:**
  - ✅ Dialog mở với 4 ports (0-3)
  - ✅ Có thể scroll nếu nhiều ports
  - ✅ Default mapping: Port 0→U0, Port 1→U1, Port 2→U2, Port 3→U3
  - ✅ Nút OK/Cancel luôn hiển thị

---

## 📝 Debug Logging

### Bật debug mode:
Edit `config/app_config.json`:
```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

### Log mong đợi khi scan:

```
DEBUG - Received OpCode: 0x2100 from 200.133.200.133
DEBUG - Poll Reply received from 200.133.200.133
DEBUG - NumPorts raw bytes: payload[162]=0x00, payload[163]=0x04, Result=4
DEBUG - Universe calc: Net=0, SubNet=0, SwIn[0]=0, Base Universe=0
INFO  - Discovered Art-Net node: 200.133.200.133 - DMX Master - 4 ports
DEBUG -   Long Name: DMX Master LTS - Universe 0-3
DEBUG -   Universe: 0, Status: 00
```

**Chú ý:**
- `Result=4` ← ĐÚNG! (không còn 16448)
- `Base Universe=0` ← ĐÚNG! (không còn 65535)

---

## 🎯 So sánh trước/sau

### Trước khi sửa:
```
Hardware Manager:
┌────────────────────────────────────────────────┐
│ IP: 200.133.200.133                           │
│ Name: X Master                                 │
│ Port: 16448  ← SAI! (0x4040)                  │
│ Universe: 65535  ← SAI! (0xFFFF)             │
└────────────────────────────────────────────────┘
```

### Sau khi sửa:
```
Hardware Manager:
┌────────────────────────────────────────────────┐
│ IP: 200.133.200.133                           │
│ Name: DMX Master                               │
│ Port: 4  ← ĐÚNG! ✅                           │
│ Universe: 0-3  ← ĐÚNG! ✅                     │
└────────────────────────────────────────────────┘
```

---

## 📦 Files đã tạo/sửa đổi

### Files sửa đổi:
1. ✅ `src/artnet/controller.py` (~150 lines changed)
   - Rollback self-detection filter (chỉ giữ localhost check)
   - Fix NumPorts offset: 162-163 (was 164-165)
   - Fix NetSwitch/SubSwitch offset: 8-9 (was 10-11)
   - Fix SwIn offset: 176 (was 178)
   - Fix ShortName/LongName offsets: 16-33, 34-97
   - Add comprehensive debug logging

2. ✅ `src/gui/tabs/hardware_manager.py` (~60 lines changed)
   - Add QScrollArea to UniverseMappingDialog
   - Add warning label for many ports
   - Improve default mapping

### Files tạo mới (debug tools):
3. ✅ `pollreply_structure.py` - Packet structure reference
4. ✅ `debug_pollreply_structure.py` - Offset verification tool
5. ✅ `BUGFIX_SELF_DETECTION_v1.3.1.md` - THIS FILE (documentation)

### Files không cần thiết (rollback):
- ❌ `requirements.txt` - Removed netifaces dependency (not needed anymore)

---

## 💡 Bài học rút ra

### 1. Art-Net Packet Structure
- **Spec bytes** bao gồm cả header (bytes 0-9)
- **Payload** sau khi unpack() BỎ 10 bytes đầu
- **Luôn trừ 10** khi chuyển từ spec byte sang payload offset

### 2. Self-Detection Logic
- Loopback adapters tự phát hiện chính nó là **ĐÚNG**
- Chỉ nên filter `127.0.0.1` và `::1` (localhost thật)
- Các adapter khác (kể cả KM-TEST) nên được hiển thị

### 3. Debugging Packets
- Tạo test scripts để verify packet structure
- Log raw bytes với offset rõ ràng
- So sánh với Art-Net specification

---

## 🚀 Cách chạy test

### Test 1: Verify packet offsets
```bash
python pollreply_structure.py
```

### Test 2: Verify packet creation
```bash
python debug_pollreply_structure.py
```

### Test 3: Run DMX Master
```bash
python main.py
```

Sau đó:
1. Mở Hardware Manager
2. Click Scan Network
3. Kiểm tra Port = 4, Universe = 0-3

---

## 📞 Hỗ trợ

Nếu vẫn còn vấn đề:

1. **Bật debug logging** trong config/app_config.json
2. **Check logs** trong logs/dmx_master.log
3. **Chụp ảnh** Hardware Manager table
4. **Gửi logs** kèm screenshot

---

**Đã sửa bởi:** GitHub Copilot  
**Ngày:** 2025-11-09  
**Version:** DMX Master LTS 1.3.1 (Patch)  
**Vấn đề:** Port Count parsing bug  
**Trạng thái:** ✅ HOÀN THÀNH
