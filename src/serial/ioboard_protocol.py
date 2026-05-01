"""
IOBoard Protocol Implementation
DMX Master IO Board Serial Protocol

Packet Format:
[0xAA] [0x55]        # Header (2 bytes)
[Universe]           # Universe number (1 byte, 0-255)
[Length Hi][Lo]      # DMX data length (2 bytes, Big Endian, always 512)
[DMX Data]           # 512 bytes DMX channels (0-255)
[Checksum]           # XOR checksum (1 byte)

Total: 517 bytes per packet
Baudrate: 500000 (configurable)
Transmission time: ~10ms @ 500000 baud

Topic: serial
Last Updated: 2026-05-01
"""

import struct
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DMXPacket:
    """DMX packet for IOBoard serial protocol"""
    
    # Protocol constants
    HEADER_BYTE_1 = 0xAA
    HEADER_BYTE_2 = 0x55
    DMX_CHANNELS = 512
    PACKET_SIZE = 518  # Header(2) + Universe(1) + Length(2) + Data(512) + Checksum(1)
    
    def __init__(self, universe: int, dmx_data: bytes):
        """
        Create DMX packet for IOBoard
        
        Args:
            universe: Universe number (0-255)
            dmx_data: DMX channel data (512 bytes)
        """
        if not 0 <= universe <= 255:
            raise ValueError(f"Universe must be 0-255, got {universe}")
        
        # Pad or truncate to 512 bytes
        if len(dmx_data) < self.DMX_CHANNELS:
            dmx_data = dmx_data + bytes(self.DMX_CHANNELS - len(dmx_data))
        elif len(dmx_data) > self.DMX_CHANNELS:
            dmx_data = dmx_data[:self.DMX_CHANNELS]
        
        self.universe = universe
        self.dmx_data = dmx_data
    
    def pack(self) -> bytes:
        """
        Pack packet into bytes for serial transmission
        
        Returns:
            bytes: 517-byte packet ready to send
        """
        packet = bytearray()
        
        # Header (2 bytes)
        packet.append(self.HEADER_BYTE_1)
        packet.append(self.HEADER_BYTE_2)
        
        # Universe (1 byte)
        packet.append(self.universe)
        
        # Length (2 bytes, Big Endian, always 512)
        length = len(self.dmx_data)
        packet.extend(struct.pack('>H', length))
        
        # DMX Data (512 bytes)
        packet.extend(self.dmx_data)
        
        # Checksum (1 byte) - XOR of all previous bytes
        checksum = 0
        for byte in packet:
            checksum ^= byte
        packet.append(checksum)
        
        return bytes(packet)
    
    @classmethod
    def unpack(cls, data: bytes) -> Optional['DMXPacket']:
        """
        Unpack bytes into DMXPacket (for verification/testing)
        
        Args:
            data: 517-byte packet
            
        Returns:
            DMXPacket or None if invalid
        """
        if len(data) != cls.PACKET_SIZE:
            logger.error(f"Invalid packet size: {len(data)} (expected {cls.PACKET_SIZE})")
            return None
        
        # Verify header
        if data[0] != cls.HEADER_BYTE_1 or data[1] != cls.HEADER_BYTE_2:
            logger.error(f"Invalid header: {data[0]:02X} {data[1]:02X}")
            return None
        
        # Extract universe
        universe = data[2]
        
        # Extract length
        length = struct.unpack('>H', data[3:5])[0]
        if length != cls.DMX_CHANNELS:
            logger.warning(f"Unexpected length: {length} (expected {cls.DMX_CHANNELS})")
        
        # Extract DMX data
        dmx_data = data[5:5+cls.DMX_CHANNELS]
        
        # Verify checksum
        checksum_received = data[-1]
        checksum_calculated = 0
        for byte in data[:-1]:
            checksum_calculated ^= byte
        
        if checksum_received != checksum_calculated:
            logger.error(f"Checksum mismatch: {checksum_received:02X} != {checksum_calculated:02X}")
            return None
        
        return cls(universe, dmx_data)
    
    def __repr__(self):
        non_zero = sum(1 for x in self.dmx_data if x > 0)
        return f"DMXPacket(universe={self.universe}, channels={len(self.dmx_data)}, active={non_zero})"


class IOBoardProtocol:
    """IOBoard serial protocol handler"""
    
    # Default baudrate for DMX Master IO boards
    DEFAULT_BAUDRATE = 500000
    
    # Supported baudrates (in order of preference)
    SUPPORTED_BAUDRATES = [
        500000,   # Recommended for DMX Master IO
        921600,   # High speed
        460800,   # Medium-high speed
        230400,   # Medium speed
        115200,   # Standard speed
    ]
    
    @classmethod
    def create_packet(cls, universe: int, dmx_data: bytes) -> bytes:
        """
        Create DMX packet bytes
        
        Args:
            universe: Universe number (0-255)
            dmx_data: DMX channel data (up to 512 bytes)
            
        Returns:
            bytes: 517-byte packet ready to send
        """
        packet = DMXPacket(universe, dmx_data)
        return packet.pack()
    
    @classmethod
    def verify_packet(cls, data: bytes) -> bool:
        """
        Verify packet integrity
        
        Args:
            data: Packet bytes to verify
            
        Returns:
            bool: True if valid packet
        """
        packet = DMXPacket.unpack(data)
        return packet is not None
    
    @classmethod
    def calculate_transmission_time(cls, baudrate: int) -> float:
        """
        Calculate packet transmission time in milliseconds
        
        Args:
            baudrate: Serial baudrate
            
        Returns:
            float: Time in milliseconds
        """
        # Each byte = 10 bits (1 start + 8 data + 1 stop)
        bits_per_packet = DMXPacket.PACKET_SIZE * 10
        time_seconds = bits_per_packet / baudrate
        return time_seconds * 1000  # Convert to ms
    
    @classmethod
    def get_max_refresh_rate(cls, baudrate: int) -> float:
        """
        Get maximum DMX refresh rate for given baudrate
        
        Args:
            baudrate: Serial baudrate
            
        Returns:
            float: Max refresh rate in Hz
        """
        transmission_time_ms = cls.calculate_transmission_time(baudrate)
        return 1000.0 / transmission_time_ms
    
    @classmethod
    def get_recommended_baudrate(cls) -> int:
        """Get recommended baudrate for DMX Master IO"""
        return cls.DEFAULT_BAUDRATE


# Performance info logging
if __name__ == "__main__":
    print("IOBoard Protocol Performance Analysis")
    print("=" * 60)
    
    for baudrate in IOBoardProtocol.SUPPORTED_BAUDRATES:
        tx_time = IOBoardProtocol.calculate_transmission_time(baudrate)
        max_rate = IOBoardProtocol.get_max_refresh_rate(baudrate)
        print(f"Baudrate: {baudrate:>7} | TX Time: {tx_time:5.2f}ms | Max Rate: {max_rate:5.1f} Hz")
    
    print("=" * 60)
    print(f"Recommended: {IOBoardProtocol.DEFAULT_BAUDRATE} baud (DMX Master IO standard)")
    print(f"Packet Size: {DMXPacket.PACKET_SIZE} bytes")
    print(f"DMX Channels: {DMXPacket.DMX_CHANNELS}")
