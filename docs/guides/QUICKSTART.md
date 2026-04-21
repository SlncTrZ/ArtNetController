# Quick Start Guide - V2.0 Production Features

Hướng dẫn nhanh để bắt đầu sử dụng 4 tính năng production của ArtNetController V2.0

## Bước 1: Cấu hình GitHub (5 phút)

### 1.1 Cập nhật thông tin repository

Mở file `src/system/update_manager.py` và thay đổi dòng 30-31:

```python
# THAY ĐỔI NÀY:
GITHUB_REPO_OWNER = "tên_github_của_bạn"  # VD: "nguyenvana"
GITHUB_REPO_NAME = "ArtNetController"
```

Mở file `src/system/crash_reporter.py` và thay đổi dòng 260-261:

```python
# THAY ĐỔI NÀY:
repo_owner = "tên_github_của_bạn"  # VD: "nguyenvana"
repo_name = "ArtNetController"
```

### 1.2 Tạo GitHub Personal Access Token (cho crash reporting)

1. Vào GitHub.com → Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Chọn quyền: `repo` và `write:discussion`
4. Copy token
5. Thêm vào `config.json`:

```json
{
  "crash_reporting": {
    "enabled": true,
    "github_token": "ghp_token_của_bạn_ở_đây"
  }
}
```

## Bước 2: Build lần đầu (10 phút)

### Trên Windows:

```powershell
# Cài dependencies (lần đầu)
pip install -r requirements.txt
pip install pyinstaller

# Build
python build_windows.py
```

Kết quả trong folder `dist/`:
- `ArtNetController-2.0.0-Setup.exe` - File cài đặt
- `ArtNetController-2.0.0-Portable.zip` - Bản portable

### Trên Raspberry Pi:

```bash
# Cài dependencies (lần đầu)
sudo apt-get install dpkg-dev
pip3 install -r requirements.txt

# Build
python3 build_raspberry.py
```

Kết quả: `dist/artnetcontroller_2.0.0_armhf.deb`

## Bước 3: Tạo GitHub Release đầu tiên (5 phút)

### Cách 1: Tự động với GitHub Actions (khuyến nghị)

```bash
# Commit tất cả thay đổi
git add .
git commit -m "Cập nhật thông tin GitHub"

# Tạo tag và push
git tag -a v2.0.0 -m "Release v2.0.0 - Production features"
git push origin main
git push origin v2.0.0

# GitHub Actions sẽ tự động:
# - Build Windows và Linux
# - Chạy tests
# - Tạo Release
# - Upload files
```

Sau 5-10 phút, check tại: `https://github.com/USERNAME/ArtNetController/releases`

### Cách 2: Upload thủ công

1. Build trên máy local (bước 2)
2. Vào GitHub → Releases → Create new release
3. Tag: `v2.0.0`
4. Upload các file từ `dist/`
5. Publish release

## Bước 4: Test các tính năng (10 phút)

### Test 1: Update System

```python
from src.system import UpdateManager

manager = UpdateManager()

# Kiểm tra update
latest = manager.check_for_updates()
if latest:
    print(f"Có bản mới: {latest.version}")
```

### Test 2: Config Manager

```python
from src.system import get_config_manager

config = get_config_manager()

# Đọc config
ip = config.get('network.artnet_ip')
print(f"IP: {ip}")

# Sửa config
config.set('network.artnet_port', 6454)

# Backup
backup_path = config.backup()
print(f"Backup tại: {backup_path}")
```

### Test 3: Crash Reporting

```python
from src.system import setup_exception_handler, get_config_manager

config = get_config_manager()
setup_exception_handler(config)

# Test crash (sẽ tự động gửi lên GitHub Issues)
raise ValueError("Test crash report")
```

### Test 4: Integration đầy đủ

```bash
# Chạy file demo
python example_integration.py
```

Kết quả mong đợi:
```
================================================================================
Initializing ArtNetController V2.0
================================================================================

[1/4] Loading configuration...
✅ Config version: 2.0.0

[2/4] Setting up logging...
✅ Logging initialized

[3/4] Setting up crash reporting...
✅ Exception handler registered

[4/4] Checking for updates...
✅ Application is up to date

================================================================================
✅ Initialization complete!
================================================================================
```

## Bước 5: Deploy cho người dùng

### Windows Users:

**Cách 1: Installer**
1. Download `ArtNetController-2.0.0-Setup.exe`
2. Double-click để cài
3. Tìm trong Start Menu

**Cách 2: Portable**
1. Download `ArtNetController-2.0.0-Portable.zip`
2. Giải nén
3. Chạy `ArtNetController.exe`

### Raspberry Pi Users:

```bash
# Download file .deb từ GitHub Releases
wget https://github.com/USERNAME/ArtNetController/releases/download/v2.0.0/artnetcontroller_2.0.0_armhf.deb

# Cài đặt
sudo dpkg -i artnetcontroller_2.0.0_armhf.deb
sudo apt-get install -f  # Fix dependencies nếu cần

# Chạy
artnetcontroller

# Hoặc dùng như service
sudo systemctl start artnetcontroller
sudo systemctl enable artnetcontroller  # Auto-start khi boot
```

