#!/usr/bin/env python3
"""Extract the statedef closure reachable from a set of seed states.

Writes a .cns containing only the [Statedef N] blocks reachable via
ChangeState/SelfState ``value =`` from the seeds -- used as trim_air's
--refs input so the 655-element AIR budget counts only the anims the SNES
engine can actually display.

Usage: filter_cns.py MERGED.cns OUT.cns SEED[,SEED...]
"""
import re
import sys

SYS = {-1, -2, -3, 0, 10, 11, 12, 20, 21, 40, 41, 42, 43, 47, 100, 105,
       110, 120, 130, 131, 132, 140, 141, 142, 143, 150, 151, 152, 160,
       170, 180, 181, 182, 183, 184, 190, 191, 192, 193, 194, 195, 196,
       5000, 5001, 5010, 5020, 5030, 5035, 5040, 5050, 5070, 5071,
       5080, 5081, 5090, 5100, 5101, 5110, 5111, 5120, 5130, 5150, 5151,
       5160, 5170, 5171, 5200, 5210, 5300, 5310, 5400, 5500, 5510, 5600,
       5610, 5611, 5612, 5615, 5616, 5617, 5619, 5631, 5650, 5661, 5700,
       5900, 5911, 5940, 5950, 5960, 5961, 5970, 5980, 5990, 6000, 6051,
       6060, 6061, 6500, 6501, 6505, 6510, 6511, 7000, 7001, 7010, 7011,
       7500, 7503, 7530, 7533, 8000, 8001, 8005, 8100, 8101, 8105, 8110,
       8111, 8120, 8130, 8200, 8210, 8220, 8240, 8300, 8900}


def main():
    src, out, seeds = sys.argv[1], sys.argv[2], sys.argv[3]
    txt = open(src, encoding="shift_jis", errors="replace").read()
    blocks = re.split(r"(?i)(?=\[statedef\s+-?\d+\])", txt)
    sdefs = {}
    for b in blocks:
        m = re.match(r"\[statedef\s+(-?\d+)\]", b, re.I)
        if m and int(m.group(1)) not in sdefs:
            sdefs[int(m.group(1))] = b

    want = {int(s) for s in seeds.split(",")} | SYS
    seen = set()
    stack = list(want)
    while stack:
        s = stack.pop()
        if s in seen or s not in sdefs:
            continue
        seen.add(s)
        for t in re.finditer(
                r"(?im)^\s*value\s*=\s*(-?\d+)\s*$", sdefs[s]):
            stack.append(int(t.group(1)))

    with open(out, "w", encoding="shift_jis", errors="replace") as f:
        f.write("; reachable statedef closure (generated)\n\n")
        for n in sorted(seen):
            f.write(sdefs[n].rstrip() + "\n\n")
    print(f"{out}: {len(seen)} statedefs kept of {len(sdefs)}")


if __name__ == "__main__":
    main()
