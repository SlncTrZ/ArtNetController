# License System Documentation

## 📋 Tổng quan

Hệ thống bảo vệ bản quyền cho Art-Net Controller với:
- ✅ **Trial 7 ngày** miễn phí
- ✅ **License Key 20 ký tự** (format: XXXXX-XXXXX-XXXXX-XXXXX)
- ✅ **Hardware binding** (gắn với máy tính cụ thể)
- ✅ **Master keys** (không gắn hardware, dùng cho admin)
- ✅ **Mã hóa SHA-256** chống crack

## 🔐 Cách hoạt động

### 1. Trial Mode (7 ngày)
- Khi lần đầu chạy phần mềm → tự động tạo trial
- File lưu: `config/license.dat`
- Đếm ngược từ ngày cài đặt
- Sau 7 ngày → **khóa toàn bộ chức năng**

### 2. License Activation
- Nhập license key 20 ký tự
- Validate checksum
- Check hardware binding (nếu có)
- Kích hoạt thành công → dùng vĩnh viễn

### 3. License Key Format

```
XXXXX-XXXXX-XXXXX-XXXXX
  |      |      |      |
  |      |      |      └─ Checksum (5 chars)
  |      |      └──────── Date Hash (5 chars)
  |      └─────────────── Hardware ID (5 chars) or Random for Master Key
  └────────────────────── Prefix (5 chars) - ARTNT or ADMIN
```

**Hardware-Bound Key:**
```
ARTNT-A3F2D-8C5E1-9B4A7
  |      |
  |      └─ Hardware ID của máy tính cụ thể
  └──────── Prefix thông thường
```

**Master Key:**
```
ADMIN-K8D2F-3E9C1-7A5B2
  |      |
  |      └─ Random hash (không bind hardware)
  └──────── ADMIN prefix → hoạt động trên mọi máy
```

## 🛠️ Generate License Keys

### Tool: `tools/generate_license.py`

```bash
cd H:\VSCode\ArtNetController
python tools/generate_license.py
```

**Menu:**
```
1. Generate Hardware-Bound License Key  → Gắn với máy tính hiện tại
2. Generate Master License Key          → Hoạt động trên mọi máy
3. Validate License Key                 → Kiểm tra key có hợp lệ không
4. Show Current Hardware ID             → Xem Hardware ID của máy
5. Exit
```

### Ví dụ Generate Key:

**Hardware-Bound:**
```
> python tools/generate_license.py
Select option: 1
Enter prefix: ARTNT

✅ HARDWARE-BOUND LICENSE KEY GENERATED
========================================
License Key: ARTNT-A3F2D-8C5E1-9B4A7
Hardware ID: A3F2D1234567890A

⚠️  This key will ONLY work on this computer!
```

**Master Key:**
```
Select option: 2

✅ MASTER LICENSE KEY GENERATED
========================================
License Key: ADMIN-K8D2F-3E9C1-7A5B2

✨ This key will work on ANY computer!
```

## 💻 Sử dụng trong phần mềm

### 1. Khi khởi động:
- Check license validity
- Nếu trial hết hạn → Hiện dialog yêu cầu activate
- Nếu không activate → Đóng ứng dụng

### 2. Activate License:
```
Menu → Help → License Activation...
```

**Dialog:**
- Hiển thị trạng thái license hiện tại
- Trial info (ngày còn lại)
- Hardware ID của máy
- Input boxes cho 4 phần của license key
- Button "Activate License"

### 3. Trial Notice:
- Hiện popup sau 2 giây khi khởi động
- Thông báo số ngày trial còn lại
- Hướng dẫn activate

## 📁 Files

### 1. `src/utils/license.py`
- `LicenseManager` class
- Generate, validate, activate keys
- Trial management
- Hardware ID detection

### 2. `src/gui/dialogs/license_dialog.py`
- `LicenseDialog` class
- UI để nhập và activate license
- Hiển thị status, trial info
- Generate test key

### 3. `config/license.dat`
```json
{
  "type": "trial",
  "start_date": "2025-11-03T10:30:00",
  "trial_days": 7,
  "activated": false,
  "license_key": null,
  "hardware_id": "A3F2D1234567890A"
}
```

Sau khi activate:
```json
{
  "type": "activated",
  "activated": true,
  "license_key": "ARTNT-A3F2D-8C5E1-9B4A7",
  "activation_date": "2025-11-05T14:20:00",
  "hardware_id": "A3F2D1234567890A",
  "start_date": "2025-11-03T10:30:00",
  "trial_days": 7
}
```

## 🔒 Security Features

### 1. Checksum Validation
- SHA-256 hash với master salt
- Không thể forge key mà không biết algorithm

### 2. Hardware Binding
- Dựa trên: Platform, Machine, MAC address
- Mỗi máy có ID duy nhất
- License key bind với hardware ID

### 3. File Encryption
- License data lưu JSON format
- Có thể encrypt thêm nếu cần

### 4. Anti-Tampering
- Không thể sửa file `license.dat` để extend trial
- Checksum validation khi load

## 📝 Best Practices

### Cho Developer:

1. **Thay đổi MASTER_SALT trong production:**
```python
# src/utils/license.py
MASTER_SALT = "YOUR_SECRET_SALT_HERE_2025"
```

2. **Generate Master Keys cho admin:**
```bash
python tools/generate_license.py
Option: 2
```

3. **Phân phối keys:**
- Email cho customer
- Portal tự động generate
- Database lưu keys đã bán

### Cho Customer:

1. **Download và cài đặt**
2. **Trial 7 ngày tự động bắt đầu**
3. **Mua license key**
4. **Activate:** Help → License Activation
5. **Nhập key → Activate**
6. **Dùng vĩnh viễn ✅**

## 🛡️ Protection Level

- ✅ Trial enforcement
- ✅ Hardware binding
- ✅ Checksum validation
- ✅ Date manipulation protection
- ⚠️ NOT protected against: Reverse engineering bytecode
- 💡 Recommend: Compile to .exe với PyInstaller + obfuscation

## 🔧 Testing

### Test Trial:
```python
from utils.license import LicenseManager

manager = LicenseManager()
is_valid, msg = manager.is_valid()
print(f"Valid: {is_valid}, Message: {msg}")

info = manager.get_trial_info()
print(f"Days remaining: {info['days_remaining']}")
```

### Test Activation:
```python
test_key = manager.generate_license_key()
print(f"Test key: {test_key}")

success, msg = manager.activate_license(test_key)
print(f"Activated: {success}, Message: {msg}")
```

### Reset Trial (for testing):
```python
manager.reset_trial()  # ⚠️ Only for testing!
```

## 📞 Support

**Issues:**
- Trial not working → Check `config/license.dat` file
- Key invalid → Verify checksum và hardware ID
- Already activated → Check license status in dialog

**Contact:** truongcongdinh@example.com
