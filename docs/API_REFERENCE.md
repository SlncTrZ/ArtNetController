# API Reference — DMX Master LTS v1.3.0

REST API cho Art-Net Controller. Mặc định chạy tại `http://localhost:5000`.

## Authentication

Tất cả API requests yêu cầu header `X-API-Key`:

```
X-API-Key: <your_api_key>
```

API key được set qua environment variable `ARTNET_API_KEY`.

---

## Endpoints

### Health Check

```
GET /api/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.3.0",
  "uptime": 3600
}
```

---

### Shows

#### List Shows

```
GET /api/shows
```

**Response:**
```json
{
  "shows": [
    {
      "name": "show_001",
      "created": "2025-11-09T10:30:00",
      "frames": 1200,
      "duration": 40.0,
      "universes": [0, 1]
    }
  ]
}
```

#### Get Show Detail

```
GET /api/shows/<name>
```

**Response:**
```json
{
  "name": "show_001",
  "created": "2025-11-09T10:30:00",
  "frames": 1200,
  "duration": 40.0,
  "universes": [0, 1],
  "binary_file": "show_001.dmxrec",
  "binary_size": 245760
}
```

#### Download Show Binary

```
GET /api/shows/<name>/download
```

**Response:** Binary `.dmxrec` file

#### Export Show to CSV

```
POST /api/shows/<name>/export-csv
```

**Response:**
```json
{
  "status": "ok",
  "csv_file": "show_001_export.csv",
  "frames": 1200
}
```

#### Import CSV to Show

```
POST /api/shows/import
Content-Type: multipart/form-data
```

**Body:**
- `file` — CSV file
- `name` — Show name (optional)

**Response:**
```json
{
  "status": "ok",
  "show_name": "imported_show",
  "frames": 500
}
```

#### Delete Show

```
DELETE /api/shows/<name>
```

**Response:**
```json
{
  "status": "ok",
  "deleted": ["show_001.json", "show_001.dmxrec"]
}
```

---

### Recordings

#### List Recordings

```
GET /api/recordings
```

**Response:**
```json
{
  "recordings": [
    {
      "filename": "recording_20251109.dmxrec",
      "size": 245760,
      "created": "2025-11-09T10:30:00",
      "frames": 1200,
      "fps": 30
    }
  ]
}
```

---

### File Management

#### List Files in Show

```
GET /api/files/<show>
```

#### Download File

```
GET /download/<show>/<file>
```

#### Delete File

```
DELETE /delete/<show>/<file>
```

---

### Upload

#### Upload MP3

```
POST /upload
Content-Type: multipart/form-data
```

**Body:**
- `file` — MP3 file

**Response:** Redirect to show page

---

### Fixtures (Placeholder)

```
GET /api/fixtures
```

**Response:**
```json
{
  "fixtures": [],
  "message": "not yet implemented"
}
```

---

## Error Responses

| Status | Meaning |
|--------|---------|
| 400 | Bad Request — thiếu parameter hoặc format sai |
| 401 | Unauthorized — thiếu hoặc sai API key |
| 404 | Not Found — show/recording không tồn tại |
| 500 | Internal Server Error |

**Format:**
```json
{
  "error": "Show not found",
  "detail": "No show named 'xyz' exists"
}
```

---

## DMXRecorder Binary Format (.dmxrec)

| Offset | Size | Description |
|--------|------|-------------|
| 0 | 4 | Magic bytes: `DMXR` |
| 4 | 2 | Version (uint16) |
| 6 | 2 | Universe count (uint16) |
| 8 | 4 | Frame count (uint32) |
| 12 | 4 | FPS (uint32) |
| 16 | 4 | Frame size (uint32) |
| 20 | N | Frame data (512 bytes per universe per frame) |
| 20+N | 2 | CRC16 checksum |

**Frame layout:** `[universe_0_data (512 bytes)] [universe_1_data (512 bytes)] ...`
