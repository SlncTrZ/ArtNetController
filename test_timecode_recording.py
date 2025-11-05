#!/usr/bin/env python3
"""
Test Timecode Recording with Depence Integration
Tests the full timecode sync recording workflow
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.system.timecode_receiver import TimecodeManager
from src.artnet.controller import ArtNetController
from src.gui.tabs.record import RecordTab

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_timecode_recording():
    """Test timecode recording functionality"""
    print("🎵 DMX Master LTS - Timecode Recording Test")
    print("=" * 50)
    
    try:
        # 1. Test timecode receiver creation
        print("\n1. Creating timecode manager...")
        timecode_manager = TimecodeManager()
        
        # 2. Create Art-Net controller 
        print("2. Creating Art-Net controller...")
        artnet_controller = ArtNetController()
        
        # 3. Start Art-Net controller
        print("3. Starting Art-Net controller...")
        if not artnet_controller.start():
            print("❌ Failed to start Art-Net controller")
            return False
        
        print("✅ Art-Net controller started successfully")
        
        # 4. Create Art-Net 4 Timecode receiver with shared socket
        print("4. Creating Art-Net 4 Timecode receiver...")
        artnet4_receiver = timecode_manager.create_artnet4_timecode_receiver(
            artnet_controller=artnet_controller
        )
        
        # 5. Set up timecode callbacks
        def on_timecode_received(data):
            timecode = data['timecode']
            fps = data['fps']
            source = data['source']
            print(f"🎵 Timecode: {timecode} ({fps}fps) from {source}")
        
        def on_timecode_stopped():
            print("⚠️ Timecode signal stopped")
        
        artnet4_receiver.set_callbacks(on_timecode_received, on_timecode_stopped)
        
        # 6. Start timecode receiver
        print("5. Starting Art-Net 4 Timecode receiver...")
        if not artnet4_receiver.start():
            print("❌ Failed to start timecode receiver")
            return False
        
        print("✅ Art-Net 4 Timecode receiver started successfully")
        print("🎭 Using shared socket with main Art-Net controller")
        
        # 7. Instructions for user
        print("\n" + "=" * 60)
        print("📋 TESTING INSTRUCTIONS:")
        print("=" * 60)
        print("1. Open Depence software")
        print("2. Configure Depence to send Art-Net 4 Timecode:")
        print("   - Go to Interfaces > Art-Net Settings")
        print("   - Enable 'Send Timecode via Art-Net 4'")
        print("   - Set target IP to 127.0.0.1 or your computer's IP")
        print("   - Start playback in Depence")
        print("3. You should see timecode messages above")
        print("4. Press Ctrl+C to stop test")
        print("=" * 60)
        
        # 8. Monitor for timecode
        print("\n🎵 Listening for Art-Net 4 Timecode from Depence...")
        print("   (Make sure Depence is sending timecode)")
        
        try:
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Test stopped by user")
        
        # 9. Cleanup
        print("🧹 Cleaning up...")
        artnet4_receiver.stop()
        artnet_controller.stop()
        
        print("✅ Test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")
        return False

def test_manual_timecode_send():
    """Send manual timecode packets for testing"""
    print("\n🧪 Sending test Art-Net 4 Timecode packets...")
    
    import socket
    import struct
    
    # Create test timecode packet
    def create_artnet_timecode_packet(hours, minutes, seconds, frames, fps_type=1):
        """Create Art-Net 4 Timecode packet"""
        # Art-Net header
        header = b'Art-Net\0'
        
        # OpCode 0x9700 (little endian)
        opcode = struct.pack('<H', 0x9700)
        
        # Protocol version 0x000e (little endian) 
        version = struct.pack('<H', 0x000e)
        
        # Filler bytes
        filler = b'\x00\x00'
        
        # Timecode data
        timecode_data = struct.pack('BBBB', frames, seconds, minutes, hours)
        
        # Type (frame rate)
        type_byte = struct.pack('B', fps_type)  # 1 = 25fps
        
        # Spare bytes
        spare = b'\x00' * 3
        
        packet = header + opcode + version + filler + timecode_data + type_byte + spare
        return packet
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        print("📡 Sending test timecode packets to localhost...")
        
        for i in range(10):
            # Create timecode: 00:00:i:00 at 25fps
            packet = create_artnet_timecode_packet(0, 0, i, 0, 1)
            
            # Send to localhost
            sock.sendto(packet, ('127.0.0.1', 6454))
            print(f"   Sent: 00:00:{i:02d}:00")
            time.sleep(1)
        
        sock.close()
        print("✅ Test timecode packets sent")
        
    except Exception as e:
        print(f"❌ Failed to send test packets: {e}")

if __name__ == "__main__":
    print("DMX Master LTS - Timecode Recording Test Suite")
    print("Choose test mode:")
    print("1. Test timecode reception (default)")
    print("2. Send test timecode packets")
    
    choice = input("Enter choice (1-2) [1]: ").strip()
    
    if choice == "2":
        test_manual_timecode_send()
    else:
        test_timecode_recording()