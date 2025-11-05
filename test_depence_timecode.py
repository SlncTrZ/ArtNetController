#!/usr/bin/env python3
"""
Depence Timecode Test Script
Test nhận timecode từ Depence qua Art-Net 4 và các giao thức khác

Hướng dẫn sử dụng:
1. Chạy script này trước
2. Mở Depence 
3. Bật timecode output trong Depence
4. Quan sát output của script

Supported protocols:
- Art-Net 4 Timecode (OpCode 0x9700) - Port 6454  
- MTC (MIDI Time Code) - MIDI devices
- Net-timecode - Port 3040
"""

import sys
import time
import socket
import struct
import threading
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('timecode_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Global variables for monitoring
timecode_count = 0
last_timecode = None
start_time = time.time()

def print_header():
    """Print test header"""
    print("=" * 80)
    print("🎭 DEPENCE TIMECODE TEST SCRIPT")
    print("=" * 80)
    print("📅 Test Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🎯 Purpose: Test timecode reception from Depence")
    print("🌐 Listening on multiple protocols...")
    print("-" * 80)

def test_artnet4_timecode():
    """Test Art-Net 4 Timecode reception (Depence primary method)"""
    print("🎭 [ART-NET 4] Starting Art-Net 4 Timecode receiver...")
    
    sock = None
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', 6454))  # Art-Net standard port
        sock.settimeout(1.0)
        
        print(f"🎭 [ART-NET 4] Listening on UDP port 6454...")
        print(f"🎭 [ART-NET 4] Ready to receive from Depence!")
        print(f"🎯 [ART-NET 4] Looking for OpCode 0x9700 (Art-TimeCode)")
        print()
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                
                # Check Art-Net packet
                if len(data) >= 19 and data[:8] == b"Art-Net\x00":
                    # Parse OpCode (little endian)
                    opcode = struct.unpack('<H', data[8:10])[0]
                    
                    if opcode == 0x9700:  # Art-TimeCode
                        # Parse timecode data
                        frames = data[14]
                        seconds = data[15]
                        minutes = data[16]
                        hours = data[17]
                        timecode_type = data[18]
                        
                        # Decode frame rate
                        fps_map = {0: 24.0, 1: 25.0, 2: 29.97, 3: 30.0}
                        fps = fps_map.get(timecode_type, 25.0)
                        
                        # Format timecode
                        timecode_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
                        
                        global timecode_count, last_timecode
                        timecode_count += 1
                        last_timecode = timecode_str
                        
                        print(f"🎭 [ART-NET 4] ✅ TIMECODE: {timecode_str} @ {fps}fps from {addr[0]} (#{timecode_count})")
                        logger.info(f"Art-Net 4 Timecode: {timecode_str} @ {fps}fps from {addr[0]}")
                        
                    elif opcode == 0x2000:  # Art-DMX
                        # This is normal DMX data, don't spam
                        continue
                    else:
                        print(f"🎭 [ART-NET 4] Other Art-Net packet: OpCode 0x{opcode:04X} from {addr[0]}")
                        
            except socket.timeout:
                # Timeout is normal, just continue
                continue
            except Exception as e:
                print(f"🎭 [ART-NET 4] ❌ Error: {e}")
                
    except Exception as e:
        print(f"🎭 [ART-NET 4] ❌ Failed to start: {e}")
    finally:
        if sock:
            sock.close()

def test_mtc_timecode():
    """Test MTC (MIDI Time Code) reception"""
    print("🎹 [MTC] Starting MTC receiver...")
    
    try:
        import rtmidi
        
        # List available MIDI inputs
        midiin = rtmidi.MidiIn()
        available_ports = midiin.get_ports()
        
        if not available_ports:
            print("🎹 [MTC] ❌ No MIDI input devices found")
            return
            
        print(f"🎹 [MTC] Available MIDI devices:")
        for i, port in enumerate(available_ports):
            print(f"🎹 [MTC]   {i}: {port}")
        
        # Open first available port
        midiin.open_port(0)
        print(f"🎹 [MTC] ✅ Opened: {available_ports[0]}")
        print(f"🎹 [MTC] Listening for MTC messages...")
        print()
        
        def mtc_callback(message, data):
            """Handle MTC message"""
            global timecode_count
            msg, deltatime = message
            
            if len(msg) == 2 and msg[0] == 0xF1:  # MTC Quarter Frame
                timecode_count += 1
                print(f"🎹 [MTC] ✅ MTC Quarter Frame: 0x{msg[1]:02X} (#{timecode_count})")
                logger.info(f"MTC Quarter Frame: 0x{msg[1]:02X}")
        
        midiin.set_callback(mtc_callback)
        
        # Keep running
        while True:
            time.sleep(1)
            
    except ImportError:
        print("🎹 [MTC] ❌ python-rtmidi not installed")
        print("🎹 [MTC] Install with: pip install python-rtmidi")
    except Exception as e:
        print(f"🎹 [MTC] ❌ Error: {e}")

def test_net_timecode():
    """Test Net-timecode reception"""
    print("🌐 [NET-TC] Starting Net-timecode receiver...")
    
    sock = None
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', 3040))  # Net-timecode standard port
        sock.settimeout(1.0)
        
        print(f"🌐 [NET-TC] Listening on UDP port 3040...")
        print(f"🌐 [NET-TC] Ready to receive Net-timecode!")
        print()
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                
                global timecode_count
                timecode_count += 1
                
                # Basic Net-timecode parsing (format varies)
                if len(data) >= 4:
                    print(f"🌐 [NET-TC] ✅ Net-timecode packet from {addr[0]} - {len(data)} bytes (#{timecode_count})")
                    print(f"🌐 [NET-TC] Data: {data[:20].hex()}")
                    logger.info(f"Net-timecode from {addr[0]}: {len(data)} bytes")
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"🌐 [NET-TC] ❌ Error: {e}")
                
    except Exception as e:
        print(f"🌐 [NET-TC] ❌ Failed to start: {e}")
    finally:
        if sock:
            sock.close()

