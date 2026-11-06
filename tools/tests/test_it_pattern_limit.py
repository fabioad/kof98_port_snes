"""SNESMOD pattern bounds and lossless repacking of Fairy's 71 patterns."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from it_pattern_limit import decode_pattern, encode_pattern, fit_snesmod, layout
import approved_music
import validate_snesmod


class PatternLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'assets/audio/ffg/stg6.it').read_bytes()
        cls.fixed = fit_snesmod(cls.source)

    def test_fairy_fits_table_and_preserves_all_4517_rows(self):
        before = layout(self.source)[3]
        after = layout(self.fixed)[3]
        self.assertEqual(len(before), 71)
        self.assertEqual(len(after), 36)
        old_rows = sum((decode_pattern(self.source, p) for p in before), [])
        new_rows = sum((decode_pattern(self.fixed, p) for p in after), [])
        self.assertEqual(len(old_rows), 4517)
        self.assertEqual(old_rows, new_rows)
        self.assertEqual(self.source[48:192], self.fixed[48:192])  # tempo, volume, channels
        for pointer in after:
            self.assertLessEqual(len(decode_pattern(self.fixed, pointer)), 128)

    def test_instrument_sample_headers_and_pcm_bytes_stay_in_place(self):
        orders, instruments, samples, pointers = layout(self.source)
        end_tables = 192 + orders + 4*(instruments+samples+len(pointers))
        self.assertEqual(self.source[end_tables:], self.fixed[end_tables:len(self.source)])
        new_orders = layout(self.fixed)[0]
        old_tables = self.source[192+orders:192+orders+4*(instruments+samples)]
        self.assertEqual(old_tables, self.fixed[192+new_orders:192+new_orders+len(old_tables)])

    def test_other_reviewed_songs_are_unchanged_and_all_outputs_fit(self):
        for row in approved_music.modules():
            source = (approved_music.PACK / row['file']).read_bytes()
            with self.subTest(song=row['file']):
                fixed = fit_snesmod(source)
                self.assertLessEqual(len(layout(fixed)[3]), 64)
                if row['file'] != 'stg6.it':
                    self.assertEqual(source, fixed)

    def test_repacking_is_idempotent_and_installed_from_approved_source(self):
        self.assertEqual(fit_snesmod(self.fixed), self.fixed)
        row = next(row for row in approved_music.modules() if row['file'] == 'stg6.it')
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'stage.it'
            approved_music.install(row, target)
            self.assertEqual(target.read_bytes(), self.fixed)
            approved_music.install(row, target)
            self.assertEqual(target.read_bytes(), self.fixed)

    def test_mask_reuse_is_expanded_across_joined_pattern_boundaries(self):
        # Note+effect followed by reused note/effect without a new mask.
        packed = bytes([129, 0x09, 60, 17, 3, 0, 129, 0x90, 0, 1, 0])
        data = b'\0' + struct.pack('<HHI', len(packed), 3, 0) + packed
        rows = decode_pattern(data, 1)
        self.assertEqual(rows[0], rows[1])
        self.assertEqual(rows[1], rows[2])
        encoded = b'\0' + encode_pattern(rows + rows)
        self.assertEqual(decode_pattern(encoded, 1), rows + rows)

    def test_unmapped_pattern_flow_is_rejected(self):
        data = bytearray(self.source)
        data[192], data[193] = data[193], data[192]
        with self.assertRaisesRegex(ValueError, 'linear'):
            fit_snesmod(data)

    def test_validator_rejects_overflow_before_smconv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'overflow.it'
            path.write_bytes(self.source)
            with patch.object(validate_snesmod.subprocess, 'run') as convert:
                with self.assertRaisesRegex(SystemExit, '71 patterns exceeds the 64-pattern'):
                    validate_snesmod.main('unused', [str(path)])
                convert.assert_not_called()


if __name__ == '__main__':
    unittest.main()
