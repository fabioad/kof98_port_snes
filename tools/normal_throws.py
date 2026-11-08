"""Normal-throw repairs, isolated from special/super states and CHR assets.

The native engine holds a victim while its owner occupies slot 75. Flatten
missing source phases into that slot rather than borrowing a special grab or
adding states outside the held-victim window. Source timings/binds are kept;
art uses only cels already selected by wire_throw_chain.
"""
from dataclasses import dataclass

STATE = 19975
ACTION = 65003


@dataclass(frozen=True)
class Phase:
    state: int
    action: int
    # (zero-based source element, HP on the native 200-HP scale).
    hits: tuple = ()
    first: int = 0
    last: int | None = None
    minimum_elements: int = 0


# Literal MUGEN damage on a 1000/1500-HP bar is not the KOF packages' small
# formula damage (which already uses damage_scale=2). Calibrate per family;
# never wrap raw -130/-152 into a positive signed byte. Capture adds 1 HP.
PLANS = {
    "kyo": (Phase(810, 810, ((5, 40),)),),
    "kyonests": (Phase(810, 810, ((5, 40),)),),
    "kyoash": (Phase(810, 810, ((5, 40),)),),
    # AIR 810 is reduced to three cels but CNS uses seven elements and
    # repeats the choke eight times. Restore the element timeline first.
    "rugal": (Phase(810, 810, first=0, last=4, minimum_elements=7),)
             + (Phase(810, 810, ((5, 6),), first=5, last=6,
                      minimum_elements=7),) * 8
             + (Phase(811, 811),),
    # The eight choke hits live on victim 802, not the attacker's HitDef.
    "omegarugal": (Phase(801, 801, tuple((e, 3) for e in
                       (3, 5, 7, 9, 11, 13, 15, 17)) + ((23, 5),)),),
    # Correct normal actor 805; the old numeric-only anim lookup picked
    # super phase 3305 because 805's header is an IfElse expression.
    "leona": (Phase(805, 805, ((5, 22),), minimum_elements=10),),
    # Source 801 delivers its final damage via a second HitDef.
    "mature": (Phase(801, 801, ((5, 30),)),),
    "vice": (Phase(810, 810, ((5, 28),)),),
    "andy": (Phase(810, 810), Phase(811, 811, ((0, 24), (8, 12)))),
    "ryo": (Phase(810, 810), Phase(811, 811, ((1, 40),))),
    "athena": (Phase(810, 810, ((11, 15),)),),
    "kensou": (Phase(810, 810, ((3, 28),)),),
    # The normal command was wired to an aerial attempt (820 -> 821).
    "mai": (Phase(801, 801, ((10, 20),)),),
    # Source changes HitDefs while the victim is held: native StThrow
    # doesn't resolve body hits, so use the final impact as TargetLifeAdd.
    "chizuru": (Phase(360, 360, ((9, 20),)),),
    "chang": (Phase(810, 810, ((5, 30),)),),
    "shermie": (Phase(810, 810, ((10, 26),)),),
    # Billy's damage is LifeAdd in victim 3003, which isn't run natively.
    "billy": (Phase(3001, 3001, ((7, 30),)),),
    "lucky": (Phase(311, 311),) + (Phase(312, 312, ((4, 4),)),) * 8
             + (Phase(313, 313),),
    "brian": (Phase(810, 810, ((6, 29),)),),
}


def _frames(phase, air):
    frames = list(air[phase.action][0])
    if not frames:
        raise ValueError(f"normal throw: empty action {phase.action}")
    # Some imported AIRs dropped elements that the CNS still references.
    # Extend with the last resident pose, using a bounded transition tick.
    while len(frames) < phase.minimum_elements:
        g, n, x, y, _t, flip, atk, hurt = frames[-1]
        frames.append((g, n, x, y, 3, flip, atk, hurt))
    last = len(frames) - 1 if phase.last is None else phase.last
    if not 0 <= phase.first <= last < len(frames):
        raise ValueError(f"normal throw: invalid phase {phase}")
    return frames, last


def _local_element(trigger, frames):
    if not trigger & 0x80:
        return trigger
    # Exact state-time events must move with their phase after flattening.
    tick = trigger & 0x7F
    elapsed = 0
    for index, frame in enumerate(frames):
        elapsed += min(frame[4], 32)
        if tick < elapsed:
            return index
    return len(frames) - 1


