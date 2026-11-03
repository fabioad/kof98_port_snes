import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
FIGHT = os.path.join(ROOT, "src", "engine", "fight.asm")


def block(text, start, end):
    first = text.index(start)
    last = text.index(end, first)
    return text[first:last]


class TeamMemberStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(FIGHT, encoding="utf-8", errors="replace") as source:
            cls.text = source.read()

    def test_member_change_drops_the_staged_chr_chunk(self):
        # The vblank alternates when both sides stream, leaving one side's
        # chunk staged in SP_KIND.  TeamMemberIn must drop it before the
        # newcomer requests its first sprite; otherwise the old chunk is
        # DMA'd and the old SP_META (boxes) is committed to the newcomer.
        body = block(self.text, "TeamMemberIn:", "TeamSelTick:")
        for field in ("SP_KIND", "SP_COUNT", "SP_LEN", "SP_META"):
            self.assertIn(f"stz.w {field},x", body)

    def test_new_confrontation_clears_the_swap_flag(self):
        # A member KO sets T_SWAP.  If it survives into the next
        # confrontation, StartFight takes the partial TeamSwap path and the
        # player's trio keeps the survivor's low HP/position.
        self.assertIn("stz.w T_SWAP", block(self.text, "CampNext:",
                                            "CampResolve:"))
        self.assertIn("stz.w T_SWAP", block(self.text, "CampResolve:",
                                            "CampStage:"))


if __name__ == "__main__":
    unittest.main()
