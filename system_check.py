#!/usr/bin/env python3
"""
Comprehensive Art-Net System Check
Kiểm tra toàn diện hệ thống Art-Net Controller
"""

import socket
import struct
import time
import subprocess
import sys
import os
from datetime import datetime

class SystemChecker:
    def __init__(self):
        self.results = {}
        self.issues = []
        self.recommendations = []
    
    def check_1_processes(self):
        """Check 1: Kiểm tra processes đang chạy"""
        print("🔍 CHECK 1: Process Status")
        print("-" * 30)
        
        try:
            # Check Art-Net Controller process
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, shell=True)
            output = result.stdout
            
            art_net_processes = [line for line in output.split('\n') if ':6454' in line and 'UDP' in line]
            webserver_processes = [line for line in output.split('\n') if ':8080' in line and 'TCP' in line]
            
            print(f"Art-Net (port 6454): {len(art_net_processes)} processes")
            for proc in art_net_processes:
                print(f"  {proc.strip()}")
            
            print(f"Webserver (port 8080): {len(webserver_processes)} processes")
            for proc in webserver_processes:
                print(f"  {proc.strip()}")
            
            self.results['artnet_running'] = len(art_net_processes) > 0
            self.results['webserver_running'] = len(webserver_processes) > 0
            
            if not self.results['artnet_running']:
                self.issues.append("❌ Art-Net Controller not listening on port 6454")
                self.recommendations.append("Start Art-Net Controller application")
            else:
                print("✅ Art-Net Controller is running")
            
            if not self.results['webserver_running']:
                self.issues.append("❌ Webserver not running on port 8080")
            else:
                print("✅ Webserver is running")
                
        except Exception as e:
            print(f"❌ Error checking processes: {e}")
            self.issues.append(f"Error checking processes: {e}")
    
    def check_2_network_connectivity(self):
        """Check 2: Test network connectivity"""
        print("\n🌐 CHECK 2: Network Connectivity")
        print("-" * 35)
        
        # Test localhost ping
        try:
            result = subprocess.run(['ping', '-n', '1', '127.0.0.1'], 
                                  capture_output=True, text=True, timeout=5)
            localhost_ok = result.returncode == 0
            print(f"Localhost ping: {'✅' if localhost_ok else '❌'}")
            self.results['localhost_ping'] = localhost_ok
        except:
            print("Localhost ping: ❌")
            self.results['localhost_ping'] = False
        
        # Test actual IP ping
        try:
            result = subprocess.run(['ping', '-n', '1', '192.168.1.171'], 
                                  capture_output=True, text=True, timeout=5)
            ip_ping_ok = result.returncode == 0
            print(f"IP 192.168.1.171 ping: {'✅' if ip_ping_ok else '❌'}")
            self.results['ip_ping'] = ip_ping_ok
        except:
            print("IP 192.168.1.171 ping: ❌")
            self.results['ip_ping'] = False
    
    def check_3_port_binding(self):
        """Check 3: Test port binding"""
        print("\n🔌 CHECK 3: Port Binding Test")
        print("-" * 30)
        
        # Test Art-Net port
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_socket.bind(('127.0.0.1', 6455))  # Test nearby port
            test_socket.close()
            print("✅ UDP binding capability: OK")
            self.results['udp_binding'] = True
        except Exception as e:
            print(f"❌ UDP binding test failed: {e}")
            self.results['udp_binding'] = False
            self.issues.append(f"UDP binding issue: {e}")
        
        # Check if 6454 is specifically busy
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_socket.bind(('0.0.0.0', 6454))
            test_socket.close()
            print("⚠️  Port 6454 is FREE (should be busy if Art-Net running)")
            self.results['port_6454_free'] = True
        except:
            print("✅ Port 6454 is BUSY (Art-Net Controller is using it)")
            self.results['port_6454_free'] = False
    
    def check_4_send_test_packet(self):
        """Check 4: Send test Art-Net packet"""
        print("\n📤 CHECK 4: Send Test Art-Net Packet")
        print("-" * 38)
        
        # Create Art-Net DMX packet
        packet = bytearray(18 + 512)
        packet[0:8] = b"Art-Net\x00"  # Header
        packet[8:10] = struct.pack("<H", 0x5000)  # OpCode DMX
        packet[10:12] = struct.pack(">H", 14)  # Protocol version
        packet[12] = 1  # Sequence
        packet[13] = 0  # Physical
        packet[14:16] = struct.pack("<H", 0)  # Universe 0
        packet[16:18] = struct.pack(">H", 512)  # Length
        
        # Fill with test pattern
        for i in range(512):
            packet[18 + i] = min(255, i % 128 + 100)  # Test pattern
        
        # Test sending to different addresses
        addresses = [
            ('127.0.0.1', 6454, 'Localhost'),
            ('192.168.1.171', 6454, 'Actual IP')
        ]
        
        for ip, port, desc in addresses:
            try:
                sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sender.settimeout(2.0)
                sender.sendto(packet, (ip, port))
                sender.close()
                print(f"✅ Test packet sent to {desc} ({ip}:{port})")
                self.results[f'send_to_{ip}'] = True
            except Exception as e:
                print(f"❌ Failed to send to {desc} ({ip}:{port}): {e}")
                self.results[f'send_to_{ip}'] = False
                self.issues.append(f"Cannot send to {ip}:{port} - {e}")
    
    def check_5_firewall_status(self):
        """Check 5: Windows Firewall status"""
        print("\n🛡️ CHECK 5: Windows Firewall")
        print("-" * 28)
        
        try:
            # Check firewall status
            result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles', 'state'], 
                                  capture_output=True, text=True)
            
            if 'ON' in result.stdout:
                print("⚠️  Windows Firewall is ON")
                print("   This may block Art-Net traffic")
                self.recommendations.append("Check Windows Firewall settings for Python/Art-Net")
            else:
                print("✅ Windows Firewall appears to be OFF")
            
        except Exception as e:
            print(f"ℹ️  Could not check firewall status: {e}")
    
    def check_6_artnet_controller_logs(self):
        """Check 6: Try to connect to Art-Net Controller"""
        print("\n📋 CHECK 6: Art-Net Controller Communication")
        print("-" * 43)
        
        # Try to create our own listener to see if we can receive
        try:
            listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            listener.settimeout(3.0)
            listener.bind(('0.0.0.0', 6455))  # Use different port
            
            # Send a packet to trigger response
            sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            poll_packet = bytearray(14)
            poll_packet[0:8] = b"Art-Net\x00"
            poll_packet[8:10] = struct.pack("<H", 0x2000)  # Poll
            poll_packet[10:12] = struct.pack(">H", 14)
            poll_packet[12] = 0x02
            poll_packet[13] = 0x00
            
            sender.sendto(poll_packet, ('255.255.255.255', 6454))
            sender.close()
            
            print("📡 Sent Art-Net Poll, waiting for responses...")
            
            start_time = time.time()
            responses = 0
            
            while time.time() - start_time < 3.0:
                try:
                    data, addr = listener.recvfrom(1024)
                    if data[:8] == b"Art-Net\x00":
                        responses += 1
                        print(f"✅ Received Art-Net response from {addr[0]}")
                except socket.timeout:
                    break
            
            listener.close()
            
            if responses > 0:
                print(f"✅ Art-Net network is active ({responses} responses)")
                self.results['artnet_network_active'] = True
            else:
                print("❌ No Art-Net responses received")
                self.results['artnet_network_active'] = False
                self.issues.append("No Art-Net responses to Poll")
                
        except Exception as e:
            print(f"❌ Communication test failed: {e}")
            self.results['artnet_network_active'] = False
    
    def print_summary(self):
        """Print comprehensive summary"""
        print("\n" + "="*60)
        print("📊 SYSTEM CHECK SUMMARY")
        print("="*60)
        
        print("\n✅ WORKING:")
        working_items = []
        if self.results.get('artnet_running'): working_items.append("Art-Net Controller process")
        if self.results.get('webserver_running'): working_items.append("Webserver")
        if self.results.get('localhost_ping'): working_items.append("Localhost connectivity")
        if self.results.get('udp_binding'): working_items.append("UDP socket binding")
        if self.results.get('send_to_127.0.0.1'): working_items.append("Send to localhost")
        if self.results.get('send_to_192.168.1.171'): working_items.append("Send to actual IP")
        if self.results.get('artnet_network_active'): working_items.append("Art-Net network communication")
        
        for item in working_items:
            print(f"  • {item}")
        
        if self.issues:
            print("\n❌ ISSUES FOUND:")
            for issue in self.issues:
                print(f"  • {issue}")
        
        if self.recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for rec in self.recommendations:
                print(f"  • {rec}")
        
        print("\n🎯 NEXT STEPS FOR DEPENCE:")
        print("1. Ensure Art-Net Controller is running (should be ✅)")
        print("2. In Depence → Setup → DMX Settings:")
        print("   • Method: Art-Net")
        print("   • Target IP: 127.0.0.1 or 192.168.1.171")
        print("   • Port: 6454")
        print("   • Universe: 0")
        print("   • ✅ Enable the output!")
        print("3. Patch fixtures and use Live mode")
        print("4. Check for 'Art-Net Output Active' in Depence")
        print("5. Monitor Art-Net Controller logs for incoming data")

def main():
    print("🔍 ART-NET CONTROLLER SYSTEM CHECK")
    print("="*50)
    print("Comprehensive check of Art-Net system status")
    print("This will help identify why Depence → Art-Net recording isn't working")
    print()
    
    checker = SystemChecker()
    
    # Run all checks
    checker.check_1_processes()
    checker.check_2_network_connectivity()
    checker.check_3_port_binding()
    checker.check_4_send_test_packet()
    checker.check_5_firewall_status()
    checker.check_6_artnet_controller_logs()
    
    # Print summary
    checker.print_summary()

if __name__ == "__main__":
    main()