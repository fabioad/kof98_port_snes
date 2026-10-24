# Diagnóstico D3 — endereços e métodos de busca MSU

Extraia `kof98-msu-diag3.sfc` e `kof98-msu-diag3.msu` na mesma pasta do SD.
Entre em Rugal normal contra Leona e tire uma foto que mostre o painel
inteiro. Esta versão investiga por que as buscas distantes parecem
retornar os mesmos dados do Rugal, apesar do SHA-256 correto do arquivo.

São oito testes de 256 bytes no boot. O tamanho menor permite conferir
vários tipos de busca sem aumentar demais a ROM e o painel. Durante a
luta, os gráficos continuam com o caminho e a espera da D2, com blocos de
até 1280 bytes. Os métodos alternativos ainda não são aplicados à luta.

## Linhas do painel

- R0: início do Rugal, posição 00008000, escritas de 8 bits em $00:2000–2003.
- R1: posição próxima, 00008400, escritas de 8 bits.
- HD: volta ao cabeçalho, posição 00000000, escritas de 8 bits.
- C0: Chizuru, 00AA0000, escritas de 8 bits.
- C1: mesma Chizuru, duas escritas de 16 bits em $00:2000 e $00:2002.
- C2: mesma Chizuru, escritas de 8 bits pelo espelho $80:2000–2003.
- K0: Ken, 01688000, escritas de 8 bits.
- K1: mesmo Ken, duas escritas de 16 bits.

Após cada código aparece o endereço de 32 bits usado pela rotina de
escrita. Esse endereço é registrado em RAM a partir dos valores fornecidos
ao MSU; não é uma leitura de volta dos registradores. O MSU não permite
ler de volta o endereço de busca por esses registradores.

C/M/V continuam sendo as diferenças, em bytes, após CPU→RAM, MSU→RAM por
DMA e RAM→VRAM com leitura de volta. Cada um compara o bloco de 256 bytes
com uma cópia incorporada à ROM. O esperado é 0000 nas três colunas.
Na segunda linha de cada teste, E/C/M exibem os primeiros quatro bytes
esperados, recebidos pela CPU e recebidos pelo DMA na RAM, na ordem do
arquivo. Para HD, E deve começar em 4B4F4639 (ASCII KOF9).

B: 0000=terminou; bit 0001=timeout CPU; bit 0002=timeout DMA;
0004=MSU não detectado. FFFF significa teste não realizado.

REQ/OK/TO/P1/P2/ST/POS/LEN são os mesmos contadores da D2 e se referem ao
carregamento durante a luta, não aos métodos alternativos do boot.

Se os endereços estiverem errados, investigaremos sua formação/leitura na
ROM. Se os endereços estiverem certos, mas apenas um dos métodos funcionar,
teremos uma diferença concreta para investigar. Se todos retornarem dados
antigos, o problema ainda pode estar na rotina, na interpretação da busca,
no firmware/hardware ou nas condições de acesso ao SD; este teste não
determina sozinho qual desses componentes falhou.

O painel ocupa as linhas 5 a 24, sobre parte do jogo. O mapa de 1280 bytes
é atualizado a cada 16 apresentações; os resultados estáticos são montados
uma vez. A ROM normal e os pacotes D1/D2 são preservados.

Recompilar: `python3 tools/build_msu_diag.py --version 3`.
