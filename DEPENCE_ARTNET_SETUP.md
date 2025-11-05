# Hướng Dẫn Cấu Hình Depence Với DMX Master LTS

## 🎭 Cấu Hình Art-Net Trong Depence

### Bước 1: Mở Depence Art-Net Settings
1. Trong Depence, đi đến: **Interfaces → Art-Net Settings**
2. Hoặc nhấn **F8** để mở Interface Settings

### Bước 2: Cấu Hình Art-Net Output
```
✅ Enable Art-Net Output: BẬT
🎯 Target IP Address: 192.168.1.171 (hoặc 127.0.0.1)
🌍 Universe: 1 (Depence universe 1 = DMX Master universe 0)
📡 Port: 6454 (mặc định Art-Net)
```

⚠️ **QUAN TRỌNG - Universe Mapping:**
- **Depence Universe 1** → **DMX Master Universe 0**
- **Depence Universe 2** → **DMX Master Universe 1**
- **Depence Universe 3** → **DMX Master Universe 2**
- Depence không hỗ trợ Universe 0, bắt đầu từ Universe 1

### Bước 3: Cấu Hình Network
- **Broadcast Mode**: Thử cả hai tùy chọn
  - ✅ Unicast: `192.168.1.171` (IP cụ thể)
  - ✅ Broadcast: `255.255.255.255` (toàn mạng)

### Bước 4: Test DMX Output
1. **Tạo fixtures trong Depence:**
   - Thêm đèn LED hoặc moving light
   - Assign vào **Universe 1** (sẽ hiển thị như Universe 0 trong DMX Master)
   - Channels 1-10 trong Universe 1

2. **Test Manual Control:**
   - Mở Live Control hoặc Manual Faders
   - Di chuyển faders cho channels 1-10 trong **Universe 1**
   - Xem DMX View trong DMX Master (**Universe 0**)

3. **Test Sequence Playback:**
   - Tạo sequence đơn giản với **Universe 1**
   - Playback và kiểm tra DMX View (**Universe 0**)

## 🔧 Troubleshooting

### Nếu không nhận được DMX data:

1. **Kiểm tra Depence Settings:**
   ```
   ☐ Art-Net Output enabled?
   ☐ Target IP đúng (192.168.1.171)?
   ☐ Universe đúng (1 trong Depence = 0 trong DMX Master)?
   ☐ Có fixtures assigned trong universe 1?
   ☐ Faders/playback đang active?
   ```

2. **Kiểm tra Windows Firewall:**
   - Cho phép port 6454 UDP
   - Cho phép DMX Master application

3. **Test Network Connectivity:**
   ```powershell
   ping 192.168.1.171
   telnet 192.168.1.171 6454
   ```

4. **Alternative IP Settings:**
   - `127.0.0.1` (localhost)
   - `192.168.1.171` (machine IP)
   - `255.255.255.255` (broadcast)

## 📊 Xác Nhận Kết Nối

### Trong DMX Master LTS:
1. **Tab DMX View:**
   - Universe: 0 (nhận từ Depence Universe 1)
   - Các channels có giá trị khác 0
   - Update rate > 0 Hz

2. **Statistics:**
   - Active Channels > 0
   - Source: Art-Net (từ 192.168.1.171)
   - Last Update: gần đây

### Log Messages Thành Công:
```
✅ Art-Net controller started on 0.0.0.0:6454
📦 DMX packet received from 192.168.1.171
🔍 DMX Parse Debug: Universe=0, Length=512 (từ Depence Universe 1)
🔄 Calling DMX callback for Universe 0, 512 channels
✅ DMX callback completed successfully
```

## 🎯 Cấu Hình Tối Ưu

### Cho Performance Cao:
- **Update Rate**: 30-44 Hz
- **Universe Count**: Chỉ universe cần thiết
- **Channel Count**: 512 channels max per universe

### Cho Stability:
- **Target IP**: Sử dụng IP cụ thể thay vì broadcast
- **Network**: Gigabit Ethernet khuyến nghị
- **Firewall**: Tắt hoặc cho phép port 6454

## 🔍 Debug Commands

### Kiểm tra Art-Net Traffic:
```powershell
cd "h:\VSCode\ArtNetController"
python test_depence_artnet.py
```

### Test DMX Callback:
```powershell
python debug_dmx_parsing.py
```

### Test Loopback:
```powershell
python test_loopback_artnet.py
```

---

## 📝 Notes

- Cả Depence và DMX Master đang chạy trên cùng máy (192.168.1.171)
- Art-Net packets được parse đúng format sau khi fix
- DMX callback system hoạt động với data 512 bytes
- Poll packets từ Depence được nhận và reply thành công