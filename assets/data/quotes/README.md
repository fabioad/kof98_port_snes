# Victory quotes

Each JSON file maps a roster key (the same keys used by `tools/build_fight.py`)
to 1-4 victory quotes.  The win screen cycles through four slots, so shorter
lists are padded by repeating the last quote.

| File | Runtime value (`Q_LANG`) |
| --- | --- |
| `en.json` | 0 (English, default) |
| `pt-BR.json` | 1 (Portuguese - Brazil) |
| `es.json` | 2 (Spanish) |
| `fr.json` | 3 (French) |

The OPTIONS > LANGUAGE row stores the selected index in `Q_LANG`
(`$F07F`, one byte); the next victory screen uses it.  `FightMain` initialises
it to 0 at power-on only, so changing it in OPTIONS persists across matches.

## Formatting

Quotes are uppercased, word-wrapped into at most two rows of 30 glyphs, and
folded onto the lifebar font.  That font only contains
`A-Z 0-9 . : ! ? ' - / +` and space, so accented source text is transliterated
(`VOCÊ` -> `VOCE`, `ÇA` -> `CA`, `¡`/`¿` are dropped).  Keep each quote at 60
characters or less after transliteration; `tools/tests/test_quotes.py`
validates this.

## Sources

- KOF '98 in-game win quotes, cross-checked with the SNK Wiki, KOF Fandom and
  English Wikiquote character pages.
- Street Fighter Alpha 2 quotes for Ryu, Ken, Chun-Li, Sakura and Vega, from
  the GameFAQs Quotes/Dialogue Guide (FAQ 916) and the Street Fighter Wiki.
  M. Bison (Vega in Japan) uses quotes from the Street Fighter II series,
  prioritizing Street Fighter II and Super Street Fighter II Turbo HD Remix,
  from the Street Fighter Wiki `M._Bison/Quotes` page.
- Fatal Fury / Art of Fighting quotes for the SNK guest characters.

Translations are free adaptations kept short enough for the 30x2 HUD rows.
