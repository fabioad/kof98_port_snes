# Known Issues — build de 04/11/2026

> **Correção em andamento:** [captura dos counters ajustada no fonte](SPECIALS_SUPERS_FIX_PROGRESS_2026-11-06.md).
> Validação na próxima ROM pendente; continuações ofensivas ainda pendentes.

> **06/11 — especiais e supers:** [auditoria funcional dos 50 personagens](SPECIALS_SUPERS_FUNCTIONAL_AUDIT_2026-11-06.md),
> com 1.161 regras de entrada verificadas. Há preparações sem complemento
> ofensivo e flags de captura residuais confirmadas em cinco personagens.
> O documento distingue falhas de ações condicionais e adaptações. Sem build.

> **06/11 — agarrões comuns:** correção dos 100 casos registrada no
> [fonte e testes](NORMAL_THROWS_FIX_2026-11-06.md). Sem build nesta etapa;
> os números da auditoria anterior ainda se referem à ROM antiga.

> **06/11 — build consolidado:** esta ROM inclui todas as correções
> pendentes (agarrões, especiais/supers, áudio e vídeo). O **Power Geyser**
> do Terry agora é apenas hitbox: o projétil continua existindo para dano,
> guarda e coluna alta, mas o clipe alternativo tem zero células e não é
> desenhado. Teste: `tools/test_terry_geyser_headless.py`.

> **06/11 — Geyser e câmera/stage:** o pilar estacionário não empurra mais a
> vítima até a parede (o `ProjPushFar` ignora o pushback quando
> `SPK_GRD` tem a marca de pilar alto, e o `PMT_last` não aplica o slide
> lateral). Com isso o `camx` fica em ~123–125 em vez de correr para a borda,
> e a vítima permanece em ~147–150 depois do golpe. O scroll também ganhou
> validação defensiva (`camx` fora de 0..256 é recalculado) e o `shakeamp`
> impossível (>= 8) é ignorado. Verificado no headless: cenário Terry vs
> Blue Mary (stage 8) sem perda de tiles e `pytest -q tools/tests`
> **301 passed**.

> **Critério de release (autor, 06/11):** preservar as adaptações do port
> e o orçamento atual de recursos. Priorizar glitches, travamentos, dano
> indevido e falhas de captura/soltura/recuperação. Diferenças intencionais
> em relação ao MUGEN não são bloqueadores de release.

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
| **Sakura** | Ouka Kyaku 1400 (20), Haru Ichiban 3150 (35), Midare Zakura 3200/3250 (30/40) e Shun Goku Satsu 3300 (51) implementados em 05/11; arremesso frente+soco forte e complemento do Otoshi corrigidos em 05/11 |
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
- **SELECT/START na luta (05/11)** — durante o combate, SELECT agora
  executa o taunt e START abre a pausa, nos dois pads. O token `s` que o
  matcher usa para o comando `start` passou a ser gerado por SELECT; a
  pausa (`PauseOpen`) passou a testar START. Fora da luta (menus, select,
  command list) os botões continuam como antes; o START também continua
  confirmando a opção atual dentro da pausa. Para o Omega Rugal, os golpes
  `striker` e `tamtam` usavam START e agora ficam em QCF/QCB+SELECT, sem
  perder o acesso. O command list mostra `SELECT` na linha TAUNT.
  Regressão: `tools/test_fight_select_start_swap_headless.py`.
- **Pausa no select de personagens (05/11)** — START no pad de um lado
  humano abre um overlay com **CONTINUE** e **EXIT**. UP/DOWN move o
  cursor; START/A/X/Y confirma e B cancela. CONTINUE volta ao select;
  EXIT vai para a tela título. Em pads CPU, START continua fazendo
  join/reclaim daquele lado (preserva o fluxo de 2P e o mid-fight join).
  O menu usa o font 8x8 do select via OAM, sem trocar a tela; ao fechar,
  o OAM é limpo e o select redesenha.
  - **Textos centralizados (05/11):** PAUSE/CONTINUE/EXIT são posicionados
    por `SelPauseCenter` com `x = (256 - len*8)/2` (108/96/112) e o bloco
    fica em y=84/112/132, com centro vertical em 112 (metade de 224).
  - **Seletor amarelo (05/11):** a opção ativa usa o atributo OAM `$32`
    (prioridade 3, paleta OBJ 1 = amarelo do `MnObjPal`); a inativa fica
    em `$30` (branco). O cursor `>` também é amarelo e fica um glifo à
    esquerda da opção ativa (x=80 para CONTINUE, x=96 para EXIT).
  - Regressão: `tools/test_select_pause_headless.py` confere as posições
    centralizadas, a paleta amarela da opção ativa e o cursor.
