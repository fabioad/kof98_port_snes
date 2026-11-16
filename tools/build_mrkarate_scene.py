"""Compose the secret boss still from the game's stage and Rugal down pose."""
from pathlib import Path
from PIL import Image
from sff import Sff
from build_select import sprite_rgb
from build_endings import build_frame

ROOT = Path(__file__).resolve().parents[1]

def build(out):
    out = Path(out)
    bg = Image.open(ROOT / 'assets/stages/stages_png_snes/KOF98-RugalStage.png').convert('RGBA').resize((256,224))
    rugal = Sff(str(ROOT / 'assets/characters/Rugal-KOF98/Rugal.sff'))
    pose, axis = sprite_rgb(rugal, 5040, 10)
    scale = .94
    pose = pose.resize((round(pose.width*scale), round(pose.height*scale)), Image.Resampling.NEAREST)
    bounds = pose.getbbox()
    x = 128 - (bounds[0] + bounds[2]) // 2
    bg.alpha_composite(pose, (x, round(204-axis[1]*scale)))
    bg.convert('RGB').save(out / 'mrkarate_sleep.png')
    build_frame(str(out / 'mrkarate_sleep.png'), str(out / 'mrkarate_sleep'))

if __name__ == '__main__':
    build(ROOT / 'build/gen_fight')
