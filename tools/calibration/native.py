"""Adapter to the existing build_fight table ABI; no new engine/state IDs.

Generated profiles only override representable, independently resolved fields.
They retain an expected base value and full input hashes: manual edits or stale
references fail the build instead of silently applying an obsolete correction.
"""
import json
import re
from pathlib import Path
from . import mugen
from .extract import json_bytes

PROFILE_DIR = 'assets/calibration'
# Native key, source parameter, tuple component, conversion, range.
FIELDS = [
    ('fall', 'fall', 0, 'integer', 0, 1),
    ('damage', 'damage', 0, 'damage', 0, 65535),
    ('gdamage', 'damage', 1, 'damage', 0, 65535),
    ('hittime', 'ground.hittime', 0, 'integer', 0, 65535),
    ('slidetime', 'ground.slidetime', 0, 'integer', 0, 65535),
    ('gvx', 'ground.velocity', 0, 'magnitude', 0, 32767),
    ('gvy', 'ground.velocity', 1, 'fixed', -32768, 32767),
    ('avx', 'air.velocity', 0, 'magnitude', 0, 32767),
    ('avy', 'air.velocity', 1, 'fixed', -32768, 32767),
    ('grvx', 'guard.velocity', 0, 'magnitude', 0, 32767),
    ('agvx', 'airguard.velocity', 0, 'magnitude', 0, 32767),
    ('agvy', 'airguard.velocity', 1, 'fixed', -32768, 32767),
    ('p2pause', 'pausetime', 1, 'integer', 0, 255),
    ('p1pause', 'pausetime', 0, 'integer', 0, 60),
    ('p1gpause', 'guard.pausetime', 0, 'integer', 0, 60),
]


def runtime_supported(key, move):
    # The engine reads TargetTab's victim pause only after a p2stateno
    # redirect. Ordinary hits go through HO_normalhit and never read it.
    return key != 'p2pause' or move.get('p2state', 0xFF) != 0xFF


def convert(v, kind, cfg):
    if not isinstance(v, (int, float)): raise mugen.Unsupported('not numeric')
    if kind == 'integer':
        if int(v) != v: raise mugen.Unsupported('fractional tick count')
        return int(v)
    if kind == 'damage': return round(v * cfg.get('damage_scale', 1))
    if kind == 'magnitude': v = abs(v)
    return round(v / cfg.get('coord_scale', 1) * 256)


def signature(c):
    return [(p['key'], re.sub(r'\s+', '', p['expression'].lower())) for p in c['fields']
            if p['key'].startswith('trigger') or p['key'] in ('attr', 'type')]


def real_hits(state):
    return [c for c in state.get('controllers', []) if c['type'] == 'hitdef'
            and mugen.values(c).get('attr', '').strip()]


def config_hash(cfg):
    import hashlib
    # A projectile FX alias only redirects the descriptor to another
    # character's compiled effect table; it changes no calibrated native
    # value, so it must not invalidate an existing profile.  The same holds
    # for the physical-pad button masks: they change input routing, never a
    # damage/hit-timing value read from the CNS.
    hashed = {k: v for k, v in cfg.items()
              if k not in ('projfx_alias', 'buttons')}
    return hashlib.sha256(json_bytes(hashed)).hexdigest()


def read_profile(root, name, cfg):
    path = Path(root) / PROFILE_DIR / (name + '.json')
    if not path.exists(): return None
    p = json.loads(path.read_text())
    if p.get('schema') != 1 or p.get('config_hash') != config_hash(cfg):
        raise ValueError(f'{name}: stale calibration configuration; run tools/calibrate.py again')
    for f, digest in p['inputs'].items():
        fpath = Path(root) / f
        if not fpath.exists() or mugen.sha(fpath) != digest:
            raise ValueError(f'{name}: stale calibration input {f}; recalibrate before build')
    return p


def apply_profile(root, name, cfg, moves, air):
    profile = read_profile(root, name, cfg)
    if not profile: return
    for correction in profile['corrections']:
        if correction['confidence'] != 'ALTA': raise ValueError('unsafe calibration profile')
        if correction['kind'] == 'combat':
            state, key = correction['state'], correction['key']
            if key not in {f[0] for f in FIELDS}: raise ValueError('unknown native field')
            if moves[state][key] != correction['before']: raise ValueError('native value changed')
            moves[state][key] = correction['after']
        elif correction['kind'] == 'animation':
            anum, index = correction['animation'], correction['element']
            frames, loop = air[anum]
            if frames[index][4] != correction['before']: raise ValueError('animation changed')
            frame = list(frames[index]); frame[4] = correction['after']
            frames[index] = tuple(frame)
        else: raise ValueError('unknown correction kind')


