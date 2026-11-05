# Banner COUNTER cortado pela metade — 03/11/2026

## Sintoma

Durante a luta, o aviso **COUNTER** (golpe de contra-ataque) aparecia apenas
com a metade superior das letras.

## Causas

1. `CounterTxt` é gerado a partir da fonte grande compartilhada
   (`big_ids` em `tools/build_fight.py`). Cada letra é um glifo 8x16 formado
   por **dois tiles consecutivos** (topo e base). O `CounterDraw` usava
   `WriteStr`, que desenha uma única linha e grava só o tile do topo.
2. A linha do banner (10, com a base na 11) fica fora das bandas de upload
   do HUD ao vivo (`HudBandTab` cobre vida, poder, contador de poder, timer e
   combo). O `CounterDraw` só fazia `inc huddirty`, que não corresponde a
   nenhuma banda: o texto podia nem chegar à VRAM, ou aparecer só quando
   outro overlay forçava um upload completo.

## Correção

- `CounterDraw` passou a escrever as duas linhas com `CounterStrBig`, um
  escritor 8x16 dedicado. Ele usa `scr0` como contador do laço, porque o
  caminho de hit guarda o índice de estado do atacante em `scr4` e lê as
  tabelas de dano depois de `CounterDraw` — usar `scr4` derrubava o dano do
  reversal de 26 para 1.
- `CounterDraw` e `CounterClear` forçam upload completo
  (`RT_HUDFULL` + `HUD_FULL`), como já fazem o logo FIGHT!, a pausa e o
  YOU LOSE para linhas fora das bandas. O clear apaga as duas linhas.
- Para não estourar a janela `CancelData` (que termina antes de `OamCache`
  em `$0A00`), o escritor foi para a janela livre `$70C0` e o desenho/clear
  para `$7F98`, ambos no mesmo banco 50 do `Fight`.

## Verificação

- Novo `test_counter_banner_headless`: força um counter hit e confere os 7
  tiles do topo na linha 10, os 7 tiles `+1` na linha 11, conclui o upload
  completo e, após os 30 ticks do flash, confirma as duas linhas apagadas.
- `test_youlose_headless`: o cursor do YOU LOSE usa `scr0` depois de
  `WriteStrBig`; continua passando.
- `test_yamazaki_reversal_headless`: o reversal/counter hit continua com
  32/26/26 de dano; confirma que `scr4` não é mais clobberado.
- `test_counter_grab_headless`: todos os grabs de contra-ataque continuam.
- Demais regressões (Team, Single, Benimaru, Ralf mount, demo, MSU, VRAM):
  PASS. `pytest -q tools/tests`: 269 passed.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$A9AD`**
- layout MSU **`0x3310`**
- `.sfc` SHA-256 `8ef11dee…f4dbdf`
- `.msu` SHA-256 `3841c9af…b2809b` (novo; copie os dois juntos)
