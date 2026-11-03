# Personagens com um quadro congelado na luta — 03/11/2026

## Sintoma

Durante a luta o personagem às vezes ficava **um quadro na pose anterior**
enquanto posição, relógio e comandos continuavam andando. O defeito aparecia
mais no stage do Japão (Esaka), que é o primeiro stage da campanha e tem a
plateia animada.

## Causa

O upload do CHR dos lutadores acontecia inteiro dentro do vblank
(`SprDmaP`): busca/espera do MSU, DMA MSU→WRAM e DMA WRAM→VRAM. Quando os
dois lados precisavam de tiles no mesmo quadro o código antigo **alternava**
os lados, então cada lutador só recebia um bloco a cada dois vblanks. O
`tools/build_fight.py` dimensiona o número de ticks de cada pose supondo
**um bloco de 1280 bytes por vblank por lutador**; com a alternância uma pose
de dois blocos levava quatro vblanks e era coalescida por `ASF_q_drop`.
Resultado: a pose anterior ficava na tela por um quadro extra.

Além disso, quando a espera pelo setor do MSU passava do orçamento, o caminho
antigo esperava o **próximo vblank dentro da apresentação**, duplicando um
quadro já apresentado. Isso também aparecia como um congelamento de um
quadro.

## Correção

O upload foi dividido em duas fases:

1. **`SprPrepBoth` / `SprPrepOne`** (fase de lógica, tela ligada): calcula a
   geometria do próximo bloco (tilebase, destino, tamanho), faz o seek e a
   espera limitada do MSU e traz `prefixo + payload` para um buffer de
   staging em WRAM. Não toca em VRAM nem em INIDISP. Se o MSU não responder
   dentro do limite, o bloco é tentado de novo no quadro seguinte — sem
   esperar vblank.
2. **`SprDmaFar`** (banco $3E, vblank): só copia o bloco já preparado de
   WRAM para a página escondida de OBJ (um DMA de até 1280 bytes por lado).
   Sem seek, sem staging e sem espera de vblank dentro da apresentação.

Como a fase de staging saiu do vblank, os dois lutadores podem enviar seu
bloco no mesmo quadro; a alternância foi removida. P1 usa `MsuStageBuf` e P2
usa `MsuStageBuf2` ($7F:5800), então os dois blocos ficam prontos ao mesmo
tempo.

Outros cuidados:

- `SP_KIND`/`SP_COUNT`/`SP_LEN`/`SP_DST` etc. ficam em $7E:5200–$5221
  (bloco reservado de streaming) e são zerados no boot e no `StartFight`,
  para nenhum bloco antigo sobreviver a uma troca de personagem ou a um
  reset a frio (WRAM pode conter lixo no console).
- `SprDmaFar` valida `SP_KIND` (1 = ROM, 2 = MSU staged, 3 = só commit) e
  recusa `SP_COUNT = 0`: no SNES um contador de DMA zero transfere 64 KiB e
  apagaria BG1/BG3.
- O commit (flip de `F_TILEPG`, `F_META`, offsets, caixas) continua sendo
  feito só quando o sprite inteiro chegou, como antes.

## Medições

Telemetria do próprio motor (`TEL_DROP_P1/P2`, `TEL_DMA_P1/P2`), VERSUS com
P1 mashando botões e P2 idle, 600 quadros, stage do Japão:

| build | poses descartadas P1/P2 | frames com upload pendente P1/P2 |
|---|---|---|
| anterior | 7 / 30 | 429 / 435 |
| nova | 3 / 5 | 301 / 346 |

No soak de 1500 quadros com entradas aleatórias (mesma semente):

| build | poses descartadas P1/P2 |
|---|---|
| anterior | 109 / 59 |
| nova | 40 / 4 |

Os poucos descartes restantes coincidem com trocas de estado (início do
caminhar e golpes), quando uma pose nova chega com o bloco anterior ainda em
trânsito; não são mais o gotejamento constante de antes.

## Verificação

- `tools/test_msu_chr_visibility_headless.py`: 960 páginas visíveis conferidas
  byte a byte contra o `.msu`, 56 poses distintas — PASS.
- `tools/test_super_stage_vram_headless.py`: super do Kyo no stage do Japão
  mantém BG1 CHR/mapa — PASS.
- `tools/test_team_swap_headless.py` (6 casos), `test_team_banner_headless`
  (4 casos), `test_round_banner_headless`, `test_single_campaign_headless`,
  `test_midfight_join_headless`, `test_ranbu_headless`,
  `test_projectile_recovery_headless`, `test_msu_voice_alignment_headless` —
  PASS.
- `test_geese_raging_storm_headless` usa QCF×2 com **1 quadro por direção**;
  com a taxa de quadros do headless ele fica no limite e passa segurando as
  direções por 3 quadros (estado 86 confirmado). Não é regressão de jogo.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$6A23`**
- layout MSU **`0xC276`**
- `.sfc` SHA-256 `d8e95a71…e2efe03`
- `.msu` SHA-256 `471f5983…ce53dcb6` (inalterado)
