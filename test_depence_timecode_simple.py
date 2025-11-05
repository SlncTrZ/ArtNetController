#!/usr/bin/env python3
"""
Simple test script to check if timecode packets are being received from Depence
Tests both port 6454 (standard Art-Net) and 6455 (alternate)
"""

import socket
import struct
import time
from datetime import datetime

# Art-Net OpCodes
OPCODE_TIMECODE = 0x9700  # Art-Net 4 TimeCode

def parse_artnet_packet(data):
    """Parse Art-Net packet and return type info"""
    if len(data) < 10:
        return None
    
    # Check Art-Net header
    if data[0:8] != b'Art-Net\x00':
        return None
    
    # Get OpCode (little-endian)
    opcode = struct.unpack('<H', data[8:10])[0]
    
    return {
        'opcode': opcode,
        'opcode_hex': f'0x{opcode:04X}',
        'data_len': len(data)
    }

def parse_timecode(data):
    """Parse Art-Net TimeCode packet"""
    if len(data) < 19:
        return None
    
    # TimeCode packet structure:
    # 0-7: "Art-Net\x00"
    # 8-9: OpCode 0x9700
    # 10-11: Protocol version (14)
    # 12: filler
    # 13: filler
    # 14: Frames (0-29)
    # 15: Seconds (0-59)
    # 16: Minutes (0-59)
    # 17: Hours (0-23)
    # 18: Type (0=Film 24fps, 1=EBU 25fps, 2=DF 29.97fps, 3=SMPTE 30fps)
    
    frames = data[14]
    seconds = data[15]
    minutes = data[16]
    hours = data[17]
    tc_type = data[18]
    
    type_names = {
        0: "Film (24fps)",
        1: "EBU (25fps)",
        2: "DF (29.97fps)",
        3: "SMPTE (30fps)"
    }
    
    return {
        'time': f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}",
        'type': type_names.get(tc_type, f"Unknown ({tc_type})")
    }

def monitor_port(port, duration=30):
    """Monitor a specific port for Art-Net packets"""
    print(f"\n{'='*70}")
    print(f"Monitoring UDP port {port} for {duration} seconds...")
    print(f"{'='*70}\n")
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind(('0.0.0.0', port))
        sock.settimeout(1.0)  # 1 second timeout
        
        start_time = time.time()
        packet_count = 0
        timecode_count = 0
        dmx_count = 0
        other_count = 0
        last_timecode = None
        
        print(f"✅ Successfully bound to port {port}")
        print(f"⏰ Waiting for packets... (Press Ctrl+C to stop)\n")
        
        while (time.time() - start_time) < duration:
            try:
                data, addr = sock.recvfrom(1024)
                packet_count += 1
                
                # Parse packet
                packet_info = parse_artnet_packet(data)
                
                if packet_info:
                    if packet_info['opcode'] == OPCODE_TIMECODE:
                        timecode_count += 1
                        tc_info = parse_timecode(data)
                        
                        # Only print if timecode changed
                        if tc_info and tc_info != last_timecode:
                            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            print(f"🎵 [{timestamp}] TIMECODE from {addr[0]}: {tc_info['time']} ({tc_info['type']})")
                            last_timecode = tc_info
                    
                    elif packet_info['opcode'] == 0x5000:  # DMX
                        dmx_count += 1
                        if dmx_count == 1:
                            print(f"📦 First DMX packet received from {addr[0]}")
                    
                    elif packet_info['opcode'] == 0x2000:  # Poll
                        pass  # Ignore Poll packets
                    
                    else:
                        other_count += 1
                        if other_count <= 3:
                            print(f"📨 Other Art-Net packet: OpCode={packet_info['opcode_hex']} from {addr[0]}")
                
            except socket.timeout:
                # No packet received in 1 second
                continue
            except Exception as e:
                print(f"❌ Error processing packet: {e}")
        
        # Summary
        print(f"\n{'='*70}")
        print(f"SUMMARY for port {port}:")
        print(f"{'='*70}")
        print(f"Total packets received: {packet_count}")
        print(f"  - TimeCode packets: {timecode_count}")
        print(f"  - DMX packets: {dmx_count}")
        print(f"  - Other packets: {other_count}")
        
        if timecode_count > 0:
            print(f"\n✅ SUCCESS: Timecode is being received on port {port}!")
            if last_timecode:
                print(f"   Last timecode: {last_timecode['time']} ({last_timecode['type']})")
        else:
            print(f"\n⚠️  WARNING: No timecode packets received on port {port}")
        
    except Exception as e:
        print(f"❌ Error binding to port {port}: {e}")
    finally:
        sock.close()

def main():
    """Main test function"""
    print("\n" + "="*70)
    print("DEPENCE TIMECODE TEST SCRIPT")
    print("="*70)
    print("\nThis script will monitor Art-Net ports for timecode packets")
    print("Make sure Depence is running and sending timecode!\n")
    
    print("Testing configuration:")
    print("  - Depence IP: 192.168.1.171 (expected)")
    print("  - Test duration: 30 seconds per port")
    print("  - Ports to test: 6454 (standard), 6455 (alternate)")
    
    input("\nPress ENTER to start monitoring port 6454...")
    
    try:
        # Test port 6454 (standard Art-Net port)
        monitor_port(6454, duration=30)
        
        print("\n" + "="*70)
        input("\nPress ENTER to test port 6455...")
        
        # Test port 6455 (alternate port)
        monitor_port(6455, duration=30)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. If timecode found on 6454: Use shared socket with main controller")
    print("2. If timecode found on 6455: Current separate receiver should work")
    print("3. If no timecode found: Check Depence timecode output settings")
    print()

if __name__ == "__main__":
    main()
