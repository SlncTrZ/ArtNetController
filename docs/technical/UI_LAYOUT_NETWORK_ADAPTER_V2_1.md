## NETWORK ADAPTER SELECTION - UI LAYOUT (V2.1)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Settings Tab                                                        │
├─────────────────────────────────────────────────────────────────────┤
│  │ Network Info │ Shows │ System │                                  │
│  └───────────────────────┘                                          │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  📋 STARTUP SETTINGS (ADMINISTRATOR ONLY)                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Start with Windows:        [  ] Checkbox                    │   │
│  │ ⚠️ Run as Administrator to enable this feature              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  📋 LOGGING SETTINGS (ADMINISTRATOR ONLY)                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Enable Logging:            [✓] Checkbox                     │   │
│  │ Log Level:                 [INFO ▼]                         │   │
│  │ ⚠️ Run as Administrator to modify logging settings           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  📋 NETWORK ADAPTER SELECTION (V2.1)  ← NEW FEATURE HERE            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│ Network Adapter:   [Ethernet (<IP thực tế>)           ▼]       │   │
│                    ┌──────────────────────────────┐          │   │
│                    │ ✓ Ethernet (<IP thực tế>)  │ ← Selected
│                    │   WiFi (<IP thực tế>)      │          │   │
│                    │   Loopback (127.0.0.1)      │          │   │
│                    │   Broadcast (0.0.0.0)       │          │   │
│                    └──────────────────────────────┘          │   │
│                                                               │   │
│ Adapter IP:        <IP thực tế của adapter được chọn>        │   │
│  │                    (color: #0066cc, bold)                    │   │
│  │                                                               │   │
│  │ ℹ️ Selected adapter will receive incoming Art-Net packets.  │   │
│  │    For best compatibility with Depence/Resolume, select     │   │
│  │    your primary network interface.                           │   │
│  │    Changes take effect after restarting the application.    │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  📋 ARTNET TIMECODE                                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Send Timecode During Playback:  [✓] Checkbox              │   │
│  │                                                               │   │
│  │ ℹ️ When enabled, DMX Master will broadcast ArtNet           │   │
│  │    Timecode (OpCode 0x9700) to all devices on the network  │   │
│  │    during show playback...                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  📋 PERFORMANCE                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Playback Buffer:           [100 ▼ frames]                  │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  [Load Settings] [Save Settings] [Reset to Defaults] ... [Apply] │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘


ADAPTER SELECTION INTERACTION:

1️⃣  User clicks dropdown
    ↓
┌──────────────────────────────────────────┐
│ Ethernet (192.168.1.13)  ←← Currently Selected (shows checkmark)
│ WiFi (10.0.0.5)
│ Loopback (127.0.0.1)
│ Broadcast (0.0.0.0)
└──────────────────────────────────────────┘

2️⃣  User selects "WiFi (10.0.0.5)"
    ↓
    IP Label updates to: "10.0.0.5"

3️⃣  User clicks "Apply" or "Save Settings"
    ↓
    Saves config: artnet.bind_ip = "10.0.0.5"
    ↓
    Popup Message:
    ╔════════════════════════════════════════════╗
    ║ Settings Saved                             ║
    ╠════════════════════════════════════════════╣
    ║ Settings have been saved successfully.    ║
    ║                                            ║
    ║ Please restart the application for        ║
    ║ network adapter changes to take effect.   ║
    ║                                            ║
    ║                                 [OK]       ║
    ╚════════════════════════════════════════════╝
    ↓
4️⃣  User closes and restarts app
    ↓
    init_artnet_controller() loads config:
    bind_ip = load_config('artnet.bind_ip') = "10.0.0.5"
    ↓
    socket.bind(("10.0.0.5", 6454))
    ↓
    ✅ Art-Net receiver now listens on WiFi adapter


════════════════════════════════════════════════════════════════════════════


COMBOBOX OPTIONS DISPLAY:

Adapter Type             Display Format          notes
─────────────────────────────────────────────────────────────────────────
Physical Network         "Ethernet (192.168.1.10)"    ← Primary for LAN
Physical Network         "WiFi (10.0.0.5)"            ← WiFi adapter
Loopback                 "Loopback (127.0.0.1)"       ← Local machine
Broadcast Mode           "Broadcast (0.0.0.0)"        ← All interfaces


════════════════════════════════════════════════════════════════════════════


TOOLTIP EXAMPLES:

When hovering over "Network Adapter:" label:
┌────────────────────────────────────────────────────────────┐
│ Select which network adapter to use for Art-Net            │
│ communication.                                              │
│ This affects incoming DMX reception and device discovery. │
│ Change requires restart of the application.                │
└────────────────────────────────────────────────────────────┘

When hovering over "Broadcast (0.0.0.0)" option:
┌────────────────────────────────────────────────────────────┐
│ Listen on all interfaces (broadcast mode).                 │
│ Note: Windows 0.0.0.0 binding receives broadcast only.    │
└────────────────────────────────────────────────────────────┘

When hovering over "Loopback (127.0.0.1)" option:
┌────────────────────────────────────────────────────────────┐
│ Use this if Depence 3D is running on the same computer.   │
│ Loopback interface only communicates within the machine.   │
└────────────────────────────────────────────────────────────┘


════════════════════════════════════════════════════════════════════════════
EXAMPLE CONFIGURATION SCENARIOS: 

Scenario A: Depence on Same Machine
────────────────────────────────────
Select: Loopback (127.0.0.1)
Result: App binds to 127.0.0.1:6454
Benefits: Fast local communication, low latency
         
Scenario B: Depence on LAN (recommended)
──────────────────────────────────────────
Network: 192.168.1.0/24 with Ethernet card at 192.168.1.13
Select: Ethernet (192.168.1.13)
Result: App binds to 192.168.1.13:6454
        Receives: Depence unicast packets + local broadcast
Benefits: Works with Depence unicast (no 255.255.255.255 needed)
         
Scenario C: Multiple Adapters (Advanced)
──────────────────────────────────────────
System has: Ethernet + WiFi + Loopback
Select: WiFi (10.0.0.5) if Depence connected via WiFi
Result: App binds to 10.0.0.5:6454
        Secondary loopback socket on 127.0.0.1:6454 (auto-created)
Benefits: Can receive from WiFi + local apps
         
Scenario D: Broadcast Mode Legacy
──────────────────────────────────
Legacy systems with no unicast support
Select: Broadcast (0.0.0.0)
Note: On Windows, this receives broadcast only
      (not unicast packets)
Best For: Media servers, lighting consoles using broadcast


════════════════════════════════════════════════════════════════════════════
