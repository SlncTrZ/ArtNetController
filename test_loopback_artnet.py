#!/usr/bin/env python3
"""
Depence Loopback Configuration Tool
Configure Art-Net for Depence and DMX Master running on same machine
"""

import sys
import time
import socket
import struct
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.artnet.controller import ArtNetController

def test_loopback_artnet():
    """Test Art-Net loopback on same machine"""
    print("🔄 Depence Loopback Test")
    print("=" * 40)
    print("📍 Both Depence and DMX Master on: 192.168.1.171")
    print("🎯 Testing loopback Art-Net communication")
    print("=" * 40)
    
    # Create Art-Net controller
    artnet_controller = ArtNetController()
    
    dmx_count = 0
    
    def on_dmx_received(universe: int, dmx_data: bytes, source_ip: str):
        nonlocal dmx_count
        dmx_count += 1
        
        # Show first 20 channels with values
        active_channels = []
        for i, value in enumerate(dmx_data[:50]):  # Check first 50 channels
            if value > 0:
                active_channels.append(f"Ch{i+1}:{value}")
        
        print(f"✅ DMX #{dmx_count}: Universe {universe} from {source_ip}")
        print(f"   📊 Packet size: {len(dmx_data)} bytes")
        
        if active_channels:
            display = ", ".join(active_channels[:15])
            if len(active_channels) > 15:
                display += f" ... (+{len(active_channels)-15} more)"
            print(f"   🔥 Active: {display}")
        else:
            print(f"   ❌ All channels zero")
        
        # Always show first 10 channels for reference
        first_10 = [dmx_data[i] if i < len(dmx_data) else 0 for i in range(10)]
        print(f"   🎯 Ch1-10: {first_10}")
        print()
    
    artnet_controller.dmx_received_callback = on_dmx_received
    
    # Start controller
    print("🚀 Starting Art-Net controller...")
    if not artnet_controller.start():
        print("❌ Failed to start Art-Net controller")
        return
    
    print("✅ Art-Net controller started on port 6454")
    print()
    
    print("📋 DEPENCE LOOPBACK CONFIGURATION:")
    print("-" * 45)
    print("1. In Depence (same machine):")
    print("   📍 Go to: Interfaces > Art-Net Settings")
    print("   ✅ Enable Art-Net Output")
    print("   🎯 Target IP: 127.0.0.1 (localhost)")
    print("   🌍 Universe: 1 (will show as Universe 0 in DMX Master)")
    print("   📡 Port: 6454 (default)")
    print("   ⚠️  NOTE: Depence Universe 1 = DMX Master Universe 0")
    print()
    print("2. Alternative settings if localhost doesn't work:")
    print("   🎯 Target IP: 192.168.1.171 (this machine's IP)")
    print("   🎯 Target IP: 255.255.255.255 (broadcast)")
    print()
    print("3. Test DMX output:")
    print("   🎚️ Move some faders in Depence")
    print("   ▶️ Or start a sequence/playback")
    print("   📺 You should see DMX data appear below")
    print("-" * 45)
    print()
    
    # Send test packet to verify loopback works
    def send_test_loopback():
        time.sleep(3)
        print("🧪 Sending test loopback packet...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Create Art-Net DMX packet
            header = b'Art-Net\0'
            opcode = struct.pack('<H', 0x5000)
            version = struct.pack('<H', 0x000e)
            sequence = struct.pack('B', 0)
            physical = struct.pack('B', 0)
            universe = struct.pack('<H', 0)
            
            # Test DMX data
            dmx_data = bytearray(512)
            dmx_data[0] = 255  # Channel 1 = 255
            dmx_data[1] = 128  # Channel 2 = 128
            dmx_data[2] = 64   # Channel 3 = 64
            
            length = struct.pack('>H', len(dmx_data))
            packet = header + opcode + version + sequence + physical + universe + length + bytes(dmx_data)
            
            # Send to localhost
            sock.sendto(packet, ('127.0.0.1', 6454))
            sock.close()
            
            print("📡 Test packet sent to localhost")
            
        except Exception as e:
            print(f"❌ Test packet failed: {e}")
    
    # Start test packet sender
    test_thread = threading.Thread(target=send_test_loopback)
    test_thread.daemon = True
    test_thread.start()
    
    # Monitor for packets
    print("🎧 Monitoring Art-Net DMX...")
    
    try:
        start_time = time.time()
        
        while True:
            time.sleep(10)
            elapsed = time.time() - start_time
            
            print(f"⏰ Status after {elapsed:.0f}s: {dmx_count} DMX packets received")
            
            if dmx_count == 0:
                print("💡 Troubleshooting tips:")
                print("   🔧 Check Depence Art-Net is enabled")
                print("   🔧 Try target IP: 127.0.0.1, 192.168.1.171, or 255.255.255.255")
                print("   🔧 Verify DMX faders are active in Depence")
                print("   🔧 Check Windows Firewall allows port 6454")
            else:
                print("✅ Loopback communication working!")
            
            print()
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped")
    
    # Cleanup
    artnet_controller.stop()
    print("🧹 Art-Net controller stopped")
    
    # Final recommendation
    print(f"\n📊 RESULTS: {dmx_count} DMX packets received")
    
    if dmx_count > 0:
        print("✅ Art-Net loopback is working!")
        print("💡 Now configure Depence with the same settings")
        print("   Target IP: 127.0.0.1 or 192.168.1.171")
        print("   Universe: 1 (will show as Universe 0 in DMX Master)")
        print("   Port: 6454")
    else:
        print("❌ No loopback communication detected")
        print("🔧 Try these solutions:")
        print("   1. Check Windows Firewall settings")
        print("   2. Try running DMX Master as Administrator")
        print("   3. Use broadcast IP (255.255.255.255) in Depence")

if __name__ == "__main__":
    test_loopback_artnet()