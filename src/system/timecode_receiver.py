"""
Timecode Receiver System - V2.0 Professional Feature
Supports Net-Timecode and Art-Net 4 Timecode

Compatible with Depence and other professional lighting software.
"""

import logging
import time
import threading
import socket
import struct
from typing import Dict, Callable, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal, QCoreApplication
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TimecodeData:
    """Timecode data structure"""
    hours: int
    minutes: int
    seconds: int
    frames: int
    fps: float
    source: str
    timestamp: float
    
    def to_string(self) -> str:
        """Convert to timecode string HH:MM:SS:FF"""
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}:{self.frames:02d}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for callbacks"""
        return {
            'timecode': self.to_string(),
            'hours': self.hours,
            'minutes': self.minutes, 
            'seconds': self.seconds,
            'frames': self.frames,
            'fps': self.fps,
            'source': self.source,
            'timestamp': self.timestamp
        }

class TimecodeReceiver(QObject):
    """Base class for all timecode receivers"""
    
    # Qt Signals for thread-safe communication
    timecode_received = pyqtSignal(dict)  # TimecodeData as dict
    timecode_stopped = pyqtSignal()
    status_changed = pyqtSignal(str)  # Status message
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.callback_func = None
        self.stop_callback_func = None
        self._thread = None
        self.last_timecode_time = 0
        self.timeout_threshold = 2.0  # Seconds before considering timecode stopped
        
    def set_callbacks(self, on_timecode: Callable, on_stopped: Callable = None):
        """Set callback functions for timecode events"""
        self.callback_func = on_timecode
        self.stop_callback_func = on_stopped
        
        # Also connect Qt signals
        self.timecode_received.connect(on_timecode)
        if on_stopped:
            self.timecode_stopped.connect(on_stopped)
    
    def start(self) -> bool:
        """Start timecode receiver (override in subclasses)"""
        raise NotImplementedError
        
    def stop(self):
        """Stop timecode receiver"""
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info(f"Stopped {self.__class__.__name__}")
    
    def _emit_timecode(self, timecode_data: TimecodeData):
        """Emit timecode signal safely"""
        self.last_timecode_time = time.time()
        payload = timecode_data.to_dict()

        # Emit Qt signal (thread-safe) - GUI consumers should use this
        try:
            self.timecode_received.emit(payload)
        except Exception as e:
            logger.error(f"Error emitting timecode signal: {e}")

        # If a direct callback is set and there is NO Qt application instance
        # (i.e., running as a non-GUI test script), call the callback directly.
        # This avoids calling GUI callbacks from a non-main thread which can
        # crash the application.
        try:
            if self.callback_func and QCoreApplication.instance() is None:
                self.callback_func(payload)
        except Exception as e:
            logger.error(f"Error in timecode callback: {e}")
    
    def _check_timeout(self):
        """Check if timecode has timed out"""
        if self.last_timecode_time > 0:
            if time.time() - self.last_timecode_time > self.timeout_threshold:
                self.timecode_stopped.emit()
                if self.stop_callback_func:
                    try:
                        self.stop_callback_func()
                    except Exception as e:
                        logger.error(f"Error in stop callback: {e}")
                self.last_timecode_time = 0

class NetTimecodeReceiver(TimecodeReceiver):
    """Net-timecode Receiver for 25fps (Depence compatible)"""
    
    def __init__(self, port: int = 3040, host: str = "0.0.0.0"):
        super().__init__()
        self.port = port
        self.host = host
        self.socket = None
        
    def start(self) -> bool:
        """Start Net-timecode receiver"""
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.settimeout(1.0)  # 1 second timeout
            
            # Bind to port
            self.socket.bind((self.host, self.port))
            
            self.is_running = True
            logger.info(f"🌐 Net-timecode receiver started on {self.host}:{self.port}")
            self.status_changed.emit(f"Net-timecode listening on port {self.port}")
            
            # Start receiver thread
            self._thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Net-timecode receiver: {e}")
            self.status_changed.emit(f"Net-timecode Error: {e}")
            return False
    
    def _receive_loop(self):
        """Main receive loop for Net-timecode"""
        while self.is_running:
            try:
                # Receive data
                data, addr = self.socket.recvfrom(1024)
                
                if len(data) >= 8:  # Minimum Net-timecode packet size
                    self._process_net_timecode_packet(data, addr)
                    
            except socket.timeout:
                # Check for timeout
                self._check_timeout()
                continue
            except Exception as e:
                if self.is_running:  # Only log if not shutting down
                    logger.error(f"Net-timecode receive error: {e}")
                break
    
    def _process_net_timecode_packet(self, data: bytes, addr: tuple):
        """Process Net-timecode packet"""
        try:
            # Net-timecode format (simplified):
            # First 8 bytes: hours, minutes, seconds, frames, fps, etc.
            if len(data) >= 4:
                # Simple parsing - adjust based on actual Net-timecode protocol
                hours = data[0] if len(data) > 0 else 0
                minutes = data[1] if len(data) > 1 else 0
                seconds = data[2] if len(data) > 2 else 0
                frames = data[3] if len(data) > 3 else 0
                
                # Validate values
                if hours < 24 and minutes < 60 and seconds < 60 and frames < 25:
                    timecode_data = TimecodeData(
                        hours=hours,
                        minutes=minutes,
                        seconds=seconds,
                        frames=frames,
                        fps=25.0,  # Net-timecode typically 25fps
                        source=f"Net-timecode ({addr[0]})",
                        timestamp=time.time()
                    )
                    
                    self._emit_timecode(timecode_data)
                
        except Exception as e:
            logger.error(f"Error processing Net-timecode packet: {e}")
    
    def stop(self):
        """Stop Net-timecode receiver"""
        super().stop()
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

class ArtNet4TimecodeReceiver(TimecodeReceiver):
    """Art-Net 4 Timecode Receiver - For Depence and other professional software"""
    
    def __init__(self, port: int = 6454, artnet_controller=None):
        super().__init__()
        self.port = port
        self.socket = None
        self.receive_thread = None
        self.artnet_controller = artnet_controller  # Share socket with main controller
        self.use_shared_socket = artnet_controller is not None
        
    def start(self) -> bool:
        """Start Art-Net 4 Timecode receiver"""
        try:
            if self.use_shared_socket and self.artnet_controller:
                # Use shared socket approach - register callback with main Art-Net controller
                logger.debug("Using shared Art-Net socket for timecode reception")
                if hasattr(self.artnet_controller, 'register_timecode_callback'):
                    self.artnet_controller.register_timecode_callback(self._handle_shared_packet)
                    self.is_running = True
                    logger.info("Art-Net 4 Timecode receiver started (shared socket)")
                    self.status_changed.emit("Art-Net 4 Timecode using shared socket")
                    return True
                else:
                    logger.warning("Main Art-Net controller doesn't support timecode callbacks")
                    # Fall back to separate socket
                    self.use_shared_socket = False
            
            if not self.use_shared_socket:
                # Create separate UDP socket for Art-Net (different port)
                timecode_port = self.port + 1  # Use 6455 to avoid conflict
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                
                # Try to bind to alternative port if main port is taken
                try:
                    self.socket.bind(('0.0.0.0', timecode_port))
                    logger.info(f"Art-Net 4 Timecode receiver started on port {timecode_port}")
                except OSError:
                    # Try multicast approach for receiving Art-Net
                    self.socket.bind(('', timecode_port + 1))
                    logger.info(f"Art-Net 4 Timecode receiver started on port {timecode_port + 1}")
                
                # Start receive thread
                self.is_running = True
                self.receive_thread = threading.Thread(target=self._receive_artnet_packets, daemon=True)
                self.receive_thread.start()
                
                self.status_changed.emit(f"Art-Net 4 Timecode listening on port {timecode_port}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Art-Net 4 Timecode receiver: {e}")
            logger.error("💡 Suggestion: Check if another Art-Net application is running")
            self.status_changed.emit(f"Error: {str(e)}")
            return False
    
    def _handle_shared_packet(self, data: bytes, addr: tuple):
        """Handle packet from shared Art-Net controller"""
        self._process_artnet_packet(data, addr)
    
    def _receive_artnet_packets(self):
        """Receive and process Art-Net packets"""
        while self.is_running:
            try:
                data, addr = self.socket.recvfrom(1024)
                self._process_artnet_packet(data, addr)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_running:
                    logger.error(f"Art-Net receive error: {e}")
                break
    
    def _process_artnet_packet(self, data: bytes, addr: tuple):
        """Process Art-Net packet for timecode"""
        try:
            # Art-Net packet starts with "Art-Net\0"
            if len(data) < 12 or data[:8] != b'Art-Net\0':
                return
            
            # Get OpCode (little endian)
            opcode = struct.unpack('<H', data[8:10])[0]
            
            # Art-Net 4 Timecode OpCode is 0x9700
            if opcode == 0x9700:  # ArtTimeCode
                self._process_timecode_packet(data, addr)
                
        except Exception as e:
            logger.error(f"Error processing Art-Net packet: {e}")
    
    def _process_timecode_packet(self, data: bytes, addr: tuple):
        """Process Art-Net 4 Timecode packet"""
        try:
            # Some devices (e.g. Depence) send a 19-byte timecode packet.
            # Accept >=19 bytes to be compatible with those implementations.
            if len(data) < 19:
                logger.debug(f"Art-Net TC packet too short ({len(data)} bytes) from {addr[0]}")
                return
            
            # Art-Net 4 Timecode packet structure:
            # 0-7: "Art-Net\0"
            # 8-9: OpCode (0x9700)
            # 10-11: Protocol version (0x0e00)
            # 12: Filler
            # 13: Filler  
            # 14: Frames
            # 15: Seconds
            # 16: Minutes
            # 17: Hours
            # 18: Type (frame rate)
            
            frames = data[14]
            seconds = data[15]
            minutes = data[16]
            hours = data[17]
            timecode_type = data[18]
            
            # Decode frame rate from type
            fps_map = {
                0: 24.0,    # 24fps
                1: 25.0,    # 25fps  
                2: 29.97,   # 29.97fps drop frame
                3: 30.0,    # 30fps
            }
            fps = fps_map.get(timecode_type, 25.0)
            
            # Validate timecode values
            if hours < 24 and minutes < 60 and seconds < 60 and frames < fps:
                timecode_data = TimecodeData(
                    hours=hours,
                    minutes=minutes,
                    seconds=seconds,
                    frames=frames,
                    fps=fps,
                    source=f"Art-Net 4 TC ({addr[0]})",
                    timestamp=time.time()
                )
                
                self._emit_timecode(timecode_data)
                # Changed to DEBUG to reduce log spam
                logger.debug(f"Art-Net 4 TC: {hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d} @ {fps}fps")
                
        except Exception as e:
            logger.error(f"Error processing Art-Net timecode: {e}")
    
    def stop(self):
        """Stop Art-Net 4 Timecode receiver"""
        super().stop()
        
        # Unregister callback from shared controller
        if self.use_shared_socket and self.artnet_controller:
            if hasattr(self.artnet_controller, 'unregister_timecode_callback'):
                self.artnet_controller.unregister_timecode_callback(self._handle_shared_packet)
                logger.debug("Timecode callback unregistered from Art-Net controller")
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

class TimecodeManager:
    """Manager for Net-Timecode and Art-Net 4 Timecode receivers"""
    
    def __init__(self):
        self.receivers: Dict[str, TimecodeReceiver] = {}
        self.active_receivers = []
    
    def create_net_timecode_receiver(self, port: int = 3040) -> NetTimecodeReceiver:
        """Create Net-timecode receiver"""
        receiver = NetTimecodeReceiver(port)
        self.receivers["net-timecode"] = receiver
        return receiver
    
    def create_artnet4_timecode_receiver(self, port: int = 6454, artnet_controller=None) -> ArtNet4TimecodeReceiver:
        """Create Art-Net 4 Timecode receiver for Depence compatibility"""
        receiver = ArtNet4TimecodeReceiver(port, artnet_controller)
        self.receivers["artnet4-timecode"] = receiver
        return receiver
    
    def start_all(self) -> int:
        """Start all receivers, return number started successfully"""
        started_count = 0
        for name, receiver in self.receivers.items():
            if receiver.start():
                self.active_receivers.append(name)
                started_count += 1
                logger.info(f"✅ Started {name} receiver")
            else:
                logger.warning(f"❌ Failed to start {name} receiver")
        
        return started_count
    
    def stop_all(self):
        """Stop all receivers"""
        for name, receiver in self.receivers.items():
            try:
                receiver.stop()
                logger.info(f"🛑 Stopped {name} receiver")
            except Exception as e:
                logger.error(f"Error stopping {name} receiver: {e}")
        
        self.active_receivers.clear()
    
    def get_active_receivers(self) -> list:
        """Get list of active receiver names"""
        return self.active_receivers.copy()

# Convenience functions for easy usage
def create_timecode_manager() -> TimecodeManager:
    """Create a new timecode manager"""
    return TimecodeManager()

def test_timecode_receivers():
    """Test function for Net-Timecode and Art-Net 4 Timecode receivers"""
    def on_timecode_received(data):
        print(f"📟 Timecode: {data['timecode']} ({data['fps']}fps) from {data['source']}")
    
    def on_timecode_stopped():
        print("⚠️ Timecode stopped")
    
    manager = create_timecode_manager()
    
    # Create receivers
    net_tc = manager.create_net_timecode_receiver()
    artnet_tc = manager.create_artnet4_timecode_receiver()
    
    # Set callbacks
    net_tc.set_callbacks(on_timecode_received, on_timecode_stopped)
    artnet_tc.set_callbacks(on_timecode_received, on_timecode_stopped)
    
    # Start receivers
    started = manager.start_all()
    print(f"Started {started} timecode receivers")
    print("Supported: Net-Timecode (UDP:3040) and Art-Net 4 Timecode (OpCode 0x9700)")

    
    try:
        print("Listening for timecode... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        manager.stop_all()

if __name__ == "__main__":
    # Test timecode receivers
    test_timecode_receivers()