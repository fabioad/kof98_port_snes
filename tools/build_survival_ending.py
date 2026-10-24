#!/usr/bin/env python3
"""Build the SURVIVOR ending theme from assets/survival_ending."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_stage_music import build_module  # noqa: E402


def main():
    midi = os.path.join(ROOT, "assets/survival_ending/kof00_crystal.mid")
    out_it = os.path.join(ROOT, "assets/audio/menu/crystal.it")
    build_module(midi, out_it)
    print(f"survival ending: {out_it} -> {os.path.getsize(out_it)}B")


if __name__ == "__main__":
    main()
