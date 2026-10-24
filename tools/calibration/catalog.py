"""Per-character animation and combat-coverage catalog for batch calibration."""
from collections import defaultdict
from pathlib import Path
import re

from .native import apply_profile, config_hash, read_profile
from .projectiles import (PROJECTILE_ACTIONS, PROJECTILE_CALIBRATION,
                          PROJECTILE_SOURCE_PALETTES, GROUND_PROJECTILES)
from runtime_abi import ABI


def generated_frames(root, name):
    """Read emitted animation records, not estimates of emulator timing."""
    path = Path(root) / 'build/gen_fight' / (name + '_spr.inc')
    if not path.exists():
        return {}
    result = {}
    pattern = re.compile(r'^' + re.escape(name) + r'Anim(\d+):\s*$', re.M)
    text = path.read_text()
    sprite_bytes = []
    meta_path = path.with_name(name + '_meta.inc')
    meta_text = meta_path.read_text() if meta_path.exists() else text
    if name + 'SprData:' in meta_text:
        sprite_section = meta_text.split(name + 'SprData:', 1)[1]
        sprite_section = re.split(r'^\w[^ \n]*:', sprite_section,
                                  maxsplit=1, flags=re.M)[0]
        for line in sprite_section.splitlines():
            if '.db' in line:
                values = [int(v.strip().replace('$', '0x'), 0)
                          for v in line.split('.db', 1)[1].split(',')]
                if len(values) >= 5:
                    sprite_bytes.append(values[3] | values[4] << 8)
    matches = list(pattern.finditer(text))
    for match in matches:
        tail = text[match.end():]
        tail = re.split(r'^\w[^ \n]*:', tail, maxsplit=1, flags=re.M)[0]
        records = []
        sprite_id = None
        for line in tail.splitlines():
            if '.dw' in line:
                sprite_id = int(line.split('.dw', 1)[1].strip(), 0)
            if '.db' not in line:
                continue
            values = [int(v.strip().replace('$', '0x'), 0)
                      for v in line.split('.db', 1)[1].split(';', 1)[0].split(',')]
            if len(values) == 6:
                records.append({'ticks': values[0], 'attack_box': values[4],
                                'hurt_box': values[5], 'sprite_id': sprite_id,
                                'upload_bytes': (sprite_bytes[sprite_id]
                                                 if sprite_id is not None
                                                 and sprite_id < len(sprite_bytes)
                                                 else None)})
        result[int(match.group(1))] = records
    # Identical clips alias another slot's label in AnimTab; no separate
    # AnimN label is emitted for these perfectly valid runtime animations.
    table_label = name + 'AnimTab:'
    if table_label in text:
        table = text.split(table_label, 1)[1]
        table = re.split(r'^\w[^ \n]*:', table, maxsplit=1, flags=re.M)[0]
        targets = re.findall(r'^\s*\.dw\s+' + re.escape(name) + r'Anim(\d+)',
                             table, re.M)
        direct = dict(result)
        for sid, target in enumerate(targets):
            if int(target) in direct:
                result[sid] = [dict(record) for record in direct[int(target)]]
    return result


def slot_category(sid):
    """Native ABI groups, not inferred names of original arcade moves."""
    if sid in range(5, 9) or sid in range(19, 27):
        return 'normal'
    if sid in range(85, 90):
        return 'super_slot'
    if sid in range(48, 67) or sid in (68, 98):
        return 'special_or_followup'
    if sid in range(74, 78):
        return 'throw_or_victim'
    return 'system_or_pose'

