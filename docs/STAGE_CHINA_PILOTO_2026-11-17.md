# Piloto: China com detalhes priorizados e poses reais

Implementado em 17/11/2026. Cenário: `KOF98-ChinaStage`, índice 1.

Atualização posterior: o [piloto do bazar](STAGE_BAZAR_PILOTO_2026-11-17.md)
elevou a ocupação do pool compartilhado para 146 tiles. Os 48 tiles de
animação e a arte estática da China permanecem preservados; os 120 tiles
citados abaixo descrevem o estado após o primeiro piloto.

## Resultado

- Limite estático preservado: 512 tiles; o resultado usa 504 tiles 4bpp.
- Três paletas de BG, sem ampliar a reserva de cores ou mudar o layout de VRAM.
- Templo, telhados, colunas e fachada recebem peso 4 na redução de tiles.
  O restante permanece com peso 1. A ponderação participa da seleção inicial,
  otimização dos padrões, erro agregado e redistribuição de padrões ociosos.
- Remador com três poses reais do SFF (grupo 15, números 0, 10 e 17),
  usando os PNGs já extraídos e alinhados pelos eixos originais.
- As poses são reduzidas proporcionalmente para uma área de 32×32, com pés
  alinhados. A roupa azul e os tons de pele recebem cores dentro da segunda
  paleta existente. O cenário anterior possuía entradas repetidas nessa paleta.
- O remador ocupa `(328,112,32,32)` na arte de 512×224. A posição foi escolhida
  no convés para aparecer durante o enquadramento usual da luta. O personagem
  sentado à direita da arte original permanece estático.
- A antiga oscilação de pedaços do fundo à esquerda foi removida deste cenário.
  Os demais cenários conservam suas animações anteriores.

## Custo e funcionamento

O gerador reduz o fundo a até 496 padrões e reserva até 16 padrões para a
pose inicial. A deduplicação final resulta em 504 tiles no cenário inteiro.
O PNG estático contém a mesma pose inicial usada na animação, evitando um
salto de composição na primeira troca.

As três poses usam 16 células cada: 48 tiles residentes, ou 1.536 bytes.
Esse é o mesmo consumo real da antiga animação do remador. O pool compartilhado
dos cenários continua com 120 dos 160 tiles disponíveis. Cada troca escreve
16 palavras no tilemap (32 bytes de dados); não há transferência de novos
gráficos durante a luta. A seleção de paleta de cada célula é conjunta para
as três poses, evitando alternância de paleta no fundo entre quadros.

A sequência preserva as durações anteriores de 24, 30 e 24 ticks do relógio
da engine. São três poses selecionadas, não os 20 quadros da sequência original.
Como a engine pode adiar a atualização de cenário quando falta tempo no
VBlank, esses ticks não constituem uma garantia de duração em segundos reais.

Os campos globais de orçamento/double buffer no JSON de animações são uma
especificação legada. Para este piloto, os arquivos `resident_patch_files` e
os números medidos aqui descrevem a implementação efetiva.

## Comparação com a fonte

Erro perceptual OKLab, calculado pelo gerador contra a fonte `hires/`:

- Área do templo: 0,07952 antes → 0,04420 depois (redução de aproximadamente 44%).
- Imagem completa, excluindo a área do novo remador: 0,06994 → 0,07205
  (aumento de aproximadamente 3%).

O ganho está concentrado nos detalhes priorizados; há uma pequena perda média
nas outras áreas. Esses números medem fidelidade à fonte, não uma porcentagem
de melhora estética. A aprovação visual do usuário continua importante.

## Arquivos e reprodução

- [Prévia animada da arte](../assets/stages/stages_png_snes/pilot_china/preview.gif).
- [Arte anterior](../assets/stages/stages_png_snes/pilot_china/before.png).
- [Arte final](../assets/stages/stages_png_snes/KOF98-ChinaStage.png).
- [Métricas](../assets/stages/stages_png_snes/pilot_china/metrics.json).
- `tools/build_stage_pilot.py`: regenera a arte e os três patches indexados.
- `tools/build_stages.py`: exporta os patches como tiles residentes.
- `animations/build_definitions.py`: conserva a configuração do piloto ao
  regenerar as definições de animação.

```sh
OPENBLAS_NUM_THREADS=2 python3 tools/build_stage_pilot.py
python3 tools/build_stages.py
python3 tools/verify_stage_export.py
make -f Makefile.pvsnes
python3 tools/test_stage_pilot_headless.py
```

Nesta sessão, o build regenerou os stages e recompilou/relinkou a ROM com os
assets de personagens e áudio já existentes. O arquivo principal atualizado
é `kof98-snes.sfc`; o conteúdo MSU de personagens não foi regenerado pelo piloto.

## Validação executada

- Exportação dos dez cenários decodificada e comparada com os PNGs: zero
  diferenças de índices. O verificador foi corrigido para considerar o
  deslocamento vertical de quatro linhas de tiles já existente na China.
- Tiles exportados das três poses comparados pixel a pixel com seus patches.
- ROM compilada e executada no Snes9x/libretro por 1.500 frames de teste,
  com um super do Kyo e movimento dos dois lutadores.
- Três poses observadas; cada atualização apresentou uma pose completa.
- Gráficos estáticos e pool dinâmico permaneceram idênticos aos dados
  exportados. Somente as 16 células previstas do tilemap foram alteradas.
- Capturas reais: `build/stage-pilot/pose-0-in-game.png` até `pose-2-in-game.png`.
- Relatório: `build/stage-pilot/validation.json`.

O teste força o cenário 1 apenas numa cópia temporária da ROM; a seleção de
cenários do jogo principal não foi alterada. Não houve teste em hardware
real nem de uma partida inteira até seu encerramento. Ampliação de VRAM,
pool por cenário e streaming de novos tiles continuam fora deste piloto.
