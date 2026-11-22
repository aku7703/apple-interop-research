# Apple Ecosystem Interoperability Research

This repository provides protocol documentation, architectural analysis, and open-source tooling for interoperability between non-Apple operating systems and Apple accessory ecosystems.

---

## Repository Contents

- **`protocols/`**: Functional specifications of accessory communication protocols.
  - **`aacp-specification.md`**: Apple Accessory Protocol (AACP) framing, opcode dispatch, and message structures.
  - **`magic-pairing-architecture.md`**: Cryptographic key derivation and trust verification across ecosystem peers.
  - **`tipi-audio-switching.md`**: Multi-device audio arbitration and handoff state machine (Triangle Protocol).
  - **`spatial-telemetry.md`**: Comparative analysis of motion sensor streaming architectures (`SensorWX` vs. `cma` / `devmotion6`).
- **`tools/`**: Reference implementations and developer utilities.
  - **`ios-selective-backup/`**: Zero-storage selective backup streaming utility built on top of `pymobiledevice3`.
  - **`aacp-decoders/`**: Standalone packet parsers for diagnostic opcodes (e.g., `0x2B` event history).

---

## Accuracy & Verification Status

These are independent research notes, not authoritative specifications. The protocol documents were cross-checked against publicly available community documentation and each document opens with a status note listing what is corroborated, disputed or unverified. Notably:

- Framing, PSM `0x1001`, and opcodes `0x04`, `0x06`, `0x09`, `0x0E`, `0x11`, `0x17`, `0x2E`, `0x4D` agree with the public reference.
- Opcodes `0x2B` and `0x30` **conflict** with the public reference, and the MagicPairing and spatial-telemetry details are **unverified**.

If you find an error, please open an issue.

---

## Scope, Safety & Legal

1. **Purpose**: Documentation and tools here are intended for interoperability with Apple accessories from non-Apple platforms (such as Windows and Linux), for devices and accounts you own.
2. **No Proprietary Code**: The repository is intended to contain no Apple source code, binaries, or firmware blobs. Examples use synthetic data.
3. **No Personal Data**: Hardware identifiers, Bluetooth addresses and credentials in examples are placeholders (`AA:BB:CC:DD:EE:01`).
4. **Legal**: Reverse-engineering and interoperability rules differ by jurisdiction (for example 17 U.S.C. section 1201(f) in the US and Article 6 of Directive 2009/24/EC in the EU, each with limits). Nothing here is legal advice, and you are responsible for how you use it. Also review the terms that apply to your devices and accounts.
5. **Trademarks**: Apple, AirPods, and related names are trademarks of Apple Inc. This project is not affiliated with or endorsed by Apple.

---

## Development

```bash
python -m unittest discover -s tests -v
```

---

## License

This repository and its tools are released under the [MIT License](LICENSE).
