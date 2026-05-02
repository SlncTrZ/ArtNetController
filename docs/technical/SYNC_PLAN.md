# 📋 Kế hoạch Đồng bộ: ArtNetController ↔ AI_DMX_Autopilot

> **Mục tiêu**: Thiết lập đồng bộ hoàn chỉnh giữa 2 dự án DMX
> **Ngày tạo**: 2026-05-01 23:06
> **Last Updated**: 2026-05-02 07:33
> **Trạng thái**: `[~]` Phase 1 đang triển khai — Phase 1.1→1.6 HOÀN THÀNH
> **Thời gian dự kiến**: 4-6 tuần

---

## 1. Tổng quan

### 1.1 Mối quan hệ 2 dự án

```
┌─────────────────────┐                    ┌─────────────────────┐
│  ArtNetController   │                    │  AI_DMX_Autopilot   │
│  (DMX Controller)   │                    │  (AI Show Creator)  │
│                     │                    │                     │
│  - Record DMX show  │ ── .dmxrec ────►  │  - Learn phong cách │
│  - Playback show    │                    │  - Generate show mới│
│  - License system   │ ◄── CSV/ArtNet ──  │  - Export CSV       │
│  - Art-Net UDP      │                    │  - ChromaDB RAG     │
└─────────────────────┘                    └─────────────────────┘
```

### 1.2 Vấn đề hiện tại

| # | Vấn đề | Mức độ |
|---|---|---|
| 1 | Export/import thủ công giữa 2 dự án | 🔴 Cao |
| 2 | Format không tương thích (.dmxrec vs CSV) | 🔴 Cao |
| 3 | Fixture database không đồng bộ schema | 🟠 Trung bình |
| 4 | Không có API để gọi giữa 2 hệ thống | 🟠 Trung bình |
| 5 | Không có real-time sync | 🟡 Thấp |

---

## 2. Giải pháp

### 2.1 Kiến trúc tổng thể

```
┌──────────────────────────────────────────────────────────┐
│                    SHARED LAYER                          │
│                                                          │
│  DMX_Shared_Lib/          (pip installable package)     │
│  ├── dmx_data/            (binary reader, CSV convert)  │
│  ├── dmx_protocol/        (packet builder, mapping)     │
│  └── common/              (constants, validation)       │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                    API LAYER                             │
│                                                          │
│  ArtNetController API    (Flask/FastAPI server)          │
│  ├── GET  /api/shows                (list shows)        │
│  ├── GET  /api/shows/{name}         (show metadata)     │
│  ├── POST /api/shows/export-csv     (convert to CSV)    │
│  ├── POST /api/shows/import         (import from AI)    │
│  └── WS   /api/live/dmx            (live stream)       │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                    CLIENT LAYER                          │
│                                                          │
│  AI_DMX_Autopilot Client (HTTP client wrapper)           │
│  ├── ArtNetClient.list_shows()                           │
│  ├── ArtNetClient.export_show_csv()                      │
│  ├── ArtNetClient.import_generated_show()                │
│  └── ArtNetClient.stream_live_dmx()                      │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Workflow mục tiêu

```
1. ArtNetController Record Show
   ↓
2. Auto-export → Shared Storage (.dmxrec)
   ↓
3. AI_DMX_Autopilot Learn (đọc .dmxrec trực tiếp qua shared lib)
   ↓
4. AI Generate new show → Export CSV
   ↓
5. Auto-import → ArtNetController (convert CSV → .dmxrec)
   ↓
