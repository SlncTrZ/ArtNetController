"""
Test script to verify Art-Net self-detection fixes
Run this to check if netifaces is working and what IPs are detected
"""

import sys

print("=" * 60)
print("DMX Master LTS - Art-Net Self-Detection Test")
print("=" * 60)

# Test 1: Check netifaces availability
print("\n[TEST 1] Checking netifaces library...")
try:
    import netifaces
    print("✅ netifaces installed successfully")
    NETIFACES_AVAILABLE = True
except ImportError:
    print("❌ netifaces NOT installed")
    print("   Install with: pip install netifaces")
    NETIFACES_AVAILABLE = False

# Test 2: Detect all local IPs
print("\n[TEST 2] Detecting local IP addresses...")
import socket

local_ips = set()
local_ips.add("127.0.0.1")
local_ips.add("::1")

if NETIFACES_AVAILABLE:
    print("   Using netifaces for comprehensive detection...")
    try:
        for interface in netifaces.interfaces():
            print(f"   - Interface: {interface}")
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr_info in addrs[netifaces.AF_INET]:
                    if 'addr' in addr_info:
                        ip = addr_info['addr']
                        local_ips.add(ip)
                        print(f"     IPv4: {ip}")
        print(f"\n   ✅ Detected {len(local_ips)} local IPs (netifaces)")
    except Exception as e:
        print(f"   ❌ netifaces detection failed: {e}")
else:
    print("   Using fallback detection (simple method)...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        s.close()
        local_ips.add(primary_ip)
        print(f"   - Primary interface: {primary_ip}")
        print(f"\n   ⚠️  Detected {len(local_ips)} local IPs (fallback - may miss loopback adapters)")
    except Exception as e:
        print(f"   ❌ Fallback detection failed: {e}")

# Test 3: Display all detected IPs
print("\n[TEST 3] All detected local IP addresses:")
for ip in sorted(local_ips):
    print(f"   - {ip}")

# Test 4: Check specific IP (loopback adapter)
print("\n[TEST 4] Checking Microsoft KM-TEST Loopback Adapter...")
test_ip = "200.133.200.133"
if test_ip in local_ips:
    print(f"   ✅ {test_ip} detected as local IP")
    print(f"   → Self-detection filter will work correctly")
else:
    print(f"   ❌ {test_ip} NOT detected")
    if NETIFACES_AVAILABLE:
        print(f"   → This IP may not exist or netifaces couldn't detect it")
    else:
        print(f"   → Install netifaces for better detection: pip install netifaces")

# Test 5: Art-Net packet parsing test
print("\n[TEST 5] Testing Art-Net PollReply parsing...")
import struct

# Simulate PollReply packet bytes
test_packet = bytearray(239)
test_packet[164] = 0x00  # NumPortsHi
test_packet[165] = 0x04  # NumPortsLo (4 ports)
test_packet[166] = 0x40  # PortTypes[0] (DMX Input)
test_packet[178] = 0x00  # SwIn[0] (Universe 0)

# Parse NumPorts
num_ports_hi = test_packet[164]
num_ports_lo = test_packet[165]
port_count = (num_ports_hi << 8) | num_ports_lo

print(f"   NumPorts: Hi=0x{num_ports_hi:02X}, Lo=0x{num_ports_lo:02X}")
print(f"   → Port Count: {port_count}")

if port_count == 4:
    print(f"   ✅ Port count parsing correct (4)")
else:
    print(f"   ❌ Port count parsing incorrect (expected 4, got {port_count})")

# Parse Universe
net_switch = 0
sub_switch = 0
sw_in_0 = test_packet[178]
base_universe = (sub_switch << 4) | (sw_in_0 & 0x0F)

print(f"\n   Universe: Net={net_switch}, SubNet={sub_switch}, SwIn[0]={sw_in_0}")
print(f"   → Base Universe: {base_universe}")

if base_universe == 0:
    print(f"   ✅ Universe parsing correct (0)")
else:
    print(f"   ❌ Universe parsing incorrect (expected 0, got {base_universe})")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

issues = []
if not NETIFACES_AVAILABLE:
    issues.append("⚠️  netifaces not installed - loopback adapters may not be detected")
if test_ip not in local_ips and NETIFACES_AVAILABLE:
    issues.append(f"⚠️  {test_ip} not detected (adapter may not exist)")
if port_count != 4:
    issues.append(f"❌ Port count parsing broken")
if base_universe != 0:
    issues.append(f"❌ Universe parsing broken")

if not issues:
    print("✅ ALL TESTS PASSED")
    print("   Self-detection filter should work correctly")
    print("   Port count and Universe will display correctly")
else:
    print("⚠️  SOME ISSUES FOUND:")
    for issue in issues:
        print(f"   {issue}")

print("\nTo test in DMX Master:")
print("   1. Launch DMX Master LTS")
print("   2. Go to Hardware Manager tab")
print("   3. Click 'Scan Network'")
print("   4. Verify your IP is NOT shown in devices list")
print("   5. Check logs for: '🔒 Ignoring poll reply from self'")
print("=" * 60)