- **Cursor P1/P2 no select (05/11)** — quando o P2 iniciava Single Play
  ou Team Play, o select acendia os dois anéis (`cpu1=0` e `cpu2=0`).
  Agora o P2 iniciado mantém `cpu2=0` (humano) e coloca `cpu1=1` (CPU) +
  `C_HUMAN_SIDE=1`: só o anel do P2 aparece. START do P1 no select
  junta o P1 sem derrubar o P2; o reclaim só vale quando foi o P1 que
  iniciou. No Team Play o CPU P1 escolhe o trio primeiro e depois o
  cursor do P2 fica ativo. Regressão:
  `tools/test_menu_p2_start_headless.py`.
- **Esquivas padrão (05/11)** — os comandos e estados continuam os
  mesmos; L+frente usa a animação 700 e L+trás a 710 (mapeamento original
  da fonte), sem troca adicional. O ActTab executava o `Turn` dos estados
  de rolagem sem a condição `P2Dist X < 0`, virando o lutador e
  invertendo a direção; essa linha foi removida só para os sids 94/95.
  L sozinho agora emite o token `c` e entra na regra `ESQ_L`/esquiva
  parada (sid 69), não mais no `start`/taunt. Vale para todos os
  personagens; Omega mantém o mapeamento explícito. Regressão:
  `tools/test_dodge_standard_headless.py`.
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
  (195). Todos os personagens usam L sozinho para a esquiva parada via
  token c/ESQ_L; o mapeamento explícito do Omega continua igual.
  Regressão: `tools/test_omega_dodge_headless.py`.
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
- **Arremessos — pose do alvo (revertido em 05/11)** — a tentativa
  genérica de usar o sprite de hold ancorado no torso (grupo 5011)
  deixou os oponentes baixos demais na tela. Revertida para o fallback
  anterior; o alinhamento fino será feito personagem por personagem.
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
  instrumento caiu de 128 para 35 (−11,3 dB no total; mais −2,9 dB em
  relação ao ajuste anterior). Bateria e lead não foram alterados.
  Padrões, ordem e `patternSha256` permanecem idênticos; só o `sha256` do
  `stg9.it` mudou. O render standalone com `smconv` confirma a redução a
  partir do trecho em que a guitarra entra.
- **RUMBLING (06/11)**: a guitarra `sawstab` do instrumento 0 também foi
  reduzida de 128 para 35 (−11,3 dB), o mesmo volume global da guitarra da
  SA YARD. Padrões, ordem e `patternSha256` do `stg4.it` continuam iguais;
  só o `sha256` do módulo mudou.

## Mature / Vice — agarrões especiais e supers (05/11)

Os comandos entravam no state raiz, mas o `p1stateno` que prende a vítima
e aplica o dano não estava ligado. Além disso, os comandos "strong" de
Mature/Vice apontavam para states de **vítima** ou para o próprio
follow-up, então o HitDef raiz nunca rodava. Correções:

- **Mature — Decide (HCF+B, 1200 -> 1201):** follow-up 1201 no sid 103.
  O `TargetLifeAdd` é uma expressão `ceil()*IfElse()` que o extrator não
  avalia; o port aplica 30 pontos no elemento 6.
- **Mature — Heaven's Gates (QCBHCF+A/B, 3000 -> 3001 -> 3004 -> 3005 ->
  3006):** 3001/3004/3005/3006 religados nos sids 104–107. O comando
  "strong" passou de 3010 (pose de vítima) para 3000. A vítima é solta no
  voo genérico (`S_VTHROW`) no elemento 3; o dano de 55 pontos é aplicado
  no elemento 4. Regra de transição 3004 -> 3005 religada.
