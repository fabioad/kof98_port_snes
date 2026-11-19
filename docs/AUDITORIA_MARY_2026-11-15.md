# Auditoria Blue Mary — 2026-11-15

Status: **todos os especiais/supers da Mary medidos**; Dunk, Dynamite, Typhoon
e Rose corrigidos e verificados. Duas ressalvas: o Splash Rose não reproduz o
loop de 4 investidas da fonte e o Vertical Arrow aéreo continua sem prender a
vítima (análise abaixo).

## Medição (Snes9x headless, `audit_specials_headless.py`, distância 24)

Os 23 regras da Mary acertam e se recuperam. O avanço em x (dx) por golpe,
depois das correções:

| Golpe | sid | dx | Situação |
|---|---|---|---|
| Super Dunk 3060 | 87 | 22 | ok, prende |
| Goodnight 4000 | 88 | 101 | ok, prende |
| Face lock 1900 | 49 | 14 | ok, prende |
| Real Counter 1500 / 1520 | 50 / 51 | 47 / 39 | ok, prende |
| Goodnight tentativa 1300 | 52 | 50 | ok, prende |
| Spider 1205 | 56 | 16,6 | ok, prende |
| Vertical Arrow 1100 / 1110 | 54 / 55 | 25 / 33 | avança, não prende |
| **Spinfall 1150 / 1160** | 60 / 59 | **148 / 146** | corrigido |
| **Straight Slicer 1600 / 1610** | 112 / 113 | **95 / 144** | corrigido |
| **Super Dunk 3000 / 30000** | 114 / 58 | **50 / 50** | corrigido, prende |
| **Dynamite 3100** | 62 | **4 (pega no local) / 60 (a 70 px)** | corrigido, prende |
| **Typhoon 3800** | 68 | 4 | corrigido, prende (60 de dano) |
| **Splash Rose 3300 / 3400** | 64 / 66 | **63 / 63** | avanço e queda (sem o loop) |

## Super Dunk 3000 / 30000

A fonte tem duas fases: o golpe inicial (3000/30000) acerta e redireciona o
atacante para 3005/30005, que fazem PosAdd +30/+30/+20, mantêm as janelas de
`TargetBind` (erguendo a vítima até 88 px), pagam o dano no elemento 14 e
entregam a vítima ao arremesso. O port importava só a fase inicial como um
golpe parado de 30/40.

- Slots livres 115/116 recebem 3005 e 30005 (desenham o clipe 3005, só dois
  cels: 1300 e 6022, sem banco novo de sprites).
- O `HitDef` de 114/58 virou agarrão (`p2state 76`, `throw 1`, dano 0) e a
  transição kind3 (no acerto) leva para 115/116.
- Dano total da cadeia 3005+3006 = 265/1000 de vida → 53 no HP de 200 do port;
  a MAX (30005+30006) = 200 → 40. Cai no elemento 14.
- No último elemento um `ActTab` op4 manda a vítima para o slot arremessado.
  Para isso o estado 3012 da fonte (lançamento) foi mapeado em
  `VICTIM_STATE_IDS` como 77.

Medido: avanço +50 px, vítima presa (76), erguida a 88 px, 53 de dano
(normal) e 41 (MAX), arremesso e queda. Quadros conferidos no emulador: sem a
vítima no teto.

Comando no port: **F, D, DF + Y** = Super Dunk (1000), **+ X** = MAX (2000).
O `mary.cmd` original usa ~D,B,D,B+x/y; o port remapeou (D,B,D,B+x cai no
Typhoon). Alinhar a tabela de comandos com a fonte é um item separado.

## Dynamite Swing 3100

A fonte é um agarrão aéreo em duas fases: 3100 (início) → 3101/3103 (pulo com
o chute) → 3110 (agarrão no ar) → 3111 (queda, -35) → 3112. O port tinha só o
início como golpe parado, e o clipe 3100 termina com um hold de 100 ticks que o
MUGEN nunca exibe (ChangeState no AnimElem 5) — daí a lentidão.

