#!/usr/bin/env python3
"""
Debug Art-Net DMX Packet Parsing
Test detailed packet parsing and callback mechanism
"""

import sys
import time
import socket
import struct
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.artnet.controller import ArtNetController, ArtNetDMX

def test_packet_parsing():
    """Test Art-Net packet parsing in detail"""
    print("🧪 Art-Net DMX Packet Parsing Debug")
    print("=" * 50)
    
    # Test manual packet creation and parsing
    print("1. Testing packet creation and parsing...")
    
    # Create test DMX data
    test_dmx = bytearray(512)
    test_dmx[0] = 255  # Channel 1 = 255
    test_dmx[1] = 128  # Channel 2 = 128
    test_dmx[2] = 64   # Channel 3 = 64
    test_dmx[3] = 32   # Channel 4 = 32
    
    print(f"   📊 Test DMX data: Ch1-4 = {list(test_dmx[:4])}")
    
    # Create Art-Net DMX packet manually
    header = b'Art-Net\0'              # 8 bytes
    opcode = struct.pack('<H', 0x5000)  # 2 bytes (little endian)
    version = struct.pack('<H', 0x000e) # 2 bytes (little endian)
    sequence = struct.pack('B', 0)      # 1 byte
    physical = struct.pack('B', 0)      # 1 byte  
    universe = struct.pack('<H', 0)     # 2 bytes (little endian)
    length = struct.pack('>H', len(test_dmx))  # 2 bytes (BIG endian!)
    
    full_packet = header + opcode + version + sequence + physical + universe + length + bytes(test_dmx)
    
    print(f"   📦 Packet size: {len(full_packet)} bytes")
    print(f"   📋 Header: {header}")
    print(f"   🔢 OpCode: 0x{struct.unpack('<H', opcode)[0]:04x}")
    print(f"   🌍 Universe: {struct.unpack('<H', universe)[0]}")
    print(f"   📏 Length: {struct.unpack('>H', length)[0]} (big endian)")
    
    # Test parsing
    print("\n2. Testing DMX packet parsing...")
    payload = full_packet[12:]  # Skip Art-Net header + opcode + version
    dmx_info = ArtNetDMX.unpack_dmx(payload)
    
    if dmx_info:
        print(f"   ✅ Parse successful:")
        print(f"      🌍 Universe: {dmx_info['universe']}")
        print(f"      📏 Length: {dmx_info['length']}")
        print(f"      📊 DMX data size: {len(dmx_info['dmx_data'])}")
        print(f"      🎯 Ch1-4: {list(dmx_info['dmx_data'][:4])}")
    else:
        print(f"   ❌ Parse failed!")
        return False
    
    # Test with Art-Net controller
    print("\n3. Testing with Art-Net controller...")
    
    controller = ArtNetController()
    
    dmx_received_count = 0
    last_dmx_data = None
    
    def debug_dmx_callback(universe: int, dmx_data: bytes, source_ip: str):
        nonlocal dmx_received_count, last_dmx_data
        dmx_received_count += 1
        last_dmx_data = dmx_data
        
        print(f"   📥 Callback #{dmx_received_count}:")
        print(f"      🌍 Universe: {universe}")
        print(f"      🔗 Source: {source_ip}")
        print(f"      📊 Data size: {len(dmx_data)} bytes")
        print(f"      🎯 Ch1-10: {list(dmx_data[:10])}")
        
        # Count non-zero channels
        non_zero = sum(1 for b in dmx_data if b > 0)
        print(f"      🔥 Non-zero channels: {non_zero}")
    
    controller.dmx_received_callback = debug_dmx_callback
    
    # Start controller
    if not controller.start():
        print("   ❌ Failed to start controller")
        return False
    
    print("   ✅ Controller started")
    
    # Send test packet
    def send_debug_packet():
        time.sleep(1)
        
        print("\n4. Sending test packet...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Send the packet we created
            sock.sendto(full_packet, ('127.0.0.1', 6454))
            print(f"   📡 Sent {len(full_packet)} byte packet to localhost:6454")
            
            # Also try a minimal packet
            minimal_dmx = bytearray(10)  # Just 10 channels
            minimal_dmx[0] = 200
            minimal_dmx[1] = 150
            minimal_dmx[2] = 100
            
            minimal_length = struct.pack('>H', len(minimal_dmx))
            minimal_packet = header + opcode + version + sequence + physical + universe + minimal_length + bytes(minimal_dmx)
            
            time.sleep(0.5)
            sock.sendto(minimal_packet, ('127.0.0.1', 6454))
            print(f"   📡 Sent {len(minimal_packet)} byte minimal packet")
            
            sock.close()
            
        except Exception as e:
            print(f"   ❌ Send failed: {e}")
    
    # Start sender
    sender_thread = threading.Thread(target=send_debug_packet)
    sender_thread.daemon = True
    sender_thread.start()
    
    # Wait for results
    time.sleep(3)
    
    # Results
    print(f"\n📊 RESULTS:")
    print(f"   📦 Callbacks received: {dmx_received_count}")
    
    if dmx_received_count > 0 and last_dmx_data:
        print(f"   📊 Last DMX size: {len(last_dmx_data)} bytes")
        print(f"   🎯 Last Ch1-10: {list(last_dmx_data[:10])}")
        print("   ✅ Packet parsing is working!")
    else:
        print("   ❌ No callbacks received - parsing may be broken")
    
    # Cleanup
    controller.stop()
    return dmx_received_count > 0

def test_depence_format():
    """Test specific Depence Art-Net format"""
    print("\n🎭 Testing Depence-style packets...")
    
    controller = ArtNetController()
    
    packets_received = 0
    
    def depence_callback(universe: int, dmx_data: bytes, source_ip: str):
        nonlocal packets_received
        packets_received += 1
        
        # Show detailed info for Depence-style packets
        print(f"🎭 Depence-style packet #{packets_received}:")
        print(f"   🌍 Universe: {universe}")
        print(f"   📊 Size: {len(dmx_data)} bytes")
        
        # Show all non-zero channels
        active = [(i+1, val) for i, val in enumerate(dmx_data) if val > 0]
        if active:
            print(f"   🔥 Active channels: {active[:20]}")  # First 20
        else:
            print(f"   ❌ All channels zero")
    
    controller.dmx_received_callback = depence_callback
    
    if not controller.start():
        print("❌ Failed to start controller")
        return False
    
    print("✅ Controller ready for Depence packets")
    print("🎚️ Now move faders in Depence and watch for packets...")
    
    # Monitor for 30 seconds
    for i in range(6):
        time.sleep(5)
        print(f"⏰ Waiting... {packets_received} packets so far ({(i+1)*5}s)")
    
    controller.stop()
    
    print(f"\n🎭 Depence test results: {packets_received} packets received")
    return packets_received > 0

if __name__ == "__main__":
    # Run packet parsing test
    parsing_ok = test_packet_parsing()
    
    if parsing_ok:
        print("\n" + "="*50)
        # Run Depence test
        test_depence_format()
    else:
        print("❌ Packet parsing failed - fix parsing first!")