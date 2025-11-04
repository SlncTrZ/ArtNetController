"""
Binary DMX Recorder Module
Ghi và đọc DMX data dạng binary format (.dmxrec) để tối ưu dung lượng và tốc độ

Binary Format Structure:
========================
HEADER (Fixed size):
- Magic bytes: 'DMXR' (4 bytes)
- Version: uint8 (1 byte) - Currently version 1
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
"""

import struct
import logging
from pathlib import Path
from typing import List, Dict, BinaryIO, Optional, Tuple
import time

logger = logging.getLogger(__name__)

# Binary format constants
MAGIC_BYTES = b'DMXR'
FORMAT_VERSION = 1
DMX_CHANNELS = 512
HEADER_SIZE = 31
FRAME_SIZE = 522  # 8 (timestamp) + 2 (universe) + 512 (DMX data)

class DMXFrame:
    """Represents a single DMX frame"""
    __slots__ = ['timestamp', 'universe', 'data']
    
    def __init__(self, timestamp: float, universe: int, data: bytes):
        self.timestamp = timestamp
        self.universe = universe
        self.data = data[:DMX_CHANNELS]  # Ensure exactly 512 bytes
    
    def to_bytes(self) -> bytes:
        """Convert frame to binary format"""
        # Pad data to 512 bytes if needed
        padded_data = self.data + b'\x00' * (DMX_CHANNELS - len(self.data))
        return struct.pack('>d H 512s', self.timestamp, self.universe, padded_data)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'DMXFrame':
        """Create frame from binary data"""
        if len(data) < FRAME_SIZE:
            raise ValueError(f"Invalid frame data size: {len(data)} (expected {FRAME_SIZE})")
        
        timestamp, universe, dmx_data = struct.unpack('>d H 512s', data[:FRAME_SIZE])
        return cls(timestamp, universe, dmx_data)
    
    def __repr__(self):
        active_channels = sum(1 for b in self.data if b > 0)
        return f"DMXFrame(t={self.timestamp:.3f}s, u={self.universe}, active={active_channels}/512)"


class DMXRecorder:
    """Binary DMX Recorder for recording Art-Net data"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file: Optional[BinaryIO] = None
        self.is_recording = False
        self.frame_count = 0
        self.start_time = 0
        self.fps = 40.0  # Default FPS
        self.universes = set()
    
    def start_recording(self, fps: float = 40.0):
        """Start recording to binary file"""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Open file in binary write mode
            self.file = open(self.file_path, 'wb')
            
            # Write placeholder header (will be updated on stop)
            self._write_header(fps, 0, 0)
            
            self.is_recording = True
            self.frame_count = 0
            self.start_time = time.time()
            self.fps = fps
            self.universes.clear()
            
            logger.info(f"Started binary DMX recording: {self.file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            if self.file:
                self.file.close()
                self.file = None
            return False
    
    def write_frame(self, universe: int, dmx_data: bytes):
        """Write a DMX frame to the recording"""
        if not self.is_recording or not self.file:
            return False
        
        try:
            timestamp = time.time() - self.start_time
            frame = DMXFrame(timestamp, universe, dmx_data)
            
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
            duration = time.time() - self.start_time
            
            # Update header with final counts
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
                'avg_fps': self.frame_count / duration if duration > 0 else 0
            }
            
            logger.info(f"Recording stopped: {self.frame_count} frames, {duration:.2f}s, "
                       f"{stats['avg_fps']:.1f} FPS, {stats['file_size'] / 1024 / 1024:.2f} MB")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            if self.file:
                self.file.close()
                self.file = None
            return {}
    
    def _write_header(self, fps: float, universe_count: int, frame_count: int):
        """Write binary header"""
        # Pack header data
        header = struct.pack(
            '>4s B f H I 16s',
            MAGIC_BYTES,           # Magic bytes
            FORMAT_VERSION,        # Version
            fps,                   # FPS
            universe_count,        # Universe count
            frame_count,           # Frame count
            b'\x00' * 16          # Reserved
        )
        
        assert len(header) == HEADER_SIZE, f"Header size mismatch: {len(header)} != {HEADER_SIZE}"
        self.file.write(header)


class DMXPlayer:
    """Binary DMX Player for playback of recorded Art-Net data"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file: Optional[BinaryIO] = None
        self.fps = 40.0
        self.universe_count = 0
        self.frame_count = 0
        self.current_frame_index = 0
    
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
            
            magic, version, fps, universe_count, frame_count, _ = struct.unpack(
                '>4s B f H I 16s', header_data
            )
            
            if magic != MAGIC_BYTES:
                raise ValueError(f"Invalid file: magic bytes mismatch ({magic} != {MAGIC_BYTES})")
            
            if version != FORMAT_VERSION:
                logger.warning(f"File version {version} != current version {FORMAT_VERSION}")
            
            self.fps = fps
            self.universe_count = universe_count
            self.frame_count = frame_count
            self.current_frame_index = 0
            
            logger.info(f"Opened recording: {self.frame_count} frames, {fps:.1f} FPS, "
                       f"{universe_count} universe(s)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to open recording: {e}")
            if self.file:
                self.file.close()
                self.file = None
            return False
    
    def read_frame(self) -> Optional[DMXFrame]:
        """Read next frame from file"""
        if not self.file:
            return None
        
        try:
            frame_data = self.file.read(FRAME_SIZE)
            if len(frame_data) < FRAME_SIZE:
                return None  # End of file
            
            frame = DMXFrame.from_bytes(frame_data)
            self.current_frame_index += 1
            return frame
            
        except Exception as e:
            logger.error(f"Failed to read frame: {e}")
            return None
    
    def read_all_frames(self) -> List[DMXFrame]:
        """Read all frames from file"""
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
        """Get frame closest to given timestamp"""
        # Binary search for efficiency
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
            
            if abs(frame.timestamp - timestamp) < 0.001:  # Close enough
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
        
        duration = 0
        if self.frame_count > 0 and self.fps > 0:
            # Estimate duration from frame count and FPS
            duration = self.frame_count / self.fps
        
        return {
            'file_path': str(self.file_path),
            'fps': self.fps,
            'universe_count': self.universe_count,
            'frame_count': self.frame_count,
            'duration': duration,
            'file_size': self.file_path.stat().st_size,
            'current_frame': self.current_frame_index
        }
    
    def close(self):
        """Close the recording file"""
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
def convert_json_to_binary(json_path: str, output_path: str, fps: float = 40.0) -> bool:
    """Convert old JSON recording to binary format"""
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
            
            # Manually set timestamp
            recorder.file.write(struct.pack('>d H 512s', 
                                          point.get('timestamp', 0),
                                          universe,
                                          dmx_data))
            recorder.frame_count += 1
            recorder.universes.add(universe)
        
        stats = recorder.stop_recording()
        logger.info(f"Converted {json_path} -> {output_path}: {stats}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert JSON to binary: {e}")
        return False


if __name__ == "__main__":
    # Test binary format
    logging.basicConfig(level=logging.INFO)
    
    # Test recording
    print("Testing DMX Binary Recorder...")
    
    test_file = Path("test_recording.dmxrec")
    
    # Record some test data
    recorder = DMXRecorder(test_file)
    recorder.start_recording(fps=40.0)
    
    for i in range(100):
        dmx_data = bytes([i % 256] * 512)
        recorder.write_frame(universe=0, dmx_data=dmx_data)
        time.sleep(0.025)  # Simulate 40 FPS
    
    stats = recorder.stop_recording()
    print(f"\nRecording stats: {stats}")
    
    # Test playback
    print("\nTesting DMX Binary Player...")
    
    with DMXPlayer(test_file) as player:
        info = player.get_info()
        print(f"Recording info: {info}")
        
        # Read first 5 frames
        print("\nFirst 5 frames:")
        for i in range(5):
            frame = player.read_frame()
            if frame:
                print(f"  {frame}")
        
        # Seek to middle
        print(f"\nSeeking to frame 50...")
        player.seek_frame(50)
        frame = player.read_frame()
        print(f"  {frame}")
    
    print(f"\nTest complete! File size: {test_file.stat().st_size} bytes")
    test_file.unlink()  # Clean up
