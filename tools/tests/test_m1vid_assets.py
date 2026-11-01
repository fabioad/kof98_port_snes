"""Validate the M1VID1 ending-format opening video container."""
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIDEO = ROOT / "assets/video/Wmva3m93t34/snes_video/Wmva3m93t34.m1vid"


class M1VidAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not VIDEO.exists():
            raise unittest.SkipTest("run tools/build_intro_m1vid.py first")
        cls.data = VIDEO.read_bytes()

    def test_header(self):
        self.assertEqual(self.data[:8], b"M1VID1\0\0")
        width, height, fps, flags = struct.unpack_from("<HHHH", self.data, 8)
        count, duration = struct.unpack_from("<II", self.data, 16)
        self.assertEqual((width, height, fps, flags), (256, 224, 15, 0))
        self.assertEqual(count, 665)
        self.assertEqual(duration, 44300)

    def test_frame_table_and_ticks(self):
        count = struct.unpack_from("<I", self.data, 16)[0]
        table = [struct.unpack_from("<IHH", self.data, 24 + i * 8)
                 for i in range(count)]
        offsets = [entry[0] for entry in table]
        self.assertEqual(offsets, sorted(offsets))
        self.assertEqual(offsets[0], 0)
        self.assertEqual(sum(entry[2] for entry in table), 2658)
        self.assertTrue(all(entry[1] and entry[1] % 32 == 0
                            for entry in table))

    def test_frame_payload_layout(self):
        count = struct.unpack_from("<I", self.data, 16)[0]
        data_start = 24 + count * 8
        for index in (0, 60, count - 1):
            off, chr_len, ticks = struct.unpack_from(
                "<IHH", self.data, 24 + index * 8)
            end = off + chr_len + 2048 + 128
            if index + 1 < count:
                next_off = struct.unpack_from(
                    "<I", self.data, 24 + (index + 1) * 8)[0]
                self.assertEqual(end, next_off)
            self.assertLessEqual(data_start + end, len(self.data))


if __name__ == "__main__":
    unittest.main()
