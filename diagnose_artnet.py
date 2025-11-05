#!/usr/bin/env python3
"""
Simple Art-Net Traffic Sniffer
Monitor Art-Net without binding to port (use different approach)
"""

import sys
import time
import socket
import struct
import threading
from pathlib import Path
from datetime import datetime

def check_port_6454():
    """Check what's using port 6454"""
    print("🔍 Checking port 6454 usage...")
    
    try:
        # Try to bind to see if port is free
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        test_sock.bind(('0.0.0.0', 6454))
        test_sock.close()
        print("✅ Port 6454 is available")
        return True
    except OSError as e:
        print(f"⚠️ Port 6454 is in use: {e}")
        print("💡 This means DMX Master or another Art-Net application is running")
        return False

def test_network_connectivity():
    """Test basic network connectivity"""
    print("\n🌐 Testing Network Connectivity...")
    print("-" * 40)
    
    # Test localhost
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        sock.sendto(b"test", ("127.0.0.1", 9999))  # Dummy port
        print("✅ Localhost (127.0.0.1) reachable")
        sock.close()
    except Exception as e:
        print(f"❌ Localhost issue: {e}")
    
    # Test self IP
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        sock.sendto(b"test", ("192.168.1.171", 9999))  # Dummy port
        print("✅ Self IP (192.168.1.171) reachable")
        sock.close()
    except Exception as e:
        print(f"❌ Self IP issue: {e}")

def send_test_artnet_packets():
    """Send test Art-Net packets to localhost to verify reception"""
    print("\n🧪 Sending Test Art-Net Packets...")
    print("-" * 40)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        for universe in [0, 1, 2, 3]:
            # Create Art-Net DMX packet
            header = b'Art-Net\0'
            opcode = struct.pack('<H', 0x5000)  # DMX
            version = struct.pack('<H', 0x000e)
            sequence = struct.pack('B', 0)
            physical = struct.pack('B', 0)
            universe_bytes = struct.pack('<H', universe)
            
            # Create test DMX data with some active channels
            dmx_data = bytearray(512)
            dmx_data[0] = 255 - (universe * 50)  # Ch1 varies by universe
            dmx_data[1] = 128 + (universe * 30)  # Ch2 varies by universe
            dmx_data[2] = 64 + (universe * 20)   # Ch3 varies by universe
            
            length = struct.pack('>H', len(dmx_data))
            
            packet = header + opcode + version + sequence + physical + universe_bytes + length + bytes(dmx_data)
            
            # Send to localhost
            sock.sendto(packet, ('127.0.0.1', 6454))
            print(f"📡 Sent test Universe {universe}: Ch1={dmx_data[0]}, Ch2={dmx_data[1]}, Ch3={dmx_data[2]}")
            time.sleep(0.5)
        
        sock.close()
        print("✅ Test packets sent successfully")
        
    except Exception as e:
        print(f"❌ Failed to send test packets: {e}")

def check_dmx_master_logs():
    """Check if DMX Master is logging received packets"""
    print("\n📋 Checking DMX Master Logs...")
    print("-" * 40)
    
    log_paths = [
        Path.home() / "AppData/Local/DMX Master LTS/logs/artnet_controller.log",
        Path("logs/artnet_controller.log"),
        Path("data/logs/artnet_controller.log")
    ]
    
    for log_path in log_paths:
        if log_path.exists():
            print(f"📄 Found log: {log_path}")
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # Show last 10 lines
                print("📋 Last 10 log entries:")
                for line in lines[-10:]:
                    line = line.strip()
                    if line:
                        print(f"   {line}")
                return True
            except Exception as e:
                print(f"❌ Could not read log: {e}")
        else:
            print(f"❌ Log not found: {log_path}")
    
    return False

def check_windows_firewall():
    """Check Windows Firewall status for port 6454"""
    print("\n🔥 Windows Firewall Check...")
    print("-" * 40)
    
    import subprocess
    
    try:
        # Check if port 6454 is allowed
        result = subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'show', 'rule', 
            'name=all', 'dir=in', 'protocol=udp', 'localport=6454'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout:
            print("✅ Firewall rules found for port 6454:")
            print(result.stdout)
        else:
            print("⚠️ No specific firewall rules for port 6454")
            print("💡 This might be blocking Art-Net traffic")
            
    except Exception as e:
        print(f"❌ Could not check firewall: {e}")

def monitor_with_different_port():
    """Monitor Art-Net by listening on a different port and using broadcast"""
    print("\n📡 Alternative Monitoring (Broadcast Detection)...")
    print("-" * 40)
    
    try:
        # Listen on broadcast port
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', 6455))  # Different port
        sock.settimeout(5.0)
        
        print("✅ Listening on port 6455 for broadcast traffic...")
        print("⏰ Monitoring for 15 seconds...")
        
        start_time = time.time()
        packets = 0
        
        while time.time() - start_time < 15:
            try:
                data, addr = sock.recvfrom(4096)
                packets += 1
                print(f"📦 Packet #{packets} from {addr[0]}:{addr[1]} ({len(data)} bytes)")
                
                # Check if it looks like Art-Net
                if len(data) >= 8 and data[:8] == b'Art-Net\0':
                    print(f"   ✅ Art-Net packet detected!")
                
            except socket.timeout:
                continue
                
        sock.close()
        
        if packets == 0:
            print("❌ No broadcast traffic detected")
        else:
            print(f"✅ Detected {packets} packets")
            
    except Exception as e:
        print(f"❌ Broadcast monitoring failed: {e}")

def main():
    print("🔍 COMPREHENSIVE ART-NET DIAGNOSTICS")
    print("=" * 60)
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️ Local IP: 192.168.1.171")
    print("=" * 60)
    
    # Step 1: Check port usage
    port_free = check_port_6454()
    
    # Step 2: Test network
    test_network_connectivity()
    
    # Step 3: Check firewall
    check_windows_firewall()
    
    # Step 4: Send test packets (if DMX Master is running)
    if not port_free:
        print("\n💡 DMX Master appears to be running...")
        send_test_artnet_packets()
        
        # Give time for processing
        time.sleep(2)
        
        # Check logs
        check_dmx_master_logs()
    
    # Step 5: Alternative monitoring
    monitor_with_different_port()
    
    # Summary and recommendations
    print(f"\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if not port_free:
        print("✅ DMX Master LTS appears to be running (port 6454 in use)")
        print("💡 Recommendations:")
        print("   1. Check DMX View tab in DMX Master for received data")
        print("   2. Ensure Depence is sending DMX (faders active)")
        print("   3. Try moving some faders in Depence Universe 1")
        print("   4. Check that DMX Master is showing Universe 0")
    else:
        print("⚠️ Port 6454 is free - DMX Master may not be running")
        print("💡 Recommendations:")
        print("   1. Start DMX Master LTS v1.0.2")
        print("   2. Check Art-Net controller status")
        print("   3. Then test again")
    
    print(f"\n🎯 DEPENCE CONFIGURATION REMINDER:")
    print("   📡 Target IP: 192.168.1.171")
    print("   🌍 Universe: 1 (shows as Universe 0 in DMX Master)")
    print("   📊 Expected data in DMX Master Universe 0")

if __name__ == "__main__":
    main()