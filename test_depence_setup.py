#!/usr/bin/env python3
"""
Test script để verify Depence setup
Kiểm tra DMX Master có nhận được data từ Depence không
"""

import time
import logging
from src.artnet.controller import ArtNetController

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def dmx_callback(universe, dmx_data, source_ip):
    """Callback khi nhận DMX data"""
    non_zero_channels = []
    for i, value in enumerate(dmx_data[:20]):  # Check first 20 channels
        if value > 0:
            non_zero_channels.append(f"Ch{i+1}={value}")
    
    if non_zero_channels:
        logger.info(f"🎯 DMX from {source_ip} → Universe {universe}: {', '.join(non_zero_channels)}")
    else:
        logger.debug(f"📊 DMX from {source_ip} → Universe {universe}: All channels = 0")

def timecode_callback(data, addr):
    """Callback khi nhận timecode"""
    logger.info(f"🎵 Timecode from {addr[0]}: {len(data)} bytes")

def main():
    print("🚀 DMX Master - Depence Setup Test")
    print("=" * 50)
    print("1. Start DMX Master")
    print("2. Configure Depence:")
    print("   - ArtNET: Realtek PCle GbE (192.168.1.171)")
    print("   - Create fixtures in Universe 1")
    print("   - Set some channels > 0")
    print("   - Start playback")
    print("3. Watch for DMX data below...")
    print("=" * 50)
    
    # Initialize Art-Net controller
    controller = ArtNetController()
    controller.set_dmx_received_callback(dmx_callback)
    controller.register_timecode_callback(timecode_callback)
    
    if not controller.start():
        print("❌ Failed to start Art-Net controller")
        return
    
    print(f"✅ Art-Net Controller started on 0.0.0.0:6454")
    print(f"🎯 Listening for DMX and Timecode from Depence...")
    print("📝 DMX data will appear when Depence sends active fixtures")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")
    finally:
        controller.stop()
        print("✅ Test completed")

if __name__ == "__main__":
    main()