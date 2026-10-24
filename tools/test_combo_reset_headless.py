#!/usr/bin/env python3
"""Headless regression: a new match starts with an empty combo counter.

The select screen launches the fight through StartFight, not through
ShowTitle/ST_select, so StartFight itself must clear combohit/combotmr.
Otherwise the first punch draws whatever WRAM held at $4FC0 -- seen as a
spurious "84 HITS" on Benimaru's opening attack.

Run after a PVSnesLib build:

    python3 tools/test_combo_reset_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight, tap  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_HP, F_X = 0x4008, 0x4010, 0x4000
FP2 = 0x40
COMBO, COMBO2 = 0x4FC0, 0x5000
COMBOTMR, COMBOTMR2 = 0x5001, 0x5041
Y_BTN = 1                               # weak punch (SNES Y -> x)


def main(core_path, rom):
    core = Core(core_path, rom)
    failed = []
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "benimaru", "kyo")

        stale = [core.ram[a] for a in (COMBO, COMBO2, COMBOTMR, COMBOTMR2)]
        if any(stale):
            failed.append("new match kept stale combo state: " +
                          ", ".join(f"${a:04X}={v}" for a, v
                                    in zip((COMBO, COMBO2, COMBOTMR,
                                            COMBOTMR2), stale)))
        else:
            print("PASS first round starts with combo 0", flush=True)

        core.put(F_X, 130 << 8)          # step into weak-punch range
        core.put(F_X + FP2, 160 << 8)
        core.step(10)
        hp0 = core.word(F_HP + FP2)
        tap(core, Y_BTN)                 # Benimaru's first weak punch
        peak = 0
        for _ in range(60):
            core.step()
            peak = max(peak, core.ram[COMBO])
        hp1 = core.word(F_HP + FP2)
        if peak != 1:
            failed.append(f"single punch counted {peak} hits")
        elif hp1 >= hp0:
            failed.append(f"punch did not connect (hp {hp0} -> {hp1})")
        else:
            print(f"PASS single punch = 1 hit ({hp0 - hp1} damage)",
                  flush=True)

        core.buttons = [set(), set()]
        core.step(20)                    # 8-tick display grace expires
        if core.ram[COMBO]:
            failed.append("combo did not clear after recovery")
        elif core.word(F_STATE) == 0 and core.word(F_STATE + FP2) == 0:
            print("PASS combo cleared after recovery", flush=True)

        # Continue a one-hit display grace with a real second contact.  Two
        # hits draw the HITS string; WriteStr returns A=16, so ComboDraw must
        # restore A=8 before marking the HUD dirty or it executes operands.
        core.put(F_X, 130 << 8)
        core.put(F_X + FP2, 160 << 8)
        core.ram[COMBO] = 1
        core.ram[COMBOTMR] = 60
        hp0 = core.word(F_HP + FP2)
        tap(core, Y_BTN)
        peak, advances = core.ram[COMBO], 0
        for _ in range(120):
            frame = core.ram[0x1024]
            core.step()
            advances += core.ram[0x1024] != frame
            peak = max(peak, core.ram[COMBO])
        if peak != 2 or core.word(F_HP + FP2) >= hp0:
            failed.append(f"second contact did not draw 2 HITS: peak={peak}")
        elif advances < 100 or core.word(F_STATE) != 0:
            failed.append(f"2 HITS display froze the fight: advances={advances}")
        else:
            print("PASS 2 HITS display returns and fight keeps advancing",
                  flush=True)
    finally:
        core.close()
    if failed:
        raise AssertionError("; ".join(failed))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
