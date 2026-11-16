#!/usr/bin/env python3
"""Secret Robert selection, boss qualification, cinematic and ending routing."""
from pathlib import Path
from calibration.headless import Core
from capture_pair_headless import wait, tap, save_frame
from test_boss_intro_headless import start_single, CORE
from test_midfight_join_headless import start_team

ROOT = Path(__file__).resolve().parents[1]
GS, SEL1, SEL2 = 0x1020, 0x1085, 0x1086
MK, ROBERT = 53, 19
LOST, BOSS, SEEN, PHASE = range(0xF1C0, 0xF1C4)
TICK, VOL, MUSIC, END = 0xF1C4, 0xF1C6, 0xF1C7, 0xF1C8
OUT = ROOT / 'build/mrkarate_regression'

def new():
    c = Core(CORE, ROOT / 'kof98-snes.sfc')
    c.capture_video = True
    return c

def ready(c):
    wait(c, lambda: c.ram[GS] == 1, 'fight ready', 4000)

def kill(c, side=1):
    c.put(0x4010+side*0x40, 0)

def qualify(c, mode=1, lost=False, code=False):
    c.ram[LOST] = int(lost)
    c.ram[0x10C1] = 5
    if mode == 2:
        c.ram[0x10C9] = 2
        c.ram[0x10CA] = 3
    else:
        c.ram[0x1080] = 1
    if code:
        c.buttons[0] = {10,11,8}         # held L+R+A
    kill(c)
    for _ in range(5000):
        if c.ram[0x10C1] == 6 and c.ram[GS] in (1,4,16):
            break
        if c.ram[GS] == 15 and c.ram[0xF180] == 1:
            tap(c, 3)
        c.step()
    else:
        raise AssertionError('boss setup timed out')
    c.buttons[0] = set()

def cinema(c):
    wait(c, lambda: c.ram[GS] == 16, "Rugal still", 400)
    assert c.ram[GS] == 16 and c.ram[BOSS] == 1
    assert c.ram[SEL2] == MK
    assert c.ram[0x1087] == 5, 'secret boss on wrong stage'
    c.step(100)
    assert c.ram[GS] == 16 and c.ram[MUSIC] == 0
    save_frame(c.last_frame, OUT / 'rugal_asleep.png')
    from PIL import Image, ImageChops, ImageStat
    actual = Image.open(OUT / 'rugal_asleep.png').convert('RGB')
    reference = Image.open(ROOT / 'build/gen_fight/mrkarate_sleep.png').convert('RGB')
    actual = actual.crop((0,0,256,224))
    error = sum(ImageStat.Stat(ImageChops.difference(actual, reference)).mean) / 3
    assert error < 25, f'Rugal still was corrupted: pixel error {error:.1f}'
    wait(c, lambda: c.ram[PHASE] == 2, 'music fade')
    c.step(10)
    assert 0 < c.ram[VOL] < 240
    wait(c, lambda: c.ram[PHASE] == 3, 'offscreen entrance', 3000)
    assert c.ram[MUSIC] == 1 and c.word(0x4042) > 0
    c.step(65)
    save_frame(c.last_frame, OUT / 'mrkarate_entrance.png')
    ready(c)
    save_frame(c.last_frame, OUT / 'mrkarate_ready.png')

def endings(c):
    wait(c, lambda: c.ram[GS] == 8, 'ending1', 3500)
    wait(c, lambda: c.word(0xF079) > 1, 'ending renderer ready', 1000)
    assert c.ram[END] == 1 and c.ram[0xF078] == 0
    for screen in range(5):
        assert c.ram[0xF078] == screen
        c.ram[0xF079] = 1
        c.ram[0xF07A] = 0
        if screen < 4:
            wait(c, lambda: c.ram[0xF078] == screen+1 and c.word(0xF079) > 1, 'ending card ready', 1000)
        else:
            wait(c, lambda: c.ram[GS] == 10, 'Survivor ending', 2000)
    assert c.ram[GS] == 10 and c.ram[0xF078] == 0, 'missing Survivor ending'
    c.step(40)
    save_frame(c.last_frame, OUT / 'secret_ending.png')

def single():
    c = new()
    try:
        start_single(c)
        qualify(c)
        cinema(c)
        kill(c)
        wait(c, lambda: c.ram[GS] == 0, 'round two intermission')
        ready(c)
        assert c.ram[SEL2] == MK and c.ram[0x1080] == 1
        assert c.ram[PHASE] == 0
        kill(c)
        endings(c)
        print('PASS Single: flawless route, still/fade/entrance, two rounds, both endings', flush=True)
    finally:
        c.close()

def team():
    c = new()
    try:
        start_team(c)
        qualify(c, 2)
        cinema(c)
        assert c.ram[0x10CE] == c.ram[0x10CF] == MK
        kill(c)
        wait(c, lambda: c.ram[0x10C9] == 1, 'second boss round')
        ready(c)
        assert c.ram[BOSS] and c.ram[SEL2] == MK
        kill(c)
        endings(c)
        print('PASS Team: two boss rounds and ending1 -> Survivor', flush=True)
    finally:
        c.close()

