import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
ABI = json.load(open(os.path.join(ROOT, "assets", "runtime_abi.json")))
FIGHT = open(os.path.join(ROOT, "src", "engine", "fight.asm")).read()


class PresentationTelemetryTests(unittest.TestCase):
    def test_telemetry_block_is_reserved_and_compact(self):
        base = ABI["TEL_FRAMES"]
        end = ABI["TEL_MAX2"] + 1
        self.assertGreaterEqual(base, 0x51B0)
        self.assertLessEqual(end, 0x51E0)
        # 32-bit HUD byte counter must not overlap the next field.
        self.assertGreaterEqual(ABI["TEL_HUD_FRAMES"],
                                ABI["TEL_HUD_BYTES"] + 4)

    def test_upload_budget_matches_the_build(self):
        src = open(os.path.join(ROOT, "tools", "build_fight.py")).read()
        self.assertIn('RUNTIME_ABI["DMACHUNK"]', src)
        self.assertGreaterEqual(ABI["DMACHUNK"], 1024)

    def test_hud_uses_dirty_bands_and_one_dma_per_frame(self):
        self.assertIn("HudBandTab:", FIGHT)
        for band in ("HUD_LIFE", "HUD_POWER", "HUD_POWCNT",
                     "HUD_TIMER", "HUD_COMBO", "HUD_FULL"):
            self.assertIn(band, FIGHT)
        # Live path must select a band; full flush is opt-in via HUD_FULL.
        self.assertIn("beq FlushHudLive", FIGHT)
        self.assertIn("jsr FlushHudRange", FIGHT)
        self.assertIn("inc.w TEL_HUD_FRAMES", FIGHT)

    def test_coalesced_pose_counter_is_wired(self):
        self.assertIn("TEL_DROP_P1", FIGHT)
        self.assertIn("ASF_q_drop:", FIGHT)
        self.assertIn("ASF_q_drop", FIGHT[FIGHT.index("ASF_q_new:"):])


if __name__ == "__main__":
    unittest.main()