6. Playback generated show
```

---

## 3. Lộ trình triển khai

### Phase 1: Shared Module Library (Tuần 1-2)

**Mục tiêu**: Tạo `DMX_Shared_Lib` package chứa code dùng chung

#### 3.1.1 Tạo project structure

- [ ] Tạo thư mục `H:\Develop\DMX_Shared_Lib\`
- [ ] Khởi tạo git repo
- [ ] Tạo `setup.py` (installable package)
- [ ] Tạo `requirements.txt`
- [ ] Tạo `README.md`

#### 3.1.2 Module `dmx_data/` — Xử lý data format

- [ ] `binary_reader.py` — Đọc .dmxrec v2.0 (extract từ ArtNetController)
- [ ] `binary_writer.py` — Viết .dmxrec v2.0
- [ ] `csv_converter.py` — Convert .dmxrec ↔ CSV (cho AI_DMX_Autopilot)
- [ ] `fixture_db.py` — Fixture database schema chuẩn (dùng cho cả 2 dự án)

#### 3.1.3 Module `dmx_protocol/` — Protocol utilities

- [ ] `constants.py` — Art-Net constants (port 6454, header, opcodes)
- [ ] `packet_builder.py` — Art-Net packet pack/unpack utilities
- [ ] `universe_mapper.py` — Universe mapping logic (Net/Sub/Uni)

#### 3.1.4 Module `common/` — Shared utilities

- [ ] `validation.py` — Validate DMX data (512 channels, 0-255 values)
- [ ] `crc.py` — CRC-16/MODBUS (extract từ dmx_recorder.py)

#### 3.1.5 Testing

- [ ] Viết unit tests cho shared lib
- [ ] Test binary reader/writer round-trip
- [ ] Test CSV converter (cả 2 chiều)
- [ ] Test fixture DB schema

#### 3.1.6 Integrate vào ArtNetController

- [ ] Update `requirements.txt` thêm `dmx-shared-lib`
- [ ] Refactor `src/show/dmx_recorder.py` dùng shared lib
- [ ] Thêm method `export_to_csv()` vào recorder
- [ ] Thêm method `import_from_csv()` vào player
- [ ] Test backward compatibility (đọc file .dmxrec cũ)

#### 3.1.7 Integrate vào AI_DMX_Autopilot

- [ ] Update `requirements.txt` thêm `dmx-shared-lib`
- [ ] Refactor `learn-legacy` mode dùng shared binary reader
- [ ] Update fixture database import dùng shared schema
- [ ] Thêm export format `.dmxrec` (cho playback trực tiếp)
- [ ] Test import/show resources workflow

---

### Phase 2: API Server (Tuần 3-4)

**Mục tiêu**: Tạo REST API trong ArtNetController để AI tự động trao đổi data

#### 3.2.1 API Server setup

- [ ] Tạo `src/api/` package trong ArtNetController
- [ ] Chọn framework: Flask (đã có dependency) hoặc FastAPI
- [ ] Tạo `src/api/server.py` — Main API server
- [ ] Tạo `src/api/routes/shows.py` — Show management routes
- [ ] Tạo `src/api/routes/export.py` — Export/Import routes
- [ ] Tạo `src/api/routes/health.py` — Health check

#### 3.2.2 API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/shows` | List tất cả shows |
| GET | `/api/shows/{name}` | Get show metadata |
| GET | `/api/shows/{name}/download` | Download .dmxrec file |
| POST | `/api/shows/{name}/export-csv` | Convert show → CSV |
| POST | `/api/shows/import` | Import CSV → tạo show mới |
| DELETE | `/api/shows/{name}` | Xóa show |
| GET | `/api/fixtures` | List fixture database |
| POST | `/api/fixtures/sync` | Sync fixture database |

#### 3.2.3 API Authentication

- [ ] Thêm API key authentication (đơn giản, cho local network)
- [ ] API key lưu trong config, không hardcode
- [ ] Rate limiting (ngăn abuse)

#### 3.2.4 API Testing

- [ ] Viết API tests (pytest + requests)
- [ ] Test tất cả endpoints
- [ ] Test error handling (file not found, invalid format)
- [ ] Test authentication

---

### Phase 3: Client Wrapper (Tuần 4-5)

**Mục tiêu**: AI_DMX_Autopilot có thể gọi API ArtNetController

#### 3.3.1 Client library

- [ ] Tạo `src/integration/artnet_client.py` trong AI_DMX_Autopilot
- [ ] Implement `ArtNetClient` class
- [ ] Methods: `list_shows()`, `export_show_csv()`, `import_show()`, `get_fixtures()`
- [ ] Error handling + retry logic
- [ ] Config: API URL, API key

#### 3.3.2 Workflow automation

- [ ] Tạo CLI command `sync-import` — Import shows từ ArtNetController
- [ ] Tạo CLI command `sync-export` — Export generated show sang ArtNetController
- [ ] Thêm vào Streamlit UI: nút "Sync with ArtNetController"
- [ ] Auto-detect ArtNetController running (port scan)

#### 3.3.3 Testing

- [ ] Test client với mock server
- [ ] Test full workflow (import → learn → generate → export)
- [ ] Test error scenarios (server down, network issue)

---

### Phase 4: Real-time & Advanced (Tuần 5-6)

**Mục tiêu**: Live DMX streaming và advanced features

