#!/usr/bin/env python3
"""Batch character audit, safe calibration/build, emulator smoke, and handoff."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import build_fight  # noqa: E402
from calibration.catalog import character_catalog, markdown  # noqa: E402
from calibration.extract import json_bytes, write_if_changed  # noqa: E402


def select_chars(args):
    if args.char:
        names = []
        for item in args.char:
            for name in item.split(','):
                key = name.strip().lower().replace(' ', '')
                if key not in build_fight.CHARS:
                    raise ValueError(f'unknown character: {name}')
                names.append(key)
        return list(dict.fromkeys(names))
    if args.all:
        return list(build_fight.CHARS)
    # The normal roster includes the original reference fighters too.  Keep
    # Omega Rugal opt-in because it is a hidden boss and not a selectable slot.
    return [name for name in build_fight.CHARS if name != 'omegarugal']


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--char', action='append',
                       help='character key; repeat or comma-separate; default is all selectable fighters')
    group.add_argument('--all', action='store_true', help='include hidden and non-selectable entries too')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/calibration/batch')
    parser.add_argument('--apply', action='store_true',
                        help='run the transactional high-confidence calibrator and build a ROM')
    parser.add_argument('--smoke', action='store_true',
                        help='select each requested character in RetroArch and check live idle animation frames')
    parser.add_argument('--launch', action='store_true', help='launch RetroArch for --smoke')
    parser.add_argument('--retroarch', default='retroarch')
    parser.add_argument('--core', default='/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so')
    parser.add_argument('--shots', action='store_true', help='save emulator screenshots for the tested batch')
    args = parser.parse_args(argv)

    names = select_chars(args)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {
        'schema': 1, 'status': 'cataloged', 'characters': [],
        'scope': 'all requested native characters; no alternate MUGEN variants',
        'calibration': 'the existing transactional calibrator applies only high-confidence source-backed corrections',
        'runtime_limits': [
            'static projectile and anti-air labels are candidates from CNS/AIR, not gameplay proof',
            'the emulator smoke checks character loading and live idle animation progression',
            'the final move feel, distance, anti-air coverage, projectile collision, and effect timing still need player validation',
        ],
    }
    if args.apply:
        command = [sys.executable, str(ROOT / 'tools/calibrate.py')]
        for name in names:
            command += ['--char', name]
        command += ['--apply', '--build', '--test']
        print('Aplicando calibração segura e compilando a ROM...', flush=True)
        subprocess.run(command, cwd=ROOT, check=True)
        report['status'] = 'calibrated_and_built'
        report['calibration_command'] = command
    for name in names:
        print(f'Catalogando {name}...', flush=True)
        catalog = character_catalog(ROOT, name, build_fight.CHARS[name], build_fight)
        char_dir = output / name
        write_if_changed(char_dir / 'catalog.json', json_bytes(catalog))
        write_if_changed(char_dir / 'animations.md', markdown(catalog).encode())
        errors = sum(d['level'] == 'error' for d in catalog['diagnostics'])
        warnings = sum(d['level'] in ('warning', 'review') for d in catalog['diagnostics'])
        report['characters'].append({
            'name': name, 'display': catalog['display'],
            'storage': 'MSU' if catalog['msu'] else 'ROM',
            'animation_provenance': catalog['animation_provenance'],
            'profile_status': catalog['profile_status'],
            'normal_sids': [r['sid'] for r in catalog['rows']
                            if r['wired_state'] and r['category'] == 'normal'],
            'special_sids': [r['sid'] for r in catalog['rows']
                             if r['wired_state'] and r['category'] == 'special_or_followup'],
            'super_sids': [r['sid'] for r in catalog['rows']
                           if r['wired_state'] and r['category'] == 'super_slot'],
            'animation_slots': catalog['mapped_slots'],
            'command_rules': catalog['command_rules'],
            'projectiles': catalog['projectile_slots'],
            'long_range_candidates': catalog['long_range_slots'],
            'antiair_candidates': catalog['antiair_slots'],
            'errors': errors, 'warnings_or_review': warnings,
            'catalog': str((char_dir / 'animations.md').relative_to(ROOT)),
            'manual_playtest': 'pending',
        })

    if args.smoke:
        # Resolve the actual select IDs from the generated runtime table, so
        # roster order changes do not silently test the wrong characters.
        import test_roster  # noqa: E402
        roster = test_roster.parse_tables()
        ids_by_name = {entry['name']: cid for cid, entry in roster.items()}
        missing = [name for name in names if name not in ids_by_name]
        if missing:
            raise ValueError('characters absent from the current select table: ' + ', '.join(missing))
        command = [sys.executable, str(ROOT / 'tools/test_roster.py'),
                   '--animation-smoke', '--retroarch', args.retroarch,
                   '--core', args.core]
        if set(names) != set(build_fight.CHARS):
            if 'omegarugal' in names:
                raise ValueError('hidden boss smoke requires --all')
            command += ['--only', ','.join(str(ids_by_name[name]) for name in names)]
        if args.launch:
            command.append('--launch')
        if args.shots:
            shots = output / 'shots'
            shots.mkdir(exist_ok=True)
            command += ['--shots', str(shots)]
        print('Executando seleção e smoke test no emulador...', flush=True)
        proc = subprocess.run(command, cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        write_if_changed(output / 'emulator.log', proc.stdout.encode())
        report['emulator'] = {'status': 'passed' if proc.returncode == 0 else 'failed',
                              'log': str((output / 'emulator.log').relative_to(ROOT)),
                              'returncode': proc.returncode}
        if proc.returncode:
            report['status'] = 'needs_repair'
        else:
            report['status'] = 'ready_for_player_validation'

    if any(c['errors'] for c in report['characters']):
        report['status'] = 'needs_repair'

    pending = [c['display'] for c in report['characters']]
    report['player_validation_request'] = {
        'status': 'pending',
        'characters': pending,
        'checks': [
            'combos and cancel timing', 'projectile launch, range, hit and disappearance',
            'long-range normal/special reach', 'anti-air coverage',
            'animation completeness and visual effects', 'overall controls and game feel',
        ],
    }
    write_if_changed(output / 'batch.json', json_bytes(report))
    lines = ['# Calibração em lote — KOF98 SNES', '',
             f"Status: `{report['status']}`", '',
             '| Personagem | Slots | Regras | Projéteis | Longo alcance | Antiaéreos | Alertas | Validação |',
             '|---|---:|---:|---|---|---|---:|---|']
    for c in report['characters']:
        lines.append(f"| {c['display']} | {c['animation_slots']} | {c['command_rules']} | "
                     f"{c['projectiles']} | {c['long_range_candidates']} | "
                     f"{c['antiair_candidates']} | {c['errors']}/{c['warnings_or_review']} | pending |")
    lines += ['', '## Arquivos por personagem', '']
    lines.extend(f"- [{c['display']} animações]({c['name']}/animations.md)" for c in report['characters'])
    lines += ['', '## Próxima etapa', '',
              'O catálogo sinaliza lacunas prováveis e o smoke test verifica carregamento e ciclo de idle. '
              'Depois do resultado automatizado, valide os personagens listados em jogo, sobretudo comandos, '
              'projéteis, longo alcance, antiaéreos e efeitos. O relatório mantém essa etapa pendente até seu retorno.', '']
    write_if_changed(output / 'batch.md', '\n'.join(lines).encode())
    print(json.dumps({'status': report['status'], 'characters': len(names),
                      'report': str(output / 'batch.md'),
                      'player_validation': 'pending'}, ensure_ascii=False))
    return 1 if report['status'] == 'needs_repair' else 0


if __name__ == '__main__':
    sys.exit(main())
