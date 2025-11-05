# 🎵 Timecode Sync Recording - User Guide

## 📋 **Overview**

**Timecode Sync Recording** là tính năng chuyên nghiệp mới trong **DMX Master LTS 1.0.0+** cho phép đồng bộ hoá recording DMX với phần mềm phát như **Depence**, **GrandMA**, **ETC Eos**, v.v.

Thay vì bắt đầu recording ngay khi nhấn nút **RECORD**, phần mềm sẽ đợi tín hiệu timecode từ phần mềm phát để đảm bảo đồng bộ hoàn hảo.

---

## 🎯 **Tại sao cần Timecode Sync?**

### ❌ **Vấn đề cũ:**
- Recording bắt đầu ngay khi nhấn RECORD
- Không đồng bộ với playback software
- Phải đoán thời điểm start recording
- Sai lệch thời gian giữa DMX và audio/video

### ✅ **Giải pháp mới:**
- Recording chờ tín hiệu timecode
- Đồng bộ hoàn hảo với Depence và phần mềm khác
- Frame-accurate synchronization
- Professional workflow như broadcast

---

## 🎛️ **Supported Timecode Formats**

| Format | FPS | Protocol | Software Support | Status |
|--------|-----|----------|------------------|--------|
| **Net-timecode** | 25fps | Network UDP | Depence, GrandMA | ✅ **Working** |
| **MTC** | 30fps | MIDI | Most audio software | ⚠️ Requires Visual Studio |
| **LTC** | Variable | Audio | Pro Tools, Logic | 🚧 Coming soon |
| **Art-Net Timecode** | Variable | Art-Net | Many lighting consoles | 🚧 Planned |

---

## 🚀 **Quick Start Guide**

### **Step 1: Enable Timecode Sync**
1. Open **Record Tab** (Admin only)
2. Find **"🎵 Timecode Sync Recording"** section
3. Check **"Wait for Timecode Signal Before Recording"**
4. Select timecode source (recommend **Net-timecode** for Depence)

### **Step 2: Configure Timecode Source**
- **For Depence**: Select "Net-timecode (Network) - 25fps"
- **For Audio Software**: Select "MTC (MIDI Time Code) - 30fps" 
- **Port**: Default 3040 for Net-timecode
- **MIDI Device**: Auto-detect for MTC

### **Step 3: Start Synchronized Recording**
1. Click **RECORD** button
2. Button changes to **"WAITING FOR TIMECODE..."** (orange)
3. Status shows: **"⏱️ Waiting for timecode signal..."**
4. Start playback in Depence/other software
5. Recording automatically starts when timecode received! 🎉

---

## 🎪 **Depence Configuration**

### **Method 1: Net-timecode (Recommended)**

1. **In Depence:**
   - Go to **Settings** → **Timecode**
   - Enable **"Send Net-timecode"**
   - Set IP: **127.0.0.1** (localhost)
   - Set Port: **3040**
   - Set Format: **25fps**

2. **In DMX Master:**
   - Timecode Source: **"Net-timecode (Network) - 25fps"**
   - Network Port: **3040**
   - Enable timecode sync checkbox

### **Method 2: MTC (If available)**

1. **Install Virtual MIDI Cable** (e.g., loopMIDI)
2. **In Depence:**
   - Enable **"Send MTC"**
   - Select virtual MIDI port
   - Set to **30fps**

3. **In DMX Master:**
   - Timecode Source: **"MTC (MIDI Time Code) - 30fps"**
   - MIDI Device: Select virtual MIDI port
   - Enable timecode sync checkbox

---

## 📊 **Status Indicators**

### **Timecode Status Display:**

| Status | Color | Meaning |
|--------|-------|---------|
| **"⏱️ Timecode: Not connected"** | Gray | Timecode sync disabled |
| **"⏱️ Timecode: Waiting for signal..."** | Orange | Enabled, waiting for signal |
| **"⏱️ Timecode: 12:34:56:15 (25fps) - Net-timecode"** | Green | Receiving timecode |
| **"⏱️ Timecode: Signal lost!"** | Red | Lost timecode connection |
| **"⏱️ Recording synced: 12:34:56:15 (25fps)"** | Green | Recording in progress |

### **Record Button States:**

| Button Text | Color | State |
|-------------|-------|-------|
| **"START RECORDING"** | Red | Ready to record |
| **"WAITING FOR TIMECODE..."** | Orange | Armed, waiting for sync |
| **"STOP RECORDING"** | Green | Recording active |

---

## 🔧 **Troubleshooting**

### **❌ "No receivers available"**

**Problem**: No timecode receivers could start
**Solutions**:
- Check network port not in use (3040)
- Install `python-rtmidi` for MTC support
- Verify MIDI devices available
- Try different port number

### **❌ "Net-timecode Error: [Errno 10048] Only one usage of each socket address"**

**Problem**: Port 3040 already in use
**Solutions**:
- Change port to 3041, 3042, etc.
- Close other software using port 3040
- Use `netstat -an | findstr 3040` to check usage

### **❌ "MTC Error: python-rtmidi not installed"**

**Problem**: MTC requires additional library
**Solutions**:
```bash
# Option 1: Install with conda (recommended)
conda install -c conda-forge python-rtmidi

# Option 2: Install with pip (requires Visual Studio)
pip install python-rtmidi

# Option 3: Use Net-timecode instead
# Select "Net-timecode" in DMX Master
```

### **❌ "Timecode: Signal lost!"**

**Problem**: Timecode stopped during recording
**Solutions**:
- Check Depence still sending timecode
- Verify network connection stable
- Check MIDI cable connections
- Recording continues even without timecode

### **❌ Recording doesn't start with timecode**

**Problem**: Timecode received but recording not starting
**Solutions**:
- Verify timecode checkbox is enabled
- Check timecode format matches (25fps vs 30fps)
- Look for error messages in status label
- Try manual recording mode first

---

## 💡 **Best Practices**

### **🎯 For Professional Shows:**
1. **Always test sync** before important recordings
2. **Use Net-timecode** for most reliable connection
3. **Monitor status display** during recording
4. **Keep backup manual recording** ready
5. **Document timecode settings** for show file

### **🔄 For Multi-track Sync:**
1. **Record audio separately** in Depence
2. **Use same timecode source** for all devices
3. **Note start timecode** in recording metadata
4. **Verify sync in post-production**

### **🛡️ For Reliability:**
1. **Dedicated network** for timecode (avoid WiFi)
2. **Wired MIDI connections** for MTC
3. **Test setup before show** day
4. **Have manual backup plan**

---

## 🚀 **Advanced Features**

### **Auto-detect Mode**
- Enables both MTC and Net-timecode receivers
- Automatically detects available signals
- Useful when unsure of source format

### **Custom Ports**
- Change Net-timecode port if conflicts
- Support multiple receivers on different ports
- Useful for complex setups

### **Timecode Metadata**
- Recording saves sync information
- Includes start timecode and FPS
- Helps with post-production alignment

---

## 📞 **Support**

### **Get Help:**
- **GitHub Issues**: [Report bugs](https://github.com/truongcongdinh97/DMX-Master/issues)
- **Email**: truongcongdinh97@gmail.com
- **Documentation**: [Complete guides](docs/INDEX.md)

### **Feature Requests:**
- **SMPTE LTC support** (audio-based timecode)
- **Art-Net timecode** integration
- **Multiple timecode sources** simultaneously
- **Timecode display** in show player

---

**🎵 Professional Timecode Sync - Making DMX Master truly professional!** ✨