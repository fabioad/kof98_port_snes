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
        # Voice ids are per-character (arg - VOICE_BASE); the local index can
        # shift when the parser discovers another sample, so only require the
        # op7 trigger at the original tick and a streamed-voice argument.
        expected = {
            "ralfAct54": 0x80 | 7,    # Air Blitz
            "ralfAct75": 0x80 | 29,   # basic throw
            "ralfAct85": 51,          # Galactica Phantom weak
            "ralfAct86": 0x80 | 123,  # Galactica Phantom strong
            "ralfAct90": 0x80 | 100,  # win pose
        }
        for label, frame in expected.items():
            rows = [r for r in act_rows(self.text, label)
                    if r[0] == frame and r[1] == 7]
            self.assertTrue(rows, f"{label} lost its voice row")
            self.assertTrue(all(r[2] >= 40 for r in rows),
                            f"{label}: {rows}")


if __name__ == "__main__":
    unittest.main()
