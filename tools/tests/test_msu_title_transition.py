"""Static guards for the MSU opening -> title hand-off.

The video hook used to stay live for a few hundred cycles after the last
frame while TitleEnter was already loading the title art.  A vblank in that
window re-asserted TM/BG2 and could consume a staged VRAM chunk into the
map/OBJ area, which showed up as a periodically garbled title after a full
opening playback.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MSU = (ROOT / "src/engine/msu_intro.asm").read_text()
MENU = (ROOT / "src/engine/menucore.asm").read_text()


def between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i)]


class MsuTitleTransitionTests(unittest.TestCase):
    def test_handoff_disables_nmi_and_drops_pending_chunks(self):
        block = between(MSU, "MI_Handoff:", "jml MsuTitleEnterBridge")
        self.assertIn("sta.l $4200", block)
        # A = 0 immediately before the NMI port write.
        self.assertIn("lda #0\n    sta.l $4200", block)
        for state in ("MV_STAGED", "MV_LOCK", "MV_FINISH",
                      "MV_READY", "MV_TOTAL"):
            self.assertIn(f"stz.w {state}", block)

    def test_vblank_ignores_the_finished_video(self):
        block = between(MSU, "MsuVideoVblank:", "sta.l $2105")
        self.assertIn("lda.w MV_FINISH", block)
        self.assertIn("bne MVV_out", block)

    def test_title_enters_gs0_before_loading_art(self):
        block = between(MENU, "TitleEnter:", "jsr MnLoadArt")
        self.assertIn("stz.b gamestate", block)


if __name__ == "__main__":
    unittest.main()
