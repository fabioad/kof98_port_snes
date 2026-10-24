#!/usr/bin/env python3
"""Build the character-select theme as a SNESMOD-compatible IT module."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_stage_music import MUSIC, build_module  # noqa: E402


def main():
    midi = "The_King_of_Fighters.mid"
    out_it = os.path.join(ROOT, "assets/audio/menu/kof.it")
    build_module(midi, out_it)
    print(f"menu KOF: {out_it} -> {os.path.getsize(out_it)}B")


if __name__ == "__main__":
    main()
