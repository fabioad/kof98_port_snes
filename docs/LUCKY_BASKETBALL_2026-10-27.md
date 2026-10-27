# Bola de basquete do Lucky (27/10/2026)

## O que o original faz

O SHOOT do Lucky não é um projétil horizontal. No CNS importado:

- `2100` é o arremesso em fadeaway: Lucky sobe (`velset = 0,-7`) e, no
  `animelem = 4`, cria o helper da bola;
- `2102` / `2107` dão à bola um deslocamento curto para frente
  (`velset = 5,-10`, depois `10,0` + aceleração `x = 2`), sem HitDef;
- `2103` zera a velocidade horizontal (`velset = 0,0`), aplica gravidade
  (`y = .45`) e é a **única fase com HitDef**: a bola cai quase na vertical
  cerca de 60 px à frente do Lucky;
- ao tocar o chão, `2104`/`2105`/`2108`/`2112` fazem três quiques para trás
  (`x = -2`, `y = -5`, `-4`, `-2`). Esses quiques são cosméticos, sem
  HitDef.

A versão anterior do port lançava a bola em linha reta, a 4 px/tick e na
altura do torso, como um fireball. Por isso o trajeto não batia.

## Como ficou

O perfil balístico fica no cabeçalho do `ProjFxTab` (offsets 5–7), gerado a
partir de `PROJECTILE_BALLISTIC["lucky"]`:

- altura de spawn: **200 px acima do chão** (a bola nasce logo acima da
  tela e entra por cima);
- gravidade: **7/16 px/tick²** (~0,4375);
- deriva: **7 px/tick durante 7 ticks** e depois `VX = 0`;
- dano: **22** (109 na escala de 100 HP do original).

Na prática, a bola nasce cerca de 63 px à frente do Lucky, aparece no topo
da tela e cai na vertical. O teste headless mede 42 px de deriva visível
(a amostra começa um tick depois do spawn) e um alcance de ~49 px. Se
acertar, causa 22 de dano e desaparece; se errar, quica três vezes para
trás e some.

## Implementação no motor

- `ProjBallisticSetup` e `SparkGravity` vivem no espaço livre do banco 126
  (`$D100`), chamados com `jsl`; o banco Fight está cheio.
- `ProjBallisticSetup` lê o perfil do `ProjFxTab` e inicializa o byte de
  padding do spark com `(ticks de deriva << 4) | gravidade`.
- `SparkGravity` substitui o bloco inline de gravidade: explods continuam
  usando `SPK_AY`; projéteis comuns não têm gravidade; a bola balística usa
  a gravidade do padding, para o `VX` no tick configurado e faz os quiques.
- O contador de quiques usa os bits 1–2 de `SPK_ATTR`; depois do primeiro
  toque no chão o HitDef é ignorado, como no original.
- Bug encontrado no caminho: a checagem de "bola quicando" usava
  `and #$000E.w` numa leitura de 16 bits em `SPK_ATTR`, o que trazia o byte
  vizinho (`SPK_BANK`) para os bits 1–2 e **descartava todo projétil**. A
  máscara agora é de 8 bits (`#$0E.b`).

## Validação

- Novo `tools/test_lucky_basketball_headless.py`:
  - P1 acerta a vítima no ponto de queda: **22 de dano**;
  - P1 erra: a bola cai, quica para trás e não cruza a tela;
  - P2 (virado para a esquerda): queda e quique espelhados, 22 de dano.
- `test_projectile_calibration`: perfil balístico, `ProjTab` e
  `ProjFxTab` gerados como esperado.
- Demais testes headless e **179 testes unitários**: PASS.
- Build PVSnesLib + `make verify`: OK.

## Hashes

- ROM `kof98-snes.sfc`: checksum **`$7CA2`**, SHA-256
  `abb3afb7…221c263`.
- MSU `kof98-snes.msu`: SHA-256 `3e8945c3…868de386` (inalterado).