## Tính năng tự động

### Auto-Update

Mỗi khi khởi động (nếu bật trong config):
1. App tự động kiểm tra bản mới trên GitHub
2. Nếu có bản mới → hiện thông báo
3. User click Download → tự động tải và cài
4. Tự động backup trước khi update
5. Nếu update lỗi → tự động rollback

### Crash Reporting

Khi có lỗi:
1. Tự động ghi log vào `logs/crashes.log`
2. Thu thập thông tin hệ thống (CPU, RAM, OS)
3. Gửi crash report lên GitHub Issues (nếu bật)
4. User có thể xem và tắt trong settings

### Config Management

- Tất cả settings lưu trong `config.json`
- Khi update phần mềm → config không mất
- Tự động migrate config từ v1.0 lên v2.0
- Có thể backup/restore config bất cứ lúc nào

## Lịch trình update

### Patch Release (2.0.0 → 2.0.1)

Bug fixes nhỏ:

```bash
# Sửa bug
# Update version trong code
# Commit
git commit -m "Fix bug XYZ"

# Tạo tag
git tag v2.0.1
git push origin v2.0.1

# GitHub Actions tự động build và release
```

### Minor Release (2.0.0 → 2.1.0)

Thêm tính năng mới:

```bash
# Thêm features
# Update version
# Update CHANGELOG.md
git commit -m "Add new feature XYZ"

git tag v2.1.0
git push origin v2.1.0
```

### Major Release (2.0.0 → 3.0.0)

Breaking changes, cần migrate:

```python
# Thêm migration code trong ConfigMigration
@staticmethod
def migrate_2_0_to_3_0(config: Dict) -> Dict:
    # Migration logic
    config["version"] = "3.0.0"
    return config
```

```bash
git tag v3.0.0
git push origin v3.0.0
```

## Monitoring

### Xem logs

**Windows:**
```powershell
# Xem log hiện tại
Get-Content logs\artnet_controller.log -Tail 50

# Theo dõi real-time
Get-Content logs\artnet_controller.log -Wait
```

**Raspberry Pi:**
```bash
# System logs
sudo journalctl -u artnetcontroller -f

# File logs
tail -f /var/log/artnetcontroller/artnet_controller.log
```

### Check crash reports

Vào GitHub Issues: `https://github.com/USERNAME/ArtNetController/issues`

Mỗi crash sẽ tự động tạo 1 issue với:
- Thông tin lỗi
- Traceback đầy đủ
- Thông tin hệ thống
- Timestamp

### Download statistics

`https://github.com/USERNAME/ArtNetController/releases`

Xem số lượng downloads cho mỗi version.

## Troubleshooting

### Update không hoạt động

```python
# Kiểm tra GitHub API
import requests
url = "https://api.github.com/repos/USERNAME/ArtNetController/releases/latest"
response = requests.get(url)
print(response.json())

# Kiểm tra rate limit
url = "https://api.github.com/rate_limit"
response = requests.get(url)
print(response.json())
```

### Crash reporting không gửi

- Kiểm tra GitHub token trong config.json
- Kiểm tra network connection
- Xem log trong `logs/crashes.log`

### Config bị mất

```python
# Restore từ backup
from src.system import get_config_manager

config = get_config_manager()
backup_path = "config_backups/config_backup_v2.0.0_20250120_103045.json"
config.restore(backup_path)
```

## Support

### Documentation

- **Full docs**: `docs/PRODUCTION_FEATURES_V2.md`
- **Build guide**: `docs/BUILD.md`
- **Summary**: `docs/V2_SUMMARY.md`

### GitHub

- **Issues**: Report bugs
- **Discussions**: Ask questions
- **Wiki**: More guides

### Code

- `example_integration.py` - Xem example code
- `src/system/` - Source code của 4 tính năng

## Checklist hoàn thành

- [ ] Cập nhật GitHub username trong code
- [ ] Tạo GitHub Personal Access Token
- [ ] Build thành công trên Windows
- [ ] Build thành công trên Raspberry Pi (optional)
- [ ] Push lên GitHub
- [ ] Tạo tag v2.0.0
- [ ] GitHub Actions build thành công
- [ ] Có GitHub Release với files
- [ ] Test update system
- [ ] Test config manager
- [ ] Test crash reporting
- [ ] Test integration

## Kết luận

Bây giờ bạn đã có:

✅ **Hệ thống update tự động** - Users luôn dùng bản mới nhất  
✅ **Config manager** - Settings không mất khi update  
✅ **Crash reporting** - Tự động report lỗi về GitHub  
✅ **Professional installer** - Dễ cài đặt cho end-users  

**Sẵn sàng cho production!** 🚀

---

**Thời gian setup**: ~30 phút  
**Difficulty**: Trung bình  
**Version**: 2.0.0
