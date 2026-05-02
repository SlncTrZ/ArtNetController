# TASK.md — DMX Master LTS Development Backlog

> Cập nhật: 2026-05-02  
> Version hiện tại: 1.3.0  
> Quy ước trạng thái: `[ ]` chưa làm · `[~]` đang làm · `[x]` hoàn thành

---

## 1. DOCUMENTATION

### 1.1 Module Docstring (Chuẩn hoá format)
Tất cả file thiếu `Topic:` và `Last Updated:` theo chuẩn CLAUDE.md.

| File | Trạng thái |
|---|---|
| `src/artnet/controller.py` | `[x]` |
| `src/gui/main_window.py` | `[x]` |
| `src/gui/tabs/dmx_view.py` | `[x]` |
| `src/gui/tabs/hardware_manager.py` | `[x]` |
| `src/gui/tabs/record.py` | `[x]` |
| `src/gui/tabs/settings.py` | `[x]` |
| `src/gui/tabs/show_manager.py` | `[x]` |
| `src/gui/widgets/timeline_editor.py` | `[x]` |
| `src/gui/widgets/ip_info_widget.py` | `[x]` |
| `src/serial/serial_controller.py` | `[x]` |
| `src/serial/ioboard_protocol.py` | `[x]` |
| `src/serial/port_scanner.py` | `[x]` |
| `src/show/manager.py` | `[x]` |
| `src/show/dmx_recorder.py` | `[x]` |
| `src/system/config_manager.py` | `[x]` |
| `src/system/timecode_receiver.py` | `[x]` |
| `src/system/crash_reporter.py` | `[x]` |
| `src/system/update_manager.py` | `[x]` |
| `src/utils/license.py` | `[x]` |
| `src/utils/network.py` | `[x]` |
| `src/utils/network_utils.py` | `[x]` |
| `src/webserver/server.py` | `[x]` |

### 1.2 Tài liệu kiến trúc (Còn thiếu)

- `[x]` Tạo `docs/ARCHITECTURE.md` — Data flow diagram, module architecture, threading model, file formats, security model
- `[x]` Tạo `docs/technical/LICENSE_ADMIN_WORKFLOW.md` — Quy trình admin tạo license (Device ID → RSA Sign → Deliver)
- `[x]` Cập nhật `docs/INDEX.md` — Cleaned up duplicate content, added ARCHITECTURE.md link, proper structure

### 1.3 Dọn dẹp docs đã hoàn thành

- `[x]` Review `docs/archive/` — 43 files lịch sử, đã được archive đúng chỗ, không có thông tin quan trọng bị vùi
- `[x]` Loại bỏ file backup rác: Không tìm thấy file backup nào (*.bak, *.backup, *.orig) — đã được dọn từ trước

---

## 2. CODE QUALITY

### 2.1 Module docstring bị vi phạm tiêu chuẩn format

```python
# Cần đổi TẤT CẢ module docstring sang format:
"""Module Name — One-line description.

Detailed explanation...

Topic: <artnet|gui|serial|show|system|utils|webserver>
Last Updated: YYYY-MM-DD  HH:MM
"""
```

### 2.2 Magic numbers cần đặt tên hằng số

- `[x]` `controller.py`: `6454` (ArtNet port), `4096` (recv buffer), `300.0` (node timeout) → extract thành constant
- `[x]` `dmx_recorder.py`: `522` / `524` (frame size) — đã có `FRAME_SIZE`, nhất quán

### 2.3 Lỗi tiềm ẩn cần review

- `[x]` `controller.py:_create_poll_reply()` — tạo socket mới mỗi lần gọi → dùng cached `self._current_ip` thay thế (fixed 2026-05-02)
- `[x]` `controller.py:_handle_poll_reply()` — bare `except:` → đã sửa thành `(UnicodeDecodeError, ValueError)`
- `[x]` `controller.py:_create_poll_reply()` — bare `except:` → đã sửa thành `(OSError, socket.error)`
- `[x]` `webserver/server.py` — CSRF protection cho upload/delete routes + `secrets.token_hex(32)` session key
- `[x]` `system/update_manager.py` — SSL `CERT_REQUIRED` + `check_hostname=True` cho cả check_for_updates và download_update

### 2.4 Xử lý lỗi thiếu tập trung

- `[ ]` `src/gui/tabs/` — các tab hiện có try/except inline khắp nơi, cân nhắc tập trung vào error handler của `MainWindow`

---

## 3. TESTING

### 3.1 Coverage hiện tại

| Module | Test file | Coverage |
|---|---|---|
| `src/artnet/controller.py` | `tests/test_artnet_controller.py` | `[x]` 33 tests passed |
| `src/show/dmx_recorder.py` | `tests/test_dmx_recorder.py` | `[x]` 28 tests passed |
| `src/utils/license.py` | `tests/test_license_tiers.py` | `[x]` 40 tests passed (pytest + mock) |
| `src/system/config_manager.py` | `tests/test_config_manager.py` | `[x]` 56 tests passed |
| `src/utils/network_utils.py` | `tests/test_network_utils.py` | `[x]` 24 tests passed |
| `src/serial/` | `tests/test_serial.py` | `[x]` 58 tests passed (mock serial) |

### 3.2 Test cases cần thêm

- `[x]` `test_artnet_controller.py` — Unit test: packet pack/unpack, universe validation, controller init (33 tests)
- `[x]` `test_dmx_recorder.py` — Unit test: binary format read/write, CRC16 validation, frame integrity (28 tests)
- `[x]` `test_config_manager.py` — Unit test: config migration, default values, validation, backup/restore, license encryption (56 tests)
- `[x]` `test_network_utils.py` — Unit test: IP validation, adapter detection, primary IP fallback (24 tests)
- `[x]` `test_serial.py` — 58 tests: DMXPacket pack/unpack, IOBoardProtocol, PortScanner mock, SerialController auto/manual mapping, send_dmx, statistics

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
- `[x]` Tạo `.gitignore` entry cho `.pytest_cache/` — đã thêm
- `[ ]` Xoá các `.spec` file cũ: `DMXMaster-LTS-0.0.1.spec` đến `DMXMaster-LTS-1.2.0.spec`

---

## 6. SECURITY

- `[x]` Kiểm tra `tools/rsa_keys/private_key.pem` không bị commit lên git remote — OK, .gitignore đầy đủ
- `[x]` Xác nhận `config/license.lic` trong `.gitignore` — OK
- `[x]` Review `webserver/server.py`: file upload path traversal prevention — `secure_filename()` áp dụng cho upload/delete ✅, thêm cho download route (fixed 2026-05-02)
- `[x]` `license.py`: SSRF prevention — `_validate_revocation_url()` validates scheme + hostname, `ssl.create_default_context()` cho HTTPS

---

_File này do Claude Code tạo ngày 2026-04-16 sau khi audit codebase v1.3.0._
