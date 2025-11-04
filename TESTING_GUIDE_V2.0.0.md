# DMX Master V2.0.0 - Testing Guide

**Build Date:** November 4, 2025  
**Tester:** Truong Cong Dinh  
**Purpose:** Comprehensive testing before GitHub Release

---

## 📦 Build Information

| Component | File | Size | Status |
|-----------|------|------|--------|
| Main Application | `dist\ArtNetController\ArtNetController.exe` | 6.22 MB | ✅ Built |
| License Generator | `tools\dist\Create License for Customer V1.5.exe` | 38.02 MB | ✅ Built |

**Known Issues:**
- ⚠️  Icon not displaying (DMXMaster.ico is 270KB - too large for PyInstaller)
- 📝 Action: Will optimize icon post-testing (non-critical for functionality)

---

## ✅ Test 1: Basic Launch

**Objective:** Verify app starts correctly and GUI is functional

### Steps:
1. Navigate to `dist\ArtNetController\`
2. Double-click `ArtNetController.exe`
3. Wait for window to appear

### Expected Results:
- [ ] 1.1. Application window opens (no crash)
- [ ] 1.2. Title bar shows "DMX Master V2.0.0"
- [ ] 1.3. All 5 tabs visible and clickable:
  - Control Tab
  - Universe Tab
  - Show Tab
  - Record Tab
  - Settings Tab
- [ ] 1.4. License status displayed (e.g., "Trial: 7 days remaining")
- [ ] 1.5. No error dialogs on startup

### Verify Created Files:
```
dist\ArtNetController\
├── logs\
│   └── artnet_controller.log  (should be created)
├── config\
│   ├── app_config.json
│   ├── network_config.json
│   └── install_date.txt
```

---

## ✅ Test 2: Art-Net Controller

**Objective:** Test network functionality

### Steps:
1. Click **"Start Art-Net Controller"** button (if not auto-started)
2. Check status bar at bottom
3. Open Record tab
4. Move a fader (Channel 1-512)

### Expected Results:
- [ ] 2.1. Status shows "Art-Net Controller: Running on 0.0.0.0:6454"
- [ ] 2.2. No network errors
- [ ] 2.3. Faders respond smoothly
- [ ] 2.4. DMX values update in real-time

### Check Logs:
```
logs\artnet_controller.log should contain:
- "Art-Net socket bound to 0.0.0.0:6454"
- "Art-Net controller started"
```

---

## ✅ Test 3: Enhanced Logging (V2.0 Feature)

**Objective:** Verify logging system works correctly

### Steps:
1. Navigate to `dist\ArtNetController\logs\`
2. Open `artnet_controller.log` in text editor
3. Perform actions in app (move faders, switch tabs)
4. Refresh log file

### Expected Results:
- [ ] 3.1. Log file exists and is being written
- [ ] 3.2. Log entries have timestamps (format: `2025-11-04 20:XX:XX`)
- [ ] 3.3. Log includes:
  - Enhanced logging system initialized (V2.0)
  - License validation messages
  - Art-Net controller status
- [ ] 3.4. Log file rotates when reaching 10MB (test later if needed)
- [ ] 3.5. Crash handler active (check for `crashes.log` if any error occurs)

---

## ✅ Test 4: Config Manager (V2.0 Feature)

**Objective:** Test unified config system and V1 migration

### Test 4A: Fresh Install (Already Done)
Expected: `config.json` created with defaults

### Test 4B: V1 Migration (If needed)
1. Close app
2. Copy old V1 configs to config/:
   - `app_config.json`
   - `network_config.json`
3. Delete `config.json` if exists
4. Restart app

### Expected Results:
- [ ] 4.1. App detects V1 configs
- [ ] 4.2. Migration creates `config.json`
- [ ] 4.3. V1 configs backed up to `config/v1_backup/`
- [ ] 4.4. All settings preserved (Art-Net port, show paths, etc.)
- [ ] 4.5. App works normally after migration

---

## ✅ Test 5: Show Record/Playback & Disable Output (V2.0 Feature)

**Objective:** Test recording system with safety feature

### Steps:
1. Go to **Record Tab**
2. Check "Disable DMX Output During Record (Recommended)" checkbox
3. Click **"Start Recording"**
4. Move some faders (Channel 1, 5, 10)
5. Wait 5-10 seconds
6. Click **"Stop Recording"**
7. Save show as `test_show.json`

### Expected Results:
- [ ] 5.1. Checkbox is **checked by default** (orange text)
- [ ] 5.2. When recording starts:
  - Status shows "Recording... (DMX OUTPUT DISABLED)" in orange
  - Art-Net stops sending data (safety feature)
- [ ] 5.3. Recording captures DMX changes
- [ ] 5.4. When recording stops:
  - DMX output resumes automatically
  - Show file saved successfully
- [ ] 5.5. Playback works: Load `test_show.json` and play

### Check Logs:
```
Should contain:
- "⏸️  Art-Net output PAUSED"
- "▶️  Art-Net output RESUMED"
```

---

## ✅ Test 6: License System

**Objective:** Test license generation and activation

### Part A: Generate License
1. Navigate to `tools\dist\`
2. Run `Create License for Customer V1.5.exe`
3. Get Device ID from main app (Settings → License → Device ID)
4. Paste Device ID into generator
5. Select license type: **Perpetual**
6. Click **"🎯 Generate License"**
7. Click **"Save to File"** → Save as `test_license.json`

### Expected Results:
- [ ] 6.1. Generator app opens without errors
- [ ] 6.2. Device ID field accepts 64-character hex string
- [ ] 6.3. License JSON generated successfully
- [ ] 6.4. Signature format uses **pipe delimiter** (`device_id|license_id|issued_date`)

### Part B: Import License
1. Return to main app
2. Go to Settings → License
3. Click **"Import License"**
4. Select `test_license.json`
5. Click **Open**

### Expected Results:
- [ ] 6.5. License imported successfully
- [ ] 6.6. Status changes from "Trial: X days" to "✅ Licensed (Perpetual)"
- [ ] 6.7. License details shown:
  - License ID
  - Issued Date
  - Type: Perpetual
- [ ] 6.8. No expiration warnings

### Verify License File:
```
config\license.lic should be created (encrypted binary file)
```

---

## ✅ Test 7: V2.0 Menu Features

**Objective:** Test new menu items

### Test 7A: View Logs
1. Click **Help** menu
2. Click **"📁 View Logs Folder"**

### Expected Results:
- [ ] 7.1. Windows Explorer opens
- [ ] 7.2. Shows `dist\ArtNetController\logs\` folder
- [ ] 7.3. Log files visible

### Test 7B: Check for Updates
1. Click **Help** menu
2. Click **"🔄 Check for Updates"**

### Expected Results:
- [ ] 7.4. Dialog appears
- [ ] 7.5. Shows current version: V2.0.0
- [ ] 7.6. Checks GitHub API: `https://api.github.com/repos/truongcongdinh97/DMX-Master/releases/latest`
- [ ] 7.7. Shows result (up to date or update available)

