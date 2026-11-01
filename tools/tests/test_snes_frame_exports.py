"""Validate the per-frame SNES Mode-7 export under frames_snes."""
import json
import struct
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets/video/Wmva3m93t34"
SRC = ASSETS / "frames"
OUT = ASSETS / "frames_snes"


class SnesFrameExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (OUT / "frame_00000.m7pak").exists():
            raise unittest.SkipTest("run tools/export_snes_frames.py first")
        cls.paks = sorted(OUT.glob("frame_*.m7pak"))
        cls.pals = sorted(OUT.glob("frame_*.m7pal"))

    def test_frame_pairs_and_manifest(self):
        manifest = json.loads((OUT / "manifest.json").read_text())
        self.assertEqual(manifest["frame_count"], 432)
        self.assertEqual(manifest["resolution"], [128, 112])
        self.assertEqual(manifest["colors"], 256)
        self.assertEqual(len(self.paks), 432)
        self.assertEqual(len(self.pals), 432)
        self.assertLessEqual(manifest["max_unique_tiles"], 256)

    def test_headers_and_lengths(self):
        for pak_path in (self.paks[0], self.paks[150], self.paks[-1]):
            data = pak_path.read_bytes()
            ntiles, cr, map0 = struct.unpack_from("<HHH", data, 0)
            self.assertGreaterEqual(ntiles, 1)
            self.assertLessEqual(ntiles, 256)
            self.assertEqual(cr, 16 | (14 << 8))
            self.assertEqual(map0, (52 << 7) | 56)
            self.assertEqual(len(data), 6 + ntiles * 64 + 16 * 14)
            self.assertEqual(len((OUT / (pak_path.stem + ".m7pal"))
                                 .read_bytes()), 512)

    def test_pak_decodes_to_the_source_png(self):
        index = 150
        data = (OUT / f"frame_{index:05d}.m7pak").read_bytes()
        ntiles, cr, _map0 = struct.unpack_from("<HHH", data, 0)
        cols, rows = cr & 0xFF, cr >> 8
        cells = data[6 + ntiles * 64:6 + ntiles * 64 + cols * rows]
        out = bytearray(128 * 112)
        for cy in range(rows):
            for cx in range(cols):
                base = 6 + cells[cy * cols + cx] * 64
                tile = data[base:base + 64]
                for y in range(8):
                    out[(cy * 8 + y) * 128 + cx * 8:
                        (cy * 8 + y) * 128 + cx * 8 + 8] = tile[y * 8:y * 8 + 8]
        png = bytes(Image.open(SRC / f"frame_{index:05d}.png").getdata())
        self.assertEqual(bytes(out), png)


if __name__ == "__main__":
    unittest.main()
