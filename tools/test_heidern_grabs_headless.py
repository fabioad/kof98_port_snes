#!/usr/bin/env python3
"""Headless regression for Heidern's grab/drain supers.

Final Bringer's leap now hands the victim to S_VHELD and runs the source
3020-3023 drain; Heidern End gets the 3120/3160 finish on sids 115/116.
Both must keep the victim held, deal the drain damage and finish with the
generic thrown flight (77).

Run after a PVSnesLib build:

    python3 tools/test_heidern_grabs_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

P1, P2 = 0x4000, 0x4040
UP, DOWN, LEFT, RIGHT = 4, 5, 6, 7
PAD_Y, PAD_X, PAD_A, PAD_B = 1, 9, 8, 0   # Heidern cmd x/y/a/b


def settle(core, limit=900):
    stable = 0
    for _ in range(limit):
        core.step()
        if (core.ram[P1 + 8] == 0 and core.ram[P2 + 8] == 0
                and core.word(P1 + 2) == 0 and core.word(P2 + 2) == 0):
            stable += 1
            if stable >= 20:
                return
        else:
            stable = 0


def press(core, seq, buttons):
    for d in seq:
        core.buttons[0] = set(d)
        core.step(2)
    core.buttons[0] = set(seq[-1]) | set(buttons)
    core.step(2)
    core.buttons[0] = set()


def qcbhcf():
    return [(DOWN,), (DOWN, LEFT), (LEFT,), (DOWN, LEFT),
            (DOWN,), (DOWN, RIGHT), (RIGHT,)]


def hcbhcb():
    return [(RIGHT,), (DOWN, RIGHT), (DOWN,), (DOWN, LEFT), (LEFT,)] * 2


def run(core, select_state, dist, seq, buttons):
    enter_fight(core, select_state, "heidern", "kyo")
    core.put(P1, 80 << 8)
    core.put(P2, (80 + dist) << 8)
    core.put(P1 + 16, 200)
    core.put(P2 + 16, 200)
    core.put(P1 + 48, 5000)
    core.ram[P1 + 8] = core.ram[P2 + 8] = 0
    core.ram[P1 + 2] = core.ram[P2 + 2] = 0
    settle(core)
    core.ram[P1 + 52] = core.ram[P1 + 53] = 0
    core.ram[P2 + 52] = core.ram[P2 + 53] = 0
    hp0 = core.word(P2 + 16)
    press(core, seq, buttons)
    path, vpath = [], []
    held = front = threw = False
    for i in range(420):
        core.step()
        state = core.ram[P1 + 8]
        victim = core.ram[P2 + 8]
        if not path or path[-1] != state:
            path.append(state)
        if not vpath or vpath[-1] != victim:
            vpath.append(victim)
        if victim in (76, 100, 102):
            held = True
            if (core.word(P2) >> 8) > (core.word(P1) >> 8):
                front = True
        if victim == 77:
            threw = True
        if state == 0 and i > 30:
            break
    return {
        "damage": hp0 - core.word(P2 + 16),
        "path": path, "vpath": vpath,
        "held": held, "front": front, "threw": threw,
    }


def check(name, result, damage, path_sid):
    assert result["held"], f"{name}: victim was never held"
    assert result["front"], f"{name}: victim bound behind Heidern"
    assert result["threw"], f"{name}: victim not released with state 77"
    assert path_sid in result["path"], \
        f"{name}: attacker never entered sid {path_sid} ({result['path']})"
    assert result["damage"] >= damage, \
        f"{name}: damage {result['damage']} < {damage}"
    print(f"PASS {name}: dmg={result['damage']} path={result['path']} "
          f"vpath={result['vpath']}")


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        check("Final Bringer weak",
              run(core, select_state, 20, qcbhcf(), [PAD_Y]), 30, 104)
        check("Final Bringer strong",
              run(core, select_state, 20, qcbhcf(), [PAD_X]), 38, 104)
        check("Final Bringer MAX",
              run(core, select_state, 20, hcbhcb(), [PAD_Y, PAD_X]), 46, 104)
        check("Heidern End weak",
              run(core, select_state, 24, qcbhcf(), [PAD_B]), 80, 115)
        check("Heidern End strong",
              run(core, select_state, 24, qcbhcf(), [PAD_A]), 80, 115)
        check("Heidern End MAX",
              run(core, select_state, 24, hcbhcb(), [PAD_Y]), 96, 116)
    finally:
        core.close()


if __name__ == "__main__":
    core_path = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
    rom = str(ROOT / "kof98-snes.sfc")
    main(core_path, rom)
