# Auditoria Blue Mary — 2026-11-15

Status: **parcial, ainda sem build nem teste** das correções abaixo (pedido do
usuário: não compilar, só registrar para commitar depois).

## Medição (Snes9x headless, `audit_specials_headless.py`, distância 24)

Os 23 regras da Mary acertam e se recuperam. O avanço em x (dx) por golpe:

| Golpe | sid | dx medido | Situação |
|---|---|---|---|
| Super Dunk 3060 | 87 | 22 | ok |
| Goodnight 4000 | 88 | 101 | ok |
| Face lock 1900 | 49 | 14 | ok |
| Real Counter 1500 / 1520 | 50 / 51 | 47 / 39 | ok |
| Goodnight tentativa 1300 | 52 | 50 | ok |
| Vertical Arrow 1100 / 1110 | 54 / 55 | 25 / 33 | avança, mas não prende |
| **Spinfall 1150 / 1160** | 60 / 59 | **0** | corrigido (abaixo) |
| **Straight Slicer 1600 / 1610** | 112 / 113 | **0** | corrigido (abaixo) |
| Super Dunk 3000 / 30000 | 114 / 58 | 0 | pendente |
| Dynamite 3100 | 62 | 4 | pendente |
| Splash Rose 3300 / 3400 | 64 / 66 | 0 | pendente |
| Typhoon 3800 | 68 | 0 | pendente |

## Causa do Spinfall parado

`StSpecial` chama `PinVXUnlessVelSet`, que zera `F_VX` a cada tick a menos que
a FlagsTab tenha o bit12 (movimento por VelSet). A velocidade de entrada do
Spinfall (`EVelTab`: 6 e 3,5 px/tick) era aplicada no tick 0 e apagada no tick
seguinte, então Mary subia e descia no lugar (x constante, y em arco).

## Mudança feita (somente `tools/build_fight.py`, bloco `mary` pós-calibração)

- `POST_CAL_TWEAKS["mary"]["velset_sids"] = [59, 60]`: liga o bit12 no Spinfall.
- `POST_CAL_ACT_OVERRIDE["mary"]`: VelSet escalonado (op5) para o Straight
  Slicer, aproximando 7 px/tick + `VelMul .85` do MUGEN:
  - 1600: quadro 1 → 5, quadro 4 → 3, quadro 7 → 2, quadro 11 → 0
  - 1610: quadro 1 → 6, quadro 4 → 4, quadro 8 → 2, quadro 12 → 0

As mudanças ficam fora de `CHARS["mary"]` de propósito: editar `CHARS` muda o
hash da calibração e o build falha com `stale calibration configuration`.

Os hunks de Saisyu e Chang no mesmo arquivo não são desta auditoria.

## Para validar antes de commitar

1. `make -f Makefile.pvsnes verify`
2. `tools/test_mary_grab_headless.py`
3. `tools/audit_specials_headless.py <snap> --chars mary --confirm --out ...`:
   dx do Spinfall e do Slicer devem sair de 0, e as 23 regras seguem
   `hit_and_recovered`.
4. `tools/probe_framerate_headless.py` e builds MID/TINY.
5. Risco do Slicer: a 24 px o avanço pode passar pelo oponente antes do quadro
   ativo. Se a regra deixar de acertar, reduzir as velocidades.

## Pendências (agarrões incompletos, fonte em `mary-s.cns`)

Cada super é uma cadeia de estados que o port reduz a um único slice com um
golpe só:

- **Super Dunk 3000** (sid 114): `HitDef S,HT` com `p1stateno 3005` /
  `p2stateno 3010`; 3005 faz PosAdd 30+30+20 e TargetBind por elemento,
  `TargetLifeAdd -105` no elem 14, depois 3006 (`-160`) e o lançamento 3012.
  O port tem um golpe de 30 sem agarrão. O PosAdd de 12 px no elem 4 aparece
  duas vezes na fonte e uma só na tabela.
- **Dynamite 3100** (sid 62): 3100 → 3101 (pulo `vx 4,9 / vy -7,5`, atrito
  `.92`, HitDef 52x8) → 3103 → 3110/3111 (agarrão no ar, `-35`, queda 3112...).
  O port só tem o clipe 3100 com um PosAdd de 8.
- **Splash Rose 3300/3400** e **Typhoon 3800**: não foram lidos ainda.
- **Vertical Arrow 107/108**: sem linhas de bind; a fase aérea não prende.
- **Typhoon 111** (anim 1525): nunca alcançado nos testes manuais (precisa de
  power e do comando D,B,D,B + botão).
- `maryBind103/104/105`: slots de contra-ataque estilo Clark com dx grande
  (68, 64, -60).
- Defeito visual relatado (vítima metade no teto, metade abaixo do chão):
  **não reproduzido**. Suspeita: `DrawCellsPlain` em
  `src/engine/fast_paths.asm` força Y negativo a `$F0`. Precisa do golpe,
  oponente e fase do usuário.
