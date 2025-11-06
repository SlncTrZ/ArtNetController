# 🚀 CÁC BƯỚC UPLOAD LÊN GITHUB - CHO TRUONG CONG DINH

## ⚡ HƯỚNG DẪN NHANH (3 PHÚT)

### Bước 1: Mở PowerShell tại thư mục project

```powershell
# Mở PowerShell và cd vào project
cd H:\VSCode\ArtNetController
```

### Bước 2: Kiểm tra Git đã cài chưa

```powershell
git --version
```

**Nếu chưa có Git:**
- Download: https://git-scm.com/downloads
- Cài đặt
- Restart PowerShell

### Bước 3: Chạy script tự động

```powershell
# Chạy script upload
.\git_push.bat
```

Script sẽ hỏi bạn:
1. **Commit message:** Nhấn Enter (dùng message mặc định)
2. **GitHub credentials:**
   - Username: `truongcongdinh97`
   - Password: **SỬ DỤNG PERSONAL ACCESS TOKEN** (không phải password GitHub)

### Bước 4: Tạo Personal Access Token (nếu chưa có)

1. Mở: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Đặt tên: `DMX-Master-Upload`
4. Chọn scope: **✅ repo** (tất cả)
5. Click **"Generate token"**
6. **COPY TOKEN** (ghp_abc123xyz...)
7. **LƯU LẠI** (chỉ hiện 1 lần!)

### Bước 5: Nhập token khi push

```
Username: truongcongdinh97
Password: [PASTE TOKEN Ở ĐÂY]
```

### Bước 6: Verify

Mở browser: https://github.com/truongcongdinh97/DMX-Master

**Nếu thấy code → THÀNH CÔNG!** ✅

---

## 🔒 KIỂM TRA BẢO MẬT TRƯỚC KHI PUSH

**QUAN TRỌNG:** Trước khi chạy `git_push.bat`, check:

```powershell
# Kiểm tra file nhạy cảm
Get-ChildItem -Path . -Filter "private_key.pem" -Recurse
Get-ChildItem -Path . -Filter "*.lic" -Recurse
```

**Kết quả phải thấy:**
- ✅ `tools\rsa_keys\private_key.pem` - File TỒN TẠI local
- ❌ **NHƯNG** sẽ KHÔNG được upload (nhờ .gitignore)

**Verify .gitignore hoạt động:**
```powershell
# Sau khi chạy git add (trong script)
# Chạy lệnh này:
git check-ignore tools\rsa_keys\private_key.pem
```

**Kết quả:** `tools/rsa_keys/private_key.pem`

→ Nghĩa là file BỊ IGNORE (an toàn!) ✅

---

## 📋 MANUAL STEPS (Nếu Script Lỗi)

### 1. Init Git
```powershell
git init
```

### 2. Configure User
```powershell
git config user.name "Truong Cong Dinh"
git config user.email "truongcongdinh97@gmail.com"
```

### 3. Add Remote
```powershell
git remote add origin https://github.com/truongcongdinh97/DMX-Master.git
```

### 4. Check .gitignore
```powershell
cat .gitignore
```

Phải có dòng:
```
tools/rsa_keys/private_key.pem
*.pem
config/license.lic
```

### 5. Stage Files
```powershell
git add .
```

### 6. Check Staged
```powershell
git status
```

**ĐỪNG THẤY:**
- ❌ `tools/rsa_keys/private_key.pem`
- ❌ `config/license.lic`

**NẾU THẤY → DỪNG LẠI! XÓA NGAY:**
```powershell
git rm --cached tools/rsa_keys/private_key.pem
git rm --cached config/license.lic
```

### 7. Commit
```powershell
git commit -m "🚀 Initial upload: DMX-Master project"
```

### 8. Push
```powershell
git push -u origin main
```

Nhập:
- Username: `truongcongdinh97`
- Password: `[YOUR_GITHUB_TOKEN]`

---

## 🛠️ TROUBLESHOOTING

### Lỗi 1: "Repository not found"

**Giải pháp:**
1. Vào https://github.com/new
2. Tạo repo tên: `DMX-Master`
3. **KHÔNG** chọn "Initialize with README"
4. Click "Create repository"
5. Chạy lại `git push`

---

### Lỗi 2: "Permission denied"

**Giải pháp:**
- Token sai hoặc hết hạn
- Tạo token mới: https://github.com/settings/tokens
- Scope phải có **repo**

---

### Lỗi 3: "Private key was uploaded!"

**NGUY HIỂM!**

```powershell
# 1. Remove from Git history
git filter-branch --force --index-filter `
  "git rm --cached --ignore-unmatch tools/rsa_keys/private_key.pem" `
  --prune-empty --tag-name-filter cat -- --all

# 2. Force push
git push origin --force --all

# 3. REGENERATE KEYS
cd tools
python generate_rsa_keys.py

# 4. Update app
# Copy new public key to src/utils/license.py
```

---

## ✅ SAU KHI UPLOAD THÀNH CÔNG

### 1. Verify trên GitHub
https://github.com/truongcongdinh97/DMX-Master

Check:
- ✅ README hiển thị
- ✅ Code đầy đủ
- ✅ **KHÔNG** thấy private_key.pem

### 2. Clone thử
```powershell
cd C:\Temp
git clone https://github.com/truongcongdinh97/DMX-Master.git test
cd test
dir
```

Verify:
- ✅ Files đầy đủ
- ❌ Không có private_key.pem (correct!)

### 3. Test app
```powershell
pip install -r requirements.txt
python main.py
```

App phải chạy được!

---

## 🔄 CẬP NHẬT SAU NÀY

Khi có thay đổi code:

```powershell
cd H:\VSCode\ArtNetController

# Stage changes
git add .

# Commit
git commit -m "📝 Update: mô tả thay đổi"

# Push
git push
```

**Không cần nhập credentials lần 2!** (đã lưu)

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề:

1. **Đọc lại:** `GITHUB_UPLOAD_GUIDE.md`
2. **Check:** `PRE_UPLOAD_CHECKLIST.md`
3. **Email:** truongcongdinh97@gmail.com (tự hỗ trợ 😄)

---

## 🎯 TÓM TẮT 1 DÒNG

```powershell
# Chạy script này → Xong!
.\git_push.bat
```

**Đơn giản vậy thôi!** 🚀

---

*Chúc may mắn! - Trương Công Định* 😊
