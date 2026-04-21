# 🎭 Hướng dẫn cấu hình Depence gửi 8 Universes đến DMX Master

## 📌 Yêu cầu
- DMX Master v1.0.3+ 
- Depence R2 (hoặc phiên bản tương đương)
- Cùng mạng LAN: `192.168.1.x`
- DMX Master IP: `192.168.1.171`

## 🎯 Mục tiêu
Gửi **8 universes** từ Depence sang DMX Master:
```
Depence Universe 1-8  →  DMX Master Universe 0-7
```

## ⚠️ Giới hạn Art-Net Legacy
- **Art-Net spec cũ**: Mỗi node chỉ quảng bá tối đa **4 ports** trong PollReply
- **Depence**: Mỗi Art-Net Output node có tối đa **4 ports**
- **Giải pháp**: Sử dụng **2 nodes** hoặc **subnet** để mở rộng

## 🔧 Giải pháp: Sử dụng Art-Net Subnet

### Cách 1: Broadcast (Đơn giản nhất - KHUYẾN NGHỊ)

**Trong Depence:**
1. **Art-Net Output Node 1:**
   - IP Address: `255.255.255.255` (Broadcast)
   - Universe 1 → Port 1
   - Universe 2 → Port 2
   - Universe 3 → Port 3
   - Universe 4 → Port 4

2. **Art-Net Output Node 2:**
   - IP Address: `255.255.255.255` (Broadcast)
   - Universe 5 → Port 1
   - Universe 6 → Port 2
   - Universe 7 → Port 3
   - Universe 8 → Port 4

**Trong DMX Master:**
- DMX View: Chọn Universe 0-7
- Tất cả sẽ nhận được tự động vì broadcast

**✅ Ưu điểm:**
- Đơn giản, không cần cấu hình phức tạp
- Hoạt động ngay lập tức
- Không phụ thuộc vào PollReply

**⚠️ Nhược điểm:**
- Broadcast tốn băng thông mạng hơn unicast
- Tất cả thiết bị trên mạng đều nhận packet (dù không cần)

---

### Cách 2: Unicast với Subnet (Tối ưu băng thông)

#### A. Hiểu về Art-Net Addressing

Art-Net universe được tính theo công thức:
```
Universe = (Net << 8) | (SubNet << 4) | SwIn
```

Ví dụ:
- Net=0, SubNet=0, SwIn=0 → Universe 0
- Net=0, SubNet=0, SwIn=3 → Universe 3
- Net=0, SubNet=1, SwIn=0 → Universe 16
- Net=0, SubNet=1, SwIn=3 → Universe 19

**⚠️ QUAN TRỌNG**: Mapping này có thể khác trong Depence!

#### B. Cấu hình Depence (Thử nghiệm)

**Option 1: Sử dụng 1 node với 8 ports (nếu Depence hỗ trợ)**

Một số phiên bản Depence cho phép cấu hình >4 ports:
1. Tạo Art-Net Output
2. IP: `192.168.1.171` (Unicast)
3. Cấu hình 8 ports:
   ```
   Port 1 → Universe 0
   Port 2 → Universe 1
   Port 3 → Universe 2
   Port 4 → Universe 3
   Port 5 → Universe 4
   Port 6 → Universe 5
   Port 7 → Universe 6
   Port 8 → Universe 7
   ```

**Option 2: Sử dụng 2 nodes riêng biệt**

1. **Node 1 (Universe 0-3):**
   - IP: `192.168.1.171`
   - Net: 0
   - SubNet: 0
   - Ports:
     ```
     Port 1 → Universe 0 (Net:0, Sub:0, U:0)
     Port 2 → Universe 1 (Net:0, Sub:0, U:1)
     Port 3 → Universe 2 (Net:0, Sub:0, U:2)
     Port 4 → Universe 3 (Net:0, Sub:0, U:3)
     ```

2. **Node 2 (Universe 4-7):**
   - IP: `192.168.1.171` (cùng IP)
   - Net: 0
   - SubNet: 1 (KHÁC subnet)
   - Ports:
     ```
     Port 1 → Universe 16 (Net:0, Sub:1, U:0) - Manual map to U4
     Port 2 → Universe 17 (Net:0, Sub:1, U:1) - Manual map to U5
     Port 3 → Universe 18 (Net:0, Sub:1, U:2) - Manual map to U6
     Port 4 → Universe 19 (Net:0, Sub:1, U:3) - Manual map to U7
     ```

**⚠️ Vấn đề**: Depence có thể không cho phép 2 nodes cùng IP.

**Option 3: Force Manual Universe Override**

Trong một số phiên bản Depence:
1. Tạo Art-Net Output node
2. IP: `192.168.1.171`
3. **Disable auto-discovery**
4. **Manual override universe mapping**:
   ```
   Depence U1 → Art-Net Universe 0
   Depence U2 → Art-Net Universe 1
   Depence U3 → Art-Net Universe 2
   Depence U4 → Art-Net Universe 3
   Depence U5 → Art-Net Universe 4
   Depence U6 → Art-Net Universe 5
   Depence U7 → Art-Net Universe 6
   Depence U8 → Art-Net Universe 7
   ```

---

### Cách 3: Sử dụng nhiều IP ảo (Advanced)

**Nếu Depence yêu cầu mỗi node phải có IP riêng:**

