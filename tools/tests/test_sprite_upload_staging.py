import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
FIGHT = open(os.path.join(ROOT, "src", "engine", "fight.asm")).read()
BRIDGE = open(os.path.join(ROOT, "src", "snes", "fight_bridge.asm")).read()


def block(text, start, end):
    return text[text.index(start):text.index(end, text.index(start))]


class SpriteUploadStagingTests(unittest.TestCase):
    """The CHR upload is split into a logic-phase staging pass and a vblank
    copy.  Guard the invariants that were broken while building it: the
    per-side state fields must not overlap, the staging must not touch the
    MSU port during vblank, and a zero DMA length (64 KiB on the SNES) must
    never reach MDMAEN."""

    def test_side_state_fields_are_four_bytes_apart(self):
        defs = re.findall(r"^\.DEFINE (SP_\w+)\s+\$([0-9A-F]+)", FIGHT,
                          re.M)
        fields = [(name, int(value, 16)) for name, value in defs
                  if name != "SP_SIDE"]
        for (_a, prev), (name, cur) in zip(fields, fields[1:]):
            self.assertEqual(cur - prev, 4,
                             f"{name}: P1/P2 word slots overlap")
        self.assertIn("SP_SIDE", dict(defs))

    def test_vblank_path_never_touches_the_msu_port(self):
        dma = block(BRIDGE, "SprDmaFar:", "\nSDF_ret:")
        self.assertNotIn("MSU_STAT", dma)
        self.assertNotIn("MSU_DATA", dma)
        self.assertNotIn("MsuStagePrepareFar", dma)
        self.assertIn("sta.l $4360", dma)
        self.assertIn("lda #$40.b\n    sta.l MDMAEN", dma)

    def test_staging_runs_with_the_display_on(self):
        stage = block(BRIDGE, "MsuStagePrepareFar:", "\n; SprDmaFar:")
        self.assertIn("jsl MsuChrPageClamp", stage)
        self.assertNotIn("INIDISP", stage)
        self.assertIn("sta.l $4355", stage)

    def test_prep_is_wired_and_records_the_prefix(self):
        self.assertIn("jsr SprPrepBoth", FIGHT)
        prep = block(FIGHT, "SprPrepOne:", "\nSP_commit_only:")
        self.assertIn("lda scr3", prep)
        self.assertIn("beq SP_commit_only", prep)
        self.assertIn("jsl MsuStagePrepareFar", FIGHT)
        self.assertIn("sta.w SP_PREFIX,y", FIGHT)

    def test_vblank_refuses_a_zero_byte_dma(self):
        dma = block(BRIDGE, "SprDmaFar:", "\nSDF_ret:")
        self.assertRegex(dma,
                         r"lda\.w SP_COUNT,y\s*\n\s*bne\s+\+\s*\n\s*jmp SDF_commit")


if __name__ == "__main__":
    unittest.main()
