"""Lossless-enough source IR and fail-closed expression evaluation.

No eval(), implicit variable defaults, or numeric-prefix guessing. Controller
parameters and repeated trigger keys retain source locations even if unresolved.
"""
import ast
import hashlib
import math
import re
import struct
from pathlib import Path


class Unsupported(ValueError):
    pass


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    data = Path(path).read_bytes()
    for encoding in ('utf-8-sig', 'cp932', 'latin1'):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass


def uncomment(line):
    # Semicolons inside quoted strings are not comments.
    return re.split(r';(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', line, 1)[0].strip()


def sections(path):
    result = []
    current = None
    for lineno, raw in enumerate(read(path).splitlines(), 1):
        line = uncomment(raw)
        m = re.fullmatch(r'\[([^]]+)\]', line)
        if m:
            current = {'name': m[1], 'source': {'file': str(path), 'line': lineno},
                       'fields': [], 'raw': []}
            result.append(current)
        elif current and line:
            current['raw'].append({'text': line, 'line': lineno})
            if '=' in line:
                key, value = line.split('=', 1)
                current['fields'].append({'key': key.strip().lower(), 'expression': value.strip(),
                                          'source': {'file': str(path), 'line': lineno}})
    return result


def values(section):
    return {p['key']: p['expression'] for p in section['fields']}


def split_values(expr):
    parts, start, depth, quoted = [], 0, 0, False
    for i, c in enumerate(expr):
        if c == '"':
            quoted = not quoted
        if quoted:
            continue
        if c in '([':
            depth += 1
        elif c in ')]':
            depth -= 1
        elif c == ',' and depth == 0:
            parts.append(expr[start:i].strip())
            start = i + 1
    parts.append(expr[start:].strip())
    return parts


def evaluate(expr, context=None):
    """Arithmetic, comparisons, boolean ops and explicit runtime context only.

    Context keys use MUGEN spelling, e.g. var(10), time, animelemtime(2).
    Assignment, redirection, interval syntax and unknown triggers fail closed.
    """
    context = {k.lower(): v for k, v in (context or {}).items()}
    expr = expr.strip().lower()
    if len(expr) > 4096 or ':=' in expr:
        raise Unsupported('assignment or oversized expression')
    expr = expr.replace('&&', ' and ').replace('||', ' or ')
    expr = re.sub(r'!(?!=)', ' not ', expr)
    expr = re.sub(r'(?<![<>=!])=(?!=)', '==', expr).strip()
    try:
        tree = ast.parse(expr, mode='eval')
    except (SyntaxError, RecursionError) as e:
        raise Unsupported('syntax/redirection/interval not supported') from e
    if sum(1 for _ in ast.walk(tree)) > 256:
        raise Unsupported('expression too complex')

    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float, bool, str)):
            return n.value
        if isinstance(n, ast.Name) and n.id in context:
            return context[n.id]
        if isinstance(n, ast.UnaryOp):
            v = ev(n.operand)
            if isinstance(n.op, ast.Not): return int(not v)
            if isinstance(n.op, ast.USub): return -v
            if isinstance(n.op, ast.UAdd): return v
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                raise Unsupported('non-numeric arithmetic')
            if isinstance(n.op, ast.Add): return a + b
            if isinstance(n.op, ast.Sub): return a - b
            if isinstance(n.op, ast.Mult): return a * b
            # MUGEN integer division truncates toward zero.
            if isinstance(n.op, ast.Div):
                return math.trunc(a / b) if isinstance(a, int) and isinstance(b, int) else a / b
            if isinstance(n.op, ast.Mod): return a - math.trunc(a / b) * b
        if isinstance(n, ast.BoolOp):
            vals = [ev(v) for v in n.values]  # do not hide unresolved side effects
            return int(all(vals) if isinstance(n.op, ast.And) else any(vals))
        if isinstance(n, ast.Compare) and len(n.ops) == 1:
            a, b = ev(n.left), ev(n.comparators[0])
            op = n.ops[0]
            if isinstance(op, ast.Eq): return int(a == b)
            if isinstance(op, ast.NotEq): return int(a != b)
            if isinstance(op, ast.Lt): return int(a < b)
            if isinstance(op, ast.LtE): return int(a <= b)
            if isinstance(op, ast.Gt): return int(a > b)
            if isinstance(op, ast.GtE): return int(a >= b)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and not n.keywords:
            name = n.func.id
            args = [ev(a) for a in n.args]
            key = name + '(' + ','.join(str(a) for a in args) + ')'
            if key in context: return context[key]
            if name in ('floor', 'ceil', 'abs') and len(args) == 1:
                return {'floor': math.floor, 'ceil': math.ceil, 'abs': abs}[name](*args)
            if name == 'ifelse' and len(args) == 3:
                return args[1] if args[0] else args[2]
        raise Unsupported('unknown expression: ' + ast.unparse(n))
    try:
        result = ev(tree.body)
        if isinstance(result, (int, float)) and (not math.isfinite(result) or abs(result) > 2**53):
            raise Unsupported('numeric range')
        return result
    except (ArithmeticError, TypeError, RecursionError) as e:
        raise Unsupported(str(e)) from e


