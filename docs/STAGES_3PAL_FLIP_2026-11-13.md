# Stages: 3 paletas + tiles espelhados — 13/11/2026

## Sintoma

Vários cenários tinham manchas quadradas bem marcadas: rochas, montanhas,
fachadas e o chão apareciam como blocos de 8×8 com um único tom. A causa era
o limite de conversão, não o desenho: cada cenário tem ~1600–1800 tiles 8×8
distintos e precisava caber em **512 tiles 4bpp** e **15 cores**.

O PNG antigo chegava a esse número substituindo tiles parecidos por um único
tile "médio". Em áreas de textura (pedra, folhagem, calçamento) o tile
substituto perdia o degradê interno e o resultado lia como um quadrado.

## O que mudou

1. **Três paletas de BG por cenário.** `StagePick`
   (`src/engine/fight.asm`) já subia 96 bytes para CGRAM 32–79, ou seja as
   paletas de BG 2, 3 e 4, mas o conversor só preenchia a primeira: as outras
   duas iam pretas. Agora cada cenário usa até 45 cores, 15 por paleta, e cada
   tile escolhe a paleta que melhor o reproduz. Nenhuma mudança foi necessária
   no engine.
2. **Tiles espelhados.** O mapa aceita os bits de H/V flip (14/15) e o mesmo
   padrão pode ser reutilizado por qualquer uma das três paletas, mudando só
   os bits 10–12. Isso libera espaço no orçamento de 512 tiles.
3. **Redução por k-medoids, não por média.** `tools/stage_requant.py` escolhe
   os 512 tiles representantes de forma discreta: cada representante é um tile
   real de índice, otimizado pixel a pixel para o conjunto de posições que o
   usa. A métrica soma o erro OKLab por pixel **e** o erro da média de cada
   sub-bloco 4×4, que é justamente o que o olho lê como "quadrado". Nenhum
   tile é criado por média, então não nascem blocos novos.
4. **Retoques preservados.** Rua japonesa (asfalto limpo), porto americano
   (céu noturno) e porto B (céu vermelho uniforme) foram repintados depois das
   referências `hires/`. Esses pixels continuam vindo do PNG aprovado; o resto
   do cenário vem do `hires/`, que tem o detalhe que faltava.

## Resultado

Erro perceptual (OKLab RMSE) contra a referência `hires/`, pixel a pixel:

| Cenário | antes | depois |
| --- | --- | --- |
| China | 0,2059 | 0,0699 |
| Rua japonesa | 0,1818 | 0,0647 |
| Templo japonês | 0,1136 | 0,0566 |
| Coreia | 0,1921 | 0,0779 |
| Bazar (Mid. East) | 0,2565 | 0,0791 |
| Rugal | 0,1938 | 0,0482 |
| Espanha | 0,2123 | 0,0524 |
| Porto B | 0,1601 | 0,0406 |
| Porto | 0,0891 | 0,0259 |
| Pátio ferroviário | 0,2063 | 0,0785 |

Todos os dez cenários continuam em **512 tiles** e 96 bytes de paleta, então
o custo por cenário na ROM não mudou (16.384 + 4.096 + 96 bytes). O conversor
confirma o limite com `assert` e o arredondamento de erro de tile é zero: a
decodificação de CHR+mapa reproduz exatamente os índices do PNG.

## Formato novo dos PNGs

`assets/stages/stages_png_snes/KOF98-*.png` agora tem 512×224, modo P e até
45 cores. O índice `p * 15 + c` significa "cor `c` da paleta `p`", com `p` de
0 a 2 (BG 2, 3 e 4). É obrigatório que os 64 pixels de um tile pertençam à
mesma paleta — o conversor aborta com mensagem clara se não pertencerem.

A cor 0 de BG é transparente no SNES, então as 15 cores de cada grupo são
gravadas nos índices 1–15 do CGRAM e o índice 0 fica livre. O mapa carrega
`paleta = 2 + grupo` nos bits 10–12 e os bits 14–15 de H/V flip.

`tools/build_stages.py` foi adaptado para esse formato, para os flips e para
as animações: cada pose do pool dinâmico (704+) é um tile próprio e escolhe,
independente, a paleta de menor erro entre as três. O pool continua com 120
tiles de 160.

## Como reproduzir

```sh
python3 tools/stage_requant.py /tmp/stages          # gera em pasta separada
python3 tools/stage_requant.py assets/stages/stages_png_snes   # aplica
python3 tools/build_stages.py                        # confere e gera o build
python3 tools/verify_stage_export.py                 # decodifica e compara
```

`verify_stage_export.py` decodifica CHR/mapa/paleta como o PPU (planos 4bpp,
flips, paletas 2–4, cor 0 transparente) e compara pixel a pixel com o PNG:
os dez cenários dão zero diferenças.

`tools/build_stages.py` é executado pelo `make` e agora depende dos PNGs e do
`stage_animations.json`, então editar um cenário força a regeneração.

`stage_requant.py` usa `numpy` e `Pillow`; cada cenário leva ~1 min.

## Limites conhecidos

- O orçamento de 512 tiles foi atingido em todos os cenários: melhorar um
  detalhe implica piorar outro. A métrica já pondera o brilho por sub-bloco,
  que é o defeito mais visível.
- As animações existentes (público, estudantes, comerciantes, remador) foram
  reamostradas do PNG novo. O pool dinâmico continua em 120 tiles de 160.
- Os PNGs anteriores foram copiados para
  `assets/stages/stages_png_snes/backups/2026-11-13-before-requant/`
  (cópia local, não versionada).
