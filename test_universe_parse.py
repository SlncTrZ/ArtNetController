import struct

# Simulate MADRIX packet with universe 236
# Universe 236 = 0x00EC
# Little Endian: EC 00

payload_236 = bytes([
    0x01,  # Sequence
    0x00,  # Physical
    0xEC, 0x00,  # Universe 236 (Little Endian)
    0x02, 0x00,  # Length (Big Endian) = 2
    0xFF, 0x7F,  # DMX data (2 bytes)
])

universe = struct.unpack('<H', payload_236[2:4])[0]
length = struct.unpack('>H', payload_236[4:6])[0]

print(f"Universe: {universe} (expected: 236)")
print(f"Length: {length} (expected: 2)")
print(f"Bytes: {payload_236[2]:02x} {payload_236[3]:02x}")
