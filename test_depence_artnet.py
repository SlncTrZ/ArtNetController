#!/usr/bin/env python3
"""
Depence Art-Net Diagnostic Tool
Debug Art-Net communication between Depence (192.168.1.171) and DMX Master (192.168.1.227)
"""

import sys
import time
import socket
import struct
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.artnet.controller import ArtNetController

class DepenceArtNetDiagnostic:
    def __init__(self):
        self.depence_ip = "192.168.1.171"
        self.dmx_master_ip = "192.168.1.227"
        self.packet_count = 0
        self.dmx_packet_count = 0
        self.universe_data = {}
        self.artnet_controller = None
        
    def start_diagnostic(self):
        print("🔍 Depence Art-Net Diagnostic Tool")
        print("=" * 50)
        print(f"📡 Depence IP: {self.depence_ip}")
        print(f"🖥️ DMX Master IP: {self.dmx_master_ip}")
        print("=" * 50)
        
        # Start Art-Net controller with detailed logging
        self.artnet_controller = ArtNetController()
        
        # Set up DMX callback
        def on_dmx_received(universe: int, dmx_data: bytes, source_ip: str):
            self.dmx_packet_count += 1
            self.universe_data[universe] = dmx_data
            
            # Count non-zero channels
            non_zero_channels = []
            for i, value in enumerate(dmx_data):
                if value > 0:
                    non_zero_channels.append((i+1, value))
            
            print(f"📥 DMX #{self.dmx_packet_count}: Universe {universe} from {source_ip}")
            print(f"   📊 Packet length: {len(dmx_data)} bytes")
            print(f"   🔥 Active channels: {len(non_zero_channels)}")
            
            if non_zero_channels:
                # Show first 20 active channels
                active_display = ", ".join([f"Ch{ch}:{val}" for ch, val in non_zero_channels[:20]])
                if len(non_zero_channels) > 20:
                    active_display += f" ... (+{len(non_zero_channels)-20} more)"
                print(f"   💡 Active: {active_display}")
            else:
                print(f"   ❌ All channels are 0")
            
            # Special attention to first 10 channels
            first_10 = list(dmx_data[:10])
            print(f"   🎯 Ch1-10: {first_10}")
            print()
        
        self.artnet_controller.dmx_received_callback = on_dmx_received
        
        # Start controller
        print("🚀 Starting Art-Net controller...")
        if not self.artnet_controller.start():
            print("❌ Failed to start Art-Net controller")
            return False
            
        print("✅ Art-Net controller started")
        print(f"🎧 Listening on port 6454 for Art-Net packets")
        print()
        
        return True
    
    def run_packet_monitor(self):
        """Monitor raw Art-Net packets"""
        try:
            # Create raw socket to monitor all Art-Net traffic
            monitor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            monitor_socket.bind(('0.0.0.0', 6454))
            monitor_socket.settimeout(1.0)
            
            print("📡 Raw packet monitor started...")
            
            while True:
                try:
                    data, addr = monitor_socket.recvfrom(1024)
                    self.packet_count += 1
                    
                    # Parse Art-Net header
                    if len(data) >= 10 and data[:8] == b'Art-Net\0':
                        opcode = struct.unpack('<H', data[8:10])[0]
                        
                        packet_types = {
                            0x2000: "Poll",
                            0x2100: "PollReply", 
                            0x5000: "DMX",
                            0x9700: "TimeCode"
                        }
                        
                        packet_type = packet_types.get(opcode, f"Unknown(0x{opcode:04x})")
                        
                        print(f"📦 Packet #{self.packet_count}: {packet_type} from {addr[0]}:{addr[1]} ({len(data)} bytes)")
                        
                        if opcode == 0x5000:  # DMX packet
                            if len(data) >= 18:
                                universe = struct.unpack('<H', data[14:16])[0]
                                dmx_length = struct.unpack('>H', data[16:18])[0]
                                print(f"   🎭 DMX Universe: {universe}, Length: {dmx_length}")
                                
                                if len(data) >= 18 + dmx_length:
                                    dmx_data = data[18:18+dmx_length]
                                    non_zero = sum(1 for b in dmx_data if b > 0)
                                    print(f"   💡 Non-zero channels: {non_zero}/{dmx_length}")
                        
                        # Special handling for Depence
                        if addr[0] == self.depence_ip:
                            print(f"   ⭐ FROM DEPENCE: {packet_type}")
                            
                except socket.timeout:
                    continue
                except KeyboardInterrupt:
                    break
                    
        except Exception as e:
            print(f"❌ Monitor error: {e}")
    
    def show_network_info(self):
        """Show network configuration"""
        print("\n🌐 Network Information:")
        print("-" * 30)
        
        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            print(f"🖥️ Local IP: {local_ip}")
            print(f"🎯 Expected Local IP: {self.dmx_master_ip}")
            
            if local_ip != self.dmx_master_ip:
                print(f"⚠️  WARNING: Local IP mismatch!")
                print(f"   Expected: {self.dmx_master_ip}")
                print(f"   Actual: {local_ip}")
            
            # Test connectivity to Depence
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                test_socket.settimeout(2)
                test_socket.sendto(b"test", (self.depence_ip, 6454))
                print(f"✅ Can send to Depence ({self.depence_ip})")
                test_socket.close()
            except Exception as e:
                print(f"❌ Cannot reach Depence: {e}")
                
        except Exception as e:
            print(f"❌ Network check failed: {e}")
    
    def run(self):
        """Run the diagnostic"""
        try:
            # Show network info
            self.show_network_info()
            
            # Start Art-Net controller
            if not self.start_diagnostic():
                return
            
            print("🎭 DEPENCE TESTING INSTRUCTIONS:")
            print("-" * 40)
            print("1. In Depence on 192.168.1.171:")
            print("   - Go to Interfaces > Art-Net")
            print("   - Enable Art-Net output")
            print("   - Set target IP to 192.168.1.227 (this machine)")
            print("   - Or use broadcast: 255.255.255.255")
            print("   - Set Universe to 1 (will appear as Universe 0 in DMX Master)")
            print("   ⚠️  NOTE: Depence starts from Universe 1, not 0!")
            print("2. Move some faders or start playback")
            print("3. You should see DMX packets below")
            print("4. Press Ctrl+C to stop")
            print("-" * 40)
            print()
            
            # Monitor packets
            start_time = time.time()
            
            try:
                while True:
                    time.sleep(5)
                    elapsed = time.time() - start_time
                    
                    print(f"⏰ Status after {elapsed:.0f}s:")
                    print(f"   📦 Total packets: {self.packet_count}")
                    print(f"   🎭 DMX packets: {self.dmx_packet_count}")
                    print(f"   🌍 Universes seen: {list(self.universe_data.keys())}")
                    
                    if self.dmx_packet_count == 0:
                        print("   ⚠️  No DMX packets received from Depence")
                        print("   💡 Check Depence Art-Net settings:")
                        print("      - Art-Net output enabled?")
                        print("      - Target IP set to 192.168.1.227?")
                        print("      - DMX output active (faders up)?")
                    else:
                        print(f"   ✅ Receiving DMX from Depence!")
                        
                        # Show current universe data
                        for universe, data in self.universe_data.items():
                            non_zero = [(i+1, val) for i, val in enumerate(data[:10]) if val > 0]
                            if non_zero:
                                print(f"   🎯 Universe {universe} Ch1-10: {non_zero}")
                    
                    print()
                    
            except KeyboardInterrupt:
                print("\n🛑 Diagnostic stopped by user")
            
            # Final summary
            print(f"\n📊 FINAL RESULTS:")
            print(f"   📦 Total packets received: {self.packet_count}")
            print(f"   🎭 DMX packets received: {self.dmx_packet_count}")
            print(f"   🌍 Universes with data: {len(self.universe_data)}")
            
            if self.dmx_packet_count > 0:
                print("✅ Art-Net communication is working!")
                print("💡 If DMX View tab still shows limited data,")
                print("   the issue may be in the GUI update mechanism.")
            else:
                print("❌ No DMX packets received from Depence")
                print("🔧 Troubleshooting recommendations:")
                print("   1. Check Depence Art-Net output settings")
                print("   2. Verify network connectivity (ping 192.168.1.171)")
                print("   3. Check Windows Firewall on both machines")
                print("   4. Try broadcast IP in Depence (255.255.255.255)")
            
        except Exception as e:
            print(f"❌ Diagnostic failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.artnet_controller:
                print("\n🧹 Stopping Art-Net controller...")
                self.artnet_controller.stop()

if __name__ == "__main__":
    diagnostic = DepenceArtNetDiagnostic()
    diagnostic.run()