"""Standing proximity HitDefs, sharing the existing animation/CHR pages.

Mappings are source Statedefs, in LP/HP/LK/HK order. None means the source
has no separate close normal for that button; do not invent an extra hit.
"""
import copy
import json
import re
from pathlib import Path

STANDARD = (205, 215, 235, 245)
SOURCE = {
    'omegarugal': (201, 211, 231, 241),
    'ralf': (None, 202, 204, 206),
    'leona': (205, 225, 215, 235),
    'mature': (None, 210, None, 230),
    'vice': (None, None, None, None),
    'yuri': (200, 202, 204, 206),
    'kensou': (None, 250, 230, 270),
    'king': (200, 220, 210, 230),
    'mai': (205, 215, 225, 235),
    'chizuru': (None, None, None, None),
    'shermie': (None, 245, None, None),
    'chris': (None, 245, 225, 265),
    'mary': (201, 215, 236, 246),
    'billy': (201, 221, 211, 231),
    'lucky': (210, 250, 230, 270),
    'brian': (205, 225, 215, 235),
}
ROWS = {}


def profiles(name, cfg, moves, hitdefs, final_rows, limit_pushback,
             headers=None, statedefs=None):
    result = []
    for sid, source in zip(range(5, 9), SOURCE.get(name, STANDARD)):
        far = final_rows[sid]
        candidates = list(hitdefs.get(source, []))
        if statedefs is not None:
            controls = [c for c in statedefs.get(source, [])
                        if c.get('type', '').lower() == 'hitdef']
            base_anim = str((headers or {}).get(source, {}).get('anim', source))
            selected = []
            for ctrl, candidate in zip(controls, candidates):
                anims = {v for t in ctrl.get('triggers', [])
                         for v in re.findall(r'\banim\s*=\s*(\d+)', t, re.I)}
                if candidate.get('damage', 0) > 0 and (not anims or base_anim in anims):
                    selected.append(candidate)
            candidates = selected
        row = copy.deepcopy(candidates[0] if candidates else moves.get(source, far))
        enabled = source is not None and source in moves and row.get('damage', 0) > 0
        hits = sorted({r['active'] for r in candidates
                       if r.get('damage', 0) > 0 and r.get('active', 0) > 0})
        # Positive HitDefs on distinct elements represent contacts. Zero-damage
        # var(12) alternatives and duplicate imported controllers are discarded.
        count = max(1, min(3, len(hits))) if enabled else 1
        if not enabled:
            row = copy.deepcopy(far)
        base = moves.get(cfg['moves'].get(sid), far).get('damage', 0)
        factor = far['damage'] / base if base else 1
        for key in ('damage', 'gdamage'):
            row[key] = max(1, round(row.get(key, 0) * factor)) if row.get(key) else 0
        if count > 1:
            # Reused far art holds its active pose briefly for the extra hit.
            # The runtime suppresses intermediate pushback; the final contact
            # uses the source velocities, capped to the SNES playfield.
            row.update(fall=0, trip=0)
            row['hittime'] = max(12, row['hittime'])
        tmp = [{} for _ in range(9)]
        tmp[sid] = row
        limit_pushback(tmp)
        row = tmp[sid]
        flags = (row.get('fall', 0) | row.get('low', 0) << 1 |
                 row.get('guard', 0) << 4 | row.get('animtype', 0) << 8 |
                 row.get('trip', 0) << 11 | 0x6000)
        words = [40 if enabled else 0, count - 1, row['damage'],
                 row['hittime'], row['slidetime'], row.get('gdamage', 0),
                 row['gvx'], row['gvy'], row['avx'], row['avy'],
                 row['grvx'], row['agvx'], row['agvy'], flags,
                 row.get('p1gpause', 0) or row.get('p1pause', 0), source or 0]
        result.append({'sid': sid, 'source': source, 'enabled': enabled,
                       'contacts': count, 'words': words})
    ROWS[name] = result


def emit(out, chars):
    lines = ['; generated proximity HitDefs: 4 x 32 bytes per fighter\n',
             'CloseNormalDirectory:\n']
    for name in chars:
        if name not in ROWS:
            raise ValueError(f'missing close-normal data: {name}')
        label = 'OmegaRugal' if name == 'omegarugal' else name.capitalize()
        lines.append(f'    .dw Char{label}, CN_{name}\n')
    lines.append('    .dw 0,0\nCloseNormalData:\n')
    for name in chars:
        lines.append(f'CN_{name}:\n')
        for row in ROWS[name]:
            lines.append('    .dw ' + ','.join(f'${v & 0xffff:04X}' for v in row['words']) + '\n')
    Path(out, 'close_normals.inc').write_text(''.join(lines))
    Path(out, 'close_normals.json').write_text(json.dumps(ROWS, indent=2) + '\n')
