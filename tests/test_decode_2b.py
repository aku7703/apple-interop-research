import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "aacp-decoders"))
import decode_2b_history as d  # noqa: E402


class Decode2B(unittest.TestCase):
    def test_sample_packet(self):
        r = d.parse_packet_hex(d.SAMPLE_PACKET)
        self.assertEqual(r["version"], 1)
        self.assertEqual(r["uptime_us"], 19_719_815_168)
        self.assertEqual(len(r["entries"]), 2)
        e0, e1 = r["entries"]
        self.assertEqual(e0["address"], "AA:BB:CC:DD:EE:01")
        self.assertEqual((e0["event_type"], e0["detail"]), (1, 0x0002))
        self.assertEqual((e1["event_type"], e1["detail"]), (2, 0x02DE))
        self.assertAlmostEqual(e0["age_s"], 4.571136, places=3)
        self.assertIn("Power Off / Smart Case Inserted", d.format_packet(r))

    def test_rejects_wrong_header(self):
        with self.assertRaises(ValueError):
            d.parse_packet_hex("0400040004000000000000000000000000")

    def test_rejects_bad_hex(self):
        with self.assertRaises(ValueError):
            d.parse_packet_hex("zz")

    def test_truncated_packet_returns_partial(self):
        r = d.parse_packet_hex(d.SAMPLE_PACKET[:-10])
        self.assertEqual(len(r["entries"]), 1)


if __name__ == "__main__":
    unittest.main()
