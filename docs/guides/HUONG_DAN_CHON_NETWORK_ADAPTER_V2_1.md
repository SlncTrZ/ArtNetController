# Hướng Dẫn Chọn Network Adapter (V2.1)

## 🎯 Tính Năng Mới
Cho phép người dùng chọn network adapter (lựa chọn card mạng) để nhận tín hiệu Art-Net, giải quyết vấn đề recording chỉ hoạt động qua broadcast.

## 📍 Vị Trí Tính Năng
Settings Tab → **System** → **Network Adapter Selection (V2.1)**

## 🚀 Các Bước Sử Dụng

### Bước 1: Mở Settings
1. Nhấp menu Settings (tuỳ chỉnh)
2. Chọn tab **System**
3. Tìm group **"Network Adapter Selection (V2.1)"**

### Bước 2: Xem Danh Sách Adapter
Combobox hiển thị tất cả network adapters có sẵn:
```
✓ Ethernet (<địa chỉ IP thực tế>)    ← Card mạng cứng (VD: 192.168.1.13)
  WiFi (<địa chỉ IP thực tế>)         ← WiFi (VD: 10.0.0.8)
  Loopback (127.0.0.1)                ← Máy local/Depence cùng máy
  Broadcast (0.0.0.0)                 ← Chế độ broadcast
```

### Bước 3: Chọn Adapter Phù Hợp

**Nếu dùng Depence 3D cùng máy tính:**
- Chọn: **Loopback (127.0.0.1)**
- Hoặc: **Primary Network (auto-detect)**

**Nếu dùng Depence trên máy khác hoặc unicast:**
- Chọn: **Ethernet (<địa chỉ IP của card mạng>)** hoặc adapter đó
- IP sẽ hiển thị: `<địa chỉ thực tế của adapter>` (VD: `192.168.1.13`)

**Nếu dùng broadcast (Resolume, lighting console):**
- Chọn: **Broadcast (0.0.0.0)**

### Bước 4: Lưu Và Khởi Động Lại

1. **Click "Save Settings"** hoặc **"Apply"**
2. Popup hiện: *"Settings have been saved successfully. Please restart the application..."*
3. **Đóng app hoàn toàn** (không chỉ minimize)
4. **Mở app lại**

✅ **App sẽ nhớ lựa chọn lần sau** (không cần chọn lại)

## ✅ Kiểm Tra Hoạt Động

### Cách 1: Xem Hardware Manager
1. Mở tab **Hardware Manager**
2. Nhấn **"Ping Device"** để scan network
3. Xem các devices được discover
4. Nếu không thấy devices → Có thể adapter sai, quay lại chọn adapter khác

### Cách 2: Test Recording
1. Khởi động Depence
2. Chọn **Unicast** mode, gửi Art-Net tới IP adapter được chọn (xem IP trong "Adapter IP")
3. Mở tab **Record** trong DMX Master
4. Nhấn **Start Recording**
5. Trong Depence: nhấn Play show
6. **Dữ liệu DMX nên xuất hiện trong Recording** ✅

## ⚠️ Thắc Mắc Thường Gặp

**Q: Recording vẫn không hoạt động?**
A: 
1. Kiểm tra adapter được chọn → Phải match với IP Depence gửi tới
2. Kiểm tra Firewall → Có thể chặn port 6454
3. Kiểm tra netstat: `netstat -ano | findstr 6454` → Port có bị chiếm không
4. Restart app sau mỗi thay đổi

**Q: Khác biệt giữa các adapter là gì?**
A:
- **Ethernet/WiFi**: Card mạng vật lý
- **Loopback**: Máy local, chạy Depence cùng máy tính
- **Broadcast**: Mode phát sóng (0.0.0.0)
- **Auto-detect**: Tự động chọn card mạng chính

**Q: Phải restart app mỗi lần thay đổi adapter sao?**
A: Có, socket UDP phải rebind. Lần tới app sẽ nhớ lựa chọn (không cần setup lại).

**Q: Recording vẫn chỉ hoạt động qua 255.255.255.255 broadcast?**
A: 
- Chọn adapter cụ thể (xem IP trong "Adapter IP" label) thay vì Broadcast 0.0.0.0
- Depence phải gửi Art-Net **unicast** tới địa chỉ IP của adapter đó (VD: 192.168.1.13)
- Không phải gửi **broadcast** (255.255.255.255)

## 🔧 Mô Tả Kỹ Thuật (For Advanced Users)

### Config File
Lựa chọn được lưu vào: `%LOCALAPPDATA%\DMX Master LTS\config\app_config.json`
```json
{
  "artnet": {
    "bind_ip": "<địa chỉ IP thực tế của adapter>"
  }
}
```

**Ví dụ:**
```json
{
  "artnet": {
    "bind_ip": "192.168.1.13"
  }
}
```

### Socket Binding (Windows)
- **Trước (V2.0)**: `socket.bind(("0.0.0.0", 6454))` - chỉ nhận broadcast
- **Sau (V2.1)**: `socket.bind(("192.168.1.13", 6454))` - nhận cả broadcast lẫn unicast

Windows UDP có đặc điểm: binding (0.0.0.0) không nhận unicast to specific addresses, phải bind specific IP.

### Secondary Socket
Nếu adapter chính không phải 127.0.0.1, app tự tạo socket thứ 2 trên loopback để support Depence chạy cùng máy.

## 📝 Troubleshooting Checklist

- [ ] IP trong "Adapter IP" label phải match với IP Depence gửi unicast tới
- [ ] Depence gửi Art-Net **unicast** (không broadcast) nếu chọn adapter cụ thể
- [ ] Firewall cho phép port 6454 UDP
- [ ] App đã khởi động lại sau thay đổi adapter
- [ ] Netstat không thấy port 6454 bị chiếm bởi app khác: `netstat -ano | findstr 6454`
- [ ] Loopback adapter (127.0.0.1) được check nếu Depence chạy cùng máy

## 🆘 Liên Hệ Hỗ Trợ

Nếu vấn đề vẫn tiếp diễn:
1. Ghi lại adapter được chọn và IP trong "Adapter IP" label
2. Sao chép log từ Settings → System (nếu có Log Export)
3. Chạy: `netstat -ano | findstr 6454` → Ghi kết quả
4. Liên hệ support với thông tin trên

---

**Version:** V2.1  
**Updated:** 2026-03-10  
**Language:** Vietnamese (Tiếng Việt)