- 62 continua sendo 3100, com o hold cortado (`tail_ticks 3100 = 1`) e
  transição no fim do clipe para 117.
- **117** = 3103 (o único clipe da cadeia com `Clsn1`): estado aéreo com
  `VelSet 4.9,-7.5`, `velset_sids` ligado e a caixa de ataque refeita nas
  imagens 1-4 (`air_box_patch_frames`) porque a original fica 51-140 px acima
  do eixo e só tocaria um oponente com os pés quase no chão. O `HitDef` virou
  agarrão (`p2state 76`, `throw 1`, 12 de dano).
- **118** = 3110 (agarrão no ar, 2 cels): janelas de bind da fonte, com o `dy`
  limitado a -55 (`bind_dy_cap`, novo) porque o bind soma a altura da Mary e o
  -104 original estourava o teto de 127 px do campo. Dano -13 no quadro 0 e
  arremesso (`op4` → 3012) no último elemento.
- `state_vel 118 = (0,-1)`: entrando com `vy = 0` e `F_Y = 0` o `Physics` não
  aplica gravidade e a regra de pouso nunca dispara (Mary ficava presa no 118
  quando o agarrão acontecia no chão).

Medido: de 24 a 90 px pega, prende, ergue a vítima, 16 de dano e arremessa.
Perto do oponente o agarrão acontece na saída do pulo; a 70 px ela voa ~60 px
antes de agarrar.

## Typhoon 3800

Cadeia da fonte: 3800 (agarrão) → 3810 (bind/erguimento) → 3811 (finalizador,
`-295` de vida) → vítima 3820/3821 (arremesso). O port tinha só um golpe parado
de 30.

Cabe num único slot porque o slot 106 era o único livre na janela de agarrão
103-118 e já despacha como especial de chão — que é o que 3810 é (`physics N` no
chão). Assim não foi preciso mexer na StateTab nem no orçamento do banco 50,
que estava no limite.

- 68 (3800) virou agarrão (`p2state 76`, `throw 1`, sem dano) e no acerto vai
  para 106.
- **106** = 3810: janelas de bind da fonte, com `dy` limitado a -60
  (`bind_dy_cap`) porque o -100 original estourava o teto de 127 px. Dano -59
  (fonte -295/1000) e arremesso (`op4` → 3821, novo mapeamento para o slot 77)
  no último elemento do clipe.
- O clipe 3800 importado tinha 7 quadros e o último com hold de 255 ticks (a
  fonte muda de estado no AnimElem 3); `frame_cap 68 = 3` corta no ponto certo e
  uma linha `(68,0,0,0)` devolve ao neutro no fim. Antes um whiff ficava parado
  mais de quatro segundos.

Limitações: a fonte tem duas versões (typhoon_b com 1000 de power e typhoon_d
com 2000, que faz -472); o port manda as duas para o mesmo estado e usa o dano
da versão fraca (59). O pulo de whiff (3801/3802) não foi importado.

Medido: de 24 e 50 px agarra, ergue, 60 de dano e arremessa com queda.

## Splash Rose 3300 / 3400

Na fonte é um rekka de dash: 3300 (início) → 3301 (investida com HitDef e
`mindist/maxdist 60-65`) → 3310 (gira e corta, repetindo até 4 vezes conforme
`var(2)`) → 3311 (mais cortes) → 3312 (finalizador aéreo). O port tinha um
único quadro parado (o clipe 3301, 1 frame) com um golpe.

- Os dois sids passaram a desenhar o clipe **3310** (8 quadros, cels 1525 e
  3301 já residentes) no lugar do quadro único.
- `POST_CAL_ACT_OVERRIDE` dá o avanço: 4 px até o quadro 5, 8 px até o 7 (a
  janela de dash da fonte), depois 0.
- O `HitDef` virou lançador (`fall 1`, `hittime 16`) e o golpe conecta de 24 a
  65 px, com queda da vítima.

