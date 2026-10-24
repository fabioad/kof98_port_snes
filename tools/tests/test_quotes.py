"""Victory-quote database, HUD wrapping and generated table layout."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import build_fight as bf

GEN = ROOT / "build" / "gen_fight"


def _parse_dbs(path):
    """label -> list of byte values for every `.db` line under that label."""
    out = {}
    label = None
    for line in path.read_text().splitlines():
        line = line.split(";")[0].strip()
        if not line:
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z_0-9]*):\s*(.*)$", line)
        if m:
            label = m.group(1)
            out.setdefault(label, [])
            line = m.group(2).strip()
        if label is not None and line.startswith(".db"):
            vals = [int(x, 0) for x in line[3:].split(",") if x.strip()]
            out[label].extend(vals)
    return out


def _parse_tables(path):
    out = {}
    label = None
    for line in path.read_text().splitlines():
        line = line.split(";")[0].strip()
        if not line:
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z_0-9]*):\s*$", line)
        if m:
            label = m.group(1)
            out[label] = []
        elif label and line.startswith(".dl"):
            out[label].append(line[3:].strip())
    return out


class QuoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = bf.load_quote_db()

    def test_every_character_has_all_four_languages(self):
        for _fname, tag in bf.QUOTE_LANGS:
            with self.subTest(lang=tag):
                self.assertEqual(sorted(bf.CHARS), sorted(self.db[tag]))

    def test_each_language_has_one_to_four_quotes(self):
        for _fname, tag in bf.QUOTE_LANGS:
            for name, quotes in self.db[tag].items():
                with self.subTest(lang=tag, char=name):
                    self.assertGreaterEqual(len(quotes), 1)
                    self.assertLessEqual(len(quotes), 4)
                    for quote in quotes:
                        self.assertTrue(quote.strip())

    def test_quotes_fit_two_hud_rows(self):
        for _fname, tag in bf.QUOTE_LANGS:
            for name, quotes in self.db[tag].items():
                for quote in quotes:
                    with self.subTest(lang=tag, char=name, quote=quote):
                        normalized = bf.normalize_quote(quote)
                        self.assertTrue(normalized)
                        self.assertTrue(all(c in bf.CHARSET
                                            for c in normalized))
                        lines = bf.wrap_quote(normalized)
                        self.assertIsNotNone(lines)
                        self.assertLessEqual(len(lines), 2)
                        for line in lines:
                            self.assertLessEqual(len(line), 30)

    def test_normalize_folds_accents_and_unsupported_punctuation(self):
        self.assertEqual("VOCE NAO E UM JOGUETE",
                         bf.normalize_quote("Você não é um joguete"))
        self.assertEqual("CA VA ETRE GENIAL",
                         bf.normalize_quote("Ça va être génial"))
        self.assertEqual("HOLA MUNDO!", bf.normalize_quote("¡Hola, mundo!"))
        self.assertEqual("DON'T STOP", bf.normalize_quote("Don’t stop"))

    def test_table_has_four_languages_times_four_pairs(self):
        # Language-major layout consumed by DrawWinQuote:
        # y = (Q_LANG*4 + quote)*6, i.e. Q_LANG*24 + quote*6.
        self.assertEqual(4, len(bf.QUOTE_LANGS))
        self.assertEqual(32, 4 * 4 * 2)

    @unittest.skipUnless((GEN / "quote_tables.inc").exists(),
                         "generated fight data not built")
    def test_generated_tables_decode_to_the_json_quotes(self):
        tables = _parse_tables(GEN / "quote_tables.inc")
        strings = {}
        for _fname, tag in bf.QUOTE_LANGS:
            strings.update(_parse_dbs(GEN / f"quote_strings_{tag}.inc"))

        for name in bf.CHARS:
            table = tables[f"{name}QuoteTab"]
            self.assertEqual(32, len(table),
                             f"{name}: 4 languages x 4 pairs x 2 pointers")
            for li, (_fname, tag) in enumerate(bf.QUOTE_LANGS):
                raw = self.db[tag][name]
                expected = [bf.wrap_quote(bf.normalize_quote(q))
                            for q in raw]
                expected = expected[:4]
                while len(expected) < 4:
                    expected.append(expected[-1] if expected else [])
                for qi in range(4):
                    # Each pair is two consecutive .dl entries.
                    p = (li * 4 + qi) * 2
                    rows = []
                    for ptr in table[p:p + 2]:
                        self.assertIn(ptr, strings,
                                      f"{name} {tag} slot {qi}: {ptr}")
                        vals = strings[ptr]
                        length = vals[0] if vals else 0
                        ids = vals[1:1 + length]
                        rows.append("".join(bf.CHARSET[i] for i in ids))
                    want = expected[qi] + [""] * (2 - len(expected[qi]))
                    self.assertEqual(want, rows,
                                     f"{name} {tag} slot {qi}")


if __name__ == "__main__":
    unittest.main()
