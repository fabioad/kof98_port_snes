# Robert / Mr. Karate

Carregue `Robert-Mr-Karate.def`. O DEF original do Robert permanece disponível.

A variante usa `Robert-Mr-Karate.sff`, `Robert-Mr-Karate.snd` e arquivos de estados, comandos e animações com o prefixo `Robert-Mr-Karate-`. Não depende da pasta de preparação `MrKarate-KOF98`.

- Máscaras vermelhas aplicadas aos sprites do Robert e aos portraits de seleção/HUD. O portrait grande tem uma máscara opaca cobrindo todo o rosto.
- Camisa cinza claro na paleta padrão e no portrait grande. As outras paletas mantêm as cores originais da roupa e recebem as cores reservadas da máscara.
- Comandos originais preservados. Especiais terrestres também podem começar durante o pulo; o personagem fica suspenso durante a execução e volta a cair ao terminar. O chute de mergulho continua usando seu movimento aéreo original.
- Ao conectar um especial, segue uma sequência de 5 impactos reais, totalizando 60 pontos de dano absoluto.
- Ao conectar um super, segue uma sequência de 50 impactos reais, totalizando `floor(LifeMax do adversário / 3)` de dano absoluto. Contra 1.000 de vida: 333 de dano. O dano é distribuído pelos impactos, sem depender da defesa do alvo.
- A sequência só começa depois que o primeiro golpe acerta. Esquiva, alcance e defesa continuam relevantes. As sequências usam poses de soco e chute de Robert, mantendo as animações iniciais dos golpes.
- Golpes de projétil disparam uma rajada simultânea com três membros. O primeiro membro que acerta inicia a sequência; os outros são removidos para que a mesma rajada não multiplique o limite de dano.
- As 20 amostras do grupo de voz 10 foram processadas com tom mais grave e eco. Os IDs e as outras 57 amostras do SND foram preservados.

## Testar

A instalação local está em `../ikemen-test`. Execute `../testar_mr_karate.sh` para abrir uma luta contra Kung Fu Man com três barras de energia.

Para adicionar a outra instalação de MUGEN/Ikemen GO, copie a pasta `Robert-KOF98` para `chars` e acrescente em `[Characters]` de `select.def`:

    Robert-KOF98/Robert-Mr-Karate.def

Consulte `txt/ReadMe(ENG).txt` para a lista original de comandos. Exemplos, olhando para a direita:

- Ryuugeki Ken: baixo, diagonal baixo/frente, frente + x ou y.
- Ryuu Ga: frente, baixo, diagonal baixo/frente + x ou y.
- Hien Shippuu Kyaku: frente, diagonal baixo/frente, baixo, diagonal baixo/trás, trás + a ou b.
- Haoh Shoukou Ken: frente, trás, diagonal baixo/trás, baixo, diagonal baixo/frente, frente + x ou y.
- Ryuko Ranbu: baixo, diagonal baixo/frente, frente, diagonal baixo/frente, baixo, diagonal baixo/trás, trás + x ou y.

## Créditos e reconstrução

Personagem original: ikaruga. Gráficos e áudio originais: SNK e os créditos do README original. Máscara de referência: GIF `Mr._Karate_Ryuuko_Ranbu_SVC.gif`, fornecido pelo usuário.

Os scripts de reconstrução ficam em `../tools`; execute `../tools/rebuild.sh` com Python, Pillow, NumPy e FFmpeg instalados. O leitor SFF está incluído. Os arquivos originais de Robert são a fonte da reconstrução e devem ser mantidos.

Os testes foram executados no Ikemen GO Linux. Não foi executado o MUGEN para Windows. O motor emite alguns avisos de compatibilidade já presentes no personagem original.

## Validação executada

27 execuções automatizadas no motor, incluindo versões aéreas: 19 conectaram e respeitaram as contagens e o dano; 8 não atingiram o alvo na distância/altura usada pelo teste. Cinco supers conectados terminaram com 50 impactos e 333 de dano. As rajadas de três projéteis foram confirmadas no chão e no ar. A soltura e a queda do adversário foram verificadas após os combos. Os testes acionam os estados dos golpes diretamente; não simulam todas as sequências de teclas do CMD.

Os registros estão em `../evidencias/testes_motor.csv` e `../evidencias/testes_motor.json`. Os 77 WAVs do novo SND e as dependências do DEF também foram validados.
