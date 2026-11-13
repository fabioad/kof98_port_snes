from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1, P2 = 0x4000, 0x4040


def andy_lift():
    """Andy's jumping throw must carry the victim through the jump.

    The bind dy is added to the attacker's live Y.  Before the signed
    overflow fix, the victim's high bind plus Andy's jump wrapped negative
    and the victim stayed on the floor while Andy rose.
    """
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "andy", "kyo")
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.put(P1, 100 << 8)
        core.put(P2, 125 << 8)
        core.step(20)
        core.buttons[0] = {9, 1, 7}
        core.step(3)
        core.buttons[0] = set()
        lifted = False
        for _ in range(110):
            core.step()
            if core.ram[P1 + 8] != 75 or core.ram[P2 + 8] != 76:
                continue
            if core.word(P1 + 2) >= (20 << 8) and core.word(P2 + 2) > (40 << 8):
                lifted = True
                break
        assert lifted, "Andy jumped but the bound victim stayed on the floor"
        print("PASS Andy jumping throw carries the victim")
    finally:
        core.close()


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "ryo", "kyo")
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.put(P1, 110 << 8)
        core.put(P2, 135 << 8)
        core.step(20)
        core.buttons[0] = {9, 1, 7}
        core.step(3)
        core.buttons[0] = set()
        checked_x = checked_y = False
        for _ in range(110):
            core.step()
            if core.ram[P1 + 8] != 75 or core.ram[P2 + 8] != 76:
                continue
            # ThrowBind follows the elem whose tiles are on screen
            # (F_SHOWN, byte 188), lagging F_FRAME while a big sprite
            # streams in; test the offsets of that elem.
            frame = core.ram[P1 + 188]
            x1, x2 = core.word(P1), core.word(P2)
            y1, y2 = core.word(P1 + 2), core.word(P2 + 2)
            if frame == 5:
                assert abs(x2 - x1 + (4 << 8)) <= 1, (frame, x1, x2)
                checked_x = True
            if frame == 7 and y1 >= 8 << 8:
                # ryoBind75 elem 7: dy = -67 at the 0.88 grab scale
                assert abs(y2 - y1 - (67 << 8)) <= 1, (frame, y1, y2)
                checked_y = True
        assert checked_x and checked_y, (checked_x, checked_y)
        print("PASS signed throw bind and airborne victim tracking")
    finally:
        core.close()
    andy_lift()


if __name__ == "__main__":
    main()
