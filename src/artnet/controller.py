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
            
        # Art-Net DMX packet format:
        # Byte 0: Sequence
        # Byte 1: Physical
        # Byte 2-3: Universe (Little Endian)
        # Byte 4-5: Length (Big Endian) - số bytes DMX data
        sequence = payload[0]
        physical = payload[1]
        universe = struct.unpack('<H', payload[2:4])[0]
        length = struct.unpack('>H', payload[4:6])[0]  # Big Endian!
        dmx_data = payload[6:6+length]
        
        # Debug: Log raw bytes
        logger.debug(f"Universe bytes: {payload[2]:02x} {payload[3]:02x} -> {universe}")
        
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
        
        # Auto-forward control
        self.auto_forward_enabled = False  # Checkbox control
        
        # V2.0: Output pause control (for recording safety)
        self.output_paused = False

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
            
            # Send initial poll
            self.poll_network()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Art-Net controller: {e}")
            return False
    
    def pause_output(self):
        """Pause DMX output (V2.0 - for recording safety)"""
        self.output_paused = True
        logger.info("⏸️  Art-Net output PAUSED")

    def resume_output(self):
        """Resume DMX output (V2.0)"""
        self.output_paused = False
        logger.info("▶️  Art-Net output RESUMED")

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
                logger.info(f"RX from {addr[0]}:{addr[1]}, size: {len(data)} bytes")
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
            logger.warning(f"❌ Failed to unpack packet from {addr[0]}")
            return
        
        opcode = packet['opcode']
        payload = packet['payload']
        
        # DEBUG: Log packet types
        if opcode == ArtNetPacket.ARTNET_DMX:
            logger.info(f"📦 DMX packet received from {addr[0]}")
            self._handle_dmx_packet(payload, addr)
        elif opcode == ArtNetPacket.ARTNET_POLL_REPLY:
            logger.info(f"📦 Poll Reply packet received from {addr[0]}")
            self._handle_poll_reply(payload, addr)
        elif opcode == ArtNetPacket.ARTNET_POLL:
            logger.info(f"📦 Poll packet received from {addr[0]}")
            self._handle_poll(payload, addr)
        else:
            logger.info(f"📦 Unknown packet type 0x{opcode:04X} from {addr[0]}")
    
    def _handle_dmx_packet(self, payload: bytes, addr: tuple):
        """Xử lý DMX packet"""
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
        
        # REDUCED LOGGING: Only log every 10th packet to prevent spam
        self._dmx_packet_count = getattr(self, '_dmx_packet_count', 0) + 1
        if self._dmx_packet_count % 10 == 0:
            logger.info(f"Received DMX data: Universe {universe}, {len(dmx_data)} channels from {addr[0]} (packet #{self._dmx_packet_count})")
        
        # Update local state (LUÔN LUÔN update để DMX View hiển thị)
        with self.dmx_lock:
            self.dmx_universe_data[universe] = dmx_data
        
        # Auto-forward ONLY if enabled and nodes configured
        if self.auto_forward_enabled and self.universe_mapping:
            try:
                self.send_dmx_with_mapping(universe, dmx_data)
                logger.debug(f"Auto-forwarded Universe {universe} to {len(self.universe_mapping)} nodes")
            except Exception as e:
                logger.error(f"Error auto-forwarding DMX: {e}")
        
        # Call callback (LUÔN LUÔN gọi để DMX View update)
        if self.dmx_received_callback:
            try:
                logger.info(f"🔄 Calling DMX callback for Universe {universe}, {len(dmx_data)} channels")
                self.dmx_received_callback(universe, dmx_data, addr[0])
                logger.info(f"✅ DMX callback completed successfully")
            except Exception as e:
                logger.error(f"❌ Error in DMX callback: {e}")
        else:
            logger.warning("⚠️ No DMX callback registered - DMX data will not reach GUI!")
    
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
            # Byte 164: NumPortsHi (usually 0)
            # Byte 165: NumPortsLo (actual port count)
            num_ports_hi = payload[164] if len(payload) > 164 else 0
            num_ports_lo = payload[165] if len(payload) > 165 else 1
            port_count = (num_ports_hi << 8) | num_ports_lo
            
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
        """
        logger.debug(f"Received Art-Net Poll from {addr[0]}")
        
        try:
            # Tạo ArtPollReply packet
            reply = self._create_poll_reply()
            
            # Gửi reply về cho requester
            self.socket.sendto(reply, addr)
            logger.info(f"Sent ArtPollReply to {addr[0]}")
            
        except Exception as e:
            logger.error(f"Error sending PollReply: {e}")
    
    def _create_poll_reply(self) -> bytes:
        """
        Tạo ArtPollReply packet theo Art-Net specification
        
        Returns:
            bytes: ArtPollReply packet
        """
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
        
        # SubSwitch (1 byte) - Subnet address (default 0)
        packet.append(0)
        
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
        
        # ShortName (18 bytes) - Null-terminated string
        short_name = "DMX Master"
        short_name_bytes = short_name.encode('utf-8')[:17]  # Max 17 chars + null
        packet.extend(short_name_bytes)
        packet.extend(b'\x00' * (18 - len(short_name_bytes)))  # Pad với null
        
        # LongName (64 bytes) - Null-terminated string
        long_name = "DMX Master Unlimited by TCD"
        long_name_bytes = long_name.encode('utf-8')[:63]  # Max 63 chars + null
        packet.extend(long_name_bytes)
        packet.extend(b'\x00' * (64 - len(long_name_bytes)))  # Pad với null
        
        # NodeReport (64 bytes) - Status message
        node_report = "#0001 [0000] Power On"
        node_report_bytes = node_report.encode('utf-8')[:63]
        packet.extend(node_report_bytes)
        packet.extend(b'\x00' * (64 - len(node_report_bytes)))
        
        # NumPorts (2 bytes) - Hi/Lo byte
        # V2.0: Advertise 16 ports (có thể mở rộng lên 512 nếu cần)
        num_ports = 16
        packet.append(num_ports >> 8)  # Hi byte
        packet.append(num_ports & 0xFF)  # Lo byte
        
        # PortTypes (4 bytes) - Type of each port
        # 0x80 = Output from Art-Net, can output DMX
        for _ in range(4):
            packet.append(0x80)
        
        # GoodInput (4 bytes) - Input status of ports (all zeros = not used)
        packet.extend(b'\x00' * 4)
        
        # GoodOutput (4 bytes) - Output status
        # Bit 7: Data transmitted
        # Bit 6: Includes test packets
        # Bit 5: Includes SIP packets
        # Bit 4: Includes text packets
        # Bit 3: Output power on
        # Bit 2: Merging ArtNet data
        for _ in range(4):
            packet.append(0b10001000)  # Data transmitted, output on
        
        # SwIn (4 bytes) - Input universe
        packet.extend(b'\x00' * 4)
        
        # SwOut (4 bytes) - Output universe (0-3)
        for i in range(4):
            packet.append(i)
        
        # SwVideo (1 byte) - deprecated
        packet.append(0)
        
        # SwMacro (1 byte) - Macro key inputs
        packet.append(0)
        
        # SwRemote (1 byte) - Remote trigger inputs
        packet.append(0)
        
        # Spare (3 bytes)
        packet.extend(b'\x00' * 3)
        
        # Style (1 byte) - 0=StNode, 1=StController, 2=StMedia, 3=StRoute, 4=StBackup
        packet.append(1)  # Controller
        
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