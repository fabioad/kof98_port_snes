"""Deterministic subset model and native-table checks (not a 65816 emulator)."""
import re
from dataclasses import dataclass, field
from . import mugen


def box_world(box, x=0, y=0, facing=1, scale=1):
    x1, y1, x2, y2 = [round(v * scale) for v in box]
    a, b = x + facing * x1, x + facing * x2
    return [min(a, b), y + y1, max(a, b), y + y2]


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


@dataclass
class Fighter:
    x: int = 0  # 8.8 fixed point
    y: int = 0
    vx: int = 0
    vy: int = 0
    hp: int = 200
    power: int = 0
    stun: int = 0
    pause: int = 0
    ctrl: int = 0
    state: int = 0
    time: int = 0
    facing: int = 1
    variables: dict = field(default_factory=dict)

    def advance(self, gravity=0):
        if self.pause:
            self.pause -= 1
            return
        self.x += self.vx; self.y += self.vy; self.vy += gravity
        self.stun = max(0, self.stun - 1)
        self.time += 1


def contact(attacker, victim, hit, blocked=False):
    """Native scalar contract; no claims about MUGEN combo/helper semantics."""
    key = 'gdamage' if blocked else 'damage'
    victim.hp = max(1 if blocked else 0, victim.hp - hit[key])
    victim.stun = hit['hittime']
    victim.vx = attacker.facing * hit['grvx' if blocked else 'gvx']
    victim.vy = 0 if blocked else hit.get('gvy', 0)
    attacker.pause = hit.get('p1gpause' if blocked else 'p1pause', 0)
    victim.pause = hit.get('p2pause', 0)


def command_matches(events, sequence, window, now, buffer=1):
    """Exact symbolic input subset; release/charge syntax explicitly refused."""
    if any(any(c in s for c in '~/$>') for s in sequence):
        raise mugen.Unsupported('charge/release/held command requires native matcher')
    if not sequence: return False
    candidates = [(i, t) for i, (t, s) in enumerate(events) if s == sequence[-1] and 0 <= now - t < buffer]
    for end, last in candidates:
        pos, first = len(sequence) - 2, last
        for t, s in reversed(events[:end]):
            if last - t > window: break
            if pos >= 0 and s == sequence[pos]: pos -= 1; first = t
        if pos < 0 and last - first <= window: return True
    return False


def execute(controller, fighter, context=None):
    """Run a controller only when all relevant expressions are resolvable.

    Complex collision controllers stay in IR. Unknowns stop the caller; a
    skipped controller must never be interpreted as a successful simulation.
    """
    ctx = {'time': fighter.time, 'power': fighter.power, 'ctrl': fighter.ctrl,
           'stateno': fighter.state, **fighter.variables, **(context or {})}
    if not mugen.triggers(controller, ctx): return False
    fields = mugen.values(controller)
    def val(key): return mugen.evaluate(fields[key], ctx)
    kind = controller['type']
    if kind in ('velset', 'veladd', 'posadd'):
        changes = {axis: round(val(axis) * 256) for axis in ('x', 'y') if axis in fields}
        for axis, value in changes.items():
            key = axis if kind == 'posadd' else 'v' + axis
            setattr(fighter, key, value if kind == 'velset' else getattr(fighter, key) + value)
    elif kind in ('varset', 'varadd'):
        writes = {k: val(k) for k in fields if re.fullmatch(r'f?var\(\d+\)', k)}
        if not writes and 'v' in fields:
            writes[f'var({int(val("v"))})'] = val('value')
        if not writes: raise mugen.Unsupported('unsupported variable write')
        for k, v in writes.items():
            if kind == 'varadd' and k not in fighter.variables: raise mugen.Unsupported('unknown variable')
            fighter.variables[k] = v if kind == 'varset' else fighter.variables[k] + v
    elif kind in ('changestate', 'selfstate'):
        target = int(val('value'))
        ctrl = int(val('ctrl')) if 'ctrl' in fields else fighter.ctrl
        fighter.state, fighter.time, fighter.ctrl = target, 0, ctrl
    elif kind == 'ctrlset': fighter.ctrl = int(val('value'))
    elif kind == 'poweradd': fighter.power = max(0, fighter.power + int(val('value')))
    elif kind == 'powerset': fighter.power = max(0, int(val('value')))
    elif kind == 'null': pass
    else: raise mugen.Unsupported(f'controller execution not implemented: {kind}')
    return True


def tables(path):
    result, label = {}, None
    for raw in path.read_text().splitlines():
        line = raw.split(';', 1)[0].strip()
        m = re.fullmatch(r'(\w+):', line)
        if m: label = m[1]; result[label] = []; continue
        m = re.fullmatch(r'\.d([wb])\s+(.+)', line, re.I)
        if m and label:
            try: nums = [int(v.strip()[1:], 16) if v.strip().startswith('$') else int(v.strip())
                         for v in m[2].split(',')]
            except ValueError: continue
            result[label].extend(nums)
    return result


def validate_tables(path, name, cfg, expected):
    data, checked = tables(path), 0
    fields = {'damage': ('DamageTab', 1, 0), 'gdamage': ('GDmgTab', 1, 0),
              'hittime': ('HitTimeTab', 1, 0), 'slidetime': ('SlideTab', 1, 0),
              'gvx': ('HitVelTab', 4, 0), 'gvy': ('HitVelTab', 4, 1),
              'avx': ('HitVelTab', 4, 2), 'avy': ('HitVelTab', 4, 3),
              'grvx': ('GVelTab', 3, 0), 'agvx': ('GVelTab', 3, 1), 'agvy': ('GVelTab', 3, 2), 'p2pause': ('TargetTab', 4, 1)}
    for sid, st in cfg['moves'].items():
        if st not in expected or sid in cfg.get('slice_hits', {}): continue
        for key, (label, stride, offset) in fields.items():
            got = data[name + label][sid * stride + offset]
            want = expected[st][key] & 0xffff
            if got != want: raise ValueError(f'{name} sid={sid} {key}: emitted {got}, expected {want}')
            checked += 1
    return checked
