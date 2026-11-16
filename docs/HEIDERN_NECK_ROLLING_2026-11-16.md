# Heidern: Neck Rolling, Final Bringer e auditoria dos especiais (16/11/2026)

## Sintoma

O **Neck Rolling** (`F, D, DF + chute`) era o golpe que deveria pular na
direção do adversário, mas o corpo ficava no chão: a animação do salto era
executada parada, o golpe só conectava colado e a recuperação ficava presa na
pose de pé. O mesmo defeito aparecia no **Final Bringer** (fraco/forte/MAX),
que também usa a animação de salto 1201.

## Causa

`tools/remaining_specials.py` achata as fases de um especial em um único
timeline nativo (`1200 + 1201`, `3010 + 3011`, `3050 + 3051`). O achatamento
preservava os sprites e as caixas, mas zerava o `VelSet y=-8` da fase 1201 e
trocava o hold de 255 ticks por um elemento curto. Resultado:

- o lutador nunca saía do chão (`selfy = 0`);
- a caixa de ataque só existia nos dois primeiros quadros do salto, então
  jump-ins altos passavam;
- o fraco Final Bringer (`3001`) mantinha o hold de 255 ticks sem velocidade e
  podia ficar ~4 segundos parado quando errava.

Além disso, o Moon Slasher (estados 1100/1110) avançava apenas 8 px: o
extrator lia `AnimElem = 5 || AnimElem = 6 || AnimElem = 7` como um único
elemento, embora o fonte avance 8 px em cada um dos três.

## Correção

- `remaining_specials.LUNGES` ganhou a opção `land`. Para Heidern:
  - `1200/1210` (Neck Rolling) saltam no elemento 2 do timeline achatado;
  - `3010/3050` (Final Bringer forte/MAX) saltam no elemento 3;
  - velocidade de subida `-4 px/tick` (quarter-px `-16`) e avanço de 2/3
    px/tick, com gravidade normal do motor;
  - o último elemento fica em 255 ticks para o corpo não voltar ao chão no
    meio do salto; a saída é a regra `kind 1` para `S_LAND` (sid 17).
- O fraco Final Bringer (`3001`, sid 103) recebeu o mesmo impulso via
  `_late_act` e já usava a regra de pouso `(103,17,1)`.
- A caixa de ataque do anim 1201 passou a cobrir os quatro quadros do salto
  (antes só 0/1), então o golpe conecta durante a subida.
- Moon Slasher: `posadd_override` repõe os três passos de 8 px (frames 4-6)
  nos estados 1100/1110.

## Verificação

- `python3 tools/build_fight.py`: OK.
- `python3 -m unittest tools.tests.test_heidern_leaps`: 4 testes OK.
- `python3 -m unittest tools.tests.test_antiair_landing_rows`: OK (nenhum
  salto com hold de 255 ticks sem regra de pouso).
- Headless (ROM/MSU deste build, Kyo parado; contagem desde o input):
  - Neck Rolling fraco: pico de ~16 px, caminho `52 -> 17 -> 0`, dano 22,
    44 frames;
  - Neck Rolling forte: pico de ~16 px, caminho `53 -> 17 -> 0`, dano 26,
    44 frames;
  - Final Bringer fraco: pico de ~16 px, caminho `85 -> 103 -> 17 -> 0`,
    dano 35, 97 frames (85 no whiff; a cadeia 104-107 não roda mais);
  - Final Bringer forte: caminho `86 -> 17 -> 0`, 51 frames, dano 38
    (MAX 48);
  - Moon Slasher: avanço de 24 px (fraco) e 18 px no forte por separação de
    corpo, dano 34/74.
- Build: `make -f Makefile.pvsnes verify` OK, checksum `$6BCF`.

## Ainda incompleto (auditoria dos especiais/supers)

| Golpe | Estado atual | Pendência |
|---|---|---|
| Heidern End 3100/3110/3150 | acerta e recupera (28/28/46) | falta a fase 3120/3125/3126 (e 3160/3161/3162 no MAX): o dano final e a cinemática de perfuração não estão ligados |
| Final Bringer 3000/3010/3050 | salto + 35/38/48 de dano | a cadeia 3020-3023 (agarrão/dreno) não segura a vítima; o `MoveHit 103->104` do fraco foi desligado para não gastar ~4 s sem dano |
| Storm Bringer 1300 | agarrão + 25 de dano | só pega a ~16 px; o fonte usa `p2bodydist X <= 29` e dreno em vários ticks |
| Killing Bringer 1400/1410 | contra-ataque + 32 de dano | OK no `test_counter_grab_headless` |
| Cross Cutter 1000/1010 | projétil 14/18 | OK |
| Moon Slasher 1100/1110 | acerta; 24 px de avanço | recuperação ainda longa (hold de 25/27 + 11 ticks do fonte) |
