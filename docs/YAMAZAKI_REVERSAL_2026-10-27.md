# Reversal da linguada do Yamazaki (27/10/2026)

## O que foi verificado

O Sadomazo (弱/強サドマゾ, states 1100/1110) arma um `ReversalDef` com
`p1stateno = 1101`. No port:

- o state 1101 ganhou o slot runtime **103** (`REVERSAL_ACTOR_SLOTS`);
- a linha `yamazakiRev48`/`yamazakiRev49` do RevTab é
  `.db 8,103,7,255` (janela 8, ator 103, posturas S/C/A, sem vítima fixa —
  parry + contra-ataque);
- `RevCheck` → `HO_rev` coloca Yamazaki no 1101 e consome o golpe do
  oponente;
- o follow-up 1101 tem HitDef nos elementos 7–9, `fall = 1`, 26 de dano
  base (32 em counter hit).

Testes headless com Yamazaki nos dois lados (P1 e P2, virando a meia-lua
conforme a direção):

| Ataque do oponente | Reversal | Dano |
|---|---|---|
| normal em pé (x/a/b) | sim | 26 |
| normal forte com a vítima ainda atacando | sim | 32 (counter hit) |
| normal agachado | sim | 26 |
| jump-in | sim | 26 |
| especial direto (DP) | sim | pode whiffar se o golpe for invencível |
| projétil | não | — |
| arremesso | não | — |

O whiff em especiais invencíveis/cross-ups é coerente com o original: o
ReversalDef só tem `p1stateno`, então a vítima não é presa num estado
customizado; o 1101 é um golpe normal e pode errar. Projéteis usam o
`ProjHit` separado e `reversal.attr = SCA,AA` não inclui `P`; arremessos
passam pelo caminho de throw antes do `RevCheck`.

## Bug corrigido: counter hit tirava só 1 de dano

Quando a vítima ainda estava na animação de ataque (counter hit), o
follow-up 1101 acertava por apenas **1** de dano. A causa:

1. `HitModifiers` detecta o counter hit e chama `CounterDraw` (texto
   "COUNTER" no HUD).
2. `CounterDraw` chama `WriteStr`, que usava `scr4` como contador do laço.
3. `scr4` é exatamente o offset `estado_do_atacante * 2` que o caminho de
   dano usa logo depois para indexar `DamageTab`, `ShakeTab`, `PauseTab` e
   `HTTimeTab`.
4. `WriteStr` deixava `scr4 = 7` (tamanho da string "COUNTER"), a leitura
   caía no meio da tabela, dava 0 e o motor elevava para 1.

A correção faz o `WriteStr` usar `scr0` como contador: esse scratch já está
morto depois que o offset do HUD é copiado para `X`. `scr4` fica intacto.
Isso conserta **qualquer counter hit do jogo**, não só o reversal do
Yamazaki. O banco `Fight` ainda ficou 1 byte menor.

## Validação

- Novo `tools/test_yamazaki_reversal_headless.py`: P2 forte contra counter
  hit (32 de dano), P1 fraco (26) e jump-in (26), todos PASS.
- `test_counter_grab_headless.py`, `test_guard_cancel_headless.py`,
  `test_ai_headless.py`, `test_choi_throw_headless.py`,
  `test_command_list_headless.py` e
  `test_msu_chr_visibility_headless.py`: PASS.
- `python3 -m unittest discover -s tools/tests`: 178 testes OK.
- Build PVSnesLib + `make verify`: OK.

## Hashes

- ROM `kof98-snes.sfc`: checksum **`$7CA2`**, SHA-256
  `abb3afb7…221c263`.
- MSU `kof98-snes.msu`: SHA-256 `3e8945c3…868de386` (inalterado).
