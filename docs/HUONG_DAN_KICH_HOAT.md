#  HƯỚNG DẪN KÍCH HOẠT PHẦN MỀM - NHANH

##  QUY TRÌNH (3 BƯỚC)

### BƯỚC 1: LẤY MÃ MÁY TÍNH (DEVICE ID)

1. Mở phần mềm ArtNet Controller
2. Vào menu: **Help  License Activation**
3. Sẽ thấy **Device ID** (mã 64 ký tự)
4. Click ** Copy** để copy

**Ví dụ Device ID:**
```
a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

---

### BƯỚC 2: XIN LICENSE TỪ ADMIN

Gửi **Device ID** cho admin (bạn - Truong Cong Dinh):

 **Email**: truongcongdinh97@gmail.com

Nội dung email:
```
Subject: Xin license ArtNet Controller

Device ID: a1b2c3d4e5f6...
Email: customer@example.com
```

---

### BƯỚC 3: TẠO LICENSE (DÀNH CHO ADMIN)

**Bạn (admin) chạy tool tạo license:**

```powershell
cd H:\VSCode\ArtNetController\tools
python generate_license.py
```

Tool sẽ hỏi:
1. **Device ID**: Paste Device ID từ khách hàng
2. **License ID**: Nhập ID bất kỳ (vd: `KH-001`)
3. **Customer Email**: Email khách hàng
4. **License Type**: Nhấn Enter (perpetual - vĩnh viễn)

**Output:** File JSON (ví dụ: `license_KH-001.json`)

---

### BƯỚC 4: GỬI LICENSE CHO KHÁCH HÀNG

Gửi file JSON cho khách hàng (hoặc paste nội dung JSON qua email)

---

### BƯỚC 5: KHÁCH HÀNG KÍCH HOẠT

Khách hàng làm:

1. Mở phần mềm
2. Vào **Help  License Activation**
3. Paste toàn bộ nội dung JSON vào ô **Step 2**
4. Click ** Activate License**
5. **XONG!** Phần mềm đã kích hoạt vĩnh viễn

---

##  CÔNG CỤ ADMIN (DÀNH CHO BẠN)

### Tool 1: Tạo RSA Keys (chạy 1 lần đầu tiên)

```powershell
cd H:\VSCode\ArtNetController\tools
.\RSA_Key_Generator.exe
```

Hoặc:
```powershell
python generate_rsa_keys.py
```

**Output:**
- `rsa_keys/private_key.pem`  **GIỮ BÍ MẬT!**
- `rsa_keys/public_key_constant.py`  Copy vào code

### Tool 2: Tạo License cho khách hàng

```powershell
cd H:\VSCode\ArtNetController\tools
python generate_license.py
```

**Input:**
- Device ID từ khách hàng
- License ID (vd: KH-001, KH-002...)
- Email khách hàng

**Output:**
- File `generated_licenses/license_KH-001.json`

Gửi file này cho khách hàng!

---

##  LƯU Ý QUAN TRỌNG

###  DÀNH CHO ADMIN (BẠN):

1. **RSA Keys chỉ tạo 1 LẦN** (đã tạo rồi thì giữ nguyên)
2. **`private_key.pem` TUYỆT ĐỐI GIỮ BÍ MẬT**
   - Không commit lên GitHub
   - Backup vào USB an toàn
   - Mất key = không tạo license được nữa
3. **Public key phải nhúng vào app** (`src/utils/license.py`)

###  DÀNH CHO KHÁCH HÀNG:

1. License **CHỈ DÙNG CHO 1 MÁY** (gắn với Device ID)
2. **Vĩnh viễn** - mua 1 lần, dùng mãi mãi
3. **Offline** - không cần internet sau khi kích hoạt
4. Cài lại Windows/đổi phần cứng  Device ID đổi  cần license mới

---

##  QUY TRÌNH HOÀN CHỈNH (FLOWCHART)

```
KHÁCH HÀNG                           ADMIN (BẠN)
    |                                    |
    | 1. Mở phần mềm                    |
    | 2. Copy Device ID                 |
    |                                    |
    | 3. Gửi Device ID qua email        |
    |----------------------------------->|
    |                                    | 4. Nhận Device ID
    |                                    | 5. Chạy generate_license.py
    |                                    | 6. Nhập Device ID + thông tin
    |                                    | 7. Tool tạo file JSON
    |                                    |
    | 8. Nhận file JSON license         |
    |<-----------------------------------|
    |                                    |
    | 9. Paste JSON vào phần mềm        |
    | 10. Click "Activate"               |
    | 11. XONG!                        |
```

---

##  DEMO NHANH

### Tạo license test:

```powershell
# Bước 1: Vào thư mục tools
cd H:\VSCode\ArtNetController\tools

# Bước 2: Chạy tool
python generate_license.py

# Bước 3: Nhập thông tin
Device ID: abc123... (paste từ phần mềm)
License ID: TEST-001
Email: test@example.com
Type: [Enter] (perpetual)

# Bước 4: Lấy JSON
# Mở file: generated_licenses/license_TEST-001.json
# Copy toàn bộ nội dung

# Bước 5: Paste vào phần mềm
# Help  License  Paste JSON  Activate
```

---

##  FAQ NHANH

**Q: Tôi (admin) phải làm gì trước tiên?**
A: Chạy `RSA_Key_Generator.exe` một lần để tạo keys.

**Q: Khách hàng cần gửi gì?**
A: Chỉ cần Device ID (64 ký tự).

**Q: Tôi tạo license như thế nào?**
A: Chạy `python generate_license.py`, nhập Device ID + thông tin.

**Q: Gửi gì cho khách hàng?**
A: File JSON (hoặc copy/paste nội dung JSON).

**Q: Khách hàng làm gì với JSON?**
A: Paste vào phần mềm  Click Activate.

**Q: License có hết hạn không?**
A: Không! Vĩnh viễn (perpetual).

**Q: Có thể dùng trên nhiều máy?**
A: Không. Mỗi license gắn với 1 Device ID.

---

##  HỖ TRỢ

**Admin (bạn):** truongcongdinh97@gmail.com
**Khách hàng:** Liên hệ admin để được hỗ trợ

---

**Tạo:** 03/11/2025 | **Truong Cong Dinh**