def monitor_status():
    """Monitor and print status periodically"""
    while True:
        time.sleep(10)  # Every 10 seconds
        elapsed = time.time() - start_time
        
        print(f"\n📊 [STATUS] Elapsed: {elapsed:.1f}s | Timecode count: {timecode_count}")
        if last_timecode:
            print(f"📊 [STATUS] Last timecode: {last_timecode}")
        print(f"📊 [STATUS] Listening for Depence timecode...")
        print("-" * 50)

def main():
    """Main test function"""
    print_header()
    
    # Instructions for Depence
    print("🎯 DEPENCE SETUP INSTRUCTIONS:")
    print("1. Open Depence software")
    print("2. Go to Settings/Preferences")
    print("3. Find Timecode Output settings")
    print("4. Enable Art-Net Timecode output")
    print("5. Set target IP to this computer's IP")
    print("6. Start timeline playback in Depence")
    print("7. You should see timecode messages below!")
    print("-" * 80)
    print()
    
    # Start monitoring threads
    threads = []
    
    try:
        # Start Art-Net 4 receiver (main Depence method)
        art_thread = threading.Thread(target=test_artnet4_timecode, daemon=True)
        art_thread.start()
        threads.append(art_thread)
        
        # Start MTC receiver
        mtc_thread = threading.Thread(target=test_mtc_timecode, daemon=True)  
        mtc_thread.start()
        threads.append(mtc_thread)
        
        # Start Net-timecode receiver
        net_thread = threading.Thread(target=test_net_timecode, daemon=True)
        net_thread.start()
        threads.append(net_thread)
        
        # Start status monitor
        status_thread = threading.Thread(target=monitor_status, daemon=True)
        status_thread.start()
        threads.append(status_thread)
        
        print("🚀 All receivers started! Press Ctrl+C to stop...")
        print("💡 If no timecode appears, check Depence settings!")
        print()
        
        # Keep main thread running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
        print(f"📊 Final stats: {timecode_count} timecode messages received")
        if last_timecode:
            print(f"📊 Last timecode: {last_timecode}")
        print("🎯 Check timecode_test.log for detailed logs")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        
    finally:
        print("🧹 Cleaning up...")

if __name__ == "__main__":
    main()