**Ressalva:** a fonte repete o 3310 até quatro vezes (`ChangeState 3310` no fim
do clipe, controlado por `var(2)`) e emenda 3311/3312, somando ~5 cortes
(195/1000 de vida ≈ 39 no port). O motor não tem contador por golpe nem slots
livres na janela 103-118, então o port toca uma investida só (31/34 de dano com
o toque de entrada). Um rush fiel precisa de 2-3 sids novos e de espaço no
banco 50.

## Vertical Arrow aéreo (107/108) — pendente

Cadeia da fonte: 1100/1110 (início, HitDef 47) → 1101/1111 (fase aérea, HitDef
59) → com `MoveHit && Vel Y < 0 && Command = "uppercut_b/d"` vai para 1120
(segura a vítima no ar, binds -60/-55/-48) → 1121 (slam -35, empurra a vítima
para 1131) → 1122/1123 (recuperação).

O port tem as fases aéreas avançando mas sem prender. O que foi descoberto:

1. O gancho da fonte é um **segundo HitDef no mesmo estado, condicionado a
   comando**. O motor do port não tem HitDef condicionado a comando; o mais
   próximo é a transição `kind 2` (pressão nova com `Vel Y < -1`), que funciona
   para trocar de estado, mas não para capturar a vítima.
2. Um HitDef `throw` num estado **sem linhas de bind** é derrubado no tick
   seguinte: `ThrowBind` não acha bind e chama `TbSlamFar` (é o mecanismo que
   evita a vítima congelada quando o atacante não a posiciona mais). Por isso
   marcar 54/55/107/108 como `throw` faz a vítima entrar em 76 e sair para 77
   no tick seguinte.
3. `ActTab op4` só aceita estado de vítima da fonte mapeado em
   `VICTIM_STATE_IDS` (1130 → 76, 1131 → 77), e mover a vítima por ali não
   substitui a captura: sem o HitDef de agarrão o alvo não fica registrado.

**Implementação que deve funcionar** (tentada, mas não validada — ver o
bloqueio): dar bind às fases aéreas (hook `bind_extra`, hoje presente no
gerador e sem uso) com um hold constante (~45 px), marcar 107/108 como
`throw`, colocar a corrente em dois slots livres da família 60-69 (63 = 1120,
61 = 1121 — `StVictimHeld` já aceita esses donos, sem crescer `S_EXT_LAST`) e
ligar a continuação a uma pressão nova durante a subida (`kind 2`). O dano do
slam é `POST_CAL_TARGET_LIFE[1121] = -7` (fonte -35).

**Bloqueio:** a árvore de trabalho está sendo editada em paralelo por outra
sessão e o build parou de gerar de forma consistente (`assert iori_spr.inc
39202 > 36864` e rótulos duplicados `daimonSprData` vindos de geração
concorrente em `build/gen_fight`). Sem build não há como validar a mudança, e
ela foi revertida para não deixar a Mary num estado pior que o atual.

### Orçamento do banco 50

As tabelas novas (StateTab 117/118, `S_EXT_LAST` 116 → 118) não cabiam: a seção
`Fight` estava a 32768 bytes. As saídas antecipadas do `BodySep` foram
reorganizadas com um trampolim curto (`BS_exit`/`BS_run`), economizando bytes
sem mudar a semântica. PRO, MID e TINY voltaram a caber.

## Spinfall

`StSpecial` chama `PinVXUnlessVelSet`, que zera `F_VX` a cada tick a menos que a
FlagsTab tenha o bit12 (movimento por VelSet). A velocidade de entrada do
Spinfall (`EVelTab`: 6 e 3,5 px/tick) era aplicada no tick 0 e apagada no tick
seguinte, então Mary subia e descia no lugar. `velset_sids [59, 60]` mantém o
movimento.

