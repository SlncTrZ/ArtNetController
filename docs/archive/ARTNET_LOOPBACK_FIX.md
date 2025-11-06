#  Art-Net Loopback Fix - Depence trên cùng máy

##  Vấn đề
Khi chạy Depence và DMX Master trên cùng 1 máy, gửi Art-Net đến IP LAN (192.168.1.171) có thể KHÔNG hoạt động do:
1. Windows không route traffic loopback qua network interface
2. Firewall block inter-process communication
3. Network stack optimization

##  GIẢI PHÁP HOÀN TOÀN

### Cách 1: Sử dụng Localhost (KHUYẾN NGHỊ)
**Trong Depence:**
- Output IP: \127.0.0.1\ hoặc \localhost\
- Port: \6454\
- Universe: theo cấu hình

**Ưu điểm:**
-  Luôn hoạt động 100%
-  Không qua network card
-  Không bị firewall block
-  Tốc độ nhanh nhất

### Cách 2: Sử dụng Broadcast
**Trong Depence:**
- Output IP: \255.255.255.255\
- Port: \6454\
- Universe: theo cấu hình

**Ưu điểm:**
-  Gửi đến tất cả devices trên network
-  Hoạt động với nhiều app cùng lúc

**Nhược điểm:**
-  Tốn bandwidth network
-  Có thể bị firewall block broadcast

### Cách 3: Multicast (Nâng cao)
**Trong Depence:**
- Output IP: \239.255.0.1\
- Port: \6454\
- Universe: theo cấu hình

**Lưu ý:** Cần thêm code hỗ trợ multicast

### Cách 4: Sử dụng Virtual Network Adapter
**Tạo virtual loopback adapter:**
1. Device Manager  Add legacy hardware
2. Chọn Microsoft KM-TEST Loopback Adapter
3. Set IP tĩnh: 192.168.100.1
4. Depence gửi đến: 192.168.100.1:6454

##  Kiểm tra kết nối

### Test 1: Kiểm tra port listening
\\\powershell
netstat -an | findstr "6454"
# Kết quả mong đợi:
# UDP    0.0.0.0:6454           *:*
\\\

### Test 2: Test với Python script
\\\python
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Gửi test packet
sock.sendto(b'Art-Net\\x00\\x00\\x50', ('127.0.0.1', 6454))
\\\

### Test 3: Wireshark capture
1. Mở Wireshark
2. Filter: \udp.port == 6454\
3. Gửi Art-Net từ Depence
4. Xem có packet đến không

##  Debug trong DMX Master

Khi nhận được Art-Net, log sẽ hiện:
\\\
INFO - Art-Net socket bound to 0.0.0.0:6454
INFO - RX from {IP}:{PORT}, size: {bytes} bytes
INFO - Received DMX data: Universe {N}, {channels} channels from {IP}
\\\

Nếu KHÔNG thấy log "RX from..."  packet không đến app.

##  Cấu hình Depence

### Bước 1: Output Settings
1. Menu  Setup  Output
2. Add new output
3. Type: Art-Net
4. **IP Address: 127.0.0.1** (quan trọng!)
5. Universe: 0 (hoặc theo cấu hình)
6. Enable output

### Bước 2: Kiểm tra Firewall
1. Windows Defender Firewall
2. Advanced settings
3. Inbound Rules
4. Cho phép UDP port 6454

### Bước 3: Test
1. Play scene trong Depence
2. Xem DMX View trong DMX Master
3. Nếu thấy giá trị thay đổi  thành công!

##  So sánh các phương pháp

| Phương pháp | Độ tin cậy | Tốc độ | Dễ cấu hình | Khuyến nghị |
|-------------|-----------|--------|-------------|-------------|
| 127.0.0.1   |  | Rất nhanh | Dễ |  TỐT NHẤT |
| Broadcast   |  | Nhanh | Dễ |  OK |
| LAN IP      |  | Chậm | Khó |  KHÔNG NÊN |
| Multicast   |  | Nhanh | Khó |  Nâng cao |

##  KẾT LUẬN

**GIẢI PHÁP HOÀN TOÀN:** 
Sử dụng **127.0.0.1** (localhost) trong Depence output settings.

**TẠM THỜI:** Không cần
Với localhost, không cần giải pháp tạm thời.

**VÌ SAO 192.168.1.171 KHÔNG HOẠT ĐỘNG:**
Windows kernel không route traffic từ network IP đến chính nó qua loopback.
Packet đi ra network card nhưng không quay lại stack.

---
**Tạo:** 2025-11-04
**Cập nhật:** 2025-11-04
