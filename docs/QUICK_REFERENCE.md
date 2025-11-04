# DMX Binary Recorder V2.0 - Quick Reference

## 🚀 Installation
```python
from show.dmx_recorder import DMXRecorder, DMXPlayer, verify_recording
```

---

## 📝 Recording

### Basic Recording
```python
recorder = DMXRecorder("show_001.dmxrec")
recorder.start_recording(fps=60.0)

# Record frames
recorder.write_frame(universe=0, dmx_data=bytes([255]*512))

# Stop and get stats
stats = recorder.stop_recording()
print(f"Recorded {stats['frame_count']} frames")
```

### Thread-Safe Recording (Multiple Sources)
```python
import threading

recorder = DMXRecorder("show_001.dmxrec")
recorder.start_recording(fps=60.0)

def record_universe(universe_id):
    while recording:
        dmx_data = get_dmx_data(universe_id)
        recorder.write_frame(universe_id, dmx_data)  # Thread-safe!

# Start multiple threads
threads = [threading.Thread(target=record_universe, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
```

---

## ▶️ Playback

### Simple Playback (Sequential)
```python
with DMXPlayer("show_001.dmxrec") as player:
    while True:
        frame = player.read_frame()
        if frame is None:
            break
        print(f"Frame {player.current_frame_index}: {frame}")
```

### Real-Time Playback (Multithreaded)
```python
with DMXPlayer("show_001.dmxrec", buffer_size=100) as player:
    info = player.get_info()
    player.start_playback()
    
    while True:
        frame = player.get_next_frame(timeout=0.1)
        if frame is None:
            break
        
        # Send to Art-Net
        controller.send_dmx(frame.universe, frame.data)
        
        # Wait for next frame time
        time.sleep(1.0 / info['fps'])
    
    player.stop_playback()
```

### Seeking
```python
with DMXPlayer("show_001.dmxrec") as player:
    # Seek to frame 100
    player.seek_frame(100)
    frame = player.read_frame()
    
    # Seek to 5.5 seconds
    frame = player.get_frame_at_time(5.5)
```

---

## 🔍 Verification

### Verify File Integrity
```python
stats = verify_recording("show_001.dmxrec", verbose=True)
print(f"Valid: {stats['valid_frames']}/{stats['total_frames']}")
print(f"CRC errors: {stats['crc_errors']}")
```

### Get Recording Info
```python
with DMXPlayer("show_001.dmxrec") as player:
    info = player.get_info()
    
print(f"""
File: {info['file_path']}
Version: {info['version']}
FPS: {info['fps']}
Frames: {info['frame_count']}
Duration: {info['duration']:.1f}s
Size: {info['file_size'] / 1024 / 1024:.2f} MB
CRC: {info['has_crc']}
""")
```

---

## 🎯 Common Patterns

### Pattern 1: Record from Art-Net
```python
controller = ArtNetController()
recorder = DMXRecorder("live_show.dmxrec")
recorder.start_recording(fps=60.0)

try:
    while recording:
        # Get Art-Net data
        for universe, dmx_data in controller.get_received_data():
            recorder.write_frame(universe, dmx_data)
        
        time.sleep(1 / 60)
        
except KeyboardInterrupt:
    stats = recorder.stop_recording()
    verify_recording("live_show.dmxrec", verbose=True)
```

### Pattern 2: Playback to Art-Net
```python
controller = ArtNetController()
controller.output_enabled = True

with DMXPlayer("live_show.dmxrec", buffer_size=100) as player:
    player.start_playback()
    
    interval = 1.0 / player.fps
    next_time = time.monotonic()
    
    while True:
        frame = player.get_next_frame(timeout=0.1)
        if frame is None:
            break
        
        controller.send_dmx(frame.universe, frame.data)
        
        # Precise timing
        next_time += interval
        sleep_time = next_time - time.monotonic()
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    player.stop_playback()
```

### Pattern 3: Convert JSON to Binary
```python
from show.dmx_recorder import convert_json_to_binary

success = convert_json_to_binary(
    json_path="old_show.json",
    output_path="new_show.dmxrec",
    fps=40.0
)
```

### Pattern 4: Analyze Recording
```python
with DMXPlayer("show.dmxrec") as player:
    frames = player.read_all_frames()
    
# Find active channels
active_channels = set()
for frame in frames:
    for i, value in enumerate(frame.data):
        if value > 0:
            active_channels.add((frame.universe, i))

print(f"Active channels: {len(active_channels)}")

# Find peak intensity
max_intensity = max(max(frame.data) for frame in frames)
print(f"Peak intensity: {max_intensity}")
```

---

## ⚙️ Configuration

### Recommended Settings

| Use Case | FPS | Buffer Size | Notes |
|----------|-----|-------------|-------|
| Music Show | 60 | 100 | Smooth effects |
| Theater | 40 | 50 | Lower CPU usage |
| High-Speed | 120 | 200 | Requires SSD |
| Low-Power | 30 | 50 | Raspberry Pi Zero |

### Performance Tuning
```python
# Increase buffer for high FPS
player = DMXPlayer("show.dmxrec", buffer_size=200)

# Disable drift correction if not needed
player.drift_correction_enabled = False

# Monitor performance
info = player.get_info()
if info['buffer_underruns'] > 0:
    print(f"⚠️ {info['buffer_underruns']} underruns - increase buffer_size!")
if info['crc_errors'] > 0:
    print(f"⚠️ {info['crc_errors']} CRC errors - file may be corrupted!")
```

---

## 🐛 Troubleshooting

### Problem: "CRC mismatch" warnings
**Solution**: File corrupted during write. Verify with `verify_recording()`.

### Problem: Buffer underruns
**Solution**: Increase `buffer_size` or lower FPS.

### Problem: Time drift accumulates
**Solution**: Enable drift correction (default: True).

### Problem: File too large
**Solution**: Lower FPS or use shorter recordings.

---

## 📊 File Format

### Header (32 bytes)
```
'DMXR' + version(1) + fps(2) + universe_count(2) + 
frame_count(4) + flags(1) + reserved(18)
```

### Frame (524 bytes)
```
timestamp(8) + universe(2) + dmx_data(512) + crc16(2)
```

### Size Calculation
```python
file_size = 32 + (frame_count × 524)

# Example: 10 min @ 60 FPS
frames = 10 × 60 × 60 = 36,000
size = 32 + (36,000 × 524) = 18,864,032 bytes = 18 MB
```

---

## 🔗 Links

- **Full Documentation**: `docs/BINARY_RECORDING_V2.md`
- **Upgrade Guide**: `docs/BINARY_RECORDING_UPGRADE.md`
- **Source Code**: `src/show/dmx_recorder.py`

---

## ⚡ Quick Examples

### Record for 10 seconds
```python
recorder = DMXRecorder("test.dmxrec")
recorder.start_recording(fps=60.0)

start = time.time()
while time.time() - start < 10:
    recorder.write_frame(0, bytes([128]*512))
    time.sleep(1/60)

recorder.stop_recording()
```

### Play first 100 frames
```python
with DMXPlayer("test.dmxrec") as player:
    player.start_playback()
    
    for i in range(100):
        frame = player.get_next_frame()
        if frame:
            print(f"Frame {i}: {frame}")
    
    player.stop_playback()
```

### Check file health
```python
with DMXPlayer("test.dmxrec") as player:
    info = player.get_info()
    
    health = "✅ HEALTHY" if info['has_crc'] else "⚠️ NO CRC"
    print(f"{info['file_path']}: {health}")
    print(f"Frames: {info['frame_count']}, FPS: {info['fps']}")
```

---

**🚀 V2.0 - Production Ready**
