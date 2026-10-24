import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from build_fight import (CHARS, LAND_SID, ROOT, parse_cns,  # noqa: E402
                         trans_rules)


class LandRecoveryTests(unittest.TestCase):
    """Dive specials must land instead of freezing on a trailing hold."""

    def test_unwired_landing_recovery_maps_to_s_land(self):
        statedefs = {
            1500: [
                {"type": "ChangeState", "value": "1501",
                 "triggers": ["Vel Y > 0 && Pos Y >= 0"]},
                {"type": "ChangeState", "value": "0",
                 "triggers": ["AnimTime = 0"]},
            ],
        }
        headers = {1501: {"type": "S", "movetype": "I"}}
        rows = trans_rules(statedefs, headers, {1500: 50}, {})
        self.assertIn((50, LAND_SID, 1, 0), rows)
        self.assertIn((50, 0, 0, 0), rows)

    def test_unwired_landing_attack_is_not_rewritten(self):
        statedefs = {
            1080: [
                {"type": "ChangeState", "value": "1081",
                 "triggers": ["Vel Y > 0 && Pos Y >= 0"]},
            ],
        }
        headers = {1081: {"type": "S", "movetype": "A"}}
        self.assertEqual(trans_rules(statedefs, headers, {1080: 54}, {}), [])

    def test_wired_target_keeps_its_slot(self):
        statedefs = {
            1500: [
                {"type": "ChangeState", "value": "1501",
                 "triggers": ["Vel Y > 0 && Pos Y >= 0"]},
            ],
        }
        headers = {1501: {"type": "S", "movetype": "I"}}
        rows = trans_rules(statedefs, headers,
                           {1500: 50, 1501: 17}, {})
        self.assertIn((50, 17, 1, 0), rows)

    def test_ryo_and_robert_dive_specials_land(self):
        """Real source data: weak/strong dive kick must leave the hold frame."""
        for name, sid in (("ryo", 50), ("robert", 54)):
            cfg = CHARS.get(name)
            if not cfg or not os.path.exists(os.path.join(ROOT, cfg["cns"])):
                continue
            cns = parse_cns(os.path.join(ROOT, cfg["cns"]))
            statedefs, headers = cns[4], cns[3]
            state_to_sid = {}
            for slot, mstate in cfg["moves"].items():
                state_to_sid.setdefault(mstate, slot)
            rows = trans_rules(statedefs, headers, state_to_sid,
                               cfg["buttons"])
            self.assertIn((sid, LAND_SID, 1, 0), rows,
                          f"{name} sid {sid} does not land into S_LAND")


if __name__ == "__main__":
    unittest.main()
