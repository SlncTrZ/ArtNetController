#  HƯỚNG DẪN SỬ DỤNG license_admin.py

 **LƯU Ý:** Tool này dành cho **LICENSE SERVER** (online revocation).

Hệ thống license của bạn dùng **RSA offline**, nên bạn **KHÔNG CẦN** tool này!

---

##  HAI CÁCH TẠO LICENSE:

###  **CÁCH 1: RSA Offline (KHUYÊN DÙNG - Đang dùng)**

**Tool:** `generate_license.py`

```powershell
cd H:\VSCode\ArtNetController\tools
python generate_license.py
```

**Ưu điểm:**
-  Offline hoàn toàn
-  Không cần server
-  Bảo mật cao (RSA-2048)
-  License vĩnh viễn gắn với hardware

**Quy trình:**
1. Khách hàng gửi Device ID
2. Chạy `generate_license.py`
3. Nhập Device ID + thông tin
4. Gửi file JSON cho khách hàng
5. XONG!

---

###  **CÁCH 2: Online Server (license_admin.py)**

**Yêu cầu:** Phải có **License Server** chạy (không cần thiết)

**Tool:** `license_admin.py`

```powershell
python license_admin.py
```

**Menu:**
```
1. Generate new license     Tạo license online
2. List all licenses        Xem danh sách
3. Revoke license           Thu hồi license
4. Check server health      Kiểm tra server
5. Exit
```

**Ưu điểm:**
- Remote revocation (thu hồi từ xa)
- Quản lý tập trung

**Nhược điểm:**
- Cần server chạy 24/7
- Phức tạp hơn
- Khách hàng cần internet

---

##  BẠN NÊN DÙNG GÌ?

### **Dùng `generate_license.py`** (RSA Offline) 

**Lý do:**
1. Đơn giản hơn (không cần server)
2. Đã setup đầy đủ
3. Phù hợp với mô hình của bạn
4. Bảo mật tốt

**Quy trình:**
```powershell
# 1. Tạo license
cd H:\VSCode\ArtNetController\tools
python generate_license.py

# 2. Nhập thông tin
Device ID: [paste từ khách hàng]
License ID: KH-001
Email: customer@example.com

# 3. Gửi file JSON
File: generated_licenses/license_KH-001.json
```

---

##  NẾU MUỐN DÙNG license_admin.py

### Bước 1: Khởi động License Server

```powershell
cd H:\VSCode\ArtNetController\server
python license_server.py
```

Server chạy tại: http://localhost:5000

### Bước 2: Chỉnh sửa cấu hình

Mở `tools/license_admin.py`, sửa:

```python
LICENSE_SERVER = "http://localhost:5000"
ADMIN_PASSWORD = "your-secret-password"  # Đổi thành password bảo mật
```

### Bước 3: Chạy Admin Tool

```powershell
cd H:\VSCode\ArtNetController\tools
python license_admin.py
```

### Bước 4: Sử dụng

**Menu:**
- **1:** Tạo license mới (nhập tên khách hàng, email)
- **2:** Xem danh sách license
- **3:** Thu hồi license (nhập license key)
- **4:** Kiểm tra server có hoạt động không
- **5:** Thoát

**Ví dụ tạo license:**
```
Choose option: 1
Customer name: Nguyen Van A
Email: nguyenvana@example.com
Notes: Trial customer

 License: abc-123-def-456-...
```

**Thu hồi license:**
```
Choose option: 3
License key: abc-123-def-456
Reason: Expired trial

Revoke? yes
  License revoked
```

---

##  SO SÁNH HAI CÁCH

| Tính năng | generate_license.py (RSA) | license_admin.py (Server) |
|-----------|---------------------------|---------------------------|
| **Offline** |  Hoàn toàn |  Cần internet |
| **Server** |  Không cần |  Phải có server |
| **Bảo mật** |  RSA-2048 |  Phụ thuộc server |
| **Thu hồi từ xa** |  Không |  Có |
| **Đơn giản** |  Rất đơn giản |  Phức tạp hơn |
| **Chi phí** |  Miễn phí |  Cần hosting |

---

##  KHUYẾN NGHỊ

### Dùng `generate_license.py` nếu:
-  Khách hàng ít (< 100)
-  Không cần thu hồi license thường xuyên
-  Muốn hệ thống đơn giản
-  Không muốn maintain server

### Dùng `license_admin.py` nếu:
-  Có nhiều khách hàng (> 100)
-  Cần thu hồi license từ xa
-  Cần quản lý tập trung
-  Có server để chạy 24/7

---

##  DEMO NHANH - license_admin.py

### Khởi động server:
```powershell
# Terminal 1: Chạy server
cd H:\VSCode\ArtNetController\server
python license_server.py
#  Server running on http://localhost:5000
```

### Sử dụng admin tool:
```powershell
# Terminal 2: Chạy admin
cd H:\VSCode\ArtNetController\tools
python license_admin.py

# Menu hiện ra:
# 1. Generate new license
# 2. List all licenses
# ...

# Chọn 1 để tạo license
Choose: 1
Customer: Test User
Email: test@example.com
Notes: Demo license

#  License: xyz-abc-123-...
```

---

##  FAQ

**Q: Tôi nên dùng cái nào?**
A: Dùng `generate_license.py` (đơn giản hơn, đủ dùng).

**Q: Làm sao để thu hồi license với RSA offline?**
A: Tạo blacklist trong code hoặc dùng license_server.py (optional).

**Q: license_admin.py có bắt buộc không?**
A: KHÔNG. Nó là optional tool cho server-based licensing.

**Q: Tôi đã setup xong chưa?**
A:  RỒI! Bạn có `generate_license.py` là đủ dùng.

---

##  HỖ TRỢ

**Email:** truongcongdinh97@gmail.com

**Tóm tắt:**
-  Dùng `generate_license.py` (RSA offline)
-  Bỏ qua `license_admin.py` (không cần thiết)

**Hệ thống của bạn đã hoàn chỉnh!** 
