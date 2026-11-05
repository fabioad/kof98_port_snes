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

`tools/test_category_d_headless.py` — **12 golpes PASS** (primeiro bloco):

- Kyo 3500/3550: 41; Kyo 3305: 18;
- Nests 3500: 41; Ash 3550: 41;
- Terry 3000: 25; 3010: 30; 3050: 50;
- Athena 4000: 62; 3000: 48; 3050: 42; 3100: 40.

`tools/test_category_d_remaining_headless.py` — **39 golpes PASS**
(segundo bloco, 05/11):

- Terry: 1050 14, 1450 12, 1550 30, 1560 34, 1600 16, 1700 20,
  3100 32, 3200 34 (3 contatos), 3250 48 (3 contatos), 3050 50;
- Andy: 1400 12, 1450 8, 1500 14, 1160 14, 3000 37, 3010 52, 3050 57,
  Dan Da Dan 3200/3210/3250 33/33/44 (2 contatos, aproximação);
- Ryo: 1150 26, 1160 32, 1250 14, 1260 28, 2100 13, 3250 30,
  1050 14, 1400 12 (3 contatos), 2000/2010 14/14 (aéreo);
- Robert: 1050 14, 3200 24, 3210 37, 3220 47, 3270 44;
- Rugal: 1800 14;
- Iori: 3100 6, 3110 8, 3150 12.

Regressões: `pytest -q tools/tests` **272 passed**, além de
`test_category_a_headless`, `test_clark_chains_headless`,
`test_chizuru_clones_headless`, `test_chizuru_dp_headless`,
`test_ai_headless`, `test_msu_chr_visibility_headless` (960 páginas/56
poses) e `test_super_stage_vram_headless`.

> Alguns testes antigos de input com `L` sem direção (`test_andy_hishouken`,
> caso Andy do `test_kyokugen_projectile_anim`) continuam falhando também
> no par anterior; são anteriores a estas mudanças.

## Segundo bloco (05/11/2026)

### Infraestrutura

- `POST_CAL_TWEAKS` / `POST_CAL_PROJS`: hooks aplicados **depois** de
  `apply_profile`, para adicionar golpes/comandos/projéteis sem invalidar
  os perfis de calibração existentes.
- As linhas de `hit_resets`/`hit_soft_resets` passaram para depois de
  `apply_profile`, permitindo que os novos golpes também declarem
  rearmes de HitDef.
- O Buster Wolf usa `hit_soft_resets` no rush (dois contatos) e o
  finalizador 3205/3255 como terceiro contato; `slice_no_fall` mantém a
  vítima em hitstun entre os contatos.

### Terry

| Golpe | State | Sid | Dano |
|---|---|---|---|
| Power Wave EX | 1050 | 60 | 14 |
| Power Dunk MOW | 1450 | 61 | 12 |
| Power Charge MOW fraco | 1550 | 64 | 30 |
| Power Charge MOW forte | 1560 | 65 | 34 |
| Fire Kick | 1600 | 62 | 16 |
| Double Kong | 1700 | 63 | 20 |
| High Angle Geyser | 3100/3101 | 105/106 | 32 |
| Buster Wolf | 3200 → 3205 | 88/103 | 34 (3 contatos) |
| MAX Buster Wolf | 3250 → 3255 | 89/104 | 48 (3 contatos) |
| MAX Power Geyser | 3050 | 87 | 50 |

`3050` é o MAX Power Geyser da origem (três pilares), não o Buster Wolf;
o HitDef de corpo usado como workaround foi removido e o golpe roda como
projétil estacionário com o clipe alternativo 3020. O Buster Wolf real
está em 3200/3250. O Double Kong reusa o clipe do Power Dunk para caber no
orçamento de CHR.

### Andy

1400/1450 (Gekiheki Haisui), 1500 (Genei Shiranui), 1160 (Hishou Ken EX),
3000/3010/3050 (Chou Reppa Dan) e 3200/3210/3250 (Dan Da Dan). 1400 e 1450
usam os rearmes de `MoveHitReset` da origem; 3000/3010/3050 rearmam a cada
golpe e mantêm a vítima em hitstun. O Dan Da Dan da origem repete o rush
até 4/10 vezes; sem loop de state no motor, ele foi aproximado como
entrada + um contato do rush + finalizador (2 contatos). Bakushin 1700
segue pendente (cadeia de agarrão 1705/1710).

### Ryo

1150/1160 (Koho EX), 1250/1260 (Hien Shippuu '95), 2100 (Ko'ou Geki,
projétil de dois níveis de helper), 3250 (MAX Tenchi Haoh Ken), 1050
(Ko'ou Ken EX), 1400 (Renbu Ken, 3 contatos) e 2000/2010 (Ko'ou Ken
aéreo). O 3150 (MAX Ryuuko Ranbu) continua pendente.

### Robert

1050 (Ryuugeki Ken EX), 3200/3210/3220 (Muei Shippuu Juudan Kyaku) e
3270 (MAX Muei Senpuu, reusando o clipe MAX).

### Rugal

1800 (Beads Destruction). A AIR 1800 não veio no pacote importado; o
golpe reusa um clipe de soco e mantém o HitDef/alcance. O Eye Beam 1700
continua bloqueado: a AIR 1704 também não existe no pacote.

### Iori

3100/3110/3150 (Ya Sakazuki): os roots da origem só tocam a invocação; a
chama vive no helper 3120 (projétil 3104). Os três slots usam o clipe do
root com dano por ProjTab 6/8/12 e release no segundo frame.

### Ainda bloqueado

- **Omega Rugal** — Gravity shot 7100 e RE 8000: a AIR 8000 e o victim
  state 8001 não foram portados; o personagem também compartilha a célula
  37 com o Rugal no seletor, então o harness headless não o seleciona.
- **Takuma** — 1400/1410, 1600/1610 e 1050/1060: a tabela gerada do
  personagem está no limite de 32 KiB do banco; seis sids novos estouram
  o assert de build. Os quatro comandos existentes seguem intactos.
- **Rugal** — Eye Beam 1700 (AIR 1704 ausente).

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$DAE7`**
- layout MSU **`0x3E20`**
- `.sfc` SHA-256 `3bcd1a54…25ed0a`
- `.msu` SHA-256 `285ef936…5b279d`

Copie `.sfc` e `.msu` juntos.

