# Chizuru: DP/antiáreo nativo (04/11/2026)

## Sintoma

O DP da Chizuru (`F, D, DF + botão`) não subia: o corpo ficava no chão,
executava a animação de invocação/descida e demorava a recuperar.

## Causa

O state 1200 do CNS é apenas o **root de invocação do clone**. Quem sobe e
ataca é o **Helper 1100** (anim 1100/1110), com `VelSet y = -9.5` no
elemento 8, `StateTypeSet` para aéreo, HitDefs no 7/8/28/34 e a descida.
O motor SNES não roda Helpers, então o corpo principal ficava no chão e
tocava a animação 1200 (29 frames, 106 ticks). Daí a impressão de
“animação de descida no chão” e recuperação longa.

## Correção

Sem mexer no mapeamento do comando (`moves[52] = 1200`, necessário para o
`CmdTab` emitir o DP):

1. **Animação nativa curta** — `anims[52] = 13000`. O clipe 13000 foi
   criado no `chizuru_maki.air` reaproveitando os sprites/boxes do anim
   1101 do clone, mas com as esperas longas encurtadas (a de 45 ticks virou
   4). O ataque continua nos elementos 6–8.
2. **Velocidade de subida** — `act_override[1200]` com
   `(7, 5, 3)` (vx = 3) e `(7, 15, -38)` (vy = -9.5 px/tick, codificado em
   quartos de pixel). A gravidade do motor faz a descida.
3. **HitDef do Helper** — `hitdef_override[52]` com `active = 7`,
   `gvx = 5 px`, `gvy = -10 px` e `fall = 1`. O dano vem do HitDef de
   origem (75 na escala MUGEN), normalizado para **18**.
4. **Transições** — `trans_drop[(52, 0)]` descarta os `ChangeState`
   complexos do root (combo/teleporte) que disparavam antes do fim do
   clipe; o motor volta ao estado 0 no fim da animação.

## Verificação

- Novo `tools/test_chizuru_dp_headless.py`: o DP sobe ~**98 px**, acerta
  o Kyo (HP 200 → 182), derruba (estado 10) e volta ao estado 0 em ~75
  frames. **PASS**.
- `test_ai_headless`: PASS (a regra do DP voltou ao `CmdTab`, então a IA
  também pode usá-la).
- `test_msu_chr_visibility_headless`: 960 páginas / 57 poses — PASS.
- `test_super_stage_vram_headless`, `test_attract_demo_headless`,
  `test_team_*`, `test_ralf_mount_headless`,
  `test_counter_banner_headless`, `test_yamazaki_reversal_headless` e
  `test_benimaru_antiair_headless`: PASS.
- `pytest -q tools/tests`: 272 passed.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$B269`**
- layout MSU **`0x9EF1`**
- `.sfc` SHA-256 `3d0a06e4…b81b9`
- `.msu` SHA-256 `ae7d0481…5dd83`

> O clipe 13000 adicionou tiles ao blob CHR do Chizuru, então o **layout e
> o `.msu` mudaram**. Copie `.sfc` e `.msu` deste build juntos.

## Pendente

Os outros golpes de clone da Chizuru foram religados em 04/11 (ver
`docs/CHIZURU_CLONES_2026-11-04.md`): QCF/QCB/HCB/RDP e os supers
2000/2100/2200 chegam aos states e acertam. O sprite do clone continua
ausente (a Chizuru executa a pose/ataque com o próprio corpo), restando
apenas o clone visual e os efeitos de PalFX/AfterImage.
