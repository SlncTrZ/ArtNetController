"""
Version information for Art-Net Controller
"""

__version__ = "1.0.0"
__build__ = "2025.11.03"
__author__ = "Trương Công Định"
__github_repo__ = "https://github.com/truongcongdinh/ArtNetController"
__update_url__ = "https://api.github.com/repos/truongcongdinh/ArtNetController/releases/latest"

def get_version():
    """Get current version string"""
    return __version__

def get_full_version():
    """Get full version string with build"""
    return f"{__version__} (Build {__build__})"
