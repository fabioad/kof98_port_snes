# Pisca-pisca na faixa CHALLENGER

O Mesen reproduziu o problema com Daimon × Kyo andando: 15 retomadas de
INIDISP durante linhas visíveis em 600 quadros. O upload começava depois do
retorno do NMI e não verificava se os DMAs e os patches do cenário ainda
cabiam no intervalo restante. A faixa superior já estava sendo desenhada
quando o forced blank terminava.

## Correção

- MainLoop prepara uma cópia estável do OAM da biblioteca e arma somente
  sua própria espera. A apresentação ocorre no hook do NMI antes da leitura
  dos controles; NMIs de atraso e esperas de carga não apresentam buffers
  parcialmente preparados. O caminho de vídeo MSU mantém seu despacho.
- A biblioteca envia o OAM uma vez. A cópia durante a lógica usa MVN; o DMA
  redundante de 544 bytes saiu da apresentação da luta.
- `frame_present.asm` lê o contador de vídeo e só inicia trabalhos que cabem
  no vblank, com margem para a restauração de paleta e registradores.
  A conta de CHR MSU inclui ambos os DMAs e o prefixo do setor alinhado.
- P1/P2 alternam a prioridade; chunks adiados preservam cursor e pose pendente.
  O caminho validado MSU → WRAM → VRAM continua em forced blank, com o seek
  feito durante a lógica. O limite por chunk permanece em 1536 bytes; o
  orçamento usa o contador amostrado antes do cálculo para não adiar
  permanentemente um bloco que cabe no vblank.
- HUD de pausa/lista e repaints completos têm prioridade sobre atores
  congelados. Patches cosméticos do cenário esperam quando falta tempo.
- WRIO bit 7 habilita o latch de contadores; STAT78 reinicia a fase de leitura
  antes do latch. O SNESMOD também lê o contador, portanto não se pode assumir
  a fase low/high anterior.

## Verificação

- `test_mesen_hud_flicker.lua`: cenário 4 (três patches animados), 1200 quadros
  por caso: Daimon × Kyo, Daimon × M. Bison, Kyo × Iori andando e Ryu × Ken
  com ataques, saltos e projéteis. Todos sem writes de INIDISP nas linhas
  visíveis; poses e movimento realmente avançam. Total: 4800 quadros.
- `test_msu_chr_visibility_headless.py`: 960 páginas visíveis comparadas byte
  a byte com o MSU, 52 poses distintas.
- Lista de comandos/pausa pelos dois controles, fechamento e limpeza de VRAM:
  PASS. ORDER SELECT e fluxo de times: PASS. As 59 telas dos endings, incluindo
  retorno ao título: PASS. 308 testes unitários: PASS.
- Logs da rodada final em `build/msu_hud_final_*.log`; os testes de progresso
  MSU também verificam as escritas de INIDISP nas linhas visíveis.

Sob carga alta, um chunk ou um patch cosmético pode esperar pelo quadro
seguinte. A página visível continua coerente e o topo não é apagado para
concluir um upload atrasado.
