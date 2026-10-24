"""Snapshot of MUGEN SND indices and the PlaySnd routes used by the SNES port."""
import re
from pathlib import Path

from . import mugen


VALUE = re.compile(r"([fFsS]?)\s*(-?\d+)\s*,\s*(-?\d+)")


def catalog(root, configs, parse_cns, self_effects, common_effects, voice_base):
    root = Path(root)
    characters = {}
    for name, cfg in configs.items():
        cns = root / cfg["cns"]
        snd_files = sorted((root / cfg["cns"]).parent.glob("*.[sS][nN][dD]"))
        snd = snd_files[0] if snd_files else None
        entries = mugen.binary_metadata(snd, "sound")["entries"] if snd else []
        available = {(row["group"], row["number"]) for row in entries}
        playable = set(cfg.get("moves", {}).values())

        # Follow the generator's state/controller order so these IDs match
        # the indices embedded in the per-character voice table.
        parsed = parse_cns(str(cns), cfg.get("coord_scale", 1),
                           cfg.get("damage_scale", 1))
        voice_ids = {}
        for state, controllers in parsed[9].items():
            for _, sound in controllers:
                if (isinstance(sound, tuple) and state in playable and
                        sound not in voice_ids and len(voice_ids) < 200):
                    voice_ids[sound] = len(voice_ids)

        playsnd = {}
        states, _, _, _ = mugen.states([cns])
        for state in states.values():
            for controller in state["controllers"]:
                if controller["type"] != "playsnd":
                    continue
                value = mugen.values(controller).get("value", "")
                match = VALUE.match(value.strip())
                if match:
                    bank = match[1].lower() or "s"
                    pair = (int(match[2]), int(match[3]))
                    key = (bank, *pair)
                    if key in playsnd:
                        playsnd[key]["uses"].append(
                            [state["id"], controller["source"]["line"]])
                        continue
                    effects = common_effects if bank == "f" else self_effects
                    row = {"bank": bank, "group": pair[0], "item": pair[1],
                           "present": (pair in available if bank == "s" else None)}
                    if pair in effects:
                        row.update(route="effect", effect_id=effects[pair])
                    elif bank == "s" and pair in voice_ids:
                        row.update(route="voice", voice_id=voice_ids[pair],
                                   runtime_id=voice_base + voice_ids[pair])
                    else:
                        row["route"] = "not_imported"
                else:
                    key = ("dynamic", value)
                    row = playsnd.get(key, {"value": value, "route": "dynamic_value"})
                row.setdefault("uses", []).append(
                    [state["id"], controller["source"]["line"]])
                playsnd[key] = row

        def relative(path):
            return path.relative_to(root).as_posix()

        characters[name] = {
            "cns": relative(cns),
            "cns_sha256": mugen.sha(cns),
            "snd": relative(snd) if snd else None,
            "snd_sha256": mugen.sha(snd) if snd else None,
            "samples": [{"group": row["group"], "item": row["number"],
                         "offset": row["offset"], "bytes": row["size"]}
                        for row in entries],
            "voice_count": len(voice_ids),
            "playsnd": list(playsnd.values()),
        }
    return {"schema": 1, "characters": characters}
