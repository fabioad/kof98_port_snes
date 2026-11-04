# CHR MSU no SNES real — DMA seguro e recuperação de velocidade

## Sintomas

1. Chars MSU controlados pelo P2 apareciam com sprites cortados/sumindo no
   SD2SNES.
2. A primeira correção (DMA sob forced blank) eliminou a corrupção, mas
   deixou os chars MSU lentos.
3. Uma tentativa de DMA direto MSU -> VRAM causou lifebar piscando e P2
   com tiles distorcidos também em chars ROM.

## Causa

O SD2SNES não tolera o DMA `MSU -> WRAM` com a PPU renderizando. O caminho
de 03/11 fazia esse DMA na fase de lógica, com a tela ligada; o P2, segundo
lado preparado, lia setores velhos do cache.

O caminho seguro precisa de dois DMAs em forced blank (MSU -> WRAM e
WRAM -> VRAM). Fazer os dois lados no mesmo vblank, ou usar DMA direto
MSU -> VRAM, estoura o orçamento do vblank: a HUD não atualiza (lifebar
piscando) e o segundo lutador recebe tiles incompletos.

## Correção final

- `MsuStagePrepareFar` (lógica, tela ligada) faz somente o seek alinhado a
  512 bytes e a espera de `MSU_STAT`. Não toca em VRAM/WRAM.
- `MsuStageDmaFar` (vblank, forced blank) copia o setor posicionado para o
  buffer WRAM do lado.
- `SprDmaFar` copia o buffer para a página OBJ escondida no mesmo vblank.
- `SprPrepBoth` prepara os dois lados por quadro, mas permite apenas **um
  seek MSU por quadro**; o outro lado MSU fica pendente para o próximo.
- `DMACHUNK` subiu de 1280 para **1536** bytes: poses grandes terminam em
  menos blocos (buffer de 2 KiB comporta prefixo + 1536).
- A HUD pode enviar **uma faixa pequena** (vida/tempo) mesmo com upload de
  lutador pendente; só o repaint completo de 2 KiB é adiado. Isso evita a
  lifebar piscando quando os dois lados estão streamando.

## Trade-off

- Um MSU + um ROM: os dois atualizam a cada quadro.
- MSU + MSU: o barramento MSU posiciona um stream por vez; cada lado recebe
  um bloco a cada dois quadros, agora de 1536 bytes (melhor que 1280).
- A página visível continua sempre coerente; o pior caso é a pose anterior
  durar mais um quadro, nunca tiles misturados.

## Verificação

- 272 testes unitários OK.
- `tools/test_msu_chr_visibility_headless.py`: 960 páginas conferidas byte
  a byte contra o `.msu`, 57 poses distintas.
- Testes de campanha, join, Team Swap e attract demo OK.

Copie **`kof98-snes.sfc` e `kof98-snes.msu` juntos** para o SD2SNES.
