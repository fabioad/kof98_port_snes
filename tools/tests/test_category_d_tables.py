"""Static checks for Category D rows that cannot be exercised by the
headless selector (Omega Rugal shares Rugal's select cell)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "build" / "gen_fight"


def body(text, label):
    m = re.search(rf"{label}:\n(.*?)(?=\n\w+:|\Z)", text, re.S)
    return m.group(1) if m else ""


class CategoryDTablesTests(unittest.TestCase):
    def test_omega_gravity_and_re_rows(self):
        text = (GEN / "omegarugal_spr.inc").read_text()
        cmd = body(text, "omegarugalCmdTab")
        self.assertRegex(cmd, r"\.db \d+,0,0,3,0,0,82")
        self.assertRegex(cmd, r"\.db \d+,0,0,3,0,0,107")
        self.assertRegex(cmd, r"\.db \d+,0,0,3,0,0,109")
        rows = re.findall(r"\.db \$([0-9A-F]{2}),\$([0-9A-F]{2}),(\d+),",
                          body(text, "omegarugalProjTab"))
        self.assertGreater(len(rows), 82)
        self.assertEqual(rows[82], ("00", "01", "14"))

    def test_rugal_eye_beam_uses_alternate_clip(self):
        text = (GEN / "rugal_spr.inc").read_text()
        cmd = body(text, "rugalCmdTab")
        self.assertRegex(cmd, r"\.db \d+,0,0,3,0,0,82")
        rows = re.findall(r"\.db \$([0-9A-F]{2}),\$([0-9A-F]{2}),(\d+),",
                          body(text, "rugalProjTab"))
        self.assertGreater(len(rows), 82)
        self.assertEqual(rows[82], ("00", "05", "14"))
        meta = (GEN / "projectiles_meta.inc").read_text()
        self.assertIn("rugalProjFx2Anim", meta)


if __name__ == "__main__":
    unittest.main()
