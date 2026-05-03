# Changelog — DMX Master LTS

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.3.0] — 2025-11-09

### Added
- License Tiers System: FREE (4 universes) / LICENSED (512 universes)
- 7-day trial period for FREE version
- Universe limit enforcement at all output layers (Art-Net, Serial, Recording, Playback)
- Art-Net PollReply optimization: 128 packets for 512 universes
- License status display in GUI status bar
- Universe validation for recording and playback

### Changed
- Universe dropdown auto-adjusts to license tier limit

## [1.2.0] — 2025-10-15

### Added
- IOBoard Serial Integration — background operation
- Auto-detect DMX Master IO Boards via USB/Serial
- Automatic universe mapping (Board #1→U0,1, #2→U2,3)
- Multi-board support with auto-reconnect
- Concurrent Art-Net + Serial DMX output
- DMX512 physical output via IOBoard (500000 baud, XOR checksum)

## [1.1.2] — 2025-09-20

### Added
- Start with Windows (Admin mode)
- Broadcast enable/disable notifications
- Network info with broadcast IP display

### Fixed
- ModuleNotFoundError on missing dependencies

## [1.1.1] — 2025-09-01

### Added
- Audio playback support
- DMX receiving control in playback mode
- System Settings tab with timecode toggle

### Fixed
- ArtPoll Reply auto-broadcast
- Universe detection byte order

## [1.1.0] — 2025-08-15

### Added
- Binary DMX recording and playback
- Multi-universe support (0-15)
- Web-based remote control
- Live DMX monitoring
- Rainbow effects and automation
- Timecode sync recording
- Depence/GrandMA integration
- Net-timecode and Art-Net 4 TC support
- Enhanced DMX View (fill UI)
- Cancel recording feature
- Professional logging system
- Optimized performance

### Fixed
- Art-Net packet parsing

## [1.0.0] — 2025-07-01

### Added
- Initial release
- Art-Net 4 protocol implementation
- PyQt6 GUI
- Show management (CRUD)
- DMX channel control
- Network adapter selection
