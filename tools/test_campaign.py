#!/usr/bin/env python3
"""Drive SINGLE PLAY / TEAM PLAY campaign transitions over the UDP remote."""
import sys
import time
sys.path.insert(0, str(__file__ if isinstance(__file__, str) else '.'))
from test_fight_remote import RetroArch, CORE, ROM

DP = 0x1000          # ENGINE_DP base: gamestate $20, framecnt $24,
                     # wins1 $80 wins2 $81 roundno $82 nextflag $84
                     # sel1 $85 sel2 $86 stageidx $87 rng $88
GS    = DP + 0x20
FCNT  = DP + 0x24
WIN_TIMER = 0x107B   # DP+$7B: free pad in the $78-$7F tail
WINS1 = DP + 0x80
WINS2 = DP + 0x81
NEXTF = DP + 0x84
SEL1  = DP + 0x85
SEL2  = DP + 0x86
STAGE = DP + 0x87
CPU1  = DP + 0x90
CPU2  = DP + 0x91

G_MODE = 0xF040
C_IDX  = 0xF041
C_USED = 0xF042
C_STAGE= 0xF044
T_STEP = 0xF047
T_I1   = 0xF048
T_I2   = 0xF049
T_N2   = 0xF04A
T_TEAM1= 0xF04B
T_TEAM2= 0xF04E
T_SWAP = 0xF051
E_SCR  = 0xF078

FP1HP = 0x4000 + 16
FP2HP = 0x4040 + 16


def rb(ra, a):
    return ra.read_ram(a, 1)[0]


def wr(ra, a, v):
    ra.command_no_reply(f"WRITE_CORE_RAM {a:X} {v:02X}")


def press(ra, user, btn, hold=0.12):
    ra.button(user, btn, True); time.sleep(hold)
    ra.button(user, btn, False); time.sleep(0.12)


def wait_gs(ra, gs, timeout=20):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if rb(ra, GS) == gs:
            return True
        time.sleep(0.1)
    return False


def wrv(ra, a, v, tries=25):
    """Write with readback retry — fire-and-forget UDP writes can drop."""
    for _ in range(tries):
        wr(ra, a, v)
        try:
            if rb(ra, a) == v:
                return
        except Exception:
            pass
        time.sleep(0.02)


def win_match(ra):
    """Pretend the player just took the confrontation."""
    for _ in range(25):
        wrv(ra, WINS1, 2); wrv(ra, WINS2, 0)
        wr(ra, NEXTF, 2); wr(ra, WIN_TIMER, 0xA3)
        wr(ra, WIN_TIMER + 1, 1); wr(ra, GS, 0)
        if rb(ra, GS) != 1:
            return


def team_match_over(ra, won=1):
    """Pretend a team confrontation just resolved (MATWON=won)."""
    for _ in range(25):
        wrv(ra, 0xF046, won)
        wr(ra, NEXTF, 2); wr(ra, WIN_TIMER, 0xA3)
        wr(ra, WIN_TIMER + 1, 1); wr(ra, GS, 0)
        if rb(ra, GS) != 1:
            return