#### 3.4.1 WebSocket live streaming

- [ ] Thêm WebSocket endpoint `/api/live/dmx` trong ArtNetController
- [ ] Stream real-time DMX data (100 FPS)
- [ ] Client subscribe/unsubscribe theo universe

#### 3.4.2 Auto-sync file watcher

- [ ] File watcher cho `data/show_resources/` (ArtNetController)
- [ ] Auto-export khi có show mới recorded
- [ ] AI_DMX_Autopilot auto-detect new files

#### 3.4.3 Show bundle format

- [ ] Định nghĩa `.dmxshow` format (ZIP bao gồm .dmxrec + audio + metadata)
- [ ] Export/Import bundle từ cả 2 dự án
- [ ] ArtNetController: Export sau khi record
- [ ] AI_DMX_Autopilot: Import để learn, Export sau khi generate

---

## 4. File Structure Chi Tiết

### 4.1 DMX_Shared_Lib

```
H:\Develop\DMX_Shared_Lib\
├── README.md
├── setup.py
├── requirements.txt
├── .gitignore
├── tests/
│   ├── test_binary_reader.py
│   ├── test_csv_converter.py
│   ├── test_fixture_db.py
│   └── test_validation.py
├── dmx_data/
│   ├── __init__.py
│   ├── binary_reader.py      # Class DMXRecReader
│   ├── binary_writer.py      # Class DMXRecWriter
│   ├── csv_converter.py      # dmxrec_to_csv(), csv_to_dmxrec()
│   └── fixture_db.py         # Class Fixture, FixtureDatabase
├── dmx_protocol/
│   ├── __init__.py
│   ├── constants.py           # ARTNET_PORT, ARTNET_HEADER, OPCODES
│   ├── packet_builder.py      # build_dmx_packet(), parse_dmx_packet()
│   └── universe_mapper.py     # uni_to_net_sub(), net_sub_to_uni()
└── common/
    ├── __init__.py
    ├── crc.py                 # crc16_modbus()
    └── validation.py          # validate_dmx_data(), validate_universe()
```

### 4.2 ArtNetController additions

```
H:\Develop\ArtNetController\
├── src/
│   ├── api/                           ← NEW
│   │   ├── __init__.py
│   │   ├── server.py                  ← Flask/FastAPI server
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── shows.py               ← Show CRUD endpoints
│   │       ├── export.py              ← Export/Import endpoints
│   │       └── health.py              ← Health check
│   └── show/
│       ├── dmx_recorder.py            ← Update: dùng shared lib
│       └── manager.py                 ← Update: thêm export/import
└── requirements.txt                   ← Update: thêm dmx-shared-lib
```

### 4.3 AI_DMX_Autopilot additions

```
H:\Develop\AI_DMX_Autopilot\
├── src/
│   ├── integration/                   ← NEW
│   │   ├── __init__.py
│   │   └── artnet_client.py           ← ArtNetClient wrapper
│   └── ingestion/
│       └── legacy_importer.py         ← Update: dùng shared binary reader
├── config/
│   └── default.yaml                   ← Update: thêm ArtNet API config
└── requirements.txt                   ← Update: thêm dmx-shared-lib
```

---

## 5. Data Flow Chi Tiết

### 5.1 Binary Format (.dmxrec) — Shared

```
HEADER (32 bytes):
  Magic:     'DMXR'     (4 bytes)
  Version:   uint8       (1 byte)  = 2
  FPS:       uint16      (2 bytes)
  UniCount:  uint16      (2 bytes)
  FrameCount: uint32     (4 bytes)
  Flags:     uint8       (1 byte)  = CRC + Monotonic
  Reserved:              (18 bytes)

FRAME (524 bytes each):
  Timestamp: float64     (8 bytes)  — seconds from start
  Universe:  uint16      (2 bytes)
  DMX Data:  512 bytes
  CRC16:     uint16      (2 bytes)
```

### 5.2 CSV Format (cho AI) — Shared

```csv
frame,timestamp,universe,channel_0,channel_1,...,channel_511
0,0.000,0,128,200,0,...,0
0,0.000,1,50,50,50,...,50
1,0.025,0,130,205,0,...,0
```

### 5.3 Fixture Database Schema — Shared

```csv
fixture_id,name,type,manufacturer,universe,address,channels,color_mode,x,y,z
F001,MH1,MovingHead,Robe,0,1,16,RGB,0.1,0.5,3.0
F002,PAR1,PAR,ETC,0,17,4,RGB,0.3,0.5,3.0
```