**Note:** Since V2.0.0 not released yet, expected message: "Update check failed" or "No releases found"

---

## 📊 Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| 1. Basic Launch | ⏳ Pending | |
| 2. Art-Net Controller | ⏳ Pending | |
| 3. Enhanced Logging | ⏳ Pending | |
| 4. Config Manager | ⏳ Pending | |
| 5. Show Record/Playback | ⏳ Pending | |
| 6. License System | ⏳ Pending | |
| 7. V2.0 Features | ⏳ Pending | |

**Legend:**
- ✅ PASS
- ❌ FAIL
- ⚠️  PARTIAL (with notes)
- ⏳ PENDING

---

## 🐛 Known Issues

### Critical (Blocking Release):
- None identified yet

### Non-Critical:
1. **Icon not displaying in exe**
   - Cause: DMXMaster.ico is 270KB (too large for PyInstaller)
   - Impact: Exe shows default Windows icon
   - Fix: Optimize icon to <100KB with standard sizes (16, 32, 48, 256)
   - Priority: LOW (cosmetic only)

### Deferred (Post V2.0.0):
- UpdateManager integration (currently uses old check_for_updates code)
- Binary recorder (.dmxrec format) - deferred for V2.1
- Startup update check - deferred as non-critical

---

## ✅ Final Checks Before Release

- [ ] All tests PASS or marked with acceptable issues
- [ ] No critical bugs found
- [ ] Build installer with Inno Setup
- [ ] Create portable ZIP
- [ ] Test on clean Windows 10/11 machine
- [ ] Prepare release notes
- [ ] Upload to GitHub Release
- [ ] Test auto-update after release

---

## 📝 Testing Notes

**Date:** _______________  
**Tester:** _______________

**Additional Observations:**

```
(Space for notes)
```

**Recommendations:**

```
(Space for recommendations)
```

---

**Next Steps After Testing:**
1. Fix any CRITICAL issues
2. Document all findings
3. Create installer + portable package
4. Final QA on clean machine
5. GitHub Release v2.0.0
