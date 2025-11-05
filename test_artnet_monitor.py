#!/usr/bin/env python3
"""
Art-Net Traffic Monitor
Kiểm tra tất cả traffic Art-Net để debug Depence connection

Sẽ hiển thị:
- Art-Net DMX (OpCode 0x2000)
- Art-Net Timecode (OpCode 0x9700) 
- Các Art-Net packets khác
"""

import socket
import struct
import time
from datetime import datetime
from collections import defaultdict

def monitor_artnet_traffic():
    print("🌐 ART-NET TRAFFIC MONITOR")
    print("=" * 60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📡 Monitoring ALL Art-Net traffic on port 6454...")
    print("🎯 Looking for ANY packets from Depence")
    print()
    print("OpCodes to watch for:")
    print("  • 0x2000 = Art-DMX (normal lighting data)")
    print("  • 0x9700 = Art-TimeCode (timecode data)")
    print("  • 0x2100 = Art-Nzs")
    print("  • 0x2200 = Art-Sync")
    print()
    print("🎬 Monitoring...")
    print("-" * 60)
    
    sock = None
    packet_count = 0
    opcode_stats = defaultdict(int)
    source_ips = set()
    last_status_time = time.time()
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', 6454))
        sock.settimeout(1.0)
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                packet_count += 1
                source_ips.add(addr[0])
                current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]  # Include milliseconds
                
                # Check if it's Art-Net
                if len(data) >= 10 and data[:8] == b"Art-Net\x00":
                    # Parse OpCode (little endian)
                    opcode = struct.unpack('<H', data[8:10])[0]
                    opcode_stats[opcode] += 1
                    
                    if opcode == 0x9700:  # Art-TimeCode - This is what we want!
                        if len(data) >= 19:
                            frames = data[14]
                            seconds = data[15]
                            minutes = data[16]
                            hours = data[17]
                            tc_type = data[18]
                            
                            fps_map = {0: 24, 1: 25, 2: 29.97, 3: 30}
                            fps = fps_map.get(tc_type, 25)
                            
                            tc_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
                            print(f"🎭 [{current_time}] ✅ TIMECODE: {tc_str} @ {fps}fps from {addr[0]} (#{packet_count})")
                        else:
                            print(f"🎭 [{current_time}] ⚠️ Short Art-TimeCode packet from {addr[0]} ({len(data)} bytes)")
                    
                    elif opcode == 0x2000:  # Art-DMX
                        if len(data) >= 18:
                            universe = struct.unpack('<H', data[14:16])[0]
                            dmx_length = struct.unpack('>H', data[16:18])[0]
                            print(f"🌈 [{current_time}] Art-DMX: Universe {universe}, {dmx_length} channels from {addr[0]}")
                        else:
                            print(f"🌈 [{current_time}] Short Art-DMX from {addr[0]} ({len(data)} bytes)")
                    
                    elif opcode == 0x2100:  # Art-Nzs
                        print(f"📡 [{current_time}] Art-Nzs from {addr[0]}")
                    
                    elif opcode == 0x2200:  # Art-Sync  
                        print(f"🔄 [{current_time}] Art-Sync from {addr[0]}")
                    
                    else:
                        print(f"🔍 [{current_time}] Art-Net OpCode 0x{opcode:04X} from {addr[0]} ({len(data)} bytes)")
                
                else:
                    print(f"❓ [{current_time}] Non-Art-Net packet from {addr[0]} ({len(data)} bytes)")
                    if len(data) >= 8:
                        print(f"   Header: {data[:8]}")
                
                # Show status every 30 seconds or every 100 packets
                if time.time() - last_status_time > 30 or packet_count % 100 == 0:
                    print_status(packet_count, opcode_stats, source_ips)
                    last_status_time = time.time()
                
            except socket.timeout:
                # No data - print status if it's been a while
                if time.time() - last_status_time > 10:
                    current_time = datetime.now().strftime('%H:%M:%S')
                    print(f"⏰ [{current_time}] No Art-Net traffic... (Total packets: {packet_count})")
                    
                    if packet_count == 0:
                        print("💡 TIP: Make sure Depence is running and Art-Net output is enabled")
                        print("💡 TIP: Check if Depence is sending to correct IP address")
                    
                    last_status_time = time.time()
                
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except KeyboardInterrupt:
        print(f"\n🛑 Monitoring stopped")
        print_final_stats(packet_count, opcode_stats, source_ips)
        
    except Exception as e:
        print(f"❌ Failed to start monitor: {e}")
        
    finally:
        if sock:
            sock.close()
            print("🧹 Socket closed")

def print_status(packet_count, opcode_stats, source_ips):
    """Print current statistics"""
    print()
    print("📊 CURRENT STATUS:")
    print(f"   Total packets: {packet_count}")
    print(f"   Source IPs: {len(source_ips)}")
    if source_ips:
        print(f"   IPs: {', '.join(sorted(source_ips))}")
    
    if opcode_stats:
        print("   OpCode counts:")
        for opcode, count in sorted(opcode_stats.items()):
            opcode_name = get_opcode_name(opcode)
            print(f"     0x{opcode:04X} ({opcode_name}): {count}")
    
    print("-" * 40)

def print_final_stats(packet_count, opcode_stats, source_ips):
    """Print final statistics"""
    print()
    print("📊 FINAL STATISTICS:")
    print(f"   Total Art-Net packets: {packet_count}")
    print(f"   Unique source IPs: {len(source_ips)}")
    
    if source_ips:
        print("   Source IPs:")
        for ip in sorted(source_ips):
            print(f"     • {ip}")
    
    if opcode_stats:
        print("   OpCode breakdown:")
        for opcode, count in sorted(opcode_stats.items()):
            opcode_name = get_opcode_name(opcode) 
            percentage = (count / packet_count) * 100
            print(f"     • 0x{opcode:04X} ({opcode_name}): {count} ({percentage:.1f}%)")
    
    # Check for timecode
    if 0x9700 in opcode_stats:
        print(f"\n✅ SUCCESS: Received {opcode_stats[0x9700]} Art-TimeCode packets!")
        print("   Depence timecode is working!")
    else:
        print(f"\n⚠️  NO TIMECODE: No Art-TimeCode packets received")
        if packet_count > 0:
            print("   Depence is sending Art-Net but not timecode")
            print("   Check Depence timecode settings")
        else:
            print("   No Art-Net traffic at all")
            print("   Check Depence Art-Net output settings")

def get_opcode_name(opcode):
    """Get human-readable OpCode name"""
    opcodes = {
        0x2000: "Art-DMX",
        0x2100: "Art-Nzs", 
        0x2200: "Art-Sync",
        0x9700: "Art-TimeCode",
        0x2001: "Art-Poll",
        0x2001: "Art-PollReply",
    }
    return opcodes.get(opcode, "Unknown")

if __name__ == "__main__":
    monitor_artnet_traffic()