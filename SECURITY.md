# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.3.x LTS | ✅ |
| 1.2.x | ⚠️ Security fixes only |
| < 1.2 | ❌ |

## Báo cáo lỗ hổng bảo mật

**KHÔNG** tạo GitHub Issue công khai cho các lỗ hổng bảo mật.

Thay vào đó, gửi email đến: **truongcongdinh97tcd@gmail.com**

### Thông tin cần cung cấp

- Mô tả lỗ hổng
- Steps to reproduce
- Mức độ ảnh hưởng
- Đề xuất sửa lỗi (nếu có)

### Quy trình xử lý

1. **Xác nhận** — Phản hồi trong vòng 48 giờ
2. **Đánh giá** — Xác định mức độ nghiêm trọng
3. **Sửa lỗi** — Phát hành bản vá
4. **Disclosure** — Công bố sau khi bản vá được phát hành

## Bảo mật hiện tại

### License System
- RSA-2048 signatures cho license validation
- Hardware binding (one license per device)
- Offline validation — không yêu cầu internet

### Configuration
- AES-256 encryption cho file cấu hình nhạy cảm
- API keys lưu trong `.env` (không commit vào git)

### Network
- Art-Net protocol trên local network
- Web server chỉ bind localhost mặc định
- Không có authentication mặc định cho web remote — cần cân nhắc khi deploy

## Best Practices

- Luôn chạy phiên bản mới nhất
- Không expose web server ra internet mà không có authentication
- Sử dụng firewall để giới hạn truy cập Art-Net port (6454)
- Backup license keys thường xuyên
