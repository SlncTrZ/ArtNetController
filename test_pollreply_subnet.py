"""
Test PollReply packet structure with subnet support
Verify that _create_poll_reply(subnet) generates correct packets
"""

import sys
import struct
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from artnet.controller import ArtNetController

def analyze_pollreply(packet: bytes, subnet: int):
    """Phân tích chi tiết PollReply packet"""
    print(f"\n{'='*70}")
    print(f"POLLREPLY ANALYSIS - SUBNET {subnet}")
    print(f"{'='*70}")
    
    if len(packet) != 239:
        print(f"❌ ERROR: Packet length = {len(packet)} bytes (expected 239)")
        return
    else:
        print(f"✅ Packet length: {len(packet)} bytes")
    
    # Header
    header = packet[0:8]
    print(f"\n📋 Header: {header}")
    if header != b'Art-Net\x00':
        print(f"   ❌ ERROR: Invalid header")
        return
    else:
        print(f"   ✅ Valid Art-Net header")
    
    # OpCode
    opcode = struct.unpack('<H', packet[8:10])[0]
    print(f"\n🔧 OpCode: 0x{opcode:04X}")
    if opcode != 0x2100:
        print(f"   ❌ ERROR: Expected 0x2100 (ArtPollReply)")
        return
    else:
        print(f"   ✅ Correct ArtPollReply opcode")
    
    # IP Address
    ip = '.'.join(str(b) for b in packet[10:14])
    print(f"\n🌐 IP Address: {ip}")
    
    # Port
    port = struct.unpack('<H', packet[14:16])[0]
    print(f"🔌 Port: {port} (0x{port:04X})")
    
    # Firmware Version
    fw_version = struct.unpack('>H', packet[16:18])[0]
    print(f"📦 Firmware: v{fw_version >> 8}.{fw_version & 0xFF}")
    
    # NetSwitch & SubSwitch
    net_switch = packet[18]
    sub_switch = packet[19]
    print(f"\n🌍 NetSwitch: {net_switch}")
    print(f"🔀 SubSwitch: {sub_switch} {'✅ MATCH' if sub_switch == subnet else '❌ MISMATCH'}")
    
    # OEM
    oem = struct.unpack('>H', packet[20:22])[0]
    print(f"\n🏢 OEM Code: 0x{oem:04X}")
    
    # Status1
    status1 = packet[23]
    print(f"📊 Status1: 0x{status1:02X}")
    
    # ESTA Code
    esta = struct.unpack('<H', packet[24:26])[0]
    print(f"🏭 ESTA Code: 0x{esta:04X}")
    
    # ShortName
    short_name = packet[26:44].rstrip(b'\x00').decode('utf-8', errors='ignore')
    print(f"\n📛 ShortName: '{short_name}'")
    expected_short = "DMX Master" if subnet == 0 else f"DMX Master S{subnet}"
    if short_name == expected_short:
        print(f"   ✅ Correct name for subnet {subnet}")
    else:
        print(f"   ⚠️  Expected: '{expected_short}'")
    
    # LongName
    long_name = packet[44:108].rstrip(b'\x00').decode('utf-8', errors='ignore')
    print(f"\n📝 LongName: '{long_name}'")
    
    # NodeReport
    node_report = packet[108:172].rstrip(b'\x00').decode('utf-8', errors='ignore')
    print(f"\n📢 NodeReport: '{node_report}'")
    
    # NumPorts
    num_ports_hi = packet[172]
    num_ports_lo = packet[173]
    num_ports = (num_ports_hi << 8) | num_ports_lo
    print(f"\n🔌 NumPorts: {num_ports} (Hi={num_ports_hi}, Lo={num_ports_lo})")
    if num_ports != 4:
        print(f"   ⚠️  Warning: Expected 4 ports")
    
    # PortTypes
    port_types = list(packet[174:178])
    print(f"\n🔧 PortTypes: {[f'0x{pt:02X}' for pt in port_types]}")
    if all(pt == 0x40 for pt in port_types):
        print(f"   ✅ All ports are Input (0x40)")
    else:
        print(f"   ⚠️  Warning: Not all ports are Input")
    
    # GoodInput
    good_input = list(packet[178:182])
    print(f"\n✅ GoodInput: {[f'0x{gi:02X}' for gi in good_input]}")
    
    # GoodOutputA
    good_output_a = list(packet[182:186])
    print(f"📤 GoodOutputA: {[f'0x{go:02X}' for go in good_output_a]}")
    
    # SwIn (Universe addresses)
    sw_in = list(packet[186:190])
    print(f"\n🌐 SwIn (Universe): {sw_in}")
    if sw_in == [0, 1, 2, 3]:
        print(f"   ✅ Correct port-level addressing (0-3)")
        # Calculate full universe addresses
        full_universes = [(subnet << 4) | sw for sw in sw_in]
        print(f"   📍 Full Universe addresses: {full_universes}")
        print(f"      (SubNet {subnet} × 16 + SwIn = Universe {full_universes[0]}-{full_universes[3]})")
    else:
        print(f"   ⚠️  Expected [0, 1, 2, 3]")
    
    # SwOut
    sw_out = list(packet[190:194])
    print(f"\n📤 SwOut: {sw_out}")
    
    # Style
    style = packet[200]
    style_names = {0: "StNode", 1: "StController", 2: "StMedia", 3: "StRoute", 4: "StBackup", 5: "StConfig"}
    style_name = style_names.get(style, f"Unknown(0x{style:02X})")
    print(f"\n🎨 Style: {style} ({style_name})")
    if style == 0:
        print(f"   ✅ Correct StNode style for Input device")
    else:
        print(f"   ⚠️  Warning: Expected StNode (0)")
    
    # MAC Address
    mac = ':'.join(f'{b:02X}' for b in packet[201:207])
    print(f"\n🔐 MAC Address: {mac}")
    
    # BindIp
    bind_ip = '.'.join(str(b) for b in packet[207:211])
    print(f"🔗 BindIp: {bind_ip}")
    
    # Status2
    status2 = packet[212]
    print(f"\n📊 Status2: 0x{status2:02X}")
    
    # GoodOutputB
    good_output_b = list(packet[213:217])
    print(f"📤 GoodOutputB: {[f'0x{go:02X}' for go in good_output_b]}")
    
    print(f"\n{'='*70}\n")


