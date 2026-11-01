"""Validate the SNES Mode-7 video pack and its PNG frame directory."""
import json
import struct
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets/video/Wmva3m93t34"
FRAMES = ASSETS / "frames"
VIDEO = ASSETS / "snes_video/Wmva3m93t34.m7vid"


class SnesVideoAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not VIDEO.exists():
            raise unittest.SkipTest("run tools/build_snes_video.py first")
        cls.data = VIDEO.read_bytes()
        cls.frames = sorted(FRAMES.glob("frame_*.png"))

    def test_manifest_and_frame_directory(self):
        manifest = json.loads((ASSETS / "manifest.json").read_text())
        self.assertEqual(manifest["duration_seconds"], 54.0)
        self.assertEqual(manifest["fps"], 8)
        self.assertEqual(manifest["resolution"], [128, 112])
        self.assertEqual(manifest["colors"], 256)
        self.assertFalse(manifest["audio"])
        self.assertEqual(manifest["frame_count"], 432)
        self.assertEqual(len(self.frames), 432)
        for i in (0, 150, 431):
            im = Image.open(self.frames[i])
            self.assertEqual(im.mode, "P")
            self.assertEqual(im.size, (128, 112))
            self.assertEqual(len(im.getpalette() or []) // 3, 256)

    def test_m7vid_header_and_frame_table(self):
        self.assertEqual(self.data[:8], b"M7VID1\0\0")
        width, height, fps, flags = struct.unpack_from("<HHHH", self.data, 8)
        count, duration = struct.unpack_from("<II", self.data, 16)
        self.assertEqual((width, height, fps, flags), (128, 112, 8, 1))
        self.assertEqual(count, 432)
        self.assertEqual(duration, 54000)
        ticks = [struct.unpack_from("<H", self.data, 24 + i * 6 + 4)[0]
                 for i in range(count)]
        self.assertEqual(ticks, [7 if i % 2 == 0 else 8 for i in range(count)])
        self.assertEqual(sum(ticks), 54 * 60)
        offsets = [struct.unpack_from("<I", self.data, 24 + i * 6)[0]
                   for i in range(count)]
        self.assertEqual(offsets, sorted(offsets))

    def test_one_pak_decodes_to_the_png_frame(self):
        index = 150
        table = 24
        off = struct.unpack_from("<I", self.data, table + index * 6)[0]
        data_start = table + 432 * 6
        pak = self.data[data_start + off + 512:]
        ntiles, cr, map0 = struct.unpack_from("<HHH", pak, 0)
        cols, rows = cr & 0xFF, cr >> 8
        self.assertEqual((cols, rows, map0), (16, 14, 0x1A38))
        self.assertLessEqual(ntiles, 256)
        cells = pak[6 + ntiles * 64:6 + ntiles * 64 + cols * rows]
        self.assertEqual(len(cells), cols * rows)
        out = bytearray(128 * 112)
        for cy in range(rows):
            for cx in range(cols):
                tile = pak[6 + cells[cy * cols + cx] * 64:
                           6 + (cells[cy * cols + cx] + 1) * 64]
                for y in range(8):
                    out[(cy * 8 + y) * 128 + cx * 8:
                        (cy * 8 + y) * 128 + cx * 8 + 8] = tile[y * 8:y * 8 + 8]
        png = bytes(Image.open(self.frames[index]).getdata())
        self.assertEqual(bytes(out), png)


if __name__ == "__main__":
    unittest.main()
