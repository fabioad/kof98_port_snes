#!/usr/bin/env python3
"""Verify the four victory-quote languages render on the match-over screen.

Runs one Terry vs Iori match per language, writes Q_LANG before the KO and
decodes rows 12/14 of the HUD tilemap.  Each rendered pair must match one of
the JSON quotes for that language.

Usage: python3 tools/test_quotes_headless.py --launch
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_fight as bf                                  # noqa: E402
import test_fight_remote as t                             # noqa: E402
from test_roster import (parse_tables, press, to_select,  # noqa: E402
                         lock_side, W_CPU2, W_LOCK1, W_LOCK2)

HUDMAP = 0x4700
NEXTFLAG = 0x1084
Q_LANG = 0xF07F
WINS1 = 0x1080
FP2_HP = 0x4050

# Terry (id 15) is the first mass-import row; Iori is a fixed descriptor.
P1_ID, P2_ID = 15, 1


def decode_row(ra, row):
    raw = ra.read_ram(HUDMAP + row * 64, 64)
    ids = [raw[i] for i in range(0, 64, 2)]
    while ids and ids[0] == 0:
        ids.pop(0)
    while ids and ids[-1] == 0:
        ids.pop()
    return "".join(bf.CHARSET[i] if i < len(bf.CHARSET) else "?"
                   for i in ids)


def expected_pairs(name, tag):
    out = []
    for quote in bf.load_quote_db()[tag][name]:
        lines = bf.wrap_quote(bf.normalize_quote(quote))
        out.append(tuple(lines + [""] * (2 - len(lines))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--retroarch", default="retroarch")
    ap.add_argument("--core", default=t.CORE)
    args = ap.parse_args()

    roster = parse_tables()
    langs = [(fname, tag) for fname, tag in bf.QUOTE_LANGS]
    want = {tag: expected_pairs("terry", tag) for _fname, tag in langs}

    ra = t.RetroArch()
    try:
        if args.launch:
            ra.launch(args.retroarch, args.core)
        ra.wait_ready()
        to_select(ra)
        for lang_index, (_fname, tag) in enumerate(langs):
            if ra.read_ram(W_CPU2, 1)[0] != 0:
                press(ra, 1, "START", settle=0.25)
            # Set the language before the match starts: StartFight must keep
            # it, otherwise its stage-music load wipes Q_LANG back to 0.
            ra.command(f"WRITE_CORE_RAM {Q_LANG:X} {lang_index:02X}")
            time.sleep(0.1)
            lock_side(ra, 1, roster[P2_ID]["cell"], W_LOCK2)
            lock_side(ra, 0, roster[P1_ID]["cell"], W_LOCK1)
            t.wait_for(ra, lambda s: s["gamestate"] == 1, timeout=30)
            time.sleep(0.15)
            actual_lang = ra.read_ram(Q_LANG, 1)[0]
            if actual_lang != lang_index:
                raise AssertionError(
                    f"{tag}: Q_LANG {actual_lang} after match start, "
                    f"expected {lang_index} (wiped by stage music?)")
            ra.command(f"WRITE_CORE_RAM {WINS1:X} 01")
            ra.command(f"WRITE_CORE_RAM {FP2_HP:X} 00 00")
            t.wait_for(ra, lambda s: ra.read_ram(NEXTFLAG, 1)[0] == 2,
                       timeout=40, interval=0.05)
            time.sleep(0.15)
            pair = (decode_row(ra, 12), decode_row(ra, 14))
            print(f"{tag}: {pair!r}")
            if pair not in want[tag]:
                raise AssertionError(
                    f"{tag}: rendered {pair!r} is not one of {want[tag]!r}")
            print(f"  OK, one of {len(want[tag])} quotes")
            # Match-over screen: START returns to character select.
            press(ra, 0, "START", settle=0.25)
            t.wait_for(ra, lambda s: s["gamestate"] == 5, timeout=15)
            time.sleep(0.3)
        print("victory quotes: all languages OK")
    finally:
        ra.close()


if __name__ == "__main__":
    main()
