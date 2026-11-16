# Mr. Big — projétil sem "chuviscos" e comandos de chute (15/11/2026)

## Sintoma

Ao desferir o Ground Blaster / Blaster Wave apareciam **chuviscos** (pontos
coloridos) dentro da bola branca do projétil.  No controle, o baixo, baixo
frente, frente (`QCF`) só respondia ao chute fraco, e os supers só aceitavam
os botões de soco.

## Causa

1. **Projétil.** O Mr. Big estava em `PROJECTILE_FX_ALIAS` apontando para o
   atlas do **Heavy D** (comentário `# beam`).  Aquele raio é uma arte larga
   e listrada; ao ser reduzido para a página de 16 células do efeito, as
   frestas transparentes entre as listras viravam pixels vazados.  O fundo do
   cenário (calça, madeira, árvore) aparecia através delas — os "chuviscos".
2. **Comandos.** O `Mrbig_SNES.cmd` gerado só tinha `QCF + a` (chute fraco)
   para o Crazy Drum.  `QCF + b` (chute forte) caía no chute normal em pé, e
   os supers `QCFx2` / `QCF,HCB` só tinham as variantes `x`/`y` (socos).

## Correção

- Removida a entrada `"mrbig": "heavyd"` de `PROJECTILE_FX_ALIAS`.  O gerador
  volta a compilar a ação 1020 do próprio Mr. Big (grupo 1002), a onda de
  fogo do Ground Blaster, que é a arte correta da fonte.  O atlas resultante
  tem duas poses (faísca + chama) e cabe na página de efeito.
- Novos comandos em `tools/build_fight.py` (`cmd_extra` do Mr. Big):
  - `QCF + b` → Crazy Drum (1100), igual ao chute fraco;
  - `QCFx2 + a` → Blaster Wave fraca (3000);
  - `QCF,HCB + a` → Bou Dotsuki Spinning fraca (3200);
  - `QCFx2 + x+a` → MAX Blaster Wave (3050) com os dois botões fracos;
  - `QCF,HCB + x+a` → MAX Bou Dotsuki Spinning (3250).
- O Rising Spear (`DP`) já aceitava o chute fraco; a lista de comandos agora
  mostra `DP + B/A` (o `DP + Y` é a California Romance e continua intacto).
- `cmd_text` mostra os dois botões aceitos (`QCF+B/A`, `QCFX2+Y/B`, …) em vez
  de exibir só a última regra que ordenou na tabela.

A ordenação por tamanho do movimento garante que os supers de 7/8 elementos
sejam testados antes dos especiais de 4 elementos que compartilham a cauda
(`QCF`, `HCB`, `DP`).

## Validação

- `python3 -m pytest tools/tests/test_projectile_calibration.py` — inclui o
  novo caso que exige o atlas próprio do Mr. Big e a ausência do alias.
- `python3 -m pytest tools/tests/test_command_list.py` — as linhas novas
  mostram os dois botões aceitos e continuam cabendo nos 11 caracteres.
- `python3 tools/test_category_d_batch2_headless.py` — **45 golpes PASS**,
  incluindo os novos: `1100 Crazy Drum S` (QCF + chute forte),
  `3000 Blaster Wave WK` (QCFx2 + chute fraco),
  `3050 MAX Blaster Wave WK` (QCFx2 + soco fraco + chute fraco),
  `3200 Bou Dotsuki Spin WK` (QCF,HCB + chute fraco) e
  `3250 ... MAX WK`.
- `python3 tools/test_mrbig_california_headless.py` — PASS nas versões fraca
  e forte (25/26 de dano, quatro contatos).
- Captura headless: o projétil agora desenha a chama laranja/branca da fonte
  (frames 0 e 8 da ação 1020), sem os pontos coloridos do feixe do Heavy D.

## Build

- ROM `kof98-snes.sfc`: checksum **`$1FCA`**,
  SHA-256 `47dfaf6e…d4b73647`.
- MSU `kof98-snes.msu`: SHA-256 `86300514…9568e881`.
- Copie ROM e MSU juntos.

