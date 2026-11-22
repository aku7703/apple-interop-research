# AACP Reference Decoders

Standalone Python decoders for Apple Accessory Protocol (AACP) frames.

- **`decode_2b_history.py`**: Parses Opcode `0x2B` (Bluetooth Event History), converting accessory microsecond hardware timestamps into delta-seconds and decoding proprietary disconnect reason codes (e.g. Smart Case insertion, Link Loss, User Disconnect).

### Usage:
```bash
# Run with a hex-encoded packet string:
python decode_2b_history.py "040004002b00012200..."
```

Runs with no arguments on a built-in synthetic packet. Exits non-zero on malformed input.

> The `0x2B` layout and event/reason names are the author's own observations and are not corroborated by public sources (see `protocols/aacp-specification.md`).

Tests: `python -m unittest discover -s tests -v` from the repository root.
