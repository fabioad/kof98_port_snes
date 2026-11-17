#!/usr/bin/env python3
"""Mr. Karate keeps the secret form in every round of a CPU-vs-CPU match.

The round setup (StartFight -> MkSanitizeFar) used to convert the hidden
Robert form back to Robert as soon as both sides were CPU-driven, which is
exactly what the CPU-vs-CPU harnesses do after the selection.  Round one was
Mr. Karate and rounds two and three were Robert.  MkSelectFar now records the
human pick and the sanitizer honours it.

Run after a PVSnesLib build (the .msu file must sit next to the ROM):

    python3 tools/test_mrkarate_rounds_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from luta_cpu import (Core, DEFAULT_CORE, DEFAULT_ROM, GS, HP1, HP2, SEL1,
                      SEL2, WINS1, WINS2, boot_to_select, build_aliases,
                      load_roster, resolve, start_fight)  # noqa: E402

F_CHAR1 = 0x4000 + 44
MK, SAKURA = 53, 47


def main() -> None:
    roster = load_roster()
    aliases = build_aliases(roster)
    p1 = resolve("Mr. Karate", roster, aliases)
    p2 = resolve("Sakura", roster, aliases)
    assert p1.id == MK and p2.id == SAKURA, (p1, p2)

    core = Core(DEFAULT_CORE, DEFAULT_ROM)
    try:
        assert boot_to_select(core), (
            "Mr. Karate needs the .msu file next to kof98-snes.sfc")
        start_fight(core, p1, p2, level=8)

        descriptor = core.ram[F_CHAR1]
        assert descriptor != 0, "Mr. Karate descriptor was not loaded"

        rounds = 0
        last_gs = -1
        for _ in range(60 * 90):
            core.step()
            gs = core.ram[GS]
            if gs == 1 and last_gs != 1:
                rounds += 1
                assert core.ram[SEL1] == MK, (
                    f"round {rounds}: P1 became id {core.ram[SEL1]}")
                assert core.ram[SEL2] == SAKURA, (
                    f"round {rounds}: P2 became id {core.ram[SEL2]}")
                assert core.ram[F_CHAR1] == descriptor, (
                    f"round {rounds}: descriptor {core.ram[F_CHAR1]} "
                    f"replaced the Mr. Karate one ({descriptor})")
            last_gs = gs
            if gs == 1:
                # 2-1 match: P1 wins rounds 1 and 3, P2 takes round 2, so all
                # three rounds are rebuilt by StartFight.
                if rounds == 2:
                    core.ram[HP1] = 0
                else:
                    core.ram[HP2] = 0
            if core.ram[WINS1] >= 2 or core.ram[WINS2] >= 2:
                break

        assert rounds == 3, f"expected 3 rounds, saw {rounds}"
        print("PASS Mr. Karate: form kept in rounds 1, 2 and 3 "
              f"(descriptor {descriptor})", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    main()
