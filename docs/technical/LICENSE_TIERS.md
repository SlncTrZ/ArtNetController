# DMX Master LTS - License Tiers

## Overview

DMX Master LTS offers two license tiers to suit different user needs:

- **FREE Version** - Limited to 4 universes, perfect for small installations
- **LICENSED Version** - Full 512 universes, professional-grade capabilities

---

## Feature Comparison

| Feature | FREE Version | LICENSED Version |
|---------|--------------|------------------|
| **Universe Limit** | **4 universes** (U0-U3) | **512 universes** (U0-U511) |
| Art-Net Send/Receive | ✅ Universe 0-3 | ✅ Universe 0-511 |
| DMX Recording | ✅ Universe 0-3 only | ✅ All 512 universes |
| Show Playback | ✅ Universe 0-3 only | ✅ All 512 universes |
| IOBoard Serial Output | ✅ Board #1 (U0-U1) only | ✅ Multiple boards (auto-mapping) |
| DMX View/Monitor | ✅ Universe 0-3 | ✅ Universe 0-511 |
| Hardware Manager | ✅ Full Access | ✅ Full Access |
| Show Management | ✅ Full Access | ✅ Full Access |
| Timecode Sync | ✅ Supported | ✅ Supported |
| Web Upload Server | ✅ Supported | ✅ Supported |
| Trial Period | **7 days** | N/A (Perpetual) |

---

## FREE Version Details

### What You Get:
- **4 Art-Net Universes** (Universe 0, 1, 2, 3)
- **7-day trial period** before requiring license activation
- Perfect for:
  - Small shows (up to 2048 DMX channels)
  - Home installations
  - Testing and evaluation
  - Learning Art-Net protocol

### Limitations:
- Cannot send/receive Art-Net data on Universe 4+
- Recording only captures Universe 0-3
- Playback skips Universe 4+ automatically
- IOBoard serial output limited to first board (U0-U1)

### Trial Mode:
- **7 days** from first installation
- Full FREE version features during trial
- After trial expires: Must activate license or continue with FREE version

---

## LICENSED Version Details

### What You Get:
- **512 Art-Net Universes** (Universe 0-511)
- **Perpetual license** (no expiration)
- **Hardware-bound** (tied to your device)
- **Offline validation** (works without internet)
- Perfect for:
  - Large venues and theaters
  - Professional lighting designers
  - Complex multi-universe shows
  - Commercial installations

### Technical Specs:
- **Art-Net Ports**: 128 PollReply packets (4 universes each)
- **Network Mapping**: Net 0-7, Subnet 0-15, Universe 0-15
- **Total DMX Channels**: 261,632 channels (512 × 512)
- **IOBoard Support**: Unlimited boards with auto-mapping
- **Recording**: All 512 universes simultaneously
- **Playback**: Full show playback across all universes

### License Activation:
1. Get Device ID from `Help > License Info`
2. Contact admin with Device ID
3. Receive license key (JSON format)
4. Activate via `Help > Activate License`
5. Restart application (license active immediately)

---

## Art-Net Universe Mapping

### FREE Version (4 Universes)
```
Universe 0 → Net 0, Subnet 0, Universe 0
Universe 1 → Net 0, Subnet 0, Universe 1
Universe 2 → Net 0, Subnet 0, Universe 2
Universe 3 → Net 0, Subnet 0, Universe 3
```

### LICENSED Version (512 Universes)
```
Universe 0-15   → Net 0, Subnet 0, Universe 0-15
Universe 16-31  → Net 0, Subnet 1, Universe 0-15
Universe 32-47  → Net 0, Subnet 2, Universe 0-15
...
Universe 496-511 → Net 7, Subnet 15, Universe 0-15
```

**Formula**: `Universe = (Net × 64) + (Subnet × 16) + UniverseAddr`

---

## IOBoard Serial Output

### FREE Version:
- **Board #1 only** → Universe 0, 1
- Additional boards ignored

### LICENSED Version:
- **Board #1** → Universe 0, 1
- **Board #2** → Universe 2, 3
- **Board #3** → Universe 4, 5
- **Board #N** → Universe [(N-1)×2, (N-1)×2+1]

---

## How to Upgrade

### From FREE to LICENSED:

1. **Get Device ID**:
   - Open DMX Master
   - Go to `Help > License Info`
   - Copy your Device ID

2. **Request License**:
   - Contact: [Your Email]
   - Provide: Device ID + Purchase receipt
   - Receive: License key (JSON file)

3. **Activate License**:
   - Open DMX Master
   - Go to `Help > Activate License`
   - Paste license key
   - Click "Activate"
   - Restart application

4. **Verify Activation**:
   - Status bar shows: `✓ LICENSED - 512 Universes`
   - Universe dropdown shows: Universe 0-511
   - All features unlocked

---

## Technical Implementation

### License Validation:
- **Offline**: RSA-2048 signature verification
- **Hardware Binding**: SHA-256 hash of MAC + CPU Serial
- **Online Check**: Periodic revocation check (optional)
- **Encryption**: AES-256-GCM for license file

### Universe Filtering:
- **Art-Net Send**: Blocked at controller level
- **Art-Net Receive**: Filtered at packet handler
- **Recording**: Frames dropped silently
- **Playback**: Frames skipped during playback
- **Serial Output**: Validated before transmission

### Security:
- ✅ Cannot bypass license check
- ✅ Cannot edit license file (encrypted)
- ✅ Cannot transfer license to another machine
- ✅ Cannot forge license signature (RSA)
- ✅ Cannot use cracked license (revocation list)

---

## FAQ

### Q: Can I test LICENSED version before buying?
**A**: Yes! 7-day trial includes all FREE version features (4 universes). Contact us for evaluation license with 512 universes.

### Q: What happens after trial expires?
**A**: FREE version continues working with 4 universes. No functionality loss.

### Q: Can I transfer license to another computer?
**A**: No. License is hardware-bound. Contact us for license transfer (may require fee).

### Q: How many devices can use one license?
**A**: One license = One device. Multi-device licenses available (contact us).

### Q: Does LICENSED version require internet?
**A**: No. Offline validation works without internet. Optional online revocation check every 24h.

### Q: Can I use FREE version commercially?
**A**: Yes, but limited to 4 universes. LICENSED version recommended for professional use.

### Q: How do I check my current license status?
**A**: Look at status bar (bottom-left):
- `🆓 FREE Version - 4 Universes` = FREE
- `✓ LICENSED - 512 Universes` = LICENSED

---

## Support

- **Email**: [Your Support Email]
- **GitHub**: https://github.com/truongcongdinh97/DMX-Master
- **Documentation**: [Your Docs URL]

---

**DMX Master LTS** - Professional Art-Net Lighting Controller
Version 1.3.0 and later
