#!/usr/bin/env python3
"""
Raw Art-Net Packet Inspector
Inspect all Art-Net traffic from Depence to understand what's being sent
"""

import sys
import time
import socket
import struct
import threading
from pathlib import Path
from datetime import datetime

def inspect_artnet_packets():
    """Inspect raw Art-Net packets using a separate monitor port"""
    print("🔍 RAW ART-NET PACKET INSPECTOR")
    print("=" * 60)
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Monitoring Art-Net traffic from Depence (192.168.1.171)")
    print("=" * 60)
    
    # Use a different port for monitoring to avoid conflict
    monitor_port = 6455
    
    try:
        # Create monitoring socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('0.0.0.0', monitor_port))
        sock.settimeout(2.0)
        
        print(f"✅ Monitor socket bound to port {monitor_port}")
        
        # Also create sender to test loopback
        sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sender_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        print("\n🧪 SENDING LOOPBACK TEST PACKETS...")
        print("-" * 40)
        
        # Send test Art-Net packets to check if our DMX Master receives them
        for universe in [0, 1]:
            # Create Art-Net DMX packet
            header = b'Art-Net\0'
            opcode = struct.pack('<H', 0x5000)  # DMX
            version = struct.pack('<H', 0x000e)
            sequence = struct.pack('B', 0)
            physical = struct.pack('B', 0)
            universe_bytes = struct.pack('<H', universe)
            
            # Create test DMX data
            dmx_data = bytearray(512)
            dmx_data[0] = 255 - (universe * 100)  # Ch1
            dmx_data[1] = 128 + (universe * 50)   # Ch2
            dmx_data[2] = 64 + (universe * 25)    # Ch3
            
            length = struct.pack('>H', len(dmx_data))
            packet = header + opcode + version + sequence + physical + universe_bytes + length + bytes(dmx_data)
            
            # Send to localhost (where DMX Master should be listening)
            sender_sock.sendto(packet, ('127.0.0.1', 6454))
            print(f"📡 Sent test DMX Universe {universe} to localhost:6454")
            print(f"   Ch1={dmx_data[0]}, Ch2={dmx_data[1]}, Ch3={dmx_data[2]}")
            time.sleep(0.5)
        
        sender_sock.close()
        
        print(f"\n💡 CHECK DMX MASTER NOW:")
        print("   1. Open DMX Master LTS")
        print("   2. Go to DMX View tab")
        print("   3. Select Universe 0 and Universe 1")
        print("   4. You should see the test values above")
        print("   5. If you see test values, DMX reception is working!")
        
        print(f"\n📡 MONITORING FOR DEPENCE TRAFFIC...")
        print("   (This monitor won't see DMX Master traffic, but can see other Art-Net)")
        print("   Press Ctrl+C to stop")
        print("-" * 40)
        
        packets_seen = 0
        start_time = time.time()
        
        try:
            while True:
                try:
                    data, addr = sock.recvfrom(4096)
                    packets_seen += 1
                    
                    print(f"📦 Packet #{packets_seen} from {addr[0]}:{addr[1]} ({len(data)} bytes)")
                    
                    # Parse Art-Net if possible
                    if len(data) >= 10 and data[:8] == b'Art-Net\0':
                        opcode = struct.unpack('<H', data[8:10])[0]
                        
                        packet_types = {
                            0x2000: "Poll",
                            0x2100: "PollReply", 
                            0x5000: "DMX",
                            0x9700: "TimeCode"
                        }
                        
                        packet_type = packet_types.get(opcode, f"Unknown(0x{opcode:04x})")
                        print(f"   📋 Art-Net {packet_type} (opcode: 0x{opcode:04x})")
                        
                        if opcode == 0x5000:  # DMX
                            print(f"   🎭 This is a DMX packet! Depence IS sending DMX")
                        elif opcode == 0x9700:  # Timecode
                            print(f"   🎵 This is a Timecode packet")
                            
                    else:
                        print(f"   ❌ Not Art-Net: {data[:8]}")
                    
                    print()
                    
                except socket.timeout:
                    # Show status every 10 seconds
                    elapsed = time.time() - start_time
                    if int(elapsed) % 10 == 0 and elapsed > 5:
                        print(f"⏰ Status: {packets_seen} packets in {elapsed:.0f}s")
                        if packets_seen == 0:
                            print("   💡 No packets on monitor port - this is normal")
                            print("   💡 Main traffic goes to port 6454 (DMX Master)")
                    continue
                    
        except KeyboardInterrupt:
            pass
            
    except Exception as e:
        print(f"❌ Monitor error: {e}")
    finally:
        if 'sock' in locals():
            sock.close()
    
    print(f"\n📊 ANALYSIS:")
    print("=" * 40)
    
    print("🔍 What we learned:")
    print("1. Test packets sent to DMX Master on port 6454")
    print("2. If you saw test values in DMX View, reception is working")
    print("3. If you didn't see test values, there's a DMX Master issue")
    print("4. Monitor on port 6455 saw limited traffic (expected)")
    
    print(f"\n💡 DEPENCE TROUBLESHOOTING:")
    print("If DMX Master shows test packets but not Depence packets:")
    print("1. ✅ DMX Master reception is working")
    print("2. ❌ Depence may not be sending DMX packets")
    print("3. 🔧 Check in Depence:")
    print("   - Hardware Manager → Art-Net enabled?")
    print("   - DMX View → Are faders/channels active?")
    print("   - Does Depence show DMX output activity?")
    print("   - Are fixtures assigned and active?")

def check_depence_configuration():
    """Provide detailed Depence configuration check"""
    print(f"\n🎭 DEPENCE CONFIGURATION CHECKLIST:")
    print("=" * 50)
    
    print("📋 Step 1: Hardware Manager")
    print("   ✅ Art-Net enabled")
    print("   ✅ Target IP: 192.168.1.171")
    print("   ✅ Universes: 0, 1, 2, 3 configured")
    print("   ❓ Is 'DMX Enabled' checkbox checked?")
    
    print(f"\n📋 Step 2: DMX View Tab")
    print("   ❓ Are there active fixtures in Universe 1?")
    print("   ❓ Do faders show non-zero values?")
    print("   ❓ Is timeline/sequence playing?")
    
    print(f"\n📋 Step 3: Fixture Patching")
    print("   ❓ Are fixtures patched to Universe 1?")
    print("   ❓ Are fixtures enabled (not dimmed/disabled)?")
    print("   ❓ Is there an active scene/cue?")
    
    print(f"\n🔧 QUICK TEST:")
    print("1. In Depence, create a simple moving light")
    print("2. Patch it to Universe 1, Channel 1")
    print("3. Set its intensity to 100%")
    print("4. Move some pan/tilt or set colors")
    print("5. Check if DMX Master shows activity")

if __name__ == "__main__":
    print("🔍 ART-NET DIAGNOSTIC TOOL")
    print("Choose test mode:")
    print("1. Raw packet inspector + loopback test (recommended)")
    print("2. Depence configuration checklist")
    
    choice = input("Enter choice (1-2) [1]: ").strip()
    
    if choice == "2":
        check_depence_configuration()
    else:
        inspect_artnet_packets()
        check_depence_configuration()