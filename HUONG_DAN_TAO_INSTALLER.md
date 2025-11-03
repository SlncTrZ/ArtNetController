# HƯỚNG DẪN TẠO FILE CÀI ĐẶT DMX MASTER

## 📥 Cài đặt Inno Setup

1. **Download Inno Setup**:
   - Truy cập: https://jrsoftware.org/isdl.php
   - Tải file: `innosetup-6.x.x.exe`
   - Chạy và cài đặt (Next → Next → Install)

2. **Kiểm tra cài đặt**:
   ```
   C:\Program Files (x86)\Inno Setup 6\ISCC.exe
   ```

## 🔨 Tạo file cài đặt

### Cách 1: Sử dụng script tự động (Khuyến nghị)

1. **Build executable**:
   ```
   Chạy: build.bat
   Đợi: 2-5 phút
   Kết quả: dist\DMXMaster.exe
   ```

2. **Build installer**:
   ```
   Chạy: build_installer.bat
   Đợi: 30 giây - 1 phút
   Kết quả: installer_output\DMXMaster_Setup_v1.0.0.exe
   ```

### Cách 2: Build thủ công

1. Build exe: `build.bat`
2. Mở Inno Setup Compiler
3. File → Open → Chọn `DMXMaster_Setup.iss`
4. Build → Compile
5. Lấy file tại `installer_output\`

## ✨ File cài đặt có gì?

### Tính năng chuyên nghiệp:

✅ **Tự động phát hiện phiên bản cũ**
   - Hỏi: "Đã có DMX Master cũ, bạn muốn nâng cấp?"
   - Tự động gỡ version cũ
   - GIỮ NGUYÊN data (shows, music, settings)

✅ **Chọn vị trí cài đặt**
   - Ổ C:\, D:\, E:\,... tuỳ ý
   - Mặc định: `C:\Program Files\DMX Master\`

✅ **Tạo shortcuts tự động**
   - Start Menu
   - Desktop (tùy chọn)
   - Quick Launch (tùy chọn)

✅ **Bảo vệ dữ liệu người dùng**
   - Folder `data\shows\` - KHÔNG BAO GIỜ BỊ XÓA
   - Folder `data\audio\` - KHÔNG BAO GIỜ BỊ XÓA
   - Folder `config\` - Giữ nguyên khi update

✅ **Gỡ cài đặt thông minh**
   - Hỏi: "Bạn có muốn giữ lại data không?"
   - YES: Giữ shows & music (để cài lại sau)
   - NO: Xóa toàn bộ

## 🔄 Quy trình Update

### Khi ra phiên bản mới:

1. **Tăng version** trong `DMXMaster_Setup.iss`:
   ```
   #define MyAppVersion "1.0.1"  ← Đổi từ 1.0.0
   ```

2. **Build lại**:
   ```
   build.bat                    ← Build exe mới
   build_installer.bat          ← Build installer mới
   ```

3. **Gửi cho user**:
   ```
   DMXMaster_Setup_v1.0.1.exe
   ```

### User cài update:

1. **Chạy installer mới**
2. **Installer tự động**:
   - Phát hiện version 1.0.0 đang cài
   - Hỏi: "Bạn muốn nâng cấp lên 1.0.1?"
   - Gỡ 1.0.0 (GIỮ NGUYÊN data)
   - Cài 1.0.1 mới
3. **Kết quả**: Version mới, data cũ giữ nguyên!

## 📁 Cấu trúc sau khi cài

```
C:\Program Files\DMX Master\
├── DMXMaster.exe              ← App chính
├── assets\
│   └── DMXMaster.ico          ← Icon
├── config\                    ← Settings (giữ nguyên khi update)
│   └── *.json
├── data\                      ← KHÔNG BAO GIỜ BỊ XÓA
│   ├── shows\                 ← Shows của user
│   │   ├── show1.json
│   │   └── show2.json
│   └── audio\                 ← Music của user
│       ├── song1.mp3
│       └── song2.mp3
├── logs\                      ← Log files
├── README.txt
└── LICENSE.txt
```

## 📤 Gửi cho khách hàng

### File cần gửi:
```
DMXMaster_Setup_v1.0.0.exe     (1 file duy nhất, ~10-15MB)
```

### Hướng dẫn khách hàng:

```
HƯỚNG DẪN CÀI ĐẶT DMX MASTER
============================

1. Double-click file: DMXMaster_Setup_v1.0.0.exe

2. Chọn ngôn ngữ: Tiếng Việt hoặc English

3. Đọc License Agreement → Chọn "I accept" → Next

4. Chọn vị trí cài đặt:
   - Mặc định: C:\Program Files\DMX Master
   - Hoặc chọn ổ khác: D:\, E:\,...

5. Chọn tạo Desktop shortcut (khuyến nghị) → Next

6. Click Install → Đợi 30 giây

7. Hoàn tất! Click "Launch DMX Master" để chạy ngay.

LƯU Ý:
- Lần đầu chạy: Windows Firewall sẽ hỏi → Chọn "Allow"
- Trial: 7 ngày miễn phí (full tính năng)
- License: Liên hệ truongcongdinh97tcd@gmail.com
```

## 🎯 Ví dụ thực tế

### Tình huống: User đang dùng v1.0.0, bạn ra v1.0.1

**User có:**
- DMX Master v1.0.0 đã cài
- 50 show files trong `data\shows\`
- 100 file nhạc trong `data\audio\`
- Settings đã config sẵn

**Bạn gửi:** `DMXMaster_Setup_v1.0.1.exe`

**User chạy installer v1.0.1:**
1. Installer detect: "Đã có v1.0.0"
2. Hỏi: "Nâng cấp lên v1.0.1?"
3. User chọn: YES
4. Installer:
   - Gỡ DMXMaster.exe cũ
   - GIỮ NGUYÊN 50 shows
   - GIỮ NGUYÊN 100 nhạc
   - GIỮ NGUYÊN settings
   - Cài DMXMaster.exe mới
5. User mở app: Mọi thứ vẫn còn! ✅

## ❓ Câu hỏi thường gặp

### 1. Tôi muốn thay đổi vị trí cài mặc định?
Sửa file `DMXMaster_Setup.iss`:
```
DefaultDirName={autopf}\{#MyAppName}     ← Mặc định Program Files
DefaultDirName=D:\DMXMaster              ← Đổi thành D:\
```

### 2. Installer quá lớn (>50MB)?
- Kiểm tra: Có thêm data thừa không?
- Normal size: 10-15MB
- Nếu quá lớn: Xóa file test, audio sample lớn

### 3. Làm sao để installer tự động chạy khi cắm USB?
Tạo file `autorun.inf`:
```
[autorun]
open=DMXMaster_Setup_v1.0.0.exe
icon=DMXMaster_Setup_v1.0.0.exe,0
label=DMX Master Installer
```

### 4. User không có quyền admin?
Installer yêu cầu admin. User phải:
- Right-click → Run as Administrator
- Hoặc nhập password admin

### 5. Antivirus chặn installer?
Bình thường! Giải pháp:
- Sign code với certificate (tốn tiền)
- Hoặc: Hướng dẫn user tắt antivirus tạm thời
- Hoặc: Upload lên VirusTotal để scan

## 📧 Hỗ trợ

Mọi thắc mắc liên hệ:
**Email**: truongcongdinh97tcd@gmail.com

---
© 2025 DMX Master - Professional Installer System
