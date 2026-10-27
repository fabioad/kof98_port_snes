# Travamento Clark × Ralf — cancelamento de guarda (27/10/2026)

## Sintoma

No SNES real, a luta **Clark × Ralf** trava: o relógio e os lutadores
param, a tela fica no último quadro (sem menu) e o áudio continua. A
foto do momento mostra o Clark no meio de um **rolamento/dodge**
(pernas afastadas, braços à frente), com a barra de vida cheia e o
relógio em 96.

## Causa

O travamento é uma corrupção do fluxo de instruções no caminho de
**cancelamento de guarda / rolamento**, não um softlock de estado. Havia
duas misturas de largura de acumulador, o mesmo tipo de erro que já
derrubou `CancelGate`/`FlushHudLive`/`ComboDraw`:

### 1. `GCancelGo` (`src/engine/fight.asm`)

O caminho Y+B / X+A durante a guarda entra no rolamento (94/95) ou no
blowback (67) e gasta um stock. Depois de `jsr EnterState` o código fazia:

```asm
pla             ; A = sid
cmp #94.w
...
lda #14.b       ; A está em 16 bits aqui
sta F_INVUL,x
lda #4.b
sta F_PFX,x
```

Duas falhas no mesmo trecho:

- `lda #14.b` / `lda #4.b` em A16: o imediato de 8 bits é lido como parte
  do endereço da instrução seguinte, desalinhando o fluxo.
- `EnterState` **retorna com A=8** quando o estado tem ActTab (é o caso de
  94/95: `clarkActTab` aponta para `clarkAct59/5A`). O `pla` seguinte
  então puxava só 1 byte, e `cmp #94.w`/`#96.w` executavam um imediato de
  16 bits no modo 8 bits — o byte `$00` virava BRK.

### 2. `CMC_roll` (`src/engine/fight.asm`)

O cancelamento de ataque da FUSION (ESQ_F/ESQ_B durante um hit-cancel)
chega em `CMC_roll` com A=8, mas lia o medidor de 16 bits:

```asm
lda F_POWER,x
cmp #1000.w
sbc #1000.w
sta F_POWER,x
```

Um imediato de 16 bits em modo 8 bits consome o opcode seguinte como
parte do valor. A rota é a mesma dos estados 94/95.

## Correção

1. `GCancelGo`: `rep #$20` / `.ACCU 16` depois de `jsr EnterState`, e
   `lda #14.w` / `lda #4.w`. O `pla` e os `cmp` de 16 bits voltam a casar
   com o que foi empilhado.
2. `CMC_roll`: `rep #$20` / `.ACCU 16` antes de ler/comparar/subtrair o
   medidor.
3. `MtCell` (select): `lda #$30.b` → `lda #$30.w`, também A16; era latente
   (pulava um store) mas foi corrigido.
4. Para caber no banco de 32 KiB, removido um `rep #$20` redundante depois
   de `jsr FillBar` (FillBar já retorna com A=16).

Nenhum DMA, HUD ou caminho de voz foi alterado nesta rodada.

## Validação

- Novo `tools/test_guard_cancel_headless.py`:
  - Y+B durante a guarda → estado **94**, power 3000→2000, luta continua;
  - X+A durante a guarda → estado **67**, power 2000, luta continua.
- No emulador, o cancelamento de ataque F+C durante um hit-cancel chega ao
  estado **95** e gasta 1000 de power (mesmo caminho do `CMC_roll`).
- `test_cancel_headless.py`, `test_sf_cancel_headless.py`,
  `test_combo_reset_headless.py`, `test_ai_headless.py`,
  `test_msu_voice_alignment_headless.py`,
  `test_msu_chr_visibility_headless.py` (960 páginas),
  `test_hud_bands_headless.py` e `test_start_transition.py`: PASS.
- `python3 -m unittest discover -s tools/tests`: 174 testes OK.
- Build PVSnesLib + `make verify`: OK.

## Hashes

- ROM `kof98-snes.sfc`: checksum **`$E047`**, SHA-256
  `b0433796…c7dc89`.
- MSU `kof98-snes.msu`: SHA-256 `3e8945c3…868de386` (inalterado).

Rollback: tag `backup-pre-powerbar-fix-20261026` e
`backup/powerbar_pre_20261026/`.
