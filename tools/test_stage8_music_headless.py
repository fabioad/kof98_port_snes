#!/usr/bin/env python3
"""Regression: stage-8 music switches never freeze the SNESMOD handshake.

The bug was ARAM exhaustion: stage 8's module plus the seven combat effects
reloaded after every spcLoad crossed into the region reserved for streamed
character voices, so the APU stopped acknowledging uploads.  The next music
change (the winner theme after a fight, or the next stage's theme) then hung
inside spcLoad/SpcFlushSafe.

This drives the real game in SINGLE PLAY, SURVIVOR and TEAM PLAY.  To make
the reproduction deterministic it patches a throw-away ROM copy so
CampPickStage always returns stage index 8; the shipped ROM is untouched.
"""
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from capture_pair_headless import tap, wait

CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
ROM = ROOT / "kof98-snes.sfc"
SYMFILE = ROOT / "kof98-snes.symfull"
MSU = ROOT / "kof98-snes.msu"

GS = 0x1020
FRAME = 0x1024
STAGE = 0x1087
WINS1 = 0x1080
SEL1 = 0x1085
LOCK1 = 0x108E
LOCK2 = 0x108F
CPU1 = 0x1090
CPU2 = 0x1091
HP2 = 0x4050
C_IDX = 0x10C1
M_ITEM = 0xF070

# ExHiROM: the no$snes symbol table stores CPU addresses; code banks
# $00-$3F/$C0-$FF map to the first/second 4 MiB with a $C00000 bias.
SYM_BIAS = 0xC00000
PATCH = bytes((
    0xE2, 0x20,             # sep #$20
    0xA9, 0x08,             # lda #8
    0x8D, 0xC4, 0x10,       # sta.w C_STAGE
    0x60,                   # rts
))


def forced_stage8_rom(tmpdir: Path) -> Path:
    """Copy the ROM and make every campaign pick use stage index 8."""
    match = re.search(r"^([0-9a-fA-F]+) CampPickStage$",
                      SYMFILE.read_text(), re.M)
    if not match:
        raise AssertionError("CampPickStage missing from kof98-snes.symfull")
    offset = int(match.group(1), 16) - SYM_BIAS
    data = bytearray(ROM.read_bytes())
    if not (0 <= offset < len(data) - len(PATCH)):
        raise AssertionError(f"CampPickStage offset {offset:#x} outside ROM")
    data[offset:offset + len(PATCH)] = PATCH
    rom = tmpdir / "stage8-music.sfc"
    rom.write_bytes(data)
    if MSU.exists():
        msu = tmpdir / "stage8-music.msu"
        try:
            msu.symlink_to(MSU)
        except OSError:
            shutil.copyfile(MSU, msu)
    return rom


def stalled(core, last, same, label, stall=300):
    cur = (core.ram[GS], core.ram[FRAME])
    if cur == last:
        same += 1
        if same > stall:
            raise AssertionError(
                f"{label}: stalled gs={core.ram[GS]} frame={core.ram[FRAME]} "
                f"stage={core.ram[STAGE]} cidx={core.ram[C_IDX]}")
        return last, same
    return cur, 0


def wait_game(core, pred, label, limit=6000, stall=300):
    last = None
    same = 0
    for _ in range(limit):
        if pred():
            return
        core.step()
        last, same = stalled(core, last, same, label, stall)
    raise AssertionError(
        f"{label}: timeout gs={core.ram[GS]} frame={core.ram[FRAME]} "
        f"stage={core.ram[STAGE]} cidx={core.ram[C_IDX]}")


def lock_sides(core, mode_item):
    for _ in range(80):
        if core.ram[GS] == 6:
            break
        tap(core, 3)
    wait(core, lambda: core.ram[GS] == 6, "mode menu")
    core.ram[M_ITEM] = mode_item
    tap(core, 3)
    wait(core, lambda: core.ram[GS] == 5, f"select item {mode_item}")
    core.ram[SEL1] = 0
    core.ram[LOCK1] = 1
    core.ram[LOCK2] = 1
    core.ram[CPU1] = 0
    core.ram[CPU2] = 1
    core.step()