def run(ra):
    # --- boot: intro -> title -> menu -------------------------------------
    end = time.monotonic() + 20
    while rb(ra, GS) != 7 and time.monotonic() < end:
        time.sleep(0.2)
    assert rb(ra, GS) == 7, "no intro"
    end = time.monotonic() + 20            # skip intro (retry: UDP drops)
    while rb(ra, GS) != 0 and time.monotonic() < end:
        press(ra, 0, "START")
        time.sleep(0.2)
    assert rb(ra, GS) == 0, "no title"
    press(ra, 0, "START")                    # -> mode menu
    assert wait_gs(ra, 6), "no menu"

    # --- SINGLE PLAY ------------------------------------------------------
    press(ra, 0, "A")                        # item 0 = SINGLE PLAY
    assert wait_gs(ra, 5), "no select"
    assert rb(ra, G_MODE) == 1, f"G_MODE={rb(ra,G_MODE)}"
    for _ in range(25):                      # sel/lock writes can race the
        wrv(ra, 0x1085, 0)                   #   select-draw reset: retry the
        wrv(ra, 0x1086, 1)                   #   whole batch until the fight
        wrv(ra, 0x108E, 1); wrv(ra, 0x108F, 1)   # lock1/lock2, Kyo vs Iori
        if wait_gs(ra, 1, 1.5):
            break
    if rb(ra, GS) != 1:
        print("DBG gs=%d tick=%d sdo=%d/%d chk=%02x l=%d,%d A5=%02x A6=%02x A7=%02x sm=%02x fc=%d stage=%d" % (
            rb(ra,GS), rb(ra,0xF19E), rb(ra,0xF19F), rb(ra,0xF1A0),
            rb(ra,0xF19B), rb(ra,0xF19C), rb(ra,0xF19D),
            rb(ra,0xF1A5), rb(ra,0xF1A6), rb(ra,0xF1A7), rb(ra,0xF1A1),
            rb(ra,FCNT), rb(ra,STAGE)))
        time.sleep(2)
        print("DBG+2s gs=%d fc=%d (fc still=%s)" % (rb(ra,GS), rb(ra,FCNT), rb(ra,FCNT)))
    assert rb(ra, GS) == 1, "no fight"
    st = rb(ra, STAGE)
    assert st != 5, f"common fight on rugal stage {st}"
    s2 = rb(ra, SEL2)
    assert s2 not in (3, 14), f"cpu picked campaign boss {s2}"
    print("single f1 ok  sel2=%d stage=%d" % (s2, st))

    # confrontations 2-7 (the seventh is Rugal)
    seen = {s2}
    for i in range(1, 7):
        win_match(ra)
        assert wait_gs(ra, 1, 15), f"fight {i+1} did not start"
        ci = rb(ra, C_IDX)
        st = rb(ra, STAGE)
        s2 = rb(ra, SEL2)
        print(f"  fight{i+1}: cidx={ci} sel2={s2} stage={st}")
        if i < 6:
            assert ci == i, f"cidx {ci} != {i}"
            assert s2 not in (3, 14), f"boss early at fight {i+1}"
            assert st != 5, "rugal stage early"
            seen.add(s2)
        else:
            assert ci == 6 and s2 == 14 and st == 5, \
                f"boss wrong: cidx={ci} sel2={s2} stage={st}"
    print("single boss ok (Rugal @ stg5)")

    # beat Rugal -> endings
    win_match(ra)
    assert wait_gs(ra, 8, 15), "endings did not start"
    e0 = rb(ra, E_SCR)
    time.sleep(6)                           # END_HOLD=300 (~5s) + fades
    e1 = rb(ra, E_SCR)
    assert e1 > e0, "ending not advancing"
    print(f"endings running scr {e0}->{e1}; waiting for title...")
    end = time.monotonic() + 40
    while time.monotonic() < end:
        g = rb(ra, GS)
        if g == 0:
            break
        press(ra, 0, "START")               # skip remaining ending screens
        time.sleep(0.5)
    assert rb(ra, GS) == 0, "did not return to title"
    assert rb(ra, G_MODE) == 0 and rb(ra, C_IDX) == 0, "campaign not reset"
    print("single campaign complete -> title, state reset")

    # --- TEAM PLAY --------------------------------------------------------
    press(ra, 0, "START")                    # title -> menu
    assert wait_gs(ra, 6), "no menu 2"
    press(ra, 0, "DOWN"); press(ra, 0, "DOWN")   # -> item 2 TEAM PLAY
    press(ra, 0, "A")
    assert wait_gs(ra, 5), "no team select"
    assert rb(ra, G_MODE) == 2, f"G_MODE={rb(ra,G_MODE)}"
    for _ in range(25):                      # two members forced, third via
        wrv(ra, T_TEAM1, 0)                  #   a real pad lock (retried: the
        wrv(ra, T_TEAM1+1, 1)                #   batch can race select draws)
        wrv(ra, T_STEP, 2)
        wrv(ra, 0xF052, 5)                   # SCUR1 -> cell of char2 (Kyo
        press(ra, 0, "A")                    #   sits at cell 5); A locks
        if wait_gs(ra, 4, 1.5) or wait_gs(ra, 1, 8):
            break
    assert rb(ra, GS) in (1, 4), "team fight did not start"
    t1 = [rb(ra, T_TEAM1+i) for i in range(3)]
    t2 = [rb(ra, T_TEAM2+i) for i in range(3)]
    assert len(set(t1)) == 3, f"dup in player team {t1}"
    assert len(set(t2)) == 3 and all(c < 3 for c in t2), f"bad cpu trio {t2}"
    print(f"team fight ok  T1={t1} T2={t2}")

    # force a P2 member out -> TeamSwap must swap in T_TEAM2[1]
    for _ in range(25):
        wrv(ra, T_SWAP, 2); wrv(ra, T_I2, 1)
        wr(ra, NEXTF, 1); wr(ra, FCNT, 59); wr(ra, GS, 0)
        if wait_gs(ra, 4, 1.5) or wait_gs(ra, 1, 8):
            break
    assert rb(ra, GS) in (1, 4), "member swap did not resume fight"
    s2 = rb(ra, SEL2)
    assert s2 == t2[1], f"member 2 not swapped in: sel2={s2} t2={t2}"
    assert rb(ra, FP2HP) == 200 or rb(ra, FP2HP+1) > 0, "new member HP"
    print(f"member swap ok: P2 now {s2}, hp={rb(ra,FP2HP)+rb(ra,FP2HP+1)*256}")

    # jump to boss: pretend confrontation 5 was just won
    wr(ra, C_IDX, 5)
    team_match_over(ra)
    assert wait_gs(ra, 1, 15), "boss fight did not start"
    assert rb(ra, C_IDX) == 6 and rb(ra, T_N2) == 1, "team boss setup"
    assert rb(ra, SEL2) == 14 and rb(ra, STAGE) == 5, "team boss char/stage"
    print("team boss ok (Rugal solo @ stg5)")

    # beat Rugal -> endings again
    team_match_over(ra)
    assert wait_gs(ra, 8, 15), "team endings missing"
    end = time.monotonic() + 40
    while time.monotonic() < end and rb(ra, GS) != 0:
        press(ra, 0, "START")
        time.sleep(0.5)
    assert rb(ra, GS) == 0, "no title after team endings"
    print("team campaign complete -> title")
    print("ALL CAMPAIGN TESTS PASSED")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--retroarch", default="retroarch")
    ap.add_argument("--core", default=CORE)
    args = ap.parse_args()
    ra = RetroArch()
    try:
        if args.launch:
            ra.launch(args.retroarch, args.core)
        ra.wait_ready()
        run(ra)
    finally:
        ra.close()


if __name__ == "__main__":
    sys.exit(main())
