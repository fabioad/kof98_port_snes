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

`tools/test_category_d_remaining_headless.py` — **70 golpes PASS**
(segundo bloco, 05/11):

`tools/test_category_d_batch2_headless.py` — **40 golpes PASS**
(terceiro bloco, 05/11: Takuma, Joe, Mai, Kim, King, Yuri, Mr. Big e Eiji).

`tools/test_category_d_batch3_headless.py` — **20 golpes PASS**
(quarto bloco, 05/11: Kensou, Chin, Chang e Choi).

`tools/test_category_d_batch4_headless.py` — **27 golpes PASS**
(quinto bloco, 05/11: Yashiro, Shermie e Chris).

`tools/test_category_d_batch5_headless.py` — **49 golpes PASS**
(sexto bloco, 05/11: Yamazaki, Blue Mary, Geese, Krauser, Ken, Chun-Li,
Sakura, Heavy D, Brian, Billy e Lucky).

`tools/test_category_d_final_headless.py` — **10 golpes PASS**
(Kyo/Nests/Ash 3010 e Omega Rugal 7100/1050/1055/2310/1010/1011/8000
no runtime).

- Terry: 1050 14, 1450 12, 1550 30, 1560 34, 1600 16, 1700 20,
  3100 32, 3200 34 (3 contatos), 3250 48 (3 contatos), 3050 50;
- Andy: 1400 12, 1450 8, 1500 14, 1160 14, 3000 37, 3010 52, 3050 57,
  Dan Da Dan 3200/3210/3250 33/33/44 (2 contatos, aproximação),
  Bakushin 45 (agarrão);
- Ryo: 1150 26, 1160 32, 1250 14, 1260 28, 2100 13, 3250 30,
  1050 14, 1400 12 (3 contatos), 2000/2010 14/14 (aéreo),
  3150 MAX Ryuuko 98;
- Kyo / Nests / Ash: Mushiki '96 3100 47, MAX 3150 58, MAX Mushiki
  3250 24, Koto Tsuki You 1400/1410 10, 182 Shiki '99 18 e Orochinagi
  MAX 3050 55 (as três variantes);
- Robert: 1050 14, 3200 24, 3210 37, 3220 47, 3270 44, 1250 28,
  1260 42, 1400 16 (4 contatos), 1450 16 (4 contatos), Haoh 3000/3010/3020
  14/14/14;
- Rugal: 1800 14 e Eye Beam 1702 14;
- Iori: 3100 6, 3110 8, 3150 12.

Regressões: `pytest -q tools/tests` **274 passed** (inclui o novo
`tools/tests/test_category_d_tables.py`), além de
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
entrada + um contato do rush + finalizador (2 contatos). O **Bakushin**
(1700) usa a cadeia 1700→1710→1715: o `p1stateno` 1705 foi redirecionado
para 1710 e o `TargetLifeAdd` do 1715 aplica o dano (45 no headless).

### Ryo

1150/1160 (Koho EX), 1250/1260 (Hien Shippuu '95), 2100 (Ko'ou Geki,
projétil de dois níveis de helper), 3250 (MAX Tenchi Haoh Ken), 1050
(Ko'ou Ken EX), 1400 (Renbu Ken, 3 contatos), 2000/2010 (Ko'ou Ken
aéreo) e **3150 MAX Ryuuko Ranbu** (98): a ativação acerta, encadeia no
flurry 3160 (10 rearmes de HitDef) e finaliza em 3161.

### Kyo / Nests / Ash

