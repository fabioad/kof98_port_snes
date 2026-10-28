# Projétil da Yuri 2x maior (27/10/2026)

## O que mudou

O Ko'ou Ken da Yuri estava sendo compilado em **48x80** (frame 0), bem menor
que o projétil do Kyo (80x96). O pedido era deixá-lo cerca de **2x maior**,
mais ou menos do tamanho do Kyo.

- `PROJECTILE_RESIZE["yuri"] = (3, 2)` aumenta o efeito em **1,5x linear**
  (~2,25x em área) antes de montar as células.
- O compilador normal redimensionaria o atlas de volta para 16 células e
  devolveria o tamanho antigo. Por isso o caminho da sequência da Yuri usa
  um **quantizador por frame**: mantém a geometria ampliada e reduz o atlas
  para as 16 células 16x16 mais frequentes, mapeando as demais para a célula
  mais próxima. O custo de página/CHR continua o mesmo (16 células/frame).

Tamanhos gerados:

| Frame | Antes | Depois |
|---|---|---|
| 0 | 48x80 | **64x128** |
| 1 | 48x80 | **64x112** |
| 2 | 48x64 | **80x96** (igual ao frame 0 do Kyo) |
| 3 | 48x48 | **80x80** |
| 4 | 48x48 | **80x64** |
| 5 | 48x48 | **64x64** |

O frame 0 tem área 2,13x a antiga; o frame 2 tem exatamente a caixa 80x96
do projétil do Kyo. A captura headless mostra a chama ocupando quase toda
a altura do personagem, em vez do risco pequeno anterior.

## Escopo e custo

- O **hitbox, dano, velocidade e tempo** não mudaram: só o desenho.
- O atlas de cada frame continua com no máximo 16 células únicas; a página
  de 2 KiB/frame e o total de 12 KiB do Ko'ou Ken não cresceram.
- O número de células desenhadas sobe de 13 para no máximo 27 no frame 0;
  o teste de OAM confirma que todos os seis frames continuam sendo
  desenhados (27/25/26/21/16/11 células).
- Ryo, Robert, Takuma e o Hishou Ken de trás do Andy compartilham o clipe
  da Yuri, então também passam a usar o efeito maior.

## Validação

- `test_kyokugen_projectile_anim_headless.py`: os seis frames e as células
  OAM de Yuri, Ryo, Robert, Takuma e Andy: PASS.
- Novo teste unitário `test_yuri_kouken_is_enlarged_to_kyo_size`: resize,
  bbox 64x128/80x96 e limite de 16 células por frame.
- Captura headless do frame 1: projétil visível e grande em frente à Yuri.
- **181 testes unitários** e demais testes headless: PASS.
- Build PVSnesLib + `make verify`: OK.

## Hashes

- ROM `kof98-snes.sfc`: checksum **`$D092`**, SHA-256
  `1231375f…e45a1a27`.
- MSU `kof98-snes.msu`: SHA-256 `3e8945c3…868de386` (inalterado).
