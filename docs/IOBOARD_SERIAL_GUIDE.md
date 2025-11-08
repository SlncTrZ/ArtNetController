# 📡 IOBoard Serial Integration Guide

## 🎯 Overview

DMX Master LTS hỗ trợ kết nối trực tiếp với **DMX Master IO boards** qua Serial/USB để xuất DMX512 vật lý. 

**⚡ Auto-Operation Mode:**
- ✅ Tự động phát hiện boards khi khởi động
- ✅ Tự động kết nối (không cần thao tác)
- ✅ Tự động mapping universes
- ✅ Hoạt động im lặng ở background
- ✅ Không có GUI - chỉ log errors nếu có

---

## 🔌 Hardware Requirements

### IOBoard Specifications

| Spec | Value |
|------|-------|
| **Device Name** | `DMX Master IO #1`, `#2`, `#3`, ... |
| **Baudrate** | 500000 baud |
| **Protocol** | Custom DMX512 Serial Protocol |
| **Channels** | 512 per universe |
| **Connection** | USB (COM port on Windows) |

### Supported Configurations

- **Single Board**: 2 universes (Universe 0, 1)
- **Multiple Boards**: Unlimited (auto-mapping)
  - Board #1 → Universe 0, 1
  - Board #2 → Universe 2, 3
  - Board #3 → Universe 4, 5
  - etc.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install pyserial

```powershell
pip install pyserial>=3.5
```

### Step 2: Connect IOBoard

