"""
Debug Art-Net PollReply packet structure
Check actual byte positions
"""

import struct

# Simulate creating a PollReply packet
packet = bytearray()

# Art-Net header
packet.extend(b"Art-Net\x00")  # 8 bytes -> position 8
print(f"After header: position {len(packet)}")

# OpCode
packet.extend(struct.pack('<H', 0x2100))  # 2 bytes -> position 10
print(f"After OpCode: position {len(packet)}")

# IP Address
packet.extend(bytes([192, 168, 1, 20]))  # 4 bytes -> position 14
print(f"After IP: position {len(packet)}")

# Port
packet.extend(struct.pack('<H', 6454))  # 2 bytes -> position 16
print(f"After Port: position {len(packet)}")

# VersInfo
packet.extend(struct.pack('>H', 0x0200))  # 2 bytes -> position 18
print(f"After VersInfo: position {len(packet)}")

# NetSwitch
packet.append(0)  # 1 byte -> position 19
print(f"After NetSwitch: position {len(packet)}")

# SubSwitch
packet.append(0)  # 1 byte -> position 20
print(f"After SubSwitch: position {len(packet)}")

# Oem
packet.extend(struct.pack('>H', 0xFFFF))  # 2 bytes -> position 22
print(f"After Oem: position {len(packet)}")

# UbeaVersion
packet.append(0)  # 1 byte -> position 23
print(f"After UbeaVersion: position {len(packet)}")

# Status1
packet.append(0)  # 1 byte -> position 24
print(f"After Status1: position {len(packet)}")

# EstaMan
packet.extend(struct.pack('<H', 0xFFFF))  # 2 bytes -> position 26
print(f"After EstaMan: position {len(packet)}")

# ShortName (18 bytes)
short_name = b"DMX Master\x00\x00\x00\x00\x00\x00\x00\x00"
packet.extend(short_name)  # 18 bytes -> position 44
print(f"After ShortName: position {len(packet)}")

# LongName (64 bytes)
long_name = b"DMX Master LTS - Universe 0-3" + b'\x00' * (64 - 29)
packet.extend(long_name)  # 64 bytes -> position 108
print(f"After LongName: position {len(packet)}")

# NodeReport (64 bytes)
node_report = b"#0001 [0000] Ready - U0-3" + b'\x00' * (64 - 25)
packet.extend(node_report)  # 64 bytes -> position 172
print(f"After NodeReport: position {len(packet)}")

# NumPorts (2 bytes)
num_ports = 4
packet.append(num_ports >> 8)  # Hi byte
packet.append(num_ports & 0xFF)  # Lo byte
print(f"After NumPorts: position {len(packet)}")
print(f"NumPorts at bytes: {len(packet)-2}-{len(packet)-1}")

# PortTypes (4 bytes)
for i in range(4):
    packet.append(0x40)
print(f"After PortTypes: position {len(packet)}")
print(f"PortTypes at bytes: {len(packet)-4}-{len(packet)-1}")

# Print actual values
print("\n" + "="*60)
print("ACTUAL PACKET STRUCTURE:")
print("="*60)
print(f"NumPorts should be at bytes 164-165 (spec)")
print(f"NumPorts actually at bytes 172-173 (our packet)")
print(f"  Byte 172: 0x{packet[172]:02X} (Hi byte) = {packet[172]}")
print(f"  Byte 173: 0x{packet[173]:02X} (Lo byte) = {packet[173]}")
print(f"  Result: {(packet[172] << 8) | packet[173]}")

print(f"\nPortTypes at bytes 174-177 (our packet)")
print(f"  Byte 174: 0x{packet[174]:02X}")
print(f"  Byte 175: 0x{packet[175]:02X}")
print(f"  Byte 176: 0x{packet[176]:02X}")
print(f"  Byte 177: 0x{packet[177]:02X}")

print(f"\nIf we incorrectly read bytes 164-165:")
if len(packet) > 165:
    wrong_hi = packet[164]
    wrong_lo = packet[165]
    wrong_result = (wrong_hi << 8) | wrong_lo
    print(f"  Byte 164: 0x{wrong_hi:02X} (actually part of NodeReport)")
    print(f"  Byte 165: 0x{wrong_lo:02X} (actually part of NodeReport)")
    print(f"  Wrong result: {wrong_result}")

print("\n" + "="*60)
print("CONCLUSION:")
print("="*60)
print("Art-Net spec counts from PAYLOAD START (after OpCode)")
print("So spec byte 164 = packet byte 164 (includes 8-byte header + 2-byte opcode)")
print("But our packet has 8-byte header BEFORE the payload!")
print("So we need to ADD 10 bytes offset when parsing!")
