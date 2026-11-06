# TEAM PLAY — ORDER SELECT (06/11/2026)

Implementado antes do primeiro confronto e antes de cada novo stage do TEAM PLAY. Cada jogador humano escolhe a sequência dos mesmos três lutadores do seu trio. O primeiro entra no round inicial; após uma eliminação, entram o segundo e o terceiro na ordem definida. Não há nova escolha entre rounds/membros do mesmo confronto.

## Controles

- Direcionais: navegam entre os lutadores ainda não posicionados.
- A, X ou Y: escolhem a próxima posição (1, 2 e 3).
- B: desfaz a última escolha enquanto a seleção ainda está aberta.
- START: preserva o prefixo escolhido e completa as posições restantes seguindo a ordem atual do trio.
- A luta começa após todos os humanos confirmarem seus três lutadores. A CPU mantém a ordem e não exige entrada de controle. Se ambos os lados são CPU, a tela é pulada.

A tela mostra os retratos, nomes, números da ordem, cursor e estados CHOOSE/READY/FIXED. Em TEAM PLAY com dois humanos, a escolha de cada lado é independente. Também funciona quando P2 vence o confronto humano inicial e passa a carregar a campanha pelo lado direito.

## Escopo

- TEAM PLAY somente (`G_MODE=2`). TEAM VS, SINGLE PLAY, SINGLE VS, SURVIVOR e PRACTICE mantêm o fluxo anterior.
- A escolha reaparece no próximo confronto e no chefe, inclusive quando a equipe CPU tem apenas dois membros.
- CONTINUE, SELECT FIGHTER e a entrada de outro jogador preservam seus fluxos de campanha e passam pela nova escolha antes do confronto reiniciado.
- Os personagens do trio não são trocados; apenas as posições são reorganizadas.

## Implementação

- `src/engine/team_order.asm`: estado de tela 15, seleção por pad, cópia confirmada das ordens e apresentação própria em BG3.
- WRAM reservada em `$7E:F180..F1BF`, fora dos buffers existentes. A ordem original fica em uma cópia até a confirmação dos humanos.
- O início da luta intercepta apenas confrontos novos do TEAM PLAY; `T_SWAP` e os índices dos membros impedem a abertura entre rounds.
- A seleção inicial do TEAM PLAY agora entrega o controle a P2 para escolher seu trio quando esse jogador entrou antes de P1 terminar.
- Os retratos usam os gráficos/paletas 2bpp já existentes. A tela de luta restaura o layout normal de VRAM/CGRAM.
- Helpers próximos foram mantidos no mesmo banco da luta, na janela livre a partir de `$7040`, sem ultrapassar as seções existentes. A lógica da nova tela fica no banco 64.

## Validação

ROM instalada: `4641e765b6361e9201220fe5e4d4562dddf5534afe44496aff0ab2817cc1f429`. Checksum: `$7FF3`. Verificador `verify_pvsnes_rom.py`: OK.

- `python3 tools/test_team_order_headless.py`: campanha completa de sete stages; CPU fixa; desfazer; entrada inicial escolhida; segundo/terceiro membros em ambos os lados; entradas simultâneas de P1/P2; espera pelos dois humanos; P2 vencedor iniciando a rota CPU; apenas P2 humano; ambos CPU; exclusão dos outros modos.
- `test_team_vs_start_headless.py`: TEAM VS permanece sem ORDER SELECT.
- `test_midfight_join_headless.py`: entrada de P1/P2 durante a luta, em SINGLE PLAY e TEAM PLAY.
- `test_team_confrontation_reset_headless.py`: novo confronto com HP restaurado e sem T_SWAP residual.
- `test_team_swap_headless.py` e `test_team_swap_palette_headless.py`: troca de membros e paletas.
- `test_team_continue_headless.py`: CONTINUE e SELECT FIGHTER.
- `test_team_banner_headless.py`: vitória/quotes dos dois lados em TEAM PLAY e TEAM VS.
- `test_options_headless.py`: texto, configurações, som e acesso aos seis modos preservados.
- `pytest -q tools/tests`: **301 testes passaram**, além de **5.069 subtestes**.

Os testes executam a ROM no Snes9x com entradas reais de controle. Usam RAM para preparar cursores e provocar KOs, sem iniciar a tela ORDER SELECT por escrita no estado do jogo.

## Capturas

- [Dois jogadores escolhendo ordens diferentes](../build/team_order/two_players_order.png).
- [Jogador humano e CPU com ordem fixa](../build/team_order/order_cpu.png).
- [Primeiro lutador escolhido entrando na luta](../build/team_order/ordered_first_fight.png).

Reabra `kof98-snes.sfc` no emulador para carregar esta versão.
