# Diagnóstico MSU D2 — MSU → RAM → VRAM

Extraia `kof98-msu-diag2.sfc` e `kof98-msu-diag2.msu` na mesma pasta do SD.
Inicie a ROM D2 e entre em Rugal normal contra Leona. Tire uma foto do
painel inteiro e, se possível, um vídeo curto de ataques. Observe também
se os corpos dos personagens passam a aparecer corretamente.

A D2 muda o caminho dos gráficos dos lutadores: primeiro faz DMA do MSU
para uma área reservada de RAM, depois DMA dessa RAM para a VRAM. As vozes
continuam com o carregamento atual. O limite de espera durante a luta
continua em 1024 consultas, para separar este teste da hipótese de timeout.
A ROM normal e o pacote D1 não são substituídos.

## Painel

Os números são hexadecimais. As três amostras iniciais continuam sendo
Rugal (`RUG`), Chizuru (`CHI`) e Ken (`KEN`), com 1280 bytes em cada uma.

Para cada personagem/amostra há três linhas:

- `C`: número de bytes diferentes após leitura pela CPU para a RAM.
- `M`: número de bytes diferentes após DMA do MSU para a RAM.
- `V`: número de bytes diferentes após copiar essa RAM para a VRAM e ler
  a VRAM de volta. Na D2 todos os três contadores contam bytes; na D1 o
  contador VRAM contava palavras de 16 bits.
- `E`: os primeiros quatro bytes esperados, na ordem do arquivo.
- Na linha de `E`, `C` mostra os primeiros quatro bytes capturados pela CPU.
- Na linha seguinte, `M` mostra os primeiros quatro bytes recebidos pelo
  DMA na RAM, e `V` os primeiros quatro bytes lidos de volta da VRAM.

Exemplo: `E 5515A22A` representa os bytes 55, 15, A2, 2A. Algumas amostras
começam com zeros, o que é normal. Os contadores comparam todos os 1280
bytes, não apenas esses primeiros quatro.

O esperado é C=0000, M=0000 e V=0000 nas três amostras, com E/C/M/V iguais.
`B` no cabeçalho: 0000=terminou; bit 0001=timeout CPU; bit 0002=timeout DMA;
0004=MSU não detectado. Contadores FFFF indicam teste não realizado; os
respectivos bytes exibidos também são inválidos. B=0003 soma dois timeouts.

As últimas três linhas mantêm os contadores da luta:

- `REQ`, `OK`, `TO`: buscas solicitadas, prontas e que excederam o prazo.
- `P1`, `P2`: blocos de personagem que completaram os dois DMAs. Cada bloco
  conta uma vez, mesmo usando duas transferências.
- `ST`: último status MSU; bit 80 significa ocupado.
- `POS`, `LEN`: última posição e tamanho solicitados no arquivo MSU.

## Interpretação

- C falha, M/V passam: investigar especificamente as leituras da CPU.
- M falha e V reproduz o mesmo conteúdo de M: a divergência já está na RAM,
  antes da transferência para a VRAM.
- M passa e V falha: investigar DMA RAM→VRAM, leitura de volta e diagnóstico.
- Tudo passa no boot e os lutadores continuam corrompidos: investigar o
  carregamento durante a luta, incluindo concorrência com vozes e OAM.
- Tudo passa e os lutadores aparecem: o caminho intermediado por RAM se
  torna candidato a correção, ainda sujeito a novos testes de estabilidade.

O painel mostra resultados do boot e contadores atualizados a cada 16
apresentações. O mapa usa RAM própria e o texto estático é preparado uma
vez; a transferência do painel tem 832 bytes. Ele cobre parte do cenário
e pode causar um breve apagamento na primeira apresentação. Esta é uma
build de diagnóstico, sem garantia de correção no console.

Os buffers de CPU, DMA e leitura da VRAM são separados e ficam em $7F:3000,
$7F:3500 e $7F:3A00. Para cada amostra também ficam registrados em WRAM os
primeiros offsets divergentes (FFFF se idêntico), embora não caibam no
painel. As comparações acontecem após capturar os blocos, sem intercalar
comparações com a ROM a cada leitura MSU como fazia a D1.

Recompilar: `python3 tools/build_msu_diag.py --version 2`.
Saídas: `build/msu_diag2` e `kof98-msu-diag2.zip`.
