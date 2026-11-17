#!/usr/bin/env python3
"""Read-only SFF validation; export native indexed frames for inspection."""
import json
from pathlib import Path
from sff_reader import Sff
from PIL import Image
root = Path(__file__).resolve().parents[1]
old = Sff(root / 'backups/Sakura.original.sff')
new = Sff(root / 'Sakura.sff')
assert len(old.sprites) == len(new.sprites) == 2076
assert old.palettes == new.palettes
changed = untouched = links = 0
for a, b in zip(old.sprites, new.sprites):
    assert (a.group, a.number, a.link, a.palidx) == (b.group, b.number, b.link, b.palidx)
    if (a.w, a.h) != (b.w, b.h):
        assert (b.w, b.h, b.ax, b.ay) == (a.w + 2, a.h + 2, a.ax + 1, a.ay + 1)
        for y in range(a.h):
            for x in range(a.w):
                if a.pix[y*a.w+x]:
                    assert a.pix[y*a.w+x] == b.pix[(y+1)*b.w+x+1]
        changed += 1
        links += not bool(a.size)
    else:
        assert (a.pix, a.ax, a.ay) == (b.pix, b.ax, b.ay)
        untouched += 1
for name, archive in [('antes', old), ('depois', new)]:
    for group in [0, 20, 200, 410, 1000, 5000]:
        f = next(s for s in archive.sprites if s.group == group and s.number == 0)
        image = Image.frombytes('P', (f.w, f.h), f.pix)
        image.putpalette(sum(map(list, archive.palettes[f.palidx]), []))
        image.save(root / f'output/{name}-{group}.png', transparency=0)
report = dict(entries=2076, changedIncludingLinks=changed, linkedImages=links,
              untouched=untouched, allOriginalOpaquePixelsPreserved=True,
              allPalettesPreserved=True, axesCorrect=True)
(root / 'output/validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
