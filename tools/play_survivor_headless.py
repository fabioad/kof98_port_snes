#!/usr/bin/env python3
"""Play a real SURVIVOR run headless (level 1) and report anomalies.

Drives pad 1 with a simple bot (walk in, attack in range, occasional
jump-ins), polls the same WRAM debug registers as tools/mesen_dbg.lua
every frame, and logs:

  * hard freezes (frame counter $1024 stops advancing),
  * softlocks (GS stuck > limit, fight with no damage for too long),
  * invalid states (GS outside the known set, HP out of range),
  * round/fight transitions until the survivor ending (GS=10) or a
    loss back at the select screen (GS=5).

Usage: play_survivor_headless.py [--msu 0|1] [--level N] [--seed N]
"""
from pathlib import Path
import argparse
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core

CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
ROM = ROOT / "kof98-snes.sfc"

GS = 0x1020
FRAME = 0x1024
M_ITEM = 0xF070
MSUOK = 0x107A
G_MODE = 0x10C0
C_IDX = 0x10C1
SEL1 = 0x1085
SEL2 = 0x1086
LOCK1 = 0x108E
LOCK2 = 0x108F
CPU1 = 0x1090
CPU2 = 0x1091
AI_LEVEL = 0x10EB
MARK = 0x4614
SCR = 0x4615

P1X = 0x4000
P1S = 0x4008
HP1 = 0x4010
P2X = 0x4040
P2S = 0x4048
HP2 = 0x4050
RSECS = 0x1076
WINS1 = 0x1080
WINS2 = 0x1081
SURV_LIST = 0x4F00
SURV_COUNT = 0x4F30

BTN_B, BTN_Y, BTN_START = 0, 1, 3
BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT = 4, 5, 6, 7
BTN_A, BTN_X = 8, 9
ATTACKS = (BTN_B, BTN_Y, BTN_X, BTN_A)

VALID_GS = {0, 1, 2, 4, 5, 6, 7, 8, 10}


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(8)


def wait(core, predicate, label, limit=8000):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise RuntimeError(f"{label}: gs={core.ram[GS]} mark={core.ram[MARK]:02X}")


def boot(core):
    for _ in range(80):
        if core.ram[GS] == 6:
            break
        tap(core, BTN_START)
    wait(core, lambda: core.ram[GS] == 6, "mode menu")


def enter_survivor(core, msu):
    core.ram[MSUOK] = msu
    core.ram[M_ITEM] = 4
    tap(core, BTN_START)
    wait(core, lambda: core.ram[GS] == 5, "select screen")
    assert core.ram[G_MODE] == 4, core.ram[G_MODE]


