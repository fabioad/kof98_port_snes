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
