#!/usr/bin/env python3
"""
Test Art-Net Reception from Depence
Debug why DMX View tab is not showing values from Depence
"""

import sys
import time
import logging
import socket
import struct
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.artnet.controller import ArtNetController

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_artnet_reception():
    """Test Art-Net reception from Depence"""
    print("🎭 DMX Master LTS - Art-Net Reception Test")
    print("=" * 50)
    
    try:
        # 1. Create Art-Net controller
        print("1. Creating Art-Net controller...")
        artnet_controller = ArtNetController()
        
        # 2. Set up DMX callback to monitor received data
        dmx_received_count = 0
        last_dmx_data = {}
        
        def on_dmx_received(universe: int, dmx_data: bytes, source_ip: str):
            nonlocal dmx_received_count, last_dmx_data
            dmx_received_count += 1
            last_dmx_data[universe] = dmx_data
            
            # Show non-zero channels
            non_zero_channels = []
            for i, value in enumerate(dmx_data):
                if value > 0:
                    non_zero_channels.append(f"Ch{i+1}:{value}")
            
            channels_str = ", ".join(non_zero_channels[:10])
            if len(non_zero_channels) > 10:
                channels_str += f"... (+{len(non_zero_channels)-10} more)"
            elif not non_zero_channels:
                channels_str = "All Zero"
            
            print(f"📥 DMX #{dmx_received_count}: U{universe} from {source_ip} - {channels_str}")
        
        artnet_controller.dmx_received_callback = on_dmx_received
        
        # 3. Start Art-Net controller
        print("2. Starting Art-Net controller...")
        if not artnet_controller.start():
            print("❌ Failed to start Art-Net controller")
            return False
        
        print("✅ Art-Net controller started successfully")
        print(f"📡 Listening on port 6454 for Art-Net DMX packets")
        
        # 4. Instructions for user
        print("\n" + "=" * 60)
        print("📋 TESTING INSTRUCTIONS:")
        print("=" * 60)
        print("1. Open Depence software")
        print("2. Configure Depence Art-Net output:")
        print("   - Go to Interfaces > Art-Net Settings")
        print("   - Enable Art-Net output")
        print("   - Set target IP to 127.0.0.1 or broadcast (255.255.255.255)")
        print("   - Set universe to 0 (or your desired universe)")
        print("3. Start playback or use manual faders in Depence")
        print("4. You should see DMX data messages above")
        print("5. Press Ctrl+C to stop test")
        print("=" * 60)
        
        # 5. Monitor for Art-Net packets
        print("\n🎭 Monitoring Art-Net DMX from Depence...")
        print("   (Make sure Depence is sending DMX data)")
        
        start_time = time.time()
        
        try:
            while True:
                time.sleep(1)
                
                # Status every 10 seconds
                elapsed = time.time() - start_time
                if int(elapsed) % 10 == 0 and elapsed > 1:
                    print(f"⏰ Status: {dmx_received_count} packets received in {elapsed:.0f}s")
                    if dmx_received_count == 0:
                        print("⚠️  No DMX packets received yet")
                        print("💡 Check Depence Art-Net settings:")
                        print("   - Art-Net output enabled?") 
                        print("   - Target IP correct? (127.0.0.1 or your IP)")
                        print("   - Universe number correct?")
                        print("   - Firewall blocking port 6454?")
                
        except KeyboardInterrupt:
            print("\n\n🛑 Test stopped by user")
        
        # 6. Summary
        print(f"\n📊 RESULTS:")
        print(f"   Total DMX packets received: {dmx_received_count}")
        print(f"   Universes seen: {list(last_dmx_data.keys())}")
        
        if dmx_received_count > 0:
            print("✅ Art-Net reception is working!")
            print("💡 If DMX View tab still shows no data, the issue is in the GUI connection")
        else:
            print("❌ No Art-Net DMX packets received")
            print("🔧 Troubleshooting steps:")
            print("   1. Check Depence Art-Net output settings")
            print("   2. Verify network connectivity")
            print("   3. Check Windows Firewall (port 6454)")
            print("   4. Try broadcast IP (255.255.255.255) in Depence")
        
        # 7. Cleanup
        print("\n🧹 Cleaning up...")
        artnet_controller.stop()
        
        return dmx_received_count > 0
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")
        return False

def send_test_artnet_dmx():
    """Send test Art-Net DMX packets"""
    print("\n🧪 Sending test Art-Net DMX packets...")
    
    def create_artnet_dmx_packet(universe: int, dmx_data: bytes):
        """Create Art-Net DMX packet"""
        # Art-Net header
        header = b'Art-Net\0'
        
        # OpCode 0x5000 (little endian)
        opcode = struct.pack('<H', 0x5000)
        
        # Protocol version 0x000e (little endian)
        version = struct.pack('<H', 0x000e)
        
        # Sequence (0 = no sequence)
        sequence = struct.pack('B', 0)
        
        # Physical (0 = not applicable)
        physical = struct.pack('B', 0)
        
        # Universe (little endian)
        universe_bytes = struct.pack('<H', universe)
        
        # Length (big endian - number of DMX channels)
        length = struct.pack('>H', len(dmx_data))
        
        # DMX data
        packet = header + opcode + version + sequence + physical + universe_bytes + length + dmx_data
        return packet
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        print("📡 Sending test DMX packets to localhost...")
        
        for i in range(10):
            # Create test DMX data - channels 1-10 with increasing values
            dmx_data = bytearray(512)  # 512 channels, all 0
            for ch in range(10):
                dmx_data[ch] = min(255, (i + 1) * 25 + ch * 10)  # Varying values
            
            packet = create_artnet_dmx_packet(0, bytes(dmx_data))
            
            # Send to localhost and broadcast
            sock.sendto(packet, ('127.0.0.1', 6454))
            sock.sendto(packet, ('255.255.255.255', 6454))
            
            print(f"   Packet {i+1}: Ch1-10 = {list(dmx_data[:10])}")
            time.sleep(0.5)
        
        sock.close()
        print("✅ Test DMX packets sent")
        
    except Exception as e:
        print(f"❌ Failed to send test packets: {e}")

def check_network_setup():
    """Check network setup for Art-Net"""
    print("\n🔍 Checking network setup...")
    
    try:
        import socket
        
        # Check if port 6454 is available
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_socket.bind(('', 6454))
            test_socket.close()
            print("✅ Port 6454 is available")
        except OSError as e:
            print(f"⚠️ Port 6454 may be in use: {e}")
        
        # Get local IP addresses
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"🖥️ Local IP: {local_ip}")
        print(f"💡 Configure Depence to send to: 127.0.0.1 or {local_ip}")
        
        # Check broadcast capability
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            test_socket.close()
            print("✅ Broadcast capability available")
        except Exception as e:
            print(f"⚠️ Broadcast issue: {e}")
            
    except Exception as e:
        print(f"❌ Network check failed: {e}")

if __name__ == "__main__":
    print("DMX Master LTS - Art-Net Reception Diagnostics")
    print("Choose test mode:")
    print("1. Test Art-Net reception from Depence (default)")
    print("2. Send test Art-Net DMX packets")
    print("3. Check network setup")
    
    choice = input("Enter choice (1-3) [1]: ").strip()
    
    if choice == "2":
        send_test_artnet_dmx()
    elif choice == "3":
        check_network_setup()
    else:
        test_artnet_reception()