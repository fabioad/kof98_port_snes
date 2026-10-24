# Diagnóstico D4 — faixas de endereço e leitura sequencial

Extraia `kof98-msu-diag4.sfc` e `kof98-msu-diag4.msu` na mesma pasta do SD.
Inicie a ROM e aguarde o teste inicial. A tela pode permanecer apagada
por vários segundos enquanto são lidos pouco mais de 8 MiB. Depois entre
em Rugal normal contra Leona e tire uma foto do painel inteiro.

Este teste não aplica uma nova correção aos personagens. Durante a luta
o carregamento continua igual à D2/D3. O objetivo é comparar buscas diretas
com uma única leitura sequencial, sem reposicionar o MSU entre os pontos.
O arquivo `.msu` tem o mesmo conteúdo e SHA-256 do pacote D2/D3.

## Painel

Cada uma das oito linhas numeradas identifica um bloco de 256 bytes:

- 00: 0000FF00 — últimos 256 bytes antes de 64 KiB.
- 01: 00010000 — 64 KiB.
- 02: 00020000 — 128 KiB.
- 03: 00040000 — 256 KiB.
- 04: 00100000 — 1 MiB.
- 05: 00200000 — 2 MiB.
- 06: 00400000 — 4 MiB.
- 07: 00800000 — 8 MiB.

Após o código aparece o endereço fornecido à rotina de busca. Esse registro
vem dos valores usados pela ROM; não é uma leitura de volta do endereço
aceito pelo hardware.

- C: bytes diferentes após uma busca direta e leitura pela CPU para RAM.
- M: bytes diferentes após outra busca direta e DMA MSU→RAM.
- S: bytes diferentes após percorrer o arquivo desde zero, sem novas buscas
  entre os pontos, usando DMA MSU→RAM em blocos de 256 bytes.
- Na segunda linha: E são os primeiros quatro bytes esperados; M e S são
  os primeiros quatro bytes capturados nas respectivas leituras.

O esperado é C/M/S=0000, com E/M/S iguais. A amostra 00 é toda zero no
arquivo atual; isso é normal. As outras têm conteúdo variado dentro dos
256 bytes, mesmo quando os primeiros quatro são zeros.

SQ indica quantos pontos da leitura sequencial foram concluídos: o esperado
é 0008. S=FFFF significa que aquele ponto não foi alcançado/verificado.
B soma os seguintes bits quando há falha:

- 0001: timeout na busca direta do teste CPU.
- 0002: timeout na busca direta do teste DMA.
- 0004: MSU não detectado.
- 0008: timeout na única busca para iniciar o fluxo sequencial em zero.
- 0010: timeout do status durante a leitura sequencial.

O esperado é B=0000. FFFF nas colunas C/M indica teste não realizado.
REQ/OK/TO/P1/P2/ST/POS/LEN, no final, continuam referentes à luta.

## Condições e interpretação

O fluxo sequencial consome desde o byte zero até incluir o bloco em
00800000, totalizando 8 MiB + 256 bytes. Descarta os blocos intermediários
e compara os oito pontos com cópias incorporadas à ROM. Há uma pausa fixa
de 1024 iterações de CPU a cada 4 KiB para dar oportunidade de reabastecer
o buffer do MSU. O status é consultado antes de cada DMA, com limite de
FFFF consultas. Não existe nova busca entre os pontos sequenciais.

Se C/M falharem a partir de uma faixa e S passar nesses mesmos endereços,
isso é evidência de diferença entre reposicionar e continuar lendo. Se S
também falhar, ainda será preciso separar problemas de fluxo/reabastecimento,
leitura do SD e outros fatores. A pausa fixa é uma condição de teste, não
garantia de que todo cartão terá tempo de responder. Os resultados só
verificam os blocos amostrados, não todos os bytes descartados entre eles.

O painel ocupa as linhas 5 a 24, sobre o jogo. A D4 preserva a ROM normal e
os pacotes D1/D2/D3. É um diagnóstico, sem correção comprovada no console.

Recompilar: `python3 tools/build_msu_diag.py --version 4`.
