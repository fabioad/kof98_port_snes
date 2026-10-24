#!/usr/bin/env python3
"""Regression: a team match must end with the survivor's WINS banner.

Team play/Team VS never score round wins (RoundEnd always hands a member KO
to TeamRoundEnd), but DrawBanner picks its winner and quote from wins1/wins2.
With both still 0-0 the last KO used to show "DRAW" with no victory quote.
TeamRoundEnd now records the surviving side from MATWON before ShowTitle.

The test plays a full five-round confrontation so both trios actually reach
their third member through TeamSwap before the deciding KO.

Run after a PVSnesLib build:

    python3 tools/test_team_banner_headless.py
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                       # noqa: E402
from capture_pair_headless import wait                      # noqa: E402
from test_midfight_join_headless import start_team, GS       # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
NEXTF = 0x1084
WINS1, WINS2 = 0x1080, 0x1081
G_MODE = 0x10C0
T_TEAM1, T_TEAM2 = 0x10CB, 0x10CE
HP1, HP2 = 0x4010, 0x4050
HUDMAP = 0x4700
CHARSET = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.:!?'-/+>,@\""


def big_strings():
    """Parse the generated big-font strings (len + tile ids) from hud.inc."""
    out = {}
    text = (ROOT / "build/gen_fight/hud.inc").read_text()
    for m in re.finditer(r"^(\w+): \.db (\d+),([0-9,]+)$", text, re.M):
        n = int(m.group(2))
        out[m.group(1)] = [int(v) for v in m.group(3).split(",")][:n]
    return out


def cell(core, row, col):
    # Low byte = tile id; the high byte is the gold announce attribute.
    return core.ram[HUDMAP + (row * 32 + col) * 2]


def decode_row(core, row):
    raw = [core.ram[HUDMAP + row * 64 + i] for i in range(0, 64, 2)]
    while raw and raw[0] == 0:
        raw.pop(0)
    while raw and raw[-1] == 0:
        raw.pop()
    return "".join(CHARSET[i] if i < len(CHARSET) else "?" for i in raw)


def check_banner(core, name_label, big):
    name = big[name_label]
    wins = big["BStrWins"]
    start = (32 - (len(name) + 5)) // 2

    got_name = [cell(core, 8, start + i) for i in range(len(name))]
    assert got_name == name, f"banner name {got_name} != {name}"
    got_wins = [cell(core, 8, start + len(name) + 1 + i)
                for i in range(len(wins))]
    assert got_wins == wins, f"banner tail {got_wins} != {wins}"

    quote1 = decode_row(core, 12)
    quote2 = decode_row(core, 14)
    assert quote1 or quote2, "winner quote missing on the match-over screen"
    return quote1, quote2


def ko(core, side, expect=1):
    """KO one side and wait for the intermission (1) or match over (2)."""
    wait(core, lambda: core.ram[GS] == 1, "fight", 6000)
    core.step(10)
    core.put(HP1 if side == 0 else HP2, 0)
    label = "team match over" if expect == 2 else "round intermission"
    wait(core, lambda: core.ram[GS] == 0 and core.ram[NEXTF] == expect,
         label, 4000)


def run_case(core, p2_wins, big, mode=2):
    start_team(core)
    if mode == 3:
        # Same TeamRoundEnd path as Team VS; keep the fight state and only
        # switch the mode so RoundEnd takes its G_MODE 3 branch.
        core.ram[G_MODE] = 3
    # Both trios: member 3 is the one alive at the deciding round.
    for i, ch in enumerate((0, 1, 2)):
        core.ram[T_TEAM1 + i] = ch
    for i, ch in enumerate((2, 0, 1)):
        core.ram[T_TEAM2 + i] = ch

    # Alternate round winners until both sides are on their last member:
    #   R1 P1, R2 P2, R3 P1, R4 P2 -> T_I1 = T_I2 = 2.
    for winner in (0, 1, 0, 1):
        ko(core, 1 - winner)
        wait(core, lambda: core.ram[GS] == 1, "next round", 6000)

    # Deciding round: member 3 is Shingo (sel 2) vs Iori (sel 1).
    ko(core, 0 if p2_wins else 1, expect=2)
    core.step(10)

    if p2_wins:
        assert core.ram[WINS1] == 0 and core.ram[WINS2] == 2, \
            (core.ram[WINS1], core.ram[WINS2])
        quote = check_banner(core, "BStrKfm", big)
    else:
        assert core.ram[WINS1] == 2 and core.ram[WINS2] == 0, \
            (core.ram[WINS1], core.ram[WINS2])
        quote = check_banner(core, "BStrShingo", big)
    print(f"PASS team {'P2' if p2_wins else 'P1'} last-member win "
          f"(mode {mode}): WINS banner + quote {quote!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()

    big = big_strings()
    for mode in (2, 3):
        for p2_wins in (False, True):
            core = Core(args.core, args.rom)
            try:
                run_case(core, p2_wins, big, mode)
            finally:
                core.close()
    print("team match-over banner: Team Play and Team VS, both sides OK")


if __name__ == "__main__":
    main()
