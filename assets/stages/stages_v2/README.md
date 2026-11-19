# Stages KOF98 — reconstrução a partir do arcade (v2)

Estes são agora os **stages ativos do build**. O pipeline
(`tools/build_stages.py`) lê esta pasta: os PNGs estáticos entram no
`StageTab`, e o par `anim/*.json` + `anim/*.pool.chr` gera os descritores e o
pool de animação de cada cenário, carregado por `StagePick`
(`StgAnimPoolTab`). A pasta é gerada por `tools/stage_v2/` (reprodução no fim
deste arquivo).

## O que há aqui

| Caminho | Conteúdo |
| --- | --- |
| `KOF98-*.png` | Arte estática 512×224, PNG indexado, 3 paletas × 15 cores, ≤ 512 tiles. **Mesmo formato** que `tools/build_stages.py` já lê. |
| `anim/KOF98-*.json` | Clips de animação do arcade: células do mapa, palavras de tilemap por estado, sequência com tempos em ticks (60/s). |
| `anim/KOF98-*.pool.chr` | Tiles 4bpp do pool dinâmico do cenário (32 bytes/tile). |
| `anim/KOF98-*.movers.json` + `movers/*.png` | Elementos que **se deslocam** (aves, gato, vaga-lumes…): poses reduzidas + movimento original. Não entram nos clips. |
| `preview/*_compare.png` | Em cima: arcade reduzido sem limite de cores. Meio: arte SNES **atual** do repositório. Embaixo: v2. |
| `preview/*.gif` | Esquerda: arcade rodando (inclui o que a v2 ainda não anima). Direita: v2 com os clips aplicados. |
| `preview/contact_snes.png`, `contact_arcade.png` | Folhas de contato dos 10 cenários. |
| `metrics.json` | Métricas por cenário. |

## Método

1. **Fonte = arcade.** `tools/stage_v2/mugen_bg.py` renderiza os `.def`/`.sff`
   MUGEN dos stages (camadas, ações de animação, `BGCtrl`, paralaxe) tick a
   tick. A rua japonesa reproduz o composto original com erro 0 pixel. A arte
   redesenhada que servia de fonte antes (`hires/`) não é usada.
2. **Mesma geometria do port.** Mundo de 752 px do arcade → 512 px
   (escala horizontal 512/752, vertical 1:1); o chão do arcade cai na linha 190
   (`GROUND_Y` de `fight.asm`). A China usa o convés ligado à `[BG Dummy]`
   (y = 208). As 12 linhas que faltam abaixo do arcade (240) são espelhadas.
3. **Redução suave.** Lanczos em luz linear (sem serrilhado) + filtro bilateral
   em OKLab, que apaga ruído de textura (gasta tiles e cores) mas mantém
   contornos.
4. **Paletas por área.** 3 × 15 cores em RGB555: k-means ponderado em OKLab,
   com tiles agrupados por cor média, desvio e posição vertical, e peso menor
   sob o HUD. Os pixels das poses animadas também entram no desenho das
   paletas, para que os clips não precisem de cores fora delas.
5. **Orçamento de 512 tiles.** K-medoids discreto (cada tile é um tile real,
   com flips H/V e escolha de paleta por posição), com termo de média por
   bloco 4×4. Células animadas entram na arte estática já com a **pose 0
   exata** do clip e saem da disputa por tiles estáticos: sem salto na
   primeira troca.
6. **Animação do arcade, não oscilação.** Para cada camada animada fixa mede-se
   que células 8×8 realmente mudam. Camadas que se tocam formam um grupo que
   percorre os estados conjuntos reais, com os tempos do `.def`. Cada estado
   vira tiles nas paletas do cenário. Orçamento: 160 tiles de pool **por
   cenário**; excedente é resolvido por fusão de tiles parecidos e poda das
   células de menor energia visual. Grupos com mais de 4 camadas ficam com as
   4 de maior energia; mais de 6 estados são reduzidos a 6 por k-medoids.

## Resultados

Erros em OKLab contra a fonte do arcade já reduzida à mesma geometria.
"Só paleta" é o limite sem orçamento de tiles (cada pixel na cor mais próxima
das 45): mostra quanto do erro vem do limite de 512 tiles.

| Cenário | Tiles estáticos | Tiles de pool | Clips | RMSE pixel | RMSE borrado | Só paleta (borrado) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| China | 512 | 160 | 1 | 0.070 | 0.027 | 0.017 |
| Rua japonesa | 511 | 160 | 7 | 0.080 | 0.033 | 0.021 |
| Templo japonês | 512 | 160 | 5 | 0.056 | 0.023 | 0.013 |
| Coreia | 511 | 156 | 3 | 0.092 | 0.037 | 0.024 |
| Bazar (Oriente Médio) | 512 | 160 | 3 | 0.083 | 0.033 | 0.020 |
| Rugal | 511 | 160 | 1 | 0.063 | 0.021 | 0.010 |
| Espanha | 463 | 141 | 1 | 0.048 | 0.016 | 0.012 |
| Porto | 507 | 160 | 3 | 0.053 | 0.024 | 0.018 |
| Porto B (vermelho) | 506 | 160 | 3 | 0.054 | 0.024 | 0.017 |
| Pátio ferroviário | 511 | 160 | 3 | 0.094 | 0.032 | 0.017 |

