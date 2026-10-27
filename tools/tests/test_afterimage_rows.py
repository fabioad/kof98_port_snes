import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "build" / "gen_fight"


class AfterImageRowsTests(unittest.TestCase):
    def test_no_afterimage_rows_in_playable_character_tables(self):
        """The SNES port must not emit AfterImage op9 rows.

        Ghost snapshots reuse the ping-pong tile pages (which can point at
        retired graphics) and add OAM pressure.  The generator drops every
        AfterImage controller for every character/move, so no playable
        character table may carry the op9 action row.
        """
        tables = sorted(GEN.glob("*_spr.inc"))
        self.assertTrue(tables, "run the fight build before this test")
        bad = []
        for path in tables:
            # kfm_spr.inc is the base template, not a roster fighter.
            if path.name == "kfm_spr.inc":
                continue
            for lineno, line in enumerate(
                    path.read_text(errors="ignore").splitlines(), 1):
                if re.search(r"\.db\s+[^,]+,\s*9,\s*1,\s*0", line):
                    bad.append(f"{path.name}:{lineno}: {line.strip()}")
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
