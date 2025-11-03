# Art-Net Controller

Một phần mềm điều khiển Art-Net chuyên nghiệp với GUI hiện đại, hỗ trợ Windows và Raspberry Pi.

## Tính năng chính

### 🎛️ Giao diện người dùng
- **Live Control**: Điều khiển DMX realtime với faders và buttons
- **Hardware Manager**: Quản lý thiết bị và cấu hình Art-Net
- **DMX View**: Hiển thị trạng thái DMX channels trực quan
- **Settings**: Cấu hình hệ thống và network
- **Record**: Ghi lại và chỉnh sửa DMX sequences (chỉ admin)

### 🌐 Art-Net Communication
- Gửi/nhận gói Art-Net qua UDP port 6454
- Hỗ trợ multiple universes
- Auto-discovery thiết bị Art-Net trên mạng
- Sync với các phần mềm lighting khác

### 🎵 Show Management
- Lưu trữ show trong file XML/JSON
- Quản lý playlist nhạc MP3
- Upload MP3 qua web interface
- Tự động tải và tổ chức file

### 📊 DMX Recording
- Record DMX data từ Art-Net stream
- Chỉnh sửa sequences
- Tự động cắt bỏ silence
- Export/Import show data

## Yêu cầu hệ thống

### Windows
- Windows 10/11
- Python 3.8+
- 512MB RAM khả dụng
- Card mạng Ethernet

### Raspberry Pi
- Raspberry Pi 3B+ hoặc mới hơn
- Raspbian OS hoặc Ubuntu
- Python 3.8+
- 256MB RAM khả dụng

## Cài đặt

```bash
# Clone repository
git clone <repository-url>
cd ArtNetController

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng
python main.py
```

## Cấu trúc dự án

```
ArtNetController/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── config/                 # Cấu hình
│   ├── app_config.json
│   └── network_config.json
├── src/                    # Source code chính
│   ├── gui/               # GUI components
│   ├── artnet/            # Art-Net protocol
│   ├── show/              # Show management
│   ├── webserver/         # Web upload server
│   └── utils/             # Utilities
├── data/                   # Dữ liệu ứng dụng
│   ├── shows/             # Show files
│   ├── music/             # MP3 files
│   └── recordings/        # DMX recordings
└── tests/                  # Unit tests
```

## Web Interface

Webserver chạy trên port 8080 để upload MP3:
- http://localhost:8080/upload
- Drag & drop MP3 files
- Tự động tổ chức vào show folders

## Art-Net Configuration

- Universe: 0-32767
- Port: 6454 (standard Art-Net)
- Protocol: Art-Net 4
- Refresh rate: 25-44 Hz

## Tác giả

Phát triển để điều khiển hệ thống ánh sáng chuyên nghiệp.

## License

MIT License - Xem file LICENSE để biết thêm chi tiết.