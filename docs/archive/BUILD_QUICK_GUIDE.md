# HƯỚNG DẪN BUILD NHANH

## ✅ Cách build ĐÚNG (chỉ 1 lệnh):

```bash
cd H:\VSCode\ArtNetController
.\build.bat
```

Hoặc:

```bash
pyinstaller --clean DMXMaster_Complete.spec
```

## ❌ KHÔNG dùng các lệnh này (thiếu dependencies):

```bash
# SAI - Thiếu PyQt6, Flask...
pyinstaller main.py

# SAI - Spec file cũ thiếu dependencies  
pyinstaller DMXMaster.spec

# SAI - Command line thiếu nhiều hidden imports
pyinstaller --onefile main.py
```

## 📋 Spec file đúng:

- File: `DMXMaster_Complete.spec`
- Có đầy đủ: PyQt6, Flask, Cryptography, Pygame, logging.handlers, platform...
- Kích thước exe: ~65-70 MB (nếu nhỏ hơn 10MB = thiếu dependencies!)

## 🔍 Kiểm tra sau build:

```powershell
# 1. Kiểm tra size (phải > 60 MB)
Get-Item dist\DMXMaster.exe | Select Name, @{N="Size(MB)";E={[math]::Round($_.Length/1MB, 2)}}

# 2. Test chạy
.\dist\DMXMaster.exe

# 3. Nếu lỗi "No module named 'XXX'" → Build lại với DMXMaster_Complete.spec
```

## 🚀 Tạo installer:

```bash
.\build_installer.bat
```

File output: `installer_output\DMXMaster_Setup_v1.0.0.exe`

---
**LƯU Ý QUAN TRỌNG**: Luôn dùng `DMXMaster_Complete.spec` - đã có đầy đủ tất cả dependencies!
