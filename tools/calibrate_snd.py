#!/usr/bin/env python3
"""Record character SND definitions in the calibration catalog."""
from pathlib import Path

import build_fight
from calibration.extract import json_bytes, write_if_changed
from calibration.sound import catalog


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets/calibration/snd.json"


def main():
    data = catalog(ROOT, build_fight.CHARS, build_fight.parse_cns,
                   build_fight.SND_TO_SFX, build_fight.COMMON_SND,
                   build_fight.VOICE_BASE)
    write_if_changed(OUTPUT, json_bytes(data))
    characters = data["characters"]
    print(f"{OUTPUT}: {len(characters)} characters, "
          f"{sum(len(c['samples']) for c in characters.values())} samples, "
          f"{sum(c['voice_count'] for c in characters.values())} voice IDs")


if __name__ == "__main__":
    main()
