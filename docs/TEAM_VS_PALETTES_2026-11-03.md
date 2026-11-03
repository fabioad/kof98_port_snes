# Team Play / Team Versus — correções (03/11/2026)

## Team Versus não iniciava a luta

Depois que P1 e P2 escolhiam os três membros, a tela ficava preta com a
música do select tocando. O `TVS_done` montava os trios e chamava
`StartFight`, mas **nunca chamava `CampStart`**. `CampReset` deixa
`C_STAGE` intacto, e `CampStage` (modos 2/3/4) copia `C_STAGE` para
`STAGEF`. No boot a WRAM do console pode conter qualquer valor (o emulador
preenche com `$55`); com `C_STAGE = $55` o `StagePick` calculava
`StageTab + 0x55*12`, lia lixo e travava com `INIDISP=$8F` e NMI
desligado — exatamente a tela preta com a música do select ainda no SPC.

**Correção:** `TVS_done` chama `CampStart` antes do contador de 8 quadros.
Ele escolhe um stage válido (`CampPickStage`), zera a campanha e deixa
`T_I1/T_I2/T_N2/T_STEP` no estado de início de luta. O Team Play já fazia
isso no fim do pick; o Team VS era o único caminho sem essa inicialização.

## Team Play: paletas do P2 e do stage na segunda luta

O `TeamSwap` chama `TeamPpuSetup` (`PpuInit`, `LoadStaticGfx`, `CampStage`,
`StagePick`) e depois `TeamMemberIn`. O `StagePick` termina com a tela
ligada (`INIDISP=$0F`), e o `TeamMemberIn` chama `LoadCharPals`, que
escreve na CGRAM. **Escrita de CGRAM com a tela renderizando não é
confiável no SNES**: a paleta do novo P2 chega incompleta (perde cores) e
o acesso pode bagunçar o endereço da CGRAM usado pelos uploads seguintes.
No primeiro combate isso não acontecia porque o `StartFight` carrega as
paletas dos personagens antes do `StagePick`, com a tela ainda em forced
blank.

**Correção:** depois do `TeamPpuSetup` o `TeamSwap` volta a forçar blank
(`INIDISP=$8F`) e mantém a tela blank durante o `TeamMemberIn`
(`LoadCharPals`). O `TS_hud` já blanka de novo para `LoadPortraits` e só
religa a tela no fim, então a luta entra normalmente.

## Verificação

- Novo `tools/test_team_vs_start_headless.py`: modo 3, P1 e P2 escolhem
  três membros, a luta 1 inicia com stage válido e HP 200; KO do P2 leva à
  luta 2 com o mesmo stage e sem travar — PASS nos dois estágios.
- `tools/test_team_swap_headless.py` (6 casos), `test_team_banner_headless`
  (4 casos, modos 2 e 3), `test_round_banner_headless`,
  `test_single_campaign_headless`, `test_midfight_join_headless` — PASS.
- `test_team_swap_palette_headless.py` (boot atualizado para pular o vídeo
  MSU): `stageidx` e `sel` do lado CPU sobrevivem às trocas — PASS.
- `test_msu_chr_visibility_headless` (960 páginas) e
  `test_super_stage_vram_headless` — PASS.
- Testes estruturais novos: `TVS_done` chama `CampStart`; o `TeamSwap`
  força blank antes de `LoadCharPals`; `TeamMemberIn` carrega as paletas.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$675B`**
- layout MSU **`0xC276`**
- `.sfc` SHA-256 `1fb78f52…e96e9f6b`
- `.msu` SHA-256 `471f5983…ce53dcb6` (inalterado)
