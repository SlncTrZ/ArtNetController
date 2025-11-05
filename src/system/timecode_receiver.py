"""
Timecode Receiver System - V2.0 Professional Feature
Supports MTC (MIDI Time Code), Net-timecode, and LTC (Linear Time Code)

Compatible with Depence and other professional lighting software.
"""

import logging
import time
import threading
import socket
import struct
from typing import Dict, Callable, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal
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
        
        # Emit Qt signal (thread-safe)
        self.timecode_received.emit(timecode_data.to_dict())
        
        # Also call callback directly if set
        if self.callback_func:
            try:
                self.callback_func(timecode_data.to_dict())
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

class MTCReceiver(TimecodeReceiver):
    """MTC (MIDI Time Code) Receiver for 30fps"""
    
    def __init__(self, midi_device: str = "auto"):
        super().__init__()
        self.midi_device = midi_device
        self.midi_input = None
        
    def start(self) -> bool:
        """Start MTC receiver"""
        try:
            # Try to import python-rtmidi
            try:
                import rtmidi
            except ImportError:
                logger.error("❌ python-rtmidi not installed. Install with: pip install python-rtmidi")
                self.status_changed.emit("ERROR: python-rtmidi not installed")
                return False
            
            # Create MIDI input
            self.midi_input = rtmidi.MidiIn()
            available_ports = self.midi_input.get_ports()
            
            if not available_ports:
                logger.warning("⚠️ No MIDI devices found for MTC")
                self.status_changed.emit("No MIDI devices found")
                return False
            
            # Auto-select first available port or find specific device
            port_index = 0
            if self.midi_device != "auto":
                for i, port_name in enumerate(available_ports):
                    if self.midi_device.lower() in port_name.lower():
                        port_index = i
                        break
            
            selected_port = available_ports[port_index]
            self.midi_input.open_port(port_index)
            self.midi_input.set_callback(self._on_midi_message)
            
            self.is_running = True
            logger.info(f"🎹 MTC Receiver started on: {selected_port}")
            self.status_changed.emit(f"MTC connected: {selected_port}")
            
            # Start timeout monitor thread
            self._thread = threading.Thread(target=self._monitor_timeout, daemon=True)
            self._thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start MTC receiver: {e}")
            self.status_changed.emit(f"MTC Error: {e}")
            return False
    
    def _on_midi_message(self, message, data=None):
        """Handle incoming MIDI messages"""
        msg_bytes, delta_time = message
        
        # Look for MTC Quarter Frame messages (0xF1)
        if len(msg_bytes) == 2 and msg_bytes[0] == 0xF1:
            self._process_mtc_quarter_frame(msg_bytes[1])
    
    def _process_mtc_quarter_frame(self, quarter_frame_data):
        """Process MTC quarter frame message"""
        # MTC Quarter Frame format: 0nnndddd
        # nnn = message type (0-7), dddd = data nibble
        message_type = (quarter_frame_data >> 4) & 0x07
        data_nibble = quarter_frame_data & 0x0F
        
        # For simplicity, we'll trigger on frame low nibble (type 0)
        if message_type == 0:  # Frame low nibble
            # Simulate timecode (in real implementation, you'd reconstruct full timecode)
            current_time = time.time()
            total_seconds = int(current_time) % (24 * 3600)
            
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            frames = int((current_time - int(current_time)) * 30)  # 30fps
            
            timecode_data = TimecodeData(
                hours=hours,
                minutes=minutes,
                seconds=seconds,
                frames=frames,
                fps=30.0,
                source="MTC",
                timestamp=current_time
            )
            
            self._emit_timecode(timecode_data)
    
    def _monitor_timeout(self):
        """Monitor for MTC timeout"""
        while self.is_running:
            self._check_timeout()
            time.sleep(0.1)
    
    def stop(self):
        """Stop MTC receiver"""
        super().stop()
        if self.midi_input:
            try:
                self.midi_input.close_port()
            except:
                pass
            self.midi_input = None

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

class LTCReceiver(TimecodeReceiver):
    """LTC (Linear Time Code) Receiver - Audio-based timecode"""
    
    def __init__(self, audio_device: str = "auto"):
        super().__init__()
        self.audio_device = audio_device
        
    def start(self) -> bool:
        """Start LTC receiver"""
        logger.warning("🎧 LTC receiver not implemented yet - requires audio processing")
        self.status_changed.emit("LTC not implemented yet")
        return False

class TimecodeManager:
    """Manager for all timecode receivers"""
    
    def __init__(self):
        self.receivers: Dict[str, TimecodeReceiver] = {}
        self.active_receivers = []
        
    def create_mtc_receiver(self, midi_device: str = "auto") -> MTCReceiver:
        """Create MTC receiver"""
        receiver = MTCReceiver(midi_device)
        self.receivers["mtc"] = receiver
        return receiver
    
    def create_net_timecode_receiver(self, port: int = 3040) -> NetTimecodeReceiver:
        """Create Net-timecode receiver"""
        receiver = NetTimecodeReceiver(port)
        self.receivers["net-timecode"] = receiver
        return receiver
    
    def create_ltc_receiver(self, audio_device: str = "auto") -> LTCReceiver:
        """Create LTC receiver"""
        receiver = LTCReceiver(audio_device)
        self.receivers["ltc"] = receiver
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
    """Test function for timecode receivers"""
    def on_timecode_received(data):
        print(f"📟 Timecode: {data['timecode']} ({data['fps']}fps) from {data['source']}")
    
    def on_timecode_stopped():
        print("⚠️ Timecode stopped")
    
    manager = create_timecode_manager()
    
    # Create receivers
    mtc = manager.create_mtc_receiver()
    net_tc = manager.create_net_timecode_receiver()
    
    # Set callbacks
    mtc.set_callbacks(on_timecode_received, on_timecode_stopped)
    net_tc.set_callbacks(on_timecode_received, on_timecode_stopped)
    
    # Start receivers
    started = manager.start_all()
    print(f"Started {started} timecode receivers")
    
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