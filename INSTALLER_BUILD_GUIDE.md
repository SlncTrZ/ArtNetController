# DMX Master - Build Installer Guide

## 📋 Yêu cầu

### 1. Inno Setup Compiler
Download và cài đặt Inno Setup:
- **Link**: https://jrsoftware.org/isdl.php
- **Version**: 6.x hoặc mới hơn
- **Cài đặt mặc định**: `C:\Program Files (x86)\Inno Setup 6\`

### 2. Build executable trước
```bash
build.bat
```
Phải có file `dist\DMXMaster.exe` trước khi build installer.

## 🚀 Cách build installer

### Bước 1: Build executable
```bash
build.bat
```

### Bước 2: Build installer
```bash
build_installer.bat
```

### Kết quả
File installer sẽ được tạo tại:
```
installer_output\DMXMaster_Setup_v1.0.0.exe
```

## ✨ Tính năng Installer

### 1. **Auto-Update Detection**
- Tự động phát hiện phiên bản cũ
- Gỡ cài đặt tự động trước khi upgrade
- Giữ nguyên data người dùng

### 2. **Data Preservation**
Các folder này KHÔNG bị ghi đè khi update:
- `data\shows\` - Show files của user
- `data\audio\` - Music files
- `config\` - Settings (nếu đã tồn tại)

### 3. **Flexible Installation**
- Cho phép chọn ổ đĩa (C:\, D:\, E:\, etc.)
- Mặc định: `C:\Program Files\DMX Master\`
- Tạo shortcuts tự động

### 4. **Uninstall Options**
Khi gỡ cài đặt, user được hỏi:
- **YES**: Giữ lại data (để cài lại sau)
- **NO**: Xóa toàn bộ

### 5. **Professional Features**
- License agreement screen
- Installation info screen
- Modern wizard UI
- Desktop shortcut option
- Start menu shortcuts
- Registry entries
- File associations (optional)

## 📁 Cấu trúc Installer

```
DMXMaster_Setup_v1.0.0.exe
├── DMXMaster.exe           ← Main app
├── assets\
│   └── DMXMaster.ico       ← Icon (always updated)
├── config\
│   └── *.json              ← Templates (if not exists)
├── data\
│   ├── shows\
│   │   └── example_show.json  ← Sample (if not exists)
│   └── audio\
│       └── .gitkeep
├── README.txt
└── LICENSE.txt
```

## 🔄 Update Workflow

### Khi user cài version mới:

1. **Installer detect old version**
   ```
   "An existing installation was detected. 
    Do you want to upgrade?"
   ```

2. **Auto-uninstall old version**
   - Giữ nguyên `data\` folder
   - Xóa file executable cũ
   - Cập nhật registry

3. **Install new version**
   - Copy executable mới
   - Update assets
   - Giữ nguyên config (nếu có)
   - Giữ nguyên data

4. **Result**: Version mới, data cũ giữ nguyên! ✅

## 🎯 Phân phối

### File cần gửi cho user:
```
DMXMaster_Setup_v1.0.0.exe  (single file, ~10-15MB)
```

### User chỉ cần:
1. Double-click installer
2. Chọn ổ đĩa
3. Chọn tạo shortcut (optional)
4. Click Install

### Khi có update:
1. Chạy installer mới
2. Chọn Yes để upgrade
3. Data tự động được giữ nguyên

## 📝 Lưu ý

### Registry Keys
Installer tạo registry entries:
```
HKEY_LOCAL_MACHINE\Software\Truong Cong Dinh\DMX Master\
├── InstallPath: "C:\Program Files\DMX Master"
└── Version: "1.0.0"
```

### AppData
License files được lưu tại:
```
C:\ProgramData\DMX Master\
└── (được tạo tự động khi chạy app)
```

### Firewall
Installer KHÔNG tự động thêm firewall rule.
User phải allow manually khi Windows hỏi lần đầu chạy.

## 🐛 Troubleshooting

### "Inno Setup not found"
- Cài đặt Inno Setup từ link ở trên
- Kiểm tra path: `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`
- Hoặc sửa path trong `build_installer.bat`

### "DMXMaster.exe not found"
- Chạy `build.bat` trước
- Kiểm tra file tồn tại: `dist\DMXMaster.exe`

### Installer size quá lớn
- Normal size: 10-15MB
- Nếu > 50MB: Kiểm tra có include thừa data không

## 📧 Support

Email: truongcongdinh97tcd@gmail.com

---
**DMX Master Installer System**
Professional deployment solution with auto-update support
