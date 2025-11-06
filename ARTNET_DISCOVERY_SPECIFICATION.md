# Art-Net Node Discovery - Technical Specification

## Overview
DMX Master LTS implements Art-Net 4 compliant node discovery using **ArtPoll** and **ArtPollReply** packets as defined in the Art-Net specification.

---

## Art-Net Poll (Node Discovery)

### Implementation
**File:** `src/artnet/controller.py`
**Method:** `poll_network()`

### Packet Structure
```python
ArtNetPoll Packet:
- Header: "Art-Net\0" (8 bytes)
- OpCode: 0x2000 (Little Endian)
- Flags: 0x06 (TalkToMe + Diagnostics)
- Priority: 0x00
```

### Broadcast Mechanism
- **Destination:** `255.255.255.255:6454` (broadcast)
- **Protocol:** UDP
- **Interval:** On-demand (user trigger from Hardware Manager)

### Code
```python
def poll_network(self):
    """Gửi Art-Net Poll để discover nodes"""
    if not self.running or not self.socket:
        return
        
    try:
        poll_packet = ArtNetPoll()
        self.socket.sendto(poll_packet.pack(), ('255.255.255.255', self.port))
        logger.debug("Sent Art-Net Poll")
        
    except Exception as e:
        logger.error(f"Failed to send poll: {e}")
```

---

## Art-Net PollReply (Node Response)

### Receiving PollReply
**Method:** `_handle_poll_reply(payload: bytes, addr: tuple)`

### Packet Parsing (Art-Net 4 Compliant)

#### Critical Fields Parsed:
1. **ShortName** (Byte 18-35, 18 bytes)
   - Null-terminated UTF-8 string
   - Node identifier for display

2. **LongName** (Byte 36-99, 64 bytes)
   - Null-terminated UTF-8 string
   - Detailed node description

3. **NumPorts** (Byte 164-165)
   - **Byte 164:** NumPortsHi (high byte)
   - **Byte 165:** NumPortsLo (low byte)
   - **Formula:** `port_count = (hi << 8) | lo`
   - **V2.0 Feature:** Unlimited port support (no cap)

4. **SubSwitch** (Byte 11)
   - Subnet address (0-15)

5. **NetSwitch** (Byte 10)
   - Network address

6. **Universe** (Calculated)
   - `universe = (net_switch << 8) | sub_switch`

7. **Status1** (Byte 15)
   - Node status byte

### Self-Discovery Prevention
```python
# V2.0: Ignore poll replies from ourselves
import socket as sock
s = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
local_ip = s.getsockname()[0]
s.close()

if ip_address == local_ip or ip_address == "127.0.0.1":
    logger.debug(f"Ignoring poll reply from self: {ip_address}")
    return
```

### Node Storage
```python
@dataclass
class ArtNetNode:
    """Thông tin một node Art-Net"""
    ip_address: str
    short_name: str
    long_name: str
    universe: int
    port_count: int
    node_type: int = 0
    last_seen: float = 0
```

---

## Sending PollReply (Acting as Node)

### When to Send
**Trigger:** When receiving **ArtPoll** from other controllers
**Method:** `_handle_poll(payload: bytes, addr: tuple)`

### Multi-Universe Support (V2.1)
DMX Master supports **unlimited universes** using multiple PollReply packets:

#### Strategy
- Each PollReply advertises **4 consecutive universes** via `SwIn[4]`
- Uses Subnet addressing for 16+ universes
- Formula: `Universe = (SubNet << 4) | SwIn`

#### Example Configurations

**8 Universes (2 PollReplies):**
```
Reply 1: SubNet=0, SwIn=[0,1,2,3]   → Universe 0-3
Reply 2: SubNet=0, SwIn=[4,5,6,7]   → Universe 4-7
```

**16 Universes (4 PollReplies):**
```
Reply 1: SubNet=0, SwIn=[0,1,2,3]   → Universe 0-3
Reply 2: SubNet=0, SwIn=[4,5,6,7]   → Universe 4-7
Reply 3: SubNet=0, SwIn=[8,9,10,11] → Universe 8-11
Reply 4: SubNet=0, SwIn=[12,13,14,15] → Universe 12-15
```

**32 Universes (8 PollReplies):**
```
SubNet 0: 4 replies (Universe 0-15)
SubNet 1: 4 replies (Universe 16-31)
```

### PollReply Packet Structure (239 bytes)
```
Header: "Art-Net\0"                (8 bytes)
OpCode: 0x2100                     (2 bytes, Little Endian)
IP Address                         (4 bytes)
Port: 0x1936                       (2 bytes, Little Endian = 6454)
VersInfo: 0x0200                   (2 bytes, Big Endian = v2.0)
NetSwitch: 0x00                    (1 byte)
SubSwitch: subnet                  (1 byte) ← VARIABLE per reply
Oem: 0xFFFF                        (2 bytes, Big Endian)
UbeaVersion: 0x00                  (1 byte)
Status1: 0x00                      (1 byte)
EstaMan: 0xFFFF                    (2 bytes, Little Endian)
ShortName: "DMX U{start}-{end}"    (18 bytes, null-terminated)
LongName: "DMX Master LTS..."      (64 bytes, null-terminated)
NodeReport: "#0001 [0000] Ready"   (64 bytes)
NumPorts: 0x0004                   (2 bytes) ← Always 4
PortTypes[4]: [0x40, 0x40, 0x40, 0x40]  (4 bytes) ← All Input
GoodInput[4]: [0x08, 0x08, 0x08, 0x08]  (4 bytes) ← All enabled
GoodOutput[4]: [0x00, 0x00, 0x00, 0x00] (4 bytes)
SwIn[4]: [sw_in[0-3]]              (4 bytes) ← VARIABLE per reply
SwOut[4]: [0x00, 0x00, 0x00, 0x00] (4 bytes)
SwVideo: 0x00                      (1 byte)
SwMacro: 0x00                      (1 byte)
SwRemote: 0x00                     (1 byte)
Spare: 0x000000                    (3 bytes)
Style: 0x00                        (1 byte) ← StNode
MAC: 0x000000000000                (6 bytes)
BindIp                             (4 bytes)
BindIndex: 0x01                    (1 byte)
Status2: 0x07                      (1 byte)
Filler: 0x00...                    (26 bytes)
---
Total: 239 bytes
```

### Critical Implementation Details

#### 1. SubNet & SwIn Calculation
```python
num_replies = (max_universes + 3) // 4  # Round up

for i in range(num_replies):
    subnet = i // 4              # Each subnet = 16 universes
    base_universe = i * 4
    sw_in = [(base_universe + j) % 16 for j in range(4)]
    
    reply = self._create_poll_reply(subnet=subnet, sw_in=sw_in)
    self.socket.sendto(reply, addr)
```

#### 2. Dynamic ShortName
```python
start_uni = (subnet << 4) | sw_in[0]
end_uni = (subnet << 4) | sw_in[3]

if start_uni == 0 and end_uni == 3:
    short_name = "DMX Master"
else:
    short_name = f"DMX U{start_uni}-{end_uni}"
```

#### 3. Port Configuration
```python
# PortTypes (4 bytes) - All Input-capable
for i in range(4):
    packet.append(0x40)  # Bit 6 = Input capable

# GoodInput (4 bytes) - All enabled
for i in range(4):
    packet.append(0x08)  # Bit 3 = Power/Input enabled

# SwIn (4 bytes) - Universe addresses
for i in range(4):
    packet.append(sw_in[i] & 0x0F)  # Low 4 bits only
```

---

## Compatibility

### Tested With:
- ✅ **Depence** (Art-Net lighting simulator)
- ✅ **MADRIX** (LED control software)  
- ✅ **Resolume Arena** (VJ software)
- ✅ **QLC+** (Open-source lighting control)

### Art-Net 4 Compliance:
- ✅ Correct OpCodes (0x2000, 0x2100)
- ✅ Little/Big Endian byte order per spec
- ✅ 239-byte PollReply structure
- ✅ Subnet addressing for 16+ universes
- ✅ Self-discovery prevention
- ✅ Broadcast to 255.255.255.255:6454
- ✅ Port 6454 (0x1936 in Little Endian)

---

## User Interface

### Hardware Manager Tab
**Location:** Main Window → Hardware Manager

**Features:**
1. **Discover Button**
   - Sends ArtPoll broadcast
   - Refreshes node list

2. **Node List Table**
   - Columns: IP, Name, Universe, Ports, Last Seen
   - Real-time updates when nodes respond

3. **Configure Universe Mapping** (Admin only)
   - Maps discovered nodes to software universes

---

## Logging

### Discovery Events
```
🔍 Sent Art-Net Poll
✅ Discovered Art-Net node: 192.168.1.50 - Depence - 4 ports
   Long Name: Depence Art-Net Node
   Universe: 0, Status: 00
```

### PollReply Sending
```
Sending 2 PollReply packets for 8 universes
Sent PollReply #1/2: SubNet=0 SwIn=[0,1,2,3] → Universe 0-3 to 192.168.1.100
Sent PollReply #2/2: SubNet=0 SwIn=[4,5,6,7] → Universe 4-7 to 192.168.1.100
```

---

## Configuration

### Default Settings
```python
PORT = 6454                    # Art-Net standard port
BROADCAST = '255.255.255.255'  # Broadcast address
MAX_UNIVERSES = 32             # Configurable in config
```

### Config File
```json
{
  "universes": {
    "max_universes": 32
  }
}
```

---

## Troubleshooting

### Common Issues

#### 1. "No nodes discovered"
**Causes:**
- Firewall blocking UDP port 6454
- Not on same network subnet
- Other software using port 6454

**Solutions:**
- Allow UDP 6454 in Windows Firewall
- Check network connection
- Close other Art-Net software

#### 2. "Node appears multiple times"
**Cause:** Multiple PollReply packets per node (expected for multi-universe)

**Solution:** This is normal - each reply advertises 4 universes

#### 3. "Self-discovered as node"
**Fix:** V2.0 auto-filters self-replies using local IP detection

---

## Future Enhancements

### Planned Features:
- [ ] RDM (Remote Device Management) support
- [ ] sACN (E1.31) protocol support
- [ ] Node timeout and auto-removal
- [ ] IPv6 support
- [ ] Art-Net 5 compatibility

---

## References

- **Art-Net 4 Specification:** https://art-net.org.uk/
- **Art-Net OpCodes:** https://art-net.org.uk/structure/packet-opcodes/
- **UDP Broadcast:** RFC 919

---

**Document Version:** 1.0
**Last Updated:** 2025-11-06
**Author:** Trương Công Định
