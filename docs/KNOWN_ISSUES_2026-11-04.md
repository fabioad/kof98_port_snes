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
  com variante por expressão (auditados em 05/11).

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
    reaproveitada). O Frankensteiner 1400/1410→1420 foi calibrado em
    05/11: o agarrão agora faz 30 de dano (`slice_damage` 56/57).
- **Ralf**
  - 520/550/570 estão ligados e dão dano/knockdown; em 05/11 os victim
    states 80010/80011/80002/80018 foram mapeados para o slot de
    arremesso (77) e os Explods de fogo usam os clipes FlameRise/
    FlameTop/MagicBurst. A animação de queimadura original continua
    aproximada.
- **Iori** — 1310 (Koto Tsuki In forte) e a família Tsumagushi 1501/1511
  são adaptações, não os states originais.
- **Takuma** — o limite do banco 83 foi resolvido com a separação do
  blob de metasprites (`SPLIT_OLD`); os especiais restantes estão
  implementados e listados na seção D.

## D. Variantes MAX/SDM e especiais — estado final (concluída)

Auditoria de 24/10 contra o build atual. Alguns states podem ser
continuações/fases do golpe pai.

| Personagem | Principais pendências |
|---|---|
| **Iori** | Ya Sakazuki 3100/3110/3150 implementados em 05/11 (6/8/12; clipe do root + projétil 3104) |
| **Kyo / Nests / Ash** | Mushiki '96 3100/3150 (47/58), MAX Mushiki 3250 (24), Koto Tsuki You 1400/1410 (10), 182 Shiki '99 (18) e Orochinagi MAX 3050 (55) implementados em 05/11; 3000, 3500/3550 e 3305 em 04/11. O Orochinagi forte 3010 (20) foi implementado em 05/11 via HCB+A+B no sid 104 |
| **Rugal** | Beads Destruction 1800 (14) e Eye Beam 1702 (14) implementados em 05/11 (AIR 1702 reusa o Reppuken e a AIR 1704 é sintetizada do grupo 1700); Gravity Smash forte 1560 pendente |
| **Omega Rugal** | Gravity shot 7100 (14), Gravity Smash 1050/1055 (40/47), RE2 2310 (30) e dark dashes 1010/1011 (24/26) rodam no runtime; o comando RE usa o clipe do Gravity Smash (30) porque o state 8000 original tem o hitbox visual e o victim state 8001 não veio no pacote |
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
| **Yashiro** | Odoru Daichi 2200/2210 (20), Kujiku Daichi 2300/2310 (22), MAX Million Bash 3020 (44), Final Impact 3100/3120 (49), Araburu Daichi 3600/3620 (30) e Ankoku Jigoku 3700/3720 (40) implementados em 05/11 |
| **Shermie** | Axle Spin/Shoot 1000/1050/1100/1150 (15), Whip 1200/1250 (20), Spiral 1300 (25), Carnival 2100 (30), Shajitsu 7100/7150 (25), Mugetsu/Yatanagi 7225/7250/7275/7350 (30), Shukumei 8000 (40) e Ankoku Raikouken 8100/8150 (25) implementados em 05/11 |
| **Chris** | Slide Touch 1300/1350 (20), Direction Change 1500/1550 (20), Shooting Dancer 1600/1650 (25), Twister/Chain Slide 2100/2200 (35), Taiyou 7000/7010 (15), Tsuki 7200/7250 (30), Shishi 7300/7350 (35) e Gouka/Ankoku Orochinagi 8000/8050/8100/8105 (45) implementados em 05/11. 1600/2100 são projéteis no port; o dano vem do byte do `ProjTab` |
| **Yamazaki** | Bakudan Pachiki 1400 (20), Todome 1600/1601 (20/15) e MAX Guillotine 3020 (30) implementados em 05/11 |
| **Blue Mary** | Straight Slicer 1600/1610 (20/22), Super Dunk 3000/30000 (30/40), Dynamite 3100 (25), Splash Rose 3300/3400 (25/30) e Typhoon/Infinity Rose 3800 (30) implementados em 05/11 |
| **Geese** | Raimei Gouha Nage 1500 (25) e Shinkuu Nage 1600 (30) implementados em 05/11 |
| **Krauser** | Phoenix Throw 1600 (25), Kaiser Claw 1700 (30), Kaiser Inferno 3100/3150 (30/40) e Unlimited Desire 3300/3310/3320 (30/35/40) implementados em 05/11 |
| **Ken** | Tatsumaki aéreo 1250 (20), Oosoto Mawashi 1320 (25), Shippuu Jinrai 3100/3150 (30/40) e Shinryuuken 3200/3201 (30) implementados em 05/11 |
| **Chun-Li** | Kikouken novo 1050 (20), Spinning Bird aéreo 1250 (25), Kikou Shou 3000 (25), Houyoku Sen 3100 (30) e Hazan Tenshou 3200 (35) implementados em 05/11 |
| **Sakura** | Ouka Kyaku 1400 (20), Haru Ichiban 3150 (35), Midare Zakura 3200/3250 (30/40) e Shinkuu Hadouken 3300 (30) implementados em 05/11 |
| **Heavy D** | D. Shadow 2200 (35) implementado em 05/11 |
| **Brian** | American Supernova 3300 (35), Galaxy Cyclone 3400 (40), Big Bang Tackle 3500 (30) e American Final Tackle 3600 (40) implementados em 05/11 |
| **Billy** | Flaming Stick Spin 1860 (25), Super Stick Swing S 2510 (30), Chou HongRenSalgon S 2600 (35) e MAX2 6000 (45, `ProjTab`) implementados em 05/11 |
| **Lucky** | Shoot 2/3/4 2200/2300/2400 (20), Finger Roll 2500 (25), Slam 2700/2800 (25), Air Slam 4700 (30), Finger Roll SDM 3100 (30) e Shoot Out 3400/3500 (35) implementados em 05/11 |
| **Mr. Big** | Crazy Drum 1100/1101 (12), Drum Shot 1500 (20), MAX Blaster Wave 3050 (30, projétil) e Rising Spear 3100 (30) implementados em 05/11 |
| **Eiji** | Kikouhou 1000 (14, projétil), Mukuro Nui 1600 (14), Zantetsu Tourouken 3100/3120 (20/30) e Yamikari 3200 (35) implementados em 05/11 |

