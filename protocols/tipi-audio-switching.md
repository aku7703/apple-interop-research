# Apple Triangle Protocol (TiPi) & Audio Switching Specification

> **Status: informal research notes.** Opcode `0x2E` (connected devices), `0x0E` (audio source),
> `0x09` (ownership control) and the audio-state values (0 none / 1 call / 2 media) agree with the
> public community reference. The following are **unverified**: the `0x0C` and `0x15` layouts, the `0x4E`
> acknowledgement, the OPACK field names and `reason` strings, the priority-tier hierarchy,
> and the handoff UI text. Treat them as hypotheses to confirm against your own captures.

## 1. Overview & Architecture

The Triangle Protocol (TiPi) is Apple's proprietary framework for seamless multi-device audio arbitration across the accessory ecosystem. Instead of requiring users to manually disconnect and reconnect Bluetooth audio across iPhones, iPads, Macs, and Apple Watches, TiPi enables dynamic audio routing while preserving simultaneous Bluetooth connections.

```
                   +-----------------------+
                   |    AirPods / Beats    |
                   |   (Central Accessory) |
                   +-----------+-----------+
                               |
               +---------------+---------------+
               | AACP / A2DP                   | AACP / A2DP
               v                               v
    +--------------------+           +--------------------+
    |    Apple Host A    |< - - - - >|  Apple / PC Host B |
    |      (iPhone)      | BLE Advert|      (Mac / PC)    |
    +--------------------+ & CloudKit+--------------------+
```

### Key Principles
1. **Multi-Point Coordination**: The accessory maintains concurrent Bluetooth links (ACL connections) to registered ecosystem peers.
2. **Dynamic DAC Routing**: The accessory's internal digital signal processor (DSP) switches DAC inputs without tearing down transport links.
3. **Intent & Priority Arbitration**: Handover is negotiated based on content priority (telephony vs. media vs. ambient) communicated via structured AACP packets.

---

## 2. Core Protocol Opcodes

### 2.1. Opcode `0x2E`: Ecosystem Table (`TIPI_TABLE`)
Broadcast by the accessory to inform connected hosts of all registered ecosystem devices and their current routing states.

- **Direction**: Accessory -> Host
- **Framing**:
```
[0..3]  04 00 04 00    AACP Prefix
[4..5]  2E 00          Opcode 0x2E
[6]     u8             TiPi Protocol Version (typically 0x01)
[7]     u8             Overall Audio State (0 = None, 1 = SCO/Call, 2 = A2DP/Media)
[8]     u8             Entry Count (N)
[9..]   N x 8 bytes    Device Records
```

- **Device Record Structure (8 bytes per peer)**:
```
[0..5]  BD_ADDR        Bluetooth MAC address (6 bytes, Big-Endian in table)
[6]     u8             Device Routing Status:
                         0x00 = Inactive / Disconnected
                         0x01 = Connected (Standby / Idle)
                         0x02 = Active Audio Owner (Streaming to DAC)
[7]     u8             Link & Feature Flags:
                         Bit 0 (0x01) = Low-latency mode
                         Bit 1 (0x02) = UTP link established
```

---

### 2.2. Opcode `0x0C`: Device State & PerfStats (`DEVICE_STATE`)
Carries incremental state changes or link performance statistics for an individual peer.

- **Direction**: Accessory -> Host
- **Framing**:
```
[0..3]  04 00 04 00    AACP Prefix
[4..5]  0C 00          Opcode 0x0C
[6..11] BD_ADDR        Target device MAC address (Little-Endian)
[12]    u8             Audio State:
                         0x00 = Inactive / None
                         0x01 = Telephony / SCO active
                         0x02 = Media / A2DP streaming
[13]    u8             Link / Transport flags
```

---

### 2.3. Opcode `0x11`: Smart Routing Intent (`SMART_ROUTING`)
Transmitted when a host announces audio playback intent or state transitions. The payload contains a compact binary-encoded dictionary (Apple OPACK format).

- **Direction**: Per the public community reference, the host sends its routing relay on opcode `0x10`, and the accessory's response arrives on `0x11` (Accessory -> Host).
- **Key OPACK Dictionary Fields**:
  - `playingApp` (`string`): Bundle identifier of the active foreground app (e.g., `com.apple.Music`, `com.spotify.client`, `com.apple.InCallService`).
  - `hostStreamingState` (`bool`): `true` when the host is actively rendering audio buffers to the Bluetooth driver.
  - `otherDeviceAudioCategory` (`int`): Audio session category / priority tier.
  - `callState` (`bool`): `true` if an active cellular, FaceTime, or VoIP call is ongoing.
  - `reason` (`string`): Trigger string explaining the routing assertion (e.g., `"UserPlaybackInitiated"`, `"CallIncoming"`, `"SR Hijack"`).

---

### 2.4. Opcode `0x15`: Triangle Previous Device (`TRIANGLE_PREVIOUS`)
When the accessory shifts audio focus to a new host, it immediately informs that host which partner device previously owned the audio link.

- **Direction**: Accessory -> Host
- **Framing**:
```
[0..3]  04 00 04 00    AACP Prefix
[4..5]  15 00          Opcode 0x15
[6..11] BD_ADDR        Bluetooth address of previous owner (Little-Endian)
```
- **Host Response**: Authentic hosts acknowledge with Opcode `0x4E` (`PROX_CARD_STATUS`) with payload `01 00 00 00 00 00 00 00`.

---

### 2.5. Opcode `0x09`: Audio Ownership Claim (`DEVICE_CONTROL`)
Sent by a host to assert explicit ownership of the audio pipeline.

- **Direction**: Host -> Accessory
- **Framing** (fixed-length control command: 4-byte prefix, opcode, then 5 data bytes; layout per public community documentation):
```
[0..3]  04 00 04 00    AACP Prefix
[4..5]  09 00          Opcode 0x09
[6]     u8             Control identifier: 0x06 = "owns connection"
[7]     u8             Value: 0x01 = enabled (owns = 1), 0x02 = disabled
[8..10] 00 00 00       Unused (zero)
```

---

## 3. Arbitration State Machine & Priority Hierarchy

When multiple devices attempt to stream audio simultaneously, TiPi enforces a strict priority hierarchy:

```
+-------------------------------------------------------------+
| Priority Tier 1: Emergency & Telephony (SCO / VoIP)         |
| Active cellular call, FaceTime, Zoom, Teams                 |
| (Preempts all media streams across all devices)             |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| Priority Tier 2: User-Initiated Media (A2DP)                |
| Explicit user press on Play (Music, YouTube, Podcasts)      |
| (Preempts passive/background audio; triggers banner alert)  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| Priority Tier 3: Passive & Ambient Sounds                   |
| Web page autoplay, background notifications, UI sound effects|
| (Yields automatically to existing media playback)           |
+-------------------------------------------------------------+
```

### Handoff Sequence Example:
1. **Device A** is playing music (`AudioState = 2`, `playingApp = "com.apple.Music"`).
2. **Device B** receives an incoming cellular call (`callState = true`).
3. **Device B** transmits Opcode `0x11` with `otherDeviceAudioCategory = 1`.
4. The accessory's DSP switches audio input to **Device B** and transmits Opcode `0x0C` (`AudioState = 1`) and `0x2E` to **Device A**.
5. **Device A** receives the update and automatically pauses local playback, presenting a notification: *"Moved to [Device B]"*.

---

## 4. Implementation Guidelines for Third-Party Platforms

When integrating non-Apple platforms (e.g., Windows or Linux) into a TiPi environment:

1. **Call Protection**: Inspect incoming Opcode `0x11` (`callState == true`) and `0x0C` (`AudioState == 1`). Third-party hosts must avoid asserting playback ownership (`0x09`) if another peer is on an active telephone call.
2. **App-Specific Hold Rules**: Respect user-configured protected applications (such as ongoing meetings or music playback) by suppressing automatic takeover until the stream terminates.
3. **Host Feature Emulation**: To participate as a first-class peer in the mesh, the host should advertise compatibility flags via Opcode `0x4D` on connection.
