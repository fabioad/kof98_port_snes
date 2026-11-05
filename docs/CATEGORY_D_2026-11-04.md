# Categoria D: primeiro bloco (04/11/2026)

## Escopo

A varredura de comandos mostrou que **todos os `[State -1]` de ataque já
chegam a um state** (com `POST_CAL_SUPERS`/`POST_CAL_REACTIVATED`). O que
restava na Categoria D eram golpes ligados mas incompletos: follow-ups de
agarre não religados, supers cujo ataque vive em Helper e projéteis que
nasciam mas não acertavam. Este primeiro bloco cobre o grupo da prioridade
— Kyo, Nests, Ash, Terry e Athena.

## Kyo / Nests / Ash

### 3500/3550 (Chou Hissatsu Waza / MAX Mushiki)

Os dois roots são agarrões (`attr S,HT`) com `p1stateno` 3501/3551. Os
follow-ups não estavam ligados, então o golpe prendia a vítima e soltava
no tick seguinte (0–1 de dano). Foram religados:

| State | Sid | Função |
|---|---|---|
| 3501 | 65 | Chou Hissatsu Waza (bind + TargetLifeAdd) |
| 3551 | 103 | MAX Mushiki (bind + TargetLifeAdd) |

As poses de vítima 3502/3503 foram mapeadas para os slots 76/77. O 3550
ainda gerava um **projétil invisível** pelo heurístico de HitDef/ChangeState;
ele foi removido com `PROJECTILE_EXCLUDE` (Kyo, Nests e Ash) para o grab
rodar de verdade.

Resultado: **41 de dano** em 3500 e 3550 (as três variantes).

### 3305 (108-Shiki '99)

O extrator lia o HitDef como 2 pontos. `slice_damage[88] = 18` dá ao golpe
um tamanho de especial normal.

## Terry

### 3000/3010 (Power Geyser)

O pilar estacionário é um Helper/projétil. O spark nascia no pool, mas o
loop de projéteis tratava o bit3 (marcador de **clipe alternativo**) como
“hitbox de bola quicando já gasta” e pulava o `ProjHit`. A máscara foi
corrigida para os bits 1–2 (estado real da bola), e o geyser passou a
acertar com o clipe alternativo 3020.

O HitDef de corpo que existia como workaround foi removido; o projétil é
quem dá o dano. O super projétil do engine faz cinco contatos, então o dano
por contato foi ajustado para 5/6 (total **25/30**).

### 3050 (Buster Wolf)

O rush é Helper (três spawns 3060) e o root não tinha HitDef/Clsn1. Foi
adicionado um HitDef de corpo no rush com caixa nos frames 6–21 e
`hit_soft_resets` nos elementos 12/18/24. O resultado atual é **20**
(aproximação de um contato; o knockdown do primeiro hit ainda corta os
contatos seguintes).

## Athena — Phoenix Fang 3000/3050/3100

Os três comandos SUP entravam nos states, mas as bolas do Phoenix Fang
(Helper 3050/3060) não existiam no motor. Implementação:

- **Clipe alternativo 7700** (a bola visível) compilado como segundo ProjFx
  da Athena; o 7701 da origem é só a hitbox invisível (Clsn1 em sprite -1).
- As três linhas de `ProjTab` (85/86/87) usam o clipe alternativo, projétil
  **estacionário** (vx=0), com dano por contato 12/14/20.
- O super projétil acerta em sequência; o total medido é **48 / 42 / 40**.
- O **4000** (super que já estava ligado) foi confirmado: **62**.

A correção do bit3 também foi o que destravou esses projéteis.

## Verificação

Novo `tools/test_category_d_headless.py` — **12 golpes PASS**:

- Kyo 3500/3550: 41; Kyo 3305: 18;
- Nests 3500: 41; Ash 3550: 41;
- Terry 3000: 25; 3010: 30; 3050: 20;
- Athena 4000: 62; 3000: 48; 3050: 42; 3100: 40.

Regressões: `pytest -q tools/tests` **272 passed**, além de
`test_category_a_headless`, `test_clark_chains_headless`,
`test_chizuru_clones_headless`, `test_chizuru_dp_headless`,
`test_ai_headless`, `test_msu_chr_visibility_headless` (960 páginas/56
poses) e `test_super_stage_vram_headless`.

> Alguns testes antigos de input com `L` sem direção (`test_andy_hishouken`,
> caso Andy do `test_kyokugen_projectile_anim`) continuam falhando também
> no par anterior; são anteriores a esta mudança.

## Ainda na Categoria D

- Terry: Power Wave EX 1050, Power Charge MOW 1550/1560, Fire Kick 1600,
  Double Kong 1700, High Angle Geyser 3100, Power Dunk MOW 1450.
- Andy, Ryo, Robert e os demais personagens da tabela de 24/10.
- Rugal/Omega Rugal, Takuma, Iori e os MAX/SDM restantes.
- O Buster Wolf pode ganhar os três contatos com slices/`slice_no_fall`.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$9C60`**
- layout MSU **`0x1135`**
- `.sfc` SHA-256 `187bc733…cf776`
- `.msu` SHA-256 `6d9ca6ba…f9528`

Copie `.sfc` e `.msu` juntos.
