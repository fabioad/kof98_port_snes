"""Per-character close/far standing normal table (KOF '98 source data).

Each entry is ``button -> (close_state, far_state, p2bodydist_x)``.  The
source `.cmd` files gate the close variant with ``p2bodydist X <= N`` and
fall back to the far state otherwise; ``N`` is the raw source threshold in
MUGEN body-distance units (edge-to-edge, already divided by the port's
coordinate scale where needed).

Buttons are the MUGEN command names: x = light punch, y = strong punch,
a = light kick, b = strong kick.  A button missing from a character's dict
has no close variant in that source (the far state always plays).

``CLOSE_CLONES`` names close states that do not exist as separate statedefs
and must be cloned from a shared source state with a fixed header anim (the
source selects the anim per button inside the state).  Chizuru is the only
current case.
"""

CLOSE_NORMALS = {
    "terry":      {"x": (205, 200, 16), "y": (215, 210, 34),
                   "a": (235, 230, 28), "b": (245, 240, 48)},
    "andy":       {"x": (205, 200, 27), "y": (215, 210, 27),
                   "a": (235, 230, 27), "b": (245, 240, 22)},
    "joe":        {"x": (205, 200, 21), "y": (215, 210, 26),
                   "a": (235, 230, 24), "b": (245, 240, 26)},
    "ryo":        {"x": (205, 200, 26), "y": (215, 210, 31),
                   "a": (235, 230, 23), "b": (245, 240, 41)},
    "robert":     {"x": (205, 200, 21), "y": (215, 210, 22),
                   "a": (235, 230, 26), "b": (245, 240, 31)},
    # Yuri/Ralf select the far state from inside the state (ChangeState at
    # time=0); the close states are the root of each pair.
    "yuri":       {"x": (200, 201, 25), "y": (202, 203, 35),
                   "a": (204, 205, 25), "b": (206, 207, 35)},
    "athena":     {"x": (205, 200, 18), "y": (215, 210, 25),
                   "b": (245, 240, 25)},
    "kensou":     {"y": (250, 240, 15), "a": (230, 220, 15),
                   "b": (270, 260, 15)},
    "chin":       {"x": (205, 200, 20), "y": (215, 210, 20),
                   "a": (235, 230, 20), "b": (245, 240, 20)},
    "king":       {"x": (200, 250, 20), "y": (210, 260, 25),
                   "a": (220, 270, 18), "b": (230, 280, 20)},
    "mai":        {"x": (200, 205, 14), "y": (210, 215, 34),
                   "a": (220, 225, 15), "b": (230, 235, 15)},
    # Chizuru: state 200/240 pick their anim from the command inside the
    # state.  Far states are already cloned by gen_char_cfg; the close
    # states below are cloned the same way with a fixed header anim.
    "chizuru":    {"x": (241, 200, 15), "y": (242, 202, 15),
                   "a": (243, 201, 15), "b": (244, 203, 15)},
    "kim":        {"x": (205, 200, 19), "y": (215, 210, 24),
                   "a": (235, 230, 18), "b": (245, 240, 21)},
    "chang":      {"x": (205, 200, 20), "y": (215, 210, 20),
                   "a": (235, 230, 20), "b": (246, 240, 20)},
    "choi":       {"x": (205, 200, 20), "y": (215, 210, 20),
                   "a": (235, 230, 20)},
    "yashiro":    {"x": (205, 200, 20), "y": (215, 210, 32),
                   "a": (235, 230, 20), "b": (245, 240, 35)},
    "shermie":    {"y": (245, 240, 36)},
    "chris":      {"y": (245, 240, 36), "a": (225, 220, 42),
                   "b": (265, 260, 37)},
    "yamazaki":   {"x": (205, 200, 31), "y": (215, 210, 32),
                   "a": (235, 230, 23), "b": (245, 240, 40)},
    "mary":       {"x": (201, 200, 15), "y": (215, 210, 20),
                   "a": (236, 230, 10), "b": (246, 240, 20)},
    "billy":      {"x": (201, 200, 25), "y": (221, 220, 25),
                   "a": (211, 210, 45), "b": (231, 230, 10)},
    "lucky":      {"x": (210, 200, 10), "y": (250, 240, 15),
                   "a": (230, 220, 30), "b": (270, 260, 10)},
    "heavyd":     {"x": (205, 200, 10), "y": (215, 210, 10),
                   "a": (235, 230, 10), "b": (245, 240, 10)},
    "brian":      {"x": (205, 200, 24), "y": (225, 220, 24),
                   "a": (215, 210, 24), "b": (235, 230, 24)},
    "geese":      {"x": (205, 200, 21), "y": (215, 210, 26),
                   "a": (235, 230, 23), "b": (245, 240, 29)},
    "krauser":    {"x": (205, 200, 32), "y": (215, 210, 59),
                   "a": (235, 230, 55), "b": (245, 240, 37)},
    "mrbig":      {"x": (205, 200, 32), "y": (215, 210, 32),
                   "a": (235, 230, 18), "b": (245, 240, 39)},
    "eiji":       {"x": (205, 200, 16), "y": (215, 210, 32),
                   "a": (235, 230, 32), "b": (245, 240, 44)},
    "vega":       {"x": (205, 200, 21), "y": (215, 210, 21),
                   "a": (235, 230, 21), "b": (245, 240, 37)},
    "ryu":        {"x": (205, 200, 11), "y": (215, 210, 29),
                   "a": (235, 230, 20), "b": (245, 240, 43)},
    "ken":        {"x": (205, 200, 11), "y": (215, 210, 19),
                   "a": (235, 230, 20), "b": (245, 240, 43)},
    "chunli":     {"x": (205, 200, 25), "y": (215, 210, 25),
                   "a": (235, 230, 25), "b": (245, 240, 25)},
    "sakura":     {"x": (205, 200, 18), "y": (215, 210, 24),
                   "a": (235, 230, 16), "b": (245, 240, 36)},
    "iori":       {"x": (205, 200, 20), "y": (215, 210, 32),
                   "a": (235, 230, 21), "b": (245, 240, 37)},
    "kyo":        {"x": (205, 200, 21), "y": (215, 210, 39),
                   "a": (235, 230, 21), "b": (245, 240, 37)},
    "kyonests":   {"x": (205, 200, 21), "y": (215, 210, 39),
                   "a": (235, 230, 21), "b": (245, 240, 37)},
    "kyoash":     {"x": (205, 200, 21), "y": (215, 210, 39),
                   "a": (235, 230, 21), "b": (245, 240, 37)},
    "shingo":     {"x": (205, 200, 21), "y": (215, 210, 39),
                   "a": (235, 230, 21), "b": (245, 240, 37)},
    "rugal":      {"x": (205, 200, 21), "y": (215, 210, 48),
                   "a": (235, 230, 24), "b": (245, 240, 40)},
    "omegarugal": {"x": (201, 200, 30), "y": (211, 210, 30),
                   "a": (231, 230, 30), "b": (241, 240, 30)},
    "saisyu":     {"x": (205, 200, 4), "y": (215, 210, 28),
                   "a": (235, 230, 25), "b": (245, 240, 48)},
    "heidern":    {"x": (205, 200, 21), "y": (215, 210, 28),
                   "a": (235, 230, 21), "b": (245, 240, 40)},
    "takuma":     {"x": (205, 200, 16), "y": (215, 210, 30),
                   "a": (235, 230, 21), "b": (245, 240, 42)},
    "clark":      {"x": (205, 200, 16), "y": (215, 210, 37),
                   "a": (235, 230, 16), "b": (245, 240, 37)},
    "ralf":       {"y": (202, 203, 35), "a": (204, 205, 15),
                   "b": (206, 207, 35)},
    "leona":      {"x": (205, 200, 19), "y": (225, 220, 19),
                   "a": (215, 210, 19), "b": (235, 230, 19)},
    "mature":     {"y": (210, 211, 20), "b": (230, 231, 20)},
    "vice":       {"y": (210, 260, 25), "a": (220, 270, 18),
                   "b": (230, 280, 20)},
    "benimaru":   {"x": (205, 200, 19), "y": (215, 210, 23),
                   "a": (235, 230, 16), "b": (245, 240, 37)},
    "daimon":     {"x": (205, 200, 34), "y": (215, 210, 41),
                   "a": (235, 230, 34), "b": (245, 240, 28)},
}

