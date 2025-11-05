"""
Test ArtPollReply packet structure
"""
import sys
sys.path.insert(0, 'src')

from artnet.controller import ArtNetController

# Create controller and PollReply packet
ctrl = ArtNetController()
reply = ctrl._create_poll_reply()

print("=" * 80)
print("ArtPollReply Packet Structure Analysis")
print("=" * 80)

print(f"\nTotal packet size: {len(reply)} bytes")
print(f"Expected size: ~239 bytes (Art-Net 4 spec)")

# Header
print("\n--- HEADER ---")
print(f"Bytes 0-7: Art-Net ID = {reply[0:8]}")
print(f"Bytes 8-9: OpCode = 0x{reply[8]:02X}{reply[9]:02X} (should be 0x2100)")

# Calculate offset
offset = 10  # After header + opcode

print(f"\n--- NODE INFO ---")
print(f"Bytes {offset}-{offset+3}: IP = {'.'.join(str(b) for b in reply[offset:offset+4])}")
offset += 4

print(f"Bytes {offset}-{offset+1}: Port = 0x{reply[offset]:02X}{reply[offset+1]:02X}")
offset += 2

print(f"Bytes {offset}-{offset+1}: VersInfo = 0x{reply[offset]:02X}{reply[offset+1]:02X}")
offset += 2

print(f"Byte {offset}: NetSwitch = {reply[offset]}")
offset += 1

print(f"Byte {offset}: SubSwitch = {reply[offset]}")
offset += 1

print(f"Bytes {offset}-{offset+1}: Oem = 0x{reply[offset]:02X}{reply[offset+1]:02X}")
offset += 2

print(f"Byte {offset}: UbeaVersion = {reply[offset]}")
offset += 1

print(f"Byte {offset}: Status1 = 0x{reply[offset]:02X}")
offset += 1

print(f"Bytes {offset}-{offset+1}: EstaMan = 0x{reply[offset]:02X}{reply[offset+1]:02X}")
offset += 2

# ShortName (18 bytes)
short_name_bytes = reply[offset:offset+18]
short_name = short_name_bytes.split(b'\x00')[0].decode('utf-8', errors='ignore')
print(f"Bytes {offset}-{offset+17}: ShortName = '{short_name}'")
offset += 18

# LongName (64 bytes)
long_name_bytes = reply[offset:offset+64]
long_name = long_name_bytes.split(b'\x00')[0].decode('utf-8', errors='ignore')
print(f"Bytes {offset}-{offset+63}: LongName = '{long_name}'")
offset += 64

# NodeReport (64 bytes)
node_report_bytes = reply[offset:offset+64]
node_report = node_report_bytes.split(b'\x00')[0].decode('utf-8', errors='ignore')
print(f"Bytes {offset}-{offset+63}: NodeReport = '{node_report}'")
offset += 64

# NumPorts
print(f"\n--- PORT CONFIGURATION ---")
print(f"Bytes {offset}-{offset+1}: NumPorts")
num_ports_hi = reply[offset]
num_ports_lo = reply[offset+1]
num_ports = (num_ports_hi << 8) | num_ports_lo
print(f"  Hi byte (offset {offset}): {num_ports_hi}")
print(f"  Lo byte (offset {offset+1}): {num_ports_lo}")
print(f"  NumPorts = {num_ports}")
offset += 2

# PortTypes (4 bytes)
print(f"\nBytes {offset}-{offset+3}: PortTypes")
for i in range(4):
    port_type = reply[offset + i]
    print(f"  Port {i} (offset {offset+i}): 0x{port_type:02X} ", end="")
    if port_type == 0x40:
        print("(Input)")
    elif port_type == 0x80:
        print("(Output)")
    elif port_type == 0xC0:
        print("(Input+Output)")
    else:
        print("(Not used)")
offset += 4

# GoodInput (4 bytes)
print(f"\nBytes {offset}-{offset+3}: GoodInput")
for i in range(4):
    good_input = reply[offset + i]
    print(f"  Port {i} (offset {offset+i}): 0x{good_input:02X}")
offset += 4

# GoodOutput (4 bytes)
print(f"\nBytes {offset}-{offset+3}: GoodOutput")
for i in range(4):
    good_output = reply[offset + i]
    print(f"  Port {i} (offset {offset+i}): 0x{good_output:02X}")
offset += 4

# SwIn (4 bytes)
print(f"\nBytes {offset}-{offset+3}: SwIn (Input Universe)")
for i in range(4):
    sw_in = reply[offset + i]
    print(f"  Port {i} (offset {offset+i}): {sw_in}")
offset += 4

# SwOut (4 bytes)
print(f"\nBytes {offset}-{offset+3}: SwOut (Output Universe)")
for i in range(4):
    sw_out = reply[offset + i]
    print(f"  Port {i} (offset {offset+i}): {sw_out}")
offset += 4

print(f"\nByte {offset}: SwVideo = {reply[offset]}")
offset += 1

print(f"Byte {offset}: SwMacro = {reply[offset]}")
offset += 1

print(f"Byte {offset}: SwRemote = {reply[offset]}")
offset += 1

print(f"Bytes {offset}-{offset+2}: Spare = {reply[offset:offset+3].hex()}")
offset += 3

print(f"Byte {offset}: Style = {reply[offset]} ", end="")
if reply[offset] == 0:
    print("(StNode)")
elif reply[offset] == 1:
    print("(StController)")
else:
    print(f"(Unknown)")
offset += 1

print(f"\nBytes {offset}-{offset+5}: MAC = {reply[offset:offset+6].hex()}")
offset += 6

print(f"Bytes {offset}-{offset+3}: BindIp = {'.'.join(str(b) for b in reply[offset:offset+4])}")
offset += 4

print(f"Byte {offset}: BindIndex = {reply[offset]}")
offset += 1

print(f"Byte {offset}: Status2 = 0x{reply[offset]:02X}")
offset += 1

print(f"Bytes {offset}-{offset+25}: Filler = {reply[offset:offset+26].hex()}")
offset += 26

print(f"\nFinal offset: {offset} (packet size: {len(reply)})")

print("\n" + "=" * 80)
print("SUMMARY FOR DEPENCE UNICAST")
print("=" * 80)
print(f"✓ NumPorts: {num_ports} (should be 4 for max compatibility)")
print(f"✓ PortTypes: {['Input' if reply[offset-142+i] == 0x40 else 'Not used' for i in range(4)]}")
print(f"✓ Style: {'StNode (correct)' if reply[offset-27] == 0 else 'StController (WRONG)'}")
print("\nThis node should appear in Depence as an INPUT device with 4 ports.")
print("=" * 80)
