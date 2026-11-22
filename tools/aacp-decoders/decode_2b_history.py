#!/usr/bin/env python3
"""
AACP Opcode 0x2B Decoder: Bluetooth Event History Parser

Decodes the event history buffer sent by some Apple accessories (e.g. AirPods Max),
converting raw microsecond timestamps and event codes into human-readable logs.

NOTE: The 0x2B layout and the event/reason code names are based on the author's
own observations and are NOT corroborated by other public sources (a public
community reference lists 0x2B only as "paired devices (?)"). Treat the output
as best-effort.
"""

import struct
import sys

HEADER = b"\x04\x00\x04\x00\x2b\x00"
ENTRY_SIZE = 17
FIXED_PREFIX = 17  # header (6) + version (1) + block length (2) + clock (8)

EVENT_NAMES = {
    1: "Connect (Host-Initiated)",
    2: "Disconnect",
    3: "Pairing",
    4: "Unpairing",
    5: "UTP Connect",
    6: "UTP Disconnect",
    7: "LE Connect",
    8: "LE Disconnect",
    9: "Connect (Accessory-Initiated)",
    10: "Connect (Source-Initiated)",
    11: "Disconnect Request",
}

DISCONNECT_REASONS = {
    0x2BE: "Case Closed / Off-Head Sleep",
    0x2CF: "User Selected Disconnect",
    0x2D1: "Link Loss / Out of Range",
    0x2D2: "Host Initiated Disconnect",
    0x2DE: "Power Off / Smart Case Inserted",
}


def parse_packet_hex(hex_str: str) -> dict:
    clean = "".join(hex_str.split()).replace(":", "")
    try:
        data = bytes.fromhex(clean)
    except ValueError as exc:
        raise ValueError(f"Invalid hex input: {exc}") from exc
    return parse_packet_bytes(data)


def parse_packet_bytes(p: bytes) -> dict:
    """Parse a 0x2B packet into a dict with 'version', 'uptime_us' and 'entries'."""
    if len(p) < FIXED_PREFIX or p[:6] != HEADER:
        raise ValueError("Not an AACP 0x2B packet (expected header 04 00 04 00 2b 00)")

    version = p[6]
    block_len = struct.unpack_from("<H", p, 7)[0]
    now_us = struct.unpack_from("<Q", p, 9)[0]

    entries = []
    offset = FIXED_PREFIX
    for _ in range(block_len // ENTRY_SIZE):
        if offset + ENTRY_SIZE > len(p):
            break  # truncated packet: return what we have

        event_time_us = struct.unpack_from("<Q", p, offset)[0]
        addr = ":".join(f"{b:02X}" for b in reversed(p[offset + 8 : offset + 14]))
        event_type = p[offset + 14]
        detail = struct.unpack_from("<H", p, offset + 15)[0]
        entries.append(
            {
                "age_s": (now_us - event_time_us) / 1_000_000,
                "address": addr,
                "event_type": event_type,
                "detail": detail,
            }
        )
        offset += ENTRY_SIZE

    return {"version": version, "uptime_us": now_us, "entries": entries}


def format_packet(result: dict) -> str:
    now_us = result["uptime_us"]
    lines = [
        f"=== AACP 0x2B Event History (Version {result['version']}) ===",
        f"Accessory Uptime: {now_us / (1_000_000 * 3600):.2f} hours ({now_us:,} microseconds)",
        "",
        f"{'Age':<12} | {'Address':<17} | {'Event':<29} | Detail / Reason",
        "-" * 78,
    ]
    for e in result["entries"]:
        et, detail = e["event_type"], e["detail"]
        event_str = EVENT_NAMES.get(et, f"Event {et}")
        if et in (2, 6, 8, 11):
            detail_str = DISCONNECT_REASONS.get(detail, f"Reason 0x{detail:03X}")
        elif et in (1, 9, 10):
            detail_str = f"Status 0x{detail:04X}"
        else:
            detail_str = f"0x{detail:04X}"
        lines.append(f"{'-%.1fs' % e['age_s']:<12} | {e['address']:<17} | {event_str:<29} | {detail_str}")
    return "\n".join(lines)


# Synthetic packet (placeholder address AA:BB:CC:DD:EE:01), 2 entries.
SAMPLE_PACKET = (
    "040004002b00012200"
    "0080649704000000"  # uptime clock = 19,719,815,168 us (~5.48 h)
    "00c01e970400000001eeddccbbaa010200"  # Connect (type 1), status 0x0002
    "004044970400000001eeddccbbaa02de02"  # Disconnect (type 2), reason 0x02DE
)


def main(argv):
    if len(argv) > 1:
        hex_input = argv[1]
    else:
        print("Running with sample synthetic packet:")
        hex_input = SAMPLE_PACKET
    try:
        print(format_packet(parse_packet_hex(hex_input)))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
