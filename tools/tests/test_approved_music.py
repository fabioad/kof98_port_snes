"""Guard approved arrangements against note drift and silently stale builds."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import approved_music as music
import validate_snesmod


def pattern_hash(data):
    orders, instruments, samples, patterns = struct.unpack_from('<4H', data, 32)
    table = 192 + orders + 4*(instruments+samples)
    pointers = struct.unpack_from(f'<{patterns}I', data, table)
    payload = data[192:192+orders]
    for ptr in pointers:
        payload += data[ptr:ptr+8+struct.unpack_from('<H', data, ptr)[0]] if ptr else b'EMPTY'
    return hashlib.sha256(payload).hexdigest()


class ApprovedMusicTests(unittest.TestCase):
    def test_all_production_sources_match_reviewed_notes_and_payloads(self):
        rows = music.modules()
        self.assertEqual(len(rows), 17)
        for row in rows:
            with self.subTest(song=row['file']):
                data = (music.PACK / row['file']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
                self.assertEqual(pattern_hash(data), row['patternSha256'])
                self.assertLessEqual(row['aramBytes'], validate_snesmod.MAX_MODULE_BYTES)

    def test_midi_routing_restores_exact_approved_module_without_converter(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'reordered-stage.it'
            midi = ROOT / 'music/Ryu-ko_Final.mid'
            self.assertTrue(music.install_for_midi(midi, target))
            self.assertEqual(target.read_bytes(), (music.PACK / 'stg8.it').read_bytes())
            target.write_bytes(b'stale generated file')
            self.assertTrue(music.install_for_midi(midi, target))
            self.assertEqual(target.read_bytes(), (music.PACK / 'stg8.it').read_bytes())

    def test_changed_midi_and_changed_pack_fail_before_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);pack = root / 'pack';pack.mkdir()
            midi = root / 'song.mid';midi.write_bytes(b'original notes')
            payload = pack / 'song.it';payload.write_bytes(b'approved arrangement')
            row = dict(file='song.it', midi='song.mid',
                       sha256=music.digest(payload), midiSha256=music.digest(midi))
            target = root / 'generated.it'
            with patch.object(music, 'ROOT', root), patch.object(music, 'PACK', pack):
                midi.write_bytes(b'new notes')
                with self.assertRaisesRegex(music.ApprovedMusicError, 'MIDI changed'):
                    music.install(row, target)
                self.assertFalse(target.exists())
                midi.write_bytes(b'original notes');payload.write_bytes(b'unreviewed samples')
                with self.assertRaisesRegex(music.ApprovedMusicError, 'Approved audio changed'):
                    music.install(row, target)
                self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