- **Vice — Deicide Slayer (HCB+A/B, 1200/1250 -> 1210):** 1210 no sid 108,
  com `p2state=76`/`throw=1` (o HitDef é `S,SA` e o build antigo o tratava
  como golpe normal). Dano de 30 pontos em `Time=25`.
- **Vice — Black Out (DP+X/Y, 1400 -> 1410):** 1410 movido do sid 53 para
  o 109; a vítima 1420 foi mantida em `S_VHELD` (o mapeamento global de
  Iori a mandava direto para o voo) e os dois `TargetLifeAdd` valem 15
  cada (30 no total). O comando "strong" passou de 1410 para 1400.
- **Vice — Gore Fest (HCBF+X/Y, 1500 -> 1510):** 1510 movido do sid 55
  para o 110; o comando "strong" passou de 1510 para 1500. Os dois
  controladores de vida no mesmo elemento valem 18 cada (36 no total).
- **Vice — Negative Gain (HCBHCB+A/B, 3300/3400 -> 3310/3410):**
  follow-ups 3310/3410 nos sids 111/112. A expressão `Floor(...IfElse())`
  não é extraída; o port aplica 45 pontos no elemento 12.

Os valores de `TargetLifeAdd` acima de 127 estouravam o byte assinado do
ActTab e viravam cura (`-154` -> `+102`, `-304` -> `+48`); por isso os
valores foram reescalados para a barra de 200 HP e ficaram dentro de
−128..−1. `POST_CAL_MOVES_DROP` remove os sids antigos para o
`state_to_sid` first-wins resolver para os novos slots 103–112.

Vice mantém a forma clássica (com diagonais) **e** a forma curta de
`HCBF_X/Y` e `HCBHCB_A/B`. Com as diagonais amostradas, a regra curta de
QCB/HCB consumia o botão antes da motion longa terminar; `cmd_no_shortcut`
preserva as duas formas, então Gore Fest e Negative Gain saem tanto no
rolamento clássico quanto no atalho cardinal.

Regressão: `tools/test_mature_vice_grabs_headless.py` — 11 comandos
(Decide, Heaven's Gates A/B, Deicide A/B, Black Out X/Y, Gore Fest X/Y e
Negative Gain A/B). Cada caso confere o follow-up do atacante, a pose de
segurado (`sid 76`) e o dano mínimo: 31, 56, 56, 31, 31, 31, 31, 37, 37,
46 e 46.

## Sakura — arremesso, Otoshi, Shinkuu e Shun Goku Satsu (05/11)

- **Arremesso (frente + soco forte):** a regra `y` + `holdfwd`/`holdback`
  não existia no `Sakura_SNES.cmd`; só o `x+y` estava ligado. A regra foi
  adicionada (estado 800 -> 810) e o teste confirma o bind (sid 75) e a
  vítima em `S_VHELD`.
  - O CNS usa `BindToTarget`, que o motor nativo ainda não executa; a
    Sakura ficava ao lado do adversário em vez de esganá-lo. O estado 810
    ganhou um `TargetBind` de porta (`pos = 10,0`), então a vítima é
    re-semeada a 9 px do eixo da Sakura durante todo o choke. O teste mede
    o espaçamento (6..14 px) e falha se o bind sumir.
- **Sakura Otoshi (DP + a/b -> 1300/1310):** o complemento aéreo existia
  na origem (`x`/`y` durante a subida -> 1320), mas 1320/1321/1325 não
  estavam ligados. Foram para os sids 65/68/66. O TransTab kind-2 agora
  dispara de fato (antes caía no `TA_hit` e exigia MoveHit).
