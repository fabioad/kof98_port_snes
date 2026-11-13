# CHR MSU: página de efeito roubava o vblank — 13/11/2026

## Sintomas

Em algumas lutas (exemplo: Daimon vs King) os lutadores congelavam na pose
anterior por até ~1,5 s, animações apareciam com um único quadro e, em casos
extremos, o personagem parecia sumir da tela. A HUD e o relógio continuavam
andando; `rt_msufail=0`, `tel_spfix=0` e `rt_oamdrop=0`.

## Causa

`FxPrepareBoth` roda no começo do vblank e, quando o atlas de um projétil
muda, dispara um DMA ROM→VRAM de **2048 bytes** para a página de efeito
(SPK1CHR/SPK2CHR). Esse DMA leva ~14 scanlines (medido: scanline 231 → 245).

O CHR dos lutadores usa DMA MSU→WRAM→VRAM e precisa de
`prefixo + 2 × 1536` bytes. Com o vblank já em 245, o teste de orçamento
recusava o chunk todos os frames (`scan + 23 >= 260`). Como o chunk continuava
"staged" (dono do seek), o lutador ficava sem nenhum upload enquanto o efeito
existisse.

Projéteis com quadros de 1 tick (ex.: o fogo do King) trocam de atlas a cada
frame, então o efeito mantinha o vblank ocupado por dezenas de frames
seguidos. Medições no baseline: `TEL_DROP` 74/128 e 149/149; idade média de
até 40 frames e máxima de 253; o chunk ficava staged por até 91 frames
seguidos.

## Correção

1. **Orçamento do CHR movido para `SprDmaFar` (bank 126).**
   `PresentSpriteFar` agora só desvia para `SprDmaFar`; o teste de vblank usa
   a scanline real no momento do DMA, com 1 linha de folga em vez das 3 linhas
   genéricas. HUD e animação de stage continuam re-checando o próprio
   orçamento em seguida, e um chunk recusado permanece staged para o próximo
   vblank.
2. **Chunk menor quando há página de efeito no vblank.**
   `DMACHUNK_FX = 768` é usado quando `RT_FXUPLOAD` (frame anterior) indica
   que o efeito usou o vblank. Assim o chunk do lutador ainda cabe em
   `prefixo + 2 × 768`.
3. **Projétil com quadro de 1 tick passa a durar no mínimo 2 ticks.**
   Só projéteis (bit7 de `SPK_ATTR`); sparks/explods continuam com o atlas
   estático em cache e mantêm a cadência original. Isso reduz a frequência de
   reenvio da página de 2048 bytes sem mexer nos hitboxes.

## Resultados (Snes9x headless, CPU vs CPU, nível 8)

| luta | drops P1/P2 | idade média | idade máx | streak staged |
| --- | --- | --- | --- | --- |
| Daimon vs King (antes) | 74/128 | 7,37/10,39 | 64/235 | 91 |
| Daimon vs King (depois) | 62/104 | 4,61/3,17 | 46/235 | 7 |
| King vs Daimon (antes) | 149/149 | 40,43/44,87 | 253/251 | 70 |
| King vs Daimon (depois) | 116/67 | 4,14/5,21 | 233/44 | 5 |
| Kyo vs Iori (referência) | 42/50 | 2,51/2,86 | 135/136 | 2 |

`probe_framerate_headless.py 13:24` passou de 48,55 para 48,88 fps; sem
`rt_msufail`, `tel_spfix` ou `rt_oamdrop`. Os drops restantes são o limite de
banda do stream compartilhado (um seek MSU por frame), não mais starvation.

## Arquivos

- `src/engine/frame_present.asm`: `PresentSpriteFar` delega para `SprDmaFar`.
- `src/snes/fight_bridge.asm`: orçamento por scanline em `SprDmaFar` e novo
  `SprRoomFar` (bank 126, $C580).
- `src/engine/fight.asm`: `DMACHUNK_FX`, cap adaptativo em `SprPrepOne`,
  mínimo de 2 ticks por quadro de projétil e telemetria `RT_SPR_SCAN/LINES`.