Total de tiles de pool somados: 1577. Cada cenário usa no máximo 160.

### Animações extraídas do arcade

| Cenário | Camadas do arcade | Células | Tiles | Estados | Ciclo |
| --- | --- | ---: | ---: | ---: | ---: |
| China | BG 15 (ação 15) | 43 | 160 | 6 | 3.68 s |
| Rua japonesa | BG 5 (ação 5) | 8 | 25 | 4 | 0.60 s |
| Rua japonesa | BG 10 (ação 10) | 15 | 47 | 4 | 0.60 s |
| Rua japonesa | BG 15 (ação 15) | 1 | 5 | 6 | 11.08 s |
| Rua japonesa | BG 20 (ação 20) | 3 | 5 | 6 | 1.20 s |
| Rua japonesa | BG 25 (ação 25), BG 30 (ação 30), BG 45 (ação 45) | 25 | 59 | 6 | 13.20 s |
| Rua japonesa | BG 35 (ação 35) | 3 | 8 | 6 | 0.80 s |
| Rua japonesa | BG 40 (ação 40) | 3 | 11 | 6 | 0.80 s |
| Templo japonês | BG 10 (ação 10), BG 25 (ação 25), BG 30 (ação 30), BG 35 (ação 35) | 130 | 139 | 6 | 0.80 s |
| Templo japonês | BG 15 (ação 15) | 1 | 4 | 6 | 0.67 s |
| Templo japonês | BG 15 (ação 15) | 2 | 3 | 6 | 0.67 s |
| Templo japonês | BG 15 (ação 15) | 1 | 2 | 6 | 0.67 s |
| Templo japonês | BG 40 (ação 40) | 4 | 12 | 4 | 0.40 s |
| Templo japonês | ~~BG 5~~ — fora do orcamento/estados | – | – | – | – |
| Templo japonês | ~~BG 15~~ — sem mudanca visivel | – | – | – | – |
| Templo japonês | ~~BG 15~~ — fora do orcamento/estados | – | – | – | – |
| Coreia | BG 5 (ação 5), BG 10 (ação 10), BG 25 (ação 25) | 44 | 120 | 6 | 1.20 s |
| Coreia | BG 15 (ação 15) | 22 | 30 | 6 | 3.20 s |
| Coreia | BG 35 (ação 35) | 2 | 6 | 6 | 26.30 s |
| Bazar (Oriente Médio) | BG 15 (ação 15) | 15 | 45 | 6 | 1.33 s |
| Bazar (Oriente Médio) | BG 20 (ação 20) | 18 | 61 | 6 | 1.33 s |
| Bazar (Oriente Médio) | BG 25 (ação 25), BG 30 (ação 30) | 30 | 54 | 6 | 1.33 s |
| Rugal | BG 5 (ação 5), BG 20 (ação 20), BG 30 (ação 30), BG 40 (ação 40) | 180 | 160 | 6 | 1.07 s |
| Rugal | ~~BG 10~~ — fora do orcamento/estados | – | – | – | – |
| Rugal | ~~BG 15~~ — fora do orcamento/estados | – | – | – | – |
| Rugal | ~~BG 25~~ — fora do orcamento/estados | – | – | – | – |
| Rugal | ~~BG 35~~ — sem mudanca visivel | – | – | – | – |
| Espanha | BG 10 (ação 10) | 33 | 141 | 6 | 0.67 s |
| Porto | BG 5 (ação 5), BG 10 (ação 10), BG 25 (ação 25), BG 30 (ação 30) | 281 | 158 | 6 | 4.80 s |
| Porto | BG 20 (ação 20) | 3 | 1 | 4 | 0.60 s |
| Porto | BG 35 (ação 35) | 4 | 1 | 4 | 0.60 s |
| Porto | ~~BG 40~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | BG 10 (ação 10), BG 60 (ação 60), BG 70 (ação 70), BG 75 (ação 75) | 535 | 136 | 6 | 16.80 s |
| Porto B (vermelho) | BG 25 (ação 25), BG 60 (ação 60) | 73 | 21 | 6 | 2.40 s |
| Porto B (vermelho) | BG 60 (ação 60) | 11 | 3 | 6 | 0.27 s |
| Porto B (vermelho) | ~~BG 5~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 15~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 15~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 15~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 15~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 30~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 35~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 40~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 50~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 55~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 60~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 60~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 60~~ — fora do orcamento/estados | – | – | – | – |
| Porto B (vermelho) | ~~BG 60~~ — fora do orcamento/estados | – | – | – | – |
| Pátio ferroviário | BG 10 (ação 10) | 29 | 82 | 6 | 1.20 s |
| Pátio ferroviário | BG 15 (ação 15) | 21 | 66 | 4 | 2.00 s |
| Pátio ferroviário | BG 20 (ação 20) | 8 | 12 | 6 | 1.20 s |

