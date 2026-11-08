import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1, P2 = 0x4000, 0x4040


def main(rom):
    core = Core(CORE, rom)
    try:
        select = boot_select(core)
        for name in ("ryu", "ken", "geese"):
            enter_fight(core, select, name, "kyo")
            core.ram[0x1090] = core.ram[0x1091] = 0
            core.put(P1, 110 << 8)
            core.put(P2, 135 << 8)
            core.step(30)
            core.buttons[0] = {1, 9, 7}
            last_frame = -1
            crossed = released = False
            for tick in range(180):
                if tick == 3:
                    core.buttons[0] = set()
                core.step()
                attacker, victim = core.ram[P1 + 8], core.ram[P2 + 8]
                if attacker == 75 and victim == 76:
                    frame = core.ram[P2 + 10]
                    assert frame >= last_frame, (name, tick, last_frame, frame)
                    last_frame = frame
                    if name in ("ryu", "ken") and core.ram[P1 + 10] in (2, 3):
                        assert core.word(P2 + 14) == 1, (name, tick, core.word(P2 + 14))
                        crossed = True
                if last_frame >= 0 and victim != 76:
                    released = True
                    break
            assert released and (name == "geese" or crossed), name
            print(f"PASS {name}: held pose and release")
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    main(parser.parse_args().rom)
