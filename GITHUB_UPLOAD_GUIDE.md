# 📤 Hướng Dẫn Upload Lên GitHub

## ⚡ Cách 1: Sử Dụng Script Tự Động (Khuyến Nghị)

### Windows:
```batch
# Chạy script tự động
git_push.bat
```

### Linux/Mac:
```bash
# Cho phép thực thi
chmod +x git_push.sh

# Chạy script
./git_push.sh
```

Script sẽ tự động:
1. ✅ Init Git repository
2. ✅ Configure user info
3. ✅ Add remote GitHub
4. ✅ Stage files (theo .gitignore)
5. ✅ Commit changes
6. ✅ Push to GitHub

---

## ⚡ Cách 2: Thủ Công (Step by Step)

### Bước 1: Cài Git (Nếu Chưa Có)

**Windows:**
- Download: https://git-scm.com/downloads
- Install với cài đặt mặc định

**Linux:**
```bash
sudo apt install git
```

### Bước 2: Cấu Hình Git

```bash
cd H:\VSCode\ArtNetController

# Cấu hình thông tin
git config --global user.name "Truong Cong Dinh"
git config --global user.email "truongcongdinh97@gmail.com"
```

### Bước 3: Khởi Tạo Repository

```bash
# Init Git
git init

# Add remote GitHub
git remote add origin https://github.com/truongcongdinh97/DMX-Master.git
```

### Bước 4: Kiểm Tra .gitignore

```bash
# Xem file nào sẽ được commit
git status

# QUAN TRỌNG: Đảm bảo các file này KHÔNG có trong list:
# ❌ tools/rsa_keys/private_key.pem
# ❌ config/license.lic
# ❌ *.pem files
```

### Bước 5: Stage & Commit

```bash
# Stage tất cả files
git add .

# Xem lại files đã stage
git status

# Commit
git commit -m "🚀 Initial commit: DMX-Master with secure license system"
```

### Bước 6: Tạo Personal Access Token (GitHub)

**Vì GitHub không còn cho phép dùng password, bạn cần tạo token:**

1. Vào: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Đặt tên: `DMX-Master Upload`
4. Chọn scope: **✅ repo** (tất cả quyền repo)
5. Click **"Generate token"**
6. **SAO CHÉP TOKEN** (chỉ hiển thị 1 lần!)
   - Ví dụ: `ghp_abc123xyz456...`

### Bước 7: Push Lên GitHub

```bash
# Push lên GitHub
git push -u origin main

# Khi được hỏi credentials:
# Username: truongcongdinh97
# Password: <PASTE TOKEN VỪA TẠO>
```

**Lưu token để sau này dùng lại!**

### Bước 8: Verify

Mở trình duyệt:
```
https://github.com/truongcongdinh97/DMX-Master
```

Bạn sẽ thấy code đã được upload! ✅

---

## 🔒 Bảo Mật: Kiểm Tra Trước Khi Push

### ❌ KHÔNG BAO GIỜ Upload Những File Này:

```bash
# Check xem các file nhạy cảm có trong staging không
git ls-files | grep -E "(private_key|\.pem|license\.lic)"

# Nếu có kết quả → NGUY HIỂM!
# Xóa khỏi staging:
git rm --cached tools/rsa_keys/private_key.pem
```

### ✅ File .gitignore Đã Bảo Vệ:

```gitignore
# Những dòng này trong .gitignore bảo vệ bạn:
tools/rsa_keys/private_key.pem
tools/rsa_keys/*.pem
config/license.lic
*.pem
*.key
*.priv
```

### 🔍 Kiểm Tra Lần Cuối:

```bash
# Xem tất cả files sẽ được push
git ls-tree -r main --name-only

# Tìm file nhạy cảm
git ls-tree -r main --name-only | grep -i "private\|secret\|key\.pem"

# Kết quả phải RỖNG! Nếu có → DỪNG LẠI!
```

---

## 🔄 Cập Nhật Sau Này

### Sau khi đã push lần đầu, các lần sau:

```bash
# 1. Stage changes
git add .

# 2. Commit
git commit -m "📝 Update: your description here"

# 3. Push
git push
```

**Không cần thêm credentials nếu đã lưu token!**

---

## 🌿 Tạo Branch Riêng (Optional)

Nếu bạn muốn giữ code cũ an toàn:

```bash
# Tạo branch development
git checkout -b development

# Push branch mới
git push -u origin development

# Sau này merge vào main:
git checkout main
git merge development
git push
```

---

## 🗂️ Cấu Trúc Repository Sau Khi Upload

