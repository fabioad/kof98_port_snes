# KOF '98 SNES — versão 1.1.2 (09/11/2026)

Esta rodada adiciona três personagens **exclusivos do pacote MSU-1** — Kasumi,
Duck King e Yuki — com normais, especiais, supers, MAX, win quotes nos quatro
idiomas e Command List. As mecânicas, o perfil 0.90 e o comportamento do
elenco anterior foram preservados.

## Personagens novos (MSU-1)

- **Kasumi Todoh** — 12 especiais e 5 supers/MAX:
  - Messin Mutou / Sassho Inshu (HCF + A/B)
  - Tatsumaki Souda (HCBF + Y/B)
  - Kasane Ate fraco/forte (QCF + Y/X)
  - Hakuzan Toh fraco/forte (QCB + B/A)
  - Taikuu Kasane Ate (DP + Y/X)
  - Rai Houkou fraco/forte (DP + B/A)
  - Chou Kasane Ate, MAX Chou Kasane Ate
  - Shingan: Kazura Otoshi e MAX Shingan
- **Duck King** — 13 especiais e 5 supers/MAX:
  - Head Spin Attack fraco/forte (QCF + Y/X)
  - Flying Spin Attack, no ar (QCB + Y/X)
  - Dancing Dive fraco/forte (QCB + B/A)
  - Break Storm fraco/forte (DP + B/A)
  - Diving Punisher, Rolling Punisher, Dancing Caliber
  - Break Spiral, Beat Rush, Highbound Spiral, Break Hurricane e
    Super Pomping Machine
- **Yuki Kushinada** — 7 especiais e 5 supers/MAX:
  - Yuki-Chan no Kaban no Nakami (DF + Y)
  - Otome no Sakebi (DF + B)
  - Valting Over (DP + Y)
  - Kaban Barrier (F,D,B + B)
  - Yuki-Chan Furimawasu (D,B + Y)
  - Hyakuretsu Terekakushi (Y repetido)
  - Sabaori 2000 (HCB + Y)
  - Yuki-Chan no Trap, Naku Ko wa Tsuyoi, suas versões MAX e
    Ai no Kusanagi Dai Koushin

Todos usam o padrão de pad **Y=WP, X=SP, B=WK, A=SK**, com **L=esquiva** e
**R=blowback**. Cada personagem recebeu uma **Command List** completa, com
nomes legíveis para os golpes e os comandos no formato SNES.

## Win quotes

- Quotes vindas de:
  - `https://snk.fandom.com/wiki/Kasumi_Todoh/Quotes`
  - `https://snk.fandom.com/wiki/Duck_King/Quotes`
  - `https://snk.fandom.com/wiki/Yuki_(KOF)/Quotes`
- Traduzidas para **inglês, português-BR, espanhol e francês**, respeitando o
  limite de duas linhas de 30 glifos do HUD.
- `tools/tests/test_quotes.py` valida contagem, charset, quebra de linha e as
  tabelas geradas.

## Tela de seleção

- Três células novas **abaixo de Shingo, Rugal e Eiji**, alinhadas à grade
  existente (x=96/118/140, y=168–190). A posição anterior estava deslocada
  4 px à esquerda e 2 px acima, o que deixava as bordas dos quadrados grossas
  e desalinhadas.
- Os ícones 50×50 dos packs kofa (Chin, King, Chizuru, Chang, Choi,
  Blue Mary, Billy, Lucky, Heavy D, Brian, Chun-Li e **Duck King**) tinham
  fundo preto opaco. O build agora remove o fundo escuro conectado às bordas
  e recorta o retrato, eliminando os quadrados pretos ao redor dos rostos.
- Os retratos 24×24 do HUD e os 32×32 do ORDER SELECT usam o mesmo recorte,
  mantendo a seleção e o HUD consistentes.
- A tela passou a usar molduras nativas de **1 px** e o fundo outline do
  screenpack, com as cores de borda fixadas nas paletas para não engrossar
  as bordas dos quadrados.

## Paleta da Yuki

- Os cels de corpo da Yuki usavam o banco de paleta **2** do SFF, uma variante
  escura. O ícone e a paleta canônica estão no banco **0** (cabelo castanho,
  uniforme branco/azul).
- O build remapeia somente o banco 2 para o banco 0; sprites de efeito
  continuam com suas próprias paletas. O resultado em jogo agora bate com o
  retrato oficial da personagem.

## Layout de ROM

- `EndData19` foi movido para o banco 54 (`$8000`) para liberar o banco 46
  ocupado pela arte maior da seleção 1.1.2.
- A tabela de cancelamentos foi deduplicada: 53 personagens geravam 50 linhas
  únicas (Ken/Ryu e as variantes Kyo compartilham a mesma linha). Isso mantém
  `CancelData` abaixo do helper fixo `OamCache` em `$0A00`, sem mover código.

## Correções da revisão

- **Duck King:** o evade para trás agora usa o estado 701 do source (`x=-5`);
  o taunt foi movido para o estado 195, que era o verdadeiro taunt. As três
  esquivas (L, L+B, L+F) entram em 69/94/95.
- **Yuki:** a personagem não tem estados de esquiva no CNS original. As três
  esquivas foram sintetizadas com os clipes de corrida/back-hop, com
  velocidade de entrada no sentido correto e sem loop infinito.
- **Kasumi:** os especiais e supers que usavam helpers (Kasane Ate,
  Chou Kasane Ate) agora lançam projéteis nativos com a arte dos helpers
  1020/3020, causando dano de verdade. Os slots 87–89 (MAX e os counters
  Shingan) voltaram ao elenco; os counters 88/89 continuam usando a RevTab.
- **Recuperação do super da Kasumi:** o clipe original segurava a última pose
  por 255 ticks. O build limita o clipe a cinco frames e reduz o hold, então
  ela volta a agir em ~0,8 s em vez de mais de 4 s.
- Prioridade de comandos: os supers de QCF duplo são testados antes do
  especial de QCF simples, evitando que o comando seja engolido pelo golpe
  curto.

## Validação

- `make -f Makefile.pvsnes`: **OK**.
- `python3 -m unittest discover -s tools/tests`: **311 testes OK**.
- `tools/test_roster.py --launch --only 48,0,49,0,50,0`: **3/3 confrontos OK**
  (Kasumi, Duck King e Yuki carregam, animam e entram em luta).
- Teste em emulador: Duck e Yuki entram em 69/94/95 com L, L+B e L+F.
- Kasumi: QCF+X causou 18 de dano, QCB+A causou 24 e o super QCFx2+X
  causou 90 de dano e recuperou em ~0,77 s.
- `make -f Makefile.pvsnes verify`: **OK**, checksum **`$3456`**.

## Build

- ROM: `kof98-snes.sfc` (8 MiB)
  - SHA-256 `5d928aa292ba098ab521002126219ed8db18051ac5b08bbaff7ae28ba8f2a717`
- MSU: `kof98-snes.msu` (54.083.072 bytes)
  - SHA-256 `3d134d268c7f3f46ed36b6b8d080639247e0f0e7ded27143bc519c4803b4d681`

> Os três personagens novos são **MSU-only**. Copie **ROM e MSU juntos** e
> reabra o par no emulador.
