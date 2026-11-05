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
                  if name not in ("SP_SIDE", "SP_MSUSTAGED", "SP_MSUOWN")]
        for (_a, prev), (name, cur) in zip(fields, fields[1:]):
            self.assertEqual(cur - prev, 4,
                             f"{name}: P1/P2 word slots overlap")
        self.assertIn("SP_SIDE", dict(defs))
        self.assertIn("SP_MSUSTAGED", dict(defs))
        self.assertIn("SP_MSUOWN", dict(defs))

    def test_vblank_path_does_the_msu_dma_under_blank(self):
        dma = block(BRIDGE, "SprDmaFar:", "\nSDF_ret:")
        self.assertIn("jsl MsuStageDmaFar", dma)
        self.assertNotIn("MsuStagePrepareFar", dma)
        self.assertIn("sta.l $4360", dma)
        self.assertIn("lda #$40.b\n    sta.l MDMAEN", dma)
        stage_dma = block(BRIDGE, "MsuStageDmaFar:\n", "\n.ENDS")
        self.assertIn("sta.l $4355", stage_dma)
        self.assertNotIn("INIDISP", stage_dma)

    def test_seek_wait_runs_with_the_display_on(self):
        stage = block(BRIDGE, "MsuStagePrepareFar:\n", "\n; SprDmaFar:")
        self.assertIn("jsl MsuChrPageClamp", stage)
        self.assertNotIn("INIDISP", stage)
        self.assertNotIn("MDMAEN", stage)
        self.assertNotIn("$4355", stage)

    def test_prep_is_wired_and_records_the_prefix(self):
        self.assertIn("jsr SprPrepBoth", FIGHT)
        prep = block(FIGHT, "SprPrepOne:", "\nSP_commit_only:")
        self.assertIn("lda scr3", prep)
        self.assertIn("beq SP_commit_only", prep)
        self.assertIn("jsl MsuStagePrepareFar", FIGHT)
        self.assertIn("sta.w SP_PREFIX,y", FIGHT)

    def test_both_sides_prep_but_only_one_msu_stream(self):
        prep = block(FIGHT, "SprPrepBoth:", "\n; X = fighter offset")
        # The staging order rotates with framecnt so a multi-chunk sprite on
        # one side cannot starve the other.
        self.assertEqual(prep.count("jsr SprPrepOne"), 4)
        self.assertIn("SP_MSUSTAGED", prep)
        self.assertIn("SP_MSUOWN", prep)
        msu = block(FIGHT, "SP_msu:", "\n; opening intro")
        self.assertIn("lda.w SP_MSUSTAGED", msu)
        self.assertIn("sta.w SP_MSUSTAGED", msu)
        self.assertIn("bne SP_msu_retry", msu)
        self.assertIn("sta.w SP_MSUOWN", msu)

    def test_msu_dma_only_consumes_the_owner_seek(self):
        dma = block(BRIDGE, "SprDmaFar:", "\nSDF_ret:")
        self.assertIn("cpy.w SP_MSUOWN", dma)
        self.assertIn("jmp SDF_ret", dma)

    def test_vblank_refuses_a_zero_byte_dma(self):
        dma = block(BRIDGE, "SprDmaFar:", "\nSDF_ret:")
        self.assertRegex(dma,
                         r"lda\.w SP_COUNT,y\s*\n\s*bne\s+\+\s*\n\s*jmp SDF_commit")


if __name__ == "__main__":
    unittest.main()
