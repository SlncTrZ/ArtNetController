"""
GUI Tabs module initialization
"""

from .show_manager import ShowManagerTab
from .hardware_manager import HardwareManagerTab
from .dmx_view import DMXViewTab
from .settings import SettingsTab
from .record import RecordTab

__all__ = [
    'ShowManagerTab',
    'HardwareManagerTab', 
    'DMXViewTab',
    'SettingsTab',
    'RecordTab'
]