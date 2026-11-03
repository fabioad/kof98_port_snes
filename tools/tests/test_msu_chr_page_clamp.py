import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
META = os.path.join(ROOT, "build", "gen_fight", "ralf_meta.inc")
SPR = os.path.join(ROOT, "build", "gen_fight", "ralf_spr.inc")
DAIMON_SPR = os.path.join(ROOT, "build", "gen_fight", "daimon_spr.inc")
VOICES = os.path.join(ROOT, "build", "gen_fight", "voices.inc")
BASES = os.path.join(ROOT, "build", "gen_fight", "msu1_bases.inc")
BRIDGE = os.path.join(ROOT, "src", "snes", "fight_bridge.asm")

DMACHUNK = 1280
PAGE = 8192
SLICE = 32768


def meta_bytes(text):
    started = False
    data = []
    for line in text.splitlines():
        if line.startswith("ralfSprData:"):
            started = True
            continue
        if not started:
            continue
        line = line.strip()
        if line.startswith(".db"):
            data += [int(v.replace("$", "0x"), 16)
                     for v in line.split(".db", 1)[1].split(",")]
        elif line and not line.startswith("."):
            break
    return data


def meta_offsets(text):
    return [int(m.group(1)) for m in
            re.finditer(r"\.dw ralfSprData\+(\d+)", text)]


def metas(text_bytes, offsets):
    out = []
    for off in offsets:
        n = text_bytes[off]
        first = int.from_bytes(bytes(text_bytes[off + 1:off + 3]), "little")
        dmalen = int.from_bytes(bytes(text_bytes[off + 3:off + 5]), "little")
        out.append((n, first, dmalen))
    return out


def chunks(first, dmalen, base_slice, clamp):
    pos = 0
    while pos < dmalen:
        count = min(DMACHUNK, dmalen - pos)
        off = first * 32 + pos
        sl = base_slice + off // SLICE
        in_slice = off % SLICE
        file_off = sl * SLICE + in_slice
        prefix = file_off & 511
        aligned = file_off & ~511
        if clamp:
            page_left = PAGE - (aligned & (PAGE - 1))
            count = min(count, page_left - prefix)
        assert count > 0
        yield aligned, prefix, prefix + count
        pos += count


def db_bytes(text, start_label, end_label):
    body = text[text.index(start_label):]
    body = body[:body.index(end_label)]
    data = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith(".db"):
            data += [int(v.strip().replace("$", "0x"), 16)
                     for v in line.split(".db", 1)[1].split(",")]
    return data


def sprite_metas(data, offsets):
    out = []
    for off in offsets:
        dmalen = data[off + 3] | data[off + 4] << 8
        first = data[off + 1] | data[off + 2] << 8
        out.append((first, dmalen))
    return out


def clamped_upload(first, dmalen, base_slice, chunk=DMACHUNK):
    """Yield (aligned, prefix, count) for the runtime page-clamped upload."""
    pos = 0
    while pos < dmalen:
        count = min(chunk, dmalen - pos)
        off = first * 32 + pos
        sl = base_slice + off // SLICE
        file_off = sl * SLICE + (off % SLICE)
        prefix = file_off & 511
        aligned = file_off & ~511
        page_left = PAGE - (aligned & (PAGE - 1))
        count = min(count, page_left - prefix)
        assert count > 0
        yield aligned, prefix, count
        pos += count


def voice_tables(text):
    """MSU voice tables: name -> [(file offset, total bytes)]."""
    offsets = {}
    for match in re.finditer(r"VoiceOfs_(\w+):", text):
        name = match.group(1)
        body = text[match.end():]
        body = body[:body.index(".ENDS")]
        values = []
        for line in body.splitlines():
            line = line.strip()
            if line.startswith(".db"):
                b = [int(v.replace("$", "0x"))
                     for v in line.split(".db", 1)[1].split(",")]
                values.append(b[0] | b[1] << 8 | b[2] << 16 | b[3] << 24)
        offsets[name] = values
    sizes = {}
    for match in re.finditer(r"VoiceTab_(\w+):", text):
        name = match.group(1)
        body = text[match.end():]
        body = body[:body.index(".ENDS")]
        lines = [line.strip() for line in body.splitlines()]
        values = []
        for i, line in enumerate(lines):
            if line.startswith(".dw") and i and lines[i - 1].startswith(".db"):
                values.append(int(line.split()[1]))
        sizes[name] = values
    tables = {}
    for name, offs in offsets.items():
        blocks = sizes.get(name, [])
        tables[name] = [(off, blocks[i] * 9)
                        for i, off in enumerate(offs) if i < len(blocks)]
    return tables


