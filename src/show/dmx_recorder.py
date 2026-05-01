"""
Binary DMX Recorder Module
Ghi và đọc DMX data dạng binary format (.dmxrec) để tối ưu dung lượng và tốc độ

Binary Format Structure:
========================
HEADER (Fixed size):
- Magic bytes: 'DMXR' (4 bytes)
- Version: uint8 (1 byte) - Currently version 2 (V2.0 with CRC + Monotonic Time)
- FPS: float32 (4 bytes) - Frames per second
- Universe count: uint16 (2 bytes) - Number of universes
- Frame count: uint32 (4 bytes) - Total number of frames
- Reserved: 16 bytes for future use
Total Header: 31 bytes

FRAME DATA (Variable size, repeated for each frame):
- Timestamp: float64 (8 bytes) - Time in seconds from start
- Universe: uint16 (2 bytes) - Universe number (0-65535)
- DMX Data: 512 bytes - Raw DMX channel values
Total per Frame: 522 bytes

Example:
- 10 minutes recording at 40 FPS, 1 universe = 10 * 60 * 40 * 522 = ~12.5 MB
- vs JSON format would be ~100+ MB

Topic: show
Last Updated: 2026-05-01
"""

import struct
import logging
import threading
import queue
import time
from pathlib import Path
from typing import List, Dict, BinaryIO, Optional, Tuple, Callable
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)

# Binary format constants
MAGIC_BYTES = b'DMXR'
FORMAT_VERSION = 2  # V2.0 with CRC and enhancements
DMX_CHANNELS = 512
HEADER_SIZE = 32
FRAME_SIZE = 524  # 8 (timestamp) + 2 (universe) + 512 (DMX) + 2 (CRC16)

# Feature flags
FLAG_HAS_CRC = 0x01
FLAG_MONOTONIC_TIME = 0x02

# Default settings
DEFAULT_BUFFER_SIZE = 100  # Frames to buffer for smooth playback
MAX_TIME_DRIFT_MS = 5  # Maximum acceptable drift before correction