def play(msu, level, seed, attempts):
    rng = random.Random(seed)
    core = Core(CORE, ROM)
    events = []
    anomalies = []

    def note(msg):
        events.append(msg)
        print(f"  [t={total[0]:>7}] {msg}", flush=True)

    def bug(msg):
        anomalies.append(msg)
        print(f"  !! ANOMALY [t={total[0]:>7}] {msg}", flush=True)

    total = [0]

    def step(n=1):
        core.step(n)
        total[0] += n

    try:
        boot(core)

        def start_run():
            enter_survivor(core, msu)
            core.ram[AI_LEVEL] = level
            core.ram[SEL1] = 0                   # kyo
            core.ram[LOCK1] = 1
            core.ram[LOCK2] = 1
            core.ram[CPU1] = 0
            core.ram[CPU2] = 1
            wait(core, lambda: core.ram[GS] in (1, 4), "survivor fight 1")
            count = core.ram[SURV_COUNT]
            roster = [core.ram[SURV_LIST + i] for i in range(count)]
            note(f"survivor roster ({count}): {roster}")
            return count

        count = start_run()

        last_frame = core.ram[FRAME]
        frame_freeze = 0
        fight_no = 0
        last_cidx = -1
        last_gs = None
        gs_stuck = 0
        fight_ticks = 0
        last_hp2 = None
        no_damage_ticks = 0
        atk_i = 0
        air_atk = 0
        saw_fight = False
        round_active = False
        macro = []
        spec_cd = 60
        attempt = 1

        while True:
            step()
            gs = core.ram[GS]
            fc = core.ram[FRAME]

            # hard freeze: framecnt only ticks while GS==1
            if gs == 1 and fc == last_frame:
                frame_freeze += 1
                if frame_freeze == 120:
                    bug(f"frame counter frozen at {fc}, gs={gs} "
                        f"mark={core.ram[MARK]:02X}")
                    break
            else:
                frame_freeze = 0
            last_frame = fc

            if gs not in VALID_GS:
                bug(f"invalid GS={gs} mark={core.ram[MARK]:02X} "
                    f"scr={core.ram[SCR]:02X}")

            if gs == last_gs:
                gs_stuck += 1
            else:
                if last_gs is not None:
                    extra = ""
                    if gs == 2 or last_gs == 2:
                        extra = (f" roundwin={core.ram[0x1083]} "
                                 f"wins={core.ram[WINS1]}-{core.ram[WINS2]} "
                                 f"hp={core.word(HP1)}/{core.word(HP2)}")
                    note(f"GS {last_gs}->{gs} mark={core.ram[MARK]:02X} "
                         f"scr={core.ram[SCR]:02X}{extra}")
                last_gs = gs
                gs_stuck = 0
            if gs_stuck and gs_stuck % 12000 == 0:
                bug(f"GS={gs} stuck for {gs_stuck} frames "
                    f"(fight {fight_no}, cidx={core.ram[C_IDX]})")

            hp1, hp2 = core.word(HP1), core.word(HP2)
            if gs == 1 and 0 < hp1 < 60:
                core.put(HP1, 140)
                note(f"  bot assist: mid-round HP {hp1} -> 140")
                hp1 = 140
            if hp1 > 200 or hp2 > 200:
                bug(f"HP out of range hp1={hp1} hp2={hp2} gs={gs}")
            for name, x in (("p1x", core.word(P1X)), ("p2x", core.word(P2X))):
                if x > 320 << 8:
                    bug(f"{name} out of stage: {x / 256:.1f} gs={gs}")

            if gs == 1:
                if not round_active:
                    round_active = True
                    hp = core.word(HP1)
                    if hp < 140:
                        core.put(HP1, 140)
                        note(f"  bot assist: round-start HP {hp} -> 140")
                saw_fight = True
                fight_ticks += 1
                if last_hp2 is not None and hp2 < last_hp2:
                    no_damage_ticks = 0
                else:
                    no_damage_ticks += 1
                last_hp2 = hp2
                if no_damage_ticks == 60 * 75:
                    bug(f"fight {fight_no}: no damage for 75 s "
                        f"(hp1={hp1} hp2={hp2} p1x={core.word(P1X) >> 8} "
                        f"p2x={core.word(P2X) >> 8} rsecs={core.ram[RSECS]})")
                if fight_ticks == 60 * 120:
                    bug(f"fight {fight_no} exceeded 120 s of round time "
                        f"(rsecs={core.ram[RSECS]})")

                # --- bot input: jump-in pressure + high block -----------
                px, ex = core.word(P1X), core.word(P2X)
                st = core.ram[P1S]
                st2 = core.ram[P2S]
                dist = abs(ex - px) >> 8
                toward = BTN_RIGHT if ex > px else BTN_LEFT
                away = BTN_LEFT if ex > px else BTN_RIGHT
                foe_attacking = st2 in (5, 6, 7, 8, 19, 20, 21, 22, 23, 24,
                                        25, 26) or 48 <= st2 <= 69
                pad = set()
                if macro:
                    raw, ticks = macro[0]
                    core.buttons[0] = {
                        toward if b == BTN_RIGHT else
                        away if b == BTN_LEFT else b for b in raw}
                    if ticks <= 1:
                        macro.pop(0)
                    else:
                        macro[0] = (raw, ticks - 1)
                elif st in (0, 1, 2, 3, 27, 28) and foe_attacking \
                        and dist < 70:
                    pad = {away}                  # stand guard the poke
                elif st in (4, 15, 16):           # airborne: drift forward
                    pad = {toward}
                    if dist < 70 and air_atk == 0:
                        pad.add(ATTACKS[atk_i % 4])
                        atk_i += 1
                        air_atk = 6               # hold the press a few ticks
                    elif air_atk > 0:
                        air_atk -= 1
                elif st == 0:                     # standing
                    air_atk = 0
                    spec_cd -= 1
                    if spec_cd <= 0 and dist <= 90:
                        # QCF + X special (canonical RIGHT-facing motion)
                        macro = [({BTN_DOWN}, 3), ({BTN_DOWN, BTN_RIGHT}, 3),
                                 ({BTN_RIGHT}, 3), ({BTN_RIGHT, BTN_X}, 4)]
                        spec_cd = 240
                    elif dist <= 40:
                        pad = {ATTACKS[atk_i % 4]}
                        if atk_i % 5 == 4:
                            pad.add(BTN_DOWN)
                        atk_i += 1
                    elif dist <= 64:
                        pad = {toward, BTN_UP}    # jump-in
                    else:
                        pad = {toward}
                        if rng.random() < 0.15:
                            pad.add(BTN_UP)
                else:
                    air_atk = 0
                core.buttons[0] = pad
            else:
                core.buttons[0] = set()
                round_active = False
                fight_ticks = 0
                no_damage_ticks = 0
                last_hp2 = None

            # skip banner quickly but through real input
            if gs == 0 and total[0] % 120 < 4:
                core.buttons[0] = {BTN_START}
            elif gs == 0:
                core.buttons[0] = set()

            cidx = core.ram[C_IDX]
            if cidx != last_cidx:
                if last_cidx != -1 and cidx > last_cidx:
                    fight_no = cidx
                    hp = core.word(HP1)
                    note(f"fight {cidx + 1}/{count}: "
                         f"P1 char {core.ram[SEL1]} hp={hp} vs "
                         f"char {core.ram[SEL2]} "
                         f"(wins {core.ram[WINS1]}-{core.ram[WINS2]})")
                    if hp < 140:
                        core.put(HP1, 140)
                        note(f"  bot assist: carried HP {hp} -> 140")
                last_cidx = cidx

            if gs == 10:
                note("SURVIVOR ENDING reached (GS=10)")
                break
            if gs == 5 and saw_fight:
                note(f"run over at fight {fight_no + 1}: back at select "
                     f"(roundwin={core.ram[0x1083]})")
                attempt += 1
                if attempt > attempts:
                    note("out of attempts")
                    break
                note(f"--- retrying survivor, attempt {attempt} ---")
                saw_fight = False
                fight_no = 0
                last_cidx = -1
                last_gs = None
                gs_stuck = 0
                count = start_run()
                continue
            if gs == 6 and fight_no:
                note("unexpected return to mode menu")
                break
            if total[0] > 60 * 60 * 40:
                bug("global timeout (40 min of emulated time)")
                break

        note(f"done: {fight_no}/{count} fights cleared, "
             f"{len(anomalies)} anomalies")
    finally:
        core.close()
    return anomalies


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--msu", type=int, default=0)
    p.add_argument("--level", type=int, default=1)
    p.add_argument("--seed", type=int, default=98)
    p.add_argument("--attempts", type=int, default=8)
    a = p.parse_args()
    bad = play(a.msu, a.level, a.seed, a.attempts)
    sys.exit(1 if bad else 0)
