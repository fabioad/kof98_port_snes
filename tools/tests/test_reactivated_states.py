"""Command-state reactivation and case-insensitive asset path checks."""
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import build_fight as bf  # noqa: E402
from asset_paths import resolve  # noqa: E402


def cmd_targets(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    out = []
    for block in re.finditer(
            r"(?ims)^\s*\[State\s+-1,\s*([^\]]*)\]\s*(.*?)"
            r"(?=^\s*\[State\s+-1|\Z)", text):
        label = block.group(1).strip()
        value = re.search(r"(?im)^\s*value\s*=\s*(\d+)", block.group(2))
        if value:
            out.append((label, int(value.group(1))))
    return out


def is_attack_command(label):
    label = label.lower()
    if any(part in label for part in ("stand ", "crouch ", "jump ")):
        return False
    if label.startswith("sys_") or "throw" in label:
        return False
    if "blowback" in label or "taunt" in label:
        return False
    return True


class ReactivatedStatesTests(unittest.TestCase):
    def test_every_missing_attack_command_is_covered(self):
        for name, rows in bf.POST_CAL_REACTIVATED.items():
            cfg = bf.CHARS[name]
            wired = set(cfg["moves"].values())
            restored = {state for _sid, state, _anim in rows}
            disabled = bf.POST_CAL_REACTIVATED_DISABLED.get(name, set())
            missing = [
                (label, state)
                for label, state in cmd_targets(ROOT / cfg["cmd"])
                if is_attack_command(label)
                and state not in wired and state not in restored
                and state not in disabled
            ]
            self.assertEqual(missing, [], name)

    def test_reactivated_sids_do_not_overwrite_existing_rows(self):
        for name, rows in bf.POST_CAL_REACTIVATED.items():
            existing = set(bf.CHARS[name]["moves"])
            seen = set()
            overwrite = bf.POST_CAL_REACTIVATED_OVERWRITE.get(name, set())
            for sid, _state, _anim in rows:
                if sid not in overwrite:
                    self.assertNotIn(sid, existing, f"{name} sid {sid}")
                self.assertNotIn(sid, seen, f"{name} duplicate sid {sid}")
                seen.add(sid)

    def test_saisyu_and_clark_split_metasprite_banks(self):
        self.assertIn("saisyu", bf.SPLIT_OLD)
        self.assertIn("clark", bf.SPLIT_OLD)

    def test_max_overrides(self):
        self.assertIn(88, bf.MAX_SIDS_OVERRIDE["leona"])
        self.assertIn(87, bf.MAX_SIDS_OVERRIDE["chizuru"])
        self.assertEqual(set(bf.MAX_SIDS_OVERRIDE["mrbig"]), {88, 89})

    def test_case_insensitive_resolver(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "Paletas").mkdir()
            target = root / "Paletas" / "Chin-KOFM-6.ACT"
            target.write_bytes(b"x")
            got = Path(resolve(root, "paletas/chin-kofm-6.act"))
            self.assertEqual(got.resolve(), target.resolve())


if __name__ == "__main__":
    unittest.main()
