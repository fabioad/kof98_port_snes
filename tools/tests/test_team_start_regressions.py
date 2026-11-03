import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
FIGHT = open(os.path.join(ROOT, "src", "engine", "fight.asm")).read()


def block(text, start, end):
    return text[text.index(start):text.index(end, text.index(start))]


class TeamStartTests(unittest.TestCase):
    def test_team_vs_initialises_the_stage(self):
        # Team VS used to skip CampStart, leaving C_STAGE at the RAM fill
        # value; StartFight then indexed StageTab out of range and hung.
        done = block(FIGHT, "TVS_done:", "TVS_deny:")
        self.assertIn("jsr CampStart", done)

    def test_team_swap_reloads_char_pals_under_forced_blank(self):
        # StagePick leaves the display on; LoadCharPals writes CGRAM and must
        # run blanked or the P2 palette is lost on hardware.
        swap = block(FIGHT, "TeamSwap:", "TeamMemberIn:")
        self.assertIn("jsr TeamPpuSetup", swap)
        self.assertIn("#$8F.b", swap)
        self.assertIn("sta.l INIDISP", swap)
        self.assertLess(swap.index("jsr TeamPpuSetup"),
                        swap.index("#$8F.b"))
        self.assertLess(swap.index("#$8F.b"),
                        swap.index("jsr TeamMemberIn") if "jsr TeamMemberIn" in swap
                        else len(swap))

    def test_team_member_in_uploads_palettes(self):
        member = block(FIGHT, "TeamMemberIn:", "Team select tick:")
        self.assertIn("jsr LoadCharPals", member)


if __name__ == "__main__":
    unittest.main()