- **Shinkuu Hadouken (QCFx2 + soco):** os estados 3000/3010 (sids 85/86)
  não tinham projétil: o tiro real morava nos helpers 3005/3055, que não
  são estados de runtime no port.
  - **Arte do Ryu:** o Hadouken normal e o Shinkuu agora usam o atlas do
    projétil do Ryu (`PROJECTILE_FX_ALIAS["sakura"] = "ryu"`). O atlas
    alternativo antigo (cel de 64x54) estourava a página de efeitos e
    deixava tiles distorcidos no Shinkuu; ele foi removido. A ação 1021
    fica só como referência de origem.
  - **8 contatos:** `ProjTab[85/86/87] = 9 HP por contato` e o `ProjSpawn`
    dá 8 contatos aos supers da Sakura (85/86/87), em vez dos 5 genéricos:
    **8 x 9 = 72 HP**. A velocidade continua 12/14 px/tick (bem mais
    rápida que o Hadouken normal, 3/4) e o sequencial é "pinado" na vítima
    por `ProjPinIfMulti` (um contato a cada 4 ticks), como os demais
    supers multi-hit. O Raging Storm do Geese continua com um contato
    único e o hitbox alto.
- **Shun Goku Satsu (QCF + chute forte):** 3300 -> 3305 -> 3306 -> fim.
  O golpe estava no sid 111 (StAirSpec, aplicava gravidade) e o comando
  não existia para o chute forte; foi para o sid 114 (StSpecial) e ganhou
  `SGS_B` (QCF+b). O `SGS_A` (QCF+a) continua. O QCFx2+b continua sendo
  o Haru Ichiban 3100.
  - Os 15 contatos usam op19 (TargetLifeAdd + ComboBump) em tempos exatos
    de estado; o ActTab agora varre até 64 linhas de tempo (256 bytes).
  - A tela preta usa `CineApply` (TM = OBJ, CGRAM 0 preto) e
    `CineAdvance`; os lutadores são omitidos do OAM e só os sparks são
    desenhados. O fundo é restaurado ao fim.
  - O combo mostra 15; o 3306 aplica o golpe final com op3 (sem contar
    como 16º hit) e solta a vítima em S_VTHROW.
  - **Final de costas:** o taunt (sid 47) saiu. O sid 113 usa a ação
    sintética **3307**, que segura o primeiro cel do 3306 (sprite 3310,0)
    por 40 ticks. É a pose da Sakura de costas para a câmera, com o
    adversário caindo ao fundo. O teste exige estado 113, ausência do 47
    e `F_NFR = 1` (clip de um único cel).
- **Travamento do SGS após a tela preta (Practice):** reproduzido no
  emulador com Sakura x Billy no Practice (estado 113 da Sakura, vítima
  em 77). A causa é o **`CmdTrack`** — o log de comandos do Practice —
  sendo chamado no `EnterState` da **vítima** (TargetState 816 -> 77)
  dentro do finisher. Ele consulta a lista de comandos e trava o
  `EnterState` da vítima, congelando `framecnt`/a luta. O ROM anterior
  também travava; não era o staging MSU.
  - Correção: `CmdTrack` não registra vítimas de arremesso
    (`F_GRAB` bit0) e o índice de `CL_SEEN1/2` é limitado a 48 (as
    tabelas têm 48 bytes).
  - Aproveitei para corrigir um bug latente no `ApplyTimeActions`: o
    cursor `sptr` era perdido quando o op4 chamava `EnterState` na
    vítima; agora é salvo/restaurado em volta de cada `ActOp`.
  - O staging MSU ganhou uma correção separada (`SP_MSUOWN`): o vblank
    só consome o seek do lado que o posicionou e os chunks não
    consumidos são descartados. Isso evita CHR trocado/chunk cruzando a
    página de 8 KiB no SD2SNES, mas não era a causa deste travamento.
  - `VrDma`, `PushOamShadow` e `ShakeScroll` saíram do banco Fight para a
    seção `SakuraCinema` (chamadas `jsl`) para abrir espaço.
- Regressão: `tools/test_sakura_fixes_headless.py` (arremesso, choke,
  Shinkuu 72 HP em 8 contatos, Otoshi, SGS 15 hits, tela preta 50/0/47,
  final de costas e **SGS no Practice sem travamento**). O
  `test_ai_headless` fixa `rng`/`framecnt` depois do início da luta para
  a cobertura não depender do frame de boot.

## Juggle aéreo por projétil (05/11)

- **Queda no ar:** um oponente em `S_DOWN` com altura (`F_Y > 0`) deixou de
  ser pass-through para projéteis. O acerto entra em `S_HIT`, aplica o
  dano/pushback e, quando o hitstun acaba no ar, `PickJumpState` escolhe
  outra queda — ou seja, o tiro reinicia a queda e estende o combo.
  `S_DOWN` no chão continua sendo pass-through.