1. Plug IOBoard vào USB port
2. Windows sẽ tự động cài driver (nếu cần)
3. Device name PHẢI là: **"DMX Master IO #1"** (hoặc #2, #3...)

### Step 3: Launch DMX Master

1. Mở DMX Master LTS
2. IOBoard sẽ **tự động được phát hiện và kết nối**
3. Check log file để verify:

```
logs/app.log
```

**Success messages:**
```
INFO - Scanning for IOBoard devices...
INFO - ✅ IOBoard: Connected to 2 board(s)
INFO -    Board #1 → Universes [0, 1]
INFO -    Board #2 → Universes [2, 3]
```

✅ **Done!** DMX output sẽ tự động gửi đến IOBoard khi play show.

**No GUI interaction needed!**

---

## 🎛️ Auto-Mapping System

### Formula

```
Board #N → Universe [(N-1)*2, (N-1)*2+1]
```

### Examples

| Boards Connected | Mapping |
|------------------|---------|
| 1 board | Board #1 → U0, U1 |
| 2 boards | Board #1 → U0, U1<br>Board #2 → U2, U3 |
| 3 boards | Board #1 → U0, U1<br>Board #2 → U2, U3<br>Board #3 → U4, U5 |
| 4 boards | Board #1 → U0, U1<br>Board #2 → U2, U3<br>Board #3 → U4, U5<br>Board #4 → U6, U7 |

### Enable/Disable Auto-Mapping

- ✅ **Auto-Mapping ON** (default): Tự động mapping theo công thức
- ⚙️ **Auto-Mapping OFF**: Sử dụng Manual Mapping

---

## ⚙️ Manual Mapping (Advanced)

**Note:** Manual mapping hiện không có GUI. Auto-mapping sẽ được áp dụng mặc định.

### Formula (Auto-Mapping)

```
Board #N → Universe [(N-1)*2, (N-1)*2+1]
```

### Override Auto-Mapping (Code Only)

Nếu cần custom mapping, edit `src/serial/serial_controller.py`:

```python
# In init_serial_controller() method of main_window.py
# After scan_and_connect_all():

# Example: Custom mapping
self.serial_controller.set_manual_mapping(1, [0, 1, 5])  # Board #1 → U0,1,5
self.serial_controller.set_manual_mapping(2, [10, 11])   # Board #2 → U10,11
```

**Not recommended for normal users - auto-mapping works for most cases.**

---

## 📊 Serial Protocol Details

### Packet Format

```
Byte 0-1:   [0xAA][0x55]        # Header
Byte 2:     [Universe]          # Universe number (0-255)
Byte 3-4:   [Length Hi][Lo]     # DMX data length (512, Big Endian)
Byte 5-516: [DMX Data]          # 512 channels (0-255)
Byte 517:   [Checksum]          # XOR checksum
```

**Total: 517 bytes per packet**

### Performance

| Baudrate | TX Time | Max Refresh Rate |
|----------|---------|------------------|
| 500000 | ~10ms | ~97 Hz |
| 921600 | ~5.6ms | ~178 Hz |
| 230400 | ~22ms | ~45 Hz |
| 115200 | ~45ms | ~22 Hz |

**Recommended:** 500000 baud (DMX Master IO standard)

---

## 🔧 Troubleshooting

### Board Not Detected

**Problem:** Check log file và thấy "No IOBoard devices detected"

**Solutions:**

1. **Check USB connection**
   - Unplug và plug lại
   - Try different USB port
   
2. **Check Device Name (CRITICAL!)**
   - Open Device Manager (Windows)
   - Ports (COM & LPT)
   - Device name PHẢI chứa "DMX Master IO #N"
   - Example: "DMX Master IO #1 (COM3)"
   - Nếu khác tên → Rename device:
     - Right-click device → Properties
     - Port Settings → Advanced
     - Description: Change to "DMX Master IO #1"

3. **Check pyserial**
   ```powershell
   pip show pyserial
   ```
   Nếu không có:
   ```powershell
   pip install pyserial
   ```

4. **Check Logs**
   ```
   logs/app.log
   ```
   Search for "IOBoard" entries:
   ```
   INFO - Scanning for IOBoard devices...
   INFO - No IOBoard devices detected
   ```

5. **Manual Test**
   Run standalone scanner:
   ```powershell
   python src/serial/port_scanner.py
   ```
   Xem tất cả COM ports và device names

### Connection Failed

**Problem:** "Failed to connect to Board #1"

**Solutions:**

1. **Check if port is in use**
   - Close other applications using same COM port
   - Arduino IDE, Putty, HyperTerminal, etc.

2. **Check baudrate**
   - Default: 500000
   - If board uses different baudrate, update config:
   ```json
   "serial": {
     "baudrate": 115200
   }
   ```

3. **Check permissions (Linux)**
   ```bash
   sudo usermod -a -G dialout $USER
   sudo chmod 666 /dev/ttyUSB0
   ```

### DMX Output Not Working

**Problem:** Board connected nhưng không có DMX output

**Solutions:**

1. **Check universe mapping**
   - Verify universes trong Serial Manager tab
   - Play show với đúng universe number

2. **Check show playback**
   - Go to DMX View tab
   - Verify DMX data có values > 0
   - If DMX View shows data nhưng IOBoard không output → check wiring

3. **Check statistics**
   - Look at "Packets" column
   - If packets = 0 → no data being sent
   - If errors > 0 → check logs

4. **Check logs**
   ```
   logs/app.log
   ```
   Search for "Serial" hoặc "IOBoard" entries

### High Error Count

**Problem:** "Errors" column tăng nhanh

**Solutions:**

1. **USB cable quality**
   - Use short, high-quality USB cable
   - Avoid USB hubs

2. **Baudrate too high**
   - Reduce baudrate to 230400 hoặc 115200
   - Update in `config/app_config.json`

3. **COM port buffer overflow**
   - Reduce DMX refresh rate
   - In Settings → Art-Net → Refresh Rate

---

## 🎮 Integration with Art-Net

### Concurrent Output

DMX Master có thể gửi DMX **đồng thời** qua:
- ✅ **Art-Net** (network)
- ✅ **Serial** (IOBoard)

**Example:**
```
Universe 0 → IOBoard #1 (Serial) + Art-Net (Network)
Universe 1 → IOBoard #1 (Serial) + Art-Net (Network)
Universe 2 → IOBoard #2 (Serial) + Art-Net (Network)
```

### Workflow

```
[Show Playback]
      ↓
[DMX Data Generated]
      ↓
  ┌───┴────┐
  ↓        ↓
[Art-Net] [Serial]
  ↓        ↓
[Network] [IOBoard] → Physical DMX
```

---

## 💻 Configuration File

### Location

```
config/app_config.json
```

### Serial Section

```json
{
  "serial": {
    "enabled": true,
    "baudrate": 500000,
    "auto_mapping": true,
    "reconnect_on_error": true,
    "reconnect_interval": 5
  }
}
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | `true` | Enable/disable IOBoard serial output |
| `baudrate` | `500000` | Serial baudrate |
| `auto_mapping` | `true` | Auto-map universes (always enabled) |
| `reconnect_on_error` | `true` | Auto-reconnect on disconnect |
| `reconnect_interval` | `5` | Seconds between reconnect attempts |

**Note:** IOBoard hoạt động tự động ở background. Không có GUI. Chỉ cần set `"enabled": false` để tắt.

---

## 🔐 Configuration

### Background Operation

IOBoard hoạt động **hoàn toàn tự động**:
- ✅ Auto-detect khi app khởi động
- ✅ Auto-connect all boards
- ✅ Auto-mapping universes
- ✅ Silent operation (logs only)
- ✅ No GUI interaction needed

### Disable IOBoard

Edit `config/app_config.json`:
```json
{
  "serial": {
    "enabled": false
  }
}
```

Restart app để apply.

---

## 📈 Performance Tips

### Optimize Refresh Rate

**High Performance:**
```
Baudrate: 921600
Refresh Rate: 44 Hz
Result: Smooth DMX output, high CPU usage
```

**Balanced:**
```
Baudrate: 500000
Refresh Rate: 30 Hz
Result: Good performance, moderate CPU usage
```

**Low CPU:**
```
Baudrate: 230400
Refresh Rate: 20 Hz
Result: Lower CPU, acceptable for most shows
```

### Multiple Boards Performance

| Boards | Total Universes | CPU Load | Notes |
|--------|----------------|----------|-------|
| 1 | 2 | Low | Single serial write |
| 2 | 4 | Low | Parallel writes |
| 4 | 8 | Medium | 4x serial writes |
| 8 | 16 | Medium-High | Consider CPU specs |

**Recommendation:** Up to 4 boards (8 universes) on standard PC

---

## 🆘 Support

### Log Files

```
logs/app.log
```

Search for:
- `"Serial Controller"`
- `"IOBoard"`
- `"COM port"`

### Debug Mode

Enable debug logging:
```json
{
  "app": {
    "debug": true
  }
}
```

### Report Issue

Include:
1. Log file (`logs/app.log`)
2. Config file (`config/app_config.json`)
3. Screenshot of Serial Manager tab
4. Device Manager screenshot (Windows)

---

## 🎓 Advanced Usage

### Custom Baudrate

Edit `config/app_config.json`:
```json
{
  "serial": {
    "baudrate": 921600
  }
}
```

Restart application.

### Multiple Board Models

Nếu bạn có các board khác (không phải DMX Master IO):

1. Update device name pattern trong `src/serial/port_scanner.py`
2. Adjust protocol trong `src/serial/ioboard_protocol.py`

### API Integration

```python
from src.serial import SerialController

# Create controller
controller = SerialController(baudrate=500000)

# Scan and connect
count = controller.scan_and_connect_all()

# Send DMX
dmx_data = bytes([255] * 10 + [0] * 502)
controller.send_dmx(universe=0, dmx_data=dmx_data)

# Cleanup
controller.disconnect_all()
```

---

## 📚 References

- **DMX512 Protocol**: USITT DMX512-A
- **Serial Communication**: RS-232/USB-CDC
- **PySerial Documentation**: https://pyserial.readthedocs.io/

---

**Last Updated:** November 8, 2025  
**Version:** 1.2.0  
**Author:** DMX Master Development Team
