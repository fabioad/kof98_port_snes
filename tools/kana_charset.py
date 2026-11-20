"""Kana glyph order used by the 8x8 HUD font and the menu font.

The order is stable: generated text stores the *tile id* (not the index in
this string), so append new characters at the end and regenerate
assets/fonts/kana8.chr with tools/build_kana_font.py.
"""

HIRAGANA = ("あいうえおかきくけこさしすせそたちつてとなにぬねの"
            "はひふへほまみむめもやゆよらりるれろわをん")
HIRAGANA_VOICED = ("がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ")
HIRAGANA_SMALL = "ぁぃぅぇぉっゃゅょゎ"

KATAKANA = ("アイウエオカキクケコサシスセソタチツテトナニヌネノ"
            "ハヒフヘホマミムメモヤユヨラリルレロワヲン")
KATAKANA_VOICED = ("ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ")
KATAKANA_SMALL = "ァィゥェォッャュョヮ"

PUNCTUATION = "ー・゛゜。、！？「」…"

KANA = (HIRAGANA + HIRAGANA_VOICED + HIRAGANA_SMALL +
        KATAKANA + KATAKANA_VOICED + KATAKANA_SMALL + PUNCTUATION)
