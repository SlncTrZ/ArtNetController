"""
Art-Net Protocol Implementation
Xử lý giao thức Art-Net theo specification Art-Net 4
"""

import struct
import socket
import threading
import time
import logging
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ArtNetNode:
    """Thông tin một node Art-Net"""
    ip_address: str
    short_name: str
    long_name: str
    universe: int
    port_count: int
    node_type: int = 0
    last_seen: float = 0

class ArtNetPacket:
    """Base class cho các loại packet Art-Net"""
    
    # Art-Net packet opcodes
    ARTNET_POLL = 0x2000
    ARTNET_POLL_REPLY = 0x2100
    ARTNET_DMX = 0x5000
    ARTNET_SYNC = 0x5200
    ARTNET_TIME_CODE = 0x9700
    
    # Art-Net header
    ARTNET_HEADER = b"Art-Net\x00"
    
    def __init__(self):
        self.header = self.ARTNET_HEADER
        self.opcode = 0
        self.data = b""
    
    def pack(self) -> bytes:
        """Pack packet thành bytes để gửi"""
        return self.header + struct.pack('<H', self.opcode) + self.data
    
    @classmethod
    def unpack(cls, data: bytes):
        """Unpack bytes thành packet"""
        if len(data) < 10:
            return None
        
        if data[:8] != cls.ARTNET_HEADER:
            return None
        
        opcode = struct.unpack('<H', data[8:10])[0]
        payload = data[10:]
        
        return {
            'opcode': opcode,
            'payload': payload
        }

class ArtNetPoll(ArtNetPacket):
    """Art-Net Poll packet để discover nodes"""
    
    def __init__(self):
        super().__init__()
        self.opcode = self.ARTNET_POLL
        self.flags = 0x06  # Talk to me and diagnostics
        self.priority = 0x00
        
    def pack(self) -> bytes:
        self.data = struct.pack('<BB', self.flags, self.priority)
        return super().pack()

class ArtNetDMX(ArtNetPacket):
    """Art-Net DMX packet để gửi DMX data"""
    
    def __init__(self, universe: int = 0, sequence: int = 0, dmx_data: bytes = None):
        super().__init__()
        self.opcode = self.ARTNET_DMX
        self.sequence = sequence
        self.physical = 0
        self.universe = universe
        self.dmx_data = dmx_data or bytes(512)  # 512 channels DMX
        
    def pack(self) -> bytes:
        length = len(self.dmx_data)
        self.data = struct.pack('<BBHH', 
                               self.sequence, 
                               self.physical,
                               self.universe,
                               length) + self.dmx_data
        return super().pack()
    
    @classmethod
    def unpack_dmx(cls, payload: bytes):
        """Unpack DMX data từ payload"""
        if len(payload) < 6:
            return None
            
        sequence, physical, universe, length = struct.unpack('<BBHH', payload[:6])
        dmx_data = payload[6:6+length]
        
        return {
            'sequence': sequence,
            'physical': physical,
            'universe': universe,
            'length': length,
            'dmx_data': dmx_data
        }

