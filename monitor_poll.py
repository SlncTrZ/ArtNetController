"""
Monitor Art-Net Poll packets từ Depence
Hiển thị chi tiết về Poll requests và PollReply responses
"""
import sys
sys.path.insert(0, 'src')

from artnet.controller import ArtNetController, ArtNetPacket
import time
import struct

print("=" * 80)
print("🔍 ART-NET POLL MONITOR - Kiểm tra Poll từ Depence")
print("=" * 80)

# Create controller
ctrl = ArtNetController(bind_ip="0.0.0.0", port=6454)

# Statistics
poll_count = 0
poll_reply_sent = 0
last_poll_time = 0

def on_packet_received(data, addr):
    """Monitor all packets"""
    global poll_count, poll_reply_sent, last_poll_time
    
    # Try to parse Art-Net packet
    packet = ArtNetPacket.unpack(data)
    if not packet:
        return
    
    opcode = packet['opcode']
    
    # Check if it's a Poll packet
    if opcode == ArtNetPacket.ARTNET_POLL:
        poll_count += 1
        current_time = time.time()
        
        if last_poll_time > 0:
            interval = current_time - last_poll_time
        else:
            interval = 0
        
        last_poll_time = current_time
        
        print(f"\n📡 Poll #{poll_count} received from {addr[0]}:{addr[1]}")
        print(f"   Time: {time.strftime('%H:%M:%S')}")
        if interval > 0:
            print(f"   Interval: {interval:.2f}s since last poll")
        
        # Parse Poll flags if available
        payload = packet['payload']
        if len(payload) >= 2:
            flags = payload[0]
            priority = payload[1]
            
            print(f"   Flags: 0x{flags:02X}")
            if flags & 0x02:
                print(f"      → Wants Diagnostics")
            if flags & 0x04:
                print(f"      → Wants Reply (Unicast/Broadcast)")
            
            print(f"   Priority: {priority}")
        
        # Create and send PollReply
        reply = ctrl._create_poll_reply()
        
        try:
            # Send reply back to sender
            ctrl.socket.sendto(reply, addr)
            poll_reply_sent += 1
            
            print(f"   ✅ PollReply sent to {addr[0]}:{addr[1]}")
            print(f"      Reply size: {len(reply)} bytes")
            
            # Parse and display PollReply info
            # NumPorts at offset 172-173
            num_ports = (reply[172] << 8) | reply[173]
            print(f"      NumPorts advertised: {num_ports}")
            
            # PortTypes at offset 174-177
            port_types = [reply[174+i] for i in range(4)]
            print(f"      PortTypes: {[hex(p) for p in port_types]}")
            
            # Get IP from reply (offset 10-13)
            ip_bytes = reply[10:14]
            reply_ip = '.'.join(str(b) for b in ip_bytes)
            print(f"      Advertised IP: {reply_ip}")
            
            # ShortName at offset 26-43
            short_name_bytes = reply[26:44]
            short_name = short_name_bytes.split(b'\x00')[0].decode('utf-8', errors='ignore')
            print(f"      Node Name: '{short_name}'")
            
        except Exception as e:
            print(f"   ❌ Error sending PollReply: {e}")

# Monkey-patch receive handler to intercept packets
original_handle = ctrl._handle_packet

def intercept_handle(data, addr):
    on_packet_received(data, addr)
    original_handle(data, addr)

ctrl._handle_packet = intercept_handle

# Start controller
print("\n🚀 Starting Art-Net Poll monitor...")
if ctrl.start():
    print("✅ Listening on 0.0.0.0:6454")
    print("\n📡 Waiting for Art-Net Poll from Depence...")
    print("   Expected source: 192.168.1.x")
    print("   Press Ctrl+C to stop...\n")
    
    try:
        # Monitor for 120 seconds or until Ctrl+C
        start_time = time.time()
        last_summary = time.time()
        
        while time.time() - start_time < 120:
            time.sleep(0.1)
            
            # Print summary every 10 seconds
            if time.time() - last_summary >= 10.0:
                if poll_count > 0:
                    print(f"\n📊 Summary: Received {poll_count} Poll(s), Sent {poll_reply_sent} Reply(ies)")
                else:
                    print(f"\n⏳ No Poll packets received yet...")
                    print(f"   Troubleshooting:")
                    print(f"   1. Check Depence Art-Net is enabled")
                    print(f"   2. Verify Depence output IP: 192.168.1.171")
                    print(f"   3. Check firewall allows UDP 6454")
                    print(f"   4. Ensure same subnet (192.168.1.x)")
                
                last_summary = time.time()
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"Total Poll packets received: {poll_count}")
    print(f"Total PollReply sent: {poll_reply_sent}")
    
    if poll_count > 0:
        print("\n✅ Poll communication is working!")
        print("\nWhat this means:")
        print("  • Depence can discover DMX Master node")
        print("  • Network connection is OK")
        print("  • Port 6454 UDP is open")
        
        print("\nNext steps:")
        print("  1. Check if Depence shows DMX Master in node list")
        print("  2. Configure Depence to send DMX to 192.168.1.171")
        print("  3. Monitor DMX data with DMX View tab")
    else:
        print("\n❌ No Poll packets received")
        print("\nTroubleshooting:")
        print("  1. Verify Depence Art-Net output is running")
        print("  2. Check IP: Should be 192.168.1.171 or 255.255.255.255")
        print("  3. Disable firewall temporarily to test")
        print("  4. Check network adapter settings")
        print("  5. Try pinging 192.168.1.171 from Depence machine")
    
    # Stop controller
    ctrl.stop()
    print("\n✅ Monitor stopped")

else:
    print("❌ Failed to start monitor")
    print("   Port 6454 may be in use by another application")
    print("   Close DMX Master application if running")

print("=" * 80)
