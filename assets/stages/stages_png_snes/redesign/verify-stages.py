"""Check all exports with the game's real converter, using temporary outputs."""
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
from PIL import Image

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent
REPO = STAGES.parents[2]
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('stage_builder', REPO / 'tools/build_fight.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

def tile_count(image):
    image = image.convert('RGB')
    return len({image.crop((x,y,x+8,y+8)).tobytes()
                for y in range(0,224,8) for x in range(0,512,8)})

report = []
with tempfile.TemporaryDirectory(prefix='verify-16bit-stages-') as directory:
    root = Path(directory)
    source = root / 'assets/stages/stages_png_snes/KOF98-JpnStreetStage.png'
    source.parent.mkdir(parents=True)
    out = root / 'output'
    out.mkdir()
    builder.ROOT, builder.OUT = str(root), str(out)
    for file in sorted((HERE / 'ready').glob('*.png')):
        if source.is_symlink():
            source.unlink()
        source.symlink_to(file)
        with Image.open(file) as image:
            assert image.size == (512,224) and image.mode == 'P', file
            colors = image.getcolors(256)
            assert len(colors) <= 15
            assert sorted(index for count,index in colors) == list(range(len(colors)))
            expected = image.tobytes()
            palette = image.getpalette()
        builder.build_stage()
        graphics = (out / 'stage.chr').read_bytes()
        tilemap = (out / 'stage.map').read_bytes()
        pal = (out / 'stage_pal.bin').read_bytes()
        assert len(graphics) <= 16384 and len(tilemap) == 4096 and len(pal) == 32
        for y in range(224):
            for x in range(512):
                tile_x,tile_y = x//8,y//8
                address = ((tile_x//32)*1024+tile_y*32+tile_x%32)*2
                word = struct.unpack_from('<H',tilemap,address)[0]
                assert word < 512
                offset = word*32+(y%8)*2
                bit = 7-x%8
                value = sum(((graphics[offset+plane//2*16+plane%2]>>bit)&1)<<plane for plane in range(4))
                assert value == expected[y*512+x]+1, (file,x,y)
        for index in range(len(colors)):
            r,g,b = palette[index*3:index*3+3]
            value = (r>>3)|((g>>3)<<5)|((b>>3)<<10)
            assert struct.unpack_from('<H',pal,(index+1)*2)[0] == value
        baseline = HERE / 'originals' / file.name
        if not baseline.exists():
            baseline = STAGES / file.name
        with Image.open(baseline) as original:
            old_tiles = tile_count(original)
        row = dict(file=file.name,originalTiles=old_tiles,finalTiles=len(graphics)//32,
                   originalPngBytes=baseline.stat().st_size,
                   finalPngBytes=file.stat().st_size,losslessConverterRoundTrip=True)
        report.append(row)
        print(json.dumps(row))
(HERE / 'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS: {len(report)} stages; real converter, palette, tilemap and every pixel verified.')
