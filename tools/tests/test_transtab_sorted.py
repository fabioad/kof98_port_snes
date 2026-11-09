import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATED_DIRS = (
    ROOT / "build" / "gen_fight",
    ROOT / "build" / "tiny" / "gen_fight",
)


def byte_value(value):
    return int(value[1:], 16) if value.startswith("$") else int(value)


class TransTabSortedTests(unittest.TestCase):
    def test_trans_tables_are_sorted_by_from_sid(self):
        paths = [
            path
            for directory in GENERATED_DIRS
            if directory.is_dir()
            for path in sorted(directory.glob("*_spr.inc"))
        ]
        if not paths:
            self.skipTest("generated fight sprite includes are unavailable")

        tables = 0
        label_re = re.compile(r"(?m)^([A-Za-z_]\w*TransTab):\s*$")
        next_label_re = re.compile(r"(?m)^[A-Za-z_]\w*:\s*$")
        row_re = re.compile(r"^\s*\.db\s+(\$[0-9A-Fa-f]+|\d+)\b")
        for path in paths:
            text = path.read_text()
            labels = list(label_re.finditer(text))
            for label in labels:
                next_label = next_label_re.search(text, label.end())
                end = next_label.start() if next_label else len(text)
                rows = []
                for line in text[label.end():end].splitlines():
                    match = row_re.match(line)
                    if match:
                        rows.append(byte_value(match.group(1)))
                if not rows:
                    continue
                tables += 1
                # TransAir/TransEnd/TransLive early exits depend on this order.
                with self.subTest(path=path.name, table=label.group(1)):
                    self.assertEqual(rows, sorted(rows))

        self.assertGreater(tables, 0, "no TransTab tables were found")


if __name__ == "__main__":
    unittest.main()
