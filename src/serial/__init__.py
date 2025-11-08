"""
Serial Communication Module for IOBoard Integration
Supports multiple DMX Master IO boards with auto-mapping
"""

from .ioboard_protocol import IOBoardProtocol, DMXPacket
from .port_scanner import PortScanner, IOBoardInfo
from .serial_controller import SerialController

__all__ = [
    'IOBoardProtocol',
    'DMXPacket',
    'PortScanner',
    'IOBoardInfo',
    'SerialController'
]