def parameter(field):
    out = dict(field)
    try:
        out['value'] = [evaluate(p) for p in split_values(field['expression'])]
        out['confidence'] = 'ALTA'
    except Unsupported as e:
        out.update(value=None, confidence='BAIXA', reason=str(e))
    return out


def triggers(controller, context):
    groups = {}
    for p in controller['fields']:
        if re.fullmatch(r'trigger(?:all|\d+)', p['key']):
            groups.setdefault(p['key'], []).append(evaluate(p['expression'], context))
    return bool(all(groups.get('triggerall', [True])) and
                any(all(v) for k, v in groups.items() if k != 'triggerall'))


def resolve(base, name):
    path = base / name.strip('"').replace('\\', '/')
    if path.is_file(): return path.resolve()
    # Windows MUGEN references are case insensitive; ambiguity is an error.
    current = base.resolve()
    for part in name.strip('"').replace('\\', '/').split('/'):
        matches = [p for p in current.iterdir() if p.name.casefold() == part.casefold()] if current.is_dir() else []
        if part == '..': current = current.parent
        elif len(matches) == 1: current = matches[0]
        else: return path.resolve()
    return current.resolve()


def definition(path):
    secs = sections(path)
    info = next((values(s) for s in secs if s['name'].lower() == 'info'), {})
    files = next((values(s) for s in secs if s['name'].lower() == 'files'), {})
    return {'path': str(path), 'info': info,
            'files': {k: str(resolve(Path(path).parent, v)) for k, v in files.items()}}


def states(paths):
    result, duplicates, constants, commands = {}, [], [], []
    for path in dict.fromkeys(paths):
        current = None
        for s in sections(path):
            m = re.fullmatch(r'statedef\s+(-?\d+)', s['name'], re.I)
            if m:
                num = str(int(m[1]))
                current = {'id': int(num), 'header': s, 'controllers': []}
                if num in result:
                    duplicates.append({'state': int(num), 'source': s['source']})
                else:
                    result[num] = current
            elif re.match(r'state\s+', s['name'], re.I):
                if current is not None:
                    s['type'] = values(s).get('type', '').lower()
                    s['index'] = len(current['controllers'])
                    s['parameters'] = [parameter(p) for p in s['fields'] if not p['key'].startswith('trigger')]
                    current['controllers'].append(s)
            else:
                current = None
                if s['name'].lower() == 'command': commands.append(s)
                else: constants.append(s)
    return result, duplicates, constants, commands