def compare(root, ir, name, cfg, builder, protection=None):
    protection = protection or {}
    native_path = Path(root) / cfg['cns']
    native_states, duplicates, _, _ = mugen.states([native_path])
    base = builder.parse_cns(str(native_path), cfg.get('coord_scale', 1), cfg.get('damage_scale', 1))[0]
    previous_path = Path(root) / PROFILE_DIR / (name + '.json')
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else None
    # Preserve only explicitly locked previous entries, otherwise recompute.
    locked = set(protection.get('states', {}).get(name, []))
    differences, corrections, matched = [], [], set()
    bad_states = {str(x['state']) for x in ir['duplicates'] + duplicates}
    for sid, st in cfg['moves'].items():
        ref, dest = ir['states'].get(str(st)), native_states.get(str(st))
        if not ref or not dest:
            differences.append({'state': st, 'sid': sid, 'status': 'unmatched_state'}); continue
        matched.add(st)
        hits, native_hits = real_hits(ref), real_hits(dest)
        if not hits: continue
        eligible = (str(st) not in bad_states and len(hits) == len(native_hits) == 1
                    and signature(hits[0]) == signature(native_hits[0]) and st in base
                    and sid not in cfg.get('slices', {})
                    and sid not in cfg.get('slice_hits', {})
                    and sid not in cfg.get('hitdef_by_sid', {}))
        if not eligible:
            differences.append({'state': st, 'sid': sid, 'status': 'ambiguous_hitdef',
                                'reference_hitdefs': len(hits), 'native_hitdefs': len(native_hits)})
            continue
        hit = hits[0]
        params = {p['key']: p for p in hit['fields']}
        for key, prop, idx, conv, lo, hi in FIELDS:
            record = {'state': st, 'sid': sid, 'property': prop, 'key': key,
                      'before': base[st].get(key), 'confidence': 'BAIXA'}
            if not runtime_supported(key, base[st]):
                differences.append({**record, 'status': 'engine_gap',
                                    'reason': 'victim pausetime is not read for ordinary hits'})
                continue
            if prop not in params:
                if key != 'fall':
                    differences.append({**record, 'status': 'missing_reference'}); continue
                # HitDef fall defaults to 0 in MUGEN. Keeping that default
                # explicit lets calibration detect missing knockdowns.
                ground_type = params.get('ground.type', {}).get('expression', '')
                default_fall = int(ground_type.strip().lower() == 'trip')
                expression = f'{default_fall} (HitDef default)'
            else:
                p = params[prop]
                expression = p['expression']
                record.update(source=p['source'], expression=expression,
                              controller=hit['index'])
            try:
                parts = mugen.split_values(expression.split(' (HitDef default)')[0])
                if idx >= len(parts): raise mugen.Unsupported('component absent; no inferred default')
                value = mugen.evaluate(parts[idx])
                new = convert(value, conv, cfg)
                if not lo <= new <= hi: raise mugen.Unsupported('native range exceeded')
            except mugen.Unsupported as e:
                differences.append({**record, 'status': 'unsupported', 'reason': str(e)}); continue
            # Only value confidence is high; this does NOT assert full trigger equivalence.
            record.update(runtime_scope=('custom_victim_only' if key == 'p2pause' else 'native_scalar'), after=new, confidence='ALTA', status='equal' if new == record['before'] else 'correctable')
            if st in locked or name in protection.get('characters', []): record['status'] = 'protected'
            differences.append(record)
            if record['status'] == 'correctable':
                corrections.append({**record, 'kind': 'combat'})
        # Fields the current ABI cannot represent independently are explicit gaps.
        for prop in ('guard.hittime', 'air.hittime', 'getpower', 'givepower', 'priority', 'yaccel'):
            if prop in params:
                differences.append({'state': st, 'sid': sid, 'property': prop,
                                    'status': 'engine_gap', **params[prop]})
    # Exact element correspondence only: do not undo sprite trimming or slices.
    current_air = mugen.air(Path(root) / cfg['air'])
    for anum in sorted(set(cfg['anims'].values())):
        ref, dest = ir['animations'].get(str(anum)), current_air.get(str(anum))
        if not ref or not dest: continue
        uses = [sid for sid, a in cfg['anims'].items() if a == anum]
        def identity(frame): return {k: v for k, v in frame.items() if k not in ('ticks', 'source')}
        safe = (not ref['unsupported'] and not dest['unsupported'] and ref['loopstart'] == dest['loopstart']
                and len(ref['frames']) == len(dest['frames'])
                and all(identity(a) == identity(b) for a, b in zip(ref['frames'], dest['frames']))
                and not any(s in cfg.get('slices', {}) or s in (90, 91, 92) for s in uses))
        if not safe:
            differences.append({'animation': anum, 'status': 'animation_mapping_requires_review',
                                'reference': mugen.timeline(ref), 'native': mugen.timeline(dest)})
            continue
        for i, (a, b) in enumerate(zip(ref['frames'], dest['frames'])):
            if a['ticks'] == b['ticks']: continue
            rec = {'kind': 'animation', 'animation': anum, 'element': i, 'before': b['ticks'],
                   'after': a['ticks'], 'source': a['source'], 'confidence': 'ALTA', 'status': 'correctable'}
            if not (0 < a['ticks'] < 255 and 0 < b['ticks'] < 255): rec['status'] = 'engine_gap'
            if name in protection.get('characters', []) or any(cfg['moves'].get(s) in locked for s in uses):
                rec['status'] = 'protected'
            differences.append(rec)
            if rec['status'] == 'correctable': corrections.append(rec)
    # Deduplicate states mapped to multiple native slots.
    unique = {}
    for c in corrections:
        key = (c['kind'], c.get('state'), c.get('key'), c.get('animation'), c.get('element'))
        unique[key] = c
    corrections = list(unique.values())
    if previous:
        for c in previous['corrections']:
            if name in protection.get('characters', []) or c.get('state') in locked:
                corrections.append(c)
    paths = {p for p, h in ir['hashes'].items() if h is not None}
    paths.update(str((Path(root) / cfg[k]).resolve()) for k in ('cns', 'cmd', 'air'))
    inputs = {str(Path(p).resolve().relative_to(root)) if Path(p).resolve().is_relative_to(root) else p: mugen.sha(p)
              for p in sorted(paths)}
    profile = {'schema': 1, 'character': name, 'definition': ir['definition']['path'],
               'config_hash': config_hash(cfg), 'inputs': inputs, 'corrections': corrections}
    return {'native': name, 'matched_states': sorted(matched),
            'unmatched_states': [m['state'] for m in ir['moves'] if m['state'] not in matched],
            'differences': differences, 'profile': profile}
