# Mr. Karate

Variante oculta de Robert, com os sprites mascarados de
`assets/robert_mrkarate/MrKarate-KOF98` e o moveset nativo de Robert.

- Exige MSU disponível. Segure L+R sobre Robert e confirme com A.
- Todos os combates com a variante usam o stage 5, inclusive quando ela
  integra um trio e ainda não entrou na luta.
- Fica fora dos sorteios de adversários, inclusive do roster de oponentes
  do Survivor e das demonstrações. Nas lutas CPU vs CPU, qualquer seleção residual é substituída por Robert.
- Apenas Single Play e Team Play recebem a rota secreta de boss. Chegue
  ao confronto final sem perder rounds, ou segure L+R+A durante
  a passagem para esse confronto. Continues não apagam derrotas anteriores.
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

Regressão: `python3 tools/test_mrkarate_headless.py`. Capturas do emulador em
`build/mrkarate_regression/`. O estado privado ocupa $7E:F1C0–F1C9; código e
quadro estático usam a metade baixa do banco 122, reservada no empacotador.
