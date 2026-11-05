# Chizuru: especiais/supers de clone (04/11/2026)

## O que foi feito

Os comandos 1000/1004 (QCF), 1100/1102 (QCB), 1300/1400 (HCB), 1500 (RDP)
e os supers 2000/2100/2200 já chegavam aos states nativos, mas o **corpo
do clone** (Helper) não é desenhado no SNES. O port mantém a Chizuru como
atacante e usa os HitDefs/dano da origem. Esta rodada corrigiu o que ainda
impedia os golpes de serem jogados de forma confiável:

### HCB (1300/1400)

O `apply_half_circle_shortcuts` reduz tanto o HCB (`F, D, B`) quanto o QCB
(`D, DB, B`) a quatro elementos. Como o QCB vem antes no CMD, ele consumia
o final do HCB e o golpe forte/fraco de meia-lua para trás nunca saía.
`cmd_priority = ("HCB_X", "HCB_Y")` coloca as regras de HCB antes; elas só
casam quando o F inicial está presente, então o QCB continua funcionando.

### Super 2000: tempo morto e multi-hit

- O clipe 2000 da origem segura a pose de invocação por **130 ticks** antes
  do rush. O motor não roda `SuperPause`, então isso era tempo morto. O
  novo clipe **13001** (no `chizuru_maki.air`) é uma cópia do 2000 com esse
  hold reduzido para 6 ticks.
- O estado 2000 tem HitDefs em vários elementos; o motor nativo usa uma
  linha só e trava depois do primeiro contato. `hit_soft_resets[2000] =
  [12, 18, 30]` rearma o golpe nos elementos seguintes. O resultado é
  **2 contatos (36 de dano)**; o terceiro reset não chega a conectar porque
  a vítima já está em knockdown.

### Super 2200

A origem tem dois HitDefs (elementos 22/23), mas o primeiro já derruba a
vítima no port e o segundo não conecta. O dano final foi fixado em **48**
via `slice_damage` (aplicado depois da normalização de dano da Chizuru,
que é x0,12). Sem isso o golpe ficava em 24 e o override em unidade de
origem seria reduzido a 6.

## Dano medido (HP 200)

| Golpe | State | Dano |
|---|---|---|
| QCF fraco/forte | 1000/1004 | 28 |
| QCB fraco/forte | 1100/1102 | 18 |
| HCB fraco/forte | 1300/1400 | 18 |
| RDP | 1500 | 18 |
| Super 2000 | 2000 | 36 (2 contatos) |
| Super 2100 | 2100 | 48 |
| Super 2200 | 2200 | 48 |

## Limite conhecido

O **sprite do clone** continua ausente: o motor não roda Helpers e o pool
de projéteis é usado pelos leques. A Chizuru executa a pose/ataque do
clone com o próprio corpo — a mesma aproximação adotada no DP. Os golpes
acertam, dão dano e recuperam; o que falta é o clone visual duplicado.

## Verificação

Novo `tools/test_chizuru_clones_headless.py` — **10 golpes PASS**, com os
danos acima e os states esperados. O teste cobre justamente o HCB, que era
o caso que não saía.

Regressões: `pytest -q tools/tests` **272 passed**, `test_chizuru_dp_headless`,
`test_category_a_headless`, `test_clark_chains_headless`,
`test_ai_headless`, `test_msu_chr_visibility_headless` (960 páginas/56
poses), `test_super_stage_vram_headless`, `test_attract_demo_headless`,
`test_team_swap` e `test_team_banner`.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$9C60`**
- layout MSU **`0x1135`**
- `.sfc` SHA-256 `187bc733…cf776`
- `.msu` SHA-256 `6d9ca6ba…f9528` (inalterado; o clipe 13001 reusa os
  sprites do 2000)

Copie `.sfc` e `.msu` juntos.
