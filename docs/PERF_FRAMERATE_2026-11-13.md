# Luta CPU vs CPU perto de 60 fps — 13/11/2026

## Sintoma

O par mais pesado (Daimon vs King, `13:24`) rodava a **48,5 fps**
(`probe_framerate_headless.py --frames 2400`).

## Diagnóstico

Perfil de instruções (Mesen, 600 quadros de luta) e linha do tempo por
scanline do laço principal:

- **41% das instruções da luta rodavam em SlowROM.** `fast_paths.asm`
  (DrawCells, BOFill, HpToPx, PowToPx…) morava no banco 64 = `$40:xxxx`, que
  no ExHiROM é SlowROM mesmo com FastROM ligado: 8 ciclos por busca de
  opcode em vez de 6.
- `VoiceQueueTickFar` custava até **95 scanlines** num quadro:
  - cópia MSU→WRAM byte a byte em SlowROM (`MRA_copy_payload`);
  - até 511 bytes de prefixo de setor lidos e descartados **a cada** pedaço
    de 512 bytes (o cursor de voz não era alinhado ao setor);
  - `spcPlaySoundV`/`spcProcess` depois, com picos de 41 linhas.
- Essa voz rodava no começo do quadro, junto com `FightTick`: 21 dos 32
  quadros que perdiam tick vinham dela.

## Mudanças

- `src/engine/fast_paths.asm`: seção movida para banco FastROM (31 = `$DF`),
  via `FREE` (o linker escolhe a posição). 34,6% das instruções da luta
  passaram a rodar em FastROM.
- `MsuCopyFar` (novo, `fast_paths.asm`): cópia MSU→WRAM desenrolada (x8 para o
  prefixo, x16 para o payload) e em FastROM. `MsuReadAlignedFar` só calcula o
  destino e chama; o port continua no caminho de dados da CPU (DMA de MSU
  intercalado já corrompeu CHR no SD2SNES).
- `src/engine/voice_queue.asm`: cada pedaço de voz termina em fronteira de
  setor (`VOICE_CHUNK` = 512), então o prefixo é lido uma vez por fala.
- `VoiceQueueSlackFar`: em luta (gs 1) a fila de voz roda na folga do quadro
  anterior (topo do `MainLoop`), só quando V < 168 e o seek de CHR está
  livre; se faltar folga por 2 quadros ela volta ao slot antigo, então a voz
  nunca deixa de tocar.

## Resultado (2400 quadros, Snes9x headless)

| par | antes | depois |
|---|---|---|
| 13:24 | 48,53 | **54,36** |
| 2:3 | 53,52 | **57,11** |
| 4:5 | 56,00 | **58,85** |
| 10:20 | 54,79 | **58,03** |
| 30:40 | 52,73 | **54,65** |
| 45:46 | 57,07 | **58,70** |
| 12:33 | 56,93 | **58,97** |
| 7:9 | 58,70 | **59,77** |
| 0:1 | 57,75 | **59,58** |

`rt_msufail`, `rt_oamdrop` e `tel_spfix` ficam em 0 em todos os pares.

## Verificação

- `test_msu_voice_alignment_headless`: PASS 21 falas, bytes idênticos ao
  `.msu` (exercita `MsuCopyFar` e o alinhamento novo).
- `test_voice_cancel_headless`, `test_voice_transition_leak`,
  `test_team_vs_start_headless`, `test_select_pause_headless`: PASS.
- `test_hud_bands_headless`, `test_voice_stream`, `test_king_voice_headless`
  e `test_round_voice_headless` falham igual à ROM anterior (pré-existentes).
- Quadro de King vs Daimon idêntico byte a byte ao da ROM anterior.

## O que sobra

Os pares 13:24 e 30:40 ainda ficam em ~54,5: os ticks perdidos vêm só de
quadros pesados de `FightTick` (p90 177, máximo ~300 linhas) com projéteis e
efeitos ativos — mesma área do `docs/MSU_FX_VBLANK_2026-11-13.md`.
