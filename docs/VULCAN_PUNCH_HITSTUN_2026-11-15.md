# Vulcan Punch de Ralf e Clark — hitstun com pushback (2026-11-15)

## Problema

Os states 400/401 (Ralf) e 1000/1010 (Clark) usavam `hit_soft_resets` e o
`MoveHitFinisher` do motor forçava knockdown no quinto contato. O HitDef
também estava com `gvx = gvy = 0`, então a vítima ficava presa no lugar e o
golpe terminava como um launcher, não como a rajada do arcade.

## Correção

- Os resets passaram de `hit_soft_resets` para `hit_resets` (op18 arg 0).
  O contador de golpes é zerado em cada janela, então o `MoveHitFinisher`
  nunca converte o quinto contato em queda.
- `hitdef_override` mantém `fall = 0` e `gvy = 0`: a vítima no chão
  permanece em pé, em hitstun, recebendo os contatos.
- O pushback horizontal ficou em 2 px/tick para Ralf e Clark. A fonte usa
  3 px/tick (Ralf) e 4,5 px/tick (Clark), mas o caminho nativo aplica a
  velocidade cheia até o fim da janela de slide; 2 px/tick preserva todos
  os contatos e ainda empurra a vítima de forma visível.
- `avx`/`avy` continuam com os valores da fonte (`-3,-8` no Ralf e
  `-4,5,-6,5` no Clark). Uma vítima já no ar usa essa rampa e pode sofrer
  juggle; a vítima no chão nunca é lançada automaticamente.

## Medição (Snes9x headless)

Distância de 24/40/60 px, Kyo no chão:

| Personagem | Contatos | Dano | Pushback | States da vítima |
|---|---|---|---|---|
| Ralf (48/49) | 5 / 5 / 4 | 19 / 19 / 16 | 72 / 72 / 60 px | `0 -> 9 -> 0` |
| Clark (49) | 5 / 5 / 5 | 29 / 29 / 29 | 66 / 66 / 62 px | `0 -> 9 -> 0` |
| Clark (48) | 5 / 5 / 4 | 29 / 29 / 24 | 80 / 72 / 62 px | `0 -> 9 -> 0` |

`9` é o state de hitstun (`S_HIT`). Em nenhum caso a vítima entrou em
`S_DOWN` nem saiu do chão (`Y = 0`). O state 1010 tem dez janelas de
HitDef na fonte; o port mantém as cinco primeiras, como antes, para não
dobrar o dano quando o knockdown forçado deixou de existir.

Com a vítima suspensa a 4 px do chão, os dois personagens continuam
acertando (Ralf 2–4 contatos, Clark 1–3), confirmando o ramo aéreo. O
número de contatos aéreos depende da altura e da caixa de colisão, como
no arcade; o que importa é que o golpe não converte a vítima no chão em
launcher.

## Testes

- `tools/tests/test_vulcan_punch.py`: garante `fall` limpo, `gvy = 0`,
  pushback horizontal e resets rígidos (arg 0) nas quatro linhas.
- `tools/test_vulcan_punch_headless.py`: valida no emulador 4+ contatos,
  hitstun, 40+ px de pushback e ausência de knockdown para vítima no chão;
  confirma também que a vítima no ar ainda recebe contatos.

Build de verificação: `verify pvsnes: OK` na árvore principal (checksum
`$8B1C` no build de 15/11 17:02) e também em worktree limpo em `HEAD`.
