# Arremessos normais de todos os personagens (27/10/2026)

## Auditoria

Testei os 50 personagens no emulador com cinco variantes de entrada
(x+y, y+frente, y+trás, b+frente, b+trás), a curta distância, esperando a
vítima entrar no estado 76 (`S_VHELD`). Antes da correção, 14 personagens
não agarravam: Saisyu, Heidern, Takuma, Clark, Ralf, Leona, Mature, Vice,
Benimaru, Daimon, Chin, Billy, Athena (em uma rodada) e outros.

## Causas

### 1. Gate de distância do comando de throw

O `CmdTab` guarda no byte de proximidade o bit7 (vítima agarrável) e a
distância máxima. Para personagens cuja CNS não tem `p2bodydist`, o
gerador emitia `distância = 0` com o bit7 ligado (`128`). O motor lia
"vítima agarrável e distância ≤ 0", então o comando só casaria com os dois
corpos exatamente sobrepostos — na prática, o arremesso nunca disparava.

A correção preserva o bit7 e troca a distância por **40 px**:

```python
if r["state"] == 74 and (r["dist"] & 0x7F) == 0:
    r["dist"] = (r["dist"] & 0x80) | 40
```

Isso consertou Saisyu, Heidern, Takuma, Clark, Ralf, Leona, Mature, Vice,
Benimaru, Daimon e os demais que usam `y` + direção.

### 2. Chin e Billy sem comando válido

- **Chin**: o `[State -1, Throw]` apontava para o estado 900 (um super,
  não um arremesso). O `wire_throw_chain` agora prefere, no fallback, uma
  linha de throw que tenha `p1stateno`/bind real e animação no AIR
  (Chin 850 → bind 860), em vez da primeira linha (810, que é só o bind).
- **Billy**: tem os estados 3000/3001/3020/3021, mas o `_SNES.cmd` não
  tinha `[State -1, Throw]`. O gerador agora sintetiza a regra padrão
  **x+y** a curta distância quando o sid 74 existe e nenhuma regra o
  cobre. A entrada também foi adicionada ao `display_defs`, então a
  PRACTICE Command List mostra `X+Y` em vez de `?`.

O resto do arremesso (animação, dano, bind, timing) não mudou.

## Validação

- Auditoria headless dos **50 personagens**: todos com arremesso normal
  OK (34 por `x+y`, 16 por `y` + direção). Chin e Billy agora agarram.
- `test_choi_throw_headless.py`, `test_guard_cancel_headless.py`,
  `test_ai_headless.py`, `test_kyokugen_projectile_anim_headless.py`,
  `test_msu_chr_visibility_headless.py`,
  `test_command_list_headless.py` e os testes de tabelas: PASS.
- `python3 -m unittest discover -s tools/tests`: 177 testes OK.
- Build PVSnesLib + `make verify`: OK.

## Hashes

- ROM `kof98-snes.sfc`: checksum **`$7CA2`**, SHA-256
  `abb3afb7…221c263`.
- MSU `kof98-snes.msu`: SHA-256 `3e8945c3…868de386` (inalterado).
