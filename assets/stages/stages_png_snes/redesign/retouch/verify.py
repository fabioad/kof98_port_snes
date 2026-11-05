"""Verify ready art using the current multi-stage converter; no ROM outputs touched."""
from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import sys
import tempfile
from PIL import Image

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
STAGES = HERE.parent.parent
REPO = STAGES.parents[2]
spec = importlib.util.spec_from_file_location('stages_builder', REPO / 'tools/build_stages.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
baseline = json.loads((HERE / 'baseline.json').read_text())
preserved = 0
for relative, digest in baseline['hashes'].items():
    if relative.startswith('redesign/ready/'):
        continue
    assert hashlib.sha256((STAGES / relative).read_bytes()).hexdigest() == digest, relative
    preserved += 1
report = []
old_pixels, new_pixels = {}, {}
clips = json.loads((STAGES / 'animations/stage_animations.json').read_text())['clips']
for file in sorted((HERE.parent / 'ready').glob('*.png')):
    with Image.open(file) as image, Image.open(HERE / 'before' / file.name) as old:
        assert image.mode == 'P' and image.size == (512, 224)
        assert len(image.getcolors()) <= 15
        assert sorted(i for _, i in image.getcolors()) == list(range(len(image.getcolors())))
        # Source sampling for animation includes the preceding rows.
        for clip in clips:
            target = clip['target']
            if clip['stage'] != file.stem or not target.get('target_region_xywh'):
                continue
            x, y, w, h = target['target_region_xywh']
            region = (x, max(0, y-8), x+w, y+h)
            assert image.convert('RGB').crop(region).tobytes() == old.convert('RGB').crop(region).tobytes(), clip['id']
        if file.name == 'KOF98-RugalStage.png':
            assert file.read_bytes() == (HERE / 'before' / file.name).read_bytes()
        expected = image.tobytes()
    graphics, tilemap, palette, pix = builder.emit_stage(str(file))
    assert len(graphics) <= 16384 and len(tilemap) == 4096 and len(palette) == 96
    for y in range(224):
        for x in range(512):
            address = ((x//256)*1024+(y//8)*32+(x//8)%32)*2
            word = struct.unpack_from('<H', tilemap, address)[0]
            assert word >> 10 == builder.STAGE_BG_PALETTE
            offset = (word & 1023)*32+(y%8)*2
            value = sum(((graphics[offset+plane//2*16+plane%2] >> (7-x%8)) & 1) << plane for plane in range(4))
            assert value == expected[y*512+x]+1
    old_pixels[file.stem] = builder.emit_stage(str(HERE / 'before' / file.name))[3]
    new_pixels[file.stem] = pix
    report.append(dict(file=file.name, tiles=len(graphics)//32, losslessRoundTrip=True))
names = sorted(new_pixels, key=lambda n: (0 if n == 'KOF98-JpnStreetStage' else 1, n))
with tempfile.TemporaryDirectory() as directory:
    builder.OUT = directory
    builder.build_anims(names, old_pixels)
    old_chr = (Path(directory) / 'stage_anim.chr').read_bytes()
    old_inc = (Path(directory) / 'stage_anim.inc').read_bytes()
    builder.build_anims(names, new_pixels)
    assert old_chr == (Path(directory) / 'stage_anim.chr').read_bytes()
    assert old_inc == (Path(directory) / 'stage_anim.inc').read_bytes()
result = dict(stages=report, preservedOriginalFiles=preserved,
              animationGraphicsAndTablesIdentical=True, rugalIdentical=True,
              romBuilt=False, backup=baseline['backup'])
(HERE / 'validation.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