def round_history():
    for draw in (False, True):
        c = new()
        try:
            start_single(c)
            kill(c, 0)
            if draw:
                kill(c, 1)
            wait(c, lambda: c.ram[GS] == 0, 'round result')
            assert c.ram[LOST] == (0 if draw else 1), (draw, c.ram[LOST])
            print(f'PASS round history: draw={draw}', flush=True)
        finally:
            c.close()

def eligibility():
    for lost, code, expected in ((True, False, 3), (True, True, MK)):
        c = new()
        try:
            start_single(c)
            qualify(c, lost=lost, code=code)
            assert c.ram[SEL2] == expected, (lost, code, c.ram[SEL2])
            print(f'PASS qualification lost={lost}, override={code}', flush=True)
        finally:
            c.close()

def selection():
    for port in (0,1):
        c = new()
        try:
            for _ in range(80):
                if c.ram[GS] == 6: break
                tap(c,3)
            c.ram[0xF070] = 1            # Single VS
            c.step(4)
            tap(c,3)
            wait(c, lambda: c.ram[GS] == 5, 'selection')
            c.ram[0x1090+port] = 0
            c.ram[0xF052+port] = 10     # SCUR1 / SCUR2, verified below
            c.buttons[port] = {10,11}
            c.step(10)
            c.buttons[port] = {10,11,8}
            c.step(12)
            assert c.ram[SEL1+port] == MK, (port,c.ram[SEL1+port])
            c.buttons[port] = set()
            c.ram[0x108E] = c.ram[0x108F] = 1
            c.step()
            ready(c)
            assert c.ram[0x1087] == 5
            print(f'PASS hidden select P{port+1}, boss stage', flush=True)
        finally:
            c.close()

def team_selection():
    from test_counter_grab_headless import boot_select
    from test_midfight_join_headless import wait_team_fight
    for mode, port in ((2,0), (3,0), (3,1)):
        c = new()
        try:
            boot_select(c)
            c.ram[0x10C0] = mode
            c.ram[0x1090] = 0
            c.ram[0x1091] = int(mode == 2)
            for side in (0,1):
                for member in range(3):
                    c.ram[0x10CB+side*3+member] = member
            c.ram[0x10C7] = 2 if port == 0 else 3
            c.ram[0x10D2] = (2 if port == 1 else 3) if mode == 3 else 0
            c.ram[0xF052+port] = 10
            if mode == 3:
                c.ram[0x108E + (1-port)] = 1
            c.buttons[port] = {10,11}
            c.step(10)
            c.buttons[port] = {8,10,11}
            c.step(12)
            c.buttons[port] = set()
            assert c.ram[0x10CB+port*3+2] == MK, (mode,port)
            wait_team_fight(c, 'team hidden selection', 4000)
            assert c.ram[0x1087] == 5, 'benched Karate allowed another stage'
            print(f'PASS team selection mode={mode}, P{port+1}, benched Karate pins boss stage', flush=True)
        finally:
            c.close()

def exclusions():
    import shutil
    import tempfile
    from test_counter_grab_headless import boot_select
    # Actual boot with no companion .msu, then try the hidden chord.
    with tempfile.TemporaryDirectory(prefix='karate-nomsu-') as tmp:
        rom = Path(tmp) / 'nomsu.sfc'
        shutil.copyfile(ROOT / 'kof98-snes.sfc', rom)
        c = Core(CORE, rom)
        try:
            boot_select(c)
            assert c.ram[0x107A] == 0
            c.ram[0xF052] = 10
            c.buttons[0] = {8,10,11}
            c.step(3)
            assert c.ram[SEL1] != MK and c.ram[BOSS] == 0
            c.buttons[0] = set()
            c.ram[0x10C0] = 1
            c.ram[SEL1], c.ram[SEL2] = 0, 1
            c.ram[0x1090], c.ram[0x1091] = 0, 1
            c.ram[0x108E] = c.ram[0x108F] = 1
            c.step()
            ready(c)
            c.ram[0x10C1] = 5
            c.ram[0x1080] = 1
            c.buttons[0] = {8,10,11}
            kill(c)
            wait(c, lambda: c.ram[GS] == 8, 'normal ending without MSU', 5000)
            assert c.ram[BOSS] == c.ram[END] == c.ram[PHASE] == 0
            assert c.ram[SEL1] != MK and c.ram[SEL2] != MK
            print('PASS no MSU: selection, flawless unlock and L+R+A cannot access Karate', flush=True)
        finally:
            c.close()
    c = new()
    try:
        boot_select(c)
        c.ram[SEL1], c.ram[SEL2] = MK, 0
        c.ram[0x1090] = c.ram[0x1091] = 1
        c.ram[0x108E] = c.ram[0x108F] = 1
        c.step()
        ready(c)
        assert c.ram[SEL1] == ROBERT and c.ram[SEL2] != MK
        assert c.ram[BOSS] == 0
        print('PASS CPU vs CPU: Mr. Karate excluded', flush=True)
    finally:
        c.close()

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    single()
    team()
    round_history()
    eligibility()
    selection()
    team_selection()
    exclusions()
