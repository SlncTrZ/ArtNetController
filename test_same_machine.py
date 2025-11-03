#!/usr/bin/env python3
"""
Same-Machine Art-Net Test Tool
Test Art-Net communication trên cùng một máy tính
"""

import socket
import struct
import time
import threading
import sys

def check_port_availability(port=6454):
    """Kiểm tra port 6454 có available không"""
    print(f"🔍 Checking port {port} availability...")
    
    # Test UDP binding
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        test_socket.bind(('127.0.0.1', port))
        test_socket.close()
        print(f"✅ Port {port} is available on localhost")
        return True
    except OSError as e:
        print(f"❌ Port {port} is NOT available on localhost: {e}")
        return False

def test_localhost_connectivity():
    """Test localhost UDP connectivity"""
    print("\n🌐 Testing localhost UDP connectivity...")
    
    # Create receiver
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver.settimeout(2.0)
    
    try:
        receiver.bind(('127.0.0.1', 6455))  # Use different port for test
        print("✅ UDP receiver bound to 127.0.0.1:6455")
        
        # Create sender
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Send test message
        test_message = b"Art-Net Test Message"
        sender.sendto(test_message, ('127.0.0.1', 6455))
        print("📤 Sent test message to localhost")
        
        # Try to receive
        data, addr = receiver.recvfrom(1024)
        print(f"📥 Received: {data.decode()} from {addr}")
        print("✅ Localhost UDP communication working!")
        
        sender.close()
        receiver.close()
        return True
        
    except Exception as e:
        print(f"❌ Localhost UDP test failed: {e}")
        receiver.close()
        return False

def send_artnet_to_localhost():
    """Gửi Art-Net DMX packet tới localhost"""
    print("\n🎭 Sending Art-Net DMX to localhost...")
    
    # Create Art-Net DMX packet
    packet = bytearray(18 + 512)  # Header + 512 channels
    packet[0:8] = b"Art-Net\x00"  # Header
    packet[8:10] = struct.pack("<H", 0x5000)  # OpCode DMX
    packet[10:12] = struct.pack(">H", 14)  # Protocol version
    packet[12] = 1  # Sequence
    packet[13] = 0  # Physical
    packet[14:16] = struct.pack("<H", 0)  # Universe 0
    packet[16:18] = struct.pack(">H", 512)  # Length
    
    # Fill with test data
    for i in range(512):
        packet[18 + i] = (i % 256)  # Test pattern
    
    # Send to localhost
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        sender.sendto(packet, ('127.0.0.1', 6454))
        print("✅ Art-Net DMX packet sent to 127.0.0.1:6454")
        
        # Also try with actual IP
        sender.sendto(packet, ('192.168.1.171', 6454))
        print("✅ Art-Net DMX packet sent to 192.168.1.171:6454")
        
        sender.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to send Art-Net: {e}")
        sender.close()
        return False

def check_windows_firewall():
    """Kiểm tra Windows Firewall settings"""
    print("\n🛡️ Windows Firewall Check...")
    print("Manual steps to check:")
    print("1. Windows Security → Firewall & network protection")
    print("2. Allow an app through firewall")
    print("3. Find 'Python' or add if not exists")
    print("4. Enable both Private and Public networks")
    print("5. Or temporarily disable firewall for testing")

def depence_config_guide():
    """Hướng dẫn cấu hình Depence cho same-machine"""
    print("\n🎯 Depence Configuration for Same-Machine:")
    print("=" * 50)
    print("1. Open Depence → Setup → DMX Settings")
    print("2. Art-Net Output Settings:")
    print("   • Method: Art-Net")
    print("   • Target IP: 127.0.0.1  (localhost)")
    print("   • Alternative: 192.168.1.171  (your actual IP)")
    print("   • Port: 6454 (automatic)")
    print("   • Universe: 0 (or as needed)")
    print("3. Enable the output")
    print("4. In Patch window, assign fixtures to DMX channels")
    print("5. Use Live mode to send data")
    print("\n💡 Pro Tips:")
    print("• Try both 127.0.0.1 and 192.168.1.171")
    print("• Check if Depence shows 'Art-Net Output Active'")
    print("• Use Depence's built-in Art-Net monitor")

def main():
    print("🚀 Art-Net Same-Machine Test Tool")
    print("=" * 40)
    
    # Step 1: Check port availability
    port_ok = check_port_availability()
    
    # Step 2: Test localhost connectivity
    localhost_ok = test_localhost_connectivity()
    
    # Step 3: Send Art-Net packets
    if localhost_ok:
        artnet_ok = send_artnet_to_localhost()
    
    # Step 4: Check firewall
    check_windows_firewall()
    
    # Step 5: Show Depence guide
    depence_config_guide()
    
    print("\n📋 Summary:")
    print(f"Port 6454 Available: {'✅' if port_ok else '❌'}")
    print(f"Localhost UDP: {'✅' if localhost_ok else '❌'}")
    print(f"Art-Net Send: {'✅' if artnet_ok else '❌'}")
    
    if not port_ok:
        print("\n⚠️  Port 6454 is busy!")
        print("Solutions:")
        print("1. Close Art-Net Controller temporarily")
        print("2. Use different port in Depence (e.g., 6455)")
        print("3. Or configure one as sender, one as receiver")
    
    print("\n🎯 Next Steps:")
    print("1. Ensure Art-Net Controller is running")
    print("2. Configure Depence with IPs above")
    print("3. Enable Depence Art-Net output")
    print("4. Check Art-Net Controller logs for incoming data")

if __name__ == "__main__":
    main()