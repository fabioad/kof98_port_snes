"""Regression checks for release-audit evidence, without building a ROM."""
import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audit_specials_headless as audit


class SpecialsAuditTests(unittest.TestCase):
    def result(self, **changes):
        result = dict(entered=True, clock_stall=1, last_states=[0, 0],
                      grab_flags=[0, 0], recovery=100, game_state=1,
                      healing=False, damage=0)
        result.update(changes)
        return result

    def test_idle_fighters_with_capture_flag_are_still_broken(self):
        result = self.result(damage=42, grab_flags=[0, 1], recovery=None)
        self.assertEqual(audit.classify(result, {"reversal": True}),
                         "grab_flag_leak")

    def test_zero_damage_counter_is_conditional(self):
        self.assertEqual(audit.classify(self.result(), {"reversal": True}),
                         "conditional")
        self.assertEqual(audit.classify(self.result(), {"reversal": None}),
                         "no_impact_review")

    def test_failed_retry_does_not_hide_entry_without_attack(self):
        attempts = [dict(status="no_impact_review", result=self.result()),
                    dict(status="input_missed", result=self.result(entered=False))]
        self.assertIs(audit.best_attempt(attempts), attempts[0])

    def test_successful_spacing_retry_preserves_a_state_leak(self):
        attempts = [dict(status="grab_flag_leak", result=self.result(grab_flags=[0, 1])),
                    dict(status="hit_and_recovered", result=self.result(damage=42))]
        self.assertIs(audit.best_attempt(attempts), attempts[0])

    def test_damage_and_return_to_idle_are_both_required(self):
        meta = {"reversal": None}
        self.assertEqual(audit.classify(self.result(damage=20, recovery=None), meta),
                         "recovery_timeout")
        self.assertEqual(audit.classify(self.result(damage=20, healing=True), meta),
                         "victim_healed")
        self.assertEqual(audit.classify(self.result(damage=20), meta),
                         "hit_and_recovered")

    def test_parser_keeps_native_specials_with_low_mugen_state_numbers(self):
        # Yuri's command attacks use source states below 1000. Filter by
        # native role, not by the source state's numeric range.
        rows = """yuriMot1: .db 2,21
    .db 2,0
    .db 0,1
yuriCmdTab:
    .db 1,0,0,3,0,0,48
    .db 1,0,0,3,0,0,48
    .db 1,0,0,3,0,0,74
yuriTargetTab:
""" + "    .db 255,0,255,0\n" * 120
        rows += "yuriProjTab:\n" + "    .db 0,0,0,0\n" * 120
        rows += "yuriDamageTab:\n" + "    .dw 0\n" * 120
        with tempfile.TemporaryDirectory() as directory:
            tables = Path(directory)
            (tables / "yuri_spr.inc").write_text(rows)
            result = audit.character("yuri", tables)
        self.assertEqual([r["sid"] for r in result["rules"]], [48])
        self.assertLess(result["metadata"][48]["state"], 1000)


if __name__ == "__main__":
    unittest.main()
