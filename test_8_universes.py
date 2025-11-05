"""
Demo: DMX Master nhận 8 universes từ Depence
Test script để verify rằng DMX Master có thể nhận tất cả 8 universes
"""
import sys
sys.path.insert(0, 'src')

from artnet.controller import ArtNetController
import time

print("=" * 80)
print("🎭 DMX MASTER - 8 UNIVERSES TEST")
print("=" * 80)

# Create controller
ctrl = ArtNetController(bind_ip="0.0.0.0", port=6454)

# Track received universes
received_universes = set()

# Callback to track DMX
def on_dmx_received(universe, dmx_data, source_ip):
    received_universes.add(universe)
    non_zero = sum(1 for x in dmx_data if x > 0)
    print(f"✅ Universe {universe:2d} | Source: {source_ip:15s} | Active channels: {non_zero:3d}/512")

ctrl.set_dmx_received_callback(on_dmx_received)

# Start controller
print("\n🚀 Starting Art-Net controller...")
if ctrl.start():
    print("✅ Art-Net controller started on 0.0.0.0:6454")
    print("\n📡 Listening for Art-Net DMX from Depence...")
    print("   Expecting universes: 0, 1, 2, 3, 4, 5, 6, 7")
    print("\n⏳ Waiting for DMX data (Press Ctrl+C to stop)...\n")
    
    try:
        # Monitor for 60 seconds or until Ctrl+C
        start_time = time.time()
        last_summary = time.time()
        
        while time.time() - start_time < 60:
            time.sleep(0.1)
            
            # Print summary every 5 seconds
            if time.time() - last_summary >= 5.0:
                if received_universes:
                    universes_list = sorted(received_universes)
                    print(f"\n📊 Received universes so far: {universes_list}")
                    
                    # Check if we got all 8
                    expected = {0, 1, 2, 3, 4, 5, 6, 7}
                    if received_universes.issuperset(expected):
                        print("🎉 SUCCESS! All 8 universes received!")
                        break
                else:
                    print("\n⏳ No DMX data received yet...")
                    print("   → Check Depence Art-Net output is enabled")
                    print("   → Verify IP address: 192.168.1.171 or 255.255.255.255")
                
                last_summary = time.time()
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    
    if received_universes:
        universes_list = sorted(received_universes)
        print(f"✅ Received {len(received_universes)} universe(s): {universes_list}")
        
        expected = {0, 1, 2, 3, 4, 5, 6, 7}
        missing = expected - received_universes
        
        if not missing:
            print("🎉 SUCCESS! All 8 universes received correctly!")
        else:
            print(f"⚠️  Missing universes: {sorted(missing)}")
            print("\nTroubleshooting:")
            print("  1. Check Depence Art-Net configuration")
            print("  2. Verify universe mapping in Depence")
            print("  3. Try using BROADCAST (255.255.255.255) instead of unicast")
    else:
        print("❌ No DMX data received")
        print("\nTroubleshooting:")
        print("  1. Check Depence Art-Net output is running")
        print("  2. Verify network connection (same subnet)")
        print("  3. Check firewall settings (allow UDP 6454)")
        print("  4. Try using BROADCAST (255.255.255.255)")
    
    # Stop controller
    ctrl.stop()
    print("\n✅ Art-Net controller stopped")

else:
    print("❌ Failed to start Art-Net controller")
    print("   Check if port 6454 is already in use")

print("=" * 80)
