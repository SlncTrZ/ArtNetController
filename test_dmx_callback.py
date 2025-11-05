#!/usr/bin/env python3
"""
Simple Art-Net DMX Callback Test
Test if DMX callback is working correctly
"""

import sys
import time
import threading
import socket
import struct
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.artnet.controller import ArtNetController

def main():
    print("🧪 Art-Net DMX Callback Test")
    print("=" * 40)
    
    # Create controller
    artnet_controller = ArtNetController()
    
    # Track received DMX
    dmx_count = 0
    
    def on_dmx_received(universe: int, dmx_data: bytes, source_ip: str):
        global dmx_count
        dmx_count += 1
        
        # Show first 10 non-zero channels
        non_zero = [(i+1, val) for i, val in enumerate(dmx_data[:10]) if val > 0]
        
        print(f"✅ DMX #{dmx_count}: U{universe} from {source_ip}")
        if non_zero:
            print(f"   Non-zero channels: {non_zero}")
        else:
            print(f"   All channels 0 (length: {len(dmx_data)})")
    
    # Set callback
    artnet_controller.dmx_received_callback = on_dmx_received
    
    # Start controller
    print("Starting Art-Net controller...")
    if not artnet_controller.start():
        print("❌ Failed to start")
        return
    
    print("✅ Controller started, waiting for DMX...")
    
    # Send test packets in background
    def send_test_packets():
        time.sleep(2)  # Wait for controller to start
        
        print("\n📡 Sending test packets...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        for i in range(3):
            # Create Art-Net DMX packet
            header = b'Art-Net\0'
            opcode = struct.pack('<H', 0x5000)  # ArtDmx
            version = struct.pack('<H', 0x000e)
            sequence = struct.pack('B', 0)
            physical = struct.pack('B', 0)
            universe = struct.pack('<H', 0)  # Universe 0
            
            # DMX data
            dmx_data = bytearray(512)
            dmx_data[0] = 100 + i * 50  # Channel 1
            dmx_data[1] = 50 + i * 25   # Channel 2
            dmx_data[2] = 200 - i * 30  # Channel 3
            
            length = struct.pack('>H', len(dmx_data))
            
            packet = header + opcode + version + sequence + physical + universe + length + bytes(dmx_data)
            
            sock.sendto(packet, ('127.0.0.1', 6454))
            print(f"   Sent test packet {i+1}: Ch1={dmx_data[0]}, Ch2={dmx_data[1]}, Ch3={dmx_data[2]}")
            time.sleep(1)
        
        sock.close()
        print("📡 Test packets completed")
    
    # Start sender thread
    sender_thread = threading.Thread(target=send_test_packets)
    sender_thread.daemon = True
    sender_thread.start()
    
    # Wait for packets
    try:
        for i in range(10):
            time.sleep(1)
            if i == 7 and dmx_count == 0:
                print("⚠️ No DMX received yet...")
        
        print(f"\n📊 Final result: {dmx_count} DMX packets received")
        
        if dmx_count > 0:
            print("✅ DMX callback is working!")
        else:
            print("❌ DMX callback not triggered")
            print("🔍 Possible issues:")
            print("   - Callback not set correctly")
            print("   - DMX packet parsing issue")
            print("   - Port binding issue")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    
    # Cleanup
    artnet_controller.stop()
    print("🧹 Cleanup complete")

if __name__ == "__main__":
    main()