def voice_raw_chunks(offset, total, chunk):
    pos = 0
    while pos < total:
        count = min(chunk, total - pos)
        src = offset + pos
        aligned = src & ~511
        prefix = src & 511
        yield aligned, prefix, prefix + count
        pos += count


class MsuChrPageClampTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path in (META, SPR, BASES):
            if not os.path.exists(path):
                raise unittest.SkipTest("run build_fight.py first")
        with open(META) as source:
            cls.data = meta_bytes(source.read())
        with open(SPR) as source:
            cls.offsets = meta_offsets(source.read())
        with open(BASES) as source:
            base = re.search(r"MSU_RALF_SLICE = (\d+)", source.read())
        cls.base_slice = int(base.group(1))

    def test_a_real_chunk_crossed_an_8k_page(self):
        # The clamp exists for a real hardware failure class: some Ralf
        # sprite chunks end past an 8 KiB MSU cache page.  The exact sprite
        # index moves whenever the CHR layout is regenerated, so scan for a
        # crossing instead of pinning one index.
        crossing = []
        for index, (_n, first, dmalen) in enumerate(
                metas(self.data, self.offsets)):
            for aligned, _prefix, length in chunks(
                    first, dmalen, self.base_slice, clamp=False):
                if (aligned & (PAGE - 1)) + length > PAGE:
                    crossing.append(index)
                    break
        self.assertTrue(crossing, 'no sprite chunk crosses an 8 KiB page')

    def test_clamped_uploads_stay_inside_one_page(self):
        for _n, first, dmalen in metas(self.data, self.offsets):
            for aligned, _prefix, length in chunks(
                    first, dmalen, self.base_slice, clamp=True):
                self.assertLessEqual((aligned & (PAGE - 1)) + length, PAGE)

    def test_clamp_covers_exactly_the_requested_bytes(self):
        for _n, first, dmalen in metas(self.data, self.offsets):
            clamped = sum(length - prefix for _a, prefix, length in chunks(
                first, dmalen, self.base_slice, clamp=True))
            self.assertEqual(clamped, dmalen)
            clamped = sum(length - prefix for _a, prefix, length in chunks(
                first, dmalen, self.base_slice, clamp=False))
            self.assertEqual(clamped, dmalen)

    def test_runtime_calls_the_clamp(self):
        with open(BRIDGE) as source:
            text = source.read()
            self.assertIn("jsl MsuChrPageClamp", text)
            self.assertIn("MsuChrPageClamp:", text)
            self.assertIn("and #$1FFF.w", text)


class DaimonWinPoseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path in (DAIMON_SPR, BASES):
            if not os.path.exists(path):
                raise unittest.SkipTest("run build_fight.py first")
        with open(DAIMON_SPR) as source:
            text = source.read()
        cls.offsets = [int(m.group(1)) for m in
                       re.finditer(r"\.dw daimonSprData\+(\d+)", text)]
        cls.data = db_bytes(text, "daimonSprData:", "daimonBoxTab:")
        with open(BASES) as source:
            base = re.search(r"MSU_DAIMON_SLICE = (\d+)",
                             source.read())
        cls.base_slice = int(base.group(1))
        anim = text[text.index("daimonAnim90:"):]
        anim = anim[:anim.index("daimonAnim91:")]
        cls.win_sprites = [int(m.group(1)) for m in
                           re.finditer(r"\.dw\s+(\d+)", anim)]

    def test_win_pose_is_anim_181_sprites_49_to_54(self):
        # S_WPOSE = 90 -> AnimTab[90] = real win pose anim 181.
        self.assertEqual([49, 50, 51, 52, 53, 54], self.win_sprites)

    def test_win_pose_chunks_would_cross_without_the_clamp(self):
        metas = sprite_metas(self.data, self.offsets)
        crossed = False
        for index in self.win_sprites:
            first, dmalen = metas[index]
            for aligned, _prefix, staged in chunks(
                    first, dmalen, self.base_slice, clamp=False):
                if (aligned & (PAGE - 1)) + staged > PAGE:
                    crossed = True
        self.assertTrue(crossed,
                        "no win-pose chunk crosses the 8 KiB page")

    def test_win_pose_chunks_stay_inside_one_page(self):
        metas = sprite_metas(self.data, self.offsets)
        for index in self.win_sprites:
            first, dmalen = metas[index]
            for aligned, prefix, count in clamped_upload(
                    first, dmalen, self.base_slice):
                self.assertLessEqual(
                    (aligned & (PAGE - 1)) + prefix + count, PAGE)

    def test_win_pose_clamp_covers_every_tile(self):
        metas = sprite_metas(self.data, self.offsets)
        for index in self.win_sprites:
            first, dmalen = metas[index]
            staged = sum(count for _a, _p, count in clamped_upload(
                first, dmalen, self.base_slice))
            self.assertEqual(dmalen, staged)

    def test_every_daimon_sprite_upload_stays_in_one_page(self):
        metas = sprite_metas(self.data, self.offsets)
        for index, (first, dmalen) in enumerate(metas):
            with self.subTest(sprite=index):
                for aligned, prefix, count in clamped_upload(
                        first, dmalen, self.base_slice):
                    self.assertLessEqual(
                        (aligned & (PAGE - 1)) + prefix + count, PAGE)


class MsuVoicePageClampTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path in (VOICES, BRIDGE):
            if not os.path.exists(path):
                raise unittest.SkipTest("run build_fight.py first")
        with open(VOICES) as source:
            cls.tables = voice_tables(source.read())

    def test_known_crossing_voices_exist(self):
        # Before the fix, these chunks started in the final 512-byte sector
        # of an 8 KiB page: Daimon's weak Jiraishin and Ralf's special-move
        # grunts.  This is the hardware freeze class the clamp removes.
        raw_cross = False
        for name, index in (("daimon", 0), ("daimon", 4),
                            ("daimon", 11), ("daimon", 18),
                            ("ralf", 34), ("ralf", 36)):
            with self.subTest(char=name, voice=index):
                offset, total = self.tables[name][index]
                for aligned, _prefix, staged in voice_raw_chunks(
                        offset, total, 512):
                    if (aligned & (PAGE - 1)) + staged > PAGE:
                        raw_cross = True
        self.assertTrue(raw_cross)

    def test_voice_clamp_covers_every_byte(self):
        for name, voices in self.tables.items():
            for index, (offset, total) in enumerate(voices):
                with self.subTest(char=name, voice=index):
                    # The voice reader clamps each 512-byte chunk against the
                    # absolute file offset, not the 32 KiB CHR slice.
                    pos = 0
                    while pos < total:
                        count = min(512, total - pos)
                        src = offset + pos
                        prefix = src & 511
                        aligned = src & ~511
                        page_left = PAGE - (aligned & (PAGE - 1))
                        count = min(count, page_left - prefix)
                        self.assertGreater(count, 0)
                        self.assertLessEqual(prefix + count, page_left)
                        pos += count
                    self.assertEqual(total, pos)

    def test_voice_reader_calls_the_page_clamp(self):
        with open(BRIDGE) as source_file:
            source = source_file.read()
        reader = source[source.index("MsuReadAlignedFar:"):
                        source.index("MRA_poll:")]
        self.assertIn("jsl MsuChrPageClamp", reader)


if __name__ == "__main__":
    unittest.main()