def single(core):
    lock_sides(core, 0)
    wait_game(core, lambda: core.ram[GS] == 1, "single battle 1")
    assert core.ram[STAGE] == 8, f"forced stage = {core.ram[STAGE]}"
    for battle in range(1, 5):
        core.ram[WINS1] = 1
        core.put(HP2, 0)
        wait_game(core, lambda: core.ram[GS] == 0, f"single winner {battle}")
        wait_game(core, lambda: core.ram[C_IDX] == battle and
                  core.ram[GS] in (1, 4), f"single battle {battle + 1}")
        wait_game(core, lambda: core.ram[GS] == 1,
                  f"single battle {battle + 1} ready")
    print("PASS single play stage-8 music switch", flush=True)


def survivor(core):
    lock_sides(core, 4)
    wait_game(core, lambda: core.ram[GS] in (1, 4), "survivor battle 1")
    assert core.ram[STAGE] == 8, f"forced stage = {core.ram[STAGE]}"
    for battle in range(1, 4):
        wait_game(core, lambda: core.ram[GS] == 1,
                  f"survivor battle {battle} ready")
        core.ram[WINS1] = 1
        core.put(HP2, 0)
        wait_game(core, lambda: core.ram[GS] == 0,
                  f"survivor winner {battle}")
        wait_game(core, lambda: core.ram[C_IDX] == battle and
                  core.ram[GS] in (1, 4), f"survivor battle {battle + 1}")
    print("PASS survivor stage-8 music switch", flush=True)


def team(core):
    for _ in range(80):
        if core.ram[GS] == 6:
            break
        tap(core, 3)
    wait(core, lambda: core.ram[GS] == 6, "mode menu")
    core.ram[M_ITEM] = 2
    tap(core, 3)
    wait(core, lambda: core.ram[GS] == 5, "team select")
    core.ram[CPU2] = 1
    # TEAM PLAY asks the human side for three distinct members: A locks the
    # cell under the cursor, RIGHT advances to a fresh one.
    for _ in range(3):
        tap(core, 8)
        for _ in range(30):
            if core.ram[GS] in (1, 4):
                break
            core.step()
        if core.ram[GS] in (1, 4):
            break
        tap(core, 7)
        core.step(10)
    wait_game(core, lambda: core.ram[GS] in (1, 4), "team match 1")
    assert core.ram[STAGE] == 8, f"forced stage = {core.ram[STAGE]}"
    # Fall all three CPU members: member swaps keep the stage module loaded,
    # then the match-over banner loads the next match's stage music.
    for member in range(1, 4):
        wait_game(core, lambda: core.ram[GS] == 1,
                  f"team member {member} ready")
        core.put(HP2, 0)
        wait_game(core, lambda: core.ram[GS] == 0,
                  f"team member {member} out")
        wait_game(core, lambda: core.ram[GS] in (1, 4),
                  f"team member {member + 1} in", limit=2500)
    wait_game(core, lambda: core.ram[C_IDX] == 1 and
              core.ram[GS] in (1, 4), "team match 2", limit=3000, stall=500)
    print("PASS team play stage-8 music switch", flush=True)


def main():
    if not CORE.exists():
        raise SystemExit(f"missing libretro core: {CORE}")
    if not ROM.exists():
        raise SystemExit(f"build the ROM first: {ROM}")
    with tempfile.TemporaryDirectory(prefix="stage8-music-",
                                     dir=ROOT / "build") as td:
        rom = forced_stage8_rom(Path(td))
        for case in (single, survivor, team):
            core = Core(CORE, rom)
            try:
                case(core)
            finally:
                core.close()
    print("PASS stage-8 music switches (single, survivor, team)")


if __name__ == "__main__":
    main()
