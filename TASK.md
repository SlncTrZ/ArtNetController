# TASK.md — DMX Master LTS Development Backlog

> Cập nhật: 2026-04-16  
> Version hiện tại: 1.3.0  
> Quy ước trạng thái: `[ ]` chưa làm · `[~]` đang làm · `[x]` hoàn thành

---

## 1. DOCUMENTATION

### 1.1 Module Docstring (Chuẩn hoá format)
Tất cả file thiếu `Topic:` và `Last Updated:` theo chuẩn CLAUDE.md.

| File | Trạng thái |
|---|---|
| `src/artnet/controller.py` | `[ ]` |
| `src/gui/main_window.py` | `[ ]` |
| `src/gui/tabs/dmx_view.py` | `[ ]` |
| `src/gui/tabs/hardware_manager.py` | `[ ]` |
| `src/gui/tabs/record.py` | `[ ]` |
| `src/gui/tabs/settings.py` | `[ ]` |
| `src/gui/tabs/show_manager.py` | `[ ]` |
| `src/gui/widgets/timeline_editor.py` | `[ ]` |
| `src/gui/widgets/ip_info_widget.py` | `[ ]` |
| `src/serial/serial_controller.py` | `[ ]` |
| `src/serial/ioboard_protocol.py` | `[ ]` |
| `src/serial/port_scanner.py` | `[ ]` |
| `src/show/manager.py` | `[ ]` |
| `src/show/dmx_recorder.py` | `[ ]` |
| `src/system/config_manager.py` | `[ ]` |
| `src/system/timecode_receiver.py` | `[ ]` |
| `src/system/crash_reporter.py` | `[ ]` |
| `src/system/update_manager.py` | `[ ]` |
| `src/utils/license.py` | `[ ]` |
| `src/utils/network.py` | `[ ]` |
| `src/utils/network_utils.py` | `[ ]` |
| `src/webserver/server.py` | `[ ]` |

### 1.2 Tài liệu kiến trúc (Còn thiếu)

- `[ ]` Tạo `docs/ARCHITECTURE.md` — Data flow diagram: *Depence/GrandMA → ArtNet UDP → Controller → DMX Recorder → Playback → Serial (IOBoard)*
- `[ ]` Tạo `docs/technical/LICENSE_ADMIN_WORKFLOW.md` — Quy trình admin tạo license (Device ID → RSA Sign → Deliver)
- `[ ]` Cập nhật `docs/INDEX.md` — Phản ánh cấu trúc docs mới (guides/, releases/, technical/, archive/)

### 1.3 Dọn dẹp docs đã hoàn thành

- `[ ]` Review `docs/archive/` — Xác nhận không còn thông tin kỹ thuật quan trọng bị vùi trong file "COMPLETE"
- `[ ]` Loại bỏ file backup rác: `src/gui/main_window_backup.py`, `src/gui/main_window.py.backup`, `src/gui/dialogs/license_dialog.py.backup`, `src/gui/tabs/record_backup.py`, `src/show/dmx_recorder_v1.py`

---

## 2. CODE QUALITY

### 2.1 Module docstring bị vi phạm tiêu chuẩn format

```python
# Cần đổi TẤT CẢ module docstring sang format:
"""Module Name — One-line description.

Detailed explanation...

Topic: <artnet|gui|serial|show|system|utils|webserver>
Last Updated: YYYY-MM-DD
"""
```

### 2.2 Magic numbers cần đặt tên hằng số

- `[ ]` `controller.py`: `6454` (ArtNet port), `4096` (recv buffer), `300.0` (node timeout) → extract thành constant
- `[ ]` `dmx_recorder.py`: `522` / `524` (frame size) — đã có `FRAME_SIZE` nhưng cần kiểm tra nhất quán

### 2.3 Lỗi tiềm ẩn cần review

- `[ ]` `controller.py:_create_poll_reply()` — tạo socket mới mỗi lần gọi (dòng 946-950) → dùng `self.bind_ip` thay thế
- `[ ]` `controller.py:_handle_poll_reply()` — bare `except:` tại dòng 744, 755 → thu hẹp exception type
- `[ ]` `webserver/server.py` — kiểm tra CSRF protection cho các route upload
- `[ ]` `system/update_manager.py` — kiểm tra certificate validation khi fetch update URL

### 2.4 Xử lý lỗi thiếu tập trung

- `[ ]` `src/gui/tabs/` — các tab hiện có try/except inline khắp nơi, cân nhắc tập trung vào error handler của `MainWindow`

---

## 3. TESTING

### 3.1 Coverage hiện tại

| Module | Test file | Coverage |
|---|---|---|
| `src/artnet/controller.py` | Không có | `[ ]` Cần viết |
| `src/show/dmx_recorder.py` | Không có | `[ ]` Cần viết |
| `src/utils/license.py` | `tests/test_license_tiers.py` | `[~]` Có nhưng cần expand |
| `src/system/config_manager.py` | `tests/test_basic.py` | `[~]` Cơ bản |
| `src/serial/` | Không có | `[ ]` Cần viết (mock serial port) |

### 3.2 Test cases cần thêm

- `[ ]` `test_artnet_controller.py` — Unit test: packet pack/unpack, universe validation, license limit enforcement
- `[ ]` `test_dmx_recorder.py` — Unit test: binary format read/write, CRC16 validation, frame integrity
- `[ ]` `test_config_manager.py` — Unit test: config migration, default values, validation
- `[ ]` `test_network_utils.py` — Unit test: IP detection, broadcast address calculation
- `[ ]` `test_serial_controller.py` — Integration test với mock serial (không cần hardware)

---

## 4. FEATURES (Backlog)

### 4.1 Đề xuất v1.4.0

- `[ ]` **Multi-adapter binding**: Bind đồng thời nhiều network interface (thay vì chỉ 1 + loopback)
- `[ ]` **Show export**: Xuất show sang file `.zip` bao gồm DMX rec + audio + metadata
- `[ ]` **Web UI dashboard**: Hiển thị live DMX levels qua WebSocket trên `webserver/server.py`

### 4.2 Cải tiến hiệu năng

- `[ ]` `dmx_recorder.py` — Benchmark I/O queue với `asyncio` thay `threading.Queue` cho high-FPS recording
- `[ ]` `controller.py:_handle_dmx_packet()` — Profile CPU usage khi nhận 512 universes đồng thời

---

## 5. BUILD & RELEASE

- `[ ]` Cập nhật `build.bat` / `build.sh` để dùng spec file mới nhất (`DMXMaster-LTS-1.3.0.spec`)
- `[ ]` Thêm bước tự động chạy `pytest` trong CI trước khi build (`.github/workflows/build.yml`)
- `[ ]` Tạo `.gitignore` entry cho `build_test/`, `dist_test/`, `__pycache__/`, `*.spec` cũ
- `[ ]` Xoá các `.spec` file cũ: `DMXMaster-LTS-0.0.1.spec` đến `DMXMaster-LTS-1.2.0.spec`

---

## 6. SECURITY

- `[ ]` Kiểm tra `tools/rsa_keys/private_key.pem` không bị commit lên git remote (nguy cơ cao)
- `[ ]` Xác nhận `config/license.lic` trong `.gitignore`
- `[ ]` Review `webserver/server.py`: file upload path traversal prevention (kiểm tra `secure_filename`)
- `[ ]` `license.py`: revocation check URL hardcode hay đọc từ config? — tránh SSRF nếu config bị tamper

---

_File này do Claude Code tạo ngày 2026-04-16 sau khi audit codebase v1.3.0._
