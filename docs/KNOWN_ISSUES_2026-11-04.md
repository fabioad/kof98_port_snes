# Known Issues — build de 04/11/2026

Levantamento dos golpes ainda incompletos no port. O foco é o que o jogador
percebe em partida: comando que não sai, golpe que não sobe/acerta, super
que não existe e efeito ausente.

## Escopo e método

- **Categoria A** — varredura dos `[State -1]` dos CMDs contra os states
  realmente ligados (`moves` + `POST_CAL_REACTIVATED`). É a lista mais
  confiável: o comando existe, mas não encontra state.
- **Categoria B** — estados cujo corpo/ataque real está em um **Helper**
  (clone, projétil ou efeito). O motor SNES não roda Helpers; em vários
  casos o build copia o HitDef/velocidade para o state principal, mas nem
  sempre.
- **Categoria C** — cadeias desativadas de propósito ou adaptadas.
- **Categoria D** — variantes MAX/SDM e especiais que a auditoria de
  24/10 ainda listava como não religadas. Alguns states podem ser fases/
  continuações do golpe pai; confira o state exato no documento de
  auditoria.
- **Categoria E** — efeitos (Explod/PalFX/AfterImage) ausentes ou
  aproximados.
- **Categoria F** — particularidades de custo, victim states e comandos
  com variante por expressão.

## A. Comandos — corrigidos em 04/11

A varredura inicial (CMD contra `moves` + `POST_CAL_REACTIVATED`) não
contava o `POST_CAL_SUPERS`, que já restaurava nove desses comandos da
dieta de ROM. A auditoria funcional no headless encontrou três problemas
reais:

1. **Mai** — o comando terminava em `~z` e o parser descartava a definição
   inteira, deixando o golpe sem linha no `CmdTab`.
2. **Final `z` (Chin/Mai)** — o pad roteia R para `y|b` e só acrescenta o
   token `z` enquanto R está segurado. O matcher é first-match-wins, então
   o super `y` consumia o botão antes do super `z`. Regras de mesmo
   tamanho com final `z` agora vêm primeiro.
3. **Dano no follow-up** — os supers de agarrão entravam no state raiz,
   mas o `p1stateno` (o state que prende o adversário e aplica o dano) não
   estava ligado. Foram religados em slots 103–111, a janela que o
   `StVictimHeld` reconhece como agarrão.

| Personagem | Golpe / state | Situação / dano no headless |
|---|---|---|
| **Joe** | MAX Bakuretsu Hurricane Tiger Kakato (3150) | já restaurado por `POST_CAL_SUPERS`; 71 |
| **Chin** | Zake FireBall Double (1920) | prioridade `z`; 55 |
| **Mai** | Super QCF×2 + C / Gekka Botan (2070) | parser `~z` + follow-up 2071; 31 |
| **Yamazaki** | Guillotine fraco/forte (3000/3010) e MAX Drill (3150) | 22 cada; MAX Drill com 3151; 41 |
| **Blue Mary** | MAX2 do Super Dunk (3060) e Dynamite Dunk (4000) | 3065 + dash reajustado; 33; 4011; 31 |
| **Geese** | MAX Rashomon (3250) | 3260/3261; 26 |
| **Krauser** | MAX Kaiser Wave (3070) e MAX Gigantic Cyclone (3220) | já restaurado; 34 por tiro; 3221/3222; 31 |
| **Ken** | MAX Shoryu Reppa (3050) | já restaurado; 24 |
| **Chun-Li** | Super QCB×2 + C (3300) | já restaurado; 26 |
| **Kyo Nests** | Orochinagi (3000) | linhas do Kyo base + clipe 3026 sintético; 55 |
| **Kyo Ash** | Orochinagi (3000) | idem; 55 |

> Dano medido contra Kyo com 200 HP no headless, sem treino de combo.

## B. Golpes que dependem de clone/Helper

**Chizuru (DP e especiais/supers de clone religados em 04/11).**
Quase todas as especiais/supers da origem são um clone/Helper:

- O **DP/antiáreo (1200)** foi o caso crítico: o state 1200 era só a
  invocação; quem subia era o Helper 1100. O sid 52 usa um clipe nativo
  curto (AIR 13000) com a velocidade de subida e o HitDef do Helper.
- **QCF/QCB/HCB/RDP (1000/1004, 1100/1102, 1300/1400, 1500)** e os
  **supers 2000/2100/2200** agora chegam aos states e acertam com os
  HitDefs de origem. O HCB era consumido pelo QCB (os dois encurtados para
  quatro elementos); `cmd_priority` corrigiu a ordem.
- O super 2000 usa o clipe 13001 (hold de invocação de 130 → 6 ticks) e
  dois contatos (36); o 2200 foi fixado em 48.
- O **sprite do clone** continua ausente: a Chizuru executa a pose/ataque
  com o próprio corpo. É a mesma aproximação do DP; faltam só os efeitos
  de PalFX/AfterImage (Categoria E).

Outros com **HitDef/ataque real dentro de Helper** (o build aproxima;
alguns funcionam, outros ficam incompletos):

- **Shingo** — 3150 (MAX) usa vários Helpers (7600/99999/9900/7500/7510/
  7530/7540/6500/8100).
- **Athena** — 4000/Crystal Bit e 2000/2020/2050 (Phoenix Fang) usam
  Helpers de corpo/efeito.
- **Mai** — 2000/2010 (super) usam Helper 40000.
- **Rugal / Omega Rugal** — 1300/1310/1500/1550/1040/2000/2899/3000/
  6000/7000/7200/8100 têm Helpers de corpo/projétil.
- **Kyo / Nests / Ash** — 3000/3200/3210/3500/3550 (HitDefs em Helpers
  3205/3220/7000/7010).
- **Benimaru** — 1000/1010/1100/1110/1401/1411/3000/3010/3050 (o
  antiáreo 1401/1411 já foi adaptado).
- **Leona** — 1200/1201/1400/1401/1500/1510 (Earring Bakudan etc.).
- **Daimon** — 1000/3100/3150/3170.
- **Terry, Andy, Ryo, Robert, Heavy D, Chang, Mr. Big, Eiji, Geese,
  Krauser** — HitDefs em Helpers/projéteis; parte já é copiada para o
  state principal, parte é aproximada.

> “Helper aproximado” não significa necessariamente que o golpe não sai.
> O DP da Chizuru era o caso crítico (o **corpo do clone** era o próprio
> golpe); agora tem uma aproximação nativa. Os outros golpes de clone dela
> ainda dependem do mesmo tratamento.

## C. Cadeias desativadas / parciais

- **Clark (corrigido em 04/11)**
  - **3050** (MAX Ultra Argentine) e **3100/3110/3150** (Running Three)
    religados. O MAX reutiliza a cadeia 3010–3016; o Running Three usa
    3105 (agarrão), 3110 (arremesso) e 3111 (finalizador) na faixa 60–69.
  - **1600** (Flashing Elbow) ligado em 112–114 (run/ataque/recuperação),
    com comando direto QCF+C e follow-up opcional de 1420/1510.
  - **Running Three MAX** ganhou o input HCF×2+C para não colidir com o
    Ultra Argentine (HCB×2+X/Y).
  - 1205/1305 reutilizam a anim 1200 e 1420 reutiliza a 3011 (pose visual
    reaproveitada). O Frankensteiner 1400/1410→1420 ainda faz só 1 de
    dano (pendência separada).
- **Ralf**
  - 520/550/570 estão ligados e dão dano/knockdown, mas de forma
    **aproximada**: faltam os victim states de queimadura (80010/80011/
    80002/80018) e os explods/palFX originais.
- **Iori** — 1310 (Koto Tsuki In forte) e a família Tsumagushi 1501/1511
  são adaptações, não os states originais.
- **Takuma** — a tabela foi cortada para caber no banco 83; só quatro
  comandos foram mantidos.

## D. Variantes MAX/SDM e especiais ainda não religados

Auditoria de 24/10 contra o build atual. Alguns states podem ser
continuações/fases do golpe pai.

