#!/usr/bin/env python3
"""Exercise real menu inputs and verify all four select modes stay live."""
import argparse
import json
import re
import time
from pathlib import Path

import test_fight_remote as t


def menu_address(name):
    source = (t.ROOT / 'src/engine/menucore.asm').read_text()
    match = re.search(r'^\.DEFINE\s+' + re.escape(name) +
                      r'\s+\$([0-9A-Fa-f]+)\b', source, re.M)
    if not match:
        raise ValueError('missing direct WRAM definition: ' + name)
    return int(match.group(1), 16)


def press(ra, name):
    ra.button(0, name, True)
    time.sleep(0.15)
    ra.button(0, name, False)
    time.sleep(0.15)


def enter_mode(ra, item):
    deadline = time.monotonic() + 60
    while ra.read_ram(0x1020, 1)[0] != 6:
        if time.monotonic() > deadline:
            raise AssertionError('mode menu not reached')
        press(ra, 'START')
    for _ in range(5):
        if ra.read_ram(menu_address('M_ITEM'), 1)[0] == item:
            break
        press(ra, 'DOWN')
    actual_item = ra.read_ram(menu_address('M_ITEM'), 1)[0]
    if actual_item != item or ra.read_ram(0x1020, 1)[0] != 6:
        raise AssertionError(f'mode menu setup failed: item={actual_item}')
    press(ra, 'START')
    t.wait_for(ra, lambda s: s['gamestate'] == 5, timeout=15)
    mode = ra.read_ram(menu_address('G_MODE'), 1)[0]
    if mode != (1, 0, 2, 3)[item]:
        raise AssertionError(f'wrong game mode: item={item} mode={mode}')
    return mode


def run_mode(item, repeat):
    ra = t.RetroArch()
    try:
        ra.launch('retroarch', t.CORE)
        ra.wait_ready()
        mode = enter_mode(ra, item)
        frames = []
        for _ in range(5):
            frames.append(ra.read_ram(0x1024, 1)[0])
            time.sleep(0.25)
        if len(set(frames)) < 2 or ra.read_ram(0x1020, 1)[0] != 5:
            raise AssertionError(f'select stopped advancing: {frames}')
        return {'item': item, 'mode': mode, 'repeat': repeat,
                'frames': frames, 'status': 'passed'}
    finally:
        ra.close()


def run_held_start():
    ra = t.RetroArch()
    try:
        ra.launch('retroarch', t.CORE)
        ra.wait_ready()
        deadline = time.monotonic() + 60
        while ra.read_ram(0x1020, 1)[0] != 0:
            if time.monotonic() > deadline:
                raise AssertionError('title not reached')
            press(ra, 'START')
        ra.button(0, 'START', False)
        t.wait_for(ra, lambda s: s['gamestate'] == 0
                   and s['p1']['joy'] == 0, timeout=5)
        time.sleep(0.1)
        ra.button(0, 'START', True)
        time.sleep(1)
        ra.button(0, 'START', False)
        t.wait_for(ra, lambda s: s['gamestate'] == 6, timeout=10)
        time.sleep(0.3)
        if ra.read_ram(0x1020, 1)[0] != 6:
            raise AssertionError('held START confirmed more than one screen')
        return {'case': 'held_start_title_to_menu', 'status': 'passed'}
    finally:
        ra.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeat', type=int, default=1)
    parser.add_argument('--held-start', action='store_true')
    parser.add_argument('--output', type=Path,
                        default=t.ROOT / 'build/calibration/menu-modes.json')
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error('--repeat must be positive')
    results = []
    for repeat in range(args.repeat):
        for item in range(4):
            try:
                result = run_mode(item, repeat)
            except Exception as exc:
                result = {'item': item, 'repeat': repeat,
                          'status': 'failed', 'error': str(exc)}
            results.append(result)
            print(json.dumps(result), flush=True)
    if args.held_start:
        try:
            result = run_held_start()
        except Exception as exc:
            result = {'case': 'held_start_title_to_menu',
                      'status': 'failed', 'error': str(exc)}
        results.append(result)
        print(json.dumps(result), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + '\n')
    return int(any(r['status'] != 'passed' for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