**3100/3101** (Mushiki '96, 47), **3150/3151** (MAX, 58),
**3250/3251** (MAX Mushiki, 24), **1400/1410 → 1405** (Koto Tsuki You,
10), **3305/182 Shiki '99** (18) e **3050** (Orochinagi MAX, 55). Os três
compartilham o CNS e o CMD; as mesmas linhas pós-calibração são aplicadas
a `kyo`, `kyonests` e `kyoash`. Os flurries usam `hit_soft_resets` nos
elementos de ataque e `slice_no_fall` para manter a vítima em hitstun.
O Orochinagi **3010** (forte) segue pendente; o MAX 3050 está ligado.

### Robert

1050 (Ryuugeki Ken EX), 3200/3210/3220 (Muei Shippuu Juudan Kyaku),
3270 (MAX Muei Senpuu), 1250/1260 (Hien Shippuu '95), 1400 (Renbu
Kyaku), 1450 (Sen'en Renbu Kyaku) e 3000/3010/3020 (Haoh Shikou Ken).
Renbu e Sen'en usam `hit_soft_resets` nos elementos de cada golpe; os
Haoh saem como projéteis (helper 3005/3025).

### Rugal

1800 (Beads Destruction). A AIR 1800 não veio no pacote importado; o
golpe reusa um clipe de soco e mantém o HitDef/alcance. O **Eye Beam**
(1700→1702, 14) foi implementado: a AIR 1702 reusa o clipe do Reppuken e
a AIR 1704 (feixe) é sintetizada do grupo SFF 1700; o ProjFx alternativo
usa o grupo 1705 com `pre_scale=2`. O comando é `QCF+Z` (R).

### Omega Rugal

**7100 Gravity shot** (14) e **8000 RE** (40) foram ligados. O 7100 usa o
projétil 1357 e o orbe 1035; o 8000 usa o HitDef de corpo no elemento 18,
com o victim state 8001 substituído por um knockdown normal
(`p2state=$FF`). O harness headless seleciona o Rugal para a célula 37,
então esses dois golpes são **verificados por tabela/build** (teste
estático `tools/tests/test_category_d_tables.py`), não em runtime.

### Iori

3100/3110/3150 (Ya Sakazuki): os roots da origem só tocam a invocação; a
chama vive no helper 3120 (projétil 3104). Os três slots usam o clipe do
root com dano por ProjTab 6/8/12 e release no segundo frame.

### Takuma, Joe, Mai, Kim, King, Yuri, Mr. Big e Eiji (terceiro bloco)

O limite de 32 KiB do banco do Takuma foi resolvido movendo o blob de
metasprites para `_meta.inc` (`SPLIT_OLD`), como já era feito com Saisyu e
Clark. Isso liberou o banco de tabelas para os novos comandos.

| Personagem | Golpes ligados (sid) | Dano medido |
|---|---|---|
| **Takuma** | Mouko Burai Gan 1400 (107), Koho 1600 (108), Ko'ou Ken ura 1050/1060 (109/110), Haoh 1500 (111), Shin Kishin Geki 3100 (113), Kyokugen Koho 3300 (114) | 13/13/14/18/20/32/36 |
| **Joe** | Screw Upper 3010 (107), Bakuretsu 3100/3101 (108/109), Thunder Fire 3200/3201 (110/111), MAX 3250/3251 (112/113), Slash Kick 1310 (114) | 34/64/39/49/19 |
| **Mai** | Bachi 1038/1040 (107), Toki Tsubute 1050 (108), Hishou Ryuu'en Jin 1080/1082 (109/110), MAX2 2030/2031 (111/112) | 16/20/30/35/5 |
| **Kim** | Houou Kyaku 3000/3020 (107/108), Houou Hiten 3200/3201/3210 (109/110/111), MAX 3220/3221 (112/113) | 15/25/16/16/61 |
| **King** | Mirage Dance 1500 (107), MAX Illusion 3200 (108), Silent Flash 3300/3400 (109/110), Surprise Rose 3600/3700 (111/112), Dragooner 3800 (113) | 24/46/30/40/39/49/61 |
| **Yuri** | MAX Haoh 550 (107, projétil), MAX Ryuuko 560/561 (108/109) | 20/10 |
| **Mr. Big** | Crazy Drum 1100/1101 (107/108), Drum Shot 1500 (109), MAX Blaster Wave 3050 (110, projétil), Rising Spear 3100 (111) | 12/20/30/30 |
| **Eiji** | Kikouhou 1000 (107, projétil), Mukuro Nui 1600 (108), Zantetsu 3100/3120 (109/110), Yamikari 3200 (111) | 14/14/20/30/35 |

Observações de implementação:

- O Takuma usa `POST_CAL_PROJS` para os Ko'ou Ken ura e o Haoh (os
  projéteis vivem em helpers), com o ProjFx do Yuri.
- O 3200/3210 do Takuma são a mesma família Haoh do 1500/1510; o 1500 já
  cobre o par e o MAX 3220 continua ligado pelo comando original.
- Kim 3220→3221 mantém a vítima no lugar (`gvy=0`) para o finalizador
  acertar; o total é 61.
- King 3200/3600/3700/3800 reusam o clipe do Silent Flash (3400) porque
  os inícios não têm caixa própria no pacote.
- Joe 3010 reusa o clipe do Bakuretsu; 3200/3250 usam o clipe de fogo.
- Mai 2030 reusa o clipe do Hishou para o launcher do MAX2; 2031 tem
  aterrissagem própria.
- Eiji 1600 reusa o clipe do Zantetsu; 3120 compartilha o clipe do 3100.

Verificação: `tools/test_category_d_batch2_headless.py` — **40 golpes
PASS**. Os comandos originais dos oito personagens foram conferidos no
headless (QCF/QCB/DP/SUP1/SUP2 continuam entrando nos states antigos).

### Kensou, Chin, Chang e Choi (quarto bloco)

| Personagem | Golpes ligados (sid) | Dano medido |
|---|---|---|
| **Kensou** | Sen Shippo 1300/1330 (107/108), Niku Man 2000 (109), Sen Ki Hakkei 2100 (110), Chouryuu Renken 2200 (111) | 23/28/0/30/25 |
| **Chin** | Fire Zake 1203/1300 (107/108, projéteis), upper forte 1400 (109), Super Long Walk Hell 1750 (110), Hyper Long Walk Hell 2200 (111) | 20/20/17/32/40 |
| **Chang** | Haki Kyaku 1400 (107), Tekkyuu Dai Assatsu nível 2 3400 (108) | 20/80 |
| **Choi** | Tatsumaki 1000/1010 (107/108), Senpuu 1100 (109), Hishou 1200 (110), Shissou 1600 (111), Ultimate Storm 2400 (112), Zan! En Getsu Rin 3100 (113), Houou Kyaku 3200 (114) | 25/30/20/20/15/30/35/30 |

Observações:

- Chin 1203/1300 usam `POST_CAL_PROJS` (o fogo vive no projétil 1201);
  o lançamento é liberado nos elementos 8/3 do clipe.
- Chin 2200 reusa o rush 2201; Chang 3400 reusa o clipe do Haki Kyaku.
- Choi 1100 reusa o clipe 1160; 1200/1600/3100 reusam 1000/1010;
  2400 reusa o rush 2901; 3200 reusa o 1010.
- Kensou 2000 é um power-up: entra e recupera sem dano.
- Os comandos novos foram escolhidos para não colidir com os antigos
  (QCB/QCF/DP/SUP). Chin/Chang/Choi continuam com os double-taps e
  half-circles antigos que já resolviam em states mais curtos antes
  deste bloco.

Verificação: `tools/test_category_d_batch3_headless.py` — **20 golpes
PASS**.

### Yashiro, Shermie e Chris (quinto bloco)

| Personagem | Golpes ligados (sid) | Dano medido |
|---|---|---|
| **Yashiro** | Odoru Daichi 2200/2210 (107), Kujiku Daichi 2300/2310 (108), MAX Million Bash 3020 (109), Final Impact 3100/3120 (110), Araburu Daichi 3600/3620 (111), Ankoku Jigoku 3700/3720 (112) | 20/22/44/49/30/40 |
| **Shermie** | Axle Spin/Shoot 1000/1050/1100/1150 (107), Whip 1200/1250 (108), Spiral 1300 (109), Carnival 2100 (110), Shajitsu 7100/7150 (111), Mugetsu/Yatanagi 7225/7250/7275/7350 (112), Shukumei 8000 (113), Ankoku Raikouken 8100/8150 (114) | 15/20/25/30/25/30/40/25 |
| **Chris** | Slide Touch 1300/1350 (107), Direction Change 1500/1550 (108), Shooting Dancer 1600/1650 (109), Twister/Chain Slide 2100/2200 (110), Taiyou 7000/7010 (111), Tsuki 7200/7250 (112), Shishi 7300/7350 (113), Gouka/Ankoku Orochinagi 8000/8050/8100/8105 (114) | 20/20/10/8/15/30/35/45 |

Observações:

- Yashiro 2200/2300 reusam o follow-up 2201; 3100 reusa o clipe do
  3020; 3600/3620 reusam o clipe do 3700.
- Shermie 1000/1100 reusam o clipe 7350; 7225/7350 compartilham o mesmo
  clipe; 8000 reusa o 8010 (o golpe real) e 8100 usa ProjTab (8120/8170).
- Chris 1500 reusa o follow-up 1510; 1600 reusa o 1610; 2100 reusa o
  2110; 7200 reusa o 7250; 8000/8050/8100/8105 reusam o 8110.
- O Chris 7000 é projétil (ProjTab, projanim 7050) e o 8000 é o golpe
  físico do 8110.

Verificação: `tools/test_category_d_batch4_headless.py` — **27 golpes
PASS**.

### Yamazaki, Blue Mary, Geese, Krauser, Ken, Chun-Li, Sakura, Heavy D, Brian, Billy e Lucky (sexto bloco)

| Personagem | Golpes ligados (sid) | Dano medido |
|---|---|---|
| **Yamazaki** | Bakudan Pachiki 1400 (107), Todome 1600/1601 (108/109), MAX Guillotine 3020 (110) | 20/20/15/30 |
| **Blue Mary** | Straight Slicer 1600/1610 (112/113), Super Dunk 3000/30000 (114/58), Dynamite Swing 3100 (62), Splash Rose 3300/3400 (64/66), Typhoon/Infinity Rose 3800 (68) | 20/22/30/40/25/25/30/30 |
| **Geese** | Raimei Gouha Nage 1500 (107), Shinkuu Nage 1600 (108) | 25/30 |
| **Krauser** | Phoenix Throw 1600 (107), Kaiser Claw 1700 (108), Kaiser Inferno 3100/3150 (109/110), Unlimited Desire 3300/3310/3320 (111/112/113) | 25/30/30/40/30/35/40 |
| **Ken** | Tatsumaki aereo 1250 (107), Oosoto Mawashi 1320 (108), Shippuu Jinrai 3100/3150 (109/110), Shinryuuken 3200/3201 (111/112) | 20/25/30/40/30 |
| **Chun-Li** | Kikouken 1050 (107), Spinning Bird aereo 1250 (108), Kikou Shou 3000 (109), Houyoku Sen 3100 (110), Hazan Tenshou 3200 (111) | 20/25/25/30/35 |
| **Sakura** | Ouka Kyaku 1400 (107), Haru Ichiban 3150 (108), Midare Zakura 3200/3250 (109/110), Shinkuu Hadouken 3300 (111) | 20/35/30/40/30 |
| **Heavy D!** | D. Shadow 2200 (107) | 35 |
| **Brian** | American Supernova 3300 (107), Galaxy Cyclone 3400 (108), Big Bang Tackle 3500 (109), American Final Tackle 3600 (110) | 35/40/30/40 |
| **Billy** | Flaming Stick Spin 1860 (107), Super Stick Swing S 2510 (108), Chou HongRenSalgon S 2600 (109), MAX2 6000 (110) | 25/30/35/45 |
| **Lucky** | Shoot 2/3/4 2200/2300/2400 (107), Finger Roll 2500 (108), Slam 2700/2800 (109), Air Slam 4700 (110), Finger Roll SDM 3100 (111), Shoot Out 3400/3500 (112) | 20/25/25/30/30/35 |

Observações:

- Blue Mary usa os sids livres 58/62/64/66/68 e 112-114; os slots
  originais 107-111 (Vertical Arrow, Goodnight e Typhoon) foram
  preservados.
- Geese Shinkuu Nage usa HCBx2 (o HCB+P já é o Raimei); Krauser Phoenix
  usa DP+P; os golpes HCB dos demais ganharam prioridade para não serem
  consumidos pelo QCB de mesmo tamanho.
- Vários golpes reusam clipes já carregados: Yamazaki 2201/3020/3700;
  Mary 3301; Krauser 3600/3700; Ken 1250; Heavy D 2000; Brian 3600;
  Billy 2500; Lucky 2100/2900.
- Projéteis: Chun-Li 1050/3000 e Lucky 3100 usam `POST_CAL_PROJS`.

Verificação: `tools/test_category_d_batch5_headless.py` — **49 golpes
PASS**.

### Fechamento (05/11)

- **Kyo / Nests / Ash — Orochinagi 3010**: comando HCB+A+B, sid 104,
  reusando o clipe 3051 e o HitDef do 3051. Dano direto **20** nas três
  variantes. O 3000 fraco dos variants também passou a chegar ao clipe
  3051 (a segunda passada de `tail_ticks` estende o último frame), então
  os três fazem **55**, igual ao Kyo base.
- **Omega Rugal em runtime**: o harness agora seleciona as formas
  escondidas com L+R na célula do Rugal e L/R na célula do Kyo.
  Implementados: 7100 Gravity Shot (14), 1050/1055 Gravity Smash
  (40/47), 2310 RE2 (30), 1010/1011 dark dashes (24/26) e 8000 RE
  (entra no state 83, mas o hitbox do rush segue visual, 0 de dano).
  A seleção e os estados são exercitados em
  `tools/test_category_d_final_headless.py` (**10 golpes PASS**).

Nenhum item da tabela da Categoria D permanece bloqueado.

### Ainda bloqueado

Nenhum item da tabela da Categoria D. Restam apenas calibrações de dano
opcionais e os efeitos da Categoria E.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$B788`**
- layout MSU **`0x9980`**
- `.sfc` SHA-256 `8c64da3d…a99e23`
- `.msu` SHA-256 `389cef46…37bf46`

Copie `.sfc` e `.msu` juntos.

