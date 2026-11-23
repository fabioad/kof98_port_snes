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
| `ja.json` | 4 (Japanese) |

The OPTIONS > LANGUAGE row stores the selected index in `Q_LANG`
(`$F07F`, one byte); the next victory screen uses it.  `FightMain` initialises
it to 0 at power-on only, so changing it in OPTIONS persists across matches.

## Formatting

Quotes are word-wrapped into at most two rows of 30 glyphs and folded onto the
lifebar font.  For Latin languages that font contains
`A-Z 0-9 . : ! ? ' - / +` and space, so accented source text is transliterated
(`VOCÊ` -> `VOCE`, `ÇA` -> `CA`, `¡`/`¿` are dropped).  Keep each quote at 60
characters or less after transliteration; `tools/tests/test_quotes.py`
validates this.

Japanese uses the kana table added for the JAPANESE option
(`tools/kana_charset.py`, glyphs in `assets/fonts/kana8.chr`).  The 8x8 font
has no kanji room, so `ja.json` is written in hiragana/katakana; full-width
`！？` and `…` are folded by NFKC to the ASCII punctuation already present.
The fight HUD has no free 173-tile BG3 window, so the build uses the first
Japanese quote of each fighter and stores only the kana it needs.  At the
first match-over frame `JaQuotePrepare` copies those glyphs into the 20 free
BG3 tiles (1004..1023) plus 13 ASCII slots the win screen does not draw
(41..53); the quote row uses per-quote slot codes.  All four runtime slots
show that same first quote.

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

### Mr. Karate (Robert variant)

Source: [SNK Wiki — Mr. Karate/Quotes](https://snk.fandom.com/wiki/Mr._Karate/Quotes).
The four slots are free adaptations for the two-row HUD: Kyokugen's
invincibility (KOF '96 Game Boy), the training criticism and masked identity
(SVC Chaos), and Yuri's safety (Art of Fighting's Ryo pre-battle dialogue,
rephrased for the victory screen). They are adaptations, not verbatim dialogue.
The speaker is Robert: self-identification uses Robert, and Yuri is addressed
as "my love" / "meu amor" / "mi amor" / "mon amour", never as his sister.

### Jason, John and Lucia (GTA tribute trio)

- **John Crawley**: [SNK Wiki — John Crawley/Quotes](https://snk.fandom.com/wiki/John_Crawley/Quotes)
  (Art of Fighting 2 win quotes, cross-checked with the GameFAQs AOF2 quote
  list). Slots 1/2 are the English win quotes, slot 3 is the Japanese win
  quote ("I've seen hell on the battlefield..."), slot 4 the short "That all
  you've got? That's too bad."
- **Jason and Lucia**: lines transcribed from the characters' own voice banks
  (`Jason_Quotes.md` / `Lucia_Quotes.md`, groups 12 and 13). The victory slots
  reuse the taunt/victory lines ("Stuck together..." / "What matters is who
  you know..."), shortened to fit the two 30-column rows.
- **CJ (Carl Johnson)**: [GTA Fandom — Carl Johnson/Quotes](https://gta.fandom.com/wiki/Carl_Johnson/Quotes),
  picking lines from the "Car-jacking", "Fighting" and "Shooting pedestrians"
  groups: "Welcome to San Andreas, fool!", "You picked the wrong playa, fool!",
  "Is that the best you got? Too bad." and "CJ, remember the name!". The
  stronger profanity is dropped because the lifebar font only carries
  `A-Z 0-9 . : ! ? ' - / +`; the street tone stays.

Translations are free adaptations. John keeps his AOF2 bravado in all four
languages; Jason/Lucia keep the trailer dialogue's tone; CJ keeps the San
Andreas slang ("playa", "fool", Ganton bravado) in every language.
References to an opposing Ryo remain references to Ryo.
