import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
AI_TABLES = os.path.join(ROOT, "build", "gen_fight", "ai_tables.inc")
FIGHT = os.path.join(ROOT, "src", "engine", "fight.asm")
S_EXT_LAST = 114                        # last state dispatched by StateTab


def parse_tables(text):
    """Yield (name, header, rows) for every generated AiTab."""
    tables = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"(\w+)AiTab:", lines[i].strip())
        if not m:
            i += 1
            continue
        name = m.group(1)
        data = []
        i += 1
        while i < len(lines) and lines[i].strip().startswith(".db"):
            values = []
            for value in lines[i].split(".db", 1)[1].split(","):
                value = value.strip()
                values.append(int(value[1:], 16) if value.startswith("$")
                              else int(value))
            data += values
            i += 1
        count = data[0]
        header = data[:12]
        rows = [data[12 + 6 * n:18 + 6 * n] for n in range(count)]
        tables.append((name, header, rows))
    return tables


class AiTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(AI_TABLES):
            raise unittest.SkipTest("run build_fight.py first")
        with open(AI_TABLES) as source:
            cls.tables = parse_tables(source.read())

    def test_every_table_has_its_declared_row_count(self):
        self.assertTrue(self.tables)
        for name, header, rows in self.tables:
            with self.subTest(char=name):
                self.assertEqual(len(rows), header[0])
                self.assertTrue(all(len(row) == 6 for row in rows))

    def test_every_row_sid_is_dispatchable(self):
        # AI_ScanMove feeds the row sid straight to EnterState, which indexes
        # StateTab.  A sid outside 0..S_EXT_LAST would jump into unrelated
        # ROM and hang the fight.
        for name, _header, rows in self.tables:
            for index, row in enumerate(rows):
                with self.subTest(char=name, row=index):
                    self.assertLessEqual(row[0], S_EXT_LAST)


class AiScanOffsetTests(unittest.TestCase):
    def test_row_offset_is_computed_in_16_bit_mode(self):
        # The row offset is idx*6+12.  Computing it with an 8-bit
        # accumulator leaves the high byte (B) stale, and the following TAY
        # (16-bit index registers) copies that garbage into Y.  The scan then
        # reads outside the table and can return an invalid sid.
        with open(FIGHT, encoding="utf-8", errors="replace") as source:
            text = source.read()
        block = text[text.index("AI_scan_loop:"):]
        block = block[:block.index("lda [sptr],y")]
        self.assertIn("rep #$20", block)
        self.assertIn(".ACCU 16", block)
        self.assertIn("tay", block)
        tail = text[text.index("AI_scan_loop:"):]
        tail = tail[:tail.index("sta scr3")]
        self.assertIn("sep #$20", tail[tail.index("tay"):])


if __name__ == "__main__":
    unittest.main()