def character_catalog(root, name, cfg, builder):
    """Describe every native slot, its source animation, sprites and hit data.

    This is deliberately an audit, not a MUGEN emulator: projectile and
    anti-air labels are candidates inferred from explicit source controllers
    and AIR collision boxes, and are marked as such in the output.
    """
    root = Path(root)
    air = builder.parse_air(str(root / cfg['air']))
    sff = builder.Sff(str(root / cfg['sff']))
    anims = (builder.resolve_import_anims(cfg, air)
             if name in builder.NEW_CHARS else dict(cfg['anims']))
    charge = builder.CHARGE_ANIMS.get(name)
    if charge:
        anims[97] = charge[0]
    move_to_sid = {}
    for sid, state in cfg.get('moves', {}).items():
        move_to_sid.setdefault(state, sid)
    (native_moves, _posadds, _powadds, headers, statedefs, *_rest) = \
        builder.parse_cns(str(root / cfg['cns']), cfg.get('coord_scale', 1),
                          cfg.get('damage_scale', 1), char=name)
    profile_status = 'current'
    try:
        if read_profile(root, name, cfg) is None:
            profile_status = 'missing_profile'
        else:
            apply_profile(root, name, cfg, native_moves, air)
    except ValueError as exc:
        profile_status = str(exc)
    emitted = generated_frames(root, name)

    derived_projectiles = builder.projectile_rules(
        statedefs, headers, cfg.get('moves', {}), cfg.get('damage_scale', 1))
    for _sid in builder.PROJECTILE_EXCLUDE.get(name, ()):
        derived_projectiles.pop(_sid, None)
    projectiles = dict(derived_projectiles)
    for sid, row in cfg.get('projs', {}).items():
        row = tuple(row)
        old = derived_projectiles.get(sid, (0, 0, 0, 0x0A))
        # 3-tuples keep the source-derived guard mask.
        projectiles[sid] = (row[0], row[1], row[2],
                            row[3] if len(row) > 3 else old[3])
    for sid, vals in PROJECTILE_CALIBRATION.get(name, {}).items():
        old = projectiles.get(sid, (0, 0, 0, 0x0A))
        projectiles[sid] = (vals[0], vals[1], old[2], old[3])
    rows = []
    diagnostics = []
    if profile_status != 'current':
        diagnostics.append({'level': 'error', 'issue': 'stale_calibration',
                            'detail': profile_status})
    used_sids = set(anims)
    for sid in sorted(used_sids):
        state = cfg.get('moves', {}).get(sid, 0 if sid == 0 else None)
        action = anims.get(sid)
        frames, loop = air.get(action, ([], -1))
        if sid == 97 and action is not None:
            frames, loop = builder.charge_frames(name, air, action)
        sprite_refs = [(f[0], f[1]) for f in frames if f[0] >= 0 and f[1] >= 0]
        missing = [(g, n) for g, n in sprite_refs if sff.get(g, n) is None]
        attack_frames = [i for i, f in enumerate(frames) if f[6]]
        max_reach = 0
        max_up = 0
        for frame in frames:
            xoff, yoff = frame[2], frame[3]
            for x1, y1, x2, y2 in frame[6]:
                max_reach = max(max_reach, xoff + x2)
                max_up = max(max_up, -(yoff + min(y1, y2)))

        controllers = statedefs.get(state, []) if state is not None else []
        kinds = [c.get('type', '').lower() for c in controllers]
        hitdefs = [c for c in controllers
                   if c.get('type', '').lower() in ('hitdef', 'projectile', 'reversaldef')]
        attrs = [c.get('attr', '') for c in hitdefs]
        projectile = sid in projectiles
        # HitFlag's default includes airborne targets on nearly every move,
        # so it is not evidence that a move is a useful anti-air.  A high
        # attack box plus an uppercut-style command is a better review cue.
        scale = cfg.get('char_scale', 1) / cfg.get('coord_scale', 1)
        max_reach = round(max_reach * scale)
        max_up = round(max_up * scale)
        antiair = bool(hitdefs and max_up >= 88)
        long_range = projectile or bool(hitdefs and max_reach >= 84)
        effects = sorted({k for k in kinds if k in {
            'helper', 'explod', 'playsnd', 'afterimage', 'envshake',
            'hitdef', 'projectile'}})

        row = {
            'sid': sid, 'state': state, 'action': action,
            'configured_action': cfg.get('anims', {}).get(sid),
            'category': slot_category(sid),
            'wired_state': sid in cfg.get('moves', {}),
            'frame_count': len(frames),
            'unique_sprite_count': len(set(sprite_refs)),
            'loopstart': loop,
            'ticks': None if any(f[4] == 255 for f in frames)
                         else sum(max(1, f[4]) for f in frames),
            'source_frames': [
                {'group': f[0], 'number': f[1], 'ticks': f[4],
                 'attack_boxes': f[6], 'hurt_boxes': f[7]} for f in frames],
            'generated_frames': emitted.get(sid),
            'combat': native_moves.get(state),
            'attack_frames': attack_frames,
            'max_hitbox_reach_px': max_reach,
            'max_hitbox_up_px': max_up,
            'hitdef_count': len(hitdefs), 'hitdef_attr': attrs,
            'projectile': ({'vx_8_8': projectiles[sid][0],
                            'damage': projectiles[sid][1],
                            'animation': projectiles[sid][2]}
                           if projectile else None),
            'projectile_config': list(projectiles[sid]) if sid in projectiles else None,
            'projectile_source': ('calibrated' if sid in PROJECTILE_CALIBRATION.get(name, {}) else
                                  'manual' if sid in cfg.get('projs', {}) else
                                  'derived' if projectile else None),
            'long_range_candidate': long_range,
            'antiair_candidate': antiair,
            'effects': effects,
            'missing_sprites': missing,
        }
        for record in row['generated_frames'] or []:
            if record['upload_bytes'] is not None:
                budget = ABI['DMACHUNK']
                record['upload_vblanks_lower_bound'] = (
                    record['upload_bytes'] + budget - 1) // budget
                record['upload_exceeds_frame_ticks'] = (
                    record['ticks'] != 255
                    and record['upload_vblanks_lower_bound'] > record['ticks'])
        rows.append(row)
        if action is None:
            diagnostics.append({'level': 'error', 'sid': sid,
                                'issue': 'missing_animation_mapping'})
        elif not frames:
            diagnostics.append({'level': 'error', 'sid': sid,
                                'issue': 'empty_animation', 'action': action})
        if missing:
            diagnostics.append({'level': 'error' if sid in cfg.get('moves', {}) or sid == 0
                                else 'warning', 'sid': sid,
                                'issue': 'missing_sprite_references',
                                'action': action, 'sprites': missing})
        if sid == 0 and len(set(sprite_refs)) < 2:
            diagnostics.append({'level': 'warning', 'sid': sid,
                                'issue': 'stand_has_fewer_than_two_sprites'})
        if hitdefs and not attack_frames:
            diagnostics.append({'level': 'warning', 'sid': sid,
                                'issue': 'hitdef_without_air_attack_boxes'})
        if any('projectile' == k for k in kinds) and not projectile:
            diagnostics.append({'level': 'error', 'sid': sid,
                                'issue': 'source_projectile_not_wired'})
        # Stationary projectiles are supported: ProjTrySpawn gates the spawn
        # on the ProjTab presence byte, not on vx.  Geese's Raging Storm and
        # Yuri's held shots rely on this.

    command_defs = builder.parse_command_defs(str(root / cfg['cmd']))
    normal_routes = builder.parse_cmd(str(root / cfg['cmd']),
                                      cfg['buttons'], cfg['moves'])
    wired = {}
    for sid, state in cfg.get('moves', {}).items():
        wired.setdefault(state, sid)
    command_rules = builder.cmd_rules(str(root / cfg['cmd']), command_defs, wired)
    commands = defaultdict(list)
    for rule in command_rules:
        commands[rule['state']].append(rule['motion'])
    for row in rows:
        row['commands'] = sorted(set(commands.get(row['sid'], [])))
        row['command_definitions'] = [
            {'name': name, 'held_dirs': command_defs[name][0],
             'elements': command_defs[name][1], 'window_ticks': command_defs[name][2]}
            for name in row['commands'] if name in command_defs]
        if row['hitdef_count'] and any(
                token in command.upper() for command in row['commands']
                for token in ('DP_', 'UPPER', 'ANTIAIR', 'ANTI_AIR')):
            row['antiair_candidate'] = True
        if row['state'] is not None:
            row['state_name'] = headers.get(row['state'], {}).get('type', '')

    mapped = {r['sid'] for r in rows}
    missing_normals = [sid for sid in range(5, 9) if sid not in mapped]
    missing_antiair = not any(r['antiair_candidate'] for r in rows if r['hitdef_count'])
    missing_range = not any(r['long_range_candidate'] for r in rows if r['hitdef_count'])
    diagnostics.extend(
        {'level': 'warning', 'sid': sid, 'issue': 'normal_slot_not_wired'}
        for sid in missing_normals)
    if missing_antiair:
        diagnostics.append({'level': 'review', 'issue': 'no_antiair_candidate'})
    if missing_range:
        diagnostics.append({'level': 'review', 'issue': 'no_long_range_candidate'})

    return {
        'character': name, 'display': cfg.get('display', name.upper()),
        'config_hash': config_hash(cfg),
        'profile_status': profile_status,
        'animation_provenance': ('synthetic_sff_groups'
                                 if '_gen.air' in cfg['air'] else 'source_air'),
        'msu': bool(cfg.get('msu')), 'animation_source': cfg['air'],
        'sprite_source': cfg['sff'], 'command_source': cfg['cmd'],
        'mapped_slots': len(rows), 'command_rules': len(command_rules),
        'normal_button_routes': normal_routes,
        'projectile_slots': [r['sid'] for r in rows if r['projectile']],
        'long_range_slots': [r['sid'] for r in rows if r['long_range_candidate']],
        'antiair_slots': [r['sid'] for r in rows if r['antiair_candidate']],
        'rows': rows, 'diagnostics': diagnostics,
        'projectile_art_action': PROJECTILE_ACTIONS.get(name),
        'projectile_palette': PROJECTILE_SOURCE_PALETTES.get(name),
        'ground_projectile': name in GROUND_PROJECTILES,
        'measurement_notes': [
            'Frame counts refer to AIR elements, not unique pictures or measured VBlanks.',
            'Generated records describe emitted tables and may be stale until a successful build.',
            '255 tick elements are holds; total duration is unknown for these clips.',
            'Categories follow native SID groups, not a count of distinct arcade moves.',
            'Attack boxes and reach alone do not establish startup, recovery or anti-air effectiveness.',
            f"Upload lower bounds use the shared runtime cap: {ABI['DMACHUNK']} B/VBlank for ROM and MSU; voices use their own bounded queue.",
            'Upload bounds assume a cold frame; repeated sprites may reuse a displayed or pending upload.',
        ],
        'manual_playtest': {
            'status': 'pending',
            'scenarios': [
                'idle animation cycles through multiple frames',
                'four standing normals and four crouching normals',
                'jump normals and landing recovery',
                'each mapped special and super',
                'projectiles: launch, travel, collision and disappearance',
                'long-range attacks at near and maximum intended distance',
                'anti-air attacks against an opponent jump',
                'guard, hitstun, knockdown and recovery',
                'visual effects and sound timing',
            ],
        },
    }


