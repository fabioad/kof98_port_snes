import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "build", "gen_fight", "ralf_spr.inc")


def act_rows(text, label):
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines)
                 if line.startswith(label + ":"))
    rows = []
    for line in lines[start + 1:]:
        if not line.startswith("    .db"):
            break
        body = line.split(".db", 1)[1].strip()
        if body.startswith("$FF"):
            break
        rows.append(tuple(int(x.strip().replace("$", "0x"), 0)
                          for x in body.split(",")))
    return rows


class RalfVoiceRowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(PATH):
            raise unittest.SkipTest("run build_fight.py first")
        with open(PATH) as source:
            cls.text = source.read()

    def test_voice_table_is_not_empty(self):
        # The seven source samples must stay addressable by ActTab op7.
        with open(os.path.join(ROOT, "build", "gen_fight",
                               "voices.inc")) as source:
            self.assertIn("VoiceTab_ralf", source.read())

    def test_move_voices_are_wired(self):
        # voice index = arg - VOICE_BASE (40)
        expected = {
            "ralfAct54": (0x80 | 7, 7, 44),   # Air Blitz
            "ralfAct75": (0x80 | 29, 7, 40),  # basic throw
            "ralfAct85": (51, 7, 45),         # Galactica Phantom weak
            "ralfAct86": (0x80 | 123, 7, 46), # Galactica Phantom strong
            "ralfAct90": (0x80 | 100, 7, 41), # win pose
        }
        for label, row in expected.items():
            rows = [r[:3] for r in act_rows(self.text, label)]
            self.assertIn(row, rows, f"{label} lost its voice row")


if __name__ == "__main__":
    unittest.main()