def air(path):
    result = {}
    for s in sections(path):
        m = re.fullmatch(r'begin\s+action\s+(-?\d+)', s['name'], re.I)
        if not m: continue
        frames, defaults, pending = [], {1: [], 2: []}, {}
        loop, invalid = None, []
        target = None
        for line in s['raw']:
            text = line['text']
            if text.lower() == 'loopstart': loop = len(frames); continue
            cm = re.fullmatch(r'clsn([12])(default)?\s*:\s*(\d+)', text, re.I)
            if cm:
                kind, count = int(cm[1]), int(cm[3])
                dest = defaults if cm[2] else pending
                dest[kind] = []
                target = (kind, count, dest)
                continue
            bm = re.fullmatch(r'clsn([12])\[\d+\]\s*=\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)', text, re.I)
            if bm and target and int(bm[1]) == target[0]:
                target[2][target[0]].append(list(map(int, bm.groups()[1:])))
                continue
            parts = split_values(text)
            if len(parts) >= 5 and all(re.fullmatch(r'-?\d+', v) for v in parts[:5]):
                if target and len(target[2][target[0]]) != target[1]: invalid.append(line)
                g, n, x, y, duration = map(int, parts[:5])
                frames.append({'sprite': [g, n], 'offset': [x, y], 'ticks': duration,
                               'flags': parts[5:], 'hitboxes': pending.get(1, defaults[1]).copy(),
                               'hurtboxes': pending.get(2, defaults[2]).copy(),
                               'source': {'file': str(path), 'line': line['line']}})
                pending, target = {}, None
            elif not bm:
                invalid.append(line)
        result[str(int(m[1]))] = {'id': int(m[1]), 'frames': frames, 'loopstart': loop,
                                  'source': s['source'], 'unsupported': invalid}
    return result


def timeline(animation):
    """AIR first-pass geometry windows, NOT HitDef activation or state recovery."""
    tick, windows = 0, []
    for i, frame in enumerate(animation['frames']):
        t = frame['ticks']
        if t < 0:
            return {'duration': None, 'box_windows': windows, 'indefinite_at': tick,
                    'startup': None, 'active': None, 'recovery': None}
        if frame['hitboxes'] and t:
            windows.append({'start': tick, 'end': tick + t, 'element': i + 1})
        tick += t
    return {'duration': tick, 'box_windows': windows,
            'startup': None, 'active': None, 'recovery': None,
            'reason': 'Requires controller execution; AIR boxes alone do not establish hit timing.'}


def binary_metadata(path, kind):
    """Read indices only, never decode/rebuild graphical or audio payloads."""
    data = Path(path).read_bytes()
    rows = []
    if kind == 'sprite':
        if data[:12] != b'ElecbyteSpr\0': raise ValueError('invalid SFF signature')
        version = data[15]
        if version == 1:
            count, offset = struct.unpack_from('<II', data, 20)
            seen = set()
            for _ in range(count):
                if offset in seen: raise ValueError('SFF cycle')
                seen.add(offset)
                nxt, size, x, y, g, n, link = struct.unpack_from('<IIhhHHH', data, offset)
                w = h = None
                if size:
                    if offset + 32 + size > len(data): raise ValueError('truncated SFF')
                    x1, y1, x2, y2 = struct.unpack_from('<4H', data, offset + 32 + 4)
                    w, h = x2 - x1 + 1, y2 - y1 + 1
                elif link < len(rows): w, h = rows[link]['width'], rows[link]['height']
                rows.append(dict(group=g, number=n, width=w, height=h, axis=[x, y], link=link))
                offset = nxt
        elif version == 2:
            offset, count = struct.unpack_from('<II', data, 36)
            for i in range(count):
                g, n, w, h, x, y, link = struct.unpack_from('<hhHHhhH', data, offset + i * 28)
                rows.append(dict(group=g, number=n, width=w, height=h, axis=[x, y], link=link))
        else: raise ValueError('unsupported SFF version')
    else:
        if data[:12] != b'ElecbyteSnd\0': raise ValueError('invalid SND signature')
        version = list(data[12:16])
        count, offset = struct.unpack_from('<II', data, 16)
        seen = set()
        for _ in range(count):
            if offset in seen: raise ValueError('SND cycle')
            seen.add(offset)
            nxt, size, g, n = struct.unpack_from('<IIII', data, offset)
            if offset + 16 + size > len(data): raise ValueError('truncated SND')
            rows.append(dict(group=g, number=n, offset=offset + 16, size=size))
            offset = nxt
    return {'file': str(path), 'version': version, 'entries': rows}
