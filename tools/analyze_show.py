"""
Analyze DMX Recording - Check which universes are used
"""

import struct
from pathlib import Path
from collections import Counter

def analyze_dmxrec(file_path):
    """Analyze .dmxrec file and show universe usage"""
    
    print("="*70)
    print(f"Analyzing: {file_path}")
    print("="*70)
    
    with open(file_path, 'rb') as f:
        # Read header (32 bytes)
        header = f.read(32)
        
        magic = header[0:4]
        version = header[4]
        fps_bytes = header[5:7]
        fps = struct.unpack('>H', fps_bytes)[0]
        universe_count = struct.unpack('>H', header[7:9])[0]
        frame_count = struct.unpack('>I', header[9:13])[0]
        flags = header[13]
        
        print(f"\n📄 File Information:")
        print(f"   Magic:          {magic}")
        print(f"   Version:        {version}")
        print(f"   FPS:            {fps}")
        print(f"   Universe Count: {universe_count}")
        print(f"   Frame Count:    {frame_count}")
        print(f"   Flags:          0x{flags:02X}")
        
        # Read all frames and count universes
        universe_counter = Counter()
        universe_frame_count = {}
        
        frame_size = 524  # 8 (timestamp) + 2 (universe) + 512 (DMX) + 2 (CRC)
        
        print(f"\n🔍 Reading {frame_count} frames...")
        
        for i in range(frame_count):
            frame_data = f.read(frame_size)
            if len(frame_data) < frame_size:
                print(f"   ⚠️ Warning: Incomplete frame at {i}")
                break
            
            # Parse frame
            timestamp = struct.unpack('>d', frame_data[0:8])[0]
            universe = struct.unpack('>H', frame_data[8:10])[0]
            
            universe_counter[universe] += 1
            
            if universe not in universe_frame_count:
                universe_frame_count[universe] = 0
            universe_frame_count[universe] += 1
        
        # Display universe usage
        print(f"\n🎭 Universe Usage:")
        print(f"   Total Universes: {len(universe_counter)}")
        print(f"   Total Frames:    {sum(universe_counter.values())}")
        
        print(f"\n📊 Frames per Universe:")
        for universe in sorted(universe_counter.keys()):
            count = universe_counter[universe]
            percentage = (count / frame_count) * 100 if frame_count > 0 else 0
            print(f"   Universe {universe:3d}: {count:6d} frames ({percentage:5.1f}%)")
        
        # Calculate duration
        duration = frame_count / fps if fps > 0 else 0
        print(f"\n⏱️ Recording Duration:")
        print(f"   Total Time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
        # Check if within FREE version limit (4 universes)
        universes_list = sorted(universe_counter.keys())
        print(f"\n🆓 License Tier Compatibility:")
        
        if all(u < 4 for u in universes_list):
            print(f"   ✅ FREE Version Compatible (all universes 0-3)")
        else:
            free_compatible = [u for u in universes_list if u < 4]
            licensed_only = [u for u in universes_list if u >= 4]
            print(f"   ⚠️  Requires LICENSED Version")
            print(f"   FREE Compatible:   {free_compatible if free_compatible else 'None'}")
            print(f"   LICENSED Only:     {licensed_only}")
            print(f"   In FREE version, Universe {min(licensed_only)}+ will be skipped")

if __name__ == "__main__":
    file_path = Path("data/shows/Default_Rainbow_Show.dmxrec")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
    else:
        analyze_dmxrec(file_path)
        print("\n" + "="*70)
