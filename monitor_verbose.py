"""
Verbose Art-Net Monitor - Shows ALL packets (Poll, PollReply, DMX, etc.)
Helps debug why Depence isn't sending DMX
"""

import socket
import struct
import time
from datetime import datetime

def parse_packet(data, addr):
    """Parse and identify Art-Net packet type"""
    
    if len(data) < 10:
        return f"❓ TOO_SHORT ({len(data)} bytes)"
    
    # Check Art-Net header
    if data[:7] != b'Art-Net':
        return f"❌ NOT_ARTNET (header: {data[:7]})"
    
    # Get OpCode (little-endian)
    opcode = struct.unpack('<H', data[8:10])[0]
    
    opcodes = {
        0x2000: "ArtPoll",
        0x2100: "ArtPollReply", 
        0x5000: "ArtDmx",
        0x9700: "ArtTimeCode",
        0x2020: "ArtAddress",
        0x8000: "ArtTrigger",
    }
    
    opcode_name = opcodes.get(opcode, f"Unknown(0x{opcode:04X})")
    
    # Parse based on type
    if opcode == 0x5000:  # ArtDmx
        if len(data) < 18:
            return f"⚠️  {opcode_name} - TOO SHORT"
        
        sequence = data[12]
        physical = data[13]
        universe_low = data[14]
        universe_hi = data[15]
        universe = (universe_hi << 8) | universe_low
        length_hi = data[16]
        length_lo = data[17]
        dmx_length = (length_hi << 8) | length_lo
        
        # Count non-zero channels
        dmx_data = data[18:18+dmx_length]
        non_zero = sum(1 for x in dmx_data if x > 0)
        
        # Show first few non-zero values
        non_zero_values = [(i+1, v) for i, v in enumerate(dmx_data[:50]) if v > 0]
        values_str = str(non_zero_values[:5]) if non_zero_values else "all zeros"
        
        return f"📦 ArtDmx | U{universe:3d} | Seq:{sequence:3d} | Len:{dmx_length:3d} | Active:{non_zero:3d}/512 | {values_str}"
    
    elif opcode == 0x2000:  # ArtPoll
        flags = data[10] if len(data) > 10 else 0
        priority = data[11] if len(data) > 11 else 0
        return f"🔍 ArtPoll | Flags:0x{flags:02X} | Priority:{priority}"
    
    elif opcode == 0x2100:  # ArtPollReply
        if len(data) >= 239:
            ip = '.'.join(str(b) for b in data[10:14])
            port = struct.unpack('<H', data[14:16])[0]
            subnet = data[19]
            num_ports = data[173]
            sw_in = list(data[186:190])
            short_name = data[26:44].rstrip(b'\x00').decode('utf-8', errors='ignore')
            return f"📡 ArtPollReply | IP:{ip}:{port} | SubNet:{subnet} | Ports:{num_ports} | SwIn:{sw_in} | Name:'{short_name}'"
        return f"📡 ArtPollReply | {len(data)} bytes"
    
    elif opcode == 0x9700:  # ArtTimeCode
        return f"🕐 ArtTimeCode"
    
    else:
        return f"📨 {opcode_name} | {len(data)} bytes"


def monitor_verbose():
    """Monitor ALL Art-Net packets with verbose output"""
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', 6454))
    sock.settimeout(5.0)  # 5 second timeout for warnings
    
    print("="*80)
    print("📺 VERBOSE ART-NET MONITOR")
    print("="*80)
    print()
    print("✅ Listening on 0.0.0.0:6454")
    print("📡 Showing ALL Art-Net packets (Poll, DMX, TimeCode, etc.)")
    print("🎯 Looking for DMX from Depence on Universe 0-7")
    print()
    print("Press Ctrl+C to stop...")
    print("="*80)
    print()
    
    # Statistics
    stats = {
        'total': 0,
        'poll': 0,
        'pollreply': 0,
        'dmx': 0,
        'timecode': 0,
        'other': 0,
    }
    
    dmx_universes = set()
    start_time = time.time()
    last_packet_time = time.time()
    
    try:
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                current_time = time.time()
                last_packet_time = current_time
                
                stats['total'] += 1
                
                # Parse packet
                info = parse_packet(data, addr)
                
                # Update stats
                if 'ArtPoll ' in info and 'Reply' not in info:
                    stats['poll'] += 1
                    color = "🔍"
                elif 'ArtPollReply' in info:
                    stats['pollreply'] += 1
                    color = "📡"
                elif 'ArtDmx' in info:
                    stats['dmx'] += 1
                    color = "📦"
                    # Extract universe
                    try:
                        universe = int(info.split('U')[1].split('|')[0].strip())
                        dmx_universes.add(universe)
                    except:
                        pass
                elif 'TimeCode' in info:
                    stats['timecode'] += 1
                    color = "🕐"
                else:
                    stats['other'] += 1
                    color = "📨"
                
                # Print packet info
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] {color} From {addr[0]:15s}:{addr[1]:5d} | {info}")
                
                # Show progress every 10 packets
                if stats['total'] % 10 == 0:
                    elapsed = current_time - start_time
                    print(f"\n📊 Stats: {stats['total']} total | "
                          f"Poll:{stats['poll']} | PollReply:{stats['pollreply']} | "
                          f"DMX:{stats['dmx']} | TimeCode:{stats['timecode']} | "
                          f"Other:{stats['other']} | "
                          f"Elapsed:{elapsed:.1f}s")
                    if dmx_universes:
                        print(f"   🎯 DMX Universes seen: {sorted(dmx_universes)}")
                    print()
                    
            except socket.timeout:
                current_time = time.time()
                idle_time = current_time - last_packet_time
                
                if idle_time > 5:
                    print(f"\n⏳ No packets for {idle_time:.1f}s...")
                    print("   💡 Troubleshooting:")
                    print("      1. Is Depence Art-Net output ACTIVE? (not just enabled)")
                    print("      2. Try moving a fixture in Depence")
                    print("      3. Check if Depence is sending to 192.168.1.171")
                    print("      4. Verify universe mapping in Depence (0-7)")
                    print()
                    last_packet_time = current_time
                    
    except KeyboardInterrupt:
        print("\n")
        print("="*80)
        print("📊 FINAL STATISTICS")
        print("="*80)
        
        elapsed = time.time() - start_time
        print(f"\nTotal runtime: {elapsed:.1f}s")
        print(f"Total packets: {stats['total']}")
        print(f"  • ArtPoll:      {stats['poll']}")
        print(f"  • ArtPollReply: {stats['pollreply']}")
        print(f"  • ArtDmx:       {stats['dmx']}")
        print(f"  • ArtTimeCode:  {stats['timecode']}")
        print(f"  • Other:        {stats['other']}")
        
        if dmx_universes:
            print(f"\n✅ DMX Universes received: {sorted(dmx_universes)}")
        else:
            print(f"\n❌ No DMX data received")
            print("\n💡 Next steps:")
            print("   • Verify Depence sees the node (should show multiple 'DMX Master' nodes)")
            print("   • Check universe assignment in Depence")
            print("   • Ensure fixtures are patched to Universe 0-7")
            print("   • Try broadcast mode instead of unicast")
        
        print("\n✅ Monitor stopped")
        print("="*80)
    
    finally:
        sock.close()


if __name__ == '__main__':
    monitor_verbose()
