#!/usr/bin/env python3
"""
Art-Net Packet Monitor
Monitor real-time Art-Net packets on port 6454
"""

import socket
import struct
import time
import threading
from datetime import datetime

class ArtNetMonitor:
    def __init__(self, port=6454):
        self.port = port
        self.socket = None
        self.running = False
        self.packet_count = 0
        
    def start_monitoring(self):
        """Start monitoring Art-Net packets"""
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.settimeout(1.0)
            
            # Bind to all interfaces
            self.socket.bind(('0.0.0.0', self.port))
            
            print(f"🎯 Art-Net Monitor listening on port {self.port}")
            print("📡 Waiting for packets... (Press Ctrl+C to stop)")
            print("-" * 60)
            
            self.running = True
            
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(4096)
                    self.process_packet(data, addr)
                    
                except socket.timeout:
                    continue
                except KeyboardInterrupt:
                    print("\n🛑 Monitoring stopped by user")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
                    
        except Exception as e:
            print(f"❌ Failed to start monitor: {e}")
            if "Address already in use" in str(e):
                print("💡 Port 6454 is already in use (probably by Art-Net Controller)")
                print("   This is normal - the app is running and listening")
        finally:
            if self.socket:
                self.socket.close()
    
    def process_packet(self, data, addr):
        """Process received packet"""
        self.packet_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Basic Art-Net header check
        if len(data) < 12:
            print(f"{timestamp} | {addr[0]}:{addr[1]} | Invalid packet (too short)")
            return
            
        # Check Art-Net header
        if data[:8] != b"Art-Net\x00":
            print(f"{timestamp} | {addr[0]}:{addr[1]} | Non-Art-Net packet")
            return
            
        # Get opcode
        opcode = struct.unpack("<H", data[8:10])[0]
        
        if opcode == 0x5000:  # DMX
            self.process_dmx_packet(data, addr, timestamp)
        elif opcode == 0x2000:  # Poll
            print(f"{timestamp} | {addr[0]}:{addr[1]} | Art-Net Poll")
        elif opcode == 0x2100:  # Poll Reply
            print(f"{timestamp} | {addr[0]}:{addr[1]} | Art-Net Poll Reply")
        else:
            print(f"{timestamp} | {addr[0]}:{addr[1]} | Art-Net OpCode: 0x{opcode:04X}")
    
    def process_dmx_packet(self, data, addr, timestamp):
        """Process DMX packet"""
        if len(data) < 18:
            print(f"{timestamp} | {addr[0]}:{addr[1]} | Invalid DMX packet")
            return
            
        # Parse DMX packet
        sequence = data[12]
        physical = data[13]
        universe = struct.unpack("<H", data[14:16])[0]
        length = struct.unpack(">H", data[16:18])[0]
        
        dmx_data = data[18:18+length] if len(data) >= 18+length else data[18:]
        
        # Show non-zero channels
        non_zero_channels = []
        for i, value in enumerate(dmx_data[:16]):  # Show first 16 channels
            if value > 0:
                non_zero_channels.append(f"Ch{i+1}:{value}")
        
        channels_str = ", ".join(non_zero_channels) if non_zero_channels else "All zero"
        
        print(f"{timestamp} | {addr[0]}:{addr[1]} | 🎭 DMX Universe {universe} | "
              f"Seq:{sequence} | Len:{length} | {channels_str}")

def main():
    print("🎭 Art-Net Packet Monitor")
    print("=" * 40)
    print("This will monitor ALL Art-Net traffic on port 6454")
    print("Perfect for debugging Depence → Art-Net Controller communication")
    print()
    
    # Check if port is available
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        test_socket.bind(('0.0.0.0', 6454))
        test_socket.close()
        print("ℹ️  Port 6454 is free - no Art-Net service running")
        print("   You may need to start Art-Net Controller first")
        print()
    except:
        print("ℹ️  Port 6454 is busy - Art-Net service is running")
        print("   Monitor will fail, but this confirms the service is active")
        print("   Check Art-Net Controller logs instead")
        print()
    
    monitor = ArtNetMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main()