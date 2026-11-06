#!/usr/bin/env python3
"""Daimon's FF/BB inputs, movement and recovery on both pads and facings."""
import json
from pathlib import Path

from calibration.headless import Core
from capture_pair_headless import save_frame, wait
from test_midfight_join_headless import enter_mode

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/daimon_dash'


def run():
    OUT.mkdir(exist_ok=True)
    c = Core('/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so',
             ROOT / 'kof98-snes.sfc')
    c.capture_video = True
    results = []
    try:
        enter_mode(c, 5)
        c.ram[0x1085] = c.ram[0x1086] = 13  # Daimon vs Daimon
        c.ram[0x108E] = c.ram[0x108F] = 1
        c.ram[0x1090] = c.ram[0x1091] = 0
        wait(c, lambda: c.ram[0x1020] == 1, 'practice ready', 6000)
        c.step(50)
        base = c.save()
        for side in (0, 1):
            for facing in (1, -1):
                for move, state in (('forward', 45), ('back', 46)):
                    c.load(base)
                    c.buttons = [set(), set()]
                    fp, opponent = 0x4000 + side * 0x40, 0x4000 + (1-side) * 0x40
                    c.put(fp, (100 if facing == 1 else 210) * 256)
                    c.put(opponent, (210 if facing == 1 else 100) * 256)
                    c.step(12)
                    assert c.word(fp + 14) == (1 if facing == 1 else 0xFFFF)
                    start = c.word(fp)
                    direction = facing if move == 'forward' else -facing
                    key = 7 if direction == 1 else 6
                    trace = []
                    shot = False
                    for frame in range(180):
                        # Release between direction taps; retain the second
                        # forward tap long enough to exercise the run loop.
                        c.buttons[side] = {key} if frame < 6 or 10 <= frame < 70 else set()
                        c.step()
                        row = dict(frame=frame, state=c.ram[fp+8], elem=c.ram[fp+10],
                                   x=c.word(fp), y=c.word(fp+2))
                        trace.append(row)
                        if row['state'] == state and not shot and frame > 25:
                            save_frame(c.last_frame, OUT / f'p{side+1}_{facing}_{move}.png')
                            shot = True
                    active = [r for r in trace if r['state'] == state]
                    label = f'P{side+1} facing {facing:+} {move}'
                    assert active, f'{label}: double tap never entered state {state}'
                    travel = max(direction * (r['x'] - start) for r in trace)
                    assert travel > 20 * 256, f'{label}: no dash displacement'
                    if move == 'forward':
                        assert len({r['elem'] for r in active}) >= 3, f'{label}: animation frozen'
                        assert all(r['y'] == 0 for r in active), f'{label}: run left the ground'
                    else:
                        assert max(r['y'] for r in trace) > 5*256, f'{label}: no back hop'
                    assert trace[-1]['state'] == 0 and trace[-1]['y'] == 0, f'{label}: no recovery'
                    assert c.word(fp+4) == c.word(fp+6) == 0, f'{label}: velocity persists after recovery'
                    results.append(dict(side=side, facing=facing, move=move, trace=trace))
                    print(f'PASS {label}: movement, animation, recovery', flush=True)
    finally:
        c.close()
    (OUT / 'regression.json').write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    run()
