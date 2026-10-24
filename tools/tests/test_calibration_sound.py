import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from calibration.sound import catalog


class SoundCatalogTests(unittest.TestCase):
    def test_preserves_sample_indices_and_runtime_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            char = root / "fighter"
            char.mkdir()
            (char / "fighter.cns").write_text(
                "[Statedef 200]\n"
                "[State 200, voice]\n"
                "type = PlaySnd\ntrigger1 = Time = 0\nvalue = S3,2\n"
                "[State 200, absent]\n"
                "type = PlaySnd\ntrigger1 = Time = 3\nvalue = 3,9\n"
                "[State 200, common]\n"
                "type = PlaySnd\ntrigger1 = Time = 4\nvalue = F5,0\n"
                "[State 200, effect]\n"
                "type = PlaySnd\ntrigger1 = Time = 5\nvalue = S0,0\n")
            data = bytearray(60)
            data[:12] = b"ElecbyteSnd\0"
            struct.pack_into("<II", data, 16, 1, 32)
            struct.pack_into("<IIII", data, 32, 0, 4, 3, 2)
            (char / "fighter.snd").write_bytes(data)
            cfg = {"cns": "fighter/fighter.cns", "moves": {5: 200}}
            parsed = [None] * 11
            parsed[9] = {200: [([], (3, 2)), ([], (3, 9))]}
            result = catalog(root, {"fighter": cfg}, lambda *args: parsed,
                             {(0, 0): 0}, {(5, 0): 4}, 40)
            fighter = result["characters"]["fighter"]
            self.assertEqual(fighter["samples"][0],
                             {"group": 3, "item": 2, "offset": 48, "bytes": 4})
            self.assertEqual(fighter["snd"], "fighter/fighter.snd")
            self.assertEqual(fighter["voice_count"], 2)
            rows = fighter["playsnd"]
            self.assertEqual([r["route"] for r in rows],
                             ["voice", "voice", "effect", "effect"])
            self.assertEqual([r["present"] for r in rows], [True, False, None, False])
            self.assertEqual([r["runtime_id"] for r in rows[:2]], [40, 41])
            self.assertEqual(rows[0]["uses"], [[200, 2]])
            self.assertEqual(json.loads(json.dumps(result))["schema"], 1)


if __name__ == "__main__":
    unittest.main()
