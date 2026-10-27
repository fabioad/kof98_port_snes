# Altura do adversário em arremessos e guard cancel (27/10/2026)

## Sintoma

Em alguns personagens, o adversário subia demais na tela durante o
arremesso (corpo segurado) e na queda; em vários casos o sprite entrava
no HUD ou saía pelo topo. O mesmo acontecia com a vítima do guard cancel
X+A, que era lançada alta demais.

## Causa

- O `TargetBind` da CNS usa a altura do palco MUGEN (240 px). O port tem
  só **190 px acima do chão** (`GROUND_Y=190`). Binds com `y` entre -100 e
  -130 deixavam o adversário com os pés em y=60..90 e a cabeça fora da
  tela.
- O guard cancel X+A entra no sid 67. Dependendo do personagem, o estado
  mapeado nesse sid é um launcher com `air.velocity` vertical de até
  -8 px/tick, o que também levanta demais a vítima.

## Correção

Tudo no gerador (`tools/build_fight.py`), sem alterar o motor:

1. **`TargetBind`**: o `y` é limitado a **-80 px** antes de virar linha do
   `BindTab`. Arremessos baixos não mudam; os que seguravam o adversário
   acima de 80 px passam a segurar em 80 px.
2. **Guard cancel (sid 67)**: o `gvy`/`avy` do `HitVelTab` é limitado a
   **-6.5 px/tick** (8.8: -1664). Com a gravidade 0.44 do motor, o pico
   fica em torno de 48 px, em vez de 60–70+.

Nada mais do arremesso/golpe muda: dano, timing, invencibilidade,
velocidade horizontal e comandos continuam iguais.

## Validação

- Novo `tools/tests/test_throw_height_rows.py`:
  - nenhum `BindTab` com lift > 80 px;
  - nenhum `HitVelTab` do sid 67 com `gvy`/`avy` abaixo de -6.5 px/tick.
- Auditoria headless (arremesso + guard cancel) nos personagens altos:
  - arremessos que agarram: pico **75–79 px** (antes 100–130);
  - guard cancel: pico **37–44 px** nos launchers (antes 59–68).
- `test_choi_throw_headless.py`, `test_guard_cancel_headless.py`,
  `test_ai_headless.py`, `test_kyokugen_projectile_anim_headless.py`,
  `test_msu_chr_visibility_headless.py` e `test_hud_bands_headless.py`:
  PASS.
- `python3 -m unittest discover -s tools/tests`: OK.
- Build PVSnesLib + `make verify`: OK.

## Hashes

- ROM `kof98-snes.sfc`: checksum **`$D550`**, SHA-256
  `1e1da4b7…df5fea4`.
- MSU `kof98-snes.msu`: SHA-256 `3e8945c3…868de386` (inalterado).
