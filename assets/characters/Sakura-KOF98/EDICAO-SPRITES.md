# Sakura: contornos reforçados

O arquivo ativo é `Sakura.sff`; o `.def` existente já aponta para ele.
A cópia original está em `backups/Sakura.original.sff`.

Foram editadas 527 imagens da personagem em 92 grupos. Com os 46 quadros
vinculados, 573 entradas recebem o novo contorno. As outras 1.503 entradas
(efeitos, retratos e demais elementos) permanecem intactas.

O contorno externo ganhou um pixel nativo, com azul quase preto na roupa,
marrom na pele e vermelho escuro nas luvas/sapatos. Usa exclusivamente os
índices já existentes na paleta compartilhada. Todos os pixels opacos originais
foram preservados. As dimensões foram expandidas em dois pixels e os eixos
compensados em um, mantendo o alinhamento das animações e caixas de colisão.
É uma adaptação dos contornos; não redesenha anatomia ou sombreamento interno.

Referências locais: Kyo, Kasumi, Athena e Yuri, em
`/run/media/fabio/Dados/Fabio/kof98_port_snes/assets/characters`.

## Reproduzir e validar

```sh
node tools/thicken_outlines.mjs
python3 tools/validate_sprites.py
./testar-ikemen.sh
```

A conversão sempre parte do backup e não acumula engrossamentos. A validação
verifica as 2.076 entradas, índices, vínculos, paletas, eixos e a preservação dos
pixels originais. Veja `output/validation.json` e `output/comparacao.png`
(pares antes/depois: guarda, soco e chute agachado).

O teste de abertura do IKEMEN foi tentado em uma cópia temporária do runtime.
O sandbox negou a conexão aos sockets X11 e Wayland (`Operation not permitted`),
impedindo a conferência visual em jogo nesta sessão. O script acima abre Sakura
editada contra Kyo fora do sandbox e não altera a instalação do IKEMEN.

`output/estudo-contorno.png` é somente um estudo visual gerado com a ferramenta
imagegen integrada. Prompt: preservar Sakura, pose e roupa; reforçar o contorno
externo em aproximadamente um pixel nativo, com azul quase preto para roupa e
marrom escuro para pele, inspirado em KOF98; manter pixel art e transparência.
O SFF final usa o processamento determinístico de pixels indexados em JavaScript.

## Stand com ritmo de KOF98

`tools/stand_kof98.py` gera a Action 0 com 14 passos (59 ticks) a partir dos
quadros 0,0..0,6 com o contorno reforçado:

- intercalações de 1 px no balanço do corpo. Os pés ficam fixos e uma linha
  da coxa/joelho é duplicada ou removida;
- pausas curtas no topo e no fundo do balanço (5 ticks), como nos stands de
  KOF98;
- a fita da bandana atrasada um passo em relação ao corpo e sempre em
  movimento, inclusive nas pausas, como a bandana do Kyo ou o cabelo de
  Iori/Athena.

Os sprites novos são 0,7..0,15, inseridos logo após 0,6 com a mesma paleta.
Os vínculos foram ajustados. Backups: `backups/Sakura.pre-stand-kof98.{sff,air}`.
Prévias: `output/sakura-stand-novo.gif`, `output/sakura-stand-antes-depois.gif`
e `output/sakura-stand-quadros.png`.

```sh
python3 tools/stand_kof98.py preview   # só gera as prévias
python3 tools/stand_kof98.py apply     # grava no SFF/AIR (recusa se já aplicado)
```

Se `thicken_outlines.mjs` for rodado de novo, ele reconstrói o SFF a partir do
original e apaga os quadros 0,7..0,15. Depois dele, rode `apply` novamente.
