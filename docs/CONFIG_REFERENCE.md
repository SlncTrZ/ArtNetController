# Configuration Reference — DMX Master LTS v1.3.0

File cấu hình: `config.json` (tự động tạo lần chạy đầu tiên)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ARTNET_API_KEY` | API key cho REST API authentication | (none) |

---

## Config Sections

### network

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `network.artnet_ip` | string | `"255.255.255.255"` | Art-Net broadcast IP |
| `network.artnet_port` | int | `6454` | Art-Net UDP port (theo spec) |
| `network.broadcast_ip` | string | (auto) | Broadcast IP của subnet |
| `network.interface` | string | (auto-detect) | Network interface name |
| `network.timeout` | float | `5.0` | Network timeout (seconds) |

### universes

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `universes.enabled` | list[int] | `[0,1,2,3]` | Universe đang enabled |
| `universes.output_enabled` | bool | `true` | Bật/tắt DMX output |
| `universes.default_universe` | int | `0` | Universe mặc định |
| `universes.max_universes` | int | `4` hoặc `512` | Max universes (theo license tier) |

### recording

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `recording.fps` | int | `30` | Recording frame rate |
| `recording.format` | string | `"binary"` | Format: `binary` hoặc `csv` |
| `recording.auto_save` | bool | `true` | Auto-save recording |
| `recording.compression` | bool | `false` | Compress recordings |
| `recording.buffer_size` | int | `1000` | Frame buffer size |
| `recording.default_path` | string | `"data/show_resources"` | Default save path |

### playback

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `playback.auto_loop` | bool | `false` | Loop playback |
| `playback.sync_audio` | bool | `true` | Sync with audio |
| `playback.drift_correction` | bool | `true` | Time drift correction |
| `playback.buffer_size` | int | `500` | Playback buffer frames |

### ui

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `ui.theme` | string | `"dark"` | Theme: `dark` hoặc `light` |
| `ui.language` | string | `"en"` | Language code |
| `ui.window_width` | int | `1280` | Window width (px) |
| `ui.window_height` | int | `800` | Window height (px) |
| `ui.fps_display` | bool | `true` | Show FPS counter |
| `ui.show_tooltips` | bool | `true` | Show tooltips |

### license

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `license.key` | string | `""` | License key |
| `license.type` | string | `"free"` | `free` hoặc `licensed` |
| `license.activated_at` | string | `""` | Activation timestamp |
| `license.expires_at` | string | `""` | Expiration timestamp |

### paths

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `paths.shows` | string | `"shows/"` | Show files directory |
| `paths.backups` | string | `"backups/"` | Backup directory |
| `paths.logs` | string | `"logs/"` | Log files directory |
| `paths.config_backups` | string | `"config_backups/"` | Config backup directory |
| `paths.temp` | string | `"temp/"` | Temporary files |

### updates

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `updates.auto_check` | bool | `true` | Auto-check for updates |
| `updates.check_interval_hours` | int | `24` | Check interval |
| `updates.include_prerelease` | bool | `false` | Include pre-release versions |
| `updates.auto_install` | bool | `false` | Auto-install updates |

### crash_reporting

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `crash_reporting.enabled` | bool | `true` | Enable crash reporting |
| `crash_reporting.anonymous` | bool | `true` | Anonymous reporting |
| `crash_reporting.include_system_info` | bool | `true` | Include OS/hardware info |
| `crash_reporting.send_logs` | bool | `false` | Include log files |

### advanced

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `advanced.log_level` | string | `"INFO"` | Log level: DEBUG/INFO/WARNING/ERROR |
| `advanced.log_rotation` | bool | `true` | Enable log rotation |
| `advanced.max_log_size_mb` | int | `10` | Max log file size |
| `advanced.keep_logs_days` | int | `30` | Log retention period |

---

## Config Migration (V1 → V2)

Ứng dụng tự động migrate từ V1 format (`settings.json`) sang V2 format (`config.json`). Quá trình:

1. Detect V1 file existence
2. Map V1 keys → V2 structure
3. Save V2 file
4. Backup V1 file to `config_backups/`

**V1 keys mapping:**

| V1 Key | V2 Path |
|--------|---------|
| `artnet_ip` | `network.artnet_ip` |
| `max_universes` | `universes.max_universes` |
| `record_fps` | `recording.fps` |
| `theme` | `ui.theme` |

---

## License Tiers

### FREE Version (default)

- 4 universes (U0-U3)
- 7-day trial period
- All features except universe expansion

### LICENSED Version

- 512 universes (U0-U511)
- RSA-2048 activation
- Hardware-bound license
- Online revocation check (24h)

**Activation flow:**
1. Generate hardware fingerprint (MAC + CPU + Platform)
2. Send to license server
3. Receive RSA-signed license file
4. Validate offline using embedded public key