# source statedef -> (clone statedef, fixed header anim)
CLOSE_CLONES = {
    "chizuru": [(240, 241, 240), (240, 242, 250),
                (240, 243, 260), (240, 244, 270)],
}

# Runtime close-normal sids.  Keep in sync with src/engine/fight.asm.
# 82/83/93/98 are unused state slots in the classic 0..97 table; 98 is free
# except for Iori and Mary, whose close strong kick uses 112 instead.  The
# engine moved ANIM_TRIP to slot 44 so sid 93 can carry close light kick.
CLOSE_SIDS = {"x": 82, "y": 83, "a": 93, "b": 98}
CLOSE_SID_FALLBACK = 112

# Alternate Kyo forms duplicate the base character's close data; the 8 MiB
# ExHiROM budget cannot hold a second copy of every close-normal clip.  They
# keep the shared far normals (Kyo itself has the full close set).
CLOSE_NORMAL_SKIP = {"kyonests", "kyoash"}

BUTTON_ORDER = ("x", "y", "a", "b")


def close_sids_for(name, moves):
    """Fixed button -> close sid mapping.

    The engine's CancelGate maps a close sid back to the far normal's cancel
    row, so the slot must always belong to the same button even for partial
    sets (Shermie's close HP is sid 83, not the low free slot 82).
    """
    tab = CLOSE_NORMALS.get(name, {})
    out = {}
    for btn in BUTTON_ORDER:
        if btn not in tab:
            continue
        out[btn] = (CLOSE_SID_FALLBACK if btn == "b" and 98 in moves
                    else CLOSE_SIDS[btn])
    return out

