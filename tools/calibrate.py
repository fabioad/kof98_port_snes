#!/usr/bin/env python3
"""Batch, conservative character calibration against the project's MUGEN sources."""
import argparse
from collections import Counter
import contextlib
import fcntl
import json
import os
from pathlib import Path
import sys
import tempfile
import time

from calibration import mugen, native, rom
from calibration.extract import discover, extract, json_bytes, write_if_changed, alias
from calibration.pipeline import Transaction, stage_tree, generate, build, run
import build_fight

ROOT = Path(__file__).resolve().parents[1]


def report_text(report):
    totals = report['totals']
    lines = ['# Calibração MUGEN → SNES', '',
             f"Status: {report['status']}", '',
             f"Definições: {totals['definitions']}; estados/ações: {totals['moves']}; "
             f"personagens ligados ao SNES: {totals['native_characters']}; "
             f"correções propostas: {totals['corrections']}; aplicadas: {totals['applied_properties']}.", '',
             'Estados auxiliares e ações de sistema estão incluídos no catálogo; não são todos golpes jogáveis.', '',
             '## Por definição', '']
    for c in report['characters']:
        lines.append(f"- **{c['id']}**: {c['moves']} estados, {c['attacks']} estados ofensivos; "
                     f"SNES: {c['native'] or 'sem correspondência'}; "
                     f"{c.get('corrections', 0)} correções; cache: {c['cache_hit']}.")
    lines += ['', '## Cobertura e limites', '',
              '- Somente parâmetros resolvidos sem variáveis implícitas e com correspondência inequívoca são aplicados.',
              '- HitDef dinâmico, helpers, multihits, cancels, modos ADVANCED/EXTRA e juggles permanecem no IR; '
              'o simulador parcial não valida a execução integral do motor nem a fidelidade Arcade.',
              '- Startup/active/recovery ficam desconhecidos quando dependem de execução; box_windows mede apenas geometria AIR.',
              '- Esta calibração não altera alcance/hitboxes, animações antiaéreas, arte de fogo ou projéteis; essas partes dependem do AIR, dos sprites e do motor nativo.',
              '- O motor atual compartilha hitstun com guardstun e parte do hitstop. Essas limitações são relatadas, não mascaradas.',
              '- Personagens sem slot nativo são extraídos, mas não adicionados automaticamente à ROM.',
              '- Consulte os JSON individuais para arquivos, linhas, estados, controladores, expressões e divergências.', '',
              '## Verificações', '']
    for test in report['tests']: lines.append('- ' + json.dumps(test, ensure_ascii=False))
    if report.get('rom'):
        lines += ['', '## ROM', '', f"Revisão: {report['rom']['revision']}. "
                  f"Validação de gameplay: {report['rom']['gameplay_validation']}.",
                  f"Fonte do mapeamento: {rom.SOURCE}"]
    if report.get('error'): lines += ['', '## Falha', '', report['error']]
    return '\n'.join(lines) + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    select = p.add_mutually_exclusive_group()
    select.add_argument('--all', action='store_true', help='all discovered definitions (including variants)')
    select.add_argument('--char', action='append', help='native name, alias or definition ID; repeatable')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--analyze', action='store_true', help='read sources only; write cache/reports under output')
    mode.add_argument('--apply', action='store_true', help='publish only high-confidence corrections after regression checks')
    p.add_argument('--build', action='store_true', help='assemble/link/verify an incremental ExHiROM in staging')
    p.add_argument('--test', action='store_true', help='run parser/conversion/simulation/transaction regression suite')
    p.add_argument('--report', action='store_true', help='write detailed JSON and Markdown reports (also default)')
    p.add_argument('--validate-rom', action='store_true', help='identify ROM bytes; report gameplay evidence separately')
    p.add_argument('--rom', type=Path, help='Neo Geo ZIP; defaults to discovered root kof98 archive')
    p.add_argument('--observations', type=Path, help='external JSON observations bound to ROM SHA256')
    p.add_argument('--mugen-root', type=Path, default=ROOT / 'assets/characters')
    p.add_argument('--output', type=Path, default=ROOT / 'build/calibration')
    p.add_argument('--protect', type=Path, default=ROOT / 'assets/calibration/protected.json', help='protected characters/states')
    p.add_argument('--rollback', type=Path, help='restore a committed transaction directory; refuses subsequent edits')
    args = p.parse_args(argv)
    if args.analyze and (args.apply or args.build): p.error('--analyze cannot build/apply')
    if args.observations and not args.validate_rom: p.error('--observations requires --validate-rom')
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=True)
    with (out / '.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.rollback:
            Transaction.rollback(ROOT, args.rollback.resolve()); print('Rollback concluído.'); return 0
        os.chdir(ROOT)
        records = discover(args.mugen_root.resolve(), build_fight.CHARS)
        if args.char:
            wanted = {alias(c) for c in args.char}
            records = [r for r in records if wanted & ({alias(r['id']), alias(r['native'] or ''), alias(Path(r['path']).stem)} | set(r['aliases']))]
            # A native name selects canonical DEF; alternate forms remain --all or explicit IDs.
            canonical = [r for r in records if r['native'] and alias(r['native']) in wanted]
            if canonical: records = canonical
            if not records: p.error('no character matched')
        report = {'schema': 1, 'status': 'analyzed', 'characters': [], 'tests': [], 'totals': {},
                  'discovery': {'native_adapter': 'tools/build_fight.py:CHARS', 'engine': 'src/engine/fight.asm',
                                'build': 'incremental WLA-DX using linkfile; existing C/audio/SDK objects'}}
        comparisons = []
        protections = json.loads(args.protect.read_text()) if args.protect.exists() else {}
        run_dir = Path(tempfile.mkdtemp(prefix='run-', dir=out))
        tx = Transaction(ROOT, run_dir / 'transaction')
        try:
            for d in records:
                print(f"Extraindo {d['id']}...", flush=True)
                ir, cache = extract(d, out / 'cache')
                summary = {'id': d['id'], 'native': d['native'], 'cache_hit': cache,
                           'moves': len(ir['moves']), 'attacks': sum(m['kind'] != 'action' for m in ir['moves']),
                           'unresolved_parameters': sum(m['unresolved_parameters'] for m in ir['moves']),
                           'issues': ir['issues']}
                if d['native']:
                    comp = native.compare(ROOT, ir, d['native'], build_fight.CHARS[d['native']], build_fight, protections)
                    comparisons.append(comp)
                    summary.update(corrections=len(comp['profile']['corrections']),
                                   matched_states=len(comp['matched_states']),
                                   unmatched_states=len(comp['unmatched_states']),
                                   differences=dict(Counter(v['status'] for v in comp['differences'])))
                    write_if_changed(out / 'characters' / (d['id'] + '.comparison.json'), json_bytes(comp))
                    tx.add(Path(native.PROFILE_DIR) / (d['native'] + '.json'), json_bytes(comp['profile']))
                write_if_changed(out / 'characters' / (d['id'] + '.json'), json_bytes(ir))
                report['characters'].append(summary)
            # Proposal diff before build, even for analysis-only runs.
            tx.prepare()
            if args.validate_rom:
                candidates = list(ROOT.glob('*kof98*.zip'))
                path = args.rom or (candidates[0] if len(candidates) == 1 else None)
                if path is None: raise ValueError('ROM archive ambiguous/missing; pass --rom')
                report['rom'] = rom.inspect(path, args.observations)
            if args.apply or args.build:
                stage = Path(tempfile.mkdtemp(prefix='kof98-calibration-')) / 'stage'
                report['staging'] = str(stage)
                stage_tree(ROOT, stage)
                # Build all mapped characters selected; graphical outputs are only
                # published if bytes differ. Source assets remain untouched.
                print('Gerando e verificando tabelas temporárias...', flush=True)
                report['tests'].extend(generate(ROOT, stage, comparisons, build_fight))
                for generated in (stage / 'build/gen_fight').rglob('*'):
                    if generated.is_file():
                        relative = generated.relative_to(stage / 'build/gen_fight')
                        tx.add(Path('build/gen_fight') / relative, generated.read_bytes())
                if args.build:
                    print('Compilando e validando ROM temporária...', flush=True)
                    output = build(ROOT, stage, run_dir / 'build.log')
                    report['tests'].append({'build': 'passed', 'rom': str(output), 'gameplay': 'not_emulated'})
                    tx.add(Path('kof98-snes.sfc'), output.read_bytes())
                    msu = stage / 'build/gen_fight/kof98-snes.msu'
                    if msu.exists():
                        tx.add(Path('kof98-snes.msu'), msu.read_bytes())
                    for suffix in ('.sym', '.symfull'):
                        f = output.with_suffix(suffix)
                        if f.exists(): tx.add(Path('kof98-snes' + suffix), f.read_bytes())
            if args.test or args.apply:
                print('Executando regressões...', flush=True)
                run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tools/tests', '-p', 'test_calibration*.py', '-v'], ROOT, run_dir / 'tests.log')
                report['tests'].append({'regressions': 'passed', 'log': str(run_dir / 'tests.log')})
            tx.prepare()
            if args.apply:
                tx.commit(); report['status'] = 'applied'
            elif args.build: report['status'] = 'build_verified_not_applied'
        except Exception as exc:
            report['status'] = 'failed_no_publication'
            report['error'] = str(exc)
            report['tests'].append({'status': 'failed', 'reason': str(exc)})
        report['transaction'] = str(tx.journal)
        report['totals'] = {
            'definitions': len(report['characters']), 'moves': sum(c['moves'] for c in report['characters']),
            'native_characters': len(comparisons), 'corrections': sum(c.get('corrections', 0) for c in report['characters']),
            'applied_properties': sum(c.get('corrections', 0) for c in report['characters']) if report['status'] == 'applied' and tx.entries else 0,
            'calibrated_moves': len({(c['native'], x.get('state', 'anim:' + str(x.get('animation')))) for c in comparisons for x in c['profile']['corrections']}),
            'changed_files': len(tx.entries) if report['status'] == 'applied' else 0,
        }
        write_if_changed(run_dir / 'report.json', json_bytes(report))
        write_if_changed(out / 'report.json', json_bytes(report))
        write_if_changed(out / 'report.md', report_text(report).encode())
        print(json.dumps({'status': report['status'], **report['totals'], 'report': str(out / 'report.md'), 'transaction': str(tx.journal)}, ensure_ascii=False))
        return 1 if report['status'].startswith('failed') else 0


if __name__ == '__main__':
    sys.exit(main())