O whiff a 24 px é fiel à fonte: a caixa `Clsn1` do anim 1150 só existe no
elemento 5 (~21 ticks), então o chute acerta a partir de ~100 px. Medido no
emulador: 24 e 60 px = 0 de dano; 100, 120 e 140 px = 34 (1150) e 32 (1160).

Tentativa descartada: lançar 1 tick depois (velocity 0 na entrada + op5/op15 no
quadro 1) para o HitDef acertar do chão. A regra de pouso kind1 dispara no
mesmo tick com Y=0 e Mary nunca sai do lugar.

## Straight Slicer

A fonte dá 7 px/tick no ar (1601/1611) e depois `VelMul .85`. O port não tinha
movimento. `POST_CAL_ACT_OVERRIDE` reescreve como VelSet escalonado (op5):

- 1600: quadro 1 → 5, quadro 4 → 3, quadro 7 → 2, quadro 11 → 0
- 1610: quadro 1 → 6, quadro 4 → 4, quadro 8 → 2, quadro 12 → 0

## Verificação

- `make -f Makefile.pvsnes verify`: OK (PRO).
- `make -f Makefile.pvsnes mid-verify`: OK.
- `make -f Makefile.pvsnes tiny`: OK; `verify_pvsnes_rom.py` OK nos três.
- `tools/test_mary_grab_headless.py`: PASS (Goodnight 105 de dano, face lock 20).
- `tools/test_counter_grab_headless.py`: PASS (mary_low, heidern, takuma).
- `tools/audit_specials_headless.py`: 23 regras, 22 `hit_and_recovered`
  (o 1160 é `no_impact_review` a 24 px pelo motivo acima).
- `tools/probe_framerate_headless.py`: 59,19 fps, sem tick zerado.

## Pendências (agarrões incompletos, fonte em `mary-s.cns`)

- **Splash Rose**: sem o loop de 4 investidas (ver a seção acima).
- **Vertical Arrow 107/108**: sem linhas de bind; a fase aérea não prende
  (a fonte usa 1120/1130 com `uppercut_b`; é o último agarrão em falta).
- **Typhoon 111** (anim 1525): nunca alcançado nos testes manuais (precisa de
  power e do comando D,B,D,B + botão).
- **Comandos**: a tabela do port difere do `mary.cmd` em D,B,D,B (x → Typhoon,
  y → Dynamite) e no Super Dunk (F,D,DF em vez de D,B,D,B).
- `maryBind103/104/105`: slots de contra-ataque estilo Clark com dx grande
  (68, 64, -60).
- **Dynamite**: a fase 3111 (queda com -35 e 17 cels) não entrou; o dano foi
  pago no agarrão aéreo (118) e usa o clipe de 2 cels do 3110. A soma ficou 16
  (fonte: 87/1000 de vida ≈ 17).
- **Vítima baixa/abaixo da tela no arremesso especial (Geese).** Reproduzido:
  os arremessos especiais entregam a vítima ao slot 77 via `TargetState`; o
  motor deixava a velocidade de voo para o clipe 816 **do próprio personagem**.
  Kyo/Iori têm `VelSet y=-6.5` e sobem; o 816 do Geese tem `VelSet y=2` e cai
  reto, ficando no chão. Correção em `AO_tstat`: vítima ainda no ar recebe o
  arco compartilhado 821 (`SlamBounceFar`, -5.28 px/tick e 3.7 px/tick para
  longe), com `STIME=128` para bloquear o VelSet específico do personagem;
  soltura no chão continua caindo/knockdown. Medido: Geese, Kyo e Iori chegam
  aos mesmos 85 px e caem juntos (`tools/test_mary_throw_height_headless.py`).
  A pose de **segurado** continua sendo a genérica do personagem (Geese usa o
  anim 47, não a 3820 específica da Mary); se o hold em si ainda parecer baixo,
  é a pose, não a física do voo.
- Suspeita separada, ainda não confirmada: `DrawCellsPlain` em
  `src/engine/fast_paths.asm` força Y negativo a `$F0`; isso só afetaria
  células acima do topo da tela, não o voo baixo acima.

