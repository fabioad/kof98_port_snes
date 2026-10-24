"""Staged generation/build and content-checked, reversible publication."""
import difflib
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from .extract import json_bytes, write_if_changed
from . import native
from .validate import validate_tables


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


class Transaction:
    def __init__(self, root, journal):
        self.root, self.journal, self.entries = Path(root), Path(journal), []
        self.journal.mkdir(parents=True, exist_ok=True)

    def add(self, relative, new):
        path = self.root / relative
        if not path.resolve().is_relative_to(self.root.resolve()): raise ValueError('output outside project')
        before = path.read_bytes() if path.exists() else None
        if before == new: return
        i = len(self.entries)
        if before is not None: (self.journal / f'{i}.before').write_bytes(before)
        (self.journal / f'{i}.after').write_bytes(new)
        self.entries.append({'path': str(relative), 'before': digest(before), 'after': digest(new), 'index': i})

    def prepare(self):
        patch = []
        for e in self.entries:
            a = (self.journal / f"{e['index']}.before")
            b = (self.journal / f"{e['index']}.after")
            try:
                old = a.read_bytes().decode('utf-8').splitlines(True) if a.exists() else []
                new = b.read_bytes().decode('utf-8').splitlines(True)
                patch.extend(difflib.unified_diff(old, new, 'a/' + e['path'], 'b/' + e['path']))
            except UnicodeDecodeError:
                patch.append(f"Binary {e['path']}: {e['before']} -> {e['after']}\n")
        write_if_changed(self.journal / 'changes.patch', ''.join(patch).encode())
        self.save('prepared')

    def save(self, status):
        write_if_changed(self.journal / 'manifest.json', json_bytes({'status': status, 'files': self.entries}))

    def commit(self):
        self.prepare()  # durable diff and backups BEFORE any published change
        done = []
        try:
            for e in self.entries:
                path = self.root / e['path']
                if digest(path.read_bytes() if path.exists() else None) != e['before']:
                    raise ValueError('concurrent modification: ' + e['path'])
                write_if_changed(path, (self.journal / f"{e['index']}.after").read_bytes())
                done.append(e)
            self.save('committed')
        except BaseException:
            for e in reversed(done): self.restore(e)
            self.save('rolled_back')
            raise

    def restore(self, e):
        path = self.root / e['path']
        if digest(path.read_bytes() if path.exists() else None) != e['after']:
            raise ValueError('rollback refused: concurrent edit ' + e['path'])
        old = self.journal / f"{e['index']}.before"
        if old.exists(): write_if_changed(path, old.read_bytes())
        else: path.unlink()

    @classmethod
    def rollback(cls, root, journal):
        tx = cls(root, journal)
        manifest = json.loads((tx.journal / 'manifest.json').read_text())
        if manifest['status'] != 'committed': raise ValueError('transaction is not committed')
        tx.entries = manifest['files']
        # Preflight the entire set before restoring even one file.
        for e in tx.entries:
            p = tx.root / e['path']
            if not p.resolve().is_relative_to(tx.root.resolve()): raise ValueError('invalid rollback path')
            if digest(p.read_bytes() if p.exists() else None) != e['after']:
                raise ValueError('rollback refused: changed since calibration: ' + e['path'])
        for e in reversed(tx.entries): tx.restore(e)
        tx.save('rolled_back')


def stage_tree(root, stage):
    root, stage = Path(root), Path(stage)
    stage.mkdir(parents=True)
    for name in ('src', 'tools', 'hdr.asm'):
        (stage / name).symlink_to(root / name, target_is_directory=(root / name).is_dir())
    (stage / 'assets').mkdir()
    for path in (root / 'assets').iterdir():
        if path.name != 'calibration': (stage / 'assets' / path.name).symlink_to(path, target_is_directory=path.is_dir())
    profiles = stage / native.PROFILE_DIR
    if (root / native.PROFILE_DIR).exists(): shutil.copytree(root / native.PROFILE_DIR, profiles)
    else: profiles.mkdir()
    (stage / 'build').mkdir()
    for path in (root / 'build').iterdir():
        if path.name not in ('calibration', 'gen_fight'):
            if path.name == 'gen_stages' and path.is_dir():
                shutil.copytree(path, stage / 'build' / path.name)
            else:
                (stage / 'build' / path.name).symlink_to(path, target_is_directory=path.is_dir())
    shutil.copytree(root / 'build/gen_fight', stage / 'build/gen_fight')


