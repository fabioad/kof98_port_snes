# Retoques de geometria — 2026-11-05

Os resultados estão em `../ready/`. Foram retocados cinco cenários:

- China: contornos dos morros ao fundo, preservando vegetação e remador.
- Rua japonesa: manchas de desgaste orgânicas no asfalto.
- Espanha: reflexos estreitos e interrompidos no piso, substituindo blocos retangulares.
- Porto americano: céu e silhueta distante da cidade.
- Porto americano B: céu vermelho mais uniforme.

Templo japonês, Coreia, bazar, pátio ferroviário e Rugal foram preservados.
Os PNGs da pasta principal, usados pelo build atual, continuam intactos.
Nenhuma ROM foi compilada ou testada no emulador nesta etapa.

`comparison.png` mostra antes à esquerda e depois à direita.
`before/` contém os dez PNGs de ready anteriores aos retoques.
O backup integral está em `assets/stages/stages_png_snes-backup-20261105-000609.tar.gz`,
relativo à raiz do projeto; seus 283 arquivos foram conferidos por SHA-256.
Os hashes anteriores estão em `baseline.json`.

## Produção e reprodução

As cinco referências retocadas foram produzidas com a ferramenta integrada
imagegen. Os prompts exatos e caminhos das gerações estão em `prompts.json`;
as cópias locais estão em `sources/`. Não dependem dos caminhos externos para
repetir a exportação.

`export.mjs` reduz as referências para 512×224, reaplica a paleta original
sem dithering e compõe somente as áreas escolhidas. Para recuperar espaço,
mescla pares de tiles estáticos semelhantes, usando um tile real em vez
de uma média que criaria novos blocos. Tiles usados pelas regiões de
animação, incluindo margem de amostragem superior, ficam protegidos.
O orçamento é compartilhado: no máximo 512 tiles 8×8 e 15 cores por PNG.
Alguma simplificação continua necessária nesse limite.

```sh
node assets/stages/stages_png_snes/redesign/retouch/export.mjs
node assets/stages/stages_png_snes/redesign/retouch/wharf-night/export.mjs
node assets/stages/stages_png_snes/redesign/retouch/street-clean/export.mjs
python3 -B assets/stages/stages_png_snes/redesign/retouch/verify.py
```

`verify.py` usa o conversor atual `tools/build_stages.py` em memória e
arquivos temporários. Verifica todos os pixels após decodificar CHR/mapa,
dimensões, índices e limites; compara também os gráficos e tabelas de
animação gerados antes/depois, que são idênticos byte a byte. Confere os
273 arquivos originais fora de ready por SHA-256 e Rugal integralmente.
Resultados em `validation.json`; contagens dos retoques em `metrics.json`.
O porto B usa 474 tiles, a rua japonesa usa 478, e os outros três retoques usam 512.

## Revisão do porto azul

`wharf-night/` guarda a versão aprovada anterior (`before.png`), a nova
referência imagegen, o prompt e a exportação reproduzível do segundo passe.
O céu passa a azul-marinho uniforme; os prédios distantes têm contornos
mais simples e janelas discretas. Os quatro tons azuis principais da paleta
também foram escurecidos, incluindo seus reflexos no primeiro plano.
O desenho do galpão, das velas, dos veículos e das texturas do piso foi mantido.
A versão final continua em `../ready/KOF98-USAWharfStage.png` (512 tiles).
`wharf-night/comparison.png` compara este passe com a versão anterior.

## Solo limpo da rua japonesa

`street-clean/` guarda o PNG anterior, a referência visual imagegen e seu
prompt. A direção visual foi aplicada aos índices originais da paleta,
com máscara exata para preservar arquitetura, carros, público, faixa de
pedestres, marcas viárias e bueiro. O asfalto usa um tom quente uniforme,
sem as manchas de desgaste que competiam com os lutadores. As sombras
próximas aos carros permanecem. A contagem caiu de 512 para 478 tiles,
com as mesmas 15 cores. `street-clean/comparison.png` compara os dois passes.
