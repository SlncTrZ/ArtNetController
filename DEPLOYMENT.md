# DMX Master - Deployment Package

## 📦 Nội dung Package

Khi deploy DMX Master lên máy khác, cần copy các file/folder sau:

```
DMXMaster/
├── DMXMaster.exe          ← File thực thi chính
├── assets/
│   └── DMXMaster.ico      ← Icon ứng dụng
├── data/
│   └── shows/             ← Thư mục chứa show files
├── config/                ← (Tự động tạo khi chạy lần đầu)
└── logs/                  ← (Tự động tạo khi chạy lần đầu)
```

## 🚀 Hướng dẫn Cài đặt

### Cách 1: Copy thủ công

1. **Tạo folder mới** trên máy đích:
   ```
   C:\DMXMaster\
   ```

2. **Copy các file sau**:
   - `dist\DMXMaster.exe` → `C:\DMXMaster\DMXMaster.exe`
   - `assets\` → `C:\DMXMaster\assets\`
   - `data\` → `C:\DMXMaster\data\`

3. **Chạy ứng dụng**:
   - Double-click `DMXMaster.exe`

### Cách 2: Sử dụng script deploy (khuyến nghị)

Chạy `deploy.bat` để tự động tạo package deployment

## ⚙️ Yêu cầu hệ thống

- **OS**: Windows 10/11 (64-bit)
- **RAM**: Tối thiểu 4GB
- **Disk**: 100MB trống
- **Network**: Port 6454 (Art-Net), Port 8080 (Web Server)

## 📝 Lưu ý

### Khi chạy lần đầu:
- App sẽ tự động tạo folder `config` và `logs`
- Timezone mặc định: UTC
- Trial mode: 7 ngày

### License Activation:
1. Copy Device ID từ **Help → License Activation**
2. Gửi Device ID cho admin
3. Nhận file license JSON
4. **Help → License Activation → Load from File**
5. Chọn file JSON nhận được

### Firewall:
Nếu Windows Firewall chặn, cho phép:
- Python.exe (khi chạy từ source)
- DMXMaster.exe (khi chạy file build)
- Port: 6454 (UDP), 8080 (TCP)

## 🔧 Troubleshooting

### App không khởi động:
- Kiểm tra Windows Defender/Antivirus
- Chạy với quyền Administrator
- Xem file log trong `logs\` folder

### Không nhận được Art-Net:
- Kiểm tra Firewall
- Kiểm tra IP address
- Test với `ping <ip_address>`

### License không activate:
- Xóa file `%APPDATA%\ArtNetController\license.lic`
- Restart app
- Activate lại với file JSON mới

## 📧 Hỗ trợ

Email: truongcongdinh97tcd@gmail.com

---
© 2025 DMX Master v1.0.0
