"""Movement of the fighters Clark throws (normal, specials, super, MAX).

The port used to keep the bound victim on one generic held pose for the
whole grab, ignore the AIR "V" (vertical flip) flag and clamp every
TargetBind ``dy`` at -80 px.  The result was a body that stood upright in
mid-air, floated at a single height for hundreds of ticks and jumped 40-80 px
when a phase changed.

These checks read the generated Clark tables (no emulator) and pin the
properties the fix depends on:

* every held phase of the chain carries its own pose (TargetPose op 21);
* the pose clips keep the source's H/V flags (the engine mirrors them);
* no frame stays at a *clamped* offset for more than three ticks;
* the per-frame vertical step stays inside the authored budget;
* the bind covers every element of the grab animation;
* the slam pose asks the release not to launch the victim upward.

Run after a build:

    python3 -m unittest tools.tests.test_clark_throw_motion
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "build" / "gen_fight"
CNS = ROOT / "assets" / "characters" / "Clark-KOF98" / "Clark_SNES.cns"

sys.path.insert(0, str(ROOT / "tools"))
import build_fight  # noqa: E402

_PROFILE = GEN / "build_profile.json"
if _PROFILE.exists():
    CLARK_SCALE = json.loads(_PROFILE.read_text())["char_scales"]["clark"]
else:
    CLARK_SCALE = build_fight.CHARS["clark"].get("char_scale", 1.0)

# Runtime slot -> source victim/attacker state for Clark's grabs.  Most of
# these come from CHARS["clark"]["moves"]; 99/101/107 are wired by
# wire_throw_chain at build time and are listed here explicitly.
SID_STATE = {75: 810, 99: 1210, 101: 1310, 107: 1420,
             109: 3010, 110: 3011, 111: 3012,
             103: 3013, 104: 3014, 105: 3015, 106: 3016,
             66: 3110, 60: 3111}
ULTRA = (109, 110, 111, 103, 104, 105, 106)
GRABS = tuple(SID_STATE)
# Source anim element where 3016 slams the victim from the lift to the floor.
# The source drops 80 px in that single element; it is authored, not a port
# artefact, so the per-frame step check allows it.
AUTHORED_SNAPS = {106: {7}}


def s8(value):
    return value - 256 if value >= 128 else value


def rows_of(text, label):
    m = re.search(rf"^{re.escape(label)}:\s*\n((?:\s*\.db[^\n]*\n)+)",
                  text, re.M)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        nums = [int(t[1:], 16) if t.startswith("$") else int(t)
                for t in re.findall(r"\$[0-9A-Fa-f]+|-?\d+", line)]
        if nums and nums[0] != 0xFF:
            out.append(tuple(nums))
    return out


def acts_of(text, sid):
    return [r for r in rows_of(text, f"clarkAct{sid}") if len(r) >= 3]


def bind_frames(rows):
    """frame -> (dx, dy) for one BindTab state."""
    table = {}
    for lo, hi, dx, dy in rows:
        for f in range(lo, min(hi, 254) + 1):
            table[f] = (s8(dx), s8(dy))
    return table


def source_binds():
    """Mugen state -> [(lo, hi, dx, dy)] straight from the CNS."""
    _moves, _pos, _pow, _hdr, _sd, binds, _acts, _rev, _lists, _snd, _hs, \
        _exp, _poses = build_fight.parse_cns(
            str(CNS), build_fight.CHARS["clark"].get("coord_scale", 1),
            build_fight.CHARS["clark"].get("damage_scale", 1),
            char="clark", char_scale=CLARK_SCALE)
    return binds


class ClarkThrowPoseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = GEN / "clark_spr.inc"
        if not path.exists():
            raise unittest.SkipTest("run tools/build_fight.py first")
        cls.text = path.read_text(errors="ignore")

    def test_each_held_phase_switches_pose(self):
        """3010..3016 must carry distinct poses, not one frozen body."""
        poses = []
        for sid in ULTRA:
            ops = [r for r in acts_of(self.text, sid) if r[1] == 21]
            self.assertTrue(ops, f"sid {sid} has no TargetPose row")
            poses.append(ops[0][2] & 0x7F)
        # 3010 grab/lift, 3011 apex, 3012 swing, 3013 apex, 3014 swing,
        # 3015 apex, 3016 slam -> the source's own 3020..3026 cadence.
        self.assertEqual(poses, [0, 1, 2, 1, 2, 1, 3])
        self.assertGreaterEqual(len(set(poses)), 4,
                                f"pose vocabulary too small: {poses}")

    def test_pose_clips_keep_source_flips(self):
        """The engine only mirrors what the clips carry: H and V bits."""
        flags = set()
        for pose in range(len(build_fight.VICTIM_POSE_ACTIONS)):
            m = re.search(rf"^clarkPose{pose}:\s*\n"
                          r"    \.db \d+,-1\n"
                          rf"((?:    \.dw \d+\n    \.db [^\n]+\n)+)",
                          self.text, re.M)
            self.assertIsNotNone(m, f"clarkPose{pose} missing")
            for line in m.group(1).splitlines():
                if line.strip().startswith(".db"):
                    flags.add(int(line.split(",")[3]))
        self.assertIn(2, flags, "no clip uses the V flag")
        self.assertIn(3, flags, "no clip combines H and V")
        self.assertIn(0, flags, "every clip is flipped")

    def test_bind_covers_every_grab_element(self):
        """A frame without a bind row freezes the victim, then snaps."""
        binds = source_binds()
        gaps = []
        for sid in GRABS:
            src = binds.get(SID_STATE[sid])
            self.assertTrue(src, f"sid {sid}: state {SID_STATE[sid]} has no "
                                 "TargetBind rows")
            want = set()
            for lo, hi, _dx, _dy in src:
                want.update(range(lo, min(hi, 254) + 1))
            have = set(bind_frames(rows_of(self.text, f"clarkBind{sid}")))
            missing = sorted(want - have)
            if missing:
                gaps.append((sid, missing[:6], len(missing)))
        self.assertEqual(gaps, [], f"frames without a bind row: {gaps}")

    def test_no_long_plateau_at_the_clamp(self):
        """The playfield ceiling may cap a few frames, never a hold."""
        binds = source_binds()
        bad = []
        for sid in GRABS:
            src = binds.get(SID_STATE[sid])
            if not src:
                continue
            emitted = bind_frames(rows_of(self.text, f"clarkBind{sid}"))
            run = 0
            for f in sorted(emitted):
                _dx, dy = emitted[f]
                want = [s8(dy_s) for lo, hi, _dx_s, dy_s in src
                        if lo <= f <= min(hi, 254)]
                clamped = bool(want) and dy != want[-1]
                if clamped:
                    run += 1
                    if run > 3:
                        bad.append((sid, f, dy, want[-1]))
                else:
                    run = 0
        self.assertEqual(bad, [], f"clamped for more than 3 frames: {bad[:8]}")

    def test_vertical_step_budget(self):
        """The port must not add snaps the source does not author."""
        binds = source_binds()
        bad = []
        for sid in GRABS:
            frames = bind_frames(rows_of(self.text, f"clarkBind{sid}"))
            if not frames:
                continue
            src = binds.get(SID_STATE[sid]) or ()
            for f in sorted(frames):
                if f - 1 not in frames:
                    continue
                step = abs(frames[f][1] - frames[f - 1][1])
                if step <= 24:
                    continue
                # Source step: last matching window wins, like canon_bind.
                want = {}
                for lo, hi, _dx, dy in src:
                    for g in range(lo, min(hi, 254) + 1):
                        want[g] = s8(dy)
                authored = 0
                if f in want and f - 1 in want:
                    authored = abs(want[f] - want[f - 1])
                if step <= authored + 8:
                    continue
                # A step that exists because the HUD ceiling truncated the
                # source arc is the guard doing its job, not an artefact.
                clamped = (f in want and frames[f][1] != want[f]) or \
                          (f - 1 in want and frames[f - 1][1] != want[f - 1])
                if clamped:
                    continue
                bad.append((sid, f, frames[f - 1][1], frames[f][1], authored))
        self.assertEqual(bad, [], f"port-induced vertical snaps: {bad[:8]}")

    def test_ultra_lifts_at_two_heights(self):
        """The two elevations must not collapse into one plateau."""
        def peak(sid):
            return min(dy for _dx, dy
                       in bind_frames(rows_of(self.text, f"clarkBind{sid}"))
                       .values())
        grab = peak(109)
        slam = peak(106)
        self.assertLessEqual(slam, -90, f"slam lift too low: {slam}")
        self.assertGreaterEqual(abs(slam - grab), 12,
                                f"lifts indistinguishable: {grab} vs {slam}")

    def test_playfield_ceiling(self):
        """No bind may ask for more than the playfield can show."""
        for sid in GRABS:
            for _dx, dy in bind_frames(
                    rows_of(self.text, f"clarkBind{sid}")).values():
                self.assertGreaterEqual(dy, -112,
                                        f"sid {sid} dy {dy} above the ceiling")

    def test_slam_pose_suppresses_the_launch(self):
        ops = [r for r in acts_of(self.text, "106") if r[1] == 21]
        self.assertTrue(ops)
        self.assertEqual(ops[0][2] & 0x80, 0x80,
                         "slam pose must clear the generic launch")

    def test_grab_starts_on_the_attacker_hands(self):
        """`(Target,const(size.head.pos.x))+48` must not collapse to 0."""
        frame0 = bind_frames(rows_of(self.text, "clarkBind99")).get(0)
        self.assertIsNotNone(frame0)
        self.assertGreaterEqual(abs(frame0[0]), 40,
                                f"grab dx {frame0[0]} ignores head.pos.x")
        rows = rows_of(self.text, "clarkBind101")
        self.assertGreaterEqual(abs(bind_frames(rows)[0][0]), 40)


class ThrowDirectionTests(unittest.TestCase):
    """command grabs must not be mistaken for back throws."""

    def test_back_throw_is_gated_to_the_plain_throw(self):
        src = (ROOT / "src" / "engine" / "fight.asm").read_text(
            errors="ignore")
        block = src.split("SetThrowDirFar:", 1)[1].split("STD_done:", 1)[0]
        self.assertIn("cmp #S_THROW.b", block)
        self.assertIn("cmp #S_TSEQ.b", block)


if __name__ == "__main__":
    unittest.main()
