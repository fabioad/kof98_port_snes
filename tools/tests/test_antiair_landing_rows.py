import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
# 46/66 are backdash/counter specials, 76/77 are the engine's throw victims;
# their 255-tick holds are owned by other state handlers, not by TransAir.
NON_ANTIAIR = {46, 66, 76, 77}


def body(lines, label):
    start = next((i for i, line in enumerate(lines)
                  if line.startswith(label + ":")), None)
    if start is None:
        return []
    out = []
    for line in lines[start + 1:]:
        if line and not line.startswith((" ", "\t")):
            break
        out.append(line.strip())
    return out


def parse_char(path):
    with open(path) as source:
        lines = source.read().splitlines()
    anim_tab = body(lines, os.path.basename(path).replace("_spr.inc", "") +
                    "AnimTab")
    anims = []
    for line in anim_tab:
        m = re.search(r"\.dw\s+(\w+Anim\d+)", line)
        if m:
            anims.append(m.group(1))
    last_ticks = {}
    for name in anims:
        ticks = []
        for line in body(lines, name):
            if not line.startswith(".db"):
                continue
            parts = [p.strip() for p in line.split(".db", 1)[1].split(",")]
            if len(parts) >= 6 and parts[0].isdigit():
                ticks.append(int(parts[0]))
        if ticks:
            last_ticks[name] = ticks[-1]

    rising = set()
    for line in body(lines, os.path.basename(path).replace("_spr.inc", "") +
                     "ActTab"):
        m = re.search(r"\.dw\s+(\w+Act\d+)", line)
        if not m:
            continue
        sid = int(re.search(r"Act(\d+)", m.group(1)).group(1))
        for row in body(lines, m.group(1)):
            if not row.startswith(".db"):
                continue
            parts = [p.strip().replace("$", "0x")
                     for p in row.split(".db", 1)[1].split(",")]
            if len(parts) >= 3 and int(parts[1], 0) == 15:
                arg = int(parts[2], 0)
                if arg >= 128:
                    arg -= 256
                if arg < 0:
                    rising.add(sid)

    char = os.path.basename(path).replace("_spr.inc", "")
    ev = body(lines, char + "EVelTab")
    i = 0
    while i + 1 < len(ev):
        row = ev[i]
        if not row.startswith(".db") or "$FF" in row:
            break
        try:
            sid = int(row.split(".db", 1)[1].strip(), 0)
        except ValueError:
            break
        m = re.search(r"\.dw\s+\$([0-9A-Fa-f]+),\$([0-9A-Fa-f]+)",
                      ev[i + 1])
        if m:
            vy = int(m.group(2), 16)
            if vy >= 32768:
                vy -= 65536
            if vy < 0:
                rising.add(sid)
        i += 2

    landing = set()
    tr = body(lines, char + "TransTab")
    i = 0
    while i + 1 < len(tr):
        if not tr[i].startswith(".db"):
            break
        parts = tr[i].split(".db", 1)[1].split(",")
        try:
            fsid = int(parts[0], 0)
        except ValueError:
            break
        if int(parts[2], 0) == 1:
            landing.add(fsid)
        i += 2
    return [(sid, last_ticks.get(name)) for sid, name in enumerate(anims)
            if last_ticks.get(name) == 255 and sid in rising
            and sid not in landing and sid not in NON_ANTIAIR]


class AntiAirLandingRowsTests(unittest.TestCase):
    def test_no_rising_move_holds_after_landing(self):
        bad = []
        for path in sorted(glob.glob(os.path.join(
                ROOT, "build", "gen_fight", "*_spr.inc"))):
            char = os.path.basename(path).replace("_spr.inc", "")
            if char in ("cancel_data", "reflect_tab", "max_masks"):
                continue
            for sid, ticks in parse_char(path):
                bad.append((char, sid))
        self.assertEqual(bad, [], f"rising moves without a kind-1 landing "
                                  f"row: {bad}")


if __name__ == "__main__":
    unittest.main()