- **Limite por queda:** `F_AIRPROJ` (byte por lado, offset 181) marca que
  aquela queda já consumiu um projétil de **um contato**. Um segundo tiro
  de um contato atravessa sem dano. O flag zera quando o lutador toca o
  chão (`F_Y == 0`, verificado no `TickFighter`) e no início do round.
- **Exceção multi-hit:** no `ProjSpawn`, o sequencial de 5 contatos marca
  `SPK_ATTR` bit0. O `ProjHit` isenta esses tiros do limite — inclusive no
  último contato, quando `RT_PROJHITS` já está em 1. Assim o Shinkuu
  (5 x 14 = 70), o Ko'ou Ken e os demais supers multi-hit continuam
  acertando todos os contatos mesmo numa vítima no ar.
- Regressão: `tools/test_air_juggle_headless.py` (1º tiro acerta, 2º
  passa, super mantém 8 contatos, pousar libera o próximo tiro).
- `FaceEachOther` saiu do banco Fight para `SakuraCinema` (chamada `jsl`)
  para abrir espaço para a regra.

## Arremesso para trás estilo Street Fighter II (05/11)

- **Entrada:** segurar **para trás** + o botão de arremesso do personagem
  (soquinho forte; Ryu/Terry/Robert usam o x+y da origem). O motor registra
  a direção no grab (`F_TFLAGS` bit5) e vira os dois lutadores no mesmo
  instante: o atacante passa a encarar o lado oposto e a vítima é levada
  para trás dele.
- **Mesmo arremesso, espelhado:** os `TargetBind` são relativos à direção
  do atacante, então os offsets positivos da origem continuam valendo e a
  animação (e o dano) é a mesma, só que espelhada. No release a vítima
  recebe **3 px/tick** horizontais para longe do arremessador
  (`BackThrowReleaseFar`), em vez de cair no lugar.
- **Golpes de comando com bind zero:** alguns grabs (Chizuru) usam
  `TargetBind` dx=0 e movem o atacante. Se a vítima terminar no lado
  errado, `BackThrowReleaseFar` agenda a posição corrigida em
  `F_LASTSCAN` e `TickFighter` aplica dois ticks depois, quando o
  `ThrowBind` do atacante já não pode sobrescrever. O resultado é a vítima
  atrás do atacante, como nos demais.
- **Comandos fonte só com /F:** Yuri declara `THROW_Y = /F, y`; o gerador
  clona a regra com um comando `/B` equivalente (`#B`) para que
  para-trás + soco forte também entre no arremesso. Personagens com
  arremesso x+y continuam aceitando para-trás + x+y.
- **Turn autoral:** durante um back throw, `SelfTurnFar` ignora as linhas
  `Turn` do ActTab (a Chizuru tem uma no elemento 8), pois elas desfariam
  a virada feita no grab.
- Regressão: `tools/test_back_throw_headless.py` cobre Yuri, Iori, King,
  Benimaru, Ryu e Chizuru, nas duas direções e no espelho, conferindo
  lado, deslizamento, dano igual e limpeza do flag.

## Chizuru — antiaéreo, supers e botões (05/11)

- **QCB anti-aéreo (estados 1100/1102):** a subida do clone mantinha os
  holds de 30/15 ticks da origem, o `VelSet` condicional era extraído como
  zero e um `PosFreeze` (op13, Time=0) zerava VX/VY todo tick. O corpo
  ficava no chão por **216 ticks**. Agora usa o clipe rápido **13000** (o
  mesmo do DP), o op13 é descartado e a subida é fraca/forte:
  - fraco: `vy = -5.5` px/tick, pico ~32 px;
  - forte: `vy = -8.5` px/tick, pico ~78 px;
  - os dois terminam em ~60 ticks, como o Shoryuken fraco/forte do Ryu
    (~32/~87 px de pico).
- **DP (estado 1200):** `DP_Y` foi ligado ao mesmo estado; fraco (x) e
  forte (y) sobem/descem e recuperam. O `DP_X` continua igual.