| Personagem | Principais pendências |
|---|---|
| **Iori** | Ya Sakazuki 3100/3110/3150 implementados em 05/11 (6/8/12; clipe do root + projétil 3104) |
| **Kyo / Nests / Ash** | Mushiki '96 3100/3150 (47/58), MAX Mushiki 3250 (24), Koto Tsuki You 1400/1410 (10), 182 Shiki '99 (18) e Orochinagi MAX 3050 (55) implementados em 05/11; 3000, 3500/3550 e 3305 em 04/11. Resta apenas o Orochinagi forte 3010 |
| **Rugal** | Beads Destruction 1800 (14) e Eye Beam 1702 (14) implementados em 05/11 (AIR 1702 reusa o Reppuken e a AIR 1704 é sintetizada do grupo 1700); Gravity Smash forte 1560 pendente |
| **Omega Rugal** | Gravity shot 7100 (14) e RE 8000 (40) ligados em 05/11 (victim state 8001 aproximado por knockdown); restam Gravity Smash 1050/1055, projéteis 1010/1011 e RE2 2310 |
| **Takuma** | Mouko Burai Gan 1400/1410 (13), Koho 1600/1610 (13), Ko'ou Ken ura 1050/1060 (14/18), Haoh 1500/1510 (20), Shin Kishin Geki 3100 (32) e Kyokugen Koho 3300/3320 (36) implementados em 05/11. O 3200/3210 é a mesma família Haoh coberta pelo 1500/1510; o MAX 3220 segue ligado |
| **Terry** | 1050/1450/1550/1560/1600/1700/3100 implementados em 05/11 (14/12/30/34/16/20/32); Buster Wolf 3200/3250 com 3 contatos (34/48); MAX Geyser 3050 50 |
| **Andy** | 1400/1450/1500/1160, Chou Reppa 3000/3010/3050 (12/8/14/14/37/52/57), Dan Da Dan 3200/3210/3250 (33/33/44, 2 contatos) e Bakushin 1700 (45, agarrão) implementados em 05/11 |
| **Joe** | Screw Upper 3010 (34), Bakuretsu 3100/3101 (64), Thunder Fire 3200/3201 e MAX 3250/3251 (39/49) e Slash Kick 1310 (19) implementados em 05/11 |
| **Ryo** | 1150/1160/1250/1260/2100/3250, Ko'ou Ken EX 1050, Renbu 1400, aéreo 2000/2010 e MAX Ryuuko 3150 (98) implementados em 05/11 (26/32/14/28/13/30/14/12/14/14/98) |
| **Robert** | 1050/3200/3210/3220/3270 implementados em 05/11 (14/24/37/47/44); 1250/1260 Hien (28/42), 1400 Renbu (16, 4 contatos), 1450 Sen'en (16, 4 contatos) e Haoh 3000/3010/3020 (14/14/14) em 05/11 |
| **Yuri** | MAX Haoh 550 (20, projétil) e MAX Ryuuko 560/561 (10) implementados em 05/11 |
| **Athena** | Phoenix Fang Arrow 2000/2020/2050. 3000/3050/3100 implementados com a bola 7700 (48/42/40); 4000 confirmado (62) |
| **Kensou** | Sen Shippo 1300/1330 (23/28), Niku Man 2000 (power-up), Sen Ki Hakkei 2100 (30) e Chouryuu Renken 2200 (25) implementados em 05/11 |
| **Chin** | Fire Zake 1203/1300 (20/20, projéteis), upper forte 1400 (17), Super Long Walk Hell 1750 (32) e Hyper Long Walk Hell 2200 (40) implementados em 05/11. Zake FireBall Double 1920 religado (04/11) |
| **King** | Mirage Dance 1500 (24), MAX Illusion 3200 (46), Silent Flash 3300/3400 (30/40), Surprise Rose 3600/3700 (39/49) e Dragooner 3800 (61) implementados em 05/11 |
| **Mai** | Bachi 1038/1040 (16), Toki Tsubute 1050 (20), Hishou Ryuu'en Jin 1080/1082 (30/35) e MAX2 2030/2031 (5) implementados em 05/11 |
| **Kim** | Houou Kyaku 3000/3020 (15/25) e Houou Hiten 3200/3201/3210/3220/3221 (16/16/61) implementados em 05/11 |
| **Chang** | Haki Kyaku 1400 (20) e Tekkyuu Dai Assatsu nível 2 3400 (80) implementados em 05/11 |
| **Choi** | Tatsumaki 1000/1010 (25/30), Senpuu 1100 (20), Hishou 1200 (20), Shissou 1600 (15), Ultimate Storm 2400 (30), Zan! En Getsu Rin 3100 (35) e Houou Kyaku 3200 (30) implementados em 05/11 |
| **Chang** | Haki Kyaku 1400; Tekkyuu Dai Assatsu 3400 |
| **Choi** | Tatsumaki 1000/1010; Senpuu 1100; Hishou 1200/1210; Shissou 1600/1610; Ultimate Storm 2400; Zan! En Getsu Rin 3100/3110; Houou Kyaku 3200/3250 |
| **Yashiro** | Orochi 2200/2210, 2300/2310; MAX Million Bash 3020; Final Impact 3100/3120; Orochi supers 3510/3520/3600/3620/3700/3720 |
| **Shermie** | normais 1000/1050, 1100/1150, 1200/1250, 1300; Orochi 7100/7150, 7225/7250/7275, 7350; 2100; 8100/8150; 8000 |
| **Chris** | normais 1300/1350, 1500/1550, 1600/1650; Orochi 7000/7010, 7200/7250, 7300/7350; 2100/2200; 8000/8050; 8100/8105 |
| **Yamazaki** | Bakudan Pachiki 1400; Todome 1600; MAX Guillotine 3020. 3000/3010/3150 religados (04/11) |
| **Blue Mary** | Straight Slicer 1600/1610; Super Dunk 3000/30000; Dynamite 3100; Splash Rose 3300/3400; Typhoon 3800; Infinity Rose 50000. 3060/4000 religados (04/11) |
| **Geese** | Raimei Gouha Nage 1500; Shinkuu Nage 1600. 3250 religado (04/11) |
| **Krauser** | Phoenix Throw 1600; Kaiser Claw 1700; Kaiser Inferno 3100/3150; Unlimited Desire 3300/3310/3320. 3070/3220 religados (04/11) |
| **Ken** | Tatsumaki aéreo 1250; Oosoto Mawashi 1320; Shippuu Jinrai 3100/3150; Shinryuuken 3200. 3050 religado (04/11) |
| **Chun-Li** | Kikouken novo 1050; Spinning Bird aéreo 1250; Kikou Shou 3000; Houyoku Sen 3100; Hazan Tenshou 3200. 3300 religado (04/11) |
| **Sakura** | Ouka Kyaku 1400; Haru Ichiban 3150; Midare Zakura 3200/3250; 3300 |
| **Heavy D** | D. Shadow 2200 |
| **Brian** | American Supernova 3300; Galaxy Cyclone 3400; Big Bang Tackle 3500/3600 |
| **Billy** | Flaming Stick Spin 1860; entradas 2510/2600/6000 |
| **Lucky** | Shoot 2/3/4 2200/2300/2400; Finger Roll 2500; Slam 2700/2800; 4700; Finger Roll SDM 3100; Shoot Out 3400/3500 |
| **Mr. Big** | Crazy Drum 1100/1101 (12), Drum Shot 1500 (20), MAX Blaster Wave 3050 (30, projétil) e Rising Spear 3100 (30) implementados em 05/11 |
| **Eiji** | Kikouhou 1000 (14, projétil), Mukuro Nui 1600 (14), Zantetsu Tourouken 3100/3120 (20/30) e Yamikari 3200 (35) implementados em 05/11 |

