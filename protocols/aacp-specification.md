# Apple Accessory Protocol (AACP) Specification

> **Status: informal research notes, not an authoritative specification.** Names and
> layouts come from independent observation. Where a public community reference
> (open-source community documentation of AACP) overlaps,
> the table in section 4 records whether it agrees. Anything marked *unverified* has no
> independent corroboration. Field names are descriptive labels, not Apple's.

## 1. Transport & Framing

Communication occurs over a dedicated Bluetooth Classic L2CAP channel (PSM `0x1001`). *(Corroborated.)*

Packets utilize a standardized 6-byte header:
```
[0..3]  04 00 04 00   Fixed packet prefix
[4..5]  u16 LE        Opcode
[6..]   Payload (variable length)
```
Note: a separate handshake packet that does not use this prefix is required before the accessory responds to any packet (documented in public community notes).

---

## 2. Opcode Dispatch Table

| Opcode | Identifier | Description | Direction |
|---|---|---|---|
| `0x02` | `CAPABILITIES_RESP` | Accessory capability descriptors (12–16 entries) | Accessory -> Host |
| `0x04` | `BATTERY_STATUS` | Ear cup / case battery percentages and charging states | Accessory -> Host |
| `0x06` | `EAR_DETECTION` | Placement state (on-head / in-ear / removed) | Accessory -> Host |
| `0x08` | `ACOUSTIC_FIT_DRC` | Acoustic seal pass/fail and dynamic range control (DRC) targets | Bidirectional |
| `0x09` | `DEVICE_CONTROL` | Host playback assertion and ownership claims (`owns=1`) | Host -> Accessory |
| `0x0C` | `DEVICE_STATE` | Status flags and connection state updates for individual peers | Accessory -> Host |
| `0x0E` | `AUDIO_SOURCE` | Active streaming source address | Accessory -> Host |
| `0x11` | `SMART_ROUTING` | Active streaming app bundle identifier and playback priority | Accessory -> Host |
| `0x15` | `TRIANGLE_PREVIOUS` | Address of the previous ecosystem device holding the audio link | Accessory -> Host |
| `0x17` | `RTBUDDY_SENSOR` | RTBuddy XML plists and fused sensor packets (`SensorWX`) | Bidirectional |
| `0x25` | `GET_CERTIFICATES` | Retrieval of hardware device certificates | Host -> Accessory |
| `0x26` | `GYRO_INFO` | Hardware gyro bias calibration metrics | Accessory -> Host |
| `0x2A` | `GAPA_AUTH` | Genuine Apple Peripheral Authentication challenge and signature | Bidirectional |
| `0x2B` | `EVENT_HISTORY` | Circular log of the last N Bluetooth connection/disconnection events | Accessory -> Host |
| `0x2E` | `TIPI_TABLE` | TiPi table listing all recognized ecosystem devices and states | Accessory -> Host |
| `0x30` | `DELETE_KEYS` (**disputed**) | Original label: purge cached pairing credentials. The public reference instead lists `0x30` as a BLE keys *request* (response on `0x31`). Do not send this opcode expecting a delete. | Host -> Accessory |
| `0x4D` | `FEATURE_FLAGS` | Host feature advertisement bitmask (Spatial, TiPi, Find My) | Host -> Accessory |
| `0x4E` | `PROX_CARD_STATUS` | Proximity pairing card interface state | Host -> Accessory |
| `0x56` | `WIRED_SENSOR_REQ` | USB / companion wired spatial sensor activation request | Host -> Accessory |

---

## 3. Selected Payload Definitions

### 3.1 Opcode 0x2B: Bluetooth Event History

Reports the last N connection/disconnection transitions recorded in accessory NVRAM:
```
[6]      u8      Version (0 or 1)
[7..8]   u16 LE  Length of entry block (e.g. 170 bytes = 10 entries)
[9..16]  u64 LE  Accessory uptime clock in microseconds
[17..]   Array of 17-byte entries:
           u64 LE  Timestamp (microseconds on accessory clock)
           6 bytes Bluetooth Address (LSB-first)
           u8      Event Type (1=Connect, 2=Disconnect, 9=Connect newer, 11=Disconnect req)
           u16 LE  Event detail / Disconnect reason code
```

### 3.2 Opcode 0x2E: TiPi Multi-Device Table

Communicates the current state of paired devices across the user's mesh:
```
[6]      u8      Version
[7]      u8      Audio state (0=No audio, 1=Call/SCO, 2=Media/A2DP)
[8]      u8      Device count
[9..]    Count × 8 bytes:
           6 bytes Bluetooth Address (MSB-first)
           u8      Connection status
           u8      State flags
```

---

## 4. Verification Status

Cross-checked against publicly available community documentation and open-source implementations of AACP.

| Opcode | Status | Notes |
|---|---|---|
| `0x04` battery, `0x06` ear detection, `0x09` control command, `0x0E` audio source, `0x17` head tracking, `0x2E` connected devices (TiPi), `0x4D` feature flags | Corroborated | Same opcode and rough purpose in the public reference. |
| `0x11` smart routing | Corroborated, direction clarified | Public reference: `0x10` = host -> accessory relay, `0x11` = accessory -> host response. |
| `0x2B` event history | **Conflicts** | Public reference lists `0x2B` only as "paired devices (?)". The event-history layout here is unconfirmed. |
| `0x30` | **Conflicts** | See table note. Public reference: BLE keys request. |
| `0x02`, `0x08`, `0x0C`, `0x15`, `0x25`, `0x26`, `0x2A`, `0x4E`, `0x56` | Unverified | No public corroboration found. In the public reference `0x0C` is only noted as an unknown TiPi-related opcode. |
