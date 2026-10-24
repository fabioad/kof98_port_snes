"""ROM identification by actual bytes, plus optional measured observations.

No game addresses or gameplay values are guessed from filenames. Observations
are external evidence, never automatic high-confidence calibration input.
"""
import hashlib
import json
import zipfile
from pathlib import Path
from .mugen import sha

SOURCE = 'https://github.com/mamedev/mame/blob/master/src/mame/snk/neogeo.cpp'
PROGRAMS = {
    '0452828785110601c65f667209fc2d2926cd3751': ('kof98', 'NGM-2420 MVS protected', 0x200000),
    '26577264aa72d6af272952a876fcd3775f53e3fa': ('kof98h', 'NGH-2420 MVS/AES', 0x100000),
}
P2 = '5e735929ec6c3ca5b2efae3c7de47bcbb8ade2c5'


def inspect(path, observations=None):
    result = {'path': str(path), 'sha256': sha(path), 'source': SOURCE, 'entries': [],
              'revision': 'unknown', 'gameplay_validation': 'not_performed', 'divergences': None,
              'reason': 'No verified emulator traces supplied; ROM identity is not gameplay validation.'}
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            if info.is_dir(): continue
            data = z.read(info)
            result['entries'].append({'name': info.filename, 'size': len(data),
                                       'crc32': f'{info.CRC:08x}', 'sha1': hashlib.sha1(data).hexdigest()})
    hashes = {r['sha1'] for r in result['entries']}
    matches = [PROGRAMS[h] for h in hashes if h in PROGRAMS and P2 in hashes]
    if len(matches) == 1:
        setname, revision, offset = matches[0]
        result.update(set=setname, revision=revision,
                      mapping={'program': '68000 ROM_LOAD16_WORD_SWAP', 'p1_offset': 0,
                               'p2_offset': offset, 'protected': setname == 'kof98'})
    if observations:
        trace = json.loads(Path(observations).read_text())
        if trace.get('rom_sha256') != result['sha256']: raise ValueError('trace belongs to another ROM')
        if not trace.get('emulator') or not trace.get('measurements'): raise ValueError('missing trace evidence')
        result['observations'] = trace
        result['gameplay_validation'] = 'external_observations_unverified'
    return result
