# Personagens MSU invisíveis na build atual — 26/10/2026

## Erro reproduzido

A alteração de flicker introduziu em `SD_msu` uma escrita em INIDISP com
`lda #$0F.b`, mas a rotina chegava com A em 16 bits. A imagem compilada
continha `A9 0F 8F 00 21 00`: a CPU consumia `0F 8F` como imediato de 16
bits e interpretava os bytes seguintes fora das instruções pretendidas.

Foi acrescentado `SEP #$20` antes da escrita de 8 bits em INIDISP e
`REP #$20` antes da aritmética de endereço. Isso também garante que a
escrita não alcance OBSEL, o registrador seguinte.

Este é um erro concreto da build atual, relacionado à alteração de
26/10; não explica retroativamente todos os resultados D1–D4 de 24/10.
O alinhamento de 512 bytes, o estágio por RAM e as correções de áudio
existentes foram mantidos.

## Conclusão do upload quando o SD responde tarde

`MsuStageUploadFar` descartava o bloco já recebido se o vblank tivesse
terminado. No quadro seguinte o seek e o estágio eram refeitos. Se a
mesma leitura sempre consumisse o vblank disponível, o upload poderia
não progredir.

Agora, após receber o bloco em WRAM, a rotina aguarda vblank com a tela
ligada e só então ativa forced blank para escrever em VRAM. A espera é
limitada a FFFF consultas de HVBJOY. Em caso de timeout retorna C=0 e o
cursor continua parado; após o DMA retorna C=1 e o cursor avança.

Uma leitura lenta pode acrescentar um quadro de latência. A alteração não
promete eliminar todo flicker de uma transferência iniciada perto do fim
do vblank; a prioridade desta rodada é restaurar os tiles sem escrita
durante o display ativo nem repetição indefinida da mesma leitura.

## Verificação

`tools/test_msu_chr_visibility_headless.py` compara os tiles da página
visível de cada lutador na VRAM com os bytes exatos da pose no `.msu`.
Testa Rugal × Leona e Chizuru × Ken, com ataques nos dois lados. Não basta
que o relógio e os estados da luta avancem para esse teste passar.

- Antes da correção: Rugal, primeira verificação, 1702 bytes divergentes
  em uma pose de 2048 bytes. Cópia anterior em
  `build/char_visibility_pre_20261026`.
- Após as duas correções: 960 comparações de páginas visíveis passaram.
- Teste de atraso: uma cópia temporária da ROM executa o DMA MSU→WRAM e
  aguarda sair do vblank antes de retornar à rotina. Assim a escrita final
  obrigatoriamente aguarda outra janela. Outras 960 comparações passaram.
  Esse atraso simulado não faz parte da ROM entregue.
- Vozes MSU: as 21 amostras do Clark passaram na comparação byte a byte.
- HUD: teste das bandas com a barra de vida continuamente suja passou.
- Build PVSnesLib, checksum e verificação estrutural da ROM passaram.

Os resultados são de Snes9x headless. O pacote ainda precisa ser validado
no SD2SNES MKII para confirmar a melhora no console.

Pacote: `kof98-chars-fix-20261026.zip`. Copiar os dois arquivos `.sfc` e
`.msu` do pacote juntos; o `.msu` atual mudou desde os diagnósticos D1–D4.

## Resultado no SD2SNES MKII (26–27/10)

O build descrito acima foi testado no console: os personagens voltaram a
aparecer, mas **com os tiles misturados**. Isso mostrou que o estágio
MSU→WRAM (`DMA -> $2181`, WMDATA) não pode rodar com o display ativo no
SD2SNES, mesmo com a escrita final em VRAM em forced blank. Reduzir demais
o `MSU_POLL_LIMIT` também não é seguro (aborta o seek no meio da leitura e
força re-seeks frequentes).

A correção final mantém o caminho de DMA inteiro em forced blank (build
validado de 24/10) e roda **só a espera de CPU** pelo `MSU_STAT` com a tela
ligada. Se essa espera demorar mais de ~0,78 ms ou o vblank acabar, o setor
já buscado é mantido e a rotina espera o próximo vblank começar, com a tela
ligada, para então fazer os dois DMAs no topo da janela. Nada é descartado
nem re-lido. O teste de visibilidade continua passando (960 páginas
visíveis). Detalhes em `docs/LIFEBAR_MSU_FLICKER_2026-10-26.md`.
