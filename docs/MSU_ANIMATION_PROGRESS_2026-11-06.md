# Congelamento de animações MSU

## Causa anterior à alteração do HUD

`MsuStagePrepareFar` reescrevia os quatro bytes de seek em toda tentativa.
Quando o cartão não ficava pronto no limite de polling daquele quadro,
a tentativa seguinte reiniciava a mesma busca. Um dispositivo com latência
maior podia nunca entregar o bloco, mantendo a página/pose visível congelada.
Esse caminho já existe no HEAD anterior às alterações do HUD desta sessão.

## Correção

- O seek tem estado persistente, dono e geometria. A mesma solicitação é
  consultada nos quadros seguintes sem reiniciar a busca. Há recuperação
  limitada a 120 tentativas para dispositivo ausente ou permanentemente ocupado.
- A prioridade alterna entre lutadores após completar uma pose, independentemente
  da paridade do quadro. Uma busca pendente mantém seu dono.
- Blocos contíguos dentro da mesma página MSU de 8 KiB aproveitam a posição
  atual do arquivo. Cruzar a página exige novamente a busca alinhada.
- Vozes aguardam a conclusão do seek de CHR antes de reposicionar o mesmo
  porto de dados. Leituras de voz e transições invalidam a posição guardada.
- Mantidos os dois DMAs em forced blank: MSU → WRAM → VRAM, páginas ocultas
  e publicação da pose somente após completar todos os seus blocos.
- Mantido o chunk de 1536 bytes, com assets regenerados pelo mesmo ABI.
- A apresentação do HUD também foi conferida: o orçamento amostra o contador
  antes de calcular o custo. `RoundVoice` agora desabilita NMI com escrita de
  8 bits, sem apagar acidentalmente o WRIO adjacente e desabilitar esse latch.

## Reprodução e verificação

`tools/test_mesen_msu_progress.lua` injeta ocupado no registro MSU por um
número configurável de quadros após cada seek. Os dois controles humanos
movimentam os personagens. O teste verifica avanço de **metadados publicados**,
compara byte a byte cada página visível com o arquivo MSU e detecta forced blank
terminando nas linhas visíveis. Esperas intencionais sem upload pendente não
são contadas como falha de streaming.

Em 360 quadros, Daimon × M. Bison, atraso de 2 quadros por seek:

- Caminho anterior: 1/1 poses publicadas, 359/359 quadros de espera pendente,
  181 seeks; FAIL por congelamento.
- Corrigido: 26/27 poses publicadas, maior espera de 15/17 quadros,
  63 seeks; PASS, sem diferenças nos tiles e sem retomada tardia do vídeo.

Outros casos corrigidos, todos PASS:

- Sem atraso: 31/36 poses; atraso de 4 quadros: 20/21 poses.
- MSU × ROM: 22/22 poses; ROM × MSU: 27/24 poses, atraso de 2 quadros.
- Ralf × Clark: 30/30 poses, maior espera de 22/23 quadros, atraso de 2 quadros.
- HUD no cenário 4, 1200 quadros cada: Daimon × Kyo e Kyo × Iori andando,
  Ryu × Ken atacando; ambos os controles ativos. Zero retomadas de INIDISP
  nas linhas visíveis e zero quadros visíveis em blank.
- Snes9x: 960 páginas MSU comparadas, 52 poses distintas; 21 vozes alinhadas;
  ORDER SELECT, troca de membro/paleta, pausa/lista pelos dois controles,
  59 endings e retorno ao título. Todos PASS.
- 308 testes unitários: PASS.

Logs de regressão: `build/msu_animation_*.log`, `build/msu_active*.log` e
`build/msu_hud_final_*.log`. O teste de latência usa Mesen; não é uma medição
no SNES real. Para testar no SD2SNES, atualizar juntos `kof98-snes.sfc` e
`kof98-snes.msu`, pois o layout dos assets foi regenerado nesta sessão.