def test_multi_subnet():
    """Test multiple subnet PollReply packets"""
    print("\n" + "="*70)
    print("TESTING MULTI-SUBNET POLLREPLY GENERATION")
    print("="*70)
    
    # Create controller instance
    controller = ArtNetController()
    
    # Test scenarios for different universe counts
    test_scenarios = [
        # (universes_to_test, description)
        (8, "8 Universes (Depence typical setup)"),
        (16, "16 Universes (1 full subnet)"),
        (32, "32 Universes (2 full subnets)"),
    ]
    
    for max_uni, desc in test_scenarios:
        print(f"\n{'='*70}")
        print(f"SCENARIO: {desc}")
        print(f"{'='*70}\n")
        
        num_replies = (max_uni + 3) // 4  # Round up
        
        for i in range(num_replies):
            subnet = i // 4  # Mỗi subnet có 4 replies
            base_universe = i * 4
            sw_in = [(base_universe + j) % 16 for j in range(4)]
            
            print(f"Reply #{i+1}/{num_replies}:")
            print(f"  subnet={subnet}, sw_in={sw_in}")
            
            try:
                packet = controller._create_poll_reply(subnet=subnet, sw_in=sw_in)
                
                # Quick validation
                start_uni = (subnet << 4) | sw_in[0]
                end_uni = (subnet << 4) | sw_in[3]
                
                # Verify SwIn in packet
                actual_sw_in = list(packet[186:190])
                
                if actual_sw_in == sw_in:
                    print(f"  ✅ Universe {start_uni}-{end_uni}, SwIn={actual_sw_in}")
                else:
                    print(f"  ❌ ERROR: Expected SwIn={sw_in}, got {actual_sw_in}")
                    
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
    
    # Detailed analysis for 8-universe scenario
    print(f"\n{'='*70}")
    print("DETAILED ANALYSIS: 8 Universes (for Depence)")
    print(f"{'='*70}\n")
    
    for i in range(2):  # 2 replies for 8 universes
        subnet = i // 4  # Both in subnet 0
        base_universe = i * 4
        sw_in = [(base_universe + j) % 16 for j in range(4)]
        
        packet = controller._create_poll_reply(subnet=subnet, sw_in=sw_in)
        analyze_pollreply(packet, subnet)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY - CORRECT ADDRESSING")
    print("="*70)
    print("\n✅ For 8 universes (Depence/Resolume):")
    print("-" * 70)
    print("  PollReply #1: SubNet=0, SwIn=[0,1,2,3]   → Universe 0-3")
    print("  PollReply #2: SubNet=0, SwIn=[4,5,6,7]   → Universe 4-7")
    print()
    print("✅ For 16 universes (1 full subnet):")
    print("-" * 70)
    print("  PollReply #1: SubNet=0, SwIn=[0,1,2,3]   → Universe 0-3")
    print("  PollReply #2: SubNet=0, SwIn=[4,5,6,7]   → Universe 4-7")
    print("  PollReply #3: SubNet=0, SwIn=[8,9,10,11] → Universe 8-11")
    print("  PollReply #4: SubNet=0, SwIn=[12,13,14,15] → Universe 12-15")
    print()
    print("✅ For 32 universes (2 full subnets):")
    print("-" * 70)
    print("  SubNet 0:")
    print("    PollReply #1-4: SwIn=[0-3], [4-7], [8-11], [12-15] → U0-15")
    print("  SubNet 1:")
    print("    PollReply #5-8: SwIn=[0-3], [4-7], [8-11], [12-15] → U16-31")
    
    print("\n" + "="*70)
    print("DEPENCE/RESOLUME/MADRIX CONFIGURATION")
    print("="*70)
    print("\nUser simply configures: Universe 0, 1, 2, 3, 4, 5, 6, 7")
    print("DMX Master automatically responds with correct PollReply packets")
    print("No special subnet configuration needed in the software!")
    print("="*70 + "\n")


if __name__ == '__main__':
    test_multi_subnet()
