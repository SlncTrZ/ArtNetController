# Changelog - v1.1.0

## [1.1.0] - 2025-11-06

### ✨ Added
- **Unified Create Show Dialog** - Single dialog for both "Create Show" and "Move to Shows" with audio assignment
- **Audio Assignment** - Assign MP3/audio files when creating shows
- **Auto-Stop Recording** - Automatically stops recording when timecode stops (3s timeout)
- **Auto-Trim** - Automatically trims last 3 seconds when auto-stopping
- **Smart Timecode Detection** - Only updates watchdog when timecode VALUE changes (>0.01s)
- **Enhanced Show Metadata** - Show name, description, duration display in create dialog

### 🔧 Changed
- **Recording Defaults** - Auto Trim: OFF, Silence Threshold: 0
- **Reduced Logging** - Removed verbose ArtNet/DMX packet logs for cleaner UI
- **Delete Functionality** - Now deletes both .json and .dmxrec files
- **Show Deletion** - Name-based matching instead of filename matching
- **Success Messages** - Enhanced with show details (duration, audio status)

### 🐛 Fixed
- **Auto-Stop Bug** - Fixed watchdog not triggering when Depence continues sending packets
- **Delete Orphaned Files** - Now properly deletes binary .dmxrec files
- **"Show File Not Found" Error** - Fixed by scanning all files and matching by name
- **DMXRecorder API** - Corrected method calls (start_recording, stop_recording, write_frame)

### 🗑️ Removed
- **Old Embedded Dialog** - Removed duplicate CreateShowDialog class from record.py (223 lines)
- **Verbose Logging** - Removed detailed ArtNet/DMX packet logs

### 📦 Technical
- New file: `src/gui/dialogs/create_show_dialog.py` (150 lines)
- Updated: `src/gui/tabs/record.py` - Timecode watchdog, create/move workflows
- Updated: `src/gui/tabs/show_manager.py` - Delete with name matching
- Build: DMXMaster-LTS-1.1.0.spec with full module imports
- Tag: v1.1.0

---

## [1.0.6] - Previous Release
- DMX Recorder V2.0 binary format
- Show Manager improvements
- License system enhancements
