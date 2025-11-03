#!/usr/bin/env python3
"""
Test Art-Net functionality
"""

import socket
import struct
import time
import sys

def send_artnet_poll():
    """Send Art-Net Poll packet to discover nodes"""
    # Art-Net Poll packet
    packet = bytearray(14)
    packet[0:8] = b"Art-Net\x00"  # Header
    packet[8:10] = struct.pack("<H", 0x2000)  # OpCode Poll
    packet[10:12] = struct.pack(">H", 14)  # Protocol version
    packet[12] = 0x02  # Talk to me flags
    packet[13] = 0x00  # Priority
    
    # Send to broadcast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    try:
        sock.sendto(packet, ('255.255.255.255', 6454))
        print("✓ Sent Art-Net Poll packet")
    except Exception as e:
        print(f"✗ Failed to send Art-Net Poll: {e}")
    finally:
        sock.close()

def send_artnet_dmx(universe=0, data=None):
    """Send Art-Net DMX packet"""
    if data is None:
        # Create test DMX data - all channels at 128 (50%)
        data = [128] * 512
    
    # Art-Net DMX packet
    packet = bytearray(18 + len(data))
    packet[0:8] = b"Art-Net\x00"  # Header
    packet[8:10] = struct.pack("<H", 0x5000)  # OpCode DMX
    packet[10:12] = struct.pack(">H", 14)  # Protocol version
    packet[12] = 0  # Sequence
    packet[13] = 0  # Physical
    packet[14:16] = struct.pack("<H", universe)  # Universe
    packet[16:18] = struct.pack(">H", len(data))  # Length
    packet[18:] = data  # DMX data
    
    # Send to localhost (our application)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        sock.sendto(packet, ('127.0.0.1', 6454))
        print(f"✓ Sent Art-Net DMX packet to universe {universe} with {len(data)} channels")
    except Exception as e:
        print(f"✗ Failed to send Art-Net DMX: {e}")
    finally:
        sock.close()

def main():
    print("=== Art-Net Test Tool ===")
    print("Testing Art-Net functionality with running application...")
    print()
    
    # Test 1: Send Poll packet
    print("1. Testing Art-Net Poll Discovery:")
    send_artnet_poll()
    time.sleep(1)
    
    print()
    
    # Test 2: Send DMX data
    print("2. Testing Art-Net DMX Data:")
    send_artnet_dmx(0, [255, 128, 64, 0] * 128)  # Rainbow pattern
    time.sleep(0.5)
    
    send_artnet_dmx(1, [255] * 16 + [0] * 496)  # Bright channels 1-16
    time.sleep(0.5)
    
    print()
    print("3. Testing continuous DMX stream:")
    for i in range(5):
        # Fade effect
        brightness = int(255 * (i / 4))
        data = [brightness] * 512
        send_artnet_dmx(0, data)
        print(f"   Sent DMX frame {i+1}/5 (brightness: {brightness})")
        time.sleep(0.2)
    
    print()
    print("✓ Art-Net tests completed!")
    print("Check the application's DMX View tab to see received data.")

if __name__ == "__main__":
    main()