1. **Tạo IP ảo trên máy DMX Master** (Windows):
   ```powershell
   # Thêm IP thứ 2 vào adapter mạng
   New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.1.172 -PrefixLength 24
   ```

2. **Trong Depence:**
   - Node 1: `192.168.1.171` → Universe 0-3
   - Node 2: `192.168.1.172` → Universe 4-7

3. **Trong DMX Master:**
   - Vẫn bind `0.0.0.0:6454` → nhận cả 2 IPs

---

## 🧪 Kiểm tra hoạt động

### 1. Test Broadcast (Nhanh nhất)

```
Depence → Broadcast 255.255.255.255
         Universe 1-8 (Depence) = Universe 0-7 (Art-Net)

DMX Master:
  - Mở DMX View
  - Chọn Universe 0 → thấy DMX từ Depence U1
  - Chọn Universe 4 → thấy DMX từ Depence U5
```

### 2. Test Unicast

```powershell
# Trên máy DMX Master, monitor traffic:
python -c "
import sys
sys.path.insert(0, 'src')
from artnet.controller import ArtNetController

ctrl = ArtNetController()
ctrl.start()

print('Listening on 0.0.0.0:6454...')
print('Waiting for Art-Net from Depence...')
input('Press Enter to stop...')
ctrl.stop()
"
```

**Kiểm tra log:**
```
✅ Received DMX data: Universe 0, 512 channels from 192.168.1.x
✅ Received DMX data: Universe 1, 512 channels from 192.168.1.x
✅ Received DMX data: Universe 4, 512 channels from 192.168.1.x
✅ Received DMX data: Universe 7, 512 channels from 192.168.1.x
```

---

## 📊 So sánh các phương pháp

| Phương pháp | Độ khó | Băng thông | Tương thích | Khuyến nghị |
|-------------|--------|------------|-------------|-------------|
| **Broadcast** | ⭐ Dễ | ⚠️ Cao | ✅ 100% | ⭐⭐⭐⭐⭐ |
| **Unicast Manual** | ⭐⭐ Trung bình | ✅ Thấp | ⚠️ 80% | ⭐⭐⭐⭐ |
| **Subnet** | ⭐⭐⭐ Khó | ✅ Thấp | ⚠️ 60% | ⭐⭐⭐ |
| **Multi-IP** | ⭐⭐⭐⭐ Rất khó | ✅ Thấp | ⚠️ 70% | ⭐⭐ |

---

## 🎯 Khuyến nghị

### Cho người mới bắt đầu:
👉 **Sử dụng Broadcast** (`255.255.255.255`)
- Đơn giản nhất
- Hoạt động 100%
- Dễ debug

### Cho mạng lớn/production:
👉 **Sử dụng Unicast với Manual Override**
- Tối ưu băng thông
- Chỉ gửi đến đúng thiết bị cần
- Cần test kỹ với phiên bản Depence cụ thể

---

## 🔍 Troubleshooting

### Vấn đề 1: Depence không thấy DMX Master node

**Nguyên nhân:**
- DMX Master chưa gửi PollReply
- Depence không scan đúng subnet

**Giải pháp:**
1. Trong DMX Master, chạy: Menu → Setting → Art-Net → Scan Network
2. Trong Depence: Refresh node list
3. Nếu vẫn không thấy: Dùng broadcast thay vì unicast

### Vấn đề 2: Chỉ nhận được Universe 0-3, không nhận 4-7

**Nguyên nhân:**
- Depence chỉ gửi đến 4 ports đầu tiên của node
- PollReply chỉ quảng bá 4 ports

**Giải pháp:**
- ✅ **Dùng Broadcast** → DMX Master nhận TẤT CẢ universes
- ⚠️ Dùng 2 nodes riêng với IP khác nhau (nếu Depence yêu cầu)

### Vấn đề 3: Universe mapping sai

**Ví dụ:**
- Depence U5 → DMX Master U16 (thay vì U4)

**Nguyên nhân:**
- Depence tự động tính universe theo subnet
- Universe = (Net << 8) | (SubNet << 4) | SwIn

**Giải pháp:**
- Sử dụng **Manual Universe Override** trong Depence
- Hoặc dùng **Broadcast** để tránh subnet calculation

---

## 📝 Tóm tắt

### ✅ KHUYẾN NGHỊ CHÍNH:

**Sử dụng BROADCAST trong Depence:**
```
Node 1: 255.255.255.255 → Depence U1-4 → Art-Net U0-3
Node 2: 255.255.255.255 → Depence U5-8 → Art-Net U4-7
```

DMX Master sẽ **tự động nhận TẤT CẢ** vì:
- Socket bind `0.0.0.0:6454`
- Không giới hạn bởi PollReply NumPorts
- PollReply chỉ để Depence biết node tồn tại

### 🎯 Nếu muốn Unicast:

Cần test với phiên bản Depence cụ thể để xác định:
1. Depence có cho phép manual override universe?
2. Depence có cho phép 2 nodes cùng IP?
3. Depence tính universe theo subnet như thế nào?

---

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra log trong `logs/` folder
2. Test với broadcast trước
3. Kiểm tra firewall không block port 6454 UDP
4. Đảm bảo cùng subnet (192.168.1.x)

**Version:** DMX Master v1.0.3+  
**Date:** 2025-11-05
