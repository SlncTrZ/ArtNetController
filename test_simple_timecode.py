#!/usr/bin/env python3
"""
Simple Depence Timecode Test - Art-Net 4 Only
Chỉ test nhận Art-Net 4 timecode từ Depence (method chính)

Chạy script này và sau đó:
1. Mở Depence
2. Bật Art-Net Timecode output 
3. Play timeline trong Depence
"""

import socket
import struct
import time
from datetime import datetime

def test_depence_artnet_timecode():
    print("🎭 DEPENCE ART-NET 4 TIMECODE TEST")
    print("=" * 50)
    print(f"Start time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    print("📡 Listening for Art-Net 4 Timecode on port 6454...")
    print("🎯 Looking for OpCode 0x9700 (Art-TimeCode)")
    print()
    print("💡 DEPENCE SETUP:")
    print("   1. Open Depence")
    print("   2. Go to Settings → Output → Art-Net")
    print("   3. Enable 'Art-Net Timecode'")
    print("   4. Set IP to this computer (or broadcast)")
    print("   5. Play timeline in Depence")
    print()
    print("🎬 Waiting for timecode...")
    print("-" * 50)
    
    sock = None
    timecode_count = 0
    last_fps = 0
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', 6454))  # Art-Net port
        sock.settimeout(2.0)  # 2 second timeout
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                
                # Check if it's Art-Net packet
                if len(data) >= 19 and data[:8] == b"Art-Net\x00":
                    # Get OpCode (little endian)
                    opcode = struct.unpack('<H', data[8:10])[0]
                    
                    if opcode == 0x9700:  # Art-TimeCode
                        # Parse timecode
                        frames = data[14]
                        seconds = data[15] 
                        minutes = data[16]
                        hours = data[17]
                        tc_type = data[18]
                        
                        # Get frame rate
                        fps_map = {0: 24, 1: 25, 2: 29.97, 3: 30}
                        fps = fps_map.get(tc_type, 25)
                        
                        timecode_count += 1
                        current_time = datetime.now().strftime('%H:%M:%S')
                        
                        # Format timecode string
                        tc_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
                        
                        # Print with nice formatting
                        print(f"🎭 [{current_time}] ✅ TIMECODE: {tc_str} @ {fps}fps from {addr[0]} (#{timecode_count})")
                        
                        # Show FPS changes
                        if fps != last_fps:
                            print(f"   📊 Frame rate changed: {last_fps} → {fps} fps")
                            last_fps = fps
                        
                    elif opcode == 0x2000:  # Art-DMX (ignore to reduce spam)
                        pass
                    else:
                        # Other Art-Net packets
                        print(f"🌐 Art-Net packet: OpCode 0x{opcode:04X} from {addr[0]}")
                
            except socket.timeout:
                # No data received, print waiting message
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"⏰ [{current_time}] Still waiting for timecode... (received {timecode_count} so far)")
                
                if timecode_count == 0:
                    print("💡 TIP: Make sure Depence Art-Net Timecode is enabled and timeline is playing")
                
            except Exception as e:
                print(f"❌ Error receiving data: {e}")
                
    except KeyboardInterrupt:
        print(f"\n🛑 Test stopped by user")
        print(f"📊 Total timecode messages received: {timecode_count}")
        
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        print("💡 Make sure no other Art-Net software is using port 6454")
        
    finally:
        if sock:
            sock.close()
            print("🧹 Socket closed")

if __name__ == "__main__":
    test_depence_artnet_timecode()