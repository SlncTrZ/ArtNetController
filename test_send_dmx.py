"""
Script test gửi DMX data để kiểm tra phần mềm có nhận được không
"""

import socket
import struct
import time

def send_artnet_dmx(universe=0, channel_values=None):
    """Gửi Art-Net DMX packet"""
    
    # Tạo socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Default: All channels at 255 (full brightness)
    if channel_values is None:
        channel_values = [255] * 512
    
    # Ensure exactly 512 channels
    dmx_data = bytes(channel_values[:512] + [0] * (512 - len(channel_values)))
    
    # Build Art-Net DMX packet
    packet = bytearray()
    
    # Header: "Art-Net\x00"
    packet.extend(b"Art-Net\x00")
    
    # OpCode: 0x5000 (ArtDMX) - Little Endian
    packet.extend(struct.pack('<H', 0x5000))
    
    # Protocol version (14)
    packet.extend(struct.pack('>H', 14))
    
    # Sequence (0)
    packet.append(0)
    
    # Physical port (0)
    packet.append(0)
    
    # Universe (Little Endian)
    packet.extend(struct.pack('<H', universe))
    
    # Length (Big Endian) - number of DMX channels
    packet.extend(struct.pack('>H', len(dmx_data)))
    
    # DMX data
    packet.extend(dmx_data)
    
    # Send to localhost and broadcast
    addresses = [
        ('127.0.0.1', 6454),      # Localhost
        ('255.255.255.255', 6454) # Broadcast
    ]
    
    for addr in addresses:
        try:
            sock.sendto(bytes(packet), addr)
            print(f"✅ Sent DMX to {addr[0]}:{addr[1]} - Universe {universe}, {len(dmx_data)} channels")
        except Exception as e:
            print(f"❌ Error sending to {addr}: {e}")
    
    sock.close()

if __name__ == '__main__':
    print("=" * 60)
    print("🎬 TEST SEND DMX DATA")
    print("=" * 60)
    
    # Test 1: Gửi Universe 0 với tất cả channels = 255
    print("\n📤 Test 1: Universe 0 - All channels at 255")
    send_artnet_dmx(universe=0, channel_values=[255] * 512)
    time.sleep(0.5)
    
    # Test 2: Gửi Universe 1 với pattern
    print("\n📤 Test 2: Universe 1 - Pattern (0, 128, 255, ...)")
    pattern = [0, 128, 255] * 170 + [0, 128]  # 512 channels
    send_artnet_dmx(universe=1, channel_values=pattern)
    time.sleep(0.5)
    
    # Test 3: Gửi Universe 2 với channels 1-10 = 255, còn lại = 0
    print("\n📤 Test 3: Universe 2 - First 10 channels at 255")
    test_data = [255] * 10 + [0] * 502
    send_artnet_dmx(universe=2, channel_values=test_data)
    
    print("\n" + "=" * 60)
    print("✅ HOÀN THÀNH! Kiểm tra log của DMX Master để xem có nhận được không")
    print("   Log file: logs/artnet_controller.log")
    print("   Tìm kiếm: 'Received DMX data' hoặc 'RX from'")
    print("=" * 60)
