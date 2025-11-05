"""
Monitor Art-Net DMX packets từ Depence
Hiển thị universe và data đang nhận
"""
import sys
sys.path.insert(0, 'src')

from artnet.controller import ArtNetController
import time

print("=" * 80)
print("📺 ART-NET DMX MONITOR - Kiểm tra DMX từ Depence")
print("=" * 80)

# Create controller
ctrl = ArtNetController(bind_ip="0.0.0.0", port=6454)

# Track received data
universe_data = {}  # {universe: (count, last_time, channels)}

def on_dmx_received(universe, dmx_data, source_ip):
    """Monitor DMX packets"""
    current_time = time.time()
    
    # Count non-zero channels
    non_zero = sum(1 for x in dmx_data if x > 0)
    
    if universe not in universe_data:
        # First time seeing this universe
        print(f"\n🆕 NEW Universe {universe} from {source_ip}")
        universe_data[universe] = [1, current_time, dmx_data]
    else:
        count, last_time, _ = universe_data[universe]
        universe_data[universe] = [count + 1, current_time, dmx_data]
    
    count, _, _ = universe_data[universe]
    
    # Print first 10 packets for each universe, then every 100th
    if count <= 10 or count % 100 == 0:
        print(f"✅ U{universe:2d} | Packet #{count:4d} | Source: {source_ip:15s} | Active: {non_zero:3d}/512")
        
        # Show first 20 channels if any are non-zero
        if non_zero > 0 and count <= 3:
            first_20 = dmx_data[:20]
            non_zero_channels = [(i+1, v) for i, v in enumerate(first_20) if v > 0]
            if non_zero_channels:
                print(f"      First active channels: {non_zero_channels[:10]}")

ctrl.set_dmx_received_callback(on_dmx_received)

# Start controller
print("\n🚀 Starting Art-Net DMX monitor...")
if ctrl.start():
    print("✅ Listening on 0.0.0.0:6454")
    print("\n📺 Waiting for DMX data from Depence...")
    print("   Expected universes: 0-7")
    print("   Press Ctrl+C to stop...\n")
    
    try:
        start_time = time.time()
        last_summary = time.time()
        
        while True:
            time.sleep(0.1)
            
            # Print summary every 5 seconds
            if time.time() - last_summary >= 5.0:
                if universe_data:
                    print(f"\n{'='*60}")
                    print(f"📊 ACTIVE UNIVERSES ({len(universe_data)} total):")
                    for u in sorted(universe_data.keys()):
                        count, last_time, data = universe_data[u]
                        non_zero = sum(1 for x in data if x > 0)
                        age = time.time() - last_time
                        status = "🟢 LIVE" if age < 1.0 else "🟡 STALE"
                        print(f"   {status} Universe {u:2d}: {count:5d} packets, {non_zero:3d}/512 active channels")
                    
                    # Check if we got all 8
                    received = set(universe_data.keys())
                    expected = {0, 1, 2, 3, 4, 5, 6, 7}
                    
                    if received.issuperset(expected):
                        print(f"\n🎉 SUCCESS! All 8 universes received!")
                    else:
                        missing = expected - received
                        if missing:
                            print(f"\n⏳ Missing universes: {sorted(missing)}")
                            print(f"   Tip: Ensure Depence is sending to all 8 universes")
                    
                    print(f"{'='*60}")
                else:
                    print(f"\n⏳ No DMX data yet. Waiting for Depence to send...")
                    print(f"   Troubleshooting:")
                    print(f"   1. Ensure Depence Art-Net output is ACTIVE (not just enabled)")
                    print(f"   2. Check universe mapping in Depence")
                    print(f"   3. Try moving a fixture/light in Depence")
                    print(f"   4. Verify output IP: 192.168.1.171 or 255.255.255.255")
                
                last_summary = time.time()
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    
    if universe_data:
        print(f"Total universes received: {len(universe_data)}")
        print(f"\nDetails:")
        for u in sorted(universe_data.keys()):
            count, _, data = universe_data[u]
            non_zero = sum(1 for x in data if x > 0)
            print(f"  Universe {u:2d}: {count:5d} packets, {non_zero:3d}/512 active channels")
        
        received = set(universe_data.keys())
        expected = {0, 1, 2, 3, 4, 5, 6, 7}
        
        if received.issuperset(expected):
            print(f"\n✅ SUCCESS! All 8 universes received from Depence!")
        else:
            missing = expected - received
            if missing:
                print(f"\n⚠️  Missing universes: {sorted(missing)}")
                print(f"\nNext steps:")
                print(f"  1. Check Depence universe configuration")
                print(f"  2. Try using BROADCAST (255.255.255.255)")
                print(f"  3. Verify subnet settings in Depence")
    else:
        print("❌ No DMX data received")
        print("\nDespite Poll working, no DMX was sent. This means:")
        print("  • Depence sees the node but isn't sending data")
        print("  • Universe mapping might be incorrect")
        print("  • Output might not be activated in Depence")
    
    ctrl.stop()
    print("\n✅ Monitor stopped")
else:
    print("❌ Failed to start monitor")

print("=" * 80)
