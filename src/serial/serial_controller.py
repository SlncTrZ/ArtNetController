"""
Serial Controller for IOBoard Communication
Supports multiple DMX Master IO boards with automatic universe mapping

Auto-Mapping Logic:
- Board #1 → Universe 0, 1
- Board #2 → Universe 2, 3
- Board #3 → Universe 4, 5
- Board #N → Universe [(N-1)*2, (N-1)*2+1]
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass

try:
    import serial
    PYSERIAL_AVAILABLE = True
except ImportError:
    PYSERIAL_AVAILABLE = False
    logging.warning("pyserial not installed - Serial features disabled")

from .ioboard_protocol import IOBoardProtocol, DMXPacket
from .port_scanner import PortScanner, IOBoardInfo

logger = logging.getLogger(__name__)


@dataclass
class BoardConnection:
    """Active connection to an IOBoard"""
    board_info: IOBoardInfo
    port: serial.Serial
    universes: List[int]  # Mapped universes for this board
    packets_sent: int = 0
    errors: int = 0
    last_send_time: float = 0
    connected: bool = True


class SerialController:
    """Controller for multiple IOBoard serial connections"""
    
    def __init__(self, baudrate: int = 500000):
        """
        Initialize Serial Controller
        
        Args:
            baudrate: Serial baudrate (default 500000 for DMX Master IO)
        """
        self.baudrate = baudrate
        self.running = False
        
        # Active board connections: {board_number: BoardConnection}
        self.connections: Dict[int, BoardConnection] = {}
        
        # Universe to board mapping: {universe: board_number}
        self.universe_to_board: Dict[int, int] = {}
        
        # Auto-mapping enabled flag
        self.auto_mapping_enabled = True
        
        # Manual mapping override: {board_number: [universes]}
        self.manual_mapping: Dict[int, List[int]] = {}
        
        # Thread safety
        self.connections_lock = threading.Lock()
        
        # Callbacks
        self.connection_status_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        
        # Performance tracking
        self.total_packets_sent = 0
        self.total_errors = 0
        
        logger.info(f"Serial Controller initialized (baudrate: {baudrate})")
    
    def is_available(self) -> bool:
        """Check if serial features are available"""
        return PYSERIAL_AVAILABLE
    
    def set_connection_status_callback(self, callback: Callable):
        """Set callback for connection status changes"""
        self.connection_status_callback = callback
    
    def set_error_callback(self, callback: Callable):
        """Set callback for errors"""
        self.error_callback = callback
    
    def scan_and_connect_all(self) -> int:
        """
        Scan for all IOBoards and connect automatically
        
        Returns:
            int: Number of boards connected
        """
        logger.info("Scanning for IOBoards...")
        
        boards = PortScanner.scan_ports()
        
        if not boards:
            logger.warning("No IOBoards detected")
            return 0
        
        logger.info(f"Found {len(boards)} IOBoard(s), connecting...")
        
        connected_count = 0
        for board in boards:
            if self.connect_board(board.board_number):
                connected_count += 1
        
        # Apply auto-mapping after all boards connected
        if self.auto_mapping_enabled and connected_count > 0:
            self.apply_auto_mapping()
        
        logger.info(f"Connected to {connected_count}/{len(boards)} boards")
        return connected_count
    
    def connect_board(self, board_number: int) -> bool:
        """
        Connect to specific board by number
        
        Args:
            board_number: Board number to connect (1, 2, 3, ...)
            
        Returns:
            bool: True if connected successfully
        """
        # Check if already connected
        if board_number in self.connections:
            logger.warning(f"Board #{board_number} already connected")
            return True
        
        # Find board info
        board_info = PortScanner.find_board_by_number(board_number)
        if not board_info:
            logger.error(f"Board #{board_number} not found")
            return False
        
        try:
            # Open serial port
            port = serial.Serial(
                port=board_info.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=1.0
            )
            
            # Create connection object
            connection = BoardConnection(
                board_info=board_info,
                port=port,
                universes=[],  # Will be assigned by mapping
                packets_sent=0,
                errors=0,
                last_send_time=time.time(),
                connected=True
            )
            
            # Store connection
            with self.connections_lock:
                self.connections[board_number] = connection
            
            logger.info(f"✅ Connected to Board #{board_number} on {board_info.port}")
            
            # Notify callback
            if self.connection_status_callback:
                try:
                    self.connection_status_callback(board_number, True)
                except Exception as e:
                    logger.error(f"Error in connection callback: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Board #{board_number}: {e}")
            
            # Notify error callback
            if self.error_callback:
                try:
                    self.error_callback(board_number, str(e))
                except Exception:
                    pass
            
            return False
    
    def disconnect_board(self, board_number: int):
        """
        Disconnect from specific board
        
        Args:
            board_number: Board number to disconnect
        """
        with self.connections_lock:
            connection = self.connections.get(board_number)
            
            if not connection:
                logger.warning(f"Board #{board_number} not connected")
                return
            
            try:
                connection.port.close()
                connection.connected = False
                del self.connections[board_number]
                
                # Remove from universe mapping
                self.universe_to_board = {
                    uni: board for uni, board in self.universe_to_board.items()
                    if board != board_number
                }
                
                logger.info(f"Disconnected from Board #{board_number}")
                
                # Notify callback
                if self.connection_status_callback:
                    try:
                        self.connection_status_callback(board_number, False)
                    except Exception as e:
                        logger.error(f"Error in connection callback: {e}")
                
            except Exception as e:
                logger.error(f"Error disconnecting Board #{board_number}: {e}")
    
    def disconnect_all(self):
        """Disconnect from all boards"""
        with self.connections_lock:
            board_numbers = list(self.connections.keys())
        
        for board_number in board_numbers:
            self.disconnect_board(board_number)
        
        logger.info("Disconnected from all boards")
    
    def apply_auto_mapping(self):
        """
        Apply automatic universe mapping
        
        Formula: Board #N → Universe [(N-1)*2, (N-1)*2+1]
        
        Examples:
        - Board #1 → Universe 0, 1
        - Board #2 → Universe 2, 3
        - Board #3 → Universe 4, 5
        """
        if not self.auto_mapping_enabled:
            logger.info("Auto-mapping disabled, skipping")
            return
        
        with self.connections_lock:
            # Clear existing mapping
            self.universe_to_board.clear()
            
            # Apply auto-mapping for each connected board
            for board_number, connection in self.connections.items():
                # Calculate universes for this board
                universe_1 = (board_number - 1) * 2
                universe_2 = universe_1 + 1
                
                # Assign universes
                connection.universes = [universe_1, universe_2]
                
                # Update reverse mapping
                self.universe_to_board[universe_1] = board_number
                self.universe_to_board[universe_2] = board_number
                
                logger.info(f"Auto-mapped Board #{board_number} → Universe {universe_1}, {universe_2}")
        
        logger.info(f"Auto-mapping applied: {len(self.connections)} boards, {len(self.universe_to_board)} universes")
    
    def set_manual_mapping(self, board_number: int, universes: List[int]):
        """
        Set manual universe mapping for specific board
        
        Args:
            board_number: Board number
            universes: List of universe numbers to map
        """
        with self.connections_lock:
            connection = self.connections.get(board_number)
            
            if not connection:
                logger.error(f"Board #{board_number} not connected")
                return
            
            # Store manual mapping
            self.manual_mapping[board_number] = universes.copy()
            
            # Apply to connection
            connection.universes = universes.copy()
            
            # Update reverse mapping (remove old entries first)
            self.universe_to_board = {
                uni: board for uni, board in self.universe_to_board.items()
                if board != board_number
            }
            
            # Add new entries
            for universe in universes:
                self.universe_to_board[universe] = board_number
            
            logger.info(f"Manual mapping set: Board #{board_number} → Universes {universes}")
    
    def get_board_for_universe(self, universe: int) -> Optional[int]:
        """
        Get board number responsible for universe
        
        Args:
            universe: Universe number
            
        Returns:
            int: Board number or None if not mapped
        """
        return self.universe_to_board.get(universe)
    
    def send_dmx(self, universe: int, dmx_data: bytes) -> bool:
        """
        Send DMX data to appropriate board
        
        Args:
            universe: Universe number
            dmx_data: DMX channel data (up to 512 bytes)
            
        Returns:
            bool: True if sent successfully
        """
        # Find board responsible for this universe
        board_number = self.get_board_for_universe(universe)
        
        if board_number is None:
            # No board mapped to this universe
            logger.debug(f"No board mapped for Universe {universe}")
            return False
        
        with self.connections_lock:
            connection = self.connections.get(board_number)
            
            if not connection or not connection.connected:
                logger.warning(f"Board #{board_number} not connected (Universe {universe})")
                return False
            
            try:
                # Create DMX packet
                packet_bytes = IOBoardProtocol.create_packet(universe, dmx_data)
                
                # Send to serial port
                connection.port.write(packet_bytes)
                
                # Update statistics
                connection.packets_sent += 1
                connection.last_send_time = time.time()
                self.total_packets_sent += 1
                
                # Log first few packets for debugging
                if connection.packets_sent <= 3:
                    non_zero = sum(1 for x in dmx_data if x > 0)
                    logger.info(f"Sent DMX to Board #{board_number}: Universe {universe}, {len(dmx_data)} channels, {non_zero} active")
                
                return True
                
            except Exception as e:
                logger.error(f"Error sending DMX to Board #{board_number}: {e}")
                
                connection.errors += 1
                self.total_errors += 1
                
                # Notify error callback
                if self.error_callback:
                    try:
                        self.error_callback(board_number, str(e))
                    except Exception:
                        pass
                
                # Try to reconnect on error
                connection.connected = False
                threading.Thread(
                    target=self._reconnect_board,
                    args=(board_number,),
                    daemon=True
                ).start()
                
                return False
    
    def _reconnect_board(self, board_number: int):
        """
        Attempt to reconnect to board (runs in background thread)
        
        Args:
            board_number: Board number to reconnect
        """
        logger.info(f"Attempting to reconnect Board #{board_number}...")
        
        # Wait before retry
        time.sleep(2.0)
        
        # Disconnect old connection
        self.disconnect_board(board_number)
        
        # Try to reconnect
        max_retries = 3
        for attempt in range(max_retries):
            logger.info(f"Reconnect attempt {attempt+1}/{max_retries} for Board #{board_number}")
            
            if self.connect_board(board_number):
                logger.info(f"✅ Reconnected to Board #{board_number}")
                
                # Reapply mapping
                if self.auto_mapping_enabled:
                    self.apply_auto_mapping()
                elif board_number in self.manual_mapping:
                    self.set_manual_mapping(board_number, self.manual_mapping[board_number])
                
                return
            
            time.sleep(3.0)
        
        logger.error(f"Failed to reconnect Board #{board_number} after {max_retries} attempts")
    
    def get_connected_boards(self) -> List[int]:
        """Get list of connected board numbers"""
        with self.connections_lock:
            return list(self.connections.keys())
    
    def get_board_info(self, board_number: int) -> Optional[IOBoardInfo]:
        """Get info for specific board"""
        with self.connections_lock:
            connection = self.connections.get(board_number)
            return connection.board_info if connection else None
    
    def get_board_statistics(self, board_number: int) -> Optional[Dict]:
        """Get statistics for specific board"""
        with self.connections_lock:
            connection = self.connections.get(board_number)
            
            if not connection:
                return None
            
            return {
                'board_number': board_number,
                'port': connection.board_info.port,
                'universes': connection.universes,
                'packets_sent': connection.packets_sent,
                'errors': connection.errors,
                'last_send_time': connection.last_send_time,
                'connected': connection.connected
            }
    
    def get_all_statistics(self) -> Dict:
        """Get overall statistics"""
        with self.connections_lock:
            return {
                'total_boards': len(self.connections),
                'connected_boards': sum(1 for c in self.connections.values() if c.connected),
                'total_packets_sent': self.total_packets_sent,
                'total_errors': self.total_errors,
                'universe_mapping': self.universe_to_board.copy(),
                'auto_mapping_enabled': self.auto_mapping_enabled
            }
    
    def get_universe_mapping(self) -> Dict[int, List[int]]:
        """
        Get mapping of boards to universes
        
        Returns:
            Dict[int, List[int]]: {board_number: [universes]}
        """
        with self.connections_lock:
            mapping = {}
            for board_number, connection in self.connections.items():
                mapping[board_number] = connection.universes.copy()
            return mapping
    
    def is_connected(self) -> bool:
        """Check if any board is connected"""
        with self.connections_lock:
            return len(self.connections) > 0
    
    def get_connection_count(self) -> int:
        """Get number of connected boards"""
        with self.connections_lock:
            return len(self.connections)


# Test/Debug code
if __name__ == "__main__":
    import sys
    
    print("Serial Controller Test")
    print("=" * 60)
    
    if not PYSERIAL_AVAILABLE:
        print("ERROR: pyserial not installed")
        print("Install: pip install pyserial")
        sys.exit(1)
    
    # Create controller
    controller = SerialController(baudrate=500000)
    
    # Scan and connect
    print("\nScanning and connecting to IOBoards...")
    count = controller.scan_and_connect_all()
    
    if count == 0:
        print("No boards connected")
        sys.exit(0)
    
    # Show mapping
    print(f"\nConnected to {count} board(s)")
    mapping = controller.get_universe_mapping()
    for board_num, universes in mapping.items():
        print(f"  Board #{board_num} → Universes {universes}")
    
    # Test DMX output
    print("\nTesting DMX output...")
    test_data = bytes([255 if i < 10 else 0 for i in range(512)])
    
    for universe in range(4):  # Test first 4 universes
        success = controller.send_dmx(universe, test_data)
        if success:
            print(f"  ✅ Sent test data to Universe {universe}")
        else:
            print(f"  ❌ Failed to send to Universe {universe}")
    
    # Show statistics
    print("\nStatistics:")
    stats = controller.get_all_statistics()
    print(f"  Total packets: {stats['total_packets_sent']}")
    print(f"  Errors: {stats['total_errors']}")
    
    # Cleanup
    print("\nDisconnecting...")
    controller.disconnect_all()
    print("Done")
