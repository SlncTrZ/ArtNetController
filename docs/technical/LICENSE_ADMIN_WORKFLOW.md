# License Admin Workflow — DMX Master LTS

> Version: 1.3.0 | Updated: 2026-05-02

## Tổng quan

License system sử dụng RSA-2048 signature + AES-256-GCM encryption. Admin giữ private key để ký license, app dùng public key (embedded) để verify offline.

## Quy trình cấp license

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│  User     │     │  Admin   │     │  License Gen  │     │  User    │
│  Request  │────►│  Verify  │────►│  Tool         │────►│  Activate│
│  DeviceID │     │  Payment │     │  (RSA Sign)   │     │  App     │
└──────────┘     └──────────┘     └──────────────┘     └──────────┘
```

### Bước 1: User lấy Device ID
1. Mở DMX Master LTS → Settings → License tab
2. Click "Copy Device ID"
3. Gửi Device ID cho admin (64-char hex string)

### Bước 2: Admin tạo license
1. Mở `tools/Create_License_V1.5.py`
2. Nhập:
   - **Device ID** (từ user)
   - **Customer Email**
   - **License Type** (standard / professional)
3. Tool tự động:
   - Generate unique License ID (UUID)
   - Tạo RSA-2048 signature: `Sign(DeviceID + LicenseID + Timestamp)`
   - Output: JSON string cho user

### Bước 3: User activate
1. Paste license JSON vào app
2. App verify:
   - Device ID match?
   - RSA signature valid?
   - Encrypt với AES-256-GCM (key derived từ hardware)
   - Save thành `license.lic`

## Công cụ Admin

### Generate RSA Keys (chạy 1 lần)
```bash
python tools/generate_rsa_keys.py
# Output: tools/rsa_keys/private_key.pem, public_key.pem
```

### Tạo License
```bash
python tools/Create_License_V1.5.py
# Hoặc dùng batch: tools/build_license_generator.bat
```

### Kiểm tra Device ID
```bash
python tools/get_device_id.py
```

### Verify License
```bash
python tools/check_license.py
```

## License Tiers

| Tier | Universes | Trial | Price |
|------|-----------|-------|-------|
| FREE | 4 | 7 days | $0 |
| LICENSED | 512 | N/A | Contact |

## Revocation (Online)

- App check revocation mỗi 24h (background thread)
- Admin revoke qua license server: `POST /api/license/revoke`
- Cache offline: fail-open nếu không có internet

## Security Notes

- **Private key**: KHÔNG bao giờ commit lên git. `tools/rsa_keys/` trong `.gitignore`
- **License file**: AES-256-GCM encrypted, chỉ decrypt được trên máy đã generate Device ID
- **SSRF protection**: Revocation URL validated trước khi request
- **SSL**: Certificate validation bắt buộc cho tất cả HTTPS connections

## Troubleshooting

| Vấn đề | Nguyên nhân | Fix |
|---------|-------------|-----|
| "Device ID mismatch" | License tạo cho máy khác | Tạo lại license với Device ID đúng |
| "Invalid signature" | Private/public key mismatch | Đảm bảo dùng cùng key pair |
| "License decryption failed" | File corrupted hoặc sai máy | Xóa license.lic, activate lại |
| "Trial expired" | Hết 7 ngày | Activate license |