#!/usr/bin/env python3
"""Probe compiled special/super commands without building or altering gameplay.

Input misses and no-impact cases are candidates until retested with suitable
spacing/conditions. Adaptation to different art or mechanics is not a failure.
Use a frozen ROM/MSU/tables snapshot so concurrent builds cannot mix evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight
import build_fight as bf

P1, P2 = 0x4000, 0x4040
BUTTONS = {1: 1, 2: 9, 4: 0, 8: 8, 16: 10, 32: 11, 64: 2}
# Token 64 is the pad's SELECT key (PushHist maps $2000 -> s), not START.
# With 3 (START) the striker commands (Rugal 2899/7200) never entered.
PAD_MASKS = {0x4000: 1, 0x0040: 9, 0x8000: 0, 0x0080: 8,
             0x0020: 10, 0x0010: 11}
SYSTEM = set(range(69, 78)) | set(range(90, 98)) | {67}


def section(text, label):
    m = re.search(r"^" + re.escape(label) + r":[^\n]*\n(.*?)(?=^\w[^\n]*:|\Z)",
                  text, re.M | re.S)
    return m.group(1) if m else ""


def numbers(text, directive="db"):
    return [[int(v.strip().replace("$", "0x"), 0)
             for v in line.split("." + directive, 1)[1].split(";", 1)[0].split(",")]
            for line in text.splitlines() if "." + directive in line]


def character(name, tables):
    text = (tables / f"{name}_spr.inc").read_text()
    motions = {}
    for m in re.finditer(r"^" + name + r"Mot(\d+): \.db (\d+),(\d+)\n"
                         r"((?:\s+\.db \d+,\d+\n)+)", text, re.M):
        motions[int(m[1])] = {"elements": numbers(m[4]), "window": int(m[3])}
    rules = []
    seen = set()
    for row in numbers(section(text, name + "CmdTab")):
        if len(row) != 7 or row[-1] < 48 or row[-1] in SYSTEM:
            continue
        motion, held, forbidden, posture, distance, nstate, sid = row
        key = (sid, tuple(map(tuple, motions[motion]["elements"])), held, forbidden, posture)
        if key in seen:
            continue
        seen.add(key)
        rules.append({"sid": sid, "row": row, **motions[motion]})
    trans = []
    body = section(text, name + "TransTab")
    for match in re.finditer(r"\.db (\d+),(\d+),(\d+)\s*\n\s*\.dw \$([0-9A-Fa-f]+)", body):
        trans.append([*map(int, match.group(1, 2, 3)), int(match[4], 16)])
    target = numbers(section(text, name + "TargetTab"))
    projectiles = numbers(section(text, name + "ProjTab"))
    damages = [v[0] for v in numbers(section(text, name + "DamageTab"), "dw")]
    reversal = {int(m[1]): numbers(m[2])[0]
                for m in re.finditer(r"^" + name + r"Rev(\d+):\n((?:\s+\.db[^\n]+\n)+)", text, re.M)}
    metadata = {}
    cfg = bf.CHARS[name]
    moves = dict(cfg["moves"])
    for sid, (state, _anim) in bf.POST_CAL_SUPERS.get(name, {}).items():
        moves.setdefault(sid, state)
    for sid, state, _anim in bf.POST_CAL_REACTIVATED.get(name, ()):
        moves[sid] = state
    compiled_map = tables / f"{name}_remaining_specials.json"
    if compiled_map.exists():
        moves = {int(sid): int(state) for sid, state in
                 json.loads(compiled_map.read_text())["moves"].items()}
    labels = bf._state_labels(bf.asset_path(cfg["cmd"]))
    for sid in {r["sid"] for r in rules}:
        state = moves.get(sid)
        label = "/".join(labels.get(state, [])) or f"state {state}"
        metadata[sid] = {"state": state, "label": label,
                         "damage": damages[sid], "target": target[sid],
                         "projectile": bool(projectiles[sid][-1]),
                         "reversal": reversal.get(sid)}
    return {"rules": rules, "trans": trans, "metadata": metadata,
            "target": target, "projectiles": projectiles}


def dirs(bits, facing=1):
    result = set()
    for bit, button in ((1, 4), (2, 5), (4, 7 if facing == 1 else 6),
                        (8, 6 if facing == 1 else 7)):
        if bits & bit:
            result.add(button)
    return result


def attempt(core, base, info, rule, distance=24, hold=2, keep_direction=True,
            limit=700, complement=False, opponent_attack=False,
            power=5000, opponent_air=False, air_height=72, combine_finish=False,
            input_game_ticks=False, opponent_at=3, opponent_button=1,
            natural_jump=False):
    core.load(base)
    core.buttons = [set(), set()]
    core.ram[0x1090] = core.ram[0x1091] = 0
    core.put(P1, 80 << 8)
    core.put(P2, (80 + distance) << 8)
    core.put(P1 + 16, 200)
    core.put(P2 + 16, 200)
    core.put(P1 + 48, power)
    core.step(16)
    if opponent_air:
        core.buttons[1] = {4}
        core.step(6)
        core.buttons[1] = set()
        core.put(P2 + 2, 64 << 8)
        core.put(P2 + 6, 0)
    airborne = not (rule["row"][3] & 3)
    if airborne:
        core.buttons[0] = {4}
        core.step(6)
        core.buttons[0] = set()
        if natural_jump:
            # Let the jump rise on its own until air_height: forcing the
            # height mid-takeoff is overwritten by some air specials (Kim).
            for _ in range(60):
                if core.word(P1 + 2) >> 8 >= air_height:
                    break
                core.step()
        else:
            core.put(P1 + 2, air_height << 8)
            core.put(P1 + 6, (-6 * 256) & 65535)
    expected = {rule["sid"]}
    if info["target"][rule["sid"]][2] != 255:
        expected.add(info["target"][rule["sid"]][2])
    path, victim_path = [], []
    min_hp, last_hp = 200, 200
    healed = False
    entered = False
    ticks = 0
    held_seen = False
    last_clock = core.word(0x1024)
    stagnation = longest_stagnation = 0
    xs, ys = [], []
    complementary = []

    def step(buttons, count):
        nonlocal min_hp, last_hp, healed, entered, ticks, held_seen
        nonlocal stagnation, longest_stagnation, last_clock
        core.buttons[0] = set(buttons)
        for _ in range(count):
            core.step()
            ticks += 1
            st, victim = core.ram[P1 + 8], core.ram[P2 + 8]
            if not path or path[-1] != st:
                path.append(st)
            if not victim_path or victim_path[-1] != victim:
                victim_path.append(victim)
            entered |= st in expected
            held_seen |= victim in (76, 100, 102)
            hp = core.word(P2 + 16)
            healed |= hp > last_hp
            last_hp = hp
            min_hp = min(min_hp, hp)
            if entered:
                xs.append(core.word(P1) / 256)
                ys.append(core.word(P1 + 2) / 256)
            clock = core.word(0x1024)
            stagnation = stagnation + 1 if clock == last_clock else 0
            longest_stagnation = max(stagnation, longest_stagnation)
            last_clock = clock

    def input_step(buttons, count):
        if not input_game_ticks:
            step(buttons, count)
            return
        start_clock = core.word(0x1024)
        for _ in range(count * 12):
            step(buttons, 1)
            if (core.word(0x1024) - start_clock) & 65535 >= count:
                break

    last_dir = 0
    elements = [list(pair) for pair in rule["elements"]]
    if (combine_finish and len(elements) >= 2 and elements[-1][0] == 0
            and elements[-1][1] and elements[-2][0] & 15
            and not elements[-2][1] and not elements[-2][0] & 32):
        elements[-2][1] = elements[-1][1]
        elements.pop()
    required, forbidden = rule["row"][1:3]
    previous_token = None
    for direction, button_mask in elements:
        d = direction & 15
        token = (d, button_mask)
        if token == previous_token:
            # D,D and repeated attack buttons need distinct press edges.
            input_step(set(), hold)
        previous_token = token
        if d:
            last_dir = d
        buttons = {v for k, v in BUTTONS.items() if button_mask & k}
        if buttons:
            d = ((d or last_dir) if keep_direction else d) | required
            d &= ~forbidden
            if rule["row"][3] == 2:
                d |= 2
        # CHR staging can make a fight tick span multiple emulated video
        # frames. Charge is measured by framecnt, not retro_run calls.
        if direction & 32:
            start_clock = core.word(0x1024)
            for _ in range(240):
                step(dirs(d) | buttons, 1)
                if (core.word(0x1024) - start_clock) & 65535 >= 44:
                    break
        else:
            input_step(dirs(d) | buttons, hold)
    core.buttons[0] = set()
    entered_at = ticks if entered else None
    recovery = None
    action_ticks = 0
    for index in range(limit):
        state = core.ram[P1 + 8]
        buttons = set()
        if complement and entered:
            for src, dst, kind, arg in info["trans"]:
                if src == state and kind == 2 and index % 6 == 0:
                    buttons |= {v for k, v in PAD_MASKS.items() if arg & k}
                    complementary.append([state, dst, arg])
        if opponent_attack and entered and index == opponent_at:
            # a tuple presses several pad bits (e.g. (5, 1) = crouch + Y)
            core.buttons[1] = (set(opponent_button)
                               if isinstance(opponent_button, (tuple, list))
                               else {opponent_button})
        if index == opponent_at + 3:
            core.buttons[1] = set()
        step(buttons, 1)
        if entered and entered_at is None:
            entered_at = ticks
        if entered:
            action_ticks += 1
            if (core.ram[P1 + 8] == 0 and core.ram[P2 + 8] == 0
                    and not core.ram[P1 + 52] and not core.ram[P2 + 52]):
                # Allow late projectiles to hit after the shooter recovers.
                if not info["metadata"][rule["sid"]]["projectile"] or index > 120:
                    recovery = ticks
                    break
        elif index >= 45:
            break
        if longest_stagnation > 360:
            break
    return {"entered": bool(entered), "path": path, "victim_path": victim_path,
            "damage": 200 - min_hp, "final_damage": 200 - core.word(P2 + 16),
            "healing": healed, "recovery": recovery, "ticks": ticks,
            "clock_stall": longest_stagnation,
            "x_range": [min(xs), max(xs)] if xs else [],
            "y_peak": max(ys) if ys else 0,
            "held": held_seen, "grab_flags": [core.ram[P1 + 52], core.ram[P2 + 52]],
            "last_states": [core.ram[P1 + 8], core.ram[P2 + 8]],
            "game_state": core.word(0x1020),
            "complements_sent": complementary,
            "setup": {"distance": distance, "hold": hold,
                      "keep_direction": keep_direction, "airborne": airborne,
                      "opponent_attack": opponent_attack, "power": power,
                      "opponent_air": opponent_air, "air_height": air_height,
                      "combine_finish": combine_finish,
                      "input_game_ticks": input_game_ticks,
                      "opponent_at": opponent_at,
                      "opponent_button": opponent_button,
                      "natural_jump": natural_jump}}


# States that are entered but, by the source's own design, deal no damage in
# this probe (no HitDef/Projectile/TargetLifeAdd in the source chain, or a
# self-heal).  Verified against the .cns; see
# docs/AUDITORIA_ESPECIAIS_2026-11-12.md.  A by-design case that suddenly
# deals damage is still reported normally.
BY_DESIGN = {
    ("athena", 1040): "no attack controller (1040->1041)",
    ("athena", 1050): "no attack controller (1050->1051)",
    ("athena", 1060): "no attack controller",
    ("athena", 1065): "no attack controller",
    ("vega", 1400): "teleport", ("vega", 1410): "teleport",
    ("vega", 1420): "teleport", ("vega", 1430): "teleport",
    ("rugal", 1300): "Dark Barrier (projectile reflector)",
    ("rugal", 1310): "Dark Barrier (projectile reflector)",
    ("daimon", 1100): "Chou Ukemi (no attack)",
    ("daimon", 1110): "Chou Ukemi (no attack)",
    ("daimon", 1010): "Jiraishin C is the feint: no shock wave",
    ("chris", 1000): "no attack controller", ("chris", 1050): "no attack controller",
    ("chris", 2000): "no attack controller",
    ("eiji", 1500): "no attack controller", ("eiji", 1510): "no attack controller",
    ("heavyd", 1250): "no attack controller", ("heavyd", 1900): "no attack controller",
    ("shermie", 2000): "no attack controller",
    ("omegarugal", 2000): "no attack controller (2000/2002->2001)",
    ("omegarugal", 2002): "no attack controller (2000/2002->2001)",
    ("lucky", 1000): "no attack controller", ("lucky", 1010): "no attack controller",
    ("kensou", 2000): "self heal (LifeAdd +10)", ("kensou", 2050): "self heal (LifeAdd +10)",
    ("iori", 1400): "Kuzukaze: knockdown throw without source damage",
    ("yuki", 1200): "positioning throw: HitDef without damage",
    ("chin", 1460): "counter wait window (hit lives in 1400/1401)",
    ("chin", 1461): "counter wait window (hit lives in 1400/1401)",
    ("billy", 3100): "power charge (3101 PowerAdd), no attack",
    ("heavyd", 1950): "partial: source deals 1 per contact (4 hits + a "
                      "falling 5th); one flags row per state, so the first "
                      "contact already knocks down",
}


def classify(result, meta, key=None):
    if not result["entered"]:
        return "input_missed"
    if result["clock_stall"] > 360:
        return "clock_frozen"
    if result["last_states"] == [0, 0] and any(result["grab_flags"]):
        return "grab_flag_leak"
    if result["recovery"] is None and result["game_state"] == 1:
        return "recovery_timeout"
    if result["healing"]:
        return "victim_healed"
    if result["damage"] <= 2:
        if key in BY_DESIGN:
            return "by_design"
        return "conditional" if meta["reversal"] else "no_impact_review"
    return "hit_and_recovered"


def best_attempt(attempts):
    # A failed fast-cadence retry must not hide an earlier successful entry
    # with zero impact. Preserve real recovery/state errors above all passes.
    rank = {"clock_frozen": 9, "grab_flag_leak": 8, "victim_healed": 7,
            "recovery_timeout": 6, "hit_and_recovered": 5, "by_design": 4,
            "conditional": 3, "no_impact_review": 2, "input_missed": 0}
    return max(attempts, key=lambda a: (rank[a["status"]], a["result"]["damage"]))


# Setups under which a case is known to connect (measured with
# /tmp-style sweeps on the frozen ROM).  Keys are (character, source state).
def _s(**kw):
    kw.setdefault("hold", 3)
    kw.setdefault("keep_direction", False)
    return kw


def _counter(at=0, button=1, air=True, distance=24):
    return _s(opponent_attack=True, opponent_air=air, opponent_at=at,
              opponent_button=button, distance=distance)


CASE_SETUPS = {
    # long-range rushes: they only connect from their real starting range
    ("joe", 1410): [_s(distance=100, hold=2)],
    ("ryo", 1510): [_s(distance=120, hold=2)],
    ("yuri", 431): [_s(distance=120, hold=2)],
    ("lucky", 2600): [_s(distance=100, hold=2)],
    # air specials: low jump-in at close range
    ("benimaru", 1100): [_s(air_height=16, distance=48, opponent_air=True)],
    ("yuri", 450): [_s(air_height=16, distance=24)],
    ("kim", 1200): [_s(natural_jump=True, air_height=16, distance=24)],
    ("mai", 1043): [_s(air_height=16, distance=24)],
    ("ryo", 2000): [_s(air_height=16, distance=24)],
    ("ryo", 2010): [_s(air_height=16, distance=24)],
    # counters: armed against a jump-in (S/A masks) or a crouch attack
    ("geese", 1400): [_counter()],
    ("billy", 1100): [_counter(button=0)],
    ("chizuru", 1004): [_counter()],
    ("chizuru", 1300): [_counter()],
    ("kasumi", 1200): [_counter()],
    ("kasumi", 1300): [_counter(at=16, button=9)],
    ("kasumi", 3100): [_counter(at=48, air=False)],
    ("kasumi", 3150): [_counter(at=48, air=False)],
    ("mary", 1520): [_counter(at=16), _counter(at=2, button=(5, 1), air=False)],
}


def confirmation_setups(case, key=None):
    # Case-specific setups first: moves that only connect at their real range
    # or timing (long rushes, jump-ins, counters).  Stop at the first hit.
    if case["status"] in ("input_missed", "no_impact_review", "conditional", "by_design"):
        for setup in CASE_SETUPS.get(key, ()):
            yield setup
    if case["status"] == "input_missed":
        for power, hold, distance in ((1000, 3, 40), (0, 3, 40), (5000, 4, 64)):
            yield dict(power=power, hold=hold, distance=distance, keep_direction=False)
        for game_ticks in (False, True):
            for power in (5000, 1000, 0):
                yield dict(power=power, hold=3, distance=40, keep_direction=True,
                           combine_finish=True, input_game_ticks=game_ticks)
    elif case["status"] == "no_impact_review":
        for distance in (32, 48):
            yield dict(hold=3, distance=distance, keep_direction=False)
        if not case["rule"]["row"][3] & 3 or case["meta"]["damage"] > 0:
            yield dict(hold=3, distance=24, keep_direction=False, opponent_air=True)
            yield dict(hold=3, distance=24, keep_direction=False, air_height=28)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def settle(core, limit=900):
    """Wait until both fighters have been standing on the ground for a while.

    The fight starts with an intro state and streams CHR from the MSU, and how
    many frames that takes changed between builds (the vblank presenter
    rewrite shifted it).  A fixed core.step(24) therefore started the move at a
    different point of the entrance on different ROMs: Billy's counter and
    Yuri's air fireball read as regressions when only their setup had moved.
    """
    stable = 0
    for _ in range(limit):
        core.step()
        if (core.ram[P1 + 8] == 0 and core.ram[P1 + 2] == 0
                and core.ram[P2 + 8] == 0 and core.ram[P2 + 2] == 0):
            stable += 1
            if stable >= 20:
                return
        else:
            stable = 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("snapshot", type=Path)
    ap.add_argument("--chars", nargs="+")
    ap.add_argument("--limit", type=int, default=700)
    ap.add_argument("--retry", action="store_true")
    ap.add_argument("--confirm", action="store_true",
                    help="also retest meter, simultaneous finish, game-tick input and aerial context")
    ap.add_argument("--out", default="specials.json")
    ap.add_argument("--charged-only", action="store_true")
    args = ap.parse_args()
    tables = args.snapshot / "tables"
    names = args.chars or list(bf.CHARS)
    report = {"scope": "compiled special/super inputs; P1 vs idle Kyo; native adaptations preserved",
              "rom_sha256": sha256(args.snapshot / "kof98-snes.sfc"),
              "msu_sha256": sha256(args.snapshot / "kof98-snes.msu"),
              "tables_sha256": {p.name: sha256(p) for p in sorted(tables.glob("*_spr.inc"))},
              "limitations": "No 1:1 MUGEN test. Input/no-impact candidates require confirmation; no new build.",
              "characters": {}}
    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
                args.snapshot / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        for name in names:
            info = character(name, tables)
            enter_fight(core, select, name, "kyo")
            core.ram[0x1090] = core.ram[0x1091] = 0
            settle(core)
            base = core.save()
            cases = []
            for index, rule in enumerate(info["rules"]):
                if args.charged_only and not any(d & 32 for d, _b in rule["elements"]):
                    continue
                meta = info["metadata"][rule["sid"]]
                key = (name, meta.get("state"))
                result = attempt(core, base, info, rule, limit=args.limit,
                                 complement=True, opponent_attack=bool(meta["reversal"]))
                status = classify(result, meta, key)
                retries = []
                if (args.retry or args.confirm) and status in ("input_missed", "no_impact_review"):
                    for distance, hold, keep in ((18, 2, False), (64, 2, False), (24, 1, True)):
                        retry = attempt(core, base, info, rule, distance, hold, keep,
                                        args.limit, True, bool(meta["reversal"]))
                        retry_status = classify(retry, meta, key)
                        retries.append({"status": status, "result": result})
                        result, status = retry, retry_status
                        if status not in ("input_missed", "no_impact_review"):
                            break
                attempts = retries + [{"status": status, "result": result}]
                best = best_attempt(attempts)
                case = {"index": index, "rule": rule, "meta": meta,
                        **best, "attempts": attempts}
                if args.confirm:
                    for setup in confirmation_setups(case, key):
                        setup = dict(setup)
                        setup.setdefault("opponent_attack", bool(meta["reversal"]))
                        result = attempt(core, base, info, rule, limit=max(800, args.limit),
                                         complement=True, **setup)
                        status = classify(result, meta, key)
                        attempts.append({"status": status, "result": result})
                        if status not in ("input_missed", "no_impact_review",
                                          "conditional", "by_design"):
                            break
                    case.update(best_attempt(attempts))
                if case["status"] == "by_design":
                    case["reason"] = BY_DESIGN[key]
                cases.append(case)
            report["characters"][name] = cases
            counts = {}
            for case in cases:
                counts[case["status"]] = counts.get(case["status"], 0) + 1
            output = args.snapshot / args.out
            temporary = output.with_suffix(output.suffix + ".tmp")
            temporary.write_text(json.dumps(report, indent=2) + "\n")
            temporary.replace(output)
            print(name, len(cases), counts, flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    main()