def crc16_modbus(data: bytes) -> int:
    """
    Calculate CRC-16/MODBUS checksum
    Polynomial: 0x8005, Init: 0xFFFF, RefIn: True, RefOut: True, XorOut: 0x0000
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

class DMXFrame:
    """Represents a single DMX frame with CRC validation"""
    __slots__ = ['timestamp', 'universe', 'data', 'crc']
    
    def __init__(self, timestamp: float, universe: int, data: bytes, crc: Optional[int] = None):
        self.timestamp = timestamp
        self.universe = universe
        self.data = data[:DMX_CHANNELS]  # Ensure exactly 512 bytes
        self.crc = crc if crc is not None else self._calculate_crc()
    
    def _calculate_crc(self) -> int:
        """Calculate CRC for this frame"""
        # Pad data to 512 bytes for CRC calculation
        padded_data = self.data + b'\x00' * (DMX_CHANNELS - len(self.data))
        # CRC covers: timestamp + universe + data
        frame_data = struct.pack('>d H 512s', self.timestamp, self.universe, padded_data)
        return crc16_modbus(frame_data)
    
    def validate_crc(self) -> bool:
        """Validate frame CRC"""
        expected_crc = self._calculate_crc()
        return self.crc == expected_crc
    
    def to_bytes(self) -> bytes:
        """Convert frame to binary format with CRC"""
        # Pad data to 512 bytes if needed
        padded_data = self.data + b'\x00' * (DMX_CHANNELS - len(self.data))
        
        # Pack: timestamp (8) + universe (2) + data (512) + crc (2)
        return struct.pack('>d H 512s H', 
                          self.timestamp, 
                          self.universe, 
                          padded_data,
                          self.crc)
    
    @classmethod
    def from_bytes(cls, data: bytes, validate: bool = True) -> Optional['DMXFrame']:
        """Create frame from binary data with validation"""
        if len(data) < FRAME_SIZE:
            logger.error(f"Invalid frame data size: {len(data)} (expected {FRAME_SIZE})")
            return None
        
        try:
            timestamp, universe, dmx_data, crc = struct.unpack('>d H 512s H', data[:FRAME_SIZE])
            frame = cls(timestamp, universe, dmx_data, crc)
            
            # Validate CRC if requested
            if validate and not frame.validate_crc():
                logger.warning(f"CRC mismatch for frame at t={timestamp:.3f}s, u={universe}")
                return None
            
            return frame
            
        except struct.error as e:
            logger.error(f"Failed to unpack frame: {e}")
            return None
    
    def __repr__(self):
        active_channels = sum(1 for b in self.data if b > 0)
        crc_status = "✓" if self.validate_crc() else "✗"
        return f"DMXFrame(t={self.timestamp:.3f}s, u={self.universe}, active={active_channels}/512, crc={crc_status})"


class DMXRecorder:
    """
    Binary DMX Recorder with CRC validation and monotonic time
    Thread-safe for concurrent frame writes
    """
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file: Optional[BinaryIO] = None
        self.is_recording = False
        self.frame_count = 0
        self.fps = 40.0
        self.universes = set()
        
        # Monotonic time tracking
        self.start_time_mono = 0
        self.start_time_wall = 0
        
        # Thread safety
        self._write_lock = threading.Lock()
        
        # V1.3.0: License manager for universe validation
        self._license_manager = None
        try:
            from src.utils.license import get_license_manager
            self._license_manager = get_license_manager()
        except Exception as e:
            logger.warning(f"License check unavailable: {e}")
    
    def start_recording(self, fps: float = 40.0):
        """Start recording to binary file with monotonic time"""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Open file in binary write mode
            self.file = open(self.file_path, 'wb')
            
            # Write placeholder header (will be updated on stop)
            self._write_header(fps, 0, 0)
            
            self.is_recording = True
            self.frame_count = 0
            self.fps = fps
            self.universes.clear()
            
            # Initialize monotonic time
            self.start_time_mono = time.monotonic()
            self.start_time_wall = time.time()
            
            logger.info(f"Started binary DMX recording: {self.file_path} at {fps} FPS (V{FORMAT_VERSION} with CRC)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            if self.file:
                self.file.close()
                self.file = None
            return False
    
    def write_frame(self, universe: int, dmx_data: bytes) -> bool:
        """Write a DMX frame with CRC (thread-safe)"""
        if not self.is_recording or not self.file:
            return False
        
        # V1.3.0: Validate universe against license limit
        if self._license_manager:
            is_valid, error_msg = self._license_manager.validate_universe(universe)
            if not is_valid:
                # Silently drop frames for universes beyond license limit
                return False
        
        try:
            # Use monotonic time for accurate timing
            timestamp = time.monotonic() - self.start_time_mono
            
            # Create frame with auto-calculated CRC
            frame = DMXFrame(timestamp, universe, dmx_data)
            
            # Thread-safe write
            with self._write_lock:
                self.file.write(frame.to_bytes())
                self.frame_count += 1
                self.universes.add(universe)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write frame: {e}")
            return False
    
    def stop_recording(self) -> Dict:
        """Stop recording and finalize the file"""
        if not self.is_recording or not self.file:
            return {}
        
        try:
            duration = time.monotonic() - self.start_time_mono
            
            # Update header with final counts
            with self._write_lock:
                self.file.seek(0)
                self._write_header(self.fps, len(self.universes), self.frame_count)
                
                self.file.close()
                self.file = None
            
            self.is_recording = False
            
            stats = {
                'file_path': str(self.file_path),
                'duration': duration,
                'frame_count': self.frame_count,
                'fps': self.fps,
                'universes': sorted(list(self.universes)),
                'file_size': self.file_path.stat().st_size,
                'avg_fps': self.frame_count / duration if duration > 0 else 0,
                'format_version': FORMAT_VERSION,
                'has_crc': True
            }
            
            logger.info(f"Recording stopped: {self.frame_count} frames, {duration:.2f}s, "
                       f"{stats['avg_fps']:.1f} avg FPS, {stats['file_size'] / 1024 / 1024:.2f} MB")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            if self.file:
                self.file.close()
                self.file = None
            return {}
    
    def _write_header(self, fps: float, universe_count: int, frame_count: int):
        """Write binary header V2.0"""
        flags = FLAG_HAS_CRC | FLAG_MONOTONIC_TIME
        
        # Pack header data (32 bytes total)
        header = struct.pack(
            '>4s B H H I B 18s',
            MAGIC_BYTES,           # Magic bytes (4)
            FORMAT_VERSION,        # Version (1)
            int(fps),              # FPS as uint16 (2)
            universe_count,        # Universe count (2)
            frame_count,           # Frame count (4)
            flags,                 # Feature flags (1)
            b'\x00' * 18          # Reserved (18)
        )
        
        assert len(header) == HEADER_SIZE, f"Header size mismatch: {len(header)} != {HEADER_SIZE}"
        self.file.write(header)


class DMXPlayer:
    """
    Binary DMX Player with multithreaded I/O buffer and time drift correction
    Ensures stable 60+ FPS playback even on Raspberry Pi
    """
    
    def __init__(self, file_path: str, buffer_size: int = DEFAULT_BUFFER_SIZE):
        self.file_path = Path(file_path)
        self.file: Optional[BinaryIO] = None
        
        # Header info
        self.version = 0
        self.fps = 40.0
        self.universe_count = 0
        self.frame_count = 0
        self.flags = 0
        
        # Playback state
        self.current_frame_index = 0
        self.is_playing = False
        
        # Multithreaded I/O buffer
        self.buffer_size = buffer_size
        self.frame_buffer = queue.Queue(maxsize=buffer_size)
        self.reader_thread: Optional[threading.Thread] = None
        self.stop_reading = threading.Event()
        
        # Time drift correction
        self.playback_start_time = 0
        self.playback_start_frame = 0
        self.drift_correction_enabled = True
        self.accumulated_drift = 0.0
        
        # Statistics
        self.frames_read = 0
        self.crc_errors = 0
        self.buffer_underruns = 0
        
        # V1.3.0: License manager for universe validation
        self._license_manager = None
        try:
            from src.utils.license import get_license_manager
            self._license_manager = get_license_manager()
        except Exception as e:
            logger.warning(f"License check unavailable: {e}")
    
    def open(self) -> bool:
        """Open recording file and read header"""
        try:
            if not self.file_path.exists():
                logger.error(f"Recording file not found: {self.file_path}")
                return False
            
            self.file = open(self.file_path, 'rb')
            
            # Read and validate header
            header_data = self.file.read(HEADER_SIZE)
            if len(header_data) < HEADER_SIZE:
                raise ValueError("Invalid file: header too short")
            
            magic, version, fps, universe_count, frame_count, flags, _ = struct.unpack(
                '>4s B H H I B 18s', header_data
            )
            
            if magic != MAGIC_BYTES:
                raise ValueError(f"Invalid file: magic bytes mismatch ({magic} != {MAGIC_BYTES})")
            
            self.version = version
            self.fps = float(fps)
            self.universe_count = universe_count
            self.frame_count = frame_count
            self.flags = flags
            self.current_frame_index = 0
            
            has_crc = bool(flags & FLAG_HAS_CRC)
            has_monotonic = bool(flags & FLAG_MONOTONIC_TIME)
            
            logger.info(f"Opened recording V{version}: {frame_count} frames, {fps:.1f} FPS, "
                       f"{universe_count} universe(s), CRC: {has_crc}, Monotonic: {has_monotonic}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to open recording: {e}")
            if self.file:
                self.file.close()
                self.file = None
            return False
    
    def _reader_worker(self):
        """Background thread to read frames into buffer"""
        logger.info("Frame reader thread started")
        
        while not self.stop_reading.is_set():
            try:
                # Check if buffer is full
                if self.frame_buffer.full():
                    time.sleep(0.001)  # 1ms wait
                    continue
                
                # Read next frame
                frame_data = self.file.read(FRAME_SIZE)
                if len(frame_data) < FRAME_SIZE:
                    logger.info("End of recording reached")
                    break
                
                # Parse and validate frame
                validate_crc = bool(self.flags & FLAG_HAS_CRC)
                frame = DMXFrame.from_bytes(frame_data, validate=validate_crc)
                
                if frame is None:
                    self.crc_errors += 1
                    logger.warning(f"Skipping corrupted frame at index {self.frames_read}")
                    continue
                
                # Add to buffer
                self.frame_buffer.put(frame, timeout=0.1)
                self.frames_read += 1
                
            except queue.Full:
                continue
            except Exception as e:
                logger.error(f"Reader thread error: {e}")
                break
        
        logger.info(f"Frame reader thread stopped (read {self.frames_read} frames)")
    
    def start_playback(self) -> bool:
        """Start multithreaded playback"""
        if not self.file:
            logger.error("File not opened")
            return False
        
        try:
            # Clear buffer and reset state
            while not self.frame_buffer.empty():
                try:
                    self.frame_buffer.get_nowait()
                except queue.Empty:
                    break
            
            self.stop_reading.clear()
            self.is_playing = True
            self.playback_start_time = time.monotonic()
            self.playback_start_frame = 0
            self.accumulated_drift = 0.0
            self.frames_read = 0
            self.crc_errors = 0
            self.buffer_underruns = 0
            
            # Start reader thread
            self.reader_thread = threading.Thread(target=self._reader_worker, daemon=True)
            self.reader_thread.start()
            
            logger.info("Multithreaded playback started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start playback: {e}")
            return False
    
    def get_next_frame(self, timeout: float = 0.1) -> Optional[DMXFrame]:
        """
        Get next frame from buffer with time drift correction
        Returns None if buffer is empty (underrun)
        """
        if not self.is_playing:
            return None
        
        try:
            frame = self.frame_buffer.get(timeout=timeout)
            
            # V1.3.0: Validate universe against license limit
            if self._license_manager:
                is_valid, _ = self._license_manager.validate_universe(frame.universe)
                if not is_valid:
                    # Skip frames for universes beyond license limit
                    logger.debug(f"Skipping frame for Universe {frame.universe} (license limit)")
                    return self.get_next_frame(timeout)  # Get next frame recursively
            
            self.current_frame_index += 1
            
            # Time drift correction every second
            if self.drift_correction_enabled and self.current_frame_index % int(self.fps) == 0:
                self._correct_time_drift()
            
            return frame
            
        except queue.Empty:
            self.buffer_underruns += 1
            logger.warning(f"Buffer underrun! (total: {self.buffer_underruns})")
            return None
    
    def _correct_time_drift(self):
        """Correct accumulated time drift"""
        if self.current_frame_index == 0:
            return
        
        # Calculate expected vs actual time
        elapsed_real = time.monotonic() - self.playback_start_time
        elapsed_expected = self.current_frame_index / self.fps
        
        drift = elapsed_real - elapsed_expected
        self.accumulated_drift = drift
        
        # Log significant drift
        drift_ms = drift * 1000
        if abs(drift_ms) > MAX_TIME_DRIFT_MS:
            logger.debug(f"Time drift: {drift_ms:.2f}ms at frame {self.current_frame_index}")
    
    def stop_playback(self):
        """Stop playback and reader thread"""
        self.is_playing = False
        self.stop_reading.set()
        
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)
        
        logger.info(f"Playback stopped. Stats: {self.frames_read} frames read, "
                   f"{self.crc_errors} CRC errors, {self.buffer_underruns} underruns, "
                   f"{self.accumulated_drift*1000:.2f}ms drift")
    
    def read_frame(self) -> Optional[DMXFrame]:
        """Read single frame (non-threaded, for seeking)"""
        if not self.file:
            return None
        
        try:
            frame_data = self.file.read(FRAME_SIZE)
            if len(frame_data) < FRAME_SIZE:
                return None
            
            validate_crc = bool(self.flags & FLAG_HAS_CRC)
            frame = DMXFrame.from_bytes(frame_data, validate=validate_crc)
            
            if frame:
                self.current_frame_index += 1
            
            return frame
            
        except Exception as e:
            logger.error(f"Failed to read frame: {e}")
            return None
    
    def read_all_frames(self) -> List[DMXFrame]:
        """Read all frames from file (blocking, for analysis)"""
        if not self.file:
            return []
        
        frames = []
        self.seek_frame(0)
        
        while True:
            frame = self.read_frame()
            if frame is None:
                break
            frames.append(frame)
        
        logger.info(f"Read {len(frames)} frames from {self.file_path}")
        return frames
    
    def seek_frame(self, frame_index: int) -> bool:
        """Seek to specific frame"""
        if not self.file or frame_index < 0 or frame_index >= self.frame_count:
            return False
        
        try:
            offset = HEADER_SIZE + (frame_index * FRAME_SIZE)
            self.file.seek(offset)
            self.current_frame_index = frame_index
            return True
            
        except Exception as e:
            logger.error(f"Failed to seek to frame {frame_index}: {e}")
            return False
    
    def get_frame_at_time(self, timestamp: float) -> Optional[DMXFrame]:
        """Get frame closest to given timestamp (binary search)"""
        if not self.file or self.frame_count == 0:
            return None
        
        left, right = 0, self.frame_count - 1
        
        while left <= right:
            mid = (left + right) // 2
            
            if not self.seek_frame(mid):
                return None
            
            frame = self.read_frame()
            if frame is None:
                return None
            
            if abs(frame.timestamp - timestamp) < 0.001:
                return frame
            elif frame.timestamp < timestamp:
                left = mid + 1
            else:
                right = mid - 1
        
        # Return closest frame
        self.seek_frame(left if left < self.frame_count else right)
        return self.read_frame()
    
    def get_info(self) -> Dict:
        """Get recording information"""
        if not self.file:
            return {}
        
        duration = self.frame_count / self.fps if self.fps > 0 else 0
        
        return {
            'file_path': str(self.file_path),
            'version': self.version,
            'fps': self.fps,
            'universe_count': self.universe_count,
            'frame_count': self.frame_count,
            'duration': duration,
            'file_size': self.file_path.stat().st_size,
            'current_frame': self.current_frame_index,
            'has_crc': bool(self.flags & FLAG_HAS_CRC),
            'monotonic_time': bool(self.flags & FLAG_MONOTONIC_TIME),
            'buffer_size': self.buffer_size,
            'frames_read': self.frames_read,
            'crc_errors': self.crc_errors,
            'buffer_underruns': self.buffer_underruns,
            'time_drift_ms': self.accumulated_drift * 1000
        }
    
    def close(self):
        """Close the recording file"""
        if self.is_playing:
            self.stop_playback()
        
        if self.file:
            self.file.close()
            self.file = None
            logger.info(f"Closed recording: {self.file_path}")
    
    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Utility functions
def verify_recording(file_path: str, verbose: bool = False) -> Dict:
    """Verify recording integrity by checking all CRCs"""
    stats = {
        'total_frames': 0,
        'valid_frames': 0,
        'crc_errors': 0,
        'duration': 0.0,
        'fps': 0.0
    }
    
    try:
        with DMXPlayer(file_path) as player:
            info = player.get_info()
            stats['total_frames'] = info['frame_count']
            stats['duration'] = info['duration']
            stats['fps'] = info['fps']
            
            if verbose:
                print(f"Verifying {file_path}...")
                print(f"  Frames: {info['frame_count']}, FPS: {info['fps']:.1f}, Duration: {info['duration']:.2f}s")
            
            # Read all frames and count CRC errors
            for i in range(info['frame_count']):
                frame = player.read_frame()
                if frame is None:
                    stats['crc_errors'] += 1
                else:
                    stats['valid_frames'] += 1
                
                if verbose and (i + 1) % 1000 == 0:
                    print(f"  Verified {i + 1}/{info['frame_count']} frames...")
            
            if verbose:
                print(f"✅ Verification complete: {stats['valid_frames']}/{stats['total_frames']} frames valid")
                if stats['crc_errors'] > 0:
                    print(f"⚠️  CRC errors: {stats['crc_errors']}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return stats


def convert_json_to_binary(json_path: str, output_path: str, fps: float = 40.0) -> bool:
    """Convert old JSON recording to binary format (legacy support)"""
    try:
        import json
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        recorder = DMXRecorder(output_path)
        recorder.start_recording(fps)
        
        # Write frames from JSON
        for point in data.get('data', []):
            universe = point.get('universe', 0)
            dmx_data = bytes(point.get('data', [0] * 512))
            recorder.write_frame(universe, dmx_data)
        
        stats = recorder.stop_recording()
        logger.info(f"Converted {json_path} -> {output_path}: {stats}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert JSON to binary: {e}")
        return False


if __name__ == "__main__":
    # Test binary format V2.0
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("=" * 80)
    print("DMX Binary Recorder V2.0 - Production Test")
    print("=" * 80)
    
    test_file = Path("test_recording_v2.dmxrec")
    
    # Test 1: Recording with CRC
    print("\n1️⃣  Testing recording with CRC16...")
    recorder = DMXRecorder(test_file)
    recorder.start_recording(fps=60.0)
    
    for i in range(200):
        # Simulate varying DMX data
        dmx_data = bytes([(i + j) % 256 for j in range(512)])
        recorder.write_frame(universe=i % 2, dmx_data=dmx_data)
        time.sleep(0.016)  # ~60 FPS
    
    stats = recorder.stop_recording()
    print(f"✅ Recording stats: {stats['frame_count']} frames, "
          f"{stats['avg_fps']:.1f} FPS, {stats['file_size'] / 1024:.2f} KB")
    
    # Test 2: Verify recording integrity
    print("\n2️⃣  Verifying recording integrity...")
    verify_stats = verify_recording(str(test_file), verbose=True)
    
    # Test 3: Multithreaded playback
    print("\n3️⃣  Testing multithreaded playback...")
    with DMXPlayer(test_file, buffer_size=50) as player:
        info = player.get_info()
        print(f"   File info: V{info['version']}, {info['frame_count']} frames, "
              f"{info['fps']:.1f} FPS, CRC: {info['has_crc']}")
        
        player.start_playback()
        
        # Simulate real-time playback
        frames_played = 0
        start = time.monotonic()
        
        while frames_played < min(100, info['frame_count']):
            frame = player.get_next_frame(timeout=0.1)
            if frame:
                frames_played += 1
                # Simulate frame processing time
                time.sleep(0.001)
        
        elapsed = time.monotonic() - start
        player.stop_playback()
        
        final_info = player.get_info()
        print(f"✅ Played {frames_played} frames in {elapsed:.2f}s ({frames_played/elapsed:.1f} FPS)")
        print(f"   CRC errors: {final_info['crc_errors']}, "
              f"Underruns: {final_info['buffer_underruns']}, "
              f"Drift: {final_info['time_drift_ms']:.2f}ms")
    
    # Test 4: Frame seeking
    print("\n4️⃣  Testing frame seeking...")
    with DMXPlayer(test_file) as player:
        # Seek to middle
        mid_frame = player.frame_count // 2
        player.seek_frame(mid_frame)
        frame = player.read_frame()
        print(f"✅ Seeked to frame {mid_frame}: {frame}")
        
        # Time-based seek
        target_time = 1.5  # 1.5 seconds
        frame = player.get_frame_at_time(target_time)
        print(f"✅ Frame at t={target_time}s: {frame}")
    
    print(f"\n{'='*80}")
    print(f"✅ All tests passed! File: {test_file.stat().st_size / 1024:.2f} KB")
    print(f"{'='*80}\n")
    
    # Clean up
    test_file.unlink()