## E. Efeitos (Explod/PalFX/AfterImage) ausentes ou aproximados

- **Ralf** — 520/550/570 sem os explods/palFX e victim states de
  queimadura.
- **Chizuru** — efeitos de clone/PalFX/AfterImage dos supers
  (2000/2100/2200); o DP já foi convertido para uma aproximação nativa.
- **Chang** — a **bola de metal não aparece em cima** durante o golpe
  (visual do projétil/Explod ausente). Reportado em 04/11.
- **Mature** — variantes e efeitos de PalFX/Explod dos supers
  3000/3500/3600.
- **Athena/Kensou/Chin** — os efeitos de magia (orbes, MagicBurst,
  garrafa do Chin) já foram implementados em boa parte; o que resta são
  Explods/continuações específicas.
- **Regra geral** — AfterImage foi removido de todos os personagens de
  propósito; efeitos dentro de Helper/Explod continuam aproximados.

## F. Outras categorias

- **MAX em slot especial sem desconto**: Iori (103), Saisyu/Heidern/
  Clark (66) usam o custo direto do PowTab, sem a janela MAX.
- **Victim states de arremesso não portados**: Ralf (queimadura 80010/
  80011/80002/80018); Clark reutiliza animações (1205/1305→1200,
  1420→3011).
- **Comandos com variante por expressão**: golpes cujo
  `value = 3050 + var(...)` podem ter a variante MAX/SDM faltando mesmo
  com o comando base funcionando; a varredura de comando só pega o valor
  literal.
- **Calibração de dano**: exemplos conhecidos são o Shou'ou Ken forte da
  Sakura (30 vs 26) e ajustes pontuais de dano de alguns supers.

## Prioridade recomendada

1. **Categoria D (em andamento)** — primeiro bloco concluído em 04/11
   (Kyo/Nests/Ash 3500/3550/3305, Terry 3000/3010/3050, Athena
   3000/3050/3100/4000). Segundo bloco concluído em 05/11: Terry
   1050/1450/1550/1560/1600/1700/3100 e Buster Wolf 3200/3250 (3
   contatos), Andy 1400/1450/1500/1160/3000/3010/3050, Dan Da Dan
   3200/3210/3250 e Bakushin 1700, Ryo 1150/1160/1250/1260/2100/3250/
   1050/1400/2000/2010/3150, Robert 1050/1250/1260/1400/1450/3000/3010/
   3020/3200/3210/3220/3270, Kyo/Nests/Ash Mushiki '96 3100/3150, MAX
   Mushiki 3250, Koto Tsuki You 1400/1410, 182 Shiki '99 e Orochinagi
   MAX 3050, Rugal 1800 + Eye Beam 1702, Omega Rugal 7100/8000 e Iori
   3100/3110/3150. Terceiro bloco concluído em 05/11: Takuma, Joe, Mai,
   Kim, King, Yuri, Mr. Big e Eiji (40 golpes). Quarto bloco concluído em
   05/11: Kensou, Chin, Chang e Choi (20 golpes; ver
   `tools/test_category_d_batch3_headless.py`). Restam Kyo Orochinagi
   3010 e os demais personagens da tabela D.