- **Dance super (estado 2000):** o `VelSet` da origem virava zero e o
  `PinVXUnlessVelSet` anulava a caminhada. O ActTab agora aplica
  `vx = 1` px/tick (FlagsTab bit12), então ela **anda devagar** para a
  frente (~132 px no movimento). Os contatos usam `hit_resets` (reset
  duro do latch, sem o knockdown de 5º hit): **9 contatos / 60 HP** ao
  longo da janela de Clsn1 (frames 8–47), até o clipe terminar.
- **Crouched one-hand super (estado 2100):** quatro PosAdds
  (24+32+36+36) dão **~131 px** (~meia tela) e o golpe mantém 48 HP de
  dano. As PosAdds antigas da origem foram removidas para o orçamento
  bater.
- **Botões:** `DP_Y`, `RDP_Y`, `SUP3_Y` e o QCFx2+b foram adicionados.
  Ficou assim:
  - DP/RDP: x **e** y;
  - QCFx2 + x/a → dance (2000); QCFx2 + y/b → crouched (2100);
  - QCBx2 + x **e** y → MAX (2200).
  - QCF/QCB/HCB já tinham os dois botões.
- **Calibração:** `assets/calibration/chizuru.json` não tem correções
  (lista vazia); só os hashes de configuração e do `Chizuru_SNES.cmd`
  foram atualizados para o build não pular o personagem.
- Regressão: `tools/test_chizuru_fixes_headless.py` (QCB fraco/forte,
  DP/RDP x/y, dance com 9 hits e avanço, crouched ~128 px, supers com
  x/y/a/b), além dos testes `test_chizuru_dp_headless` e
  `test_chizuru_clones_headless`.

## Chizuru — HCB e input da dança (05/11)

- **HCB fraco (estado 1300):** o `VelSet x` condicional da origem era
  extraído como zero. O ActTab agora aplica `vx = 4` a partir do elemento
  10 (depois da extensão da mão) até o 20: ~54 px de avanço, mantendo os
  18 HP.
- **HCB forte (estado 1400):** o `VelSet` condicional virava zero e o
  clipe 1400 tinha um hold de **992 ticks** no ápice (255 no compilado),
  então ela ficava plantada. O hold foi cortado para 6 ticks, o Turn
  incondicional (op0) foi descartado e a subida (`vy = -6`) começa no
  frame ativo (11): o golpe acerta no chão (18 HP) e em seguida ela pula
  ~38 px.
- **Input da dança:** as janelas dos comandos `SUP1/SUP2/SUP3` e dos
  `MDFDF_*` passaram de 18 para **30 frames**, e os supers são testados
  antes do QCF simples (`cmd_priority`). Assim o QCFx2 + x/a vence o
  `1000/1004` e a dança sai com cadências de 2 a 4 frames por direção; um
  QCF simples + x continua sendo o especial normal.
- **Sugestões para facilitar ainda mais** (não aplicadas):
  1. atalho de **um QCF + a** (SNES B) direto para 2000;
  2. **QCF + x+y** para a dança (o source já usa x+y/c nos supers);
  3. aumentar o teto do matcher (`CmdScanCap`, hoje 30) ou usar
     `buffer.time` para aceitar motions de ~40 frames;
  4. manter o medidor em 1000+ (o super consome 1000).
- Regressão: `tools/test_chizuru_fixes_headless.py` agora mede o avanço
  do HCB fraco, o pulo do forte, a cadência lenta do QCFx2 e o fallback
  do QCF simples.

## Chin — DP, super e blowback (05/11)

- **DP fraco (estado 1450, sid 66):** o `ChangeState` de pouso para 1402
  não estava ligado porque 1402 não tinha slot. Agora 1402 usa o sid 53 e
  a transição `(66, 53, kind 1)` é emitida; o DP fraco pousa e volta ao
  neutro em ~51 ticks (antes ficava 283+ ticks na pose aérea).
- **DP forte (1400 -> 1401 -> 1402):** os três estados foram ligados aos
  sids 54/57/53. O comando `UPPER_S` usa o mesmo motion do DP fraco com o
  soco forte (`y`): F, D, DF + soco forte. O chain termina no pouso 1402.
