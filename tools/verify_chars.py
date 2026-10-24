#!/usr/bin/env python3
"""Audit every roster character's generated fight data.

Checks artwork, combat rows and system poses directly from the current
build inputs (CNS/AIR/config), applying the same calibration profiles as
tools/build_fight.py.  Prints one OK/NÃO column per requested feature.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_fight as bf
from calibration.native import apply_profile
from newroster import NEW_CHARS

ATTACK_SIDS = (
    list(range(5, 9)) + list(range(19, 27)) +
    list(range(48, 69)) + list(range(85, 90))
)
SPECIAL_SIDS = list(range(48, 69))
SUPER_SIDS = list(range(85, 90))
SYSTEM = {"intro": 92, "win": 90, "lose": 91}


def air_frame_sprites(frames):
    out = []
    for g, n, *_rest in frames:
        if g >= 0 and n >= 0:
            out.append((g, n))
    return out


def main():
    rows = []
    for name in sorted(bf.CHARS):
        cfg = bf.CHARS[name]
        air = bf.parse_air(str(ROOT / cfg["air"]))
        cns = bf.parse_cns(str(ROOT / cfg["cns"]),
                           cfg.get("coord_scale", 1),
                           cfg.get("damage_scale", 1))
        (moves, _pos, _pow, headers, statedefs, _binds, _acts, _revs,
         _hitlists, _snds, _hitsnds, _exprows) = cns
        apply_profile(str(ROOT), name, cfg, moves, air)
        anims = (bf.resolve_import_anims(cfg, air)
                 if name in NEW_CHARS else dict(cfg["anims"]))
        for _sid, (_state, _anim) in bf.POST_CAL_SUPERS.get(name, {}).items():
            cfg["moves"].setdefault(_sid, _state)
            cfg["anims"][_sid] = _anim
            anims[_sid] = _anim
        if name in bf.POST_CAL_LOSE_ANIM and anims.get(91) == 47:
            anims[91] = bf.POST_CAL_LOSE_ANIM[name]
            cfg["anims"][91] = anims[91]

        problems = []

        def anim_status(sid, placeholder_ok=False, require_state=True):
            anim = anims.get(sid)
            state = cfg["moves"].get(sid)
            if state is None:
                return False, "sem slot", None
            if require_state and state not in statedefs:
                return False, "estado %d ausente" % state, anim
            frames, _loop = air.get(anim, ([], 0))
            sprites = air_frame_sprites(frames)
            if not frames or not sprites:
                return False, "anim %s sem sprites" % anim, anim
            if not placeholder_ok and anim == 47 and state != 47:
                return False, "anim 47 (placeholder)", anim
            return True, "", anim

        specials = [s for s in SPECIAL_SIDS if s in cfg["moves"]]
        bad_specials = []
        for sid in specials:
            ok, why, _ = anim_status(sid)
            if not ok:
                bad_specials.append((sid, why))
        if not specials:
            spec = "NÃO"
            spec_note = "nenhum"
            spec_txt = "NÃO(0)"
        elif bad_specials:
            spec = "NÃO"
            spec_note = "%d/%d sem arte" % (len(bad_specials), len(specials))
            spec_txt = "NÃO(%d/%d)" % (len(specials) - len(bad_specials),
                                       len(specials))
        else:
            spec = "OK"
            spec_note = str(len(specials))
            spec_txt = "OK(%d)" % len(specials)

        supers = [s for s in SUPER_SIDS if s in cfg["moves"]]
        bad_supers = []
        for sid in supers:
            ok, why, _ = anim_status(sid)
            if not ok:
                bad_supers.append((sid, why))
        if not supers:
            sup = "NÃO"
            sup_note = "nenhum"
            sup_txt = "NÃO(0)"
        elif bad_supers:
            sup = "NÃO"
            sup_note = "%d/%d sem arte" % (len(bad_supers), len(supers))
            sup_txt = "NÃO(%d/%d)" % (len(supers) - len(bad_supers),
                                      len(supers))
        else:
            sup = "OK"
            sup_note = str(len(supers))
            sup_txt = "OK(%d)" % len(supers)

        from build_fight import (PROJECTILE_EXCLUDE, PROJECTILE_CALIBRATION,
                                 projectile_rules)
        derived = projectile_rules(statedefs, headers, cfg["moves"],
                                   cfg.get("damage_scale", 1))
        for sid in PROJECTILE_EXCLUDE.get(name, ()):
            derived.pop(sid, None)
        projs = {}
        for sid, row in list(derived.items()) + list(
                cfg.get("projs", {}).items()):
            row = tuple(row)
            old = derived.get(sid, (0, 0, 0, 0x0A))
            # 3-tuples keep the source-derived guard mask.
            projs[sid] = (row[0], row[1], row[2],
                          row[3] if len(row) > 3 else old[3])
        for sid, vals in PROJECTILE_CALIBRATION.get(name, {}).items():
            old = projs.get(sid, (0, 0, 0, 0x0A))
            projs[sid] = (vals[0], vals[1], old[2], old[3])
        bad_projs = []
        fx = ROOT / "build" / "gen_fight" / "projectiles_meta.inc"
        fx_count = 0
        if fx.exists():
            txt = fx.read_text(errors="ignore")
            fx_name = cfg.get("projfx_alias", name)
            marker = fx_name + "ProjFxAnim:"
            if marker in txt:
                after = txt.split(marker, 1)[1].lstrip()
                if after.startswith(".db"):
                    try:
                        fx_count = int(after.split(".db", 1)[1].split()[0])
                    except ValueError:
                        fx_count = 0
        for sid, (vx, dmg, anim, _guard) in projs.items():
            if dmg <= 0:
                bad_projs.append("%d:0dmg" % sid)
            if fx_count <= 0:
                bad_projs.append("%d:sem arte" % sid)
        if not projs:
            proj = "OK"
            proj_note = "nenhum"
            proj_txt = "OK(0)"
        elif bad_projs:
            proj = "NÃO"
            proj_note = ",".join(bad_projs[:4])
            bad_sids = {x.split(':')[0] for x in bad_projs}
            proj_txt = "NÃO(%d/%d)" % (len(projs) - len(bad_sids),
                                       len(projs))
        else:
            proj = "OK"
            proj_note = str(len(projs))
            proj_txt = "OK(%d)" % len(projs)

        def system_check(sid, placeholder_ok=False):
            ok, why, anim = anim_status(sid, placeholder_ok,
                                        require_state=False)
            return ok, why, anim

        intro_ok, intro_why, intro_anim = system_check(SYSTEM["intro"])
        win_ok, win_why, win_anim = system_check(SYSTEM["win"])
        lose_ok, lose_why, lose_anim = system_check(SYSTEM["lose"])
        time_ok = win_ok and lose_ok
        time_why = "; ".join(x for x in (win_why, lose_why) if x)

        bad_combat = []
        hitlists = cns[8]
        for sid in ATTACK_SIDS:
            if sid not in cfg["moves"]:
                continue
            state = cfg["moves"][sid]
            if state not in statedefs:
                bad_combat.append("%d:estado" % sid)
                continue
            mv = moves.get(state, {})
            hitrows = hitlists.get(state, [])
            raw_hits = [c for c in statedefs.get(state, [])
                        if c.get("type", "").lower() == "hitdef"]
            follow = (mv.get("p1mugen", -1) != -1 or
                      mv.get("p2state", 0xFF) != 0xFF or
                      mv.get("throw") or
                      any(c.get("type", "").lower() in
                          ("changestate", "targetstate", "helper")
                          for c in statedefs.get(state, [])))
            if sid in projs:
                if projs[sid][1] <= 0:
                    bad_combat.append("%d:dano" % sid)
                continue
            if not raw_hits:
                # no HitDef in this slice: non-damaging move or follow-up
                continue
            best = max((r.get("damage", 0) or 0 for r in hitrows),
                       default=0)
            if best <= 0 and not follow:
                bad_combat.append("%d:dano0" % sid)
                continue
            if mv:
                velocities = [mv.get(k, 0) or 0 for k in
                              ("gvx", "gvy", "avx", "avy", "grvx", "agvx", "agvy")]
                if not any(velocities) and not follow and \
                        not mv.get("fall") and not mv.get("trip"):
                    bad_combat.append("%d:mov" % sid)
        combat = "OK" if not bad_combat else "NÃO"
        combat_note = "" if not bad_combat else ",".join(bad_combat[:6])

        rows.append({
            "name": name,
            "spec": spec, "spec_note": spec_note, "spec_txt": spec_txt,
            "sup": sup, "sup_note": sup_note, "sup_txt": sup_txt,
            "proj": proj, "proj_note": proj_note, "proj_txt": proj_txt,
            "intro": ("OK" if intro_ok else "NÃO"),
            "win": ("OK" if win_ok else "NÃO"),
            "time": ("OK" if time_ok else "NÃO"),
            "time_note": time_why,
            "combat": combat, "combat_note": combat_note,
            "details": (bad_specials, bad_supers, intro_why, win_why,
                        lose_why, bad_projs, bad_combat),
        })

    # table
    print("%-12s %-7s %-7s %-7s %-6s %-5s %-5s %-5s %-7s" %
          ("CHAR", "ESPEC", "SUPER", "PROJ", "INTRO", "WIN", "TIME", "DANO", "DETALHE"))
    print("-" * 92)
    for r in rows:
        detail = []
        if r["spec"] != "OK":
            detail.append("esp:" + r["spec_note"])
        if r["sup"] != "OK":
            detail.append("sup:" + r["sup_note"])
        if r["proj"] != "OK":
            detail.append("proj:" + r["proj_note"])
        if r["intro"] != "OK":
            detail.append("intro:" + r["details"][2])
        if r["win"] != "OK":
            detail.append("win:" + r["details"][3])
        if r["time"] != "OK":
            detail.append("time:" + r["time_note"])
        if r["combat"] != "OK":
            detail.append("dano/mov:" + r["combat_note"])
        print("%-12s %-8s %-8s %-8s %-6s %-5s %-5s %-5s %s" % (
            r["name"].upper(), r["spec_txt"], r["sup_txt"], r["proj_txt"],
            r["intro"], r["win"], r["time"], r["combat"],
            "; ".join(detail)))

    bad = [r for r in rows if any(r[k] != "OK" for k in
                                  ("spec", "sup", "proj", "intro", "win",
                                   "time", "combat"))]
    print("\n%d/%d personagens com pendências." % (len(bad), len(rows)))


if __name__ == "__main__":
    main()
