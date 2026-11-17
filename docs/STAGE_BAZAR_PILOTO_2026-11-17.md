# Piloto: KOF98-Mid.EastStage

Adaptação do bazar, seguindo o piloto da China e preservando o limite de
512 tiles estáticos, três paletas e o layout de VRAM da engine.

## Arte e animação

`tools/build_stage_bazar.py` parte da fonte HD e prioriza os ornamentos da
fachada superior (peso 3) e os objetos da banca esquerda (peso 2). As áreas
com personagens recebem peso 3. As demais regiões mantêm peso 1.

As oscilações artificiais foram substituídas por duas poses reais por clip:

- Espectador da esquerda: grupo SFF 25, imagens 0 e 5; 10 células animadas.
- Público central: grupo 30, imagens 0 e 3; recorte das duas pessoas à
  direita desse grupo; 3 células animadas. As demais pessoas ficam estáticas.
- Comerciante: grupo 20, imagens 0 e 6; 16 células animadas.

As poses vêm dos PNGs extraídos e alinhados em `animations/selected/`.
O gerador ajusta a escala e a posição na composição HD, substitui os trechos
correspondentes e recompõe o pequeno fundo descoberto pelo movimento com
pixels vizinhos fora das silhuetas. Não há deslocamento vertical de pixels
do cenário para simular os gestos. O comerciante utiliza o recorte de torso
e braço disponível, integrado à banca; não é uma animação completa de corpo.

O gerador escolhe uma mesma paleta por célula para ambas as poses, evitando
que a cor do fundo alterne durante o gesto. Apenas células cujos índices
realmente diferem entram na lista `resident_patch_cells`. Os outros pixels
permanecem na imagem estática. A pose inicial dos tiles animados está
incluída no PNG estático, sem salto de composição na primeira atualização.

## Orçamento

São 29 células × 2 poses = 58 tiles residentes (1.856 bytes), em vez dos
32 tiles usados pelas oscilações anteriores do bazar. O pool compartilhado
passa de 120 para 146 tiles, dentro dos 160 já reservados. A reserva de VRAM
não foi ampliada e os dados da China foram preservados.

Cada pose dura 30 ticks da engine. Os três clips começam com fases 0, 10 e
20, distribuindo as trocas: no máximo 16 palavras de tilemap (32 bytes)
por troca. Nenhum gráfico novo é transferido durante a luta. Os ticks podem
ser adiados pela política existente de prioridade dos lutadores/HUD; a
prévia GIF representa o relógio ideal e não uma medição da cadência da ROM.

A redução reserva inicialmente os tiles das células animadas e depois
reaproveita o espaço liberado pela substituição de tiles da pose inicial.
Cada candidato é contado após deduplicação; somente resultados com até
512 tiles são aceitos. A contagem e os erros finais estão em
[metrics.json](../assets/stages/stages_png_snes/pilot_bazar/metrics.json).

## Arquivos e reprodução

- [Prévia animada](../assets/stages/stages_png_snes/pilot_bazar/preview.gif).
- [Imagem anterior](../assets/stages/stages_png_snes/pilot_bazar/before.png).
- [Imagem final](../assets/stages/stages_png_snes/KOF98-Mid.EastStage.png).
- `pilot_bazar/targets.json` guarda posições, células, poses e durações.
  `animations/build_definitions.py` preserva esses dados ao regenerar as
  definições. Os campos globais de double buffer do JSON original continuam
  sendo uma proposta legada, não o orçamento implementado por este piloto.

```sh
OPENBLAS_NUM_THREADS=2 python3 tools/build_stage_bazar.py
python3 tools/build_stages.py
python3 tools/verify_stage_export.py
make -f Makefile.pvsnes
python3 tools/test_stage_pilot_headless.py --stage bazar
python3 tools/test_stage_pilot_headless.py --stage china
```

O teste força o cenário 4 numa cópia temporária da ROM, valida os pixels
dos tiles animados, observa as duas poses de cada clip e verifica a VRAM
durante um super e deslocamentos. A seleção normal de cenários não muda.
O relatório de execução é salvo em `build/stage-bazar/validation.json`,
junto com capturas reais do emulador.

## Resultado e validação de 17/11/2026

- Resultado final: **512 tiles estáticos**, 96 bytes de paleta e 58 tiles
  de animação do bazar. O pool global contém 146 tiles.
- Erro OKLab nas áreas de arquitetura priorizadas: 0,08177 → 0,06613
  (redução de aproximadamente 19%).
- Erro nas áreas medidas fora dos recortes dos personagens: 0,07893 → 0,08221
  (aumento de aproximadamente 4%). O ganho é regional, não uma melhoria
  uniforme da imagem; as métricas não representam uma nota estética.
- Exportação dos dez cenários: zero diferenças entre PNGs e dados decodificados.
- ROM `kof98-snes.sfc` recompilada com os assets de personagens/áudio já
  existentes, sem regenerar o conteúdo MSU neste piloto.
- Teste do bazar no Snes9x/libretro: 1.500 frames, duas poses observadas em
  cada um dos três clips, super do Kyo e deslocamento dos lutadores.
- Gráficos estáticos e pool de animação intactos; apenas as 29 células
  previstas foram alteradas. Pico observado de 16 células por frame
  amostrado, com poses completas e sem atualizações parciais.

Não foi realizado teste em hardware real nem uma partida completa até o fim.
