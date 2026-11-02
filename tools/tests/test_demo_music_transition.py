"""Static guards for the title -> attract-demo music transition.

MusPlaySong loads a frontend/UI module (Cipher Beta).  It used to leave
MUSIC_VALID set, so when the demo randomly picked the same stage as the last
bout, StageMusic skipped the reload: the title theme kept playing and the UI
effect slots (including the winner announcer) stayed selected.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPTIONS = (ROOT / "src/engine/options.asm").read_text()
VOICE = (ROOT / "src/engine/voice_queue.asm").read_text()
FIGHT = (ROOT / "src/engine/fight.asm").read_text()


def between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i)]


class DemoSongTransitionTests(unittest.TestCase):
    def test_frontend_song_invalidates_the_stage_cache(self):
        block = between(OPTIONS, "MusPlaySongFar:", "MPS_out:")
        self.assertIn("sta.w UI_SFXLOAD", block)
        self.assertIn("lda #0\n    sta.w MUSIC_VALID", block)
        self.assertLess(block.index("sta.w UI_SFXLOAD"),
                        block.index("sta.w MUSIC_VALID"))

    def test_stage_loader_distrusts_a_ui_module(self):
        block = between(VOICE, "StageMusicFar:", "SMF_changed:")
        self.assertIn("lda.w UI_SFXLOAD", block)
        self.assertIn("bne SMF_changed", block)
        self.assertLess(block.index("lda.w UI_SFXLOAD"),
                        block.index("lda.w MUSIC_STAGE"))

    def test_fight_start_drops_a_deferred_winner_voice(self):
        block = between(FIGHT, "StartFight:", "SF_not_team:")
        self.assertIn("stz.b winvoice", block)


if __name__ == "__main__":
    unittest.main()
