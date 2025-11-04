"""
Test Art-Net Reception
"""
import socket
import struct

def test_artnet_receive():
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(('0.0.0.0', 6454))
    
    print(" Listening on 0.0.0.0:6454")
    print(" Send Art-Net to:")
    print("   - 127.0.0.1:6454 (LOCALHOST - KHUYẾN NGHỊ)")
    print("   - 255.255.255.255:6454 (BROADCAST)")
    print("   - 192.168.1.171:6454 (LAN IP - CÓ THỂ KHÔNG HOẠT ĐỘNG)\n")
    
    sock.settimeout(5.0)
    
    try:
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                print(f" RX from {addr[0]}:{addr[1]}, size: {len(data)} bytes")
                
                # Check if Art-Net
                if data[:8] == b'Art-Net\x00':
                    print(f"    Art-Net packet detected!")
                    opcode = struct.unpack('<H', data[8:10])[0]
                    if opcode == 0x5000:  # DMX
                        print(f"    DMX packet")
                else:
                    print(f"    Not Art-Net packet")
                    
            except socket.timeout:
                print(" Waiting for packets... (send from Depence)")
                
    except KeyboardInterrupt:
        print("\n Stopped")
    finally:
        sock.close()

if __name__ == '__main__':
    test_artnet_receive()
