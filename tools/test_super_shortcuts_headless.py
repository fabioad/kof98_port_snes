#!/usr/bin/env python3
"""Easy super inputs must exist alongside the original KOF commands.

Additive shortcut rules only: Yuri's pretzel supers, Geese's Raging Storm and
MAX Rashomon, and Terry's Power Geyser.  The classic entries from each
_SNES.cmd stay in the command table and are checked here too.

Run after a PVSnesLib build:

    python3 tools/test_super_shortcuts_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import audit_specials_headless as audit                # noqa: E402
from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"

QCB2_X = [[2, 0], [10, 0], [8, 0], [2, 0], [10, 0], [8, 0], [0, 1]]
QCF2_A = [[2, 0], [6, 0], [4, 0], [2, 0], [6, 0], [4, 0], [0, 4]]
QCF2_AB = [[2, 0], [6, 0], [4, 0], [2, 0], [6, 0], [4, 0], [0, 12]]
QCB2_XY = [[2, 0], [10, 0], [8, 0], [2, 0], [10, 0], [8, 0], [0, 3]]

CASES = (
    # char, state, elements, label
    ("yuri", 500, QCB2_X, "HAOH SC"),
    ("yuri", 510, QCF2_A, "HIEN SC"),
    ("yuri", 500, [[68, 0], [8, 0], [10, 0], [6, 0], [4, 0], [0, 1]],
     "HAOH original"),
    ("geese", 3000, QCB2_X, "RAGING SC"),
    ("geese", 3250, QCF2_AB, "RASHOMON SC"),
    ("geese", 3250, [[72, 0], [2, 0], [4, 0], [0, 12]],
     "RASHOMON original"),
    ("terry", 3000, QCB2_X, "GEYSER SC"),
    ("terry", 3050, QCB2_XY, "GEYSER SC MAX"),
    ("terry", 3000, [[66, 0], [8, 0], [4, 0], [0, 1]],
     "GEYSER original"),
)


def find_rule(info, state, elements):
    for rule in info["rules"]:
        if (info["metadata"][rule["sid"]]["state"] == state
                and rule["elements"] == elements):
            return rule
    return None


def main():
    for char, state, elements, label in CASES:
        info = audit.character(char, ROOT / "build/gen_fight")
        rule = find_rule(info, state, elements)
        assert rule is not None, f"{label}: command rule missing"
        core = Core(CORE, ROOT / "kof98-snes.sfc")
        try:
            select = boot_select(core)
            enter_fight(core, select, char, "kyo")
            result = audit.attempt(core, core.save(), info, rule,
                                   complement=True, input_game_ticks=True)
            assert result["entered"], f"{label}: did not enter {state}"
            assert result["final_damage"] > 0, (
                f"{label}: no damage, path {result['path']}")
            print(f"PASS {label}: state {state} (sid {rule['sid']}), "
                  f"{result['final_damage']} HP, path {result['path']}")
        finally:
            core.close()


if __name__ == "__main__":
    main()
