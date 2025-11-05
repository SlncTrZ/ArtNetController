"""
Version information for DMX Master LTS
"""

__version__ = "1.0.3"
__version_name__ = "DMX Master LTS 1.0.3"
__build__ = "2025.11.05.4"
__author__ = "Trương Công Định"
__email__ = "truongcongdinh97tcd@gmail.com"
__github_repo__ = "https://github.com/truongcongdinh97/DMX-Master"
__update_url__ = "https://api.github.com/repos/truongcongdinh97/DMX-Master/releases/latest"

# Release information
__release_type__ = "LTS"  # Long Term Support
__release_date__ = "2025-11-05"
__stability__ = "Stable"
__features__ = [
    "Binary DMX Recording & Playback",
    "Multi-Universe Support (0-15)",
    "Real-time Art-Net Controller", 
    "Web-based Remote Control",
    "Professional Show Management",
    "Rainbow Effects & Automation",
    "🎵 Timecode Sync Recording",
    "Depence/GrandMA Integration", 
    "Net-timecode & MTC Support",
    "💙 Enhanced DMX View (Fill UI)",
    "🔧 CANCEL RECORDING Feature",
    "🌍 Fixed Art-Net Packet Parsing",
    "� Full Depence Broadcast Support",
    "🔧 Enhanced Network Compatibility"
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
