import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
MENUCORE = os.path.join(ROOT, "src", "engine", "menucore.asm")


def block(text, start, end):
    first = text.index(start)
    last = text.index(end, first)
    return text[first:last]


class ThrowSel1ImmediateTests(unittest.TestCase):
    """The throw helpers run in A16; their SfxPlay ids must be 8-bit.

    `lda #SFX_THROW.b` while the accumulator is 16-bit assembles as a
    16-bit immediate that swallows the following JSR/JMP opcode.  The
    leftover bytes then execute as `ROL $84`, rotating the pair
    nextflag/sel1 and doubling sel1 on every throw.  In Team Play the
    next member swap reloads the survivor's palette from that corrupted
    sel1, so the player's fighter changes colours.
    """

    @classmethod
    def setUpClass(cls):
        with open(MENUCORE, encoding="utf-8", errors="replace") as source:
            cls.text = source.read()

    def assert_8bit_sfx(self, start, end, immediate):
        body = block(self.text, start, end)
        line = f"lda #{immediate}"
        self.assertIn(line, body)
        before = body[:body.index(line)]
        self.assertIn("sep #$20", before,
                      f"{start}: missing SEP before {immediate}")
        self.assertIn(".ACCU 8", before,
                      f"{start}: missing .ACCU 8 before {immediate}")

    def test_throw_tech_guard_sfx_is_8bit(self):
        self.assert_8bit_sfx("ThrowTechFx:", "SlamRelease:", "SFX_GUARD.b")

    def test_launch_victim_throw_sfx_is_8bit(self):
        self.assert_8bit_sfx("LaunchVictim:", "MsuTitleEnterBridge:",
                             "SFX_THROW.b")


if __name__ == "__main__":
    unittest.main()