### Elementos em deslocamento (fora dos clips)

| Cenário | Camada | Poses | Folha |
| --- | --- | ---: | --- |
| Templo japonês | BG 15 | 5 | `movers/KOF98-JpnTempleStage_bg8.png` |
| Templo japonês | BG 15 | 5 | `movers/KOF98-JpnTempleStage_bg9.png` |
| Templo japonês | BG 15 | 5 | `movers/KOF98-JpnTempleStage_bg10.png` |
| Templo japonês | BG 15 | 5 | `movers/KOF98-JpnTempleStage_bg11.png` |
| Templo japonês | BG 15 | 5 | `movers/KOF98-JpnTempleStage_bg12.png` |
| Templo japonês | BG 15 | 5 | `movers/KOF98-JpnTempleStage_bg13.png` |
| Templo japonês | BG 15 | 5 | `movers/KOF98-JpnTempleStage_bg14.png` |
| Coreia | BG 40 | 3 | `movers/KOF98-KoreaStage_bg8.png` |
| Coreia | BG 45 | 3 | `movers/KOF98-KoreaStage_bg9.png` |
| Coreia | BG 50 | 4 | `movers/KOF98-KoreaStage_bg10.png` |
| Coreia | BG 55 | 4 | `movers/KOF98-KoreaStage_bg11.png` |
| Espanha | BG 20 | 154 | `movers/KOF98-SpainStage_bg4.png` |
| Porto | BG 45 | 24 | `movers/KOF98-USAWharfStage_bg9.png` |
| Porto B (vermelho) | BG 45 | 24 | `movers/KOF98-USAWharfStage-B_bg12.png` |
| Pátio ferroviário | BG 25 | 10 | `movers/KOF98-USAYardStage_bg5.png` |
| Pátio ferroviário | BG 26 | 10 | `movers/KOF98-USAYardStage_bg6.png` |

## Limites e pendências (leia antes de julgar)

* **Arte e integração validadas no emulador.** `verify_v2.py` passa cada PNG
  por `emit_stage` (conversor real do jogo), decodifica CHR/mapa/CGRAM como o
  PPU e compara com o PNG, e reconstrói todos os estados dos clips só a partir
  do JSON + `pool.chr`. No Mesen, `tools/test_mesen_hud_flicker.lua` rodou os
  dez cenários (andando e atacando) sem nenhum write de INIDISP em linhas
  visíveis depois do fatiamento dos commits.
* **Clips integrados, com três cenários ainda estáticos.** O build gera um
  pool de 160 tiles por cenário (`anim/*.pool.chr`) e descritores `.inc` no
  formato do ticker nativo; `StagePick` carrega o pool do cenário atual em
  `$2C00` (`StgAnimPoolTab`). Os descritores de Rua japonesa, Templo e Rugal
  ainda deixam a tela preta no ticker atual (o problema é do descritor, não da
  arte); esses três ficam em `V2_ANIM_DISABLE` e usam a arte estática v2 até a
  revisão dos tempos/estados.
* **Commits de pose são fatiados entre quadros.** Os clips grandes (Porto,
  Porto B) mudam centenas de células; escrever tudo em um vblank estourava o
  forced blank e piscava a tela. O ticker agora mede as linhas restantes
  (`StageAnimRoom`), escreve só as células cuja palavra mudou e retoma no
  quadro seguinte. Em troca, os clips maiores podem animar um pouco mais
  devagar que o arcade; os pequenos continuam no ritmo original.
* **China:** a v2 já está alinhada ao convés; `STAGE_YOFS` ficou vazio para
  não deslocar a arte 32 px. O balanço do barco (±3 px) e as camadas de fundo
  em rolagem contínua não foram portados (exigiriam BG2 ou scroll por cenário).
* **Elementos em deslocamento** (aves, gaivotas, gato, vaga-lumes) não viraram
  tiles; as poses estão exportadas para uso futuro como sprites.
* **O orçamento de 512 tiles continua sendo o maior limite de qualidade**
  (coluna "Só paleta"). Nos trechos mais detalhados há fusão visível de tiles.
  O espaço de VRAM de BG1 acima do tile 512 é compartilhado com o HUD (BG3)
  e o pool, então ampliar o orçamento exige mexer no layout de VRAM.
* Pontilhado ordenado foi implementado e testado (`quant.ordered_dither`),
  mas **não está ativo**: nos testes ficou mais ruidoso que a redução sem
  pontilhado e piorou as métricas perceptuais.
* Buracos onde camadas de paralaxe não alcançam as bordas do mundo foram
  preenchidos com a vista dos extremos da câmera; pode haver repetição de
  prédios na borda (Coreia).

## Reprodução

```sh
python3 -I tools/stage_v2/build_v2.py assets/stages/stages_v2      # ~6 min, numpy+Pillow
python3 -I tools/stage_v2/movers.py assets/stages/stages_v2
python3 -I tools/stage_v2/verify_v2.py assets/stages/stages_v2
python3 -I tools/stage_v2/report.py assets/stages/stages_v2
```
