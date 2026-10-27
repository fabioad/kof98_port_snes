# Projétil do Andy com a animação da Yuri (27/10/2026)

## Pedido

O Hishou Ken do Andy deve usar a mesma animação do Ko'ou Ken da Yuri.

## O que foi feito

`tools/calibration/projectiles.py`, em `PROJECTILE_FX_ALIAS`:

```python
"andy": "yuri",   # antes: "kyo"
```

O alias já existente faz o gerador:

- pular a compilação do atlas próprio do Andy (`andyProjFxTab/Chr`);
- apontar o descritor do Andy (`CharAndy`, campo `CH_PROJFXTAB/CH_PROJFXCHR`)
  para `yuriProjFxTab`/`yuriProjFxChr`.

O resultado é o mesmo conjunto de **seis cels** do Ko'ou Ken da Yuri, com
a paleta e o tamanho nativos dela. O resto do Hishou Ken (comando QCF+c,
estado 1150, sid 58, velocidade, dano e altura de spawn no chão) continua
igual.

## Validação

- `tools/test_kyokugen_projectile_anim_headless.py`, agora com Andy
  (`sid 58`, QCF+c): frames `[0,1,2,3,4,5]` desenhados, mesmos 14/12/9/8/7/13
  cells da Yuri. PASS.
- `test_yuri_projectile_anim_headless.py`, flip, mirror, AI e os 174
  testes unitários: PASS.
- Build PVSnesLib + `make verify`: OK.

## Hashes

- ROM `kof98-snes.sfc`: checksum **`$E05F`**, SHA-256
  `61ce51a9…da99e3e`.
- MSU `kof98-snes.msu`: SHA-256 `3e8945c3…868de386` (inalterado).
