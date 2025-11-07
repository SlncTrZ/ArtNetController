# DMX Master LTS - Release Notes v1.1.0

**Release Date:** November 6, 2025

## 🎉 Major Features

### 1. Unified Create Show Dialog with Audio Assignment
- **NEW**: Single dialog for both "Create Show" and "Move to Shows" workflows
- **Audio Assignment**: Assign MP3/audio files directly when creating shows
- **Enhanced Metadata**: Add show name, description, and view duration
- **Consistent UX**: Same professional dialog experience across all workflows

### 2. Auto-Stop Recording When Timecode Stops
- **Smart Detection**: Automatically detects when timecode VALUE stops changing
- **3-Second Timeout**: Stops recording after 3 seconds of no timecode change
- **Auto-Trim**: Automatically trims last 3 seconds from recording
- **Auto-Save**: Saves recording with timestamp filename
- **Depence Compatible**: Handles Depence continuing to send packets after show ends

### 3. Improved Delete Functionality
- **Complete Deletion**: Deletes both .json metadata AND .dmxrec binary files
- **Name-Based Matching**: Scans all files and matches by show name (not filename)
- **Robust**: No more orphaned files or "file not found" errors
- **Auto-Reload**: Refreshes library after deletion

## 🔧 Improvements

### Recording Tab
- ✅ Reduced verbose logging (removed noisy ArtNet/DMX packet logs)
- ✅ Changed default recording settings:
  - Auto Trim: OFF (was ON)
  - Silence Threshold: 0 (was 5)
- ✅ Cleaner status messages and user feedback
- ✅ Enhanced success messages with show details

### Show Manager
- ✅ Fixed "Show file not found" error on delete
- ✅ Improved file scanning and name matching
- ✅ Better error handling for missing files

### DMX Recorder
- ✅ Full V2.0 binary format support
- ✅ Correct API usage throughout codebase
- ✅ Magic bytes validation (DMXR header)

## 🐛 Bug Fixes

1. **Auto-Stop Not Working**
   - Fixed: Changed from "update on packet" to "update only when VALUE changes"
   - Root cause: Depence sends packets with same timecode after show ends
   - Solution: Watchdog only resets when timecode value changes > 0.01s

2. **Delete Show/Recording Leaving Orphaned Files**
   - Fixed: Now deletes both .json and .dmxrec files
   - Added: Auto-reload after deletion

3. **DMXRecorder API Mismatch**
   - Fixed: Used correct methods (start_recording, stop_recording, write_frame)
   - Removed: Non-existent methods (open_write, close)

4. **Delete Show "File Not Found" Error**
   - Fixed: Scans all JSON files and matches by metadata.name
   - Handles: Spaces, underscores, and any filename variations

## 📦 Technical Changes

### New Files
- `src/gui/dialogs/create_show_dialog.py` - Unified dialog component (150 lines)

### Modified Files
- `src/gui/tabs/record.py`:
  - Timecode watchdog with VALUE-based detection (line 726-745)
  - Updated create_show() to use new dialog (line 1765-1820)
  - Updated move_recording_to_shows() to use new dialog (line 1587-1684)
  - Removed old embedded dialog class
- `src/gui/tabs/show_manager.py`:
  - Rewritten _delete_show() with name-based matching (line 852-920)

### Build Configuration
- Updated to version 1.1.0
- Enhanced .spec file with full module imports
- Added comprehensive feature documentation in spec file

## 🚀 Usage Notes

### Recording Workflow
1. Start timecode sync from Depence/controller
2. Recording automatically starts when timecode detected
3. When show ends, recording auto-stops after 3 seconds
4. Last 3 seconds automatically trimmed
5. File saved with timestamp

### Creating Shows
1. Click "Create Show" or select recording → "Move to Shows"
2. Unified dialog opens with:
   - Show name (auto-filled with timestamp or recording name)
   - Description field
   - Audio file browser (optional)
   - Duration display
3. Click "Create Show" to save

### Deleting Shows
- Select any show in Show Manager
- Click "Delete Show"
- Both .json and .dmxrec files deleted
- Library auto-reloads

## 📋 Known Limitations

- Auto-stop requires timecode VALUE to stop changing (0.01s threshold)
- Audio assignment is optional (can be added later in future versions)
- Binary format V2.0 (not backwards compatible with V1.x recordings)

## 🔜 Future Enhancements

- Edit show metadata after creation
- Batch audio assignment for multiple shows
- Recording preview before creating show
- Show merging/splitting tools

---

**Build:** DMXMaster-LTS-1.1.0.exe  
**Platform:** Windows 10/11  
**Python:** 3.13.7  
**PyQt:** 6.x  

For installation and usage, see [QUICKSTART.md](QUICKSTART.md)
