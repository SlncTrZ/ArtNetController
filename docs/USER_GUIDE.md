# Art-Net Controller - Hướng dẫn sử dụng

## Cài đặt và Khởi động

### Windows
```bash
# Clone hoặc download project
cd ArtNetController

# Chạy file cài đặt
install.bat

# Hoặc cài đặt thủ công
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Chạy ứng dụng
python main.py
# hoặc
python run.py --port 6454 --webport 8080
```

### Raspberry Pi
```bash
# Cài đặt và tối ưu cho Pi
chmod +x setup_rpi.sh
./setup_rpi.sh

# Chạy với tối ưu Pi
python3 run_pi.py
```

## Sử dụng các Tab

### 1. Live Control
- **Faders**: Điều khiển 16 channel faders (có thể điều chỉnh start channel)
- **Master**: Fader tổng điều khiển tất cả channels
- **Blackout**: Tắt tất cả outputs ngay lập tức
- **Universe**: Chọn universe để output (0-15)
- **All Full/Zero**: Set tất cả faders về full hoặc zero

### 2. Hardware Manager
- **Scan Network**: Quét mạng tìm thiết bị Art-Net
- **Device List**: Hiển thị thiết bị đã phát hiện
- **Auto Scan**: Tự động quét mỗi 30 giây
- **Select Device**: Chọn thiết bị để điều khiển
- **Ping**: Test kết nối với thiết bị

### 3. DMX View
- **Universe Selection**: Chọn universe để hiển thị
- **Channel Range**: Điều chỉnh channels hiển thị
- **Visual Display**: Hiển thị giá trị DMX bằng màu sắc
- **Statistics**: Thống kê channels hoạt động và tần suất cập nhật

### 4. Settings
- **Art-Net**: Cấu hình port, universe, refresh rate
- **Web Server**: Cài đặt webserver upload MP3
- **Shows**: Đường dẫn lưu shows, auto-save
- **Recording**: Cài đặt ghi DMX, auto-trim silence
- **Security**: Admin mode, password protection
- **System**: Theme, logging, performance

### 5. Record (Admin only)
- **Recording**: Ghi DMX data từ Art-Net stream
- **Playback**: Phát lại recordings đã lưu
- **Editing**: Cắt, trim, auto-remove silence
- **Export**: Xuất recordings ra file JSON

## Web Interface (MP3 Upload)

Truy cập: `http://localhost:8080`

### Tính năng:
- **Drag & Drop**: Kéo thả MP3 files để upload
- **Show Selection**: Chọn show để upload vào
- **File Management**: Xem, download, xóa files
- **Metadata**: Hiển thị thông tin file (title, artist, duration)

### Supported formats:
- MP3, WAV, FLAC, M4A, OGG

## Show Management

### Tạo Show mới:
1. File > New Show
2. Nhập tên show
3. Thêm music files qua web interface
4. Tạo DMX scenes trong Live Control
5. File > Save Show

### Load Show:
1. File > Open Show
2. Chọn file .json hoặc .xml
3. Show sẽ load playlist và scenes

### Show Structure:
```json
{
  "metadata": {
    "name": "Tên Show",
    "description": "Mô tả",
    "author": "Tác giả",
    "duration": 240.0,
    "universes": [0, 1]
  },
  "playlist": [
    {
      "file_path": "path/to/music.mp3",
      "title": "Tên bài",
      "artist": "Ca sĩ",
      "duration": 180.0,
      "start_time": 0.0
    }
  ],
  "scenes": [
    {
      "name": "Scene 1",
      "universe": 0,
      "channels": {"1": 255, "2": 128},
      "timestamp": 0.0,
      "fade_time": 2.0
    }
  ]
}
```

## DMX Recording

### Ghi DMX:
1. Vào tab Record (cần admin mode)
2. Chọn universe để ghi (hoặc All)
3. Click "START RECORDING"
4. DMX data sẽ được ghi realtime
5. Click "STOP" và "Save Recording"

### Chỉnh sửa Recording:
1. Load recording từ danh sách
2. Sử dụng timeline để navigate
3. Trim start/end nếu cần
4. Auto-trim silence
5. Save changes

## Art-Net Configuration

### Network Setup:
- **Port**: 6454 (standard Art-Net)
- **Universe**: 0-32767
- **Broadcast**: 255.255.255.255 (hoặc subnet specific)
- **Refresh Rate**: 25-44 Hz (recommended 30Hz)

### Compatibility:
- Art-Net 3 & 4
- Tương thích với: MA2, Avolites, Chamsys, ETC, etc.

## Troubleshooting

### Art-Net không hoạt động:
1. Kiểm tra firewall (port 6454 UDP)
2. Đảm bảo cùng subnet với thiết bị
3. Test với phần mềm khác (Art-Net Viewer)

### Web server không khởi động:
1. Kiểm tra port 8080 không bị chiếm
2. Thay đổi port trong Settings
3. Chạy với quyền admin

### Performance trên Raspberry Pi:
1. Sử dụng `setup_rpi.sh` để tối ưu
2. Giảm GUI refresh rate
3. Tắt các service không cần thiết
4. Overclock Pi (nếu cần)

### Memory issues:
1. Giảm buffer sizes trong settings
2. Giới hạn số universes
3. Tắt auto-save
4. Restart ứng dụng định kỳ

## Command Line Options

```bash
python run.py --help

Options:
  --port PORT         Art-Net port (default: 6454)
  --webport PORT      Web server port (default: 8080)
  --debug            Enable debug mode
  --no-artnet        Disable Art-Net on startup
  --no-webserver     Disable web server
```

## File Locations

```
ArtNetController/
├── config/                 # Configuration files
├── data/
│   ├── shows/             # Show files (.json/.xml)
│   ├── music/             # Default music folder
│   └── recordings/        # DMX recordings
├── logs/                  # Log files
└── src/                   # Source code
```

## Tips & Best Practices

1. **Backup Shows**: Thường xuyên backup thư mục `data/shows/`
2. **Network**: Sử dụng switch gigabit cho nhiều universes
3. **Performance**: Monitor CPU/memory usage với htop
4. **Security**: Enable admin mode khi cần bảo mật
5. **Updates**: Keep PyQt6 và dependencies updated

## Support

- **Documentation**: Xem thêm trong thư mục `docs/`
- **Issues**: Report bugs qua GitHub issues
- **Performance**: Xem `raspberry_pi_optimization.md` cho Pi tuning

---

**Lưu ý**: Đây là phần mềm mã nguồn mở, sử dụng cho mục đích học tập và thương mại theo MIT License.