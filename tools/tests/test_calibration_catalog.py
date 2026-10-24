import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_fight
from calibration.catalog import generated_frames, slot_category
from calibration.extract import CANONICAL_DEFINITIONS, discover
from calibration.pipeline import generate
import test_menu_modes


class CatalogTests(unittest.TestCase):
    def test_generated_frames_exclude_header_and_other_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'build/gen_fight'
            target.mkdir(parents=True)
            (target / 'test_spr.inc').write_text(
                'testAnim48:\n    .db 2,0\n'
                '    .dw 8\n    .db 3,0,0,0,1,2\n'
                '    .dw 9\n    .db 255,0,0,0,0,2\n'
                'testDamageTab:\n    .dw 99\n'
                'testAnim49:\n    .db 1,0\n'
                '    .dw 9\n    .db 5,0,0,0,0,2\n')
            data = generated_frames(tmp, 'test')
            self.assertEqual([f['ticks'] for f in data[48]], [3, 255])
            self.assertEqual([f['attack_box'] for f in data[48]], [1, 0])
            self.assertEqual(len(data[49]), 1)

    def test_split_metasprite_upload_length(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'build/gen_fight'
            target.mkdir(parents=True)
            (target / 'test_spr.inc').write_text(
                'testAnim48:\n    .db 1,0\n'
                '    .dw 0\n    .db 3,0,0,0,1,2\n')
            (target / 'test_meta.inc').write_text(
                'testSprData:\n    .db $01,$00,$00,$80,$07\n')
            self.assertEqual(generated_frames(tmp, 'test')[48][0]['upload_bytes'],
                             1920)

    def test_deduplicated_animation_aliases_are_not_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'build/gen_fight'
            target.mkdir(parents=True)
            (target / 'test_spr.inc').write_text(
                'testAnimTab:\n    .dw testAnim0\n    .dw testAnim0\n'
                'testAnim0:\n    .db 1,0\n'
                '    .dw 0\n    .db 5,0,0,0,0,2\n')
            records = generated_frames(tmp, 'test')
            self.assertEqual(records[0], records[1])
            self.assertEqual(len(records[1]), 1)

    def test_native_slot_labels_do_not_claim_arcade_move_names(self):
        self.assertEqual(slot_category(5), 'normal')
        self.assertEqual(slot_category(58), 'special_or_followup')
        self.assertEqual(slot_category(85), 'super_slot')
        self.assertEqual(slot_category(97), 'system_or_pose')

    def test_generation_does_not_accept_silently_skipped_characters(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            with patch('calibration.pipeline.run') as run:
                def skipped(*args):
                    (stage / 'generation.log').write_text('kyo: SKIPPED (ValueError: stale)\n')
                run.side_effect = skipped
                with self.assertRaisesRegex(ValueError, 'incomplete roster'):
                    generate(stage, stage, [], build_fight)
                self.assertEqual(run.call_args.args[0][1],
                                 stage / 'tools/build_fight.py')

    def test_versus_setup_rejects_accidental_campaign_mode(self):
        class WrongMode:
            def read_ram(self, address, size):
                return bytes([6 if address == 0x1020 else 1])
        with patch('test_menu_modes.press'), patch('test_menu_modes.t.wait_for'):
            with self.assertRaisesRegex(AssertionError, 'wrong game mode'):
                test_menu_modes.enter_mode(WrongMode(), 1)

    def test_canonical_aliases_are_mapped_once(self):
        root = Path(__file__).resolve().parents[2]
        records = discover(root / 'assets/characters', build_fight.CHARS)
        for name in CANONICAL_DEFINITIONS:
            matches = [r for r in records if r['native'] == name]
            self.assertEqual(len(matches), 1, name)
            expected = (root / 'assets/characters' /
                        CANONICAL_DEFINITIONS[name]).resolve()
            self.assertEqual(Path(matches[0]['path']).resolve(), expected)


if __name__ == '__main__':
    unittest.main()
