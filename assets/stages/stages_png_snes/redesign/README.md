# Cenários redesenhados — 16-bit

Os dez PNGs na pasta superior são as versões finais para o jogo.
Os arquivos anteriores estão em `originals/`; as referências em `../hires/`
foram preservadas. `ready/` contém cópias das exportações aprovadas.

Desenhos produzidos com a ferramenta integrada de geração de imagens,
usando cada cenário de `hires/` como referência. Os prompts completos e
os caminhos das gerações estão em `manifest.json`.

Cada imagem final tem 512×224 pixels, PNG indexado de 4 bits, 15 cores
compatíveis com RGB555 e 512 tiles distintos de 8×8. O índice transparente
é acrescentado pelo conversor do jogo. Custo por cenário: 16.384 bytes de
gráficos 4bpp + 4.096 bytes de mapa + 32 bytes de paleta = 20.512 bytes,
antes de eventual compressão da ROM.

Os PNGs têm aproximadamente 15–26 KB e são maiores que as versões antigas
muito simplificadas. Seu tamanho em disco não representa o custo na ROM.
O orçamento de 512 tiles do conversor foi respeitado. Espanha e Rugal
usam mais tiles que seus antigos desenhos de quatro cores para recuperar
formas e contraste; a contagem original está em `validation.json`.

`export-stages.mjs` reduz os desenhos gerados, quantiza a paleta sem
dithering, ajusta RGB555 e agrupa tiles semelhantes dentro do orçamento.
Esse agrupamento simplifica texturas e pode tornar blocos visíveis em
áreas de baixo contraste. Não aplica redução global de resolução abaixo
de 512×224.

Para repetir a exportação, com os desenhos originais gerados disponíveis:

```sh
node redesign/export-stages.mjs
python3 -B redesign/verify-stages.py
```

A verificação executa `build_stage()` do projeto em uma pasta temporária
para cada cenário, decodifica gráficos/mapa e compara todos os pixels e
a paleta. Os dez passaram. A ROM não foi recompilada nem verificada no
emulador nesta tarefa. O conversor atual seleciona a rua japonesa; os
demais arquivos estão preparados para uso posterior.
