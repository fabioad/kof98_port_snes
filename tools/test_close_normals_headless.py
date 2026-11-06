#!/usr/bin/env python3
"""Exercise proximity selection and real contacts in the linked SNES ROM."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight

BUTTONS = (1, 9, 0, 8)
PROFILE = 0x5260
F_STATE = 0x4008


def press_until(core, button, want, limit=40):
    """Hold the button through CHR staging until the normal enters."""
    core.buttons[0] = {button}
    for _ in range(limit):
        core.step()
        if core.ram[F_STATE] == want:
            break
    core.buttons[0] = set()
    return core.ram[F_STATE]


def main():
    data = json.loads((ROOT / 'build/gen_fight/close_normals.json').read_text())
    c = Core('/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so', ROOT/'kof98-snes.sfc')
    try:
        select = boot_select(c)
        checked = 0
        for name, rows in data.items():
            enter_fight(c, select, name, 'kyo')
            c.ram[0x1090] = c.ram[0x1091] = 0
            c.step(25)
            base = c.save()
            for close in (False, True):
                for i, row in enumerate(rows):
                    c.load(base)
                    c.put(0x4000, 96 << 8)
                    c.put(0x4040, (124 if close else 180) << 8)
                    c.step(4)
                    assert press_until(c, BUTTONS[i], i + 5) == i + 5, (
                        name, close, i, c.ram[F_STATE])
                    assert bool(c.word(PROFILE)) == (close and row['enabled']), (
                        name, close, i, hex(c.word(PROFILE)))
                    for _ in range(240):
                        c.step()
                        if not 5 <= c.ram[F_STATE] <= 8:
                            # One extra tick: TickFighter clears the profile
                            # on the first tick after the normal's state.
                            c.step()
                            break
                    assert not 5 <= c.ram[F_STATE] <= 8, (
                        name, 'normal did not recover', i, close)
                    assert c.word(PROFILE) == 0, (
                        name, 'stale proximity profile', i, close)
                    checked += 1
            print(f'PASS selection {name}', flush=True)
        # The specific requested case: one input, two distinct HP deductions.
        for side in (0, 1):
            enter_fight(c, select, 'terry' if side==0 else 'kyo', 'kyo' if side==0 else 'terry')
            c.ram[0x1090] = c.ram[0x1091] = 0
            c.step(25)
            for close in (False, True):
                c.put(0x4000, 100 << 8)
                c.put(0x4040, (128 if close else 150) << 8)
                c.put(0x4010, 200);c.put(0x4050, 200)
                c.step(4)
                c.buttons[side] = {9}; c.step(); c.buttons[side] = set()
                victim = 0x4050 if side == 0 else 0x4010
                victim_x = 0x4040 if side == 0 else 0x4000
                hp = c.word(victim); px = c.word(victim_x)
                drops, moves = [], []
                for t in range(110):
                    c.step()
                    now = c.word(victim); x = c.word(victim_x)
                    if now < hp:
                        drops.append(hp - now)
                        moves.append((x - px) / 256)
                    hp, px = now, x
                assert len(drops) == (2 if close else 1), (side,close,drops)
                if close:
                    # Intermediate contact keeps the victim in place; the
                    # last contact owns the profile pushback.
                    assert abs(moves[0]) < 0.1, (side, 'early pushback', moves)
                    assert abs(moves[-1]) > 0.5, (
                        side, 'missing final pushback', moves)
                print(f'PASS Terry P{side+1} {"close" if close else "far"}: '
                      f'{drops}, moves {moves}', flush=True)
        print(f'PASS {checked} proximity selections; Terry two-hit HP both sides')
    finally:
        c.close()

if __name__ == '__main__':
    main()
