/*---------------------------------------------------------------------------------
    KOF98 SNES - FFG HQ sound test (SNESMOD)

    Every song exists twice in the soundbank: the module the game ships now
    ("ATUAL") and the new full-arrangement conversion ("NOVA").

    UP/DOWN        : select song
    A / START      : play the selected version
    SELECT / L / R : switch ATUAL <-> NOVA (restarts the song if playing)
    B              : stop
---------------------------------------------------------------------------------*/
#include <snes.h>

#include "res/soundbank.h"
#include "songs.h"

extern char snesfont, snespal;

static u16 sel, ver, playing, playver, pad, prev, down;

static void drawList(void)
{
    u16 i;
    for (i = 0; i < NSONGS; i++)
    {
        consoleDrawText(1, 5 + i, i == sel ? ">" : " ");
        consoleDrawText(3, 5 + i, (char *)names[i]);
        if (i == playing)
            consoleDrawText(24, 5 + i, playver ? "NOVA " : "ATUAL");
        else
            consoleDrawText(24, 5 + i, "     ");
    }
    consoleDrawText(3, 23, ver ? "VERSAO: NOVA  (FFG HQ) " : "VERSAO: ATUAL (NO JOGO)");
}

static void playSong(u16 s)
{
    spcStop();
    spcLoad(ver ? s : s + NSONGS);
    spcPlay(0);
    playing = s;
    playver = ver;
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

    consoleDrawText(3, 1, "KOF98 SNES SOUND TEST FFG HQ");
    consoleDrawText(3, 2, "ATUAL X NOVA (SNESMOD)");
    consoleDrawText(2, 25, "A:TOCAR B:PARAR SEL/L/R:VERSAO");

    sel = 0;
    ver = 1;
    playing = 0xff;
    setPaletteColor(0x00, RGB5(0, 0, 4));
    setScreenOn();

    playSong(0);
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
        if (down & (KEY_SELECT | KEY_L | KEY_R))
        {
            ver ^= 1;
            if (playing != 0xff)
                playSong(playing);
            drawList();
        }
        if (down & (KEY_A | KEY_START))
        {
            playSong(sel);
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
