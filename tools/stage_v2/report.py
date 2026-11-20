#!/usr/bin/env python3
"""Gera README.md e as folhas de contato de assets/stages/stages_v2 a partir
das metricas e dos manifestos reais (nenhum numero e escrito a mao).

Uso: python3 -I tools/stage_v2/report.py OUTDIR
"""
import glob
import json
import os
import sys

from PIL import Image, ImageDraw

LABEL = {
    "KOF98-ChinaStage": "China", "KOF98-JpnStreetStage": "Rua japonesa",
    "KOF98-JpnTempleStage": "Templo japonês", "KOF98-KoreaStage": "Coreia",
    "KOF98-Mid.EastStage": "Bazar (Oriente Médio)", "KOF98-RugalStage": "Rugal",
    "KOF98-SpainStage": "Espanha", "KOF98-USAWharfStage-B": "Porto B (vermelho)",
    "KOF98-USAWharfStage": "Porto", "KOF98-USAYardStage": "Pátio ferroviário",
}


def contact(out, names):
    for kind, suffix in (("snes", "_snes.png"), ("arcade", "_arcade.png")):
        W, H = 512, 224
        sheet = Image.new("RGB", (W * 2 + 6, (H + 16) * 5 + 4), (24, 24, 24))
        d = ImageDraw.Draw(sheet)
        for i, n in enumerate(names):
            im = Image.open(os.path.join(out, "preview", n + suffix)).convert("RGB")
            x, y = (i % 2) * (W + 6), (i // 2) * (H + 16)
            sheet.paste(im, (x, y + 14))
            d.text((x + 4, y + 2), f"{LABEL.get(n, n)} — {kind}", fill=(255, 220, 80))
        sheet.save(os.path.join(out, "preview", f"contact_{kind}.png"))


def main():
    out = os.path.abspath(sys.argv[1])
    met = json.load(open(os.path.join(out, "metrics.json")))
    names = sorted(met)
    contact(out, names)
    rows, clip_rows, mover_rows = [], [], []
    tot_pool = 0
    for n in names:
        m = met[n]
        man = json.load(open(os.path.join(out, "anim", n + ".json")))
        rows.append(f"| {LABEL.get(n, n)} | {m['static_tiles']} | {m['pool_tiles']} | "
                    f"{m['clips']} | {m['pix_rmse']:.3f} | {m['blur_rmse']:.3f} | "
                    f"{m['palette_only_blur']:.3f} |")
        tot_pool += m["pool_tiles"]
        for c in man["clips"]:
            lay = ", ".join(f"{l['name']} (ação {l['action']})" for l in c["arcade_layers"])
            clip_rows.append(f"| {LABEL.get(n, n)} | {lay} | {len(c['cells_ty_tx'])} | "
                             f"{c['pool_tiles']} | {len(c['state_tilemap_words'])} | "
                             f"{c['cycle_ticks'] / 60:.2f} s |")
        mv = os.path.join(out, "anim", n + ".movers.json")
        if os.path.exists(mv):
            for e in json.load(open(mv)):
                mover_rows.append(f"| {LABEL.get(n, n)} | {e['name']} | "
                                  f"{len(e['poses'])} | `{e['sheet']}` |")
        for dl in man["dropped_layers"]:
            clip_rows.append(f"| {LABEL.get(n, n)} | ~~{dl['name']}~~ — {dl['reason']} | – | – | – | – |")
    text = f"""# Stages KOF98 — reconstrução a partir do arcade (v2)

Versão para **análise**. Nada aqui é lido pelo jogo: `assets/stages/stages_png_snes/`
e o pipeline atual (`tools/build_stages.py`) não foram alterados. Esta pasta é
gerada por `tools/stage_v2/` (reprodução no fim deste arquivo).

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
{chr(10).join(rows)}

Total de tiles de pool somados: {tot_pool}. Cada cenário usa no máximo 160.

### Animações extraídas do arcade

| Cenário | Camadas do arcade | Células | Tiles | Estados | Ciclo |
| --- | --- | ---: | ---: | ---: | ---: |
{chr(10).join(clip_rows)}

### Elementos em deslocamento (fora dos clips)

| Cenário | Camada | Poses | Folha |
| --- | --- | ---: | --- |
{chr(10).join(mover_rows)}

## Limites e pendências (leia antes de julgar)

* **Não foi testado na ROM nem no emulador.** O que foi verificado:
  `verify_v2.py` passa cada PNG por `emit_stage` (conversor real do jogo),
  decodifica CHR/mapa/CGRAM como o PPU e compara com o PNG, e reconstrói todos
  os estados dos clips só a partir do JSON + `pool.chr`.
* **A engine atual não carrega esses clips.** Hoje há um pool compartilhado
  de 160 tiles em VRAM (tile 704+, `stage_anim.chr`) e descritores gerados por
  `build_anims()`. Os clips v2 precisam de um pool **por cenário** carregado
  na troca de cenário e de um relógio de ticks por grupo. As palavras de
  tilemap do JSON são relativas ao início do pool (somar 704).
* **China:** `STAGE_YOFS` em `build_stages.py` desloca a arte da China 16 px.
  O arcade desenha a borda frontal do convés (BG 25) em `layerno 1`, na frente
  dos lutadores; como o port usa um único BG1 atrás dos OBJ, essa borda caía
  atrás das canelas e os lutadores pareciam estar fora do barco. O deslocamento
  coloca a borda logo abaixo da linha dos pés sem reverter a arte v2.
  O balanço do barco (±3 px) e as camadas de fundo em rolagem contínua não
  foram portados (exigiriam BG2 ou scroll por cenário).
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
"""
    open(os.path.join(out, "README.md"), "w").write(text)
    print("README.md", len(text))


if __name__ == "__main__":
    main()
