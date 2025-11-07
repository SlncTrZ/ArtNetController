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
        """Unpack DMX data từ payload (after Art-Net header + opcode)"""
        if len(payload) < 8:  # Need at least version + sequence + physical + universe + length
            return None
            
        # Art-Net DMX payload format (after header + opcode):
        # Byte 0-1: Version (Little Endian)
        # Byte 2: Sequence  
        # Byte 3: Physical
        # Byte 4-5: Universe (Little Endian)
        # Byte 6-7: Length (Big Endian) - số bytes DMX data
        # Byte 8+: DMX data
        
        version = struct.unpack('<H', payload[0:2])[0]
        sequence = payload[2]
        physical = payload[3]
        universe = struct.unpack('<H', payload[4:6])[0]
        length = struct.unpack('>H', payload[6:8])[0]  # Big Endian!
        
        # Extract DMX data
        if len(payload) >= 8 + length:
            dmx_data = payload[8:8+length]
        else:
            dmx_data = payload[8:]  # Take what we have
        
        # Debug: Log parsing details
        logger.debug(f"DMX Parse: version=0x{version:04x}, seq={sequence}, phys={physical}, uni={universe}, len={length}, data_size={len(dmx_data)}")
        
        return {
            'version': version,
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
        
        # Auto-forward control
        self.auto_forward_enabled = False  # Checkbox control
        
        # V2.0: Output pause control (for recording safety)
        self.output_paused = False
        
        # V2.2: DMX receiving control (for playback mode - prevent interference)
        self.receiving_paused = False
        
        # V2.0: Timecode callback support
        self.timecode_callbacks = []

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
            
            logger.info(f"Art-Net socket bound to {self.bind_ip}:{self.port}")
            logger.info(f"Listening for Art-Net on UDP port {self.port}")
            logger.info(f"Send Art-Net to: 127.0.0.1, {self.bind_ip}, or 255.255.255.255")
            
            # Start receive thread
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            logger.info(f"Art-Net controller started on {self.bind_ip}:{self.port}")
            
            # V2.2: REMOVED auto-poll on startup
            # User complaint: Software sends ArtPoll Reply without receiving ArtPoll request
            # FIX: Do NOT send initial poll automatically
            # User must click "Ping Device" button in Hardware Manager to scan network
            logger.info("Art-Net receiver ready - use 'Ping Device' to scan network")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Art-Net controller: {e}")
            return False
    
    def pause_output(self):
        """Pause DMX output (V2.0 - for recording safety)"""
        self.output_paused = True
        logger.info("Art-Net output PAUSED")

    def resume_output(self):
        """Resume DMX output (V2.0)"""
        self.output_paused = False
        logger.info("Art-Net output RESUMED")
    
    def pause_dmx_receiving(self):
        """Pause DMX receiving (V2.2 - for playback mode to prevent interference)"""
        self.receiving_paused = True
        logger.info("⏸️ Art-Net DMX RECEIVING PAUSED (Playback Mode)")
    
    def resume_dmx_receiving(self):
        """Resume DMX receiving (V2.2)"""
        self.receiving_paused = False
        logger.info("▶️ Art-Net DMX RECEIVING RESUMED")
    
    def register_timecode_callback(self, callback_func: Callable):
        """Register callback for timecode packets (V2.0)"""
        if callback_func not in self.timecode_callbacks:
            self.timecode_callbacks.append(callback_func)
            logger.debug(f"Timecode callback registered (total: {len(self.timecode_callbacks)})")
        else:
            logger.debug(f"Callback already registered: {callback_func}")
    
    def unregister_timecode_callback(self, callback_func: Callable):
        """Unregister timecode callback (V2.0)"""
        if callback_func in self.timecode_callbacks:
            self.timecode_callbacks.remove(callback_func)
            logger.debug("Timecode callback unregistered from Art-Net controller")

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
        
        # V2.0: Skip sending if output is paused (recording safety)
        if self.output_paused:
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
        
        # Tự động tắt auto-forward nếu không có nodes
        if not self.universe_mapping:
            self.auto_forward_enabled = False
            logger.info("Auto-forward disabled: No nodes configured")
        
        logger.info(f"Universe mapping updated: {len(mapping)} nodes configured")
    
    def set_auto_forward(self, enabled: bool):
        """Bật/tắt auto-forward"""
        # Chỉ cho phép bật nếu có nodes được cấu hình
        if enabled and not self.universe_mapping:
            logger.warning("Cannot enable auto-forward: No nodes configured")
            return False
        
        self.auto_forward_enabled = enabled
        status = "enabled" if enabled else "disabled"
        logger.info(f"Auto-forward {status}")
        return True
    
    def is_auto_forward_enabled(self) -> bool:
        """Kiểm tra trạng thái auto-forward"""
        return self.auto_forward_enabled
    
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
            
            # Nếu không có mapping, gửi đến localhost + broadcast
            # Để có thể test với phần mềm thứ 3 trên cùng máy
            if sent_count == 0:
                logger.debug(f"No mapping found for Universe {universe}, sending to localhost + broadcast")
                
                # Gửi đến localhost (cho phần mềm thứ 3 trên cùng máy)
                self.socket.sendto(packet_data, ('127.0.0.1', self.port))
                
                # Gửi broadcast (cho các thiết bị khác trên mạng)
                self.socket.sendto(packet_data, ('255.255.255.255', self.port))
                
                sent_count = 2
            
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
                logger.debug(f"RX from {addr[0]}:{addr[1]}, size: {len(data)} bytes")
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
            logger.warning(f"Failed to unpack packet from {addr[0]}")
            return
        
        opcode = packet['opcode']
        payload = packet['payload']
        
        # DEBUG: Log ALL opcodes (moved to DEBUG level to reduce spam)
        logger.debug(f"Received OpCode: 0x{opcode:04X} from {addr[0]}")
        
        # Route packets to handlers
        if opcode == ArtNetPacket.ARTNET_DMX:
            self._handle_dmx_packet(payload, addr)
        elif opcode == ArtNetPacket.ARTNET_POLL_REPLY:
            logger.debug(f"Poll Reply received from {addr[0]}")
            self._handle_poll_reply(payload, addr)
        elif opcode == ArtNetPacket.ARTNET_POLL:
            logger.debug(f"Poll received from {addr[0]}")
            self._handle_poll(payload, addr)
        elif opcode == ArtNetPacket.ARTNET_TIME_CODE:
            logger.debug(f"Timecode packet (OpCode 0x{opcode:04X}) from {addr[0]}")
            self._handle_timecode_packet(data, addr)  # Pass full data for timecode processing
        else:
            logger.debug(f"Unknown packet type 0x{opcode:04X} from {addr[0]}")
    
    def _handle_timecode_packet(self, data: bytes, addr: tuple):
        """Handle Art-Net 4 Timecode packet (V2.0)"""
        try:
            # Forward to registered timecode callbacks
            if len(self.timecode_callbacks) == 0:
                # Only log warning once to reduce spam
                self._timecode_warning_count = getattr(self, '_timecode_warning_count', 0) + 1
                if self._timecode_warning_count == 1:
                    logger.warning("Timecode packet received but NO callbacks registered")
                    logger.info("Enable 'Wait for Timecode Signal' in Record tab to capture timecode")
                return
            
            for callback in self.timecode_callbacks:
                try:
                    callback(data, addr)
                except Exception as e:
                    logger.error(f"Error in timecode callback: {e}")
            
            logger.debug(f"Timecode packet forwarded to {len(self.timecode_callbacks)} callback(s)")
            
        except Exception as e:
            logger.error(f"Error handling timecode packet: {e}")
    
    def _handle_dmx_packet(self, payload: bytes, addr: tuple):
        """Xử lý DMX packet với optimization để giảm load"""
        # V2.2: Skip receiving if paused (playback mode - prevent interference)
        if self.receiving_paused:
            logger.debug(f"DMX receiving paused - ignoring packet from {addr[0]}")
            return
        
        logger.debug(f"Processing DMX packet from {addr[0]}")
        dmx_info = ArtNetDMX.unpack_dmx(payload)
        if not dmx_info:
            logger.warning(f"Failed to unpack DMX packet from {addr[0]}")
            return
        
        universe = dmx_info['universe']
        dmx_data = dmx_info['dmx_data']
        
        # VALIDATE: Clip to 512 channels max (prevent 515 channel bug)
        if len(dmx_data) > 512:
            logger.warning(f"DMX data truncated: {len(dmx_data)} → 512 channels from {addr[0]}")
            dmx_data = dmx_data[:512]
        
        # CRITICAL: Make a copy of dmx_data to prevent reference issues
        dmx_data_copy = bytes(dmx_data)
        
        # OPTIMIZATION 1: Check if data actually changed
        data_changed = False
        with self.dmx_lock:
            previous_data = self.dmx_universe_data.get(universe)
            
            # Check if data is identical to previous
            if previous_data is not None and previous_data == dmx_data_copy:
                # Data unchanged - skip callback to reduce CPU load
                logger.debug(f"⏩ Skipping Universe {universe} - data unchanged")
                return
            
            # OPTIMIZATION 2: Check if all channels are zero (blackout)
            # Only check first time or periodically to save CPU
            is_all_zero = all(b == 0 for b in dmx_data_copy)
            
            if is_all_zero:
                # If previous was also all zero, skip callback
                if previous_data is not None and all(b == 0 for b in previous_data):
                    logger.debug(f"Skipping Universe {universe} - still all zeros")
                    return
                else:
                    # First time going to blackout - update once
                    logger.debug(f"Universe {universe} entered blackout")
                    data_changed = True
            else:
                # Data changed and not all zero
                data_changed = True
                non_zero = sum(1 for b in dmx_data_copy if b > 0)
                logger.debug(f"DMX U{universe}: {len(dmx_data_copy)}ch, {non_zero} active from {addr[0]}")
            
            # Update local state
            self.dmx_universe_data[universe] = dmx_data_copy
        
        # Auto-forward ONLY if enabled and nodes configured
        if self.auto_forward_enabled and self.universe_mapping:
            try:
                self.send_dmx_with_mapping(universe, dmx_data_copy)
                logger.debug(f"Auto-forwarded Universe {universe} to {len(self.universe_mapping)} nodes")
            except Exception as e:
                logger.error(f"Error auto-forwarding DMX: {e}")
        
        # Call callback (ONLY when data changed)
        if self.dmx_received_callback:
            try:
                self.dmx_received_callback(universe, dmx_data_copy, addr[0])
            except Exception as e:
                logger.error(f"Error in DMX callback: {e}")
        else:
            # Only log this warning once
            if not hasattr(self, '_dmx_callback_warning_logged'):
                logger.warning("No DMX callback registered - DMX data will not reach GUI")
                self._dmx_callback_warning_logged = True
    
    def _handle_poll_reply(self, payload: bytes, addr: tuple):
        """
        Xử lý Poll Reply packet
        Parse theo Art-Net specification để lấy đúng thông tin về ports
        
        ArtPollReply structure (simplified):
        Byte 0-5: IP Address
        Byte 6-7: Port (always 0x1936)
        Byte 8-9: VersInfo (firmware version)
        Byte 10-11: NetSwitch, SubSwitch
        Byte 12-13: Oem
        Byte 14: UbeaVersion
        Byte 15: Status1
        Byte 16-17: EstaMan
        Byte 18-35: ShortName (18 bytes, null terminated)
        Byte 36-99: LongName (64 bytes, null terminated)
        Byte 100-163: NodeReport (64 bytes)
        Byte 164-165: NumPorts (Hi/Lo) - SỐ PORTS Ở ÂY!
        Byte 166-169: PortTypes[4]
        Byte 170-173: GoodInput[4]
        Byte 174-177: GoodOutput[4]
        Byte 178-181: SwIn[4]
        Byte 182-185: SwOut[4]
        ...
        """
        ip_address = addr[0]
        
        # V2.0: Ignore poll replies from ourselves
        try:
            import socket as sock
            s = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            if ip_address == local_ip or ip_address == "127.0.0.1":
                logger.debug(f"Ignoring poll reply from self: {ip_address}")
                return
        except:
            pass  # Continue if can't determine local IP
        
        try:
            # Minimum payload size check
            if len(payload) < 200:
                logger.warning(f"ArtPollReply from {ip_address} too short: {len(payload)} bytes")
                return
            
            # Parse ShortName (byte 18-35, 18 bytes, null-terminated)
            short_name_bytes = payload[18:36]
            try:
                short_name = short_name_bytes.split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
            except:
                short_name = f"Node_{ip_address.split('.')[-1]}"
            
            if not short_name:
                short_name = f"Node_{ip_address.split('.')[-1]}"
            
            # Parse LongName (byte 36-99, 64 bytes, null-terminated)
            long_name_bytes = payload[36:100]
            try:
                long_name = long_name_bytes.split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
            except:
                long_name = f"Art-Net Node at {ip_address}"
            
            if not long_name:
                long_name = f"Art-Net Node at {ip_address}"
            
            # Parse NumPorts (byte 164-165, High byte + Low byte)
            # CRITICAL FIX V2.2: Art-Net spec says Hi byte FIRST (at byte 164)
            # Byte 164: NumPortsHi (MSB) 
            # Byte 165: NumPortsLo (LSB)
            # Fix: 65280 (0xFF00) was caused by reading bytes in wrong order
            # Example: Device sends [0x00, 0x08] → should be 8, not 2048
            num_ports_hi = payload[164] if len(payload) > 164 else 0
            num_ports_lo = payload[165] if len(payload) > 165 else 1
            port_count = (num_ports_hi << 8) | num_ports_lo
            
            # Debug: Log raw bytes
            if len(payload) > 165:
                logger.debug(f"NumPorts raw bytes: Hi=0x{num_ports_hi:02X}, Lo=0x{num_ports_lo:02X}, Result={port_count}")
            
            # V2.0: Hỗ trợ unlimited ports - không giới hạn
            # Validate port count (chỉ check hợp lệ, không cap)
            if port_count == 0:
                logger.warning(f"Node {ip_address} reported 0 ports, defaulting to 1")
                port_count = 1
            
            # Parse SubSwitch (byte 11) for universe
            sub_switch = payload[11] if len(payload) > 11 else 0
            
            # Parse NetSwitch (byte 10) for network
            net_switch = payload[10] if len(payload) > 10 else 0
            
            # Calculate base universe (simplified)
            universe = (net_switch << 8) | sub_switch
            
            # Parse Status1 (byte 15) for node type
            status1 = payload[15] if len(payload) > 15 else 0
            
            # Create node info with parsed data
            node = ArtNetNode(
                ip_address=ip_address,
                short_name=short_name,
                long_name=long_name,
                universe=universe,
                port_count=port_count,
                node_type=status1,
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
            
            logger.info(f"Discovered Art-Net node: {ip_address} - {short_name} - {port_count} ports")
            logger.debug(f"  Long Name: {long_name}")
            logger.debug(f"  Universe: {universe}, Status: {status1:02x}")
            
        except Exception as e:
            logger.error(f"Error parsing ArtPollReply from {ip_address}: {e}")
            # Fallback to basic node info
            node = ArtNetNode(
                ip_address=ip_address,
                short_name=f"Node_{ip_address.split('.')[-1]}",
                long_name=f"Art-Net Node at {ip_address}",
                universe=0,
                port_count=1,
                last_seen=time.time()
            )
            with self.nodes_lock:
                self.discovered_nodes[ip_address] = node


    def _handle_poll(self, payload: bytes, addr: tuple):
        """
        Xử lý Art-Net Poll - Respond với thông tin node
        V2.0: Cho phép các thiết bị khác scan được DMX Master
        V2.1: Gửi nhiều PollReply packets để hỗ trợ unlimited universes
        V2.2: CHỈ gửi Reply khi nhận được Poll request hợp lệ (FIX: không tự gửi)
        
        Cơ chế tương thích với Depence/Resolume/MADRIX:
        - Mỗi PollReply quảng bá 4 universes liên tục qua SwIn
        - Universe 0-15: SubNet=0, SwIn thay đổi [0-3], [4-7], [8-11], [12-15]
        - Universe 16-31: SubNet=1, SwIn thay đổi [0-3], [4-7], [8-11], [12-15]
        - Công thức: Universe = (SubNet << 4) | SwIn
        
        Ví dụ:
        - 8 universes → 2 PollReply: S0/SwIn[0-3], S0/SwIn[4-7]
        - 16 universes → 4 PollReply: S0/SwIn[0-3,4-7,8-11,12-15]
        - 32 universes → 8 PollReply: S0(4 replies) + S1(4 replies)
        
        CRITICAL: Function này CHỈ được gọi khi nhận ArtPoll OpCode 0x2000
        """
        # Validate payload là ArtPoll hợp lệ (ít nhất 2 bytes: flags + priority)
        if len(payload) < 2:
            logger.warning(f"Invalid ArtPoll packet from {addr[0]}: payload too short ({len(payload)} bytes)")
            return
        
        logger.debug(f"Received valid Art-Net Poll from {addr[0]}, responding...")
        
        try:
            # Đọc max_universes từ config
            try:
                from system.config_manager import get_config_manager
                max_universes = int(get_config_manager().get('universes.max_universes', 32))
            except Exception:
                max_universes = 32
            
            # Tính số PollReply cần gửi (mỗi reply = 4 universes)
            num_replies = (max_universes + 3) // 4  # Round up division
            num_replies = min(num_replies, 64)  # Max 64 replies = 256 universes
            
            logger.debug(f"Sending {num_replies} PollReply packets for {max_universes} universes")
            
            # Gửi PollReply cho mỗi block 4 universes
            for i in range(num_replies):
                # Tính subnet và SwIn
                subnet = i // 4  # Mỗi subnet có 4 replies (16 universes)
                base_universe = i * 4  # Universe bắt đầu của reply này
                sw_in = [(base_universe + j) % 16 for j in range(4)]  # SwIn trong subnet
                
                # Tạo và gửi PollReply
                reply = self._create_poll_reply(subnet=subnet, sw_in=sw_in)
                self.socket.sendto(reply, addr)
                
                # Calculate actual universe range
                start_uni = base_universe
                end_uni = min(start_uni + 3, max_universes - 1)
                
                logger.debug(f"Sent PollReply #{i+1}/{num_replies}: SubNet={subnet} SwIn={sw_in} → Universe {start_uni}-{end_uni} to {addr[0]}")
            
        except Exception as e:
            logger.error(f"Error sending PollReply: {e}")
    
    def _create_poll_reply(self, subnet: int = 0, sw_in: list = None) -> bytes:
        """
        Tạo ArtPollReply packet theo Art-Net specification
        V2.1: Thêm subnet + sw_in parameters để hỗ trợ unlimited universes
        
        Args:
            subnet: SubNet number (0-15), mỗi subnet = 16 universes
            sw_in: List of 4 universe addresses [0-15] trong subnet này
                   Ví dụ: [0,1,2,3] hoặc [4,5,6,7] hoặc [8,9,10,11]
        
        Returns:
            bytes: ArtPollReply packet (239 bytes)
        """
        if sw_in is None:
            sw_in = [0, 1, 2, 3]  # Default: universe 0-3
        
        # Art-Net header
        packet = bytearray(b"Art-Net\x00")
        
        # OpCode: 0x2100 (ArtPollReply) - Little Endian
        packet.extend(struct.pack('<H', ArtNetPacket.ARTNET_POLL_REPLY))
        
        # IP Address (4 bytes) - lấy IP của interface
        try:
            # Lấy IP hiện tại của máy
            import socket as sock
            s = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_addr = s.getsockname()[0]
            s.close()
            ip_bytes = [int(x) for x in ip_addr.split('.')]
        except:
            ip_bytes = [127, 0, 0, 1]  # Fallback localhost
        
        packet.extend(bytes(ip_bytes))
        
        # Port (2 bytes) - 0x1936 (Little Endian)
        packet.extend(struct.pack('<H', self.port))
        
        # VersInfo (2 bytes) - Firmware version (e.g., 2.0 → 0x0200)
        packet.extend(struct.pack('>H', 0x0200))  # v2.0
        
        # NetSwitch (1 byte) - Network address (default 0)
        packet.append(0)
        
        # SubSwitch (1 byte) - Subnet address (0-15) - CRITICAL FOR MULTI-SUBNET
        packet.append(subnet & 0x0F)  # Chỉ lấy 4 bits thấp
        
        # Oem (2 bytes) - OEM code (Big Endian) - 0xFFFF = custom
        packet.extend(struct.pack('>H', 0xFFFF))
        
        # UbeaVersion (1 byte) - UBEA version (default 0)
        packet.append(0)
        
        # Status1 (1 byte) - Node status
        # Bit 0-1: Indicator state (0=Unknown, 1=Locate, 2=Mute, 3=Normal)
        # Bit 2-3: Port-Address Programming Authority (0=Unknown, 1=Front Panel)
        # Bit 4: Boot from ROM
        # Bit 5: RDM capable
        # Bit 6-7: UBEA Present
        status1 = 0b00000000  # Normal state
        packet.append(status1)
        
        # EstaMan (2 bytes) - ESTA Manufacturer code (Little Endian) - 0xFFFF = not registered
        packet.extend(struct.pack('<H', 0xFFFF))
        
        # ShortName (18 bytes) - Null-terminated string - Thêm universe range
        # Tính universe range từ subnet và sw_in
        start_uni = (subnet << 4) | sw_in[0]
        end_uni = (subnet << 4) | sw_in[3]
        if start_uni == 0 and end_uni == 3:
            short_name = "DMX Master"  # Đẹp hơn cho universe đầu tiên
        else:
            short_name = f"DMX U{start_uni}-{end_uni}"
        short_name_bytes = short_name.encode('utf-8')[:17]  # Max 17 chars + null
        packet.extend(short_name_bytes)
        packet.extend(b'\x00' * (18 - len(short_name_bytes)))  # Pad với null
        
        # LongName (64 bytes) - Null-terminated string - Thêm full info
        long_name = f"DMX Master LTS - Universe {start_uni}-{end_uni}"
        long_name_bytes = long_name.encode('utf-8')[:63]  # Max 63 chars + null
        packet.extend(long_name_bytes)
        packet.extend(b'\x00' * (64 - len(long_name_bytes)))  # Pad với null
        
        # NodeReport (64 bytes) - Status message - Thêm universe info
        node_report = f"#0001 [0000] Ready - U{start_uni}-{end_uni}"
        node_report_bytes = node_report.encode('utf-8')[:63]
        packet.extend(node_report_bytes)
        packet.extend(b'\x00' * (64 - len(node_report_bytes)))
        
        # NumPorts (2 bytes) - Hi/Lo byte  
        # CRITICAL V2.2: Art-Net specification says Hi byte FIRST
        # Byte 164: NumPortsHi (MSB)
        # Byte 165: NumPortsLo (LSB)
        # Always advertise 4 ports (legacy Art-Net limit for arrays)
        # Each reply advertises 4 consecutive universes via SwIn
        num_ports = 4  # Fixed at 4 (legacy arrays are 4-long)
        packet.append(num_ports >> 8)  # Hi byte (MSB) first
        packet.append(num_ports & 0xFF)  # Lo byte (LSB) second
        
        # PortTypes (4 bytes) - Type of each port
        # 0x40 = Input to Art-Net (node receives DMX via Art-Net)
        # All 4 ports are Input-capable
        for i in range(4):
            packet.append(0x40)  # All ports are Input
        
        # GoodInput (4 bytes) - Input status of ports
        # Bit3 (0x08) = Input enabled/power on
        # All 4 ports active
        good_input = 0x08
        for i in range(4):
            packet.append(good_input)
        
        # GoodOutput (4 bytes) - Output status (not used for input node but included)
        # All zeros since we're an input node
        for _ in range(4):
            packet.append(0x00)
        
        # SwIn (4 bytes) - Input universe low-byte (0-15 trong subnet)
        # CRITICAL: Sử dụng sw_in parameter thay vì hardcode [0,1,2,3]
        # Ví dụ: sw_in=[4,5,6,7] cho universe 4-7 trong subnet 0
        for i in range(4):
            packet.append(sw_in[i] & 0x0F)  # Chỉ lấy 4 bits thấp
        
        # SwOut (4 bytes) - Output universe (not used for input-only node)
        for i in range(4):
            packet.append(0x00)
        
        # SwVideo (1 byte) - deprecated
        packet.append(0)
        
        # SwMacro (1 byte) - Macro key inputs
        packet.append(0)
        
        # SwRemote (1 byte) - Remote trigger inputs
        packet.append(0)
        
        # Spare (3 bytes)
        packet.extend(b'\x00' * 3)
        
        # Style (1 byte) - 0=StNode (input/output device)
        packet.append(0)  # StNode
        
        # MAC Address (6 bytes)
        packet.extend(b'\x00' * 6)
        
        # BindIp (4 bytes) - IP address of root device
        packet.extend(bytes(ip_bytes))
        
        # BindIndex (1 byte) - Network interface index
        packet.append(1)
        
        # Status2 (1 byte) - Additional status
        # Bit 0: Web browser config supported
        # Bit 1: DHCP capable
        # Bit 2: DHCP used
        # Bit 3: Port 15-bit
        # Bit 4-7: Reserved
        status2 = 0b00000111  # Web + DHCP capable + used
        packet.append(status2)
        
        # Filler (26 bytes) - Reserved for future use
        packet.extend(b'\x00' * 26)
        
        logger.debug(f"Created ArtPollReply: {len(packet)} bytes")
        return bytes(packet)

    
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