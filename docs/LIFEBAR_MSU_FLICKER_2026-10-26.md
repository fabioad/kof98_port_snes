# Barra de vida piscando com personagens MSU (26–27/10/2026)

## Sintoma

No SNES real com SD2SNES MKII, a **barra de vida verde do topo** (BG3,
linha 2 do HUD) pisca escura quando algum dos lutadores usa CHR streamado
do `.msu` — inclusive com os dois lutadores parados. No Snes9x o problema
não aparece, porque o emulador não reproduz a latência do cartão.

## Causa

`FightPresent` (caminho PVSnesLib) liga o *forced blank* (`INIDISP=$8F`)
no início da apresentação e só volta para `$0F` no fim. O upload de CHR de
um personagem MSU faz, antes dos DMAs, o seek do setor alinhado e espera o
`MSU_STAT`. No SD2SNES essa espera depende do cartão (e da música MSU
concorrendo pelo SD) e pode passar de vários milissegundos. Como a tela
ficava apagada até o fim, as primeiras linhas visíveis — onde está a barra
de vida — apareciam escuras naquele frame.

A barra de power do rodapé não era a afetada: ela fica na linha 25 e só
escureceria se o estouro passasse de ~200 linhas.

## O que não pode ser feito

Os dois DMAs do CHR precisam de forced blank no SD2SNES:

- **DMA MSU→WRAM** (destino `$2181`, WMDATA): com a tela ligada os tiles
  do personagem saem misturados.
- **DMA WRAM→VRAM** (destino `$2118/$2119`): com a tela ligada os tiles
  ficam inválidos/invisíveis.

Também não se deve reduzir demais o `MSU_POLL_LIMIT`: isso aborta o seek
no meio da leitura e força re-seeks frequentes, mexendo no cache do MSU.

## Correção final

Só a **espera por CPU** sai da janela apagada; os dois DMAs continuam
exatamente no caminho validado de 24/10.

1. **`SD_msu` (`src/engine/fight.asm`)**: a tela é ligada (`$0F`) antes
   do seek. O seek e o poll do `MSU_STAT` rodam com a imagem ligada — são
   acessos de CPU ao cartucho, não tocam VRAM/WRAM.
2. Depois do poll, se ele demorou mais de ~224 iterações (~0,78 ms) ou se
   o vblank já acabou, o chunk **não é descartado**: o setor já buscado é
   mantido e a rotina espera o próximo vblank começar, com a tela ligada
   (só lê `$4212`). Assim os DMAs sempre começam no topo de uma janela
   nova, sem re-seek e sem escrever durante o display ativo.
3. Com o vblank disponível, `MsuStageUploadFar`
   (`src/snes/fight_bridge.asm`) liga `$8F`, faz o estágio MSU→WRAM e o
   DMA WRAM→VRAM, e volta para `$0F`. É o caminho validado, byte a byte.
4. **`FightPresent`**: depois do bloco de CHR, só religa o forced blank
   para HUD/cenário se `$4212` ainda indicar vblank. Se o vblank acabou,
   mantém a tela ligada e adia as bandas sujas para o próximo frame.

Não há laço de espera novo: no pior caso um chunk ou uma banda de HUD
atrasa um frame.

## Validação

- `tools/test_msu_chr_visibility_headless.py`: **960 páginas visíveis**
  comparadas byte a byte com o `.msu` (Rugal × Leona e Chizuru × Ken, com
  ataques dos dois lados), 58 poses distintas: todas exatas.
- `test_ai_headless.py`, `test_msu_voice_alignment_headless.py` (21 vozes
  do Clark), `test_hud_bands_headless.py`, `test_start_transition.py` e
  `test_intros_headless.py`: PASS.
- `python3 -m unittest discover -s tools/tests`: 174 testes OK.
- Build PVSnesLib + `make verify`: OK.

## Hashes

- ROM `kof98-snes.sfc`: checksum **`$DA94`**, SHA-256
  `a1928fdd…240f2f88`.
- MSU `kof98-snes.msu`: SHA-256 `3e8945c3…868de386` (inalterado).

Rollback: tag `backup-pre-powerbar-fix-20261026` e
`backup/powerbar_pre_20261026/`.
