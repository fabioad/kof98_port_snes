# Projétil do Kyo, Saisyu e Iori com a arte do Yami Barai (18/11/2026)

## Pedido

Trocar o projétil do **Kyo** e do **Saisyu** pela chama do Yami Barai do GIF
de referência e dar ao **Iori** a mesma chama em roxo, usando no máximo
**2 quadros** e reduzindo o que fosse necessário para caber no orçamento.

Fontes:

- animação (18 quadros): `108_Shiki_Yami_Barai_Kyo_'98.gif` (SNK Wiki);
- referência de cor: `Iori_Yamibarai_XV.png` (SNK Wiki).

As duas URL do `static.wikia.nocookie.net` só respondem com um `User-Agent`
de navegador; o download foi feito assim e as imagens **não** ficam no
repositório (só o recorte final).

## Arte

`tools/extract_yamibarai_art.py` recorta a chama do GIF (o corpo do Kyo fica
fora do recorte), gera os PNGs e cria a versão púrpura do Iori por
*histogram matching* da luminância da chama sobre a rampa de roxos tirada da
imagem do Iori XV.  Saída em `assets/projectiles/`:

| Arquivo | Tamanho | Uso |
|---|---:|---|
| `kyo_yamibarai_a.png` | 81x36 | 1º quadro (estalo pequeno) |
| `kyo_yamibarai_b.png` | 97x75 | 2º quadro (erupção alta) |
| `iori_yamibarai_a.png` | 81x36 | igual, em roxo |
| `iori_yamibarai_b.png` | 97x75 | igual, em roxo |

Os dois quadros são **consecutivos no GIF** (12 e 13), então a alternância
pequeno/alto é o próprio tremular da fonte.  O clipe de 2 quadros fica em
loop enquanto o projétil vive e termina no quadro alto, que é o que fica na
tela na maior parte do voo.

Para regerar:

```sh
python3 -I tools/extract_yamibarai_art.py CAMINHO/kyo98.gif CAMINHO/iori.png
```

## Integração no build

`tools/calibration/projectiles.py`, em `PROJECTILE_EXTERNAL_ART`:

```python
"kyo":    (4, ("kyo_yamibarai_a.png", "kyo_yamibarai_b.png")),
"saisyu": (4, ("kyo_yamibarai_a.png", "kyo_yamibarai_b.png")),
"iori":   (4, ("iori_yamibarai_a.png", "iori_yamibarai_b.png")),
```

`tools/build_fight.py` (`projectile_effect_external`) compila o PNG em vez do
SFF do personagem:

- **escala comum** aos dois quadros, procurada em passos de 1/16 a partir de
  1x — fica a maior em que os dois cabem na página de 16 células 16x16;
- grade de 16x16 deslocada para o encaixe que deixa **menos células**
  não vazias;
- no máximo **duas páginas de 2 KiB** por lutador (uma por quadro);
- arte apoiada no chão (`y = 0`) e centrada em x, como as chamas que ela
  substitui.

Resultado do build (perfil PRO): **13/16** de escala, quadro A com **9
células** (66x29) e quadro B com **15 células** (79x61) — o mesmo teto do
projétil antigo (15 células no quadro grande).  Um PNG novo ou editado
também regenera as tabelas: as imagens entraram nas dependências do
`Makefile.pvsnes`.

### Paleta

Impactos e projéteis dividem a paleta 2 (15 cores).  A chama púrpura do Iori
precisava de mais de um tom e o *median cut* do elenco só lhe dava um, o que
deixava o fogo branco com pontinhos azuis.  Por isso:

- as cores exatas dos PNGs entram no histograma (Kyo com peso 8, Iori 12);
- `PROJECTILE_PALETTE_PINS` garante o roxo escuro e o lavanda
  (`74,36,120` e `214,186,245`); quando falta o tom, ele toma o lugar da cor
  **menos usada** do histograma (o violeta médio já existia).

O Saisyu também alimenta o histograma com a arte do Kyo, mas continua usando
o atlas do Kyo pelo alias — não gasta tabela própria.

### Quem mais é afetado

`PROJECTILE_FX_ALIAS` já apontava **Saisyu**, **Shingo**, **Yamazaki**, e os
dois Kyo EX (`kyonests`/`kyoash`) para o clipe do Kyo — cinco descritores usam
`kyoProjFxTab/kyoProjFxChr`.  Todos passam a desenhar a chama nova sem gastar
outra página de CHR (Saisyu era o pedido; os outros eram atalhos já
documentados).

## Validação

```sh
python3 tools/test_yamibarai_projectile_headless.py
python3 tools/audit_projectile_release.py kyo iori saisyu
python3 tools/test_yuri_projectile_anim_headless.py    # paleta compartilhada
```

Saída do teste novo (ROM de 18/11):

```
PASS weak: frames [0, 1], cells {0: 9, 1: 15}, orange pixels 344->367
PASS strong: frames [0, 1], cells {0: 18, 1: 18}, orange pixels 312->440
PASS kyo Yami Barai: two-frame orange burst
PASS weak: frames [0, 1], cells {0: 9, 1: 15}, violet pixels 0->176
PASS strong: frames [0, 1], cells {0: 9, 1: 15}, violet pixels 0->180
PASS iori Yami Barai: two-frame violet burst
```

O teste confere no emulador que os **dois** quadros do clipe chegam à tela
como células OAM de paleta 2 (≥8 células em cada) e que o vídeo ganha pixels
laranja (Kyo) ou violeta (Iori).  `test_yuri_projectile_anim_headless`
continua passando: o clipe da Yuri não perdeu cor nem células com a paleta
nova.

Build: `make -f Makefile.pvsnes verify` OK.

- ROM `kof98-snes.sfc`: checksum **`$4457`**, SHA-256
  `aea22edd0ac2…` (8 388 608 B, 32,31% livre).
- MSU `kof98-snes.msu`: SHA-256 `a5e4ea29…`.

## Regressões conhecidas (anteriores a esta mudança)

- `test_yuki_kusanagi_headless.py` falha em "shot was hidden": o
  `yukiProjTab` já estava zerado antes desta alteração (o snapshot da árvore
  anterior a este trabalho tem a mesma tabela vazia).
- `test_reflect_headless.py` para em `opening: gs=14` porque não avança o
  vídeo MSU da abertura.
- `test_projectile_render.py` compara a prioridade OAM esperada (`0x04`) com
  a que o motor atual escreve (`0x34`, mesma paleta 2); as tabelas geradas
  aqui só carregam deslocamento e tile, então o teste não é afetado por este
  trabalho.
