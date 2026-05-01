"""
COM Port Scanner for IOBoard Detection
Auto-detect DMX Master IO boards and extract board numbers

Topic: serial
Last Updated: 2026-05-01
"""

import logging
import re
from typing import List, Optional, Dict
from dataclasses import dataclass

try:
    import serial.tools.list_ports
    PYSERIAL_AVAILABLE = True
except ImportError:
    PYSERIAL_AVAILABLE = False
    logging.warning("pyserial not installed - Serial features will not work")

logger = logging.getLogger(__name__)


@dataclass
class IOBoardInfo:
    """Information about detected IOBoard"""
    port: str              # COM3, /dev/ttyUSB0, etc.
    device_name: str       # "DMX Master IO #1"
    board_number: int      # 1, 2, 3, ...
    description: str       # Full device description
    vid: Optional[int]     # Vendor ID
    pid: Optional[int]     # Product ID
    serial_number: Optional[str]  # Hardware serial number
    manufacturer: Optional[str]   # Manufacturer name
    
    def __repr__(self):
        return f"IOBoard #{self.board_number} on {self.port}"
    
    def __lt__(self, other):
        """Sort by board number"""
        return self.board_number < other.board_number


class PortScanner:
    """Scanner for IOBoard COM ports"""
    
    # Device name pattern for DMX Master IO boards
    DEVICE_NAME_PATTERN = r"DMX Master IO #(\d+)"
    
    # Alternative patterns (case-insensitive)
    ALT_PATTERNS = [
        r"DMX\s*Master\s*IO\s*#?(\d+)",
        r"DMXMaster\s*IO\s*#?(\d+)",
        r"DMX-Master-IO-(\d+)",
    ]
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if pyserial is available"""
        return PYSERIAL_AVAILABLE
    
    @classmethod
    def _get_comports(cls) -> list:
        """Wrapper for serial.tools.list_ports.comports() — easier to mock in tests"""
        return serial.tools.list_ports.comports()

    @classmethod
    def scan_ports(cls) -> List[IOBoardInfo]:
        """
        Scan all COM ports and detect IOBoards
        
        Returns:
            List[IOBoardInfo]: Sorted list of detected boards
        """
        if not PYSERIAL_AVAILABLE:
            logger.error("Cannot scan ports: pyserial not installed")
            return []
        
        boards = []
        
        try:
            # List all available COM ports
            ports = cls._get_comports()
            logger.info(f"Scanning {len(ports)} COM ports for IOBoards...")
            
            for port_info in ports:
                # Try to extract board info
                board = cls._parse_port_info(port_info)
                if board:
                    boards.append(board)
                    logger.info(f"Found IOBoard: {board}")
                else:
                    # Log non-IOBoard devices for debugging
                    logger.debug(f"Ignored: {port_info.device} - {port_info.description}")
            
            # Sort by board number
            boards.sort()
            
            if boards:
                logger.info(f"Total IOBoards detected: {len(boards)}")
            else:
                logger.warning("No IOBoards detected")
            
            return boards
            
        except Exception as e:
            logger.error(f"Error scanning ports: {e}")
            return []
    
    @classmethod
    def _parse_port_info(cls, port_info) -> Optional[IOBoardInfo]:
        """
        Parse port info and extract IOBoard details
        
        Args:
            port_info: serial.tools.list_ports.ListPortInfo
            
        Returns:
            IOBoardInfo or None if not an IOBoard
        """
        # Get device description
        description = port_info.description or ""
        device = port_info.device or ""
        manufacturer = getattr(port_info, 'manufacturer', None) or ""
        
        # Combine all searchable text
        search_text = f"{description} {device} {manufacturer}"
        
        # Try to match device name pattern
        board_number = None
        device_name = None
        
        # Try main pattern first
        match = re.search(cls.DEVICE_NAME_PATTERN, search_text, re.IGNORECASE)
        if match:
            board_number = int(match.group(1))
            device_name = f"DMX Master IO #{board_number}"
        else:
            # Try alternative patterns
            for pattern in cls.ALT_PATTERNS:
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    board_number = int(match.group(1))
                    device_name = f"DMX Master IO #{board_number}"
                    break
        
        # Not an IOBoard if no match
        if board_number is None:
            return None
        
        # Extract VID/PID
        vid = getattr(port_info, 'vid', None)
        pid = getattr(port_info, 'pid', None)
        serial_number = getattr(port_info, 'serial_number', None)
        
        return IOBoardInfo(
            port=port_info.device,
            device_name=device_name,
            board_number=board_number,
            description=description,
            vid=vid,
            pid=pid,
            serial_number=serial_number,
            manufacturer=manufacturer
        )
    
    @classmethod
    def find_board_by_number(cls, board_number: int) -> Optional[IOBoardInfo]:
        """
        Find specific board by number
        
        Args:
            board_number: Board number to find (1, 2, 3, ...)
            
        Returns:
            IOBoardInfo or None if not found
        """
        boards = cls.scan_ports()
        for board in boards:
            if board.board_number == board_number:
                return board
        return None
    
    @classmethod
    def get_port_by_board_number(cls, board_number: int) -> Optional[str]:
        """
        Get COM port for specific board number
        
        Args:
            board_number: Board number (1, 2, 3, ...)
            
        Returns:
            str: COM port (e.g., "COM3") or None
        """
        board = cls.find_board_by_number(board_number)
        return board.port if board else None
    
    @classmethod
    def get_board_count(cls) -> int:
        """Get total number of detected IOBoards"""
        boards = cls.scan_ports()
        return len(boards)
    
    @classmethod
    def get_board_mapping(cls) -> Dict[int, str]:
        """
        Get mapping of board numbers to COM ports
        
        Returns:
            Dict[int, str]: {board_number: port}
            Example: {1: "COM3", 2: "COM4"}
        """
        boards = cls.scan_ports()
        return {board.board_number: board.port for board in boards}
    
    @classmethod
    def list_all_ports(cls) -> List[Dict]:
        """
        List ALL COM ports (not just IOBoards) for debugging
        
        Returns:
            List[Dict]: All port information
        """
        if not PYSERIAL_AVAILABLE:
            return []
        
        all_ports = []
        
        try:
            ports = serial.tools.list_ports.comports()
            for port_info in ports:
                port_dict = {
                    'port': port_info.device,
                    'description': port_info.description,
                    'hwid': port_info.hwid,
                    'vid': getattr(port_info, 'vid', None),
                    'pid': getattr(port_info, 'pid', None),
                    'serial_number': getattr(port_info, 'serial_number', None),
                    'manufacturer': getattr(port_info, 'manufacturer', None),
                }
                all_ports.append(port_dict)
            
            return all_ports
            
        except Exception as e:
            logger.error(f"Error listing ports: {e}")
            return []


# Test/Debug code
if __name__ == "__main__":
    print("IOBoard Port Scanner")
    print("=" * 60)
    
    if not PortScanner.is_available():
        print("ERROR: pyserial not installed")
        print("Install: pip install pyserial")
        exit(1)
    
    print("\nScanning for IOBoards...")
    boards = PortScanner.scan_ports()
    
    if boards:
        print(f"\nFound {len(boards)} IOBoard(s):")
        for board in boards:
            print(f"\n  Board #{board.board_number}")
            print(f"  Port: {board.port}")
            print(f"  Name: {board.device_name}")
            print(f"  Description: {board.description}")
            if board.vid and board.pid:
                print(f"  VID:PID: {board.vid:04X}:{board.pid:04X}")
            if board.serial_number:
                print(f"  Serial: {board.serial_number}")
        
        print("\nBoard Mapping:")
        mapping = PortScanner.get_board_mapping()
        for num, port in mapping.items():
            print(f"  Board #{num} → {port}")
    else:
        print("\nNo IOBoards detected")
        print("\nAll available COM ports:")
        all_ports = PortScanner.list_all_ports()
        for port in all_ports:
            print(f"\n  {port['port']}")
            print(f"  Description: {port['description']}")
            if port['vid'] and port['pid']:
                print(f"  VID:PID: {port['vid']:04X}:{port['pid']:04X}")
