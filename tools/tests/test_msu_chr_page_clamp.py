import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
META = os.path.join(ROOT, "build", "gen_fight", "ralf_meta.inc")
SPR = os.path.join(ROOT, "build", "gen_fight", "ralf_spr.inc")
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

    def test_known_idle_chunk_crossed_an_8k_page(self):
        # Idle sprite 6 (AnimTab entry 6) is queued right after the guard
        # pose in ralfAnim0; its first tile chunk sits at the end of an
        # 8 KiB MSU cache page.  This is the frame from the hardware report.
        n, first, dmalen = metas(self.data, self.offsets)[6]
        raw = list(chunks(first, dmalen, self.base_slice, clamp=False))
        self.assertTrue(any((aligned & (PAGE - 1)) + length > PAGE
                            for aligned, _prefix, length in raw))

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


if __name__ == "__main__":
    unittest.main()