### 5.4 Show Bundle (.dmxshow) — ZIP

```
show_name.dmxshow (ZIP):
  ├── show_record.dmxrec      # DMX recording
  ├── audio.mp3                # Audio file
  ├── fixture_database.csv     # Fixture mapping
  └── metadata.json            # Show info (name, duration, FPS, universes)
```

---

## 6. API Specification

### 6.1 Authentication

```http
Headers:
  X-API-Key: <api_key_from_config>
```

### 6.2 Endpoints

#### Health Check
```http
GET /api/health
Response: { "status": "ok", "version": "1.3.0" }
```

#### List Shows
```http
GET /api/shows
Response: {
  "shows": [
    { "name": "Show_001", "frames": 24000, "duration": 600.0,
      "fps": 40.0, "universes": [0, 1], "file_size": 12582912 }
  ]
}
```

#### Export Show to CSV
```http
POST /api/shows/{name}/export-csv
Response: CSV file (attachment)
```

#### Import Show from AI
```http
POST /api/shows/import
Body: multipart/form-data
  - csv_file: <CSV file>
  - name: "AI_Generated_Show_001"
  - fps: 40
  - metadata: {"source": "ai_dmx_autopilot", "audio": "song.mp3"}
Response: { "status": "ok", "show_name": "AI_Generated_Show_001",
            "frames": 24000, "file_size": 12582912 }
```

#### Get Fixtures
```http
GET /api/fixtures
Response: {
  "fixtures": [
    { "id": "F001", "name": "MH1", "type": "MovingHead",
      "universe": 0, "address": 1, "channels": 16 }
  ]
}
```

#### Live DMX Stream (WebSocket)
```
WS /api/live/dmx
Subscribe: {"action": "subscribe", "universes": [0, 1]}
Receive: {"universe": 0, "data": [128, 200, 0, ...], "timestamp": 1234.567}
```

---

## 7. Checklist Tổng hợp

### Phase 1: Shared Module
- [x] 3.1.1 Tạo DMX_Shared_Lib project structure ✅ 2026-05-02
- [x] 3.1.2 Module dmx_data/ (reader, writer, converter, fixture) ✅ 2026-05-02
- [x] 3.1.3 Module dmx_protocol/ (constants, packets) ✅ 2026-05-02
- [x] 3.1.4 Module common/ (validation, CRC) ✅ 2026-05-02
- [x] 3.1.5 Unit tests cho shared lib — 34/34 pass ✅ 2026-05-02
- [x] 3.1.6 Integrate vào ArtNetController — 28/28 tests pass ✅ 2026-05-02
- [ ] 3.1.7 Integrate vào AI_DMX_Autopilot

### Phase 2: API Server
- [ ] 3.2.1 API Server setup (Flask/FastAPI)
- [ ] 3.2.2 API Endpoints (CRUD shows, export/import)
- [ ] 3.2.3 API Authentication
- [ ] 3.2.4 API Testing

### Phase 3: Client Wrapper
- [ ] 3.3.1 ArtNetClient library trong AI_DMX_Autopilot
- [ ] 3.3.2 Workflow automation (CLI + UI)
- [ ] 3.3.3 Integration testing

### Phase 4: Advanced
- [ ] 3.4.1 WebSocket live streaming
- [ ] 3.4.2 Auto-sync file watcher
- [ ] 3.4.3 Show bundle format (.dmxshow)

---

## 8. Dependencies

### DMX_Shared_Lib
```
numpy>=1.24.0
pandas>=2.0.0
```

### ArtNetController (thêm)
```
dmx-shared-lib>=1.0.0
flask>=3.0.0          # cho API server
flask-cors>=4.0.0     # CORS support
```

### AI_DMX_Autopilot (thêm)
```
dmx-shared-lib>=1.0.0
requests>=2.31.0      # cho API client
websockets>=12.0       # cho live streaming
```

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Shared lib breaking changes | Cao | Semantic versioning, pin version |
| API security (local network) | Trung bình | API key + rate limiting |
| Binary format compatibility | Cao | Version field trong header, migration |
| Performance overhead | Thấp | Async I/O, buffer management |
| .dmxrec version mismatch | Trung bình | Reader hỗ trợ multiple versions |

---

## 10. Rà soát Code Thực tế (2026-05-01 23:10)