## E. Efeitos (Explod/PalFX/AfterImage) ausentes ou aproximados

- **Ralf** — 520/550/570 ganharam um flash de impacto (PalFX) em 05/11;
  os explods e os victim states de queimadura continuam aproximados.
- **Chizuru** — os supers 2000/2100/2200 ganharam flash de impacto e os
  Explods 4950/4951/15600–15602 usam o clipe MagicBurst em 05/11; o
  sprite do clone e o AfterImage continuam ausentes.
- **Chang** — a bola agora aparece em cima (Explod 17100/17110) usando o
  clipe Bottle como aproximação; o sprite original do metal não coube no
  pool de 16 células dos efeitos.
- **Mature** — os supers 3500/3600 ganharam flash de impacto e os
  Explods 910/911/11000/11010/11020 usam o clipe MagicBurst em 05/11; as
  variantes 3000 ainda são aproximadas.
- **Athena/Kensou/Chin** — os efeitos de magia (orbes, MagicBurst,
  garrafa do Chin) já foram implementados em boa parte; o que resta são
  Explods/continuações específicas.
- **Regra geral** — AfterImage foi removido de todos os personagens de
  propósito; efeitos dentro de Helper/Explod continuam aproximados.

## F. Outras categorias

- **MAX em slot especial**: Iori (103), Saisyu/Heidern/Clark (66)
  receberam o bit de MAX no `MAX_SIDS_EXTRA` em 05/11; a janela MAX agora
  aplica o custo correto.
- **Victim states de arremesso**: os do Ralf (80010/80011/80002/80018)
  foram mapeados para o slot de arremesso em 05/11; Clark reutiliza
  animações (1205/1305→1200, 1420→3011).
- **Comandos com variante por expressão**: auditados em 05/11. Os
  arquivos `*_SNES.cmd` usados pelo build têm `value` literal; as
  expressões `value = 3050 + var(...)` existem apenas nos `.cmd`
  originais, que não entram na ROM. Não há variante MAX/SDM faltando por
  esse motivo.
- **Calibração de dano**: o corpo do Shou'ou Ken forte da Sakura foi
  ajustado para 26 em 05/11 (o projétil ainda soma à parte). Chris
  1600/2100 (25/35) e Billy 6000 (45) foram corrigidos pelo byte de dano
  do `ProjTab` em 05/11; esses golpes são projéteis no port, então
  `slice_damage`/`DamageTab` não os alcançavam.
- **Adaptações de dano (05/11)**: Krauser 1700 Kaiser Claw (30),
  Chun-Li 3100 Houyoku Sen (30), Sakura 1400 Ouka Kyaku (agora entra no
  state 1200, 30) e os golpes do Lucky 2200/2300/2400/2500/2700/2800/
  4700/3100/3400/3500 (20–35) foram religados reusando clipes
  existentes, sem arte nova.

## Prioridade recomendada

