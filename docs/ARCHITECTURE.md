# DMX Master LTS — System Architecture

> Version: 1.3.0 | Updated: 2026-05-02

## Data Flow Overview

```
┌──────────────┐     ArtNet UDP      ┌─────────────────────┐
│  Lighting    │ ──── Port 6454 ───► │  ArtNet Controller   │
│  Console     │ ◄── Poll Reply ──── │  (src/artnet/)       │
│  (GrandMA,   │                     │                      │
│   Depence)   │                     └──────┬───────────────┘
└──────────────┘                            │
                                            │ DMX frames (512ch)
                                            ▼
┌───────────────────────────────────────────────────────┐
│                    DMX Recorder                        │
│              (src/show/dmx_recorder.py)                │
│  • Binary format: Header + Frames + CRC16             │
│  • Thread-safe queue (800µs/frame @40Hz)               │
│  • Record → Playback → Export CSV                      │
└──────┬────────────────────────────────────┬───────────┘
       │ Playback                           │ Export
       ▼                                    ▼
┌──────────────┐                   ┌──────────────┐
│  Serial Out  │                   │  CSV / Binary│
│  (IOBoard)   │                   │  Files       │
│  500000 baud │                   └──────────────┘
│  Universe    │
│  mapping     │
└──────┬───────┘
       │ RS485
       ▼
┌──────────────┐
│  DMX Master  │
│  IO Board    │
│  (Hardware)  │
└──────────────┘
```

## Module Architecture

### Core Modules

| Module | Path | Responsibility |
|--------|------|---------------|
| **ArtNet Controller** | `src/artnet/controller.py` | UDP listener, DMX packet parser, node discovery |
| **DMX Recorder** | `src/show/dmx_recorder.py` | Record/playback DMX frames, binary I/O |
| **Show Manager** | `src/show/manager.py` | Show CRUD, playlist, metadata |
| **Serial Controller** | `src/serial/serial_controller.py` | Multi-board serial communication |
| **IOBoard Protocol** | `src/serial/ioboard_protocol.py` | Packet format (0xAA55 header, XOR checksum) |
| **Port Scanner** | `src/serial/port_scanner.py` | Auto-detect IOBoard COM ports |

### System Modules

| Module | Path | Responsibility |
|--------|------|---------------|
| **Config Manager** | `src/system/config_manager.py` | JSON config with migration & backup |
| **Update Manager** | `src/system/update_manager.py` | GitHub releases, auto-update |
| **License Manager** | `src/utils/license.py` | RSA-2048 + AES-256-GCM licensing |
| **Timecode Receiver** | `src/system/timecode_receiver.py` | SMPTE timecode sync |
| **Crash Reporter** | `src/system/crash_reporter.py` | Error logging & reporting |

### Interface Modules

| Module | Path | Responsibility |
|--------|------|---------------|
| **Web Server** | `src/webserver/server.py` | MP3 upload, file management |
| **REST API** | `src/webserver/api.py` | CRUD endpoints for AI_DMX_Autopilot |
| **GUI (PyQt5)** | `src/gui/` | Main window, tabs, widgets |

## Threading Model

```
Main Thread (GUI)
├── ArtNet Listener Thread (UDP recv)
├── DMX Recorder Thread (Queue consumer)
├── Serial Writer Thread (per board)
├── Flask Web Server Thread
├── License Revocation Check Thread (daemon, 24h interval)
└── Update Check Thread (on-demand)
```

## License Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Device ID   │────►│  RSA-2048    │────►│  AES-256-GCM │
│  (SHA256 of  │     │  Signature   │     │  Encrypted   │
│  MAC+CPU+OS) │     │  Verification│     │  License File│
└─────────────┘     └──────────────┘     └──────────────┘
                           │                     │
                    Offline Validation    File Protection
                    (Public Key Embedded) (HW-bound Key)
```

**Tiers**: FREE (4 universes, 7-day trial) / LICENSED (512 universes)

## Universe Mapping

```
Board #1 → Universe 0, 1    (auto-mapping)
Board #2 → Universe 2, 3
Board #N → Universe [(N-1)*2, (N-1)*2+1]

Manual override: controller.set_manual_mapping(board, [universes])
```

## File Formats

### DMX Recording (.dmxrec)
```
Header: 24 bytes (magic, version, channels, fps, frame_count, duration, crc16)
Frames:  N × FRAME_SIZE bytes (522 bytes = 4ch × 512 + 4ch flag)
Footer:  4 bytes (magic 0xDEADBEEF)
```

### IOBoard Packet (serial)
```
[0xAA][0x55][Universe:1][Length:2][DMX:512][Checksum:1] = 518 bytes
```

## Security Model

- **License**: RSA-2048 offline + AES-256-GCM encrypted + online revocation
- **Web Server**: CSRF tokens, `secure_filename()`, file size limits
- **Update**: SSL certificate validation, SHA256 checksum verification
- **License Server**: SSRF URL validation, HTTPS enforced