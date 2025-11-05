#!/usr/bin/env python3
"""
Comprehensive Art-Net Traffic Monitor
Debug all Art-Net communication from Depence and other sources
"""

import sys
import time
import socket
import struct
import threading
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.artnet.controller import ArtNetController
    HAS_CONTROLLER = True
except ImportError:
    print("⚠️ DMX Controller not available, using raw socket monitoring")
    HAS_CONTROLLER = False

class ComprehensiveArtNetMonitor:
    def __init__(self):
        self.running = False
        self.packets_received = 0
        self.dmx_packets = 0
        self.poll_packets = 0
        self.other_packets = 0
        self.universes_seen = set()
        self.sources_seen = set()
        
    def start_raw_monitor(self):
        """Raw socket monitoring for all Art-Net traffic"""
        print("🔍 Starting RAW Art-Net Traffic Monitor")
        print("=" * 60)
        print(f"📡 Monitoring port 6454 on 192.168.1.171")
        print(f"🎯 Looking for traffic from Depence")
        print("=" * 60)
        
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('0.0.0.0', 6454))
            sock.settimeout(1.0)
            
            print("✅ Socket bound to 0.0.0.0:6454")
            print("📡 Listening for Art-Net packets...\n")
            
            self.running = True
            start_time = time.time()
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(4096)
                    self.packets_received += 1
                    
                    # Parse Art-Net header
                    if len(data) >= 10 and data[:8] == b'Art-Net\0':
                        opcode = struct.unpack('<H', data[8:10])[0]
                        
                        packet_type = self._get_packet_type(opcode)
                        source_ip = addr[0]
                        
                        self.sources_seen.add(source_ip)
                        
                        print(f"📦 #{self.packets_received}: {packet_type} from {source_ip}:{addr[1]} ({len(data)} bytes)")
                        
                        if opcode == 0x5000:  # DMX packet
                            self.dmx_packets += 1
                            self._parse_dmx_packet(data, source_ip)
                        elif opcode == 0x2000:  # Poll
                            self.poll_packets += 1
                        elif opcode == 0x2100:  # PollReply
                            print("   📋 PollReply packet")
                        else:
                            self.other_packets += 1
                        
                        # Highlight Depence traffic
                        if source_ip == "192.168.1.171":
                            print(f"   ⭐ FROM DEPENCE! ⭐")
                        
                        print()
                        
                    else:
                        print(f"❌ Non-Art-Net packet from {addr[0]} ({len(data)} bytes)")
                        if len(data) >= 8:
                            print(f"   Header: {data[:8]}")
                        print()
                        
                except socket.timeout:
                    # Show status every 10 seconds
                    elapsed = time.time() - start_time
                    if int(elapsed) % 10 == 0 and elapsed > 1:
                        self._show_status(elapsed)
                    continue
                except KeyboardInterrupt:
                    break
                    
        except Exception as e:
            print(f"❌ Monitor error: {e}")
        finally:
            if 'sock' in locals():
                sock.close()
            self.running = False
            
    def _get_packet_type(self, opcode):
        """Get packet type name from opcode"""
        packet_types = {
            0x2000: "Poll",
            0x2100: "PollReply", 
            0x5000: "DMX",
            0x9700: "TimeCode",
            0x8000: "TimeSync",
            0x2200: "Address",
            0x2300: "Input",
            0x2400: "TodRequest",
            0x2500: "TodData",
            0x2600: "TodControl",
            0x2700: "Rdm",
            0x2800: "RdmSub"
        }
        return packet_types.get(opcode, f"Unknown(0x{opcode:04x})")
    
    def _parse_dmx_packet(self, data, source_ip):
        """Parse DMX packet details"""
        try:
            if len(data) >= 18:
                # Skip Art-Net header (8) + opcode (2) = 10
                payload = data[10:]
                
                version = struct.unpack('<H', payload[0:2])[0]
                sequence = payload[2]
                physical = payload[3]
                universe = struct.unpack('<H', payload[4:6])[0]
                length = struct.unpack('>H', payload[6:8])[0]
                
                self.universes_seen.add(universe)
                
                print(f"   🎭 DMX Details:")
                print(f"      Universe: {universe}")
                print(f"      Length: {length} channels")
                print(f"      Sequence: {sequence}")
                
                if len(payload) >= 8 + length:
                    dmx_data = payload[8:8+length]
                    
                    # Count non-zero channels
                    non_zero = [(i+1, val) for i, val in enumerate(dmx_data[:20]) if val > 0]
                    
                    if non_zero:
                        print(f"      🔥 Active channels (first 20): {non_zero}")
                    else:
                        print(f"      ❌ All channels are 0")
                        
                    # Show first 10 channels always
                    first_10 = [dmx_data[i] if i < len(dmx_data) else 0 for i in range(10)]
                    print(f"      📊 Ch1-10: {first_10}")
                else:
                    print(f"      ⚠️ Packet too short for DMX data")
                    
        except Exception as e:
            print(f"   ❌ DMX parse error: {e}")
    
    def _show_status(self, elapsed):
        """Show periodic status"""
        print(f"⏰ Status after {elapsed:.0f}s:")
        print(f"   📦 Total packets: {self.packets_received}")
        print(f"   🎭 DMX packets: {self.dmx_packets}")
        print(f"   📋 Poll packets: {self.poll_packets}")
        print(f"   🔄 Other packets: {self.other_packets}")
        print(f"   🌍 Universes seen: {sorted(self.universes_seen)}")
        print(f"   📡 Sources: {sorted(self.sources_seen)}")
        
        if not self.sources_seen:
            print("   ⚠️ No Art-Net traffic detected")
            print("   💡 Check if Depence Art-Net output is enabled")
        elif "192.168.1.171" not in self.sources_seen:
            print("   ⚠️ No traffic from Depence (192.168.1.171)")
            print("   💡 Check Depence Art-Net IP setting")
        
        print()
    
    def start_controller_monitor(self):
        """Monitor using DMX Master controller"""
        if not HAS_CONTROLLER:
            print("❌ Controller not available")
            return
            
        print("🎛️ Starting DMX Master Controller Monitor")
        print("=" * 60)
        
        controller = ArtNetController()
        
        def on_dmx_received(universe: int, dmx_data: bytes, source_ip: str):
            self.dmx_packets += 1
            self.universes_seen.add(universe)
            self.sources_seen.add(source_ip)
            
            print(f"✅ DMX #{self.dmx_packets}: Universe {universe} from {source_ip}")
            print(f"   📊 Data length: {len(dmx_data)} bytes")
            
            # Show active channels
            non_zero = [(i+1, val) for i, val in enumerate(dmx_data[:20]) if val > 0]
            if non_zero:
                print(f"   🔥 Active: {non_zero}")
            else:
                print(f"   ❌ All zero")
            
            # Highlight Depence
            if source_ip == "192.168.1.171":
                print(f"   ⭐ FROM DEPENCE! ⭐")
            print()
        
        controller.dmx_received_callback = on_dmx_received
        
        if controller.start():
            print("✅ Controller started successfully")
            
            try:
                while True:
                    time.sleep(10)
                    print(f"⏰ Status: {self.dmx_packets} DMX packets, universes: {sorted(self.universes_seen)}")
                    
            except KeyboardInterrupt:
                pass
            finally:
                controller.stop()
        else:
            print("❌ Failed to start controller")
    
    def run_comprehensive_test(self):
        """Run both raw and controller monitoring"""
        print("🔬 COMPREHENSIVE ART-NET TRAFFIC ANALYSIS")
        print("=" * 80)
        print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🖥️ Local IP: 192.168.1.171")
        print(f"🎭 Expected Depence traffic from: 192.168.1.171")
        print(f"🌍 Expected universes: 0, 1, 2, 3 (based on Depence config)")
        print("=" * 80)
        print()
        
        # Test 1: Raw monitoring
        print("📡 TEST 1: RAW SOCKET MONITORING (30 seconds)")
        print("-" * 50)
        
        try:
            # Run raw monitor in thread
            monitor_thread = threading.Thread(target=self.start_raw_monitor)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            time.sleep(30)
            self.running = False
            
        except KeyboardInterrupt:
            self.running = False
        
        print(f"\n📊 RAW MONITOR RESULTS:")
        print(f"   📦 Total packets: {self.packets_received}")
        print(f"   🎭 DMX packets: {self.dmx_packets}")
        print(f"   🌍 Universes: {sorted(self.universes_seen)}")
        print(f"   📡 Sources: {sorted(self.sources_seen)}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if self.packets_received == 0:
            print("❌ No Art-Net traffic detected at all")
            print("🔧 Check:")
            print("   1. Windows Firewall blocking port 6454")
            print("   2. Depence Art-Net output disabled")
            print("   3. Network connectivity issues")
        elif self.dmx_packets == 0:
            print("⚠️ Art-Net traffic detected but no DMX packets")
            print("🔧 Check:")
            print("   1. Depence DMX output enabled")
            print("   2. Faders/sequences active in Depence")
        elif "192.168.1.171" not in self.sources_seen:
            print("⚠️ Art-Net detected but not from Depence")
            print(f"🔧 Sources seen: {sorted(self.sources_seen)}")
            print("   Check Depence IP configuration")
        else:
            print("✅ Art-Net communication working!")
            print(f"   Universes received: {sorted(self.universes_seen)}")

if __name__ == "__main__":
    monitor = ComprehensiveArtNetMonitor()
    
    print("🔍 Art-Net Traffic Monitor")
    print("Choose monitoring mode:")
    print("1. Raw socket monitoring (detects all traffic)")
    print("2. DMX Master controller monitoring")
    print("3. Comprehensive test (recommended)")
    
    choice = input("Enter choice (1-3) [3]: ").strip()
    
    if choice == "1":
        monitor.start_raw_monitor()
    elif choice == "2":
        monitor.start_controller_monitor()
    else:
        monitor.run_comprehensive_test()