# Apple MagicPairing & CloudKit Key Architecture

> **Status: unverified research notes.** The key-derivation formula, the CloudKit record layout and the
> extraction paths below could not be corroborated against public sources, and the
> feasibility ratings are the author's judgment. Do not rely on them without independent confirmation.
> Intended only for accessories and accounts you own.

## 1. Overview

Apple MagicPairing replaces static Bluetooth Long-Term Keys (LTKs) with an account-synchronized dynamic trust model. When an accessory is paired with an Apple ID, cryptographic material is synchronized across all trusted devices in the user's iCloud Keychain circle via CloudKit.

---

## 2. Cryptographic Key Derivation

```
                +-------------------------+
                |  iCloud Account Secrets |
                |  masterKey (16 bytes)   |
                |  masterHint (16 bytes)  |
                +------------+------------+
                             |
             +---------------+---------------+
             |                               |
   AES-128-ECB(masterKey,          AES-128-ECB(masterHint,
        BluetoothAddressBlob)           BluetoothAddressBlob)
             |                               |
             v                               v
   +--------------------+          +--------------------+
   |  accKey (16 bytes) |          | accHint (16 bytes) |
   |   (Accessory Key)  |          |   (Accessory Hint) |
   +---------+----------+          +--------------------+
             |
             +-----------------------+
             |                       |
             v                       v
     [Accessory NVRAM]      [CloudKit Manatee Zone]
    Transmitted during      MagicCloudPairingProtectedAccessoryBlob
    initial pairing         (Encrypted with Keychain circle keys)
```

1. **`masterKey` & `masterHint`**: 16-byte random values generated once per Apple ID account.
2. **`BluetoothAddressBlob`**: Formatted 16-byte structure containing the accessory's 6-byte MAC address.
3. **`accKey` (Accessory Key)**: The shared symmetric key derived as:
   $$\text{accKey} = \text{AES-128-ECB}(\text{masterKey}, \text{BluetoothAddressBlob})$$
4. **`MagicCloudPairingProtectedAccessoryBlob`**: The record stored in the end-to-end encrypted **Manatee** CloudKit zone (`MPCloudKit_Manatee`). Contains:
   - `accKey` and `accHint`
   - Classic Bluetooth Link Key (`LK`) and BLE `LTK`, `EDIV`, `RAND`, `IRK`
   - Device metadata and capabilities

---

## 3. Trust Enforcement & ProtectedAccess

1. **Initial Provisioning**:
   - During proximity pairing on an Apple device, the host transmits `accKey` to the accessory over an encrypted Bluetooth link.
   - The accessory writes `accKey` to its internal NVRAM.

2. **Connection Authentication**:
   - When any device connects, the accessory issues a challenge.
   - Devices possessing `accKey` complete the MagicPairing handshake and are elevated to **Authenticated Apple Ecosystem Peer**.
   - Peripherals requiring `<key>ProtectedAccess</key><true/>` (such as AirPods Max 1st gen motion streams) only permit data transmission once this state is confirmed.

---

## 4. Key Recovery & Interoperability Avenues

| Platform | Extraction Path | Mechanism | Feasibility |
|---|---|---|---|
| **macOS** | Local Plist / Keychain | `sudo` read of `/Library/Preferences/com.apple.Bluetooth.plist` or `bluetoothd` memory | **High** (Immediate, plaintext) |
| **iOS** | MobileBackup2 | Encrypted local backup of `keychain-backup.plist` | **Low** (Hardware-bound to Secure Enclave) |
| **Non-Apple Host** | Direct Emulation | Factory reset accessory and emulate initial proximity pairing | **Experimental** (Breaks iCloud multi-device sync) |
