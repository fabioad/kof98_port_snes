# Team Play: Daimon com tiles misturados / golpes que não acertam e barra de HP — 03/11/2026

## 1. Daimon com tiles misturados e hurtbox errada na troca de membro

### Sintoma

No Team Play, quando o Daimon entra como próximo membro, a tela podia
mostrar tiles misturados no corpo dele e os golpes do oponente deixavam de
acertá-lo.

### Causa

O upload de CHR dos lutadores é feito em duas fases: `SprPrepBoth` prepara o
próximo bloco em `MsuStageBuf`/`MsuStageBuf2` e o vblank copia para a página
escondida. Quando **os dois lados** têm `F_DMAREQ` no mesmo quadro, o vblank
atende só um lado (alternância por `framecnt`); o bloco do outro fica
guardado em `SP_KIND`.

`TeamMemberIn` (a troca de membro) zerava `F_DMAREQ`, `F_DMAPOS` e
`F_TILEPG`, mas **não** o estado de staging (`SP_KIND`/`SP_COUNT`/`SP_LEN`/
`SP_META`). Em seguida `EnterState(S_INTRO)` já marca `F_DMAREQ` para o
sprite do novo membro. No quadro seguinte, `SprPrepOne` vê `SP_KIND != 0` e
retorna ("já tem bloco preparado"), então o vblank envia o **bloco do membro
anterior** para a página do Daimon e comita o `SP_META` antigo.

Consequências:

- as tiles do Daimon ficam com o CHR do membro anterior (tiles misturados);
- `F_META`/`F_HURTBOX` são comitados com a caixa do membro anterior, então a
  hurtbox fica errada/deslocada e os golpes não conectam.

O CHR do Daimon é grande (slice MSU 182, corrida de 19 slices), então o
streaming dele fica vários vblanks pendente — é o caso em que a corrida
aparece com mais facilidade.

### Correção

`TeamMemberIn` agora limpa, para o lado que troca, todo o estado de staging
antes de `EnterState`: `SP_KIND`, `SP_COUNT`, `SP_LEN`, `SP_SRC`,
`SP_SRCBANK`, `SP_DST`, `SP_PREFIX` e `SP_META`. O próximo vblank não
encontra bloco válido; o Daimon começa o streaming do zero e comita o próprio
meta/caixas.

## 2. Barra de HP do player não enchia ao enfrentar o trio seguinte

### Sintoma

Ao derrotar o trio adversário, no confronto seguinte a barra de vida do
player começava parcial (por exemplo, em 104/200) em vez de cheia.

### Causa

O KO do último membro do trio grava `T_SWAP` para a troca de membro. Se o
trio inteiro cai, `TeamRoundEnd` vai para `ShowTitle` sem limpar `T_SWAP`.
Depois, `CampResolve`/`CampNext` chamam `StartFight` para o novo confronto;
como `T_SWAP != 0`, o `StartFight` entra no caminho **parcial** `TeamSwap`
em vez do reset completo. O lado sobrevivente (o trio do player) mantinha
HP e posição do combate anterior — daí a barra não encher.

### Correção

`CampNext` e `CampResolve` agora zeram `T_SWAP` antes de montar o próximo
confronto. O `StartFight` seguinte faz o reset completo: HP = 200 para os
dois lados, spawn em 80/176 e stage/PPU recarregados. O medidor (power)
continua sendo carregado por `FUS_CARRY`, como antes.

## Verificação

- Novo `test_team_confrontation_reset_headless`: vence os três membros do
  CPU, confere `C_IDX=1`, `T_SWAP=0`, HP do player = 200, spawn em 80 e
  medidor preservado (3000).
- Novo `tools/tests/test_team_staging.py`: garante que `TeamMemberIn` limpa
  `SP_KIND`/`SP_COUNT`/`SP_LEN`/`SP_META` e que `CampNext`/`CampResolve`
  limpam `T_SWAP`.
- Entrada do Daimon como segundo membro: `F_GRAB`/hurtbox corretos
  (`F_META 0x896`, `F_HURTBOX 0x7e43`), golpes do oponente acertam
  (200 → 166).
- Soak CPU vs CPU de 5000 quadros com Daimon no time: sem travamento.
- `test_team_swap_headless` (6), `test_team_vs_start_headless`,
  `test_team_banner_headless` (4), `test_team_swap_palette_headless`,
  `test_single_campaign_headless`, `test_midfight_join_headless`,
  `test_ai_headless`, `test_attract_demo_headless`, `test_ralf_mount_headless`,
  `test_counter_banner_headless`, `test_yamazaki_reversal_headless`,
  `test_benimaru_antiair_headless`, `test_msu_chr_visibility_headless` e
  `test_super_stage_vram_headless`: PASS.
- `pytest -q tools/tests`: 271 passed.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$B269`**
- layout MSU **`0x9EF1`**
- `.sfc` SHA-256 `3d0a06e4…b81b9`
- `.msu` SHA-256 `ae7d0481…5dd83` (novo; copie os dois juntos)
