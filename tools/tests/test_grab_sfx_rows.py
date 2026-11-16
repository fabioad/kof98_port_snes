"""Static regressions for the grab SFX on special/super holds.

Normal throws get SFX_HIT_MED on the first bind element.  Every special or
super that owns a TargetBind chain must play the same capture cue on its
first bind state, and a hold that closes on a strike (Clark's Ultra
Argentine elbow, Iori's 3021 explosion) must play SFX_HIT_HEAVY on the last
TargetLifeAdd element.  Run after a fight build:

    python3 -m unittest tools.tests.test_grab_sfx_rows
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
GEN = os.path.join(ROOT, "build", "gen_fight")

SFX_HIT_MED = 5
SFX_HIT_HEAVY = 18


def act_rows(text, label):
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines)
                     if line.startswith(label + ":"))
    except StopIteration:
        return None
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


class GrabSfxRowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = {}
        for name in ("kyo", "ralf", "clark", "iori", "daimon", "mary",
                     "duckking"):
            path = os.path.join(GEN, f"{name}_spr.inc")
            if not os.path.exists(path):
                raise unittest.SkipTest("run build_fight.py first")
            with open(path) as source:
                cls.texts[name] = source.read()

    def rows(self, name, sid):
        rows = act_rows(self.texts[name], f"{name}Act{sid}")
        self.assertIsNotNone(rows, f"{name}Act{sid} missing")
        return rows

    def test_normal_throw_cue_is_preserved(self):
        for name in ("kyo", "ralf"):
            rows = self.rows(name, 75)
            self.assertTrue(
                any(r[0] == 0 and r[1] == 7 and r[2] == SFX_HIT_MED
                    for r in rows),
                f"{name}Act75 lost the frame-0 grab cue")

    def test_special_grab_cue_on_capture(self):
        # Clark 3010 (Ultra Argentine grab), Iori 3020 (Ya Otome rush),
        # Daimon 3010 (command grab) and Mary 3810 (Typhoon) all open their
        # TargetBind chain here.
        for name, sid in (("clark", 109), ("iori", 87),
                          ("daimon", 86), ("mary", 106)):
            rows = self.rows(name, sid)
            self.assertTrue(
                any(r[0] == 0 and r[1] == 7 and r[2] == SFX_HIT_MED
                    for r in rows),
                f"{name}Act{sid} has no grab-connect cue")

    def test_cue_survives_a_frame0_voice(self):
        # Duck King's 2300 root plays a voice at element 0; the cue must be
        # appended after it instead of being dropped.
        rows = self.rows("duckking", 108)
        self.assertTrue(any(r[2] >= 40 for r in rows if r[1] == 7))
        self.assertTrue(
            any(r[0] == 0 and r[1] == 7 and r[2] == SFX_HIT_MED
                for r in rows),
            "duckkingAct108 lost the cue to its frame-0 voice")

    def test_slam_strike_plays_the_hit_sfx(self):
        # Clark's elbow lands with the life-add at element 7 of 3016.
        rows = self.rows("clark", 106)
        self.assertTrue(any(r[0] == 7 and r[1] == 3 and r[2] >= 128
                            for r in rows), "clarkAct106 lost the slam damage")
        self.assertTrue(
            any(r[0] == 7 and r[1] == 7 and r[2] == SFX_HIT_HEAVY
                for r in rows),
            "clarkAct106 has no hit SFX on the elbow")

    def test_finisher_strike_plays_the_hit_sfx(self):
        # Iori 3021 and Daimon 3010 close their holds with a damaging element.
        for name, sid, frame in (("iori", 115, 6), ("daimon", 86, 36)):
            rows = self.rows(name, sid)
            self.assertTrue(
                any(r[0] == frame and r[1] == 3 and r[2] >= 128
                    for r in rows),
                f"{name}Act{sid} lost its finisher damage")
            self.assertTrue(
                any(r[0] == frame and r[1] == 7 and r[2] == SFX_HIT_HEAVY
                    for r in rows),
                f"{name}Act{sid} has no hit SFX on the finisher")
        # Iori's source also plays a swish on that element; the hit cue must
        # not disappear behind it.
        rows = self.rows("iori", 115)
        self.assertTrue(any(r[0] == 6 and r[1] == 7 and r[2] == 0
                            for r in rows))


if __name__ == "__main__":
    unittest.main()