- **Super Zake FireBall:** 1900/1910/1920 foram remapeados para os slots
  85/86/87, então entram no sequencial multi-hit de 5 contatos do motor;
  o dano por contato ficou 9/9/12 (45/45/60 HP no total) e o custo é
  1000 de power. O port desenha **um** projétil multi-hit porque o pool
  de sparks tem dois slots; o barrage de 14 projéteis da origem não cabe
  como 14 objetos, mas o número de golpes e o dano total estão completos.
- **Blowback (estado 900):** o bloco de guard-cancel
  (`prevstateno = [150,153]`: PalFX, PowerAdd -1000, EnvColor, Pause,
  AfterImage, Explod) era executado em todo CD porque o port não modela
  `prevstateno`. Ele foi removido da cópia SNES: o blowback não gasta
  mais 1000 de power nem escurece a tela como um super.
- O `UPPER STRONG` e os supers aparecem na lista de comandos do PRACTICE
  (sids 54, 85, 86 e 87).
- Regressão: `tools/test_chin_fixes_headless.py` cobre DP fraco/forte,
  supers fraco/forte e o CD sem flash/power.

## Lote de especiais, agarrões e hitboxes (06/11)

- **M. Bison — Head Press / Devil Reverse:** o `VelSet x = p2dist X/33`
  da origem era normalizado para zero. Agora os dois voam para o
  oponente: subida 2 px/tick, Head Press 4 px/tick, mergulho do Devil
  Reverse 3 px/tick, com a transição 1201→1205 cedo (2 frames) e um
  hitbox de mergulho largo/ativo desde o primeiro frame. Dano 18 no
  Devil Reverse e 30 no Head Press.
- **Chun-Li — Kikou Shou:** o super 3000 foi remapeado para o slot 85.
  O projétil usa o sequencial de 5 contatos do motor: **5 acertos,
  25 HP, derrubada**.
- **Geese — DP:** 1301/1311 (o HitDef real e o clip 1302/1312) foram
  ligados aos slots 55/56. O DP fraco/forte agora acerta e derruba.
- **Ken — Shoryureppa:** o HitDef de 3050 fica ativo durante o clip e os
  `MoveHitReset` de cada subida rearmam o golpe: **8 acertos, 45 HP**
  (o `MoveHitFinisher` continua limitando a 5 contatos quando aplicável).
- **Krauser — Kaiser Claw:** o override tinha transformado o grab em um
  golpe normal de 30. Restaurados `p1stateno 1701`, vítima em `S_VHELD`
  (1705→76) e o dano via `TargetLifeAdd`; agora ele agarra, dá 51 e
  derruba.
- **Ryu/Ken — golpes aéreos:** cada normal aéreo ganhou uma segunda
  caixa mais baixa no frame ativo (600/610/630/640), cobrindo melhor
  adversários agachados/caindo.
- **Arremesso padrão:** todos os 50 personagens com sid 74 agora aceitam
  **frente/trás + soco forte (y sozinho)**, mesmo quando a origem usava
  x+y ou um chute. A regra fica depois dos especiais/supers de motion,
  então QCF/DP terminando em frente+forte não são mais roubados.
- Testes de fumaça: Back throw, Chin fixes, Shoryuken five hits, AI,
  Super FX, VRAM, select pause, MSU CHR, FFG music, air juggle, Choi/Chris.

## Build de referência

`build/teamfix_benimaru_20261103/`

- checksum **`$65A7`**
- layout MSU **`0xD14F`**
- `.sfc` SHA-256 `1a27d89b…081b4943d`
- `.msu` SHA-256 `b7054f51…348e857fb4`
- `.msu` 52.149.760 bytes

## Referências

- `docs/GOLPES_FALTANTES_MUGEN_SNES_2026-10-24.md` — auditoria completa
  state a state.
- `docs/REATIVACAO_STATES_2026-11-02.md` — states religados e limites
  conhecidos.
- `docs/TEAM_DAIMON_STAGING_2026-11-03.md` — correções recentes do Team
  Play.
- `docs/COUNTER_BANNER_2026-11-03.md`, `docs/RALF_MOUNT_AI_FREEZE_2026-11-03.md`
  — correções recentes de HUD/IA/Ralf.
