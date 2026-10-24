#!/usr/bin/env python3
"""Merge a MUGEN char's .cns/.def state files into a single X_SNES.cns.

Replicates the Kyo_SNES.cns/Iori_SNES.cns layout: a [Quotes] block lifted
from the base file, then each source file verbatim under a
"; ===== from FILE =====" marker in .def order:

    St, St1, St2, St3, St4, St5 (Helper), St7 (Member), St6 (Config),
    Cns (Constants), StCommon (common_kof)

Usage: merge_cns.py assets/characters/Shingo-KOF98/Shingo-KOF98.def
"""
import os
import re
import sys


def read(path):
    raw = open(path, "rb").read()
    return raw.decode("shift_jis", errors="replace")


def main():
    deffile = sys.argv[1]
    root = os.path.dirname(deffile)
    base = os.path.splitext(os.path.basename(deffile))[0]
    char = base.split("-")[0]

    slots = {}
    for line in read(deffile).splitlines():
        m = re.match(r"\s*([A-Za-z0-9]+)\s*=\s*(\S+)", line)
        if m:
            slots[m.group(1).upper()] = m.group(2)

    order = ["ST", "ST1", "ST2", "ST3", "ST4",
             "ST5", "ST7", "ST6", "CNS", "STCOMMON"]
    files = [slots[k] for k in order if k in slots]
    # Marker order in the existing _SNES.cns files puts Member before
    # Config; Constants.cns follows Config.
    header = ("; Merged/sanitized CNS for the SNES port (generated)\n"
              "; Sources (precedence order): "
              + ", ".join(files) + "\n\n")

    out = [header]
    base_txt = read(os.path.join(root, slots["ST"]))
    m = re.search(r"\[Quotes\](.*?)(?=\n\[|\Z)", base_txt, re.S | re.I)
    if m:
        out.append("[Quotes]\n" + m.group(1).strip() + "\n\n\n")
    for fn in files:
        txt = read(os.path.join(root, fn))
        out.append(f"; ===== from {fn} =====\n\n" + txt.strip() + "\n\n")

    dest = os.path.join(root, f"{char}_SNES.cns")
    # build_fight.py's parse_cns reads UTF-8
    open(dest, "w", encoding="utf-8").write("".join(out))
    print(f"{dest}: {sum(o.count(chr(10)) for o in out)} lines")


if __name__ == "__main__":
    main()