def repair(name, cfg, anims, air, moves, headers, statedefs, binds, acts, posadds):
    """Repair slot 75 after calibration, voices and late overrides.

    Return False for the 31 unaffected roster entries. Synthetic data is
    local to this character build; original special/victim states stay intact.
    """
    phases = PLANS.get(name)
    if phases is None:
        return False
    if STATE in headers or ACTION in air:
        raise ValueError("normal throw: reserved state/action collision")
    resident = air[anims[75]][0]
    if not resident:
        raise ValueError(f"{name}: normal throw has no resident art")

    timeline, damage, windows, actions, positions = [], [], [], [], []
    for phase in phases:
        source, last = _frames(phase, air)
        offset = len(timeline)
        if offset:
            # A flattened phase still has the source state's entry VelSet
            # (notably Ryo 811 stops the jump/rush before the slam).
            velocity = headers.get(phase.state, {}).get("velset", "").split(",")
            if len(velocity) == 2:
                try:
                    vx, vy = map(float, velocity)
                except ValueError:
                    pass
                else:
                    vx = round(vx / cfg.get("coord_scale", 1))
                    vy = round(vy * 4)
                    if not (-128 <= vx <= 127 and -128 <= vy <= 127):
                        raise ValueError(f"{name}: unencodable throw entry velocity")
                    actions.extend([(offset, 5, vx & 255, 0),
                                    (offset, 15, vy & 255, 0)])
        selected = source[phase.first:last + 1]
        for frame in selected:
            # Loop/negative-duration holds are not exits in native StThrow.
            g, n, x, y, ticks, flip, atk, hurt = frame
            timeline.append((g, n, x, y, min(ticks, 32), flip, atk, hurt))
        for element, hp in phase.hits:
            if not phase.first <= element <= last or not 0 < hp <= 128:
                raise ValueError(f"{name}: unreachable or unencodable throw damage")
            damage.append((offset + element - phase.first, 3, -hp, 0))
        for lo, hi, dx, dy in binds.get(phase.state, ()):
            lo, hi = max(lo, phase.first), min(hi, last)
            if lo <= hi:
                windows.append((offset + lo - phase.first,
                                offset + hi - phase.first, dx, dy))
        for trigger, op, arg, cond in acts.get(phase.state, ()):
            # Discard old damage, custom victim states, source self-turns,
            # invulnerability and hit latches.  op2 is TargetFacing: the
            # victim Turn rows extracted by wire_throw_chain are injected as
            # op2, so keep them in the flattened timeline.  A native throw
            # already owns the target and must preserve the chosen
            # front/back direction.
            if op not in (2, 5, 7, 10, 14, 15, 16, 17):
                continue
            element = _local_element(trigger, source)
            if phase.first <= element <= last:
                actions.append((offset + element - phase.first, op, arg, cond))
        for element, dx in posadds.get(phase.state, ()):
            if phase.first <= element <= last:
                positions.append((offset + element - phase.first, dx))

    # No new sprites/metasprites/CHR pages: map the restored source timeline
    # onto the existing throw art. Keep element count so events stay reachable.
    frames = []
    for index, frame in enumerate(timeline):
        art = resident[min(index * len(resident) // len(timeline), len(resident) - 1)]
        frames.append((art[0], art[1], art[2], art[3], frame[4], art[5], [], art[7]))
    if len(frames) >= 128 or sum(f[4] for f in frames) >= 450:
        raise ValueError(f"{name}: normal throw exceeds native timeline budget")
    # Fill gaps with the preceding hold. Do not inherit an unbounded source
    # window beyond its phase or a conditional TargetBind from another move.
    held = [(24, 0)] * len(frames)
    for lo, hi, dx, dy in windows:
        for index in range(lo, hi + 1):
            held[index] = (dx, dy)
    for index in range(1, len(held)):
        if not any(lo <= index <= hi for lo, hi, _x, _y in windows):
            held[index] = held[index - 1]
    # Chizuru's dynamic bind expression wasn't representable by parse_cns.
    if name == "chizuru":
        held = [(25 if i < 6 else 35 if i < 8 else 45, 0)
                for i in range(len(frames))]

    air[ACTION] = (frames, -1)
    anims[75] = cfg.setdefault("anims", {})[75] = ACTION
    cfg.setdefault("moves", {})[75] = STATE
    cfg.get("slices", {}).pop(75, None)
    headers[STATE] = {"type": "S", "movetype": "A", "physics": "N",
                      "anim": str(ACTION), "velset": "0,0"}
    statedefs[STATE] = [{"type": "ChangeState", "value": "0",
                        "triggers": ["AnimTime = 0"],
                        "trigger_groups": ["trigger1"]}]
    binds[STATE] = [(i, i, dx, dy) for i, (dx, dy) in enumerate(held)]
    acts[STATE] = sorted(set(actions + damage))
    posadds[STATE] = positions
    overrides = cfg.setdefault("hitdef_override", {})
    capture = dict(moves[800] if name == "mai" else moves[cfg["moves"][74]])
    capture.update(p1mugen=STATE, p2state=76, throw=1, damage=0, gdamage=0)
    overrides[74] = capture
    # Slot 75 runs only the held sequence; never apply a second melee HitDef.
    overrides[75] = {"active": 0, "damage": 0, "gdamage": 0,
                     "throw": 0, "p2state": 0xFF}
    # Returning to stand at animation end uses VH_free and the existing
    # BackThrowReleaseFar path; TargetState would bypass its back-throw push.
    return True
