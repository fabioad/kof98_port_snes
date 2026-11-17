# Mr. Karate

Variante oculta de Robert, com os sprites mascarados de
`assets/robert_mrkarate/MrKarate-KOF98` e o moveset nativo de Robert.

- Exige MSU disponível. Segure L+R sobre Robert e confirme com A.
- Na pose deitado no chão, a máscara Tengu fica apoiada na altura do peito
  em vez de sumir com o enquadramento horizontal.
- Quando escolhido por P1 ou P2, o Mr. Karate entra no sorteio normal de
  stages como qualquer personagem; o stage 5 fica reservado ao confronto de
  boss da rota secreta.
- Fica fora dos sorteios de adversários, inclusive do roster de oponentes
  do Survivor e das demonstrações. Nas lutas CPU vs CPU, qualquer seleção residual é substituída por Robert.
- Especiais terrestres iniciados no ar executam a 16 px do chão. A altura do
  pulo não afasta mais os hitboxes nem o ponto de saída dos projéteis, então
  projéteis e golpes de contato acertam adversários em pé ou agachados mesmo
  quando o comando é feito no ápice de um pulo alto.
- Robert normal usa `Robert.snd` (vozes originais). Só o Mr. Karate usa o
  banco processado `MrKarate.snd`, com as vozes mais graves e o eco. A pasta
  compartilhada tem os dois arquivos, então a resolução do build não pode
  depender da ordem alfabética.
- Apenas Single Play e Team Play recebem a rota secreta de boss. Chegue
  ao confronto final sem perder rounds, ou segure L+R+A durante
  a passagem para esse confronto. Continues não apagam derrotas anteriores.
- Quando a CPU controla o Mr. Karate, ele usa sempre o nível efetivo 9,
  independentemente do LEVEL escolhido em OPTIONS (o HUD mostra LEVEL 8).
  A IA mantém a própria tabela `mrkarateAiTab` e prefere contra-atacar uma
  investida do oponente em vez de só bloquear. O id 53 está dentro de
  `NROSTER`, então não cai mais na tabela genérica do Kyo.
- O quadro de Rugal derrotado no chão, centralizado, permanece por 180
  frames com a música do boss;
  o volume cai de 240 a 0 em 60 frames. A luta é reconstruída com Crystal
  e Mr. Karate entra por cima da tela antes de sua animação de intro.
- Single Play exige duas vitórias. Team Play usa duas vidas consecutivas
  do boss, preservando a eliminação e recuperação dos membros do jogador.
- A vitória abre as cinco telas de ending1 e depois as treze telas da
  ending Survivor. O modo Survivor conserva sua rota e seu final anteriores.

Compile com `make -f Makefile.pvsnes verify`. A ROM e o arquivo MSU precisam
ser usados juntos, pois adicionar a variante altera os offsets dos sprites.

Regressão: `python3 tools/test_mrkarate_headless.py` e
`python3 tools/test_mrkarate_ai_headless.py`. Capturas do emulador em
`build/mrkarate_regression/`. O estado privado ocupa $7E:F1C0–F1C9; código e
quadro estático usam a metade baixa do banco 122, reservada no empacotador.