2. **Categoria E** — efeitos e victim states (Ralf, Mature, Chizuru,
   bola de metal do Chang). Na Chizuru faltam os PalFX/AfterImage e o
   clone visual dos supers.
3. **Clark** — cadeias e Flashing Elbow concluídos em 04/11; resta o
   Frankensteiner 1400/1410→1420 (1 de dano).
4. **Chizuru** — DP e golpes de clone concluídos em 04/11 (10 comandos);
   resta apenas o sprite do clone/efeitos.
5. **Categoria A** — concluída em 04/11 (ver tabela acima); manter a
   regressão dos comandos ao mexer no parser/matcher.

## Nota sobre a Chizuru

O antiáreo (DP, `F, D, DF + botão`) foi corrigido em 04/11. O state 1200
era apenas a invocação do clone; a subida/ataque estava no Helper 1100
(anim 1100/1110, `VelSet y=-9.5`, HitDefs e descida). Como o motor não
roda Helpers, o corpo principal ficava no chão, executava a animação 1200
(106 ticks) e recuperava devagar.

A correção mantém o comando no state 1200 (para não quebrar o `CmdTab`),
mas troca a animação por um clipe nativo curto (AIR 13000), aplica a
velocidade de subida (`vy = -9.5 px/tick` no elemento 7) e o HitDef do
Helper (18 de dano, knockdown). Teste: `tools/test_chizuru_dp_headless.py`
— pico de ~98 px, P2 200→182, knockdown e retorno ao estado 0.

Os especiais/supers de clone dela (1000/1004, 1100/1102, 1300/1400,
1500, 2000/2100/2200) foram religados em 04/11 e acertam com os HitDefs
de origem. O que resta é o **sprite do clone** e os efeitos de
PalFX/AfterImage (Categoria E).

## Resumo do que falta

- **Categoria D (restante)** — Robert, Andy, Ryo, Kyo/Nests/Ash, Rugal,
  Omega Rugal (7100/8000), Takuma, Joe, Mai, Kim, King, Yuri, Mr. Big,
  Eiji, Kensou, Chin, Chang e Choi concluídos em 05/11; restam o Kyo
  Orochinagi forte 3010, o runtime do Omega (célula 37 compartilhada no
  harness) e as pendências dos demais personagens listadas na tabela da
  seção D (Yashiro, Shermie, Chris, Yamazaki, Mary, Geese, Krauser, Ken,
  Chun-Li, Sakura, Heavy D, Brian, Billy, Lucky).
- **Categoria E** — efeitos/victim states: Ralf (queimadura), Mature
  (PalFX/Explod), Chizuru (clone/PalFX) e a bola de metal do Chang.
- **Clark** — Frankensteiner 1400/1410→1420 ainda faz só 1 de dano.
- **Categoria F** — MAX em slot especial sem desconto (Iori 103,
  Saisyu/Heidern/Clark 66) e a calibração de dano de alguns golpes
  (ex.: Shou'ou Ken forte da Sakura, 30 vs 26).
- **Categoria A** — concluída; manter a regressão de comandos.

## Build de referência

`build/teamfix_benimaru_20261103/`

- checksum **`$F475`**
- layout MSU **`0xF8A5`**
- `.sfc` SHA-256 `16879e6e…544c6a`
- `.msu` SHA-256 `9dbbbc0b…0f0cc1`

## Referências

- `docs/GOLPES_FALTANTES_MUGEN_SNES_2026-10-24.md` — auditoria completa
  state a state.
- `docs/REATIVACAO_STATES_2026-11-02.md` — states religados e limites
  conhecidos.
- `docs/TEAM_DAIMON_STAGING_2026-11-03.md` — correções recentes do Team
  Play.
- `docs/COUNTER_BANNER_2026-11-03.md`, `docs/RALF_MOUNT_AI_FREEZE_2026-11-03.md`
  — correções recentes de HUD/IA/Ralf.
