# Clark: cadeias de agarrão e Flashing Elbow (04/11/2026)

## O que estava faltando

A dieta de ROM remove os sids 58–66 e 87–89 de Clark. Isso deixava os
comandos do **Ultra Argentine MAX (3050)** e do **Running Three
(3100/3110/3150)** sem state, e o **Flashing Elbow (1600)** sem nenhuma
cadeia. Além disso:

- o comando `HCFHCF_B` (Running Three forte) aponta para **3110**, que é a
  animação do arremesso, não uma tentativa de agarrão;
- o dano do Running Three está em **3111** (TargetLifeAdd -41), que não
  estava ligado;
- o MAX Running Three usa `SUPER_X` (HCB×2 + x), o **mesmo input** do Ultra
  Argentine fraco, então uma regra consumia a outra.

## Correções

### Ultra Argentine MAX (3050)

Religado no sid 87. O `p1stateno` original (3060) foi redirecionado para
**3010**, reutilizando a cadeia 3010→3011→…→3016 já portada. Resultado:
105 de dano, o mesmo caminho visual do Ultra Argentine normal, sem
adicionar os oito states 3060–3067.

### Running Three (3100/3110/3150)

Os states do arremesso foram religados na faixa **60–69** (knee family), que
é aceita pelo `HitOne`:

| State | Sid | Função |
|---|---|---|
| 3105 | 62 | tentativa de agarrão (fraca/forte) |
| 3155 | 64 | tentativa de agarrão (MAX) |
| 3110 | 66 | animação do arremesso |
| 3111 | 60 | finalizador (TargetLifeAdd -41) |

- O comando forte (`HCFHCF_B`) foi remapeado para **3105**.
- O MAX Running Three (3150) foi para o sid **86**, dentro da janela
  85–89 do MAX mask. O comando `SUPER_X` foi desativado e substituído por
  **HCF×2 + C** (duplo HCF + chute), que não colide com o Ultra Argentine.
- O `StVictimHeld` agora mantém a vítima presa também nos states 60–69,
  e o `HitOne` já aceitava essa faixa.
- O 3110 termina em `Vel Y > 0 && Pos Y >= 0`; como o parser de pouso não
  representa essa condição, a passagem para 3111 foi adicionada no fim da
  animação.

Dano medido: **83** para as três variantes (a MAX reutiliza o mesmo
arremesso 3110/3111).

### Flashing Elbow (1600)

Os states 1600/1605/1606 foram ligados nos sids **112–114**, e a faixa
`S_EXT_LAST` subiu de 111 para 114 (o `StateTab` ganhou três entradas
`StSpecial`). O golpe:

- continua sendo um follow-up opcional de 1420 (Frankensteiner) e 1510
  (Napalm Stretch);
- ganhou também um comando direto **QCF + C**, porque depois de um throw a
  vítima costuma estar caída e o HitDef do 1605 (`p2statetype != L`) não
  acerta um adversário no chão.

Dano medido pelo comando: **12**.

## Inputs novos do Clark

| Golpe | Input |
|---|---|
| Running Three MAX | HCF×2 + C |
| Flashing Elbow | QCF + C |

Os demais continuam iguais: HCB×2 + X/Y (Ultra Argentine), HCF×2 + A/B
(Running Three fraco/forte), HCB×2 + X+Y (Ultra Argentine MAX).

## Verificação

Novo `tools/test_clark_chains_headless.py`:

- Ultra Argentine fraco: 105;
- Ultra Argentine MAX: 105;
- Running Three fraco: 83;
- Running Three forte: 83;
- Running Three MAX: 83;
- Flashing Elbow: 12.

Todos PASS. Regressões: `pytest -q tools/tests` **272 passed**, mais
`test_category_a_headless`, `test_ai_headless`,
`test_msu_chr_visibility_headless` (960 páginas/56 poses),
`test_super_stage_vram_headless`, `test_chizuru_dp_headless`,
`test_attract_demo_headless`, `test_team_*`, `test_single_campaign`,
`test_midfight_join`, `test_counter_grab`, `test_mary_grab`,
`test_chin_zake`, `test_yamazaki_reversal`, `test_chunli_hyakuretsu`,
`test_takuma_shouran` e `test_antiair_landing`.

> O Frankensteiner (1400/1410 → 1420) continua com apenas 1 de dano; é uma
> pendência separada, anterior a esta mudança, e não foi alterado.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$0CA0`**
- layout MSU **`0x9EF1`**
- `.sfc` SHA-256 `ef1612aa…3a89`
- `.msu` SHA-256 `ae7d0481…5dd83`

O `.msu` cresceu com as animações do Flashing Elbow (1600/1605/1606).
Copie `.sfc` e `.msu` juntos.
