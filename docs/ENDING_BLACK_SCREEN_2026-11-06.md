# Ending black screen after Omega Rugal

The failure reproduced in TEAM PLAY and SINGLE PLAY. Reverting only the
accumulator-width fix in a temporary ROM also reproduces it in SURVIVOR:
`ending crashed after its first frame`.

`OpnApply` returns with the accumulator in 16-bit mode. The next instruction
at `FP_present_on` is assembled as an 8-bit immediate load. Without `SEP #$20`,
the CPU consumes the following STA opcode as the high byte of the immediate,
decodes the remaining bytes incorrectly and eventually corrupts WRAM. The
ending state has already been entered at this point, so tests that only wait
for GS_END falsely pass. This is shared presentation code, independent of
ORDER SELECT.

The fix explicitly restores the 8-bit accumulator at `FP_present_on`.

Validation with the installed Snes9x libretro core and the rebuilt
`kof98-snes.sfc` plus matching MSU data:

- `python3 tools/test_boss_intro_headless.py`: normal Rugal to Omega entrance,
  Omega KO to ending and continuing palette/timer activity in all campaigns;
  the Single Play round-2 entrance regression also passes.
- `python3 tools/test_endings.py`: actual campaign boss transitions, rendered
  pixel/color checks, unique card images, running timers, every automatic
  transition and return to title. SINGLE PLAY: 23 cards; TEAM PLAY: 23;
  SURVIVOR: 13. No direct ending-gamestate injection.
- Screenshots: `build/ending_regression/{single,team,survivor}_NN.png`.
- Logs: `build/ending_fix_all_cards.log`, `build/ending_fix_boss_tests.log`.

SINGLE VS, TEAM VS and PRACTICE do not have campaign endings.
