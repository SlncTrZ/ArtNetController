# 🧪 QUICK TEST GUIDE - v1.1.0

## Hướng Dẫn Test Nhanh Các Tính Năng Mới

---

## 1️⃣ Test Auto-Stop Recording (Tính năng chính!)

### Bước test:
1. Mở Depence → Settings → Timecode → Enable "Send Net-timecode"
2. Mở DMX Master → Record tab
3. Click RECORD
4. Chạy show trong Depence
5. **Dừng show trong Depence**
6. **Chờ 3 giây** → Recording tự động dừng ✅
7. Kiểm tra:
   - ✅ Recording đã dừng
   - ✅ 3 giây cuối đã bị trim
   - ✅ File đã lưu với tên timestamp

### Kết quả mong đợi:
```
[INFO] Timecode stopped changing. Auto-stopping in 3 seconds...
[INFO] Auto-stop triggered. Stopping recording...
[INFO] Auto-trimming last 3.0 seconds...
[INFO] Recording saved: Recording_20251106_143052.dmxrec
```

---

## 2️⃣ Test Unified Create Show Dialog

### Test A: Create Show từ Recording hiện tại

1. Record một show (hoặc dùng auto-stop)
2. Click nút **"Create Show"**
3. Dialog mở ra với:
   - Show name: "Light Show 20251106_143052"
   - Description: (rỗng)
   - Audio file: (rỗng)
   - Duration: "Recording: 45.2s"
4. **Thử thêm audio:**
   - Click "Browse Audio File..."
   - Chọn file MP3
   - Kiểm tra tên file hiển thị
5. Click "Create Show"
6. Kiểm tra message:
   ```
   ✅ Show created successfully!
   
   📂 Duration: 45.2s
   🎵 Audio: Assigned
   
   💡 The show is now available in Show Manager library.
   ```

### Test B: Move to Shows (từ Recordings list)

1. Vào Recordings tab
2. Chọn một recording
3. Click **"Move to Shows"**
4. Dialog mở ra (giống như Create Show)
   - Show name: (tên recording)
   - Duration hiển thị
5. Thay đổi tên, thêm description, chọn audio
6. Click "Create Show"
7. Kiểm tra:
   - ✅ Recording biến mất khỏi Recordings
   - ✅ Show xuất hiện trong Show Manager
   - ✅ File .dmxrec đã move

---

## 3️⃣ Test Delete Show (Improved)

### Bước test:
1. Mở Show Manager
2. Chọn bất kỳ show nào
3. Click **"Delete Show"**
4. Confirm deletion
5. Kiểm tra:
   - ✅ Show biến mất khỏi list
   - ✅ Không có lỗi "Show file not found"
   - ✅ Library tự động reload

### Kiểm tra kỹ (trong Explorer):
1. Mở thư mục: `C:\Users\[User]\AppData\Local\DMX Master LTS\data\shows\`
2. Xác nhận:
   - ✅ File .json đã xóa
   - ✅ File .dmxrec đã xóa
   - ✅ Không còn file rác

---

## 4️⃣ Test Reduced Logging

### Bước test:
1. Mở app
2. Chạy một show trong Depence
3. Quan sát console/log

### Kết quả mong đợi:
- ✅ **KHÔNG** thấy: `[DEBUG] ArtNet packet: ...`
- ✅ **KHÔNG** thấy: `[DEBUG] DMX data: [0, 0, 0, ...]`
- ✅ **CHỈ** thấy: Messages quan trọng
  ```
  [INFO] Timecode received: 00:00:05:12
  [INFO] Recording started
  [INFO] Auto-stop triggered
  [INFO] Show created: My Show
  ```

---

## 5️⃣ Test Recording Defaults

### Bước test:
1. Mở Record tab
2. Kiểm tra mặc định:
   - ✅ Auto Trim: **UNCHECKED** (OFF)
   - ✅ Silence Threshold: **0**

---

## 🎯 Quick Checklist

Sử dụng checklist này để test nhanh:

### Auto-Stop ⏱️
- [ ] Recording tự động dừng sau 3s khi timecode ngừng
- [ ] 3 giây cuối được trim
- [ ] File lưu với tên timestamp
- [ ] Log hiển thị đúng

### Create Show Dialog 📝
- [ ] Dialog mở đúng từ "Create Show"
- [ ] Dialog mở đúng từ "Move to Shows"
- [ ] Audio file browser hoạt động
- [ ] Show name, description lưu đúng
- [ ] Duration hiển thị chính xác
- [ ] Success message đầy đủ thông tin

### Delete Show 🗑️
- [ ] Xóa show không báo lỗi
- [ ] Xóa cả .json và .dmxrec
- [ ] Library tự động reload
- [ ] Không còn file rác

### Logging 📊
- [ ] Console sạch, không rối
- [ ] Không có verbose ArtNet logs
- [ ] Chỉ hiển thị messages quan trọng

### Defaults ⚙️
- [ ] Auto Trim mặc định OFF
- [ ] Silence Threshold mặc định 0

---

## 🐛 Nếu Gặp Lỗi

### Auto-Stop không hoạt động:
- Kiểm tra: Depence có đang gửi timecode không?
- Kiểm tra: Log có hiển thị "Timecode stopped changing"?
- Kiểm tra: Giá trị timecode có thay đổi không?

### Create Show dialog không mở:
- Kiểm tra: Console có lỗi import?
- Kiểm tra: File `src/gui/dialogs/create_show_dialog.py` có tồn tại?

### Delete show báo lỗi:
- Kiểm tra: File .json và .dmxrec có tồn tại?
- Kiểm tra: Log hiển thị lỗi gì?

### Logging vẫn verbose:
- Kiểm tra: Version có đúng 1.1.0?
- Restart app

---

## ✅ Test Pass Criteria

Tất cả tính năng được coi là **PASS** khi:

1. ✅ Auto-stop hoạt động ổn định (không miss timeout)
2. ✅ Create Show dialog xuất hiện và hoạt động tốt
3. ✅ Move to Shows sử dụng cùng dialog
4. ✅ Delete xóa sạch cả 2 files
5. ✅ Logging sạch sẽ, dễ đọc
6. ✅ Defaults đúng như yêu cầu
7. ✅ Không có crash hoặc error nào

---

## 📞 Báo Kết Quả

Sau khi test xong, báo lại:
- ✅ Tính năng nào OK
- ❌ Tính năng nào có vấn đề
- 📝 Chi tiết lỗi (nếu có)

Nếu tất cả OK → Ready to build! 🚀

---

*Test guide for DMX Master LTS v1.1.0*
*November 6, 2025*
