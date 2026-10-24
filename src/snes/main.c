#include <snes.h>

/*
 * PVSnesLib owns reset, the ROM header and the outer NMI dispatcher.  The
 * existing fight engine remains hand-written 65816 and is entered only after
 * the library has established the C runtime.
 */
extern void FightMain(void);
extern char SOUNDBANK__;                /* soundbank base (Makefile aliases
                                           SOUNDBANK__0 -> SOUNDBANK__) */

volatile u8 audiomarker;

void BootAudio(void)
{
    int j;
    audiomarker = 1;
    spcBoot();
    audiomarker = 2;
    spcSetBank(&SOUNDBANK__);
    audiomarker = 3;
    spcAllocateSoundRegion(18);         /* 4.5KB stream buffer: the longest
                                           character voice is 375 BRR blocks
                                           (3375 B), so 18*256 covers it and
                                           leaves ARAM for the stage module +
                                           combat effects. */
    spcLoad(1);                         /* module 1 = stage 0 (Esaka) */
    /* No spcFlush() here: the library routine corrupts the stack when the
       fifo is not empty (see SpcFlushSafe in fight.asm).  Nothing has been
       queued yet and spcLoad is synchronous, so there is nothing to drain. */
    audiomarker = 4;
    {
        /* Bootstrap effects used by the MSU status screen.  Later screen
           and stage changes reload their own module and effect directory. */
        static const u8 fx[] = { 0, 1, 2, 5, 6, 4, 13, 12 };
        for (j = 0; j < (int)sizeof(fx); j++) { spcLoadEffect(fx[j]); }
    }
    audiomarker = 5;
    /* Keep the driver running, but leave the bootstrap stage silent until
       the opening selects and loads its own frontend module. */
    spcPlay(0);
    spcSetModuleVolume(0);
    audiomarker = 6;
}

int main(void)
{
    BootAudio();
    FightMain();

    /* FightMain is the game loop and does not return. */
    return 0;
}
