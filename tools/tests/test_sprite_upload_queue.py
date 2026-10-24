import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIGHT = os.path.join(ROOT, "src", "engine", "fight.asm")


class SpriteUploadQueueTests(unittest.TestCase):
    """ASF_q_new must not replace the pending sprite id / DMA position
    while an upload is in flight, or sprites larger than one VBlank
    budget starve and the displayed metasprite pointer never changes.
    Runtime proof is the roster displayed_metas check; this is a
    structural guard on the ordering."""

    def test_inflight_upload_completes_before_queue_replace(self):
        src = open(FIGHT).read()
        m = re.search(r"ASF_q_new:(.*?)ASF_q_wait:", src, re.S)
        self.assertIsNotNone(m, "ASF_q_new block not found")
        block = m.group(1)
        guard = re.search(
            r"lda\s+FP\+F_DMAREQ,x\s*\n\s*bne\s+ASF_q_(?:wait|drop)", block)
        self.assertIsNotNone(
            guard, "missing in-flight DMAREQ guard in ASF_q_new")
        if "bne ASF_q_drop" in block:
            drop = src[src.index("ASF_q_drop:"):src.index("ASF_q_wait:")]
            self.assertIn("bra ASF_q_wait", drop,
                          "coalesced-pose telemetry path must reach the wait")
        first_write = block.find("sta FP+F_PSPRID,x")
        self.assertGreater(first_write, 0)
        self.assertLess(guard.start(), first_write,
                        "DMAREQ guard must precede the sprite id write")
        dmapos = block.find("stz FP+F_DMAPOS,x")
        self.assertGreater(dmapos, first_write,
                           "DMAPOS reset must stay after the guard")


if __name__ == "__main__":
    unittest.main()
