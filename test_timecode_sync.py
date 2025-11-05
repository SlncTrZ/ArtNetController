"""
Test script for Timecode Sync Recording feature
V2.0 - DMX Master Professional

This script tests the timecode receivers without GUI to verify functionality.
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.system.timecode_receiver import (
    TimecodeManager, MTCReceiver, NetTimecodeReceiver, TimecodeData
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_net_timecode_receiver():
    """Test Net-timecode receiver"""
    print("🌐 Testing Net-timecode Receiver...")
    
    def on_timecode(data):
        print(f"📟 Received: {data['timecode']} ({data['fps']}fps) from {data['source']}")
    
    def on_stopped():
        print("⚠️ Timecode signal stopped")
    
    receiver = NetTimecodeReceiver(port=3040)
    receiver.set_callbacks(on_timecode, on_stopped)
    
    if receiver.start():
        print("✅ Net-timecode receiver started on port 3040")
        print("📡 Waiting for timecode from Depence or other software...")
        print("💡 To test: Configure Depence to send Net-timecode to localhost:3040")
        
        try:
            for i in range(30):  # Wait 30 seconds
                time.sleep(1)
                print(f"⏳ Listening... {30-i}s remaining", end='\r')
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
        
        receiver.stop()
        print("✅ Net-timecode receiver stopped")
    else:
        print("❌ Failed to start Net-timecode receiver")

def test_mtc_receiver():
    """Test MTC receiver"""
    print("🎹 Testing MTC Receiver...")
    
    def on_timecode(data):
        print(f"📟 Received: {data['timecode']} ({data['fps']}fps) from {data['source']}")
    
    def on_stopped():
        print("⚠️ Timecode signal stopped")
    
    receiver = MTCReceiver()
    receiver.set_callbacks(on_timecode, on_stopped)
    
    if receiver.start():
        print("✅ MTC receiver started")
        print("📡 Waiting for MIDI Time Code...")
        print("💡 To test: Configure Depence to send MTC to available MIDI device")
        
        try:
            for i in range(30):  # Wait 30 seconds
                time.sleep(1)
                print(f"⏳ Listening... {30-i}s remaining", end='\r')
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
        
        receiver.stop()
        print("✅ MTC receiver stopped")
    else:
        print("❌ Failed to start MTC receiver (MIDI device may not be available)")

def test_timecode_manager():
    """Test TimecodeManager with multiple receivers"""
    print("🎛️ Testing TimecodeManager...")
    
    def on_timecode(data):
        print(f"📟 Manager received: {data['timecode']} ({data['fps']}fps) from {data['source']}")
    
    def on_stopped():
        print("⚠️ Timecode signal stopped")
    
    manager = TimecodeManager()
    
    # Create receivers
    mtc = manager.create_mtc_receiver()
    net_tc = manager.create_net_timecode_receiver(3040)
    
    # Set callbacks
    mtc.set_callbacks(on_timecode, on_stopped)
    net_tc.set_callbacks(on_timecode, on_stopped)
    
    # Start all receivers
    started_count = manager.start_all()
    print(f"✅ Started {started_count} timecode receivers")
    
    if started_count > 0:
        active = manager.get_active_receivers()
        print(f"📡 Active receivers: {', '.join(active)}")
        print("💡 Send timecode from Depence or other software...")
        
        try:
            for i in range(60):  # Wait 60 seconds
                time.sleep(1)
                print(f"⏳ Listening on all channels... {60-i}s remaining", end='\r')
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
    
    manager.stop_all()
    print("✅ All receivers stopped")

def simulate_timecode_for_testing():
    """Simulate timecode data for testing RecordTab integration"""
    print("🎭 Simulating timecode data...")
    
    # This would be called by actual timecode receivers
    test_data = TimecodeData(
        hours=12,
        minutes=34,
        seconds=56,
        frames=15,
        fps=30.0,
        source="Test Simulator",
        timestamp=time.time()
    )
    
    print(f"📟 Simulated timecode: {test_data.to_string()} ({test_data.fps}fps)")
    print(f"📊 Data dict: {test_data.to_dict()}")
    
    return test_data.to_dict()

def main():
    """Main test function"""
    print("🚀 DMX Master - Timecode Sync Recording Test")
    print("=" * 50)
    
    print("\n1️⃣ Testing Net-timecode receiver...")
    test_net_timecode_receiver()
    
    print("\n2️⃣ Testing MTC receiver...")
    test_mtc_receiver()
    
    print("\n3️⃣ Testing TimecodeManager...")
    test_timecode_manager()
    
    print("\n4️⃣ Testing data simulation...")
    simulate_timecode_for_testing()
    
    print("\n✅ All tests completed!")
    print("\n📋 Next steps:")
    print("   1. Configure Depence to send timecode")
    print("   2. Test with actual DMX Master GUI")
    print("   3. Verify recording synchronization")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()