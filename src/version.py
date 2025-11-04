"""
Version information for DMX Master
"""

__version__ = "2.0.0"
__build__ = "2025.11.04"
__author__ = "Trương Công Định"
__email__ = "truongcongdinh97tcd@gmail.com"
__github_repo__ = "https://github.com/truongcongdinh97/DMX-Master"
__update_url__ = "https://api.github.com/repos/truongcongdinh97/DMX-Master/releases/latest"

def get_version():
    """Get current version string"""
    return __version__

def get_full_version():
    """Get full version string with build"""
    return f"{__version__} (Build {__build__})"
