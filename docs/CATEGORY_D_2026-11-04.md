# Categoria D: primeiro bloco (04/11/2026)

## Escopo

A varredura de comandos mostrou que **todos os `[State -1]` de ataque já
chegam a um state** (com `POST_CAL_SUPERS`/`POST_CAL_REACTIVATED`). O que
restava na Categoria D eram golpes ligados mas incompletos: follow-ups de
agarre não religados, supers cujo ataque vive em Helper e golpes com dano
residual. Este primeiro bloco cobre o grupo citado na prioridade — Kyo,
Nests, Ash, Terry e Athena.

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

O pilar estacionário é um Helper/projétil. O spark chega a nascer no pool
(x=93, y=190), mas o caminho de hit do projétil não conecta enquanto o
super ainda está na janela de ataque. Foi adicionado um HitDef de corpo no
soco de chão (`active=7`, `fall=1`) e uma caixa de ataque nos frames 6–8
dos clipes 3000/3010; o projétil continua como efeito visual.

Resultado: **26** (fraco) e **30** (forte).

### 3050 (Buster Wolf)

O rush também é Helper (três spawns 3060) e o root não tinha HitDef/Clsn1.
Foi adicionado um HitDef de corpo no rush com caixa nos frames 6–21 e
`hit_soft_resets` nos elementos 12/18/24. O resultado atual é **20**
(aproximação de um contato; o knockdown do primeiro hit ainda corta os
contatos seguintes).

## Athena

O **4000** (super que já estava ligado) foi confirmado: **62 de dano**. Os
states 3000/3050/3100 são as fases de carga/invocação do Phoenix Fang e
continuam sem ataque próprio — o golpe que sai é o 4000. Ficam para o
próximo bloco, junto com o clone visual.

## Verificação

Novo `tools/test_category_d_headless.py` — **9 golpes PASS**:

- Kyo 3500/3550: 41; Kyo 3305: 18;
- Nests 3500: 41; Ash 3550: 41;
- Terry 3000: 26; 3010: 30; 3050: 20;
- Athena 4000: 62.

Regressões: `pytest -q tools/tests` **272 passed**, além de
`test_category_a_headless`, `test_clark_chains_headless`,
`test_chizuru_clones_headless`, `test_chizuru_dp_headless`,
`test_ai_headless`, `test_msu_chr_visibility_headless` (960 páginas/56
poses) e `test_super_stage_vram_headless`.

## Ainda na Categoria D

- Athena 3000/3050/3100 (fases de carga do Phoenix Fang) e clone visual.
- Terry: Power Wave EX 1050, Power Charge MOW 1550/1560, Fire Kick 1600,
  Double Kong 1700, High Angle Geyser 3100, Power Dunk MOW 1450.
- Andy, Ryo, Robert e os demais personagens da tabela de 24/10.
- Rugal/Omega Rugal, Takuma, Iori e os MAX/SDM restantes.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$BB7B`**
- layout MSU **`0x1135`**
- `.sfc` SHA-256 `ccd8e340…38120`
- `.msu` SHA-256 `6d9ca6ba…f9528`

O `.msu` cresceu com as animações 3501/3551 do Kyo/Nests/Ash. Copie `.sfc`
e `.msu` juntos.