### 10.1 Phát hiện quan trọng

| # | Phát hiện | File | Mức độ |
|---|---|---|---|
| 1 | **dmx_recorder.py docstring sai** — ghi "Version: Currently version 1" nhưng code = `FORMAT_VERSION = 2`, FRAME_SIZE = 524 (có CRC) | `ArtNetController/src/show/dmx_recorder.py:9-24` | 🔴 Phải sửa |
| 2 | **AI_DMX_Autopilot ĐÃ CÓ .dmxrec reader** — `legacy_show_importer.py:700-735` đã đọc V2.0 binary | `AI_DMX_Autopilot/src/ingestion/legacy_show_importer.py` | ✅ Không cần viết lại |
| 3 | **Flask server ĐÃ CÓ sẵn** — `src/webserver/server.py` dùng Flask, port 8080, đã có `/api/shows` | `ArtNetController/src/webserver/server.py` | ⚠️ Mở rộng, không tạo mới |
| 4 | **Fixture column name khác nhau** — AI dùng: `fixture_id, model_name, type, start_universe, dmx_in_universe, num_channels`. Plan đề xuất: `fixture_id, name, type, manufacturer, universe, address, channels` | `AI_DMX_Autopilot/src/ingestion/legacy_show_importer.py:546-554` | ⚠️ Phải map alias |
| 5 | **.dmxrec format thực tế khớp plan** — HEADER 32 bytes, FRAME 524 bytes, struct pack `>4s B H H I B 18s` | `ArtNetController/src/show/dmx_recorder.py:40-44,270-278` | ✅ Khớp |
| 6 | **DMXFrame class đã đầy đủ** — to_bytes(), from_bytes(), validate_crc(), hỗ trợ V1+V2 | `ArtNetController/src/show/dmx_recorder.py:70-130` | ✅ Dùng lại được |

### 10.2 Đánh giá Impact lên Plan

#### Phase 1 — CẬP NHẬT QUAN TRỌNG:

**3.1.2 Module dmx_data/**
- `binary_reader.py` → **Không viết từ đầu**. Extract `DMXFrame`, `DMXPlayer` từ ArtNetController, bổ sung `_read_dmxrec()` từ AI_DMX_Autopilot
- `binary_writer.py` → **Không viết từ đầu**. Extract `DMXRecorder` từ ArtNetController
- `csv_converter.py` → **Viết mới**. Chưa có converter .dmxrec ↔ CSV
- `fixture_db.py` → **Viết mới**. Cần hỗ trợ cả 2 bộ column aliases

**3.1.4 Module common/**
- `crc.py` → **Extract** từ `dmx_recorder.py:55-68` (function `crc16_modbus`)
- `validation.py` → **Viết mới**

#### Phase 2 — CẬP NHẬT:

**3.2.1 API Server setup**
- ⚠️ **Không tạo server mới**. Mở rộng `src/webserver/server.py` hiện có (Flask, port 8080)
- Đã có sẵn: `/api/shows`, `/api/files/<show_name>`, `/upload`, `/download`, `/delete`
- Cần thêm: `/api/health`, `/api/shows/{name}/export-csv`, `/api/shows/import`, `/api/fixtures`

**3.2.2 API Endpoints**
- Endpoint `/api/shows` đã có nhưng chỉ return `show_names` (list string). Cần nâng cấp return full metadata

#### Phase 3 — KHÔNG ĐỔI:
- Plan đúng, vẫn cần viết ArtNetClient wrapper

#### Phase 4 — KHÔNG ĐỔI:
- Plan đúng

### 10.3 Action Items từ Rà soát

- [ ] **SỬA BUG**: `dmx_recorder.py` docstring line 9 — "Currently version 1" → "Currently version 2"
- [ ] **CẬP NHẬT PLAN Phase 1**: binary_reader/writer = EXTRACT không phải viết mới
- [ ] **CẬP NHẬT PLAN Phase 2**: API server = MỞ RỘNG webserver hiện có không phải tạo mới
- [ ] **THÊM VÀO Phase 1**: Fixture schema phải support column aliases (map 2 bộ tên)
- [ ] **VERIFY**: CSV format plan (section 5.2) vs AI's CSV reader (section `_build_csv_arrays_by_universe`)

---

_Tài liệu này sẽ được cập nhật khi triển khai từng phase._
_Repo GitHub: DMX_Shared_Lib sẽ được tạo mới._