def markdown(catalog):
    lines = [f"# {catalog['display']} — animações e cobertura", '',
             f"AIR: `{catalog['animation_source']}`; SFF: `{catalog['sprite_source']}`; "
             f"comandos: `{catalog['command_source']}`.", '',
             f"Slots: {catalog['mapped_slots']}; regras de comando: {catalog['command_rules']}; "
             f"projéteis: {catalog['projectile_slots']}; longo alcance: {catalog['long_range_slots']}; "
             f"candidatos antiaéreos: {catalog['antiair_slots']}.", '',
             'Quadros sao elementos AIR, nao imagens unicas. A coluna ROM le os registros '
             'gerados; ticks 255 indicam hold. Os indices de caixas ativas comecam em zero. '
             'Categorias seguem slots da engine, nao nomes ou contagens de golpes Arcade.', '',
             '| SID | Estado | Categoria | AIR | Elementos AIR | Elementos ROM | Imagens | Ticks AIR | Dano | Projétil | Comandos |',
             '|---:|---:|---|---:|---:|---:|---:|---|---:|---|---|']
    for r in catalog['rows']:
        lines.append('| {sid} | {state} | {category} | {action} | {frame_count} | {emitted} | {images} | {ticks} | {damage} | {proj} | {cmd} |'.format(
            sid=r['sid'], state=r['state'], action=r['action'],
            category=r['category'], frame_count=r['frame_count'],
            emitted=len(r['generated_frames']) if r['generated_frames'] is not None else '?',
            images=r['unique_sprite_count'],
            ticks=r['ticks'] if r['ticks'] is not None else 'hold',
            damage=(r['combat'] or {}).get('damage', ''),
            proj=(f"vx={r['projectile']['vx_8_8']}/256 dmg={r['projectile']['damage']}"
                  if r['projectile'] else '—'),
            cmd=', '.join(r['commands']) or '—'))
    lines += ['', '## Alertas', '']
    if not catalog['diagnostics']:
        lines.append('Nenhuma inconsistência estática encontrada.')
    for d in catalog['diagnostics']:
        lines.append(f"- **{d['level']}** SID {d.get('sid', '—')}: `{d['issue']}`")
    lines += ['', '## Validação manual pendente', '',
              'O smoke test automático não confirma sensação de jogo, alcance percebido ou leitura dos efeitos. '
              'Validar estes cenários após a auditoria automatizada:', '']
    lines.extend(f"- [ ] {s}" for s in catalog['manual_playtest']['scenarios'])
    return '\n'.join(lines) + '\n'
