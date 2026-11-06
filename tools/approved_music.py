"""Install the reviewed FFG arrangements, including on clean/repeated builds.

assets/audio/ffg is the production source. Previews and the reference ROM are
not build inputs. Fail on stale MIDI or a modified approved payload so changes
cannot silently ship with an old arrangement or the legacy 909 instrument bank.
Long linear songs are losslessly repacked for SNESMOD's 64-pattern table;
the reviewed source bytes, musical events, instruments and samples stay intact.
"""
import argparse
import hashlib
import json
from pathlib import Path
from it_pattern_limit import fit_snesmod

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'assets/audio/ffg'


class ApprovedMusicError(RuntimeError):
    pass


def digest(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def modules():
    return json.loads((PACK / 'manifest.json').read_text())['modules']


def install(row, destination):
    source = PACK / row['file']
    if digest(source) != row['sha256']:
        raise ApprovedMusicError(f"Approved audio changed: {source}; rebuild/review the FFG pack")
    if row['midi'] and digest(ROOT / row['midi']) != row['midiSha256']:
        raise ApprovedMusicError(f"MIDI changed: {row['midi']}; regenerate/review its FFG arrangement")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = fit_snesmod(source.read_bytes())
    if not destination.exists() or destination.read_bytes() != payload:
        destination.write_bytes(payload)


def install_for_midi(midi, destination):
    midi = Path(midi).resolve()
    for row in modules():
        if row['midi'] and (ROOT / row['midi']).resolve() == midi:
            install(row, destination)
            return True
    return False


def install_frontend():
    for row in modules():
        if row['target'].startswith('assets/audio/menu/'):
            install(row, ROOT / row['target'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frontend', action='store_true', required=True)
    parser.parse_args()
    install_frontend()
