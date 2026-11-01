"""Verify the opening FMV is embedded in the game's kof98-snes.msu."""
import hashlib
import json
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MSU = ROOT / "kof98-snes.msu"
MSU_BUILD = ROOT / "build/gen_fight/kof98-snes.msu"
VIDEO = ROOT / "assets/video/Wmva3m93t34/snes_video/Wmva3m93t34.m1vid"
BASES = ROOT / "build/gen_fight/msu1_bases.inc"
MANIFEST = ROOT / "assets/video/Wmva3m93t34/manifest.json"
ALIGN = 32768
MAGIC = b"M1VID1\0\0"


class MsuVideoEmbedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not MSU.exists() or not VIDEO.exists():
            raise unittest.SkipTest("build the ROM/MSU first")
        cls.msu = MSU.read_bytes()
        cls.video = VIDEO.read_bytes()

    def test_header_keeps_the_rom_layout_crc(self):
        self.assertEqual(self.msu[:8], b"KOF98MSU")
        crc = self.msu[8] | self.msu[9] << 8
        text = BASES.read_text()
        match = re.search(r"MSU_LAYOUT\s*=\s*\$([0-9A-Fa-f]+)", text)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1), 16), crc)

    def test_video_payload_is_the_same_msu_file(self):
        off = int.from_bytes(self.msu[10:14], "little")
        length = int.from_bytes(self.msu[14:18], "little")
        self.assertEqual(off % ALIGN, 0)
        self.assertGreater(off, 0)
        self.assertEqual(self.msu[off:off + 8], MAGIC)
        self.assertEqual(length, len(self.video))
        self.assertEqual(hashlib.sha256(self.msu[off:off + length]).hexdigest(),
                         hashlib.sha256(self.video).hexdigest())
        self.assertEqual(off + length, len(self.msu))

    def test_engine_constants(self):
        off = int.from_bytes(self.msu[10:14], "little")
        length = int.from_bytes(self.msu[14:18], "little")
        count = struct.unpack_from("<I", self.msu, off + 16)[0]
        text = BASES.read_text()
        values = dict(re.findall(r"^MSU_VIDEO_(\w+)\s*=\s*(.+)$", text,
                                 re.MULTILINE))
        self.assertEqual(int(values["OFFSET"].replace("$", ""), 16), off)
        self.assertEqual(int(values["SIZE"]), length)
        self.assertEqual(int(values["FRAMES"]), count)
        self.assertEqual(int(values["DATA"]), 24 + count * 8)
        self.assertEqual(int(values["SLICE"]), off // ALIGN)
        seek = [int(values[f"OFF{i}"].replace("$", ""), 16) for i in range(4)]
        self.assertEqual(seek[0] | seek[1] << 8 | seek[2] << 16 | seek[3] << 24,
                         off)
        vtable = off + 24
        vbase = off + 24 + count * 8
        self.assertEqual(int(values["TABLE_LO"].replace("$", ""), 16),
                         vtable & 0xFFFF)
        self.assertEqual(int(values["TABLE_HI"].replace("$", ""), 16),
                         (vtable >> 16) & 0xFFFF)
        self.assertEqual(int(values["BASE_LO"].replace("$", ""), 16),
                         vbase & 0xFFFF)
        self.assertEqual(int(values["BASE_HI"].replace("$", ""), 16),
                         (vbase >> 16) & 0xFFFF)

    def test_manifest_points_at_the_same_file(self):
        manifest = json.loads(MANIFEST.read_text())
        msu = manifest["msu"]
        self.assertEqual(msu["file"], "kof98-snes.msu")
        self.assertTrue(msu["embedded"])
        self.assertEqual(msu["offset"], int.from_bytes(self.msu[10:14], "little"))
        self.assertEqual(msu["sha256"],
                         hashlib.sha256(self.video).hexdigest())

    def test_build_copy_matches_the_runtime_copy(self):
        if not MSU_BUILD.exists():
            self.skipTest("no build/gen_fight copy")
        self.assertEqual(MSU_BUILD.read_bytes(), self.msu)


if __name__ == "__main__":
    unittest.main()
