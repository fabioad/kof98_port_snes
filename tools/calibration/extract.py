"""Discovery, content-addressed extraction, and dynamic state cataloguing."""
import hashlib
import json
import re
from pathlib import Path
from . import mugen

VERSION = 1

# Package filenames differ from roster keys; do not infer these from display names.
CANONICAL_DEFINITIONS = {
    'athena': 'Athena-98/Athena-98.def',
    'chang': 'chang-kofa/chang-kofa.def',
    'chin': 'chin-kofa/chin-kofa.def',
    'choi': 'choi-kofa/choi-kofa.def',
    'heavyd': 'heavy-d-kofa/heavy-d-kofa.def',
    'leona': 'Leona-KOF98/98Leona.def',
    'mai': 'Mai-KOF98/K_Mai.def',
    'mary': 'bluemary-kofa/bluemary-kofa.def',
    'ralf': 'Ralf-KOF98/Ralf.def',
}


def json_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def write_if_changed(path, data):
    path = Path(path)
    if path.exists() and path.read_bytes() == data: return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_bytes(data)
    tmp.replace(path)
    return True


def alias(text):
    return re.sub(r'[^a-z0-9]', '', text.lower().replace('kof98', ''))


def discover(root, configs):
    records = []
    for path in sorted(Path(root).rglob('*')):
        if path.suffix.lower() != '.def' or '_excluded' in path.parts: continue
        d = mugen.definition(path)
        if not all(k in d['files'] for k in ('sprite', 'anim')): continue
        aliases = {alias(path.stem), alias(path.parent.name)}
        aliases.update(alias(v.strip('"')) for k, v in d['info'].items() if k in ('name', 'displayname'))
        candidates = []
        for name, cfg in configs.items():
            pinned = CANONICAL_DEFINITIONS.get(name)
            if pinned:
                if (path.resolve() == (Path(root) / pinned).resolve()
                        and Path(d['files']['sprite']).resolve() == Path(cfg['sff']).resolve()):
                    candidates.append(name)
                continue
            # Require alias AND shared asset identity; alternate DEFs with shared
            # assets aren't automatically equated to the canonical character.
            if alias(name) in aliases and Path(d['files']['sprite']).resolve() == Path(cfg['sff']).resolve():
                if alias(path.stem) == alias(name): candidates.append(name)
        d['native'] = candidates[0] if len(candidates) == 1 else None
        d['aliases'] = sorted(aliases)
        d['id'] = str(path.relative_to(root).with_suffix('')).replace('/', '__')
        records.append(d)
    # Multiple definitions claiming the same native slot are all blocked.
    for r in records:
        if r['native'] and sum(x['native'] == r['native'] for x in records) > 1:
            r['mapping_ambiguous'] = True
    for r in records:
        if r.get('mapping_ambiguous'): r['native'] = None
    return records


def dependencies(d):
    paths = {d['path'], *d['files'].values()}
    anim = Path(d['files']['anim'])
    if anim.with_suffix(anim.suffix + '.orig').exists(): paths.add(str(anim) + '.orig')
    return {p: mugen.sha(p) if Path(p).is_file() else None for p in sorted(paths)}


def extract(d, cache):
    deps = dependencies(d)
    # Parser changes invalidate cache, not only source changes.
    code = mugen.sha(__file__) + mugen.sha(mugen.__file__)
    key = hashlib.sha256(json_bytes([VERSION, code, deps])).hexdigest()
    cached = Path(cache) / (key + '.json')
    if cached.exists(): return json.loads(cached.read_text()), True
    paths = [p for k, p in d['files'].items()
             if (k in ('cns', 'cmd', 'stcommon') or re.fullmatch(r'st\d*', k)) and Path(p).is_file()]
    states, duplicates, constants, commands = mugen.states(paths)
    animfile = Path(d['files']['anim'])
    original = Path(str(animfile) + '.orig')
    source = original if original.exists() else animfile
    animations = mugen.air(source) if source.exists() else {}
    issues = [{'kind': 'missing_file', 'file': p} for p, h in deps.items() if h is None]
    moves = []
    for state in states.values():
        header = mugen.values(state['header'])
        ctrls = state['controllers']
        hitdefs = [c for c in ctrls if c['type'] in ('hitdef', 'projectile', 'reversaldef')]
        attrs = [mugen.values(c).get('attr', '') for c in hitdefs]
        classification = 'action'
        if hitdefs: classification = 'attack'
        if any(re.search(r',\s*[nsh]t', a, re.I) for a in attrs): classification = 'throw'
        elif any(re.search(r',\s*h[apt]', a, re.I) for a in attrs): classification = 'super'
        elif any(re.search(r',\s*s[apt]', a, re.I) for a in attrs): classification = 'special'
        elif any(re.search(r',\s*n[apt]', a, re.I) for a in attrs): classification = 'normal'
        if any(c['type'] == 'projectile' for c in ctrls): classification = 'projectile'
        edges = []
        for c in ctrls:
            if c['type'] in ('changestate', 'selfstate', 'helper', 'targetstate'):
                f = next((f for f in c['fields'] if f['key'] in ('value', 'stateno')), None)
                if f: edges.append({'type': c['type'], **mugen.parameter(f)})
        anim = header.get('anim', '')
        action = animations.get(anim)
        moves.append({'state': state['id'], 'kind': classification, 'animation_id': anim,
                      'animation': mugen.timeline(action) if action else None,
                      'source': state['header']['source'], 'dependencies': edges,
                      'controllers': ctrls, 'header': state['header'],
                      'unresolved_parameters': sum(p['value'] is None for c in ctrls for p in c['parameters'])})
    binaries = {}
    for k in ('sprite', 'sound'):
        p = d['files'].get(k)
        if p and Path(p).exists():
            try: binaries[k] = mugen.binary_metadata(p, k)
            except (ValueError, IndexError, OSError, __import__('struct').error) as e:
                issues.append({'kind': 'binary_error', 'file': p, 'reason': str(e)})
    result = {'schema': VERSION, 'definition': d, 'hashes': deps, 'states': states,
              'moves': moves, 'animations': animations, 'animation_source': str(source),
              'constants': constants, 'commands': commands, 'duplicates': duplicates,
              'binaries': binaries, 'issues': issues,
              'coverage': {'controller_execution': 'subset only; see validator',
                           'rom_gameplay': False, 'full_mugen_vm': False}}
    write_if_changed(cached, json_bytes(result))
    return result, False
