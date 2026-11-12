"""Clark's Ultra Argentine slam: the victim must follow the bind even when the
thrower's sprite uploads were coalesced away.

In a real match the CHR upload of several 3015 elems can be dropped while an
earlier one is still streaming in.  The tiles that finally land can then be the
last elem (10, the 24-tick slam hold), which has no bind row of its own.  The
bind used to be skipped in that case, freezing the victim at the height of the
last elem it did see (~70 px up) while Clark finished the slam on the ground.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight
from trace_clark_throws_headless import CASES, motion, snap

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1, P2 = 0x4000, 0x4040
F_STATE, F_FRAME = 8, 10
F_SHOWN = 188               # elem whose tiles are on screen
S_TSEQ = 106                # 3016, the Ultra Argentine final slam


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "clark", "iori")
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.step(20)
        label, mot, buttons, gap, _ = next(
            c for c in CASES if c[0] == "Ultra Argentine weak")
        core.put(P1, 110 << 8)
        core.put(P2, (110 + gap) << 8)
        core.put(P1 + 48, 3000)
        core.put(P1 + 16, 200)
        core.put(P2 + 16, 200)
        core.step(20)
        steps = motion(mot, snap(core, P1)["facing"] > 0)
        for tok in steps:
            core.buttons[0] = set(tok)
            core.step(2)
        core.buttons[0] = set(steps[-1]) | set(buttons)
        core.step(2)
        core.buttons[0] = set()
        core.step(1)
        for _ in range(420):
            if (core.ram[P1 + F_STATE] == S_TSEQ
                    and core.ram[P1 + F_FRAME] >= 8
                    and core.word(P2 + 2) <= 8 << 8):
                break
            core.step(1)
        else:
            raise AssertionError("slam never reached")
        # Coalesced uploads: the only tiles that landed are the final elem.
        for _ in range(4):
            core.ram[P1 + F_SHOWN] = 10
            core.step(1)
            y = core.word(P2 + 2) / 256
            assert y <= 8, f"victim froze {y:.0f} px up on an unbind elem"
        print("PASS clamp: unbind elem keeps the victim on the floor")
    finally:
        core.close()


if __name__ == "__main__":
    main()
