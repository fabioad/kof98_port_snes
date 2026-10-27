# Remoção das sombras (AfterImage) de todos os personagens (27/10/2026)

## Pedido

Remover as sombras das esquivas e dos demais golpes de todos os
personagens que ainda as exibiam.

## O que foi feito

O gerador convertia cada controlador `AfterImage` da CNS em uma ação
`op9` (liga o rastro de ghost).  Antes só quatro estados eram filtrados
(dash 100, esquivas 250/251 e roll 710); os rolls 700/720 e os especiais/
supers de quase todos os personagens continuavam com sombra.

`tools/build_fight.py` agora remove **todas** as linhas `op9` de todos os
estados, para todos os personagens:

```python
for state in cns_acts:
    cns_acts[state] = [row for row in cns_acts[state] if row[1] != 9]
```

Com isso o `AfterImage` da CNS não chega ao `ActTab`; o motor não liga
`F_TFLAGS` bit2 e `GhostTick`/`DrawGhost` não encontram nenhum slot ativo.
Não há mais sombra em esquiva, rolamento, especial ou super de nenhum
personagem.  O resto dos golpes (animação, dano, invencibilidade,
velocidade) não muda.

## Validação

- Novo `tools/tests/test_afterimage_rows.py`: varre os `*_spr.inc` de
  todos os personagens jogáveis e falha se encontrar qualquer linha
  `.db ...,9,1,0` (op9).  PASS.
- `test_ai_headless.py`, `test_guard_cancel_headless.py`,
  `test_kyokugen_projectile_anim_headless.py` (Andy incluso),
  `test_msu_chr_visibility_headless.py` e `test_hud_bands_headless.py`:
  PASS.
- `python3 -m unittest discover -s tools/tests`: OK.
- Build PVSnesLib + `make verify`: OK.

## Hashes

- ROM `kof98-snes.sfc`: checksum **`$C33F`**, SHA-256
  `4dd2ed86…71edf80`.
- MSU `kof98-snes.msu`: SHA-256 `3e8945c3…868de386` (inalterado).
