# ART-NET CONTROLLER - SYSTEM DOCUMENTATION
## Hệ Thống License & Tools Hoàn Chỉnh

---

## 📦 CẤU TRÚC DỰ ÁN

```
ArtNetController/
├── src/                          # Main application source
│   ├── gui/
│   │   ├── dialogs/
│   │   │   └── license_dialog.py  # ✅ License activation dialog (có Load from File)
│   │   └── main_window.py
│   └── utils/
│       ├── license.py             # ✅ License manager
│       └── public_key.pem         # ✅ Public key (SYNCED with tools)
│
└── tools/                         # Admin tools
    ├── rsa_keys/                  # 🔐 RSA keypair
    │   ├── private_key.pem        # ⚠️ PRIVATE - Keep secret!
    │   ├── public_key.pem         # Public key
    │   └── public_key_constant.py
    │
    ├── dist/                      # 📦 Distribution package
    │   ├── LicenseGenerator.exe   # ✅ Standalone GUI (39 MB)
    │   └── README.txt
    │
    ├── generated_licenses/        # Output folder
    │   └── license_*.json
    │
    ├── license_generator_gui.py   # GUI source code
    ├── LicenseGenerator.spec      # PyInstaller spec
    ├── build_license_generator.bat
    ├── package_license_generator.bat
    └── LicenseGenerator_v1.0.0.zip # 📦 Ready to ship (37.56 MB)
```

---

## ✅ CHECKLIST - ĐÃ HOÀN THÀNH

### 1. RSA Keys
- [x] Generated RSA-2048 keypair
- [x] Private key: `tools/rsa_keys/private_key.pem`
- [x] Public key: `tools/rsa_keys/public_key.pem`
- [x] **SYNCED**: Public key copied to `src/utils/public_key.pem`
- [x] **VERIFIED**: Hash match confirmed (802EAF3A...)

### 2. License Generator Tool
- [x] GUI application với PyQt6
- [x] Nhập email + Device ID
- [x] 3 loại license: perpetual/trial/subscription
- [x] RSA-2048 signature
- [x] Copy to clipboard
- [x] Save to file
- [x] Built thành .exe standalone (39 MB)
- [x] Embedded private key (bảo mật)
- [x] README đầy đủ

### 3. Main Application
- [x] License activation dialog
- [x] **Load from File** button (MỚI)
- [x] Paste from clipboard
- [x] Public key embedded
- [x] Offline validation
- [x] Admin mode dựa trên license
- [x] Trial: 7 days, no admin rights
- [x] Licensed: Full admin rights

### 4. Documentation
- [x] Tool README (usage guide)
- [x] Customer instructions
- [x] Troubleshooting guide
- [x] System documentation

---

## 🔄 WORKFLOW - TẠO & KÍCH HOẠT LICENSE

### ADMIN (Tạo License)

1. **Nhận Device ID từ khách hàng**
   - Khách hàng: Help → License Activation → Copy Device ID
   - Email Device ID cho admin

2. **Chạy License Generator**
   - Double-click `LicenseGenerator.exe`
   - Nhập Email: `customer@example.com`
   - Paste Device ID (64 chars)
   - Chọn License Type: `perpetual`
   - Click **Generate License**

3. **Gửi License cho khách hàng**
   - Click **Save to File** → `license_customer_at_example_com_xxx.json`
   - Hoặc **Copy to Clipboard** → Paste vào email
   - Gửi file/text cho khách hàng

### CUSTOMER (Kích hoạt)

1. **Nhận license file hoặc JSON text**

2. **Mở Art-Net Controller**
   - Help → License Activation

3. **Kích hoạt**
   - **Cách 1**: Click **📁 Load from File** → Chọn file `.json`
   - **Cách 2**: Copy JSON → Click **📋 Paste from Clipboard**
   - Click **✅ Activate License**

4. **Restart app**
   - License được mã hóa AES-256 và lưu tại `config/license.lic`
   - Status bar: "Licensed to customer@example.com"
   - Admin features unlocked (Delete/Edit shows)

---

## 🔐 BẢO MẬT

### RSA-2048 Signature
- Private key chỉ có ở admin
- Public key embed trong app
- Không thể forge license

### Hardware Binding
- Device ID = SHA256(MAC + CPU Serial + Platform)
- License chỉ chạy trên 1 máy

### AES-256-GCM Encryption
- License file được mã hóa
- Không thể edit trực tiếp

### Trial System
- 7 ngày free trial
- Tự động tính từ lần cài đầu tiên
- Không có admin rights trong trial

---

## 📊 KIỂM TRA ĐỒNG BỘ

### Verify Keys Match
```powershell
cd H:\VSCode\ArtNetController

# Check hash
$hash1 = (Get-FileHash tools\rsa_keys\public_key.pem).Hash
$hash2 = (Get-FileHash src\utils\public_key.pem).Hash

if ($hash1 -eq $hash2) {
    Write-Host "✅ Keys SYNCED" -ForegroundColor Green
} else {
    Write-Host "❌ Keys OUT OF SYNC!" -ForegroundColor Red
}
```

### Test License Generation
```powershell
cd tools\dist
.\LicenseGenerator.exe

# Test with:
Email: test@example.com
Device ID: (paste 64-char hex)
Type: perpetual
```

### Test Activation
```
1. Run main app: python main.py
2. Help → License Activation
3. Load from File → Select generated .json
4. Click Activate
5. Restart app
6. Check status bar shows license email
```

---

## 🚀 DEPLOYMENT

### For Admin
1. Extract `LicenseGenerator_v1.0.0.zip`
2. Run `LicenseGenerator.exe`
3. Keep it secure (contains private key)

### For End Users
1. Install Art-Net Controller
2. Run trial for 7 days
3. Contact admin for license
4. Activate via Help → License Activation

---

## 📞 SUPPORT

**Developer**: Trương Công Định
**Email**: truongcongdinh97tcd@gmail.com
**Version**: 1.0.0
**Build**: 2025-11-03

---

## ✨ TÍNH NĂNG CHÍNH ĐÃ HOÀN THÀNH

### License System
- [x] RSA-2048 cryptographic signatures
- [x] Hardware binding (device ID)
- [x] AES-256-GCM encryption
- [x] Trial period (7 days)
- [x] Online revocation check (optional)
- [x] Admin vs User roles

### License Tools
- [x] GUI license generator
- [x] Standalone .exe (no Python needed)
- [x] Easy to use interface
- [x] Validation & error handling
- [x] File save & clipboard copy

### Main Application
- [x] License activation dialog
- [x] Load from file feature
- [x] Paste from clipboard
- [x] Offline validation
- [x] Admin features locked for trial
- [x] Show Manager (play/add/delete shows)
- [x] DMX View (512 channels)
- [x] Art-Net controller
- [x] Timezone support
- [x] Auto-forward toggle

---

**© 2025 Art-Net Controller. All rights reserved.**
