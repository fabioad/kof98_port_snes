# Retratos da luta e do order select com 15 cores — CONCLUÍDO

Data: 2026-11-20. Pedido: "os retratos da barra de vida da luta tenham 15
cores, assim como os retratos da tela de select" e, em seguida, "15 cores
também nos retratos do order select".

## Problema

Os retratos do HUD e do ORDER SELECT eram 2bpp com 3 cores (índice 0
transparente), enquanto as células do SELECT já usam paletas de 15 cores.
No modo 1 do SNES o BG3 (HUD) é 2bpp, então não havia como dar 15 cores aos
retratos mantendo-os naquela camada.

## Solução

Os retratos viraram **4bpp com paleta de 16 cores** (15 cores + índice 0
transparente) e saíram do BG3 para um **overlay no BG2**, que durante a luta
está livre (TM = BG1+BG2+BG3+OBJ = `$17`).

### Luta (barra de vida)

- `tools/build_fight.py::build_portraits` gera 288 B por personagem
  (3x3 tiles 4bpp) + 32 B de paleta; a paleta das 15 cores é extraída apenas
  dos pixels opacos do ícone (`_face_palette`).
- P1 usa a paleta 5 do BG2 (CGRAM 80..95) e os tiles 1..9; P2 usa a paleta 6
  (CGRAM 96..111) e os tiles 11..19. O espelhamento do P2 é feito pelo bit
  H-FLIP do mapa (`$4000`), então não há mais cópia espelhada na ROM.
- `HudPortraitMap` (mapa 32x32 do BG2) é gerado no build e carregado em
  `PpuInit` junto com o tile 0 vazio (`HudBlankTile`).
- `PortraitMap` agora só limpa as 18 células 3x3 do BG3: o BG3 é prioritário
  no modo 1 e qualquer tile ali cobriria a face.
- VRAM da luta: `BG2CHR=$4000` (20 tiles), `BG2MAP=$4400`, `BG1MAP` passou de
  `$4000` para `$4800` (mapa 64x32 do cenário, `$4800-$4FFF`); `BG3MAP=$5000`
  e `STGACHR=$2C00` não mudaram.
- `TM = $17` nos quatro pontos de luta (StartFight, ShowTitle, intro do
  round e `CineApply`).

### Order select

- 57 retratos 32x32 4bpp (512 B cada) em janelas de 16 tiles
  (`tile 1+slot*16`), uma paleta de 16 cores por card em CGRAM
  **0/48/64/80/96/112** (`OrderPalBase`, tabela de **bytes** — `lda.l` indexa
  por byte).
- `OrderBg2Map` é estático (seis janelas 4x4; o resto aponta para o tile 0
  vazio, carregado por `OrderBg2Blank`). Cards fora do time (`OR_CARD >=
  OR_SIZE`) recebem 512 bytes zerados (`OrderBg2Zero`) para a janela ficar
  transparente.
- VRAM do order: `BG2CHR=$4000` (97 tiles → `$4000-$460F`), `BG2MAP` do order
  em **`$4C00`** (`ORDER_BG2MAP`, logo depois do mapa do BG1 em `$4800`),
  `BG3MAP=$5000` para o texto. `TM = $07`.
- `OrderDrawPortrait` foi removido: o mapa do BG2 é fixo e só os tiles +
  paletas são recarregados em `OrderLoadPortraits`.
- Os 57 retratos 32x32 (29.184 B) não cabiam mais na cauda de 18 KiB do banco
  64: foram para `.BANK 87 .ORGA $8000` (`OrderPortraitChr`). Os mapas e a
  tabela de paletas do order continuam no banco 64 (`$B700`).

## Verificação

- Build: `make pvsnes` OK (ROM 8 MB, 2.4 MB livres; `OrderPortraits` em
  `$01178000`, `HudPortraitMap` em `$0100BE20`).
- `tools/test_portrait_swap_headless.py`: PASS (P1/P2 trocam de retrato nas
  trocas de membro; dados do BG2 conferidos na VRAM).
- `python3 -m unittest tools/tests/test_portraits.py`: OK.
- Capturas headless (Snes9x libretro, 256x224):
  - luta (versus e team): HUD com os dois retratos em 15 cores, P2 espelhado;
  - ORDER SELECT: seis cards em 15 cores (KYO/BENIMARU/DAIMON x
    KENSOU/ATHENA/YURI), seleção e START seguem para a luta normalmente.

## Armadilhas encontradas

- `lda.l Tabela,x` indexa **bytes**: a tabela `OrderPalBase` precisou ser
  `.db` (com `.dw` os cards 3..5 caíam em CGRAM 0 e as faces apareciam com a
  paleta errada).
- O mapa do BG2 do order não pode ficar em `$4400`: as 97 tiles de face vão
  até `$460F` e o mapa (carregado depois) sobrescrevia os cards 3..5.
