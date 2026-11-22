# Apple Accessory Spatial Audio & Sensor Telemetry Architectures

> **Status: unverified research notes.** Only the AACP head-tracking opcode (`0x17`) and the model number
> A2096 (AirPods Max) are corroborated. Product codenames (B515, B288, B494, B515c), the "Max 2 A3454"
> model number, the `SensorDataWX` frame layout (58 bytes, Q15 quaternion) and the authentication gate for
> each generation could not be confirmed against public sources. Treat them as hypotheses.

## 1. Architectural Divergence Across Generations

Apple's implementation of head tracking and motion telemetry evolved through two distinct generations:

| Feature | Generation 1 (AirPods Max 1st Gen A2096) | Generation 2+ (AirPods Pro 1/2, Max 2 A3454) |
|---|---|---|
| **Apple Codename** | B515 | B288, B494, B515c |
| **Connector** | Lightning | Lightning / USB-C |
| **Spatial Capability Flag (`0xC0`)** | **Absent** | Present |
| **Sensor Transport** | `B2PRelayHIDDevice` (Service 5) & `cma` (Service 3) | `SensorWX` (AACP Bit 20, `0x100000`) |
| **Payload Format** | HID Report Descriptors / RTBuddy XML | Protobuf `SensorDataWX` frames |
| **Access Gate** | `<key>ProtectedAccess</key><true/>` (Requires `accKey`) | Open / Unauthenticated |
| **Third-Party Streaming** | Requires authentic MagicPairing authentication | Direct streaming via standard RTBuddy commands |

---

## 2. Generation 2+: SensorWX Protobuf Stream

On AirPods Pro 1/2 and AirPods Max 2, the host initiates streaming by issuing a `ServiceSetting` packet over opcode `0x17`:
```
04 00 04 00 17 00 [ServiceSetting Payload]
```
The accessory immediately streams 58-byte `SensorDataWX` frames containing:
- Sensor sequence number
- Device timestamp
- Fused orientation quaternion in Q15 fixed-point format:
  $$\mathbf{q} = \begin{bmatrix} w & x & y & z \end{bmatrix}^T$$
- Calibrated angular velocity and linear acceleration vectors

---

## 3. Generation 1: CMA & ProtectedAccess

On AirPods Max 1st gen (`A2096`), the firmware advertises its services via RTBuddy XML plists:
```xml
<key>ProtectedAccess</key><true/>
<key>AccessoryService</key><string>devmotion6</string>
...
<key>ProtectedAccess</key><true/>
<key>AccessoryService</key><string>cma</string>
```

- **ProtectedAccess Gate**: The accessory verifies that the host has completed the authenticated MagicPairing handshake using `accKey`.
- If the host is unauthenticated (standard Bluetooth connection), the firmware acknowledges handshake commands but suppresses motion packet generation.
