# Create License for Customer V1.5

## 📋 Tổng Quan

**Create License for Customer V1.5** là công cụ chuyên nghiệp để tạo license cho DMX Master, hỗ trợ tất cả các máy tính trên toàn thế giới.

### ✨ Tính Năng Chính

- ✅ Tạo license cho **BẤT KỲ** máy tính nào trên thế giới
- ✅ Hỗ trợ 3 loại license: Perpetual, Trial, Subscription
- ✅ Giao diện đẹp, dễ sử dụng
- ✅ Tự động validate input
- ✅ Copy to clipboard hoặc save to file
- ✅ Sử dụng thuật toán PSS chính xác như GUI
- ✅ Không cần thiết lập môi trường Python

---

## 🚀 Cách Sử Dụng

### Bước 1: Lấy Device ID từ khách hàng

Yêu cầu khách hàng:
1. Mở DMX Master
2. Vào menu **Help → About**
3. Copy **Device ID** (chuỗi 64 ký tự)
4. Gửi Device ID cho bạn

### Bước 2: Tạo License

1. **Chạy file exe:**
   ```
   Create License for Customer V1.5.exe
   ```

2. **Nhập thông tin:**
   - **Device ID**: Paste Device ID từ khách hàng (64 ký tự)
   - **Customer Email**: Email của khách hàng
   - **License Type**: Chọn loại license
     - `perpetual`: Vĩnh viễn (mặc định)
     - `trial`: Dùng thử
     - `subscription`: Theo tháng

3. **Tạo license:**
   - Click nút **"🔨 Generate License"**
   - License JSON sẽ hiển thị trong ô output

4. **Gửi cho khách hàng:**
   - Click **"📋 Copy to Clipboard"** để copy
   - Hoặc click **"💾 Save to File"** để lưu file

### Bước 3: Hướng Dẫn Khách Hàng

Gửi file license cho khách hàng và hướng dẫn:

1. Lưu file với tên: **`license.lic`** hoặc **`license.json`**
2. Copy vào thư mục: **`config/license.lic`** trong thư mục cài đặt DMX Master
3. Khởi động lại DMX Master
4. License sẽ được kích hoạt tự động

---

## 🔒 Bảo Mật

### Thuật Toán Mã Hóa

- **Algorithm**: RSA-2048
- **Padding**: PSS (Probabilistic Signature Scheme)
- **Hash**: SHA256
- **MGF**: MGF1 with SHA256
- **Salt Length**: MAX_LENGTH
- **Encoding**: Base64

### Signature Payload

```python
signature_payload = f"{device_id}{license_id}{issued_date}".encode()
```

### Validation

License chỉ hoạt động trên máy tính có Device ID khớp chính xác. Device ID được tạo từ:

```python
SHA256(MAC_address + hostname + processor + Windows_UUID)
```

---

## 📂 Cấu Trúc File

```
tools/
├── Create License for Customer V1.5.exe   ← File thực thi
├── Create_License_V1.5.py                  ← Source code
├── Create_License_V1.5.spec                ← PyInstaller spec
├── rsa_keys/
│   ├── private_key.pem                     ← Private key (BẢO MẬT!)
│   └── public_key.pem                      ← Public key
└── README_Create_License_V1.5.md          ← File này
```

---

## ⚠️ LƯU Ý QUAN TRỌNG

### 🔐 Bảo Vệ Private Key

**TUYỆT ĐỐI KHÔNG chia sẻ file `private_key.pem`!**

- Private key được sử dụng để ký license
- Nếu bị lộ, người khác có thể tạo license không giới hạn
- Chỉ giữ trên máy tính bảo mật
- Backup ở nơi an toàn

### ✅ Device ID Phải Chính Xác

- Device ID phải đúng **64 ký tự hex** (0-9, a-f)
- Lấy trực tiếp từ DMX Master của khách hàng
- Không tự tạo hoặc đoán

### 🌍 Hỗ Trợ Toàn Cầu

License được tạo có thể dùng trên **BẤT KỲ** máy tính nào trên thế giới, miễn là:

1. Device ID khớp chính xác
2. File `license.lic` được đặt đúng vị trí
3. Signature hợp lệ

---

## 🛠️ Troubleshooting

### Lỗi: "Private key not found"

**Nguyên nhân**: Không tìm thấy `rsa_keys/private_key.pem`

**Giải pháp**:
```
tools/
└── rsa_keys/
    └── private_key.pem  ← Đảm bảo file này tồn tại
```

### Lỗi: "Device ID must be 64 characters"

**Nguyên nhân**: Device ID không đúng định dạng

**Giải pháp**:
- Kiểm tra lại Device ID từ khách hàng
- Phải là chuỗi hex 64 ký tự
- Ví dụ: `0dc2b4c6b3d94797e854b82cf6451d0d13e7f604ca86a341bd4069e7ce8e6807`

### Lỗi: "Invalid license key" khi khách hàng kích hoạt

**Nguyên nhân**: Device ID không khớp

**Giải pháp**:
1. Yêu cầu khách hàng gửi lại Device ID chính xác
2. Tạo license mới với Device ID đúng
3. Gửi lại cho khách hàng

---

## 📊 Output Format

License được tạo có định dạng JSON:

```json
{
  "device_id": "0dc2b4c6b3d94797e854b82cf6451d0d13e7f604ca86a341bd4069e7ce8e6807",
  "license_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
  "issued_date": "2025-11-04T14:30:00.123456",
  "customer_email": "customer@example.com",
  "license_type": "perpetual",
  "version": "1.0.0",
  "signature": "CTChW3pGtBcNjSQueUcXvMT4UPIpfTICaIGr24YkZZXNC5IY..."
}
```

---

## 📞 Support

**Developer**: Trương Công Định

**Version**: 1.5

**Date**: 2025-11-04

**Repository**: truongcongdinh97/DMX-Master

---

## 📝 Change Log

### Version 1.5 (2025-11-04)
- ✅ Tạo công cụ độc lập với GUI chuyên nghiệp
- ✅ Hỗ trợ tạo license cho mọi máy tính trên thế giới
- ✅ Sử dụng thuật toán PSS chính xác
- ✅ Copy to clipboard và save to file
- ✅ Validation tự động
- ✅ Build thành file exe độc lập (37.83 MB)

### Version 1.0 (2025-11-03)
- Initial release với tool command-line

---

## 🎯 Best Practices

### Khi Tạo License

1. ✅ Luôn verify Device ID với khách hàng
2. ✅ Ghi nhớ email khách hàng để track license
3. ✅ Chọn đúng loại license (perpetual/trial/subscription)
4. ✅ Test license trước khi gửi cho khách hàng
5. ✅ Lưu backup license đã tạo

### Khi Gửi Cho Khách Hàng

1. ✅ Gửi kèm hướng dẫn cài đặt
2. ✅ Hướng dẫn vị trí file: `config/license.lic`
3. ✅ Nhắc nhở restart DMX Master
4. ✅ Hỏi khách hàng xác nhận kích hoạt thành công

### Bảo Mật

1. ✅ Không share private key
2. ✅ Không commit private key lên Git
3. ✅ Backup private key ở nơi an toàn
4. ✅ Chỉ chạy tool trên máy tính bảo mật

---

**🎉 ENJOY CREATING LICENSES FOR YOUR CUSTOMERS! 🎉**
