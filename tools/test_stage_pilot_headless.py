#!/usr/bin/env python3
"""Validate real China/Bazar pose tiles and atomic map commits in Snes9x."""
import argparse
import ctypes as C
import json
from pathlib import Path
import re
import tempfile
from PIL import Image
from calibration.headless import Core
from capture_pair_headless import tap, wait, save_frame
from test_super_stage_vram_headless import stage0_rom, qcf, CORE, ROOT
from verify_stage_export import decode_tile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['china', 'bazar'], default='china')
    args = parser.parse_args()
    stage = 1 if args.stage == 'china' else 4
    name = 'KOF98-ChinaStage' if stage == 1 else 'KOF98-Mid.EastStage'
    out = ROOT / ('build/stage-pilot' if stage == 1 else 'build/stage-bazar')
    out.mkdir(exist_ok=True)
    gen = ROOT / 'build/gen_fight'
    art = ROOT / 'assets/stages/stages_png_snes'
    text = (gen / 'stage_anim.inc').read_text()
    anim = (gen / 'stage_anim.chr').read_bytes()
    assert len(anim) <= 160 * 32
    spec = json.loads((art / 'animations/stage_animations.json').read_text())
    clips = []
    for clip in spec['clips']:
        if clip['stage'] != name:
            continue
        target = clip['target']
        files = target['resident_patch_files']
        nposes = len(files)
        block = text.split('; '+clip['id']+'\n', 1)[1].split('StgAnim', 1)[0]
        words = [int(v, 16) for v in re.findall(r'\$([0-9A-F]{4})', block)]
        entries = [words[i:i+1+nposes] for i in range(0, len(words), 1+nposes)]
        assert len(entries) == target['changed_tiles_per_pose_cap']
        expected = [tuple(e[p+1] for e in entries) for p in range(nposes)]
        rx,ry,rw,rh = target['target_region_xywh']
        for pose, filename in enumerate(files):
            patch = Image.open(art / filename)
            raw = patch.tobytes()
            for cell, word in zip(entries, expected[pose]):
                mi = cell[0]
                tx = (mi // 1024) * 32 + mi % 32
                ty = (mi % 1024) // 32 - (4 if stage == 1 else 0)
                tile = (word & 1023) - 704
                decoded = decode_tile(anim[tile*32:(tile+1)*32], 0)
                for y in range(8):
                    for x in range(8):
                        idx = (((word >> 10) & 7) - 2) * 15 + decoded[y][x] - 1
                        assert idx == raw[(ty*8-ry+y)*rw + tx*8-rx+x]
        clips.append((clip['id'], entries, expected, set()))
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        core = Core(CORE, stage0_rom(Path(tmp), stage=stage))
        try:
            core.capture_video = True
            vram = (C.c_ubyte * 65536).from_address(core.lib.retro_get_memory_data(3))
            for _ in range(80):
                if core.ram[0x1020] == 6:
                    break
                tap(core, 3)
            wait(core, lambda: core.ram[0x1020] == 6, 'menu')
            core.ram[0xF070] = 1
            for _ in range(30):
                tap(core, 3)
                core.step(20)
                if core.ram[0x1020] == 5:
                    break
            wait(core, lambda: core.ram[0x1020] == 5, 'select')
            core.ram[0x1085], core.ram[0x1086] = 0, 1
            core.ram[0x108E] = core.ram[0x108F] = 1
            core.ram[0x1090] = core.ram[0x1091] = 0
            core.step()
            wait(core, lambda: core.ram[0x1020] == 1, 'fight')
            assert core.ram[0x1087] == stage
            core.put(0x4000, 70 << 8)
            core.put(0x4040, 150 << 8)
            static = (gen / f'stages/stg{stage}.chr').read_bytes()
            base_map = bytes(vram[0x8000:0x9000])
            previous_map = base_map
            peak_cells = 0
            allowed = {e[0] for _,entries,_,_ in clips for e in entries}
            super_states = set()
            for tick in range(1500):
                if tick == 300:
                    core.put(0x4030, 1000)
                    qcf(core)
                    core.buttons[0] = {9}
                elif tick == 303:
                    core.buttons[0] = set()
                elif tick == 600:
                    core.buttons[0] = {7}
                    core.buttons[1] = {7}
                elif tick == 800:
                    core.buttons[0] = {6}
                    core.buttons[1] = {6}
                elif tick == 1000:
                    core.buttons = [set(), set()]
                core.step()
                if 300 <= tick < 600:
                    super_states.add(core.ram[0x4008])
                assert bytes(vram[:len(static)]) == static, f'static VRAM tick {tick}'
                assert bytes(vram[0x5800:0x5800+len(anim)]) == anim
                current = bytes(vram[0x8000:0x9000])
                changed = {i//2 for i in range(0,4096,2) if current[i:i+2] != base_map[i:i+2]}
                assert changed <= allowed, f'unexpected map cells: {changed-allowed}'
                if tick != 300:  # qcf advances several frames between samples
                    delta = sum(current[i:i+2] != previous_map[i:i+2] for i in range(0,4096,2))
                    peak_cells = max(peak_cells, delta)
                    assert delta <= 16, f'overlapping pose commits: {delta}'
                previous_map = current
                for clip_id, entries, expected, seen in clips:
                    state = tuple(current[e[0]*2] | current[e[0]*2+1] << 8 for e in entries)
                    if state in expected:
                        pose = expected.index(state)
                        if pose not in seen:
                            save_frame(core.last_frame, out / f'{clip_id}-pose-{pose}-in-game.png')
                        seen.add(pose)
                    else:
                        assert not seen, 'partial/non-atomic pose: '+clip_id
            for clip_id, _, expected, seen in clips:
                assert seen == set(range(len(expected))), (clip_id, seen)
            assert any(s >= 30 for s in super_states), super_states
            report = {'ticks': 1500, 'poses_seen': {c:sorted(seen) for c,_,_,seen in clips}, 'static_tiles': len(static)//32,
                      'shared_dynamic_tiles': len(anim)//32, 'changed_map_cells': len(allowed),
                      'peak_cells_per_sampled_frame': peak_cells,
                      'super_states': sorted(super_states), 'vram_checks': 'PASS'}
            (out / 'validation.json').write_text(json.dumps(report, indent=2)+'\n')
            print(report)
        finally:
            core.close()


if __name__ == '__main__':
    main()
