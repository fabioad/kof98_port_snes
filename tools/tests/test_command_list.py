"""PRACTICE command-list tables: coverage, text and category checks."""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import build_fight as bf  # noqa: E402


def _table_path(name):
    if name in bf.FIXED_CMD_LIST:
        return os.path.join(bf.OUT, name + "_spr.inc")
    return os.path.join(bf.OUT, name + "_cmdlist.inc")


def _parse_table(name):
    path = _table_path(name)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    strings = {}
    for match in re.finditer(
            r"^([A-Za-z0-9_]+): \.db (\d+)((?:,\d+)*)\s*$", text, re.M):
        ids = [int(v) for v in match.group(3).split(",") if v]
        strings[match.group(1)] = "".join(
            bf.CHARSET[v] if v < len(bf.CHARSET) else "?" for v in ids)
    match = re.search(rf"^{name}CmdList:\s*\n\s*\.db (\d+)", text, re.M)
    if not match:
        return None
    count = int(match.group(1))
    lines = [line.strip() for line in text[match.end():].splitlines()]
    rows = []
    i = 0
    while len(rows) < count:
        if not lines[i].startswith(".db"):
            i += 1
            continue
        sid, cat = (int(v) for v in
                    lines[i].split(None, 1)[1].split(","))
        refs = re.findall(r"[A-Za-z0-9_]+", lines[i + 1])
        rows.append((sid, cat, strings[refs[1]], strings[refs[2]]))
        i += 2
    return rows


class CommandListTests(unittest.TestCase):
    def test_every_character_has_rows(self):
        for name in sorted(bf.CHARS):
            with self.subTest(char=name):
                rows = _parse_table(name)
                self.assertTrue(rows, name)
                self.assertLessEqual(len(rows), 48, name)

    def test_rows_are_unique_and_fit_the_hud(self):
        for name in sorted(bf.CHARS):
            with self.subTest(char=name):
                rows = _parse_table(name)
                sids = [row[0] for row in rows]
                self.assertEqual(len(sids), len(set(sids)), name)
                # Imported fighters wire as many normal slots as their CMD
                # provides; the engine's ButtonTab is the source of truth.
                self.assertGreaterEqual(
                    sum(1 for row in rows if row[1] == 0), 4, name)
                for sid, cat, move, command in rows:
                    self.assertLessEqual(sid, 97, (name, sid))
                    self.assertIn(cat, range(7), (name, sid, cat))
                    self.assertTrue(move and move.strip(), (name, sid))
                    self.assertLessEqual(len(move), 16, (name, move))
                    self.assertLessEqual(len(command), 11, (name, command))
                    self.assertTrue(all(c in bf.CHARSET for c in move),
                                    (name, move))
                    self.assertTrue(all(c in bf.CHARSET for c in command),
                                    (name, command))
                    self.assertNotIn("?", command, (name, command))
                    self.assertFalse(command.endswith(("+", ",", "-", "/")),
                                     (name, command))

    def test_normal_buttons_follow_pad_layout(self):
        """LP=Y, HP=X, LK=B, HK=A for every fighter (physical pad remap)."""
        expected = {5: "Y", 6: "X", 7: "B", 8: "A"}
        for name in sorted(bf.CHARS):
            rows = {row[0]: row for row in _parse_table(name)}
            for sid, button in expected.items():
                with self.subTest(char=name, sid=sid):
                    self.assertIn(sid, rows, name)
                    self.assertEqual(button, rows[sid][3], (name, sid))

    def test_specials_show_a_button(self):
        """Long motions must not push the button past the 11-cell field."""
        buttons = set(bf.SNES_BTN_TEXT.values())
        for name in sorted(bf.CHARS):
            for sid, cat, move, command in _parse_table(name):
                if cat not in (2, 3, 4):
                    continue
                with self.subTest(char=name, sid=sid):
                    last = command.split("+")[-1].strip()
                    self.assertIn(last, buttons, (name, sid, move, command))

    def test_known_kof98_commands(self):
        kyo = {row[0]: row for row in _parse_table("kyo")}
        self.assertEqual((2, "DP + Y"), (kyo[50][1], kyo[50][3]))
        self.assertTrue(kyo[50][2].startswith("ONIYAKI"))
        # Physical L/R routing: R = blowback, L+R = taunt, L = dodge.
        self.assertEqual((1, "R"), (kyo[67][1], kyo[67][3]))
        self.assertEqual("L+R", kyo[47][3])
        self.assertEqual("L", kyo[69][3])
        self.assertEqual("L + BACK", kyo[94][3])
        self.assertEqual("L + FWD", kyo[95][3])
        self.assertEqual(4, kyo[87][1])                  # MAX super
        self.assertEqual(3, kyo[88][1])                  # second super (SUP)
        self.assertEqual(3, kyo[89][1])                  # second super (SUP)
        self.assertEqual(5, kyo[74][1])                  # throw

        iori = {row[0]: row for row in _parse_table("iori")}
        self.assertEqual(4, iori[89][1])                 # SDM/MAX slot
        self.assertEqual(3, iori[88][1])                 # ordinary finisher
        # Composed super: the list keeps the full QCBHCF notation even
        # though the matcher also accepts the diagonal-free HCF portion.
        self.assertEqual("QCBHCF + Y", iori[85][3])

        heavyd = {row[0]: row for row in _parse_table("heavyd")}
        self.assertEqual(4, heavyd[86][1])               # MAX D. Crazy
        self.assertEqual(3, heavyd[87][1])               # D. Magnum

        ryu = {row[0]: row for row in _parse_table("ryu")}
        self.assertEqual(3, ryu[87][1])                  # normal super
        self.assertEqual(4, ryu[88][1])                  # MAX hadouken

        brian = {row[0]: row for row in _parse_table("brian")}
        self.assertEqual(3, brian[87][1])                # Galaxy Cyclone
        self.assertEqual(3, brian[88][1])                # Big Bang Tackle

        terry = {row[0]: row for row in _parse_table("terry")}
        self.assertTrue(terry[50][2].startswith("BURN KNUCKLE"))
        self.assertEqual("QCB + Y", terry[50][3])
        self.assertTrue(terry[52][2].startswith("CRACK SHOOT"))
        self.assertEqual("QCB + B", terry[52][3])
        # The command list keeps the classic motion even though the matcher
        # also accepts the diagonal-free HCF/HCB form.
        self.assertEqual("HCF + B", terry[56][3])
        self.assertEqual(6, terry[45][1])                # system/dash

    def test_reachable_supers_cost_meter(self):
        """A command that enters 85-89 must spend at least one stock."""
        for name in sorted(bf.CHARS):
            with self.subTest(char=name):
                path = os.path.join(bf.OUT, name + "_spr.inc")
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
                match = re.search(rf"^{name}PowTab:\s*\n", text, re.M)
                self.assertIsNotNone(match, name)
                powtab = []
                for row in re.finditer(r"^\s*\.dw (-?\d+)\s*$",
                                       text[match.end():], re.M):
                    powtab.append(int(row.group(1)))
                rows = _parse_table(name)
                for sid, cat, move, command in rows:
                    if 85 <= sid <= 89:
                        self.assertLessEqual(
                            powtab[sid], -1000,
                            (name, sid, move, powtab[sid]))

    def test_categories_cover_all_seven_tags(self):
        seen = set()
        for name in bf.CHARS:
            seen.update(row[1] for row in _parse_table(name))
        self.assertEqual(set(range(7)), seen)


if __name__ == "__main__":
    unittest.main()