1. **Categoria D (concluída)** — primeiro bloco concluído em 04/11
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
   05/11: Kensou, Chin, Chang e Choi (20 golpes). Quinto bloco concluído
   em 05/11: Yashiro, Shermie e Chris (27 golpes). Sexto bloco concluído
   em 05/11: Yamazaki, Blue Mary, Geese, Krauser, Ken, Chun-Li, Sakura,
   Heavy D, Brian, Billy e Lucky (49 golpes). Fechamento em 05/11: Kyo
   Orochinagi 3010 (20 nas três variantes) e Omega Rugal no runtime
   (L+R na célula do Rugal; 7100/8000). A Categoria D está concluída.
2. **Categoria E** — flashes de impacto adicionados em 05/11 (Ralf,
   Mature, Chizuru, Chang e Clark); ainda faltam os Explods completos, os
   victim states de queimadura do Ralf, a bola de metal do Chang e o
   sprite/AfterImage do clone da Chizuru.
3. **Clark** — cadeias, Flashing Elbow e Frankensteiner (30 de dano)
   concluídos.
4. **Chizuru** — DP e golpes de clone concluídos; resta o sprite do
   clone/efeitos.
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

- **Categoria D** — concluída em 05/11: todos os personagens da tabela D,
  incluindo Kyo/Nests/Ash Orochinagi 3010 e Omega Rugal no runtime
  (seleção escondida L+R). O comando RE usa o clipe do Gravity Smash
  (30) como aproximação; o state 8000 original continua visual porque o
  victim state 8001 não veio no pacote.
- **Categoria E** — os flashes e Explods principais já entram; ainda
  faltam:
  - **Ralf** — animação de queimadura fiel (os victim states já vão para
    o slot de arremesso).
  - **Chang** — o sprite original da bola de metal (a bola aparece com o
    clipe Bottle).
  - **Chizuru** — sprite do clone e AfterImage dos supers.
  - **Mature** — Explods completos das variantes 3000.
  - **Athena / Kensou / Chin** — Explods/continuações específicas.
- **Categoria B** — golpes cujo ataque real vive em Helper continuam
  aproximados (lista da seção B); não há caso crítico conhecido.
- **Categoria C** — Ralf 520/550/570 aproximados; Iori 1310 e Tsumagushi
  1501/1511 são adaptações.
- **Categoria F** — MAX em slot especial corrigido (Iori 103,
  Saisyu/Heidern/Clark 66); victim states do Ralf mapeados; comandos
  com variante por expressão auditados; resta apenas a calibração fina
  de dano (corpo do Shou'ou Ken forte da Sakura em 26, projétil soma à
  parte).
- **Clark** — Frankensteiner corrigido em 05/11 (30 de dano).
- **Benimaru (05/11)** — Handou Sandan agora entra direto em 1501/1511,
  sem o pulo que cruzava um oponente colado, e ganhou caixa de contato
  para ponto-cego. O Raikouken forte passou a nascer na altura do torso
  (antes subia acima do hurtbox). Os supers 3000/3010/3050 usam ProjTab
  de 5 contatos (30/40/50 totais); Benimaru Collider (30), Electro
  Trigger (30) e Electro Trigger MAX (40) receberam dano. Regressão:
  `tools/test_benimaru_close_headless.py`.
- **Choque de projéteis (05/11)** — quando dois projéteis de lados
  opostos se encontram, ambos são liberados e um spark de impacto +
  `SFX_GUARD` marcam o choque. Sem arte nova; cobre o caso de dois tiros
  simultâneos e preserva o tiro solitário. Regressões:
  `tools/test_projectile_clash_headless.py` (slots injetados) e
  `tools/test_projectile_clash_input_headless.py` (comandos reais).
- **Controles/menu/join (05/11)** — no Team VS o anel do P2 agora é
  desenhado mesmo com o `cpu2` padrão; START no menu com o Pad2 abre o
  select com o cursor do P2 vivo; START do P2 no select liga o lado
  oponente; o join limpa o stream de CHR pendente e valida `C_STAGE`/
  timers antes de `StartFight`, evitando o travamento após a escolha.
  Regressões: `test_menu_p2_start_headless.py`,
  `test_midfight_join_headless.py` e `test_team_vs_start_headless.py`.
- **Robert (05/11)** — Ryuga agora sobe (follow-ups 1101/1111 ligados);
  o Hien Ryujin aéreo ganhou caixa de contato desde o primeiro frame;
  o Hien Shippuu '95 passou para chute e o HCB+K real tem prioridade.
  Regressões: `test_ryo_robert_antiair_headless.py` e
  `test_kyokugen_projectile_anim_headless.py`.
- **Omega Rugal (05/11)** — o Gravity Shot usa o projanim 1357 (feixe)
  em um clipe alternativo comprimido (4 células por frame), não mais a
  orbe do Gravity Smash; isso elimina o estouro de OAM/VRAM. Regressão:
  `test_omega_gravity_headless.py` (14 de dano, 4 células).
