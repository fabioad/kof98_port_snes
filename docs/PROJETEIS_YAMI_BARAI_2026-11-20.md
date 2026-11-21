# Projéteis do Yami Barai (Kyo, Saisyu e Iori)

## Problema

O clipe de projétil do Kyo/Iori/Saisyu saía do SFF de origem como uma chama
esparsa de dois quadros: o primeiro com 15 células e o último com 3. Como o
motor alterna entre eles, o 108 Shiki aparecia como um piscar minúsculo no
chão — bem diferente da labareda larga do arcade.

## Solução

O projétil agora é importado do rip do arcade
(`assets/fx/kyo98-projectile.gif`, frames 7 a 15) em vez de ser compilado do
SFF:

- cada quadro é recortado a partir de uma borda esquerda própria (o GIF mostra
  o Kyo inteiro; só a chama que viaja é mantida);
- os dois primeiros quadros também cortam o topo, onde ainda aparecem as
  faíscas que saem da mão;
- o recorte é reduzido para 90% (o elenco usa 0,81) e quantizado na rampa de
  cores que o `spark_pal.bin` compilou;
- a grade de células de 16 px tem a fase escolhida por quadro, o que mantém a
  chama larga dentro das 16 células da página de efeitos (máximo de 15).

A rampa é resolvida em tempo de build contra a paleta OBJ compartilhada
(CGADD 160), então o fogo acompanha a paleta em vez de fixar índices:

- Kyo/Saisyu: amarelo-claro → laranja-claro → laranja → vermelho → sombra;
- Iori: branco-quente → lilás → roxo → roxo-escuro (referência KOF XV).

Saisyu continua usando o clipe do Kyo por `PROJECTILE_FX_ALIAS`. O Iori voltou
a ter projétil viajante: as linhas 48/49 do `ProjTab` voltaram em
`PROJECTILE_CALIBRATION` e a conversão melee (HitDef de corpo + caixas de ar)
foi removida.

## Verificação

- `test_iori_yami_projectile_headless.py`: fraco 14 / forte 18, o tiro viaja e
  acerta.
- `test_projectile_render.py`: todas as 9 células por quadro, nas duas
  orientações, com os tiles de VRAM batendo byte a byte com a ROM.
- `test_mesen_hud_flicker.lua` (Kyo × Iori atacando, 900 quadros):
  `late_unblank=0`, `visible_blank=0`.