```
https://github.com/truongcongdinh97/DMX-Master
│
├── README.md                    ← Mô tả dự án
├── LICENSE                      ← License file
├── .gitignore                   ← Bảo vệ file nhạy cảm
├── requirements.txt             ← Python dependencies
│
├── src/                         ← Source code
│   ├── gui/                     ← GUI components
│   ├── artnet/                  ← Art-Net protocol
│   ├── utils/                   ← Utilities
│   │   └── license.py          ← License system (source)
│   └── ...
│
├── tools/                       ← Admin tools
│   ├── generate_rsa_keys.py    ← Key generator
│   ├── generate_license.py     ← License signer
│   └── rsa_keys/
│       ├── public_key.pem      ← ✅ Safe to upload
│       └── (private_key.pem)   ← ❌ EXCLUDED by .gitignore
│
├── docs/                        ← Documentation
│   ├── ADMIN_TOOLS_README.md
│   ├── SECURITY_ARCHITECTURE.md
│   └── ...
│
└── config/                      ← Config (empty in repo)
    └── .gitkeep
```

---

## ❓ Troubleshooting

### Issue 1: "Repository not found"

**Nguyên nhân:** Repository chưa tồn tại trên GitHub

**Giải pháp:**
1. Vào https://github.com/new
2. Tạo repo tên: `DMX-Master`
3. **Không** chọn "Initialize with README"
4. Chạy lại `git push`

---

### Issue 2: "Permission denied"

**Nguyên nhân:** Token sai hoặc hết hạn

**Giải pháp:**
1. Tạo token mới: https://github.com/settings/tokens
2. Copy token
3. Chạy:
   ```bash
   git push
   # Nhập token vào password
   ```

---

### Issue 3: "Private key uploaded!"

**NGUY HIỂM!** Nếu bạn vô tình upload private key:

```bash
# 1. XÓA NGAY khỏi Git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch tools/rsa_keys/private_key.pem" \
  --prune-empty --tag-name-filter cat -- --all

# 2. Force push
git push origin --force --all

# 3. GENERATE NEW KEYS
python tools/generate_rsa_keys.py

# 4. Update public key in app
# Copy new public key to src/utils/license.py

# 5. RE-ISSUE all customer licenses
```

**Tốt nhất: Kiểm tra kỹ trước khi push!**

---

### Issue 4: "Too large file"

**Nguyên nhân:** File > 100MB (GitHub limit)

**Giải pháp:**
```bash
# Tìm file lớn
git ls-files | xargs du -h | sort -rh | head -10

# Xóa khỏi Git (nhưng giữ local)
git rm --cached path/to/large/file

# Add vào .gitignore
echo "path/to/large/file" >> .gitignore

# Commit & push
git commit -m "Remove large file"
git push
```

---

## 📊 Check Upload Thành Công

Sau khi push, verify bằng cách:

1. **Mở GitHub:**
   ```
   https://github.com/truongcongdinh97/DMX-Master
   ```

2. **Kiểm tra:**
   - ✅ README.md hiển thị đẹp
   - ✅ Source code đầy đủ
   - ✅ .gitignore hoạt động (private key KHÔNG có)
   - ✅ Badges hiển thị

3. **Clone thử từ GitHub:**
   ```bash
   cd /tmp
   git clone https://github.com/truongcongdinh97/DMX-Master.git test
   cd test
   ls -la
   # Verify structure đúng
   ```

---

## 🎯 Next Steps Sau Khi Upload

### 1. Tạo Release (Optional)

```bash
# Tag version
git tag -a v1.0.0 -m "Version 1.0.0 - First release"
git push origin v1.0.0
```

Trên GitHub:
1. Vào **Releases** → **Create new release**
2. Chọn tag: `v1.0.0`
3. Tiêu đề: `v1.0.0 - DMX-Master First Release`
4. Mô tả: Features, changes, download links
5. Attach compiled `.exe` hoặc `.zip` (nếu có)

### 2. Tạo GitHub Pages (Optional)

Cho documentation website:

1. Settings → Pages
2. Source: `main` branch, `/docs` folder
3. Save
4. Website: `https://truongcongdinh97.github.io/DMX-Master`

### 3. Setup GitHub Actions (Optional)

Tự động test & build:

Tạo `.github/workflows/test.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - run: pip install -r requirements.txt
      - run: pytest tests/
```

---

## 🎉 Hoàn Thành!

Bạn đã thành công upload DMX-Master lên GitHub! 🚀

**Repository:** https://github.com/truongcongdinh97/DMX-Master

**Nhớ:**
- ✅ Private key an toàn (không bị upload)
- ✅ Code được backup trên cloud
- ✅ Có thể clone về bất cứ đâu
- ✅ Collaborate với người khác (nếu muốn)

---

*Happy Coding! 💻✨*
