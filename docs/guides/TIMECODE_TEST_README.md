# 🎭 Depence Timecode Test Suite

Bộ test scripts để kiểm tra nhận timecode từ Depence và các phần mềm lighting khác.

## 📁 Files trong bộ test:

### 1. `test_timecode.bat` - **CHẠY FILE NÀY**
- Menu chính để chọn test
- Dễ sử dụng nhất cho người không biết code

### 2. `test_simple_timecode.py` - **RECOMMEND**
- Test đơn giản chỉ Art-Net 4 timecode
- Dễ hiểu, ít nhiễu
- Phù hợp cho test Depence

### 3. `test_depence_timecode.py`
- Test đầy đủ tất cả protocols
- Art-Net 4, MTC, Net-timecode
- Cho test advanced

### 4. `test_artnet_monitor.py`
- Monitor tất cả traffic Art-Net
- Dùng để debug khi không nhận được timecode
- Hiển thị mọi packet Art-Net

## 🚀 Cách sử dụng:

### **Quick Start:**
```bash
# Chạy menu chính
test_timecode.bat

# Hoặc chạy trực tiếp test đơn giản
python test_simple_timecode.py
```

### **Chi tiết từng bước:**

#### **1. Setup Depence:**
- Mở Depence software
- Vào Settings → Output → Art-Net
- ✅ Bật "Art-Net Timecode" 
- Đặt IP target: `127.0.0.1` hoặc IP máy này
- Đặt Universe: 0 (hoặc bất kỳ)

#### **2. Chạy Test:**
```bash
# Chạy script test
python test_simple_timecode.py
```

#### **3. Test Depence:**
- Mở timeline trong Depence
- Nhấn Play ▶️
- Quan sát output của script
- Nếu thành công sẽ thấy: `✅ TIMECODE: 00:01:23:15`

## 📊 Kết quả mong đợi:

### **✅ Thành công:**
```
🎭 [12:34:56] ✅ TIMECODE: 00:01:23:15 @ 25fps from 192.168.1.100 (#1)
🎭 [12:34:57] ✅ TIMECODE: 00:01:24:15 @ 25fps from 192.168.1.100 (#2)
```

### **⚠️ Không nhận được timecode:**
```
⏰ [12:34:56] Still waiting for timecode... (received 0 so far)
💡 TIP: Make sure Depence Art-Net Timecode is enabled and timeline is playing
```

## 🔧 Troubleshooting:

### **Không nhận được timecode:**

1. **Kiểm tra Depence settings:**
   - Art-Net Timecode có được bật?
   - IP address có đúng?
   - Timeline có đang play?

2. **Chạy Art-Net Monitor:**
   ```bash
   python test_artnet_monitor.py
   ```
   - Xem có nhận Art-Net DMX không?
   - Nếu có DMX nhưng không có timecode → Depence chưa bật timecode
   - Nếu không có gì → Depence chưa gửi Art-Net

3. **Kiểm tra network:**
   - Firewall có block port 6454?
   - Depence và test script cùng network?

4. **Kiểm tra port conflict:**
   - Có phần mềm nào khác dùng port 6454?
   - DMX Master có đang chạy?

## 🎯 Các OpCode Art-Net:

- `0x2000` = Art-DMX (lighting data)
- `0x9700` = Art-TimeCode (timecode data) ← **CÁI NÀY QUAN TRỌNG**
- `0x2100` = Art-Nzs
- `0x2200` = Art-Sync

## 📝 Protocols hỗ trợ:

### **Art-Net 4 Timecode** (Chính)
- Port: 6454 UDP
- OpCode: 0x9700
- Depence, ETC Eos, GrandMA3

### **MTC (MIDI Time Code)**
- MIDI interface required
- Cần `python-rtmidi`: `pip install python-rtmidi`
- DAWs, some lighting consoles

### **Net-timecode**
- Port: 3040 UDP
- Various network timecode protocols

## 🎵 Frame Rates:

- `0` = 24fps
- `1` = 25fps (EU standard)
- `2` = 29.97fps (NTSC drop frame)
- `3` = 30fps (NTSC)

## 📋 Log Files:

Script sẽ tạo log file:
- `timecode_test.log` - Chi tiết debug

## 🔗 Related:

- [Art-Net 4 Specification](https://art-net.org.uk/)
- [Depence Documentation](https://depence.com/)
- DMX Master LTS Timecode Support

---

## 💡 Tips:

1. **Chạy Simple test trước** - dễ hiểu nhất
2. **Nếu không work, chạy Monitor** - xem có traffic không
3. **Check Depence manual** - mỗi version khác nhau
4. **Test với timeline đơn giản** - không cần effects phức tạp
5. **Dùng local IP** - tránh routing issues

**Good luck testing! 🎭**