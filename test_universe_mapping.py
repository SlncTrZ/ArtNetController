#!/usr/bin/env python3
"""
Test Universe Mapping between Depence and DMX Master
Verify that Depence Universe 1 appears as Universe 0 in DMX Master
"""

import sys
import time
import socket
import struct
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.artnet.controller import ArtNetController

def test_universe_mapping():
    """Test universe mapping from Depence to DMX Master"""
    print("🌍 Universe Mapping Test")
    print("=" * 40)
    print("Testing: Depence Universe 1 → DMX Master Universe 0")
    print("=" * 40)
    
    # Create Art-Net controller
    controller = ArtNetController()
    
    received_universes = {}
    
    def on_dmx_received(universe: int, dmx_data: bytes, source_ip: str):
        received_universes[universe] = {
            'data': dmx_data,
            'source': source_ip,
            'time': time.time()
        }
        
        # Show non-zero channels
        non_zero = [(i+1, val) for i, val in enumerate(dmx_data[:20]) if val > 0]
        
        print(f"📥 Universe {universe} from {source_ip}:")
        if non_zero:
            print(f"   🔥 Active channels: {non_zero}")
        else:
            print(f"   ❌ All channels zero")
        print()
    
    controller.dmx_received_callback = on_dmx_received
    
    # Start controller
    if not controller.start():
        print("❌ Failed to start Art-Net controller")
        return
    
    print("✅ Art-Net controller started")
    print()
    print("🎭 DEPENCE CONFIGURATION:")
    print("-" * 30)
    print("1. In Depence:")
    print("   📡 Target IP: 127.0.0.1 or 192.168.1.171")
    print("   🌍 Universe: 1 (will show as Universe 0 below)")
    print("   🎚️ Move some faders on Universe 1")
    print()
    print("2. Expected result:")
    print("   ✅ DMX data appears on Universe 0 in this test")
    print("   ✅ Same data shows in DMX Master Universe 0")
    print("-" * 30)
    print()
    
    print("📡 Monitoring for 60 seconds...")
    print("⚠️  Press Ctrl+C to stop early")
    print()
    
    try:
        for i in range(60):
            time.sleep(1)
            
            if i % 10 == 9:  # Every 10 seconds
                print(f"⏰ {i+1}s - Universes received: {list(received_universes.keys())}")
                
                if received_universes:
                    for uni, info in received_universes.items():
                        age = time.time() - info['time']
                        print(f"   Universe {uni}: last seen {age:.1f}s ago from {info['source']}")
                else:
                    print("   ❌ No universes received yet")
                    print("   💡 Check Depence is sending to Universe 1")
                print()
                
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    
    # Final results
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Universes received: {list(received_universes.keys())}")
    
    if 0 in received_universes:
        print("✅ SUCCESS: Universe 0 received (from Depence Universe 1)")
        print("💡 Universe mapping is working correctly!")
        
        # Show sample data
        data = received_universes[0]['data']
        non_zero = [(i+1, val) for i, val in enumerate(data[:20]) if val > 0]
        if non_zero:
            print(f"   Sample data: {non_zero}")
        
    else:
        print("❌ ISSUE: No data on Universe 0")
        if received_universes:
            print(f"   Received universes: {list(received_universes.keys())}")
            print("   💡 Check that Depence is set to Universe 1")
        else:
            print("   💡 No Art-Net DMX received at all")
            print("   🔧 Check Depence Art-Net settings:")
            print("      - Art-Net output enabled?")
            print("      - Target IP correct?")
            print("      - Faders active on Universe 1?")
    
    # Cleanup
    controller.stop()
    print("\n🧹 Test complete")

if __name__ == "__main__":
    test_universe_mapping()