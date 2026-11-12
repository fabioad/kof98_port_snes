/*---------------------------------------------------------------------------------
    KOF98 SNES - USA Yard (stg9) lead options sound test (SNESMOD)
    Generated project: music/ffg_hq/tools/make_stg9_lead_test.py

    UP/DOWN    : select version
    A / START  : play from the start
    X / Y      : play from order 7 (long lead notes)
    L / R / SEL: previous / next version, restarting at the same start point
    B          : stop
---------------------------------------------------------------------------------*/
#include <snes.h>

#include "res/soundbank.h"
#include "songs.h"

#define LEADPOS 7

extern char snesfont, snespal;

static u16 sel, playing, startpos, pad, prev, down;

static void drawList(void)
{
    u16 i;
    for (i = 0; i < NSONGS; i++)
    {
        consoleDrawText(1, 6 + i * 2, i == sel ? ">" : " ");
        consoleDrawText(3, 6 + i * 2, (char *)names[i]);
        consoleDrawText(23, 6 + i * 2, i == playing ? "TOCANDO" : "       ");
    }
    consoleDrawText(3, 18, startpos ? "INICIO: TRECHO 7 (LEAD)" : "INICIO: COMECO         ");
}

static void playSong(u16 s, u16 pos)
{
    spcStop();
    spcLoad(s);
    spcPlay(pos);
    playing = s;
    startpos = pos;
}

int main(void)
{
    spcBoot();

    consoleSetTextMapPtr(0x6800);
    consoleSetTextGfxPtr(0x3000);
    consoleSetTextOffset(0x0100);
    consoleInitText(0, 16 * 2, &snesfont, &snespal);

    registerBanks();

    bgSetGfxPtr(0, 0x2000);
    bgSetMapPtr(0, 0x6800, SC_32x32);
    setMode(BG_MODE1, 0);
    bgSetDisable(1);
    bgSetDisable(2);

    consoleDrawText(3, 1, "KOF98 SNES - USA YARD (STG9)");
    consoleDrawText(3, 2, "OPCOES DO LEAD DE GUITARRA");
    consoleDrawText(2, 21, "A:TOCAR  X/Y:TRECHO 7");
    consoleDrawText(2, 22, "L/R/SEL:VERSAO  B:PARAR");

    sel = 0;
    playing = 0xff;
    startpos = 0;
    setPaletteColor(0x00, RGB5(0, 0, 4));
    setScreenOn();

    playSong(0, 0);
    drawList();

    prev = 0;
    while (1)
    {
        pad = padsCurrent(0);
        down = pad & ~prev;
        prev = pad;

        if (down & KEY_DOWN)
        {
            sel = (sel + 1) % NSONGS;
            drawList();
        }
        if (down & KEY_UP)
        {
            sel = (sel + NSONGS - 1) % NSONGS;
            drawList();
        }
        if (down & (KEY_R | KEY_SELECT))
        {
            sel = (sel + 1) % NSONGS;
            playSong(sel, startpos);
            drawList();
        }
        if (down & KEY_L)
        {
            sel = (sel + NSONGS - 1) % NSONGS;
            playSong(sel, startpos);
            drawList();
        }
        if (down & (KEY_A | KEY_START))
        {
            playSong(sel, 0);
            drawList();
        }
        if (down & (KEY_X | KEY_Y))
        {
            playSong(sel, LEADPOS);
            drawList();
        }
        if (down & KEY_B)
        {
            spcStop();
            playing = 0xff;
            drawList();
        }

        spcProcess();
        WaitForVBlank();
    }
    return 0;
}
