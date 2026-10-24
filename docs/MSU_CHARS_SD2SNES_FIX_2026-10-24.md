# CHR do MSU no SD2SNES MKII — causa e correção (24/10/2026)

## Sintoma

No SNES real com SD2SNES MKII, os lutadores cujo CHR vem do arquivo
`.msu` aparecem com tiles trocados, parcialmente transparentes ou
"colados" de outras poses. Em emuladores (Snes9x/Mesen) o mesmo par
ROM+MSU desenha os corpos corretamente.

## O que os diagnósticos D1–D4 já provaram

- D1: as buscas de boot (`0x8000`, `0xAA0000`, `0x1688000`) e a cópia
  MSU→VRAM funcionam; os contadores de luta (`REQ=OK`, `TO=0000`)
  mostram que nenhuma busca estourou o prazo.
- D2: MSU→RAM por DMA e RAM→VRAM por DMA casam byte a byte com o
  `.msu` nas três amostras de boot.
- D3: oito buscas diretas (inclusive acima de 8 MiB) devolvem os dados
  certos.
- D4: leitura sequencial de 8 MiB + 256 bytes e as oito buscas diretas
  casam por CPU e por DMA (`C/M/S=0000`, `SQ=0008`).

Ou seja: o arquivo, a porta MSU, o DMA e a VRAM não estão quebrados. A
única diferença entre as amostras de boot **que passam** e os blocos
de CHR **que falham** é o alinhamento do endereço.

## Causa

Todas as amostras de boot são alinhadas a 512 bytes (offset 0 dentro
do setor). Os blocos de CHR carregados durante a luta são apenas
alinhados a 32 bytes (início de tile). O SD2SNES preenche o cache de
dados do MSU a partir do setor de 512 bytes e posiciona o ponteiro de
leitura da SNES no offset dentro desse setor. Em leituras feitas por
DMA, a combinação desse ponteiro não nulo com a página de cache do
SD2SNES pode devolver o primeiro byte/posição anterior (ou atravessar
a página de 8 KiB do cache), deslocando o bloco inteiro. O resultado
visual é exatamente o mosaico de tiles visto no console.

O caminho direto antigo (`MSU $2001 -> VRAM`, modo 1 de DMA) também
dependia desse ponteiro e era o único ponto em que o diagnóstico de
boot D1 já mostrava algumas palavras divergentes (`VRAM 000C`).

## Correção

Em `SD_msu` (`src/engine/fight.asm`):

1. A busca do MSU é **sempre alinhada para baixo em 512 bytes**; o
   número de bytes entre o setor e o bloco pedido fica em
   `MSU_PREFIX` ($543E).
2. O bloco `prefixo + payload` é trazido do MSU para `MsuStageBuf`
   (2 KiB em `$7F:5000`, `src/snes/fight_bridge.asm`).
3. Só o payload é enviado de `MsuStageBuf + prefixo` para a VRAM.

Com isso toda leitura começa no offset 0 do setor, o primeiro byte
eventualmente inválido cai no prefixo descartado e o DMA para a VRAM
nunca lê direto da porta MSU. O total lido (até 480 + 1280 = 1760
bytes) cabe com folga em uma página de 8 KiB do cache do SD2SNES.

O caminho é o mesmo já validado no boot pela D2 (MSU→RAM→VRAM), agora
com o alinhamento de 512 bytes. O código da rotina fica fora do banco
de 32 KiB do motor (`.ORGA $CF00` no banco auxiliar) para não estourar
o setor `Fight`.

## Verificação feita

- Build de produção `kof98-snes.sfc` linkado e `tools/verify_pvsnes_rom.py` OK.
- Snes9x: 546 blocos de CHR ao vivo de Rugal × Leona conferidos contra
  o `.msu` na VRAM, incluindo todos os 12 valores de prefixo usados
  (0, 64, 96, 128, 160, 224, 256, 320, 352, 384, 416, 480): 546/546
  exatos.
- Diagnósticos D1, D2, D3 e D4 recompilados e aprovados no teste
  headless.
- O conteúdo do `.msu` não mudou (SHA-256
  `60f09fec…40dc0888`); só a ROM foi alterada.

## Teste final no console

Copie `kof98-snes.sfc` **e** `kof98-snes.msu` deste build para a mesma
pasta do SD (substituindo os dois; não misture com um `.msu` antigo),
ligue o SNES e entre em Rugal normal × Leona. Os dois corpos devem
aparecer completos e animar. Se possível, repita uma luta espelhada
(Rugal × Rugal) para exercitar o cache com endereços próximos.

Se ainda houver corrupção, o próximo suspeito é o firmware do
SD2SNES: as versões anteriores à 1.11.0 têm correções de cache de
dados do MSU ("wrong data streamed") e a 1.11.2 corrige o incremento
do ponteiro no fim do DMA. Atualizar para a 1.11.2 (ou a última
disponível para o MKII) remove essa variável.