- **Queda/knockdown (05/11)** — a ação 5050 tinha duas poses; a segunda
  iniciava um upload de CHR no meio da queda e deixava o corpo em branco
  por alguns frames (o efeito de "surgir de baixo da tela"). O port agora
  mantém a primeira pose de queda até o estado deitado (5110), sem troca
  de página no meio do tombo.
- **Omega Rugal / evasivas (05/11)** — os comandos `ESQ_L/ESQ_F/ESQ_B`
  existiam no CMD mas não tinham regra `State -1` nem slots. Agora:
  L+frente = rolagem para frente (1010/sid 95), L+trás = rolagem para
  trás (1011/sid 94), L sozinho = esquiva parada 720 (sid 69) e DODGE
  (Y+B) também entra na 720. Os clipes 1009/1010 foram trocados entre
  1010/1011 para corrigir a inversão visual: frente usa 1010 e trás usa
  1009. A esquiva parada ganhou afterimage e a regressão confere o
  ponteiro de animação, garantindo que L sozinho não caia no taunt
  (195). Nos demais personagens L sozinho continua taunt; só Omega usa o
  token s para a esquiva. Regressão:
  `tools/test_omega_dodge_headless.py`.
- **Blowback aéreo (05/11)** — o R no ar reutiliza o clipe do normal
  aéreo forte (sid 24), cujo Clsn1 cobria só o braço. Enquanto o latch
  de air-blowback está ativo, o `MinReachBox` une uma caixa de corpo
  inteiro à caixa original do atacante (preservando o alcance do braço);
  os mesmos frames e timings são mantidos. O normal aéreo forte sem o
  latch continua com a caixa original. Regressão:
  `tools/test_air_blowback_headless.py`.
- **King/Yuri — normais de chão (05/11)** — o pack da King tem normais
  close e far; o port misturava as duas séries (chute fraco usava o
  chute forte close e chute forte usava o soco fraco far). Agora os
  quatro botões usam as animações far 250/260/270/280. A Yuri foi
  conferida e já estava correta (200/202/204/206). Regressão:
  `tools/test_king_yuri_normals_headless.py`.
- **Arremessos — pose do alvo (05/11)** — o alvo usava a animação de hit
  em pé (5000), cujo eixo fica nos pés; preso no ponto da mão, parecia
  ser segurado pelos pés. O slot 76 agora usa o sprite de hold ancorado
  no torso (grupo 5011) do próprio SFF do alvo. Custa um sprite por
  personagem, então o layout MSU foi repaginado. Regressão:
  `tools/test_throw_hold_headless.py`.
- **Categoria A** — concluída; manter a regressão de comandos.

## Áudio

- Pacote aprovado Final Fight Guy: 17 módulos em `assets/audio/ffg/`,
  integrado e commitado em `c11317a`.
- `tools/test_ffg_music_headless.py`: **17/17** módulos confirmados na
  ROM (upload real, ARAM, áudio e UI).
- `tools/tests/test_approved_music.py`: **3 passed / 17 subtests**.
- O `.msu` da build de referência contém o pacote FFG atual.
- **Chizuru**: as 10 vozes da `VoiceTab_chizuru` foram transmitidas do
  `.msu` e conferidas byte a byte, e um `PlaySnd` de especial (QCF+X)
  chegou ao `SfxPlay`. Regressão:
  `tools/test_chizuru_audio_headless.py`.
- **SA YARD (05/11)**: o “piano” percebido na luta é a guitarra
  nylon/aço, mapeada no instrumento 1 (`sawstab`). O volume global desse
  instrumento caiu de 128 para 49 (−8,3 dB no total; mais −2,0 dB em
  relação ao ajuste anterior). Bateria e lead não foram alterados.
  Padrões, ordem e `patternSha256` permanecem idênticos; só o `sha256` do
  `stg9.it` mudou. O render standalone com `smconv` confirma a redução a
  partir do trecho em que a guitarra entra.

## Build de referência

`build/teamfix_benimaru_20261103/`

- checksum **`$0D7F`**
- layout MSU **`0x77D7`**
- `.sfc` SHA-256 `f1c20993…4e1a536`
- `.msu` SHA-256 `cefef5ff…0f1c486`
- `.msu` 51.428.864 bytes

## Referências

- `docs/GOLPES_FALTANTES_MUGEN_SNES_2026-10-24.md` — auditoria completa
  state a state.
- `docs/REATIVACAO_STATES_2026-11-02.md` — states religados e limites
  conhecidos.
- `docs/TEAM_DAIMON_STAGING_2026-11-03.md` — correções recentes do Team
  Play.
- `docs/COUNTER_BANNER_2026-11-03.md`, `docs/RALF_MOUNT_AI_FREEZE_2026-11-03.md`
  — correções recentes de HUD/IA/Ralf.
