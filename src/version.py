"""
Version information for DMX Master LTS
"""

__version__ = "1.3.0"
__version_name__ = "DMX Master LTS 1.3.0"
__build__ = "2025.11.09.1"
__author__ = "Trương Công Định"
__email__ = "truongcongdinh97tcd@gmail.com"
__github_repo__ = "https://github.com/truongcongdinh97/DMX-Master"
__update_url__ = "https://api.github.com/repos/truongcongdinh97/DMX-Master/releases/latest"

# Release information
__release_type__ = "LTS"  # Long Term Support
__release_date__ = "2025-11-09"
__stability__ = "Stable"
__features__ = [
    "Binary DMX Recording & Playback",
    "Multi-Universe Support (0-15)",
    "Real-time Art-Net Controller", 
    "Web-based Remote Control",
    "Professional Show Management",
    "Rainbow Effects & Automation",
    "Timecode Sync Recording",
    "Depence/GrandMA Integration", 
    "Net-timecode & Art-Net 4 TC Support",
    "Enhanced DMX View (Fill UI)",
    "CANCEL RECORDING Feature",
    "Fixed Art-Net Packet Parsing",
    "Full Depence Broadcast Support",
    "Enhanced Network Compatibility",
    "Professional Logging System",
    "Optimized Performance",
    "Audio Playback Support (V1.1.1)",
    "DMX Receiving Control in Playback Mode (V1.1.1)",
    "System Settings Tab with Timecode Toggle (V1.1.1)",
    "Fixed ArtPoll Reply Auto-Broadcast (V1.1.1)",
    "Fixed Universe Detection Byte Order (V1.1.1)",
    "Start with Windows (Admin) (V1.1.2)",
    "Broadcast Enable/Disable Notifications (V1.1.2)",
    "Network Info with Broadcast IP (V1.1.2)",
    "Fixed ModuleNotFoundError (V1.1.2)",
    "IOBoard Serial Integration - Background Operation (V1.2.0)",
    "Auto-detect DMX Master IO Boards via USB/Serial (V1.2.0)",
    "Automatic Universe Mapping (Board #1→U0,1, #2→U2,3) (V1.2.0)",
    "Multi-Board Support with Auto-Reconnect (V1.2.0)",
    "Concurrent Art-Net + Serial DMX Output (V1.2.0)",
    "DMX512 Physical Output via IOBoard (V1.2.0)",
    "License Tiers System - FREE (4 universes) / LICENSED (512 universes) (V1.3.0)",
    "Universe Limit Enforcement at All Layers (V1.3.0)",
    "Art-Net PollReply Optimization - 128 packets for 512 universes (V1.3.0)",
    "License Status Display in GUI (V1.3.0)",
    "Universe Validation for Recording/Playback (V1.3.0)",
    "7-Day Trial Period for FREE Version (V1.3.0)"
]

def get_version():
    """Get current version string"""
    return __version__

def get_version_name():
    """Get full version name"""
    return __version_name__

def get_full_version():
    """Get full version string with build"""
    return f"{__version_name__} (Build {__build__})"

def get_release_info():
    """Get complete release information"""
    return {
        "version": __version__,
        "name": __version_name__,
        "build": __build__,
        "type": __release_type__,
        "date": __release_date__,
        "stability": __stability__,
        "features": __features__,
        "author": __author__,
        "github": __github_repo__
    }
