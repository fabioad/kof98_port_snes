"""Freeze existing batch catalogs for presentation without rerunning extraction."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from .extract import json_bytes, write_if_changed


def freeze(output, root):
    batch = json.loads((output / 'batch.json').read_text())
    characters = []
    for item in batch['characters']:
        catalog = json.loads((output / item['name'] / 'catalog.json').read_text())
        rows = []
        for row in catalog['rows']:
            generated = row.get('generated_frames')
            rows.append({
                'sid': row['sid'], 'state': row['state'],
                'action': row['action'], 'category': row['category'],
                'wired': row['wired_state'], 'commands': row['commands'],
                'command_definitions': row['command_definitions'],
                'source_elements': row['frame_count'],
                'source_images': row['unique_sprite_count'],
                'source_ticks': row['ticks'],
                'generated_elements': None if generated is None else len(generated),
                'generated_ticks': None if generated is None else
                    [f['ticks'] for f in generated],
                'frames': generated,
                'source_frames': row['source_frames'],
                'combat': row['combat'], 'projectile': row['projectile'],
                'projectile_config': row['projectile_config'],
                'projectile_source': row['projectile_source'],
                'missing_sprites': row['missing_sprites'],
            })
        characters.append({
            **item, 'config_hash': catalog['config_hash'],
            'normal_button_routes': catalog['normal_button_routes'],
            'projectile_art_action': catalog['projectile_art_action'],
            'rows': rows, 'diagnostics': catalog['diagnostics'],
            'measurement_notes': catalog['measurement_notes'],
        })
    result = {
        'captured_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'native port roster, including hidden Omega Rugal',
        'status': batch['status'],
        'characters': characters,
        'counts': {
            'characters': len(characters),
            'msu': sum(c['storage'] == 'MSU' for c in characters),
            'rom': sum(c['storage'] == 'ROM' for c in characters),
            'wired_slots': sum(r['wired'] for c in characters for r in c['rows']),
            'normal_slots': sum(r['wired'] and r['category'] == 'normal'
                                for c in characters for r in c['rows']),
            'special_followup_slots': sum(
                r['wired'] and r['category'] == 'special_or_followup'
                for c in characters for r in c['rows']),
            'super_slots': sum(r['wired'] and r['category'] == 'super_slot'
                               for c in characters for r in c['rows']),
            'projectile_slots': sum(r['projectile'] is not None
                                    for c in characters for r in c['rows']),
            'static_errors': sum(d['level'] == 'error'
                                 for c in characters for d in c['diagnostics']),
        },
        'artifacts': {},
        'evidence': {},
        'limits': batch['runtime_limits'],
    }
    for name in ('kof98-snes.sfc', 'kof98-snes.msu'):
        path = root / name
        data = path.read_bytes()
        result['artifacts'][name] = {
            'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    for name in ('menu-modes.json', 'roster-runtime.json'):
        path = output / name
        if path.exists():
            result['evidence'][name] = json.loads(path.read_text())
    write_if_changed(output / 'snapshot.json', json_bytes(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--root', type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    result = freeze(args.output.resolve(), args.root.resolve())
    print(json.dumps(result['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