class ArtNetController:
    """Main controller cho Art-Net communication"""
    
    def __init__(self, bind_ip: str = "0.0.0.0", port: int = 6454):
        self.bind_ip = bind_ip
        self.port = port
        self.socket = None
        self.running = False
        self.receive_thread = None
        
        # Callbacks
        self.dmx_received_callback: Optional[Callable] = None
        self.node_discovered_callback: Optional[Callable] = None
        
        # State
        self.discovered_nodes: Dict[str, ArtNetNode] = {}
        self.dmx_universe_data: Dict[int, bytes] = {}
        self.sequence_counter = 0
        
        # Universe mapping: {ip_address: {port_number: universe}}
        self.universe_mapping: Dict[str, Dict[int, int]] = {}
        
        # Thread locks
        self.nodes_lock = threading.Lock()
        self.dmx_lock = threading.Lock()
        
    def start(self) -> bool:
        """Khởi động Art-Net controller"""
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socket.settimeout(1.0)  # 1 second timeout for debugging
            
            # Bind to port
            self.socket.bind((self.bind_ip, self.port))
            
            # Start receive thread
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            logger.info(f"Art-Net controller started on {self.bind_ip}:{self.port}")
            
            # Send initial poll
            self.poll_network()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Art-Net controller: {e}")
            return False
    
    def stop(self):
        """Dừng Art-Net controller"""
        self.running = False
        
        if self.socket:
            self.socket.close()
            
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)
            
        logger.info("Art-Net controller stopped")
    
    def send_dmx(self, universe: int, dmx_data: bytes, broadcast: bool = True):
        """Gửi DMX data đến universe"""
        if not self.running or not self.socket:
            return False
            
        try:
            # Create DMX packet
            self.sequence_counter = (self.sequence_counter + 1) % 256
            packet = ArtNetDMX(universe, self.sequence_counter, dmx_data)
            
            # Send packet
            if broadcast:
                self.socket.sendto(packet.pack(), ('255.255.255.255', self.port))
            else:
                # Send to specific nodes in universe
                with self.nodes_lock:
                    for node in self.discovered_nodes.values():
                        if node.universe == universe:
                            self.socket.sendto(packet.pack(), (node.ip_address, self.port))
            
            # Update local state
            with self.dmx_lock:
                self.dmx_universe_data[universe] = dmx_data
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to send DMX: {e}")
            return False
    
    def set_universe_mapping(self, mapping: Dict[str, Dict[int, int]]):
        """
        Set universe mapping configuration
        mapping format: {ip_address: {port_number: universe}}
        Example: {'192.168.1.100': {0: 1, 1: 2}} means:
            - IP 192.168.1.100, Port 0 → Universe 1
            - IP 192.168.1.100, Port 1 → Universe 2
        """
        self.universe_mapping = mapping.copy()
        logger.info(f"Universe mapping updated: {len(mapping)} nodes configured")
    
    def send_dmx_with_mapping(self, universe: int, dmx_data: bytes):
        """
        Gửi DMX data đến universe theo cấu hình mapping
        Tìm tất cả các IP:Port được map với universe này và gửi
        """
        if not self.running or not self.socket:
            return False
        
        try:
            # Create DMX packet
            self.sequence_counter = (self.sequence_counter + 1) % 256
            packet = ArtNetDMX(universe, self.sequence_counter, dmx_data)
            packet_data = packet.pack()
            
            sent_count = 0
            
            # Tìm và gửi đến tất cả IP:Port được map với universe này
            for ip_address, port_mapping in self.universe_mapping.items():
                for port_num, mapped_universe in port_mapping.items():
                    if mapped_universe == universe:
                        # Gửi đến IP này
                        self.socket.sendto(packet_data, (ip_address, self.port))
                        sent_count += 1
                        logger.debug(f"Sent Universe {universe} to {ip_address}:Port{port_num}")
            
            # Nếu không có mapping, fallback về broadcast
            if sent_count == 0:
                logger.warning(f"No mapping found for Universe {universe}, using broadcast")
                self.socket.sendto(packet_data, ('255.255.255.255', self.port))
            
            # Update local state
            with self.dmx_lock:
                self.dmx_universe_data[universe] = dmx_data
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send DMX with mapping: {e}")
            return False
    
    def poll_network(self):
        """Gửi Art-Net Poll để discover nodes"""
        if not self.running or not self.socket:
            return
            
        try:
            poll_packet = ArtNetPoll()
            self.socket.sendto(poll_packet.pack(), ('255.255.255.255', self.port))
            logger.debug("Sent Art-Net Poll")
            
        except Exception as e:
            logger.error(f"Failed to send poll: {e}")
    
    def get_discovered_nodes(self) -> List[ArtNetNode]:
        """Lấy danh sách nodes đã discover"""
        with self.nodes_lock:
            return list(self.discovered_nodes.values())
    
    def get_universe_data(self, universe: int) -> Optional[bytes]:
        """Lấy DMX data của universe"""
        with self.dmx_lock:
            return self.dmx_universe_data.get(universe)
    
    def set_dmx_received_callback(self, callback: Callable):
        """Set callback khi nhận được DMX data"""
        self.dmx_received_callback = callback
    
    def set_node_discovered_callback(self, callback: Callable):
        """Set callback khi discover node mới"""
        self.node_discovered_callback = callback
    
    def _receive_loop(self):
        """Thread loop để nhận Art-Net packets"""
        logger.info("Art-Net receive loop started")
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                logger.debug(f"Received packet from {addr[0]}:{addr[1]}, size: {len(data)} bytes")
                self._handle_packet(data, addr)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Error in receive loop: {e}")
                break
        
        logger.info("Art-Net receive loop stopped")
    
    def _handle_packet(self, data: bytes, addr: tuple):
        """Xử lý packet nhận được"""
        packet = ArtNetPacket.unpack(data)
        if not packet:
            return
        
        opcode = packet['opcode']
        payload = packet['payload']
        
        if opcode == ArtNetPacket.ARTNET_DMX:
            self._handle_dmx_packet(payload, addr)
        elif opcode == ArtNetPacket.ARTNET_POLL_REPLY:
            self._handle_poll_reply(payload, addr)
        elif opcode == ArtNetPacket.ARTNET_POLL:
            self._handle_poll(payload, addr)
    
    def _handle_dmx_packet(self, payload: bytes, addr: tuple):
        """Xử lý DMX packet"""
        logger.debug(f"Processing DMX packet from {addr[0]}")
        dmx_info = ArtNetDMX.unpack_dmx(payload)
        if not dmx_info:
            logger.warning(f"Failed to unpack DMX packet from {addr[0]}")
            return
        
        universe = dmx_info['universe']
        dmx_data = dmx_info['dmx_data']
        
        logger.info(f"Received DMX data: Universe {universe}, {len(dmx_data)} channels from {addr[0]}")
        
        # Update local state
        with self.dmx_lock:
            self.dmx_universe_data[universe] = dmx_data
        
        # Call callback
        if self.dmx_received_callback:
            try:
                self.dmx_received_callback(universe, dmx_data, addr[0])
            except Exception as e:
                logger.error(f"Error in DMX callback: {e}")
        else:
            logger.warning("No DMX callback registered")
    
    def _handle_poll_reply(self, payload: bytes, addr: tuple):
        """Xử lý Poll Reply packet"""
        # Simplified poll reply parsing
        # Real implementation would parse full Art-Net poll reply structure
        ip_address = addr[0]
        
        # Create basic node info
        node = ArtNetNode(
            ip_address=ip_address,
            short_name=f"Node_{ip_address.split('.')[-1]}",
            long_name=f"Art-Net Node at {ip_address}",
            universe=0,  # Would parse from packet
            port_count=1,
            last_seen=time.time()
        )
        
        # Add to discovered nodes
        with self.nodes_lock:
            self.discovered_nodes[ip_address] = node
        
        # Call callback
        if self.node_discovered_callback:
            try:
                self.node_discovered_callback(node)
            except Exception as e:
                logger.error(f"Error in node discovery callback: {e}")
        
        logger.debug(f"Discovered Art-Net node: {ip_address}")
    
    def _handle_poll(self, payload: bytes, addr: tuple):
        """Xử lý Art-Net Poll - có thể respond nếu cần"""
        # For now, just log that we received a poll
        logger.debug(f"Received Art-Net Poll from {addr[0]}")
    
    def cleanup_old_nodes(self, timeout: float = 300.0):
        """Cleanup các nodes cũ không còn active"""
        current_time = time.time()
        
        with self.nodes_lock:
            expired_nodes = [
                ip for ip, node in self.discovered_nodes.items()
                if current_time - node.last_seen > timeout
            ]
            
            for ip in expired_nodes:
                del self.discovered_nodes[ip]
                logger.debug(f"Removed expired node: {ip}")