def generate(root, stage, comparisons, builder):
    results = []
    for comparison in comparisons:
        name = comparison['native']
        write_if_changed(stage / native.PROFILE_DIR / (name + '.json'),
                         json_bytes(comparison['profile']))
    # CHR sizes affect shared MSU offsets, voices, effect tables and ROM bank
    # placement. Regenerate the complete bundle in isolation, not just fighters.
    run([os.sys.executable, stage / 'tools/build_fight.py'], stage,
        stage / 'generation.log')
    if ': SKIPPED (' in (stage / 'generation.log').read_text():
        raise ValueError('incomplete roster generation; inspect ' +
                         str(stage / 'generation.log'))
    for comparison in comparisons:
        name = comparison['native']
        cfg = builder.CHARS[name]
        expected = builder.parse_cns(str(stage / cfg['cns']), cfg.get('coord_scale', 1), cfg.get('damage_scale', 1))[0]
        air = builder.parse_air(str(stage / cfg['air']))
        native.apply_profile(stage, name, cfg, expected, air)
        checked = validate_tables(stage / 'build/gen_fight' / (name + '_spr.inc'), name, cfg, expected)
        results.append({'character': name, 'status': 'passed', 'table_values': checked})
    return results


def run(command, cwd, logfile):
    with Path(logfile).open('ab') as f:
        f.write(('\n$ ' + ' '.join(map(str, command)) + '\n').encode()); f.flush()
        subprocess.run(list(map(str, command)), cwd=cwd, stdout=f, stderr=subprocess.STDOUT,
                       check=True, timeout=300)


def build(root, stage, log):
    """Incremental native build using the project's existing linker manifest.

    Reassembles engine, header, boot trampoline; reuses unchanged C/audio/SDK
    objects. No asset generation writes through stage symlinks.
    """
    assembler, linker = root / 'tools/bin/wla-65816', root / 'tools/bin/wlalink'
    # SDK objects and repository fallback tools can use incompatible WLA object
    # formats. Derive the matching SDK from the actual linker inputs.
    for line in (root / 'linkfile').read_text().splitlines():
        if line.startswith('/'):
            for parent in Path(line).parents:
                sdkbin = parent / 'devkitsnes/bin'
                if (sdkbin / 'wla-65816').is_file() and (sdkbin / 'wlalink').is_file():
                    assembler, linker = sdkbin / 'wla-65816', sdkbin / 'wlalink'
                    break
    for source in ('src/snes/main.c', 'build/gen_audio/soundbank.asm'):
        src, obj = root / source, (root / source).with_suffix('.obj')
        if not obj.exists() or src.stat().st_mtime_ns > obj.stat().st_mtime_ns:
            raise ValueError(f'{obj} stale/missing: run make pvsnes first')
    objects = {}
    for source in ('src/snes/fight_bridge.asm', 'src/snes/boot64.asm', 'hdr.asm'):
        out = stage / (Path(source).stem + '.obj')
        run([assembler, '-d', '-s', '-x', '-I', 'src', '-I', 'build', '-I', '.', '-o', out, source], stage, log)
        objects[str(Path(source).with_suffix('.obj'))] = str(out)
    lines = []
    for raw in (root / 'linkfile').read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('['): lines.append(raw); continue
        lines.append(objects.get(line, str((root / line).resolve())))
    link = stage / 'calibration.link'
    link.write_text('\n'.join(lines) + '\n')
    output = stage / 'kof98-snes.sfc'
    run([linker, '-d', '-s', '-A', '-c', link, output], stage, log)
    run(['python3', root / 'tools/fix_checksum.py', output], stage, log)
    run(['python3', root / 'tools/verify_pvsnes_rom.py', output], stage, log)
    return output
