# DMX Master LTS - Customer Guide
## Professional Art-Net Lighting Controller

---

## 📖 Table of Contents

1. [Installation](#installation)
2. [Getting Started](#getting-started)
3. [Using the Application](#using-the-application)
4. [Show Management](#show-management)
5. [DMX Recording](#dmx-recording)
6. [License Activation](#license-activation)
7. [Troubleshooting](#troubleshooting)
8. [Support](#support)

---

## 🚀 Installation

### Windows Installation

1. **Download the Installer**
   - Get `DMX-Master-LTS-1.0.6-Setup.exe` from your download location
   - File size: ~100MB

2. **Run the Installer**
   - Double-click the `.exe` file
   - Click "Yes" if Windows SmartScreen appears (this is safe)
   - Follow the installation wizard
   - Choose installation location (default: `C:\Program Files\DMX Master LTS`)

3. **First Launch**
   - Find DMX Master LTS in Start Menu
   - Or use Desktop shortcut if you created one during installation
   - Application will create data folders automatically

### System Requirements

- **Operating System**: Windows 10 or later
- **Network**: Ethernet or Wi-Fi connection
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 200MB free space
- **Screen**: 1280x720 minimum resolution

---

## 🎯 Getting Started

### First Time Setup

When you launch DMX Master LTS for the first time:

1. **Welcome Screen**
   - Trial mode: 7 days (full features)
   - To activate license, see [License Activation](#license-activation)

2. **Network Configuration**
   - Go to `Settings` → `Art-Net`
   - Select your network interface
   - Default port: 6454 (Art-Net standard)
   - Click `Start Art-Net` to begin receiving DMX

3. **Test Connection**
   - Go to `Hardware Manager` tab
   - Click `Scan Network` to find Art-Net devices
   - You should see your lighting console or Depence software

### Quick Test

**Play the Default Rainbow Show:**

1. Go to `Show Manager` tab
2. Find "Default_Rainbow_Show" in the list
3. Click `Play` button
4. You should see rainbow effects across 6 universes!

---

## 💡 Using the Application

### Main Tabs Overview

#### 1️⃣ **Show Manager**
Play, organize, and manage your lighting shows

**Features:**
- ✅ Load and play binary DMX shows (.dmxrec files)
- ✅ Create playlists
- ✅ Loop and shuffle modes
- ✅ Real-time progress display

**How to Use:**
```
1. Shows are listed in the table
2. Select a show
3. Click "Add to Playlist" or "Play Single"
4. Use ▶️ Play/Pause, ⏭️ Next, ⏮️ Previous controls
5. Enable 🔁 Loop or 🔀 Shuffle as needed
```

#### 2️⃣ **Hardware Manager**
Discover and manage Art-Net devices on your network

**Features:**
- ✅ Auto-scan network for Art-Net nodes
- ✅ View device information (IP, MAC, universes)
- ✅ Test connectivity with ping
- ✅ Universe mapping

**How to Use:**
```
1. Click "Scan Network"
2. Wait for devices to appear (usually 2-5 seconds)
3. Select a device to see details
4. Enable "Auto Scan" for automatic discovery
```

#### 3️⃣ **DMX View**
Real-time visualization of DMX data

**Features:**
- ✅ View all 512 channels per universe
- ✅ Color-coded value display (0-255)
- ✅ Channel statistics
- ✅ Multiple universes support (0-31)

**How to Use:**
```
1. Select universe from dropdown (0-31)
2. Channels update in real-time
3. Active channels are highlighted
4. Hover over channels to see exact values
```

#### 4️⃣ **Settings**
Configure application preferences

**Main Settings:**

**Network:**
- Art-Net Port: 6454 (standard)
- Broadcast IP: 255.255.255.255
- Refresh Rate: 30 FPS (adjustable)

**Shows:**
- Storage location (automatic: AppData)
- Auto-save enabled

**Security:**
- Admin password for recording features
- Default: (none - set your own)

#### 5️⃣ **Record** *(Admin Only)*
Record and edit DMX data from Art-Net streams

**Requires admin mode** - see [Admin Features](#admin-features)

---

## 🎬 Show Management

### Playing Shows

**Method 1: Play Single Show**
```
1. Go to Show Manager
2. Select a show from the table
3. Click "Play Single" button
4. Show plays immediately
```

**Method 2: Create Playlist**
```
1. Select multiple shows (Ctrl+Click)
2. Click "Add to Playlist"
3. Arrange order by dragging items
4. Click "Play" to start playlist
5. Enable Loop/Shuffle as desired
```

### Show Information

Each show displays:
- **Name**: Show title
- **Duration**: Total length (seconds)
- **Scenes**: "Binary" for DMX recordings
- **Audio**: Associated music file (if any)

### Default Rainbow Show

**Included with installation:**
- **Name**: Default_Rainbow_Show
- **Duration**: 180 seconds (3 minutes)
- **Universes**: 6 (0-5)
- **Effects**: 
  - Rainbow color cycling
  - Cross-universe wave patterns
  - Breathing brightness
  - Per-universe phase shifting

**Perfect for testing your setup!**

---

## 🎥 DMX Recording

### Prerequisites

1. **Admin Mode Required**
   - Go to `Help` → `Admin Mode`
   - Enter admin password (if set)
   - Record tab will appear

2. **Timecode Source** *(Optional but recommended)*
   - Art-Net 4 Timecode (from Depence)
   - Net-Timecode (network timecode)

### Recording Process

**Step 1: Configure Recording**
```
1. Go to Record tab
2. Select universe to record (0-31)
3. Enable "Wait for Timecode" if using timecode sync
4. Choose timecode source (Art-Net 4 or Net-timecode)
```

**Step 2: Start Recording**
```
1. Click "Start Recording"
2. If timecode sync is ON:
   - Status shows "Waiting for timecode signal..."
   - Recording starts when timecode begins
3. If timecode sync is OFF:
   - Recording starts immediately
4. Perform your lighting cues in the console
```

**Step 3: Stop and Save**
```
1. Click "Stop Recording"
2. Recording statistics displayed:
   - Duration
   - Frames captured
   - Data points
3. Click "Save Recording"
4. Enter filename (auto-suggested with timestamp)
5. File saved as .dmxrec (binary format)
```

### Creating Shows from Recordings

**After saving a recording:**
```
1. Still in Record tab
2. Click "Create Show from Recording"
3. Enter show details:
   - Name
   - Description  
   - Author (optional)
4. Click "Create"
5. Show appears in Show Manager!
```

### Recording Tips

✅ **Best Practices:**
- Use timecode sync for precise synchronization
- Record universe 0 first, then others if needed
- Keep recordings under 10 minutes for best performance
- Test recording on one universe before doing multiple

⚠️ **Common Issues:**
- "No timecode signal": Check Depence timecode output settings
- "High frame rate": Reduce lighting console refresh rate
- "Large file size": Normal for long recordings (60 frames/second)

---

## 🔑 License Activation

### Trial Mode (7 Days)

**What you get:**
- ✅ Full access to all features
- ✅ Unlimited shows and recordings
- ✅ No watermarks or limitations
- ✅ 7 days from first installation

### Activating Your License

**Step 1: Get Device ID**
```
1. Go to Help → License Activation
2. Your Device ID is displayed
3. Click "Copy Device ID"
```

**Step 2: Request License**
```
Send email to: truongcongdinh97tcd@gmail.com

Subject: DMX Master LTS License Request

Body:
- Your Name:
- Company (optional):
- Device ID: [paste here]
- License Type: Standard / Professional
```

**Step 3: Activate**
```
1. You will receive a license key via email
2. Go to Help → License Activation
3. Paste the license key
4. Click "Activate"
5. Restart application
```

### License Types

**Standard License**
- Single computer
- All core features
- Free updates for 1 year
- Email support

**Professional License**
- Up to 3 computers
- All features + priority support
- Free updates for 2 years
- Phone/remote support

---

## 🔧 Troubleshooting

### Cannot Start Art-Net

**Problem:** "Failed to start Art-Net on port 6454"

**Solutions:**
1. Check if another application is using port 6454
2. Run as Administrator (right-click → Run as administrator)
3. Check Windows Firewall settings
4. Try changing port in Settings

### No DMX Output

**Problem:** Show plays but no DMX output

**Solutions:**
1. Check Art-Net is started (green indicator in status bar)
2. Verify network connection
3. Check universe mapping in Hardware Manager
4. Scan for devices to ensure they're online
5. Try playing Default Rainbow Show to test

### Timecode Not Detected

**Problem:** "Waiting for timecode signal..." never changes

**Solutions:**
1. Verify Depence timecode output is enabled
2. Check timecode source selection (Art-Net 4 vs Net-timecode)
3. Ensure correct network port (UDP 3040 for Net-timecode)
4. Try unchecking timecode sync for manual recording

### Application Crashes

**Problem:** Application closes unexpectedly

**Solutions:**
1. Check logs folder:
   - Location: `%LOCALAPPDATA%\DMX Master LTS\logs`
   - Open `artnet_controller.log`
   - Send to support if needed
2. Update to latest version
3. Reinstall application

### Unknown Publisher Warning

**Problem:** Windows shows "Unknown Publisher" warning

**Solution:**
- Click "More info" → "Run anyway"
- This is normal for unsigned applications
- Application is safe - source code available on GitHub

---

## 📁 File Locations

### User Data Folder

All your shows, recordings, and settings are stored in:

**Windows:**
```
%LOCALAPPDATA%\DMX Master LTS\
├── data\
│   ├── shows\           ← Your shows (.json + .dmxrec files)
│   └── recordings\      ← DMX recordings
├── config\              ← Application settings
└── logs\                ← Log files
```

**To open this folder:**
1. Press `Win + R`
2. Type: `%LOCALAPPDATA%\DMX Master LTS`
3. Press Enter

### Backup Your Data

**Important files to backup:**
- `data\shows\` - All your lighting shows
- `data\recordings\` - Recorded DMX data
- `config\` - Your settings and preferences

**How to backup:**
1. Close DMX Master LTS
2. Copy the entire `DMX Master LTS` folder
3. Save to external drive or cloud storage

---

## 📞 Support

### Getting Help

**Email Support:**
- Address: truongcongdinh97tcd@gmail.com
- Response time: 24-48 hours
- Include logs if reporting a bug

**What to Include in Support Requests:**
1. DMX Master LTS version
2. Windows version
3. Description of the problem
4. Steps to reproduce
5. Log files (if applicable)

### Useful Information for Support

**Check Your Version:**
```
Help → About
Shows: DMX Master v1.0.6
```

**Export Logs:**
```
Help → Export Logs
Saves all logs to a ZIP file
Attach to your support email
```

### Community & Resources

- **GitHub**: https://github.com/truongcongdinh97/DMX-Master
- **Documentation**: Check `docs` folder in installation directory
- **Updates**: Automatic update notification in application

---

## 🎓 Tips & Tricks

### Performance Optimization

**For Large Shows:**
1. Close unused applications
2. Disable auto-scan in Hardware Manager when not needed
3. Reduce refresh rate if experiencing lag
4. Use binary format (.dmxrec) for recordings

### Network Best Practices

**Stable Connection:**
1. Use wired Ethernet for best reliability
2. Disable Wi-Fi power saving mode
3. Use gigabit network switches
4. Avoid network loops

### Recording Quality

**Professional Recordings:**
1. Always use timecode sync with Depence
2. Test record/playback before important shows
3. Keep master recording + create variations
4. Name recordings descriptively with date

---

## 📋 Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Play/Pause | `Space` |
| Stop | `Escape` |
| Next Show | `Right Arrow` |
| Previous Show | `Left Arrow` |
| Start Recording | `R` (admin mode) |
| Stop Recording | `S` (admin mode) |
| Admin Mode | `Ctrl+Alt+A` |
| Settings | `Ctrl+,` |
| Quit | `Ctrl+Q` |

---

## ⚖️ License Information

DMX Master LTS is proprietary software.

**Copyright © 2025 Cong Dinh Truong**

**Trial Version:**
- 7 days full functionality
- No payment required for trial

**Licensed Version:**
- Perpetual license
- Includes updates and support
- Transferable to new computer with approval

For licensing inquiries: truongcongdinh97tcd@gmail.com

---

## 🔄 Updates

### Checking for Updates

```
Help → Check for Updates
Application will notify you if update is available
```

### Installing Updates

1. Close DMX Master LTS
2. Download new installer
3. Run installer (will detect existing installation)
4. Choose "Upgrade" to keep your data
5. Installation preserves:
   - All shows and recordings
   - Configuration settings
   - License activation

**Your data is safe during updates!**

---

**Thank you for using DMX Master LTS!**

*For the latest version and updates, visit our GitHub repository.*
