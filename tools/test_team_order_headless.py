#!/usr/bin/env python3
"""TEAM PLAY: per-stage ordering, two human pads, CPU bypass and member flow."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from calibration.headless import Core
from test_midfight_join_headless import enter_mode
from capture_pair_headless import save_frame

GS=0x1020
ORDER=15
ACTIVE,COUNT,CURSOR,MASK,HUMAN=0xF180,0xF184,0xF186,0xF188,0xF18A
TEAM=0x10CB
STEP,SIDE=0x10C7,0x10D2
CPU1,CPU2=0x1090,0x1091
CELLS=(3,6,36)
OUT=Path('build/team_order')


def wait(c,pred,label,limit=9000):
    for _ in range(limit):
        if pred():return
        c.step()
    raise AssertionError(f'{label}: gs={c.ram[GS]}, stage={c.ram[0x10C1]}, order={list(c.ram[COUNT:COUNT+6])}')


def press(c,button,side=0):
    c.buttons[side]=set();c.step(8)
    c.buttons[side]={button};c.step(6)
    c.buttons[side]=set();c.step(8)


def pick_team(c,side):
    for idx,cell in enumerate(CELLS):
        for _ in range(8):
            if c.ram[GS]==ORDER:return
            c.ram[0xF052+side]=cell
            press(c,8,side)
            if c.ram[STEP]!=idx or c.ram[SIDE]!=side:break
        else:raise AssertionError(f'character pick {side}/{idx} failed')


def order_ready(c):
    wait(c,lambda:c.ram[GS]==ORDER and c.ram[ACTIVE]==1,'order select ready')
    c.step(12)


def choose(c,side,indices):
    for idx in indices:
        for _ in range(3):
            if c.ram[CURSOR+side]==idx:break
            press(c,5,side)
        press(c,8,side)


def wait_fight(c):
    wait(c,lambda:c.ram[GS]==1,'fight')
    c.step(30)


def ko_member(c,ending=False):
    c.put(0x4010,200)
    c.put(0x4050,0)
    wait(c,lambda:c.ram[GS]==2,'member KO')
    for _ in range(9000):
        if c.ram[GS] in ((1,ORDER,8,13) if ending else (1,ORDER)):return
        c.step()
    raise AssertionError('member resolution stalled')


def solo_campaign(c):
    enter_mode(c,2);pick_team(c,0);order_ready(c)
    assert list(c.ram[TEAM:TEAM+3])==[0,1,2]
    assert list(c.ram[HUMAN:HUMAN+2])==[1,0]
    assert c.ram[COUNT+1]==3, 'CPU waits for ordering'
    cpu=list(c.ram[TEAM+3:TEAM+6])
    save_frame(c.last_frame,OUT/'order_cpu.png')
    choose(c,0,[2]);press(c,0)
    assert c.ram[COUNT]==0 and c.ram[MASK]==0, 'undo failed'
    choose(c,0,[2,0,1]);wait_fight(c)
    assert list(c.ram[TEAM:TEAM+3])==[2,0,1]
    assert list(c.ram[TEAM+3:TEAM+6])==cpu
    assert c.ram[0x1085]==2, 'wrong first member'
    print('PASS custom order, undo, CPU fixed and chosen first fighter',flush=True)
    save_frame(c.last_frame,OUT/'ordered_first_fight.png')
    # Every confrontation of the route, including the two-member boss team.
    for stage in range(7):
        if stage:
            order_ready(c)
            assert c.ram[0x10C1]==stage
            assert c.ram[COUNT]==0, 'choices were not reset at next stage'
            before=list(c.ram[TEAM:TEAM+3])
            if stage==1:
                choose(c,0,[1,2,0]);expected=[before[1],before[2],before[0]]
            else:
                press(c,3);expected=before
            wait_fight(c)
            assert list(c.ram[TEAM:TEAM+3])==expected
            assert c.ram[0x1085]==expected[0]
        size=2 if stage==6 else 3
        for member in range(size):
            # Keep the campaign human alive while the real KO/round code runs.
            ko_member(c,ending=stage==6 and member==size-1)
            if member<size-1:
                assert c.ram[GS]!=ORDER, 'order select between members'
                wait_fight(c)
            elif stage<6:
                assert c.ram[GS]==ORDER, 'no order select before next stage'
        print('PASS stage',stage+1,'order once, no order between member rounds',flush=True)
    assert c.ram[GS]!=ORDER, 'ordering opened after campaign end'


def two_humans(c):
    enter_mode(c,2)
    press(c,3,1)
    assert c.ram[CPU2]==0, 'P2 did not join Team Play select'
    pick_team(c,0)
    assert c.ram[SIDE]==1, 'P1 did not hand trio selection to P2'
    pick_team(c,1);order_ready(c)
    assert list(c.ram[HUMAN:HUMAN+2])==[1,1]
    c.buttons=[{5,8},{4,8}];c.step(6);c.buttons=[set(),set()];c.step(8)
    assert list(c.ram[COUNT:COUNT+2])==[1,1], 'simultaneous pad input was lost'
    assert c.ram[0xF196]==1 and c.ram[0xF199]==2
    press(c,0,1)                       # P2 undoes, without touching P1
    assert list(c.ram[COUNT:COUNT+2])==[1,0]
    choose(c,0,[2,0])
    c.step(50)
    assert c.ram[GS]==ORDER and c.ram[COUNT+1]==0, 'P1 confirmation skipped P2'
    choose(c,1,[2,1])
    save_frame(c.last_frame,OUT/'two_players_order.png')
    choose(c,1,[0]);wait_fight(c)
    assert list(c.ram[TEAM:TEAM+6])==[1,2,0,2,1,0]
    assert [c.ram[0x1085],c.ram[0x1086]]==[1,2]
    print('PASS independent P1/P2 order; launch waits for both humans',flush=True)
    save_frame(c.last_frame,OUT/'two_human_order_fight.png')
    # Elimination follows the chosen second and third positions on both pads.
    for side,expected in ((0,2),(0,0),(1,1),(1,0)):
        c.put(0x4010+(1-side)*0x40,200)
        c.put(0x4010+side*0x40,0)
        wait(c,lambda:c.ram[GS]==2,'human member KO')
        for _ in range(9000):
            assert c.ram[GS]!=ORDER,'order select appeared between human members'
            if c.ram[GS]==1:break
            c.step()
        else:raise AssertionError('human member replacement stalled')
        c.step(30)
        assert c.ram[0x1085+side]==expected
    print('PASS chosen second/third fighters enter consecutively on both pads',flush=True)
    c.put(0x4010,0)
    wait(c,lambda:c.ram[GS]==2,'P1 team loses')
    order_ready(c)
    assert list(c.ram[HUMAN:HUMAN+2])==[0,1]
    assert c.ram[0x10EA]==1,'P2 did not retain the campaign'
    choose(c,1,[2,0,1]);wait_fight(c)
    assert c.ram[0x1086]==0,'P2 winner order was ignored against CPU'
    print('PASS P2 campaign winner can reorder before the next CPU stage',flush=True)



def cpu_and_p2_only(c):
    enter_mode(c,2)
    c.ram[CPU1]=c.ram[CPU2]=1
    for _ in range(6000):
        assert c.ram[GS]!=ORDER, "both CPUs were asked for order"
        if c.ram[GS]==1:break
        c.step()
    else:raise AssertionError("CPU-only team did not launch")
    print('PASS CPU-only teams skip ORDER SELECT',flush=True)
    c.load(BOOT);c.buttons=[set(),set()]
    enter_mode(c,2);c.ram[CPU1]=1;c.ram[CPU2]=0
    wait(c,lambda:c.ram[SIDE]==1,'CPU finishes first trio')
    pick_team(c,1);order_ready(c)
    assert list(c.ram[HUMAN:HUMAN+2])==[0,1]
    cpu=list(c.ram[TEAM:TEAM+3])
    choose(c,1,[2,0,1]);wait_fight(c)
    assert list(c.ram[TEAM:TEAM+3])==cpu
    assert list(c.ram[TEAM+3:TEAM+6])==[2,0,1]
    print('PASS P2 alone orders while P1 CPU stays fixed',flush=True)


def other_modes(c):
    for mode in (0,1,4,5):
        enter_mode(c,mode)
        c.ram[0x1085]=0;c.ram[0x1086]=1
        c.ram[0x108E]=1;c.ram[0x108F]=1
        for _ in range(6000):
            assert c.ram[GS]!=ORDER,f'order select leaked into mode {mode}'
            if c.ram[GS]==1:break
            c.step()
        else:raise AssertionError(f'mode {mode} did not launch')
        print('PASS non-team-play mode',mode,'does not show ORDER SELECT',flush=True)
        c.load(BOOT)


def main():
    global BOOT
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--rom',type=Path,default=Path('kof98-snes.sfc'));args=ap.parse_args()
    OUT.mkdir(exist_ok=True);c=Core('/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so',args.rom);c.capture_video=True;BOOT=c.save()
    try:
        solo_campaign(c);c.load(BOOT);c.buttons=[set(),set()]
        two_humans(c);c.load(BOOT);c.buttons=[set(),set()]
        cpu_and_p2_only(c);c.load(BOOT);c.buttons=[set(),set()]
        other_modes(c)
    finally:c.close()


if __name__=='__main__':main()
