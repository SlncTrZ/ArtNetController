# Timecode Recording Troubleshooting Guide - DMX Master LTS v1.0.1

## 🎵 Timecode Recording with Depence - Troubleshooting

### **Problem: Cannot record with timecode sync from Depence**

## ✅ **Quick Diagnosis Steps**

### **1. Check Timecode Settings in Record Tab**
- ✅ Enable "Wait for Timecode Signal Before Recording"
- ✅ Select "Art-Net 4 Timecode (Depence) - Variable fps"
- ✅ Status should show "Art-Net 4 Timecode using shared socket"

### **2. Verify Depence Configuration**
```
Depence Settings:
1. Go to Interfaces → Art-Net Settings
2. Enable "Send Timecode via Art-Net 4"
3. Set target IP: 127.0.0.1 (localhost)
4. Ensure Art-Net output is enabled
5. Start playback to generate timecode
```

### **3. Check Network Configuration**
```
Art-Net Requirements:
- Port 6454 must be available
- Windows Firewall may block Art-Net
- DMX Master LTS and Depence on same network
- No other Art-Net software interfering
```

## 🔧 **Common Issues & Solutions**

### **Issue 1: "Timecode: Not connected"**
**Symptoms:**
- Status shows "⏱️ Timecode: Not connected"
- Recording doesn't start after clicking RECORD

**Solutions:**
1. **Check Depence Art-Net Output:**
   ```
   Depence → Interfaces → Art-Net
   ✅ Enable Art-Net output
   ✅ Enable "Send Timecode via Art-Net 4"
   ✅ Set correct target IP (127.0.0.1)
   ```

2. **Verify Network Connection:**
   ```bash
   # Test if Art-Net packets are being sent
   python test_timecode_recording.py
   ```

3. **Windows Firewall:**
   ```
   Windows Defender Firewall → Allow an app
   ✅ Add DMXMaster-LTS-1.0.1-Build2.exe
   ✅ Allow both Private and Public networks
   ```

### **Issue 2: "Error: python-rtmidi not installed"**
**Symptoms:**
- MTC option shows error about python-rtmidi

**Solutions:**
1. **Install python-rtmidi (if using MTC):**
   ```bash
   pip install python-rtmidi
   ```

2. **Use Art-Net 4 Timecode instead:**
   - Select "Art-Net 4 Timecode (Depence)" instead of MTC
   - Art-Net 4 is preferred for Depence

### **Issue 3: "No MIDI devices found"**
**Symptoms:**
- MTC shows "No MIDI devices found"

**Solutions:**
1. **Use Art-Net 4 Timecode (Recommended):**
   - Art-Net 4 doesn't require MIDI hardware
   - More reliable for Depence integration

2. **For MTC (if needed):**
   - Install MIDI interface drivers
   - Connect MIDI interface
   - Verify MIDI devices in Windows

### **Issue 4: Port Conflict**
**Symptoms:**
- "Failed to start Art-Net 4 Timecode receiver"
- "Address already in use" error

**Solutions:**
1. **Close other Art-Net software:**
   - Close other lighting software
   - Check Task Manager for Art-Net processes

2. **Restart DMX Master LTS:**
   - Close and restart the application
   - This reinitializes the shared socket

## 🧪 **Testing Timecode Reception**

### **Test 1: Manual Timecode Test**
```bash
cd "h:\VSCode\ArtNetController"
python test_timecode_recording.py
```

### **Test 2: Depence Integration Test**
1. Start DMX Master LTS
2. Go to Record tab
3. Enable "Wait for Timecode Signal Before Recording"
4. Select "Art-Net 4 Timecode (Depence)"
5. Click "START RECORDING" → Should show "WAITING FOR TIMECODE..."
6. Start playback in Depence
7. Should see timecode display update and recording start

### **Test 3: Network Packet Monitoring**
```bash
# Use included Art-Net monitor
python test_artnet_monitor.py
```

## 📋 **Step-by-Step Recording Process**

### **Correct Workflow:**
1. **Setup Depence:**
   - Configure Art-Net 4 Timecode output
   - Set target IP to DMX Master LTS computer

2. **Setup DMX Master LTS:**
   - Open Record tab
   - ✅ Enable "Wait for Timecode Signal Before Recording"
   - ✅ Select "Art-Net 4 Timecode (Depence)"
   - ✅ Enable "Disable DMX Output During Record" (recommended)

3. **Start Recording:**
   - Click "START RECORDING"
   - Status: "WAITING FOR TIMECODE..."
   - Button: "CANCEL RECORDING" (orange)

4. **Start Depence Playback:**
   - Start timeline/show in Depence
   - DMX Master LTS should automatically start recording
   - Status: "Recording..." 
   - Button: "STOP RECORDING" (green)

5. **Finish Recording:**
   - Stop Depence playback or click "STOP RECORDING"
   - Save recording with "Save Recording" button

## ⚠️ **Common Mistakes**

### **❌ Wrong: Starting recording before Depence**
- Don't start Depence playback first
- Start recording in DMX Master LTS first (wait mode)
- Then start Depence

### **❌ Wrong: Using wrong timecode source**
- Don't use MTC for Depence
- Use "Art-Net 4 Timecode (Depence)" specifically

### **❌ Wrong: Firewall blocking**
- Windows Firewall may block Art-Net packets
- Add DMX Master LTS to firewall exceptions

## 🔍 **Advanced Diagnostics**

### **Check Art-Net Traffic**
```bash
# Run Art-Net monitor to see all packets
python test_artnet_monitor.py

# Look for:
# - OpCode 0x9700 (Art-Net 4 Timecode)
# - Source IP matching Depence computer
# - Regular timecode updates
```

### **Verify Depence Settings**
```
Depence → File → Preferences → Interfaces
Art-Net Tab:
✅ Enable Art-Net
✅ Interface: "All Interfaces" or specific network
✅ Send Timecode: ON
✅ Target: 127.0.0.1 (or DMX Master LTS IP)
```

### **Network Troubleshooting**
```bash
# Test if Art-Net port is accessible
telnet 127.0.0.1 6454

# Check if other Art-Net software is running
netstat -an | findstr 6454
```

## 📞 **Still Need Help?**

### **Collect Debug Information**
1. **Enable debug logging:**
   - Check logs in `logs/artnet_controller.log`
   - Look for timecode-related messages

2. **Test with provided scripts:**
   ```bash
   python test_timecode_recording.py
   python test_artnet_monitor.py
   ```

3. **Verify Depence version:**
   - Ensure Depence supports Art-Net 4 Timecode
   - Update Depence if necessary

### **Contact Information**
- Use the provided test scripts to gather diagnostic info
- Check logs for specific error messages
- Verify all network and firewall settings

---

**✅ Expected Result:** 
When working correctly, you should see:
- "⏱️ Timecode: 00:12:34:15 (25fps) - Art-Net 4 TC (Depence IP)"
- Recording starts automatically when Depence plays
- Perfect synchronization between Depence and DMX recording