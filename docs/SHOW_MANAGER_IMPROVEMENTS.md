#  Show Manager - Improvements Summary

##  Đã hoàn thành

### 1. **Thêm nút "Reload Shows"** 
- **Vị trí:** Shows Library panel
- **Chức năng:** Tải lại danh sách shows từ thư mục data/shows/
- **Sử dụng:** Click nút "Reload Shows" để cập nhật danh sách sau khi thêm/sửa show files

### 2. **Kiểm tra Timezone**
- **Cấu hình hiện tại:** Asia/Ho_Chi_Minh (UTC+7)
- **Trạng thái:**  Đã cài đặt và hoạt động đúng
- **Debug log:**
  - Timezone initialized: Asia/Ho_Chi_Minh, index: 1
  - TZ index: 1, TZ: Asia/Ho_Chi_Minh

---

##  Chi tiết thay đổi

### File: src/gui/tabs/show_manager.py

#### 1. Thêm nút Reload Shows (line 123-126)
``python
# Reload shows button
self.btn_reload = QPushButton("Reload Shows")
self.btn_reload.clicked.connect(self._load_shows)
btns.addWidget(self.btn_reload)
``

#### 2. Debug logging cho timezone (line 91)
``python
print(f"[DEBUG] Timezone initialized: {saved_tz}, index: {self._tz_index}")
``

#### 3. Debug logging cho clock update (line 432)
``python
print(f"[DEBUG Clock] TZ index: {self._tz_index}, TZ: {self._timezones[self._tz_index] if self._tz_index < len(self._timezones) else 'INVALID'}")
``

---

##  Test Results

### Timezone Configuration Test
``bash
$ python -c "from src.utils.config import ConfigManager; cm = ConfigManager(); print('Timezone:', cm.get_app_config('ui.timezone', 'UTC'))"
Timezone: Asia/Ho_Chi_Minh  
``

### Timezone Conversion Test
``bash
$ python -c "from zoneinfo import ZoneInfo; from datetime import datetime, timezone; ..."
UTC time: 2025-11-04 06:07:54+00:00
VN time:  2025-11-04 13:07:54+07:00   (Đúng UTC+7)
``

### App Runtime Test
``
[DEBUG] Timezone initialized: Asia/Ho_Chi_Minh, index: 1  
[DEBUG Clock] TZ index: 1, TZ: Asia/Ho_Chi_Minh  
``

---

##  Cách sử dụng

### Reload Shows
1. Thêm/sửa file show trong data/shows/
2. Mở tab "Show Manager"
3. Click nút **"Reload Shows"**
4. Danh sách shows sẽ được cập nhật ngay lập tức

### Kiểm tra Timezone
1. Giờ hiển thị ở góc trên bên phải
2. Menu  Timezone  chọn timezone
3. Hoặc kiểm tra file: config/app_config.json
   ``json
   "ui": {
     "timezone": "Asia/Ho_Chi_Minh"
   }
   ``

---

##  Nếu vẫn thấy giờ UTC

### Giải pháp:
1. **Restart app** (đóng hoàn toàn và mở lại)
2. Kiểm tra menu Timezone  chọn lại Asia/Ho_Chi_Minh
3. Debug output sẽ hiện trong console khi app khởi động

### Xác nhận timezone đúng:
- Debug log: [DEBUG] Timezone initialized: Asia/Ho_Chi_Minh, index: 1
- Giờ hiển thị = UTC + 7 giờ
- VD: UTC 06:00  Vietnam 13:00

---

##  Notes

- Debug logs có thể được remove sau khi xác nhận timezone hoạt động
- Nút "Reload Shows" không reload playlist (chỉ reload thư viện)
- Timezone được lưu vào config tự động khi thay đổi

---

**Last Updated:** 2025-11-04 13:10
