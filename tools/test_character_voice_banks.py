#!/usr/bin/env python3
"""Robert and Mr. Karate must read their own .snd voice banks.

Robert-KOF98 ships two sample banks in the same directory: the original
``Robert.snd`` and the processed ``Robert-Mr-Karate.snd``.  The voice builder
used to take the first .snd in directory order, so normal Robert played the
pitched-down/echoed Mr. Karate voices.  This static check pins the resolved
banks without booting the emulator.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_fight as bf                                      # noqa: E402


def main():
    robert = bf.voice_snd_path("robert")
    karate = bf.voice_snd_path("mrkarate")
    assert robert, "Robert has no .snd bank"
    assert karate, "Mr. Karate has no .snd bank"
    assert Path(robert).name == "Robert.snd", robert
    assert Path(karate).name in ("MrKarate.snd", "Robert-Mr-Karate.snd"), karate
    assert Path(robert) != Path(karate), (robert, karate)
    assert Path(robert).exists() and Path(karate).exists()
    assert (Path(robert).read_bytes() != Path(karate).read_bytes()), \
        "variant bank is a copy of the original"
    print(f"PASS voice banks: Robert -> {Path(robert).name}, "
          f"Mr. Karate -> {Path(karate).name}")


if __name__ == "__main__":
    main()
