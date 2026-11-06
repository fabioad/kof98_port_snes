# Especiais e supers — auditoria funcional de 06/11/2026

**Ainda há golpes com preparação ligada e complemento ofensivo ausente.**
Há também comandos que não alcançaram o destino esperado e contra-ataques
que deixam o adversário marcado como agarrado após a recuperação.
Esta etapa identifica problemas; não altera golpes nem gera build.

O critério respeita as adaptações do autor: animação diferente, menos efeitos,
menos fases e dano ajustado podem ser decisões do port. Uma diferença em
relação ao MUGEN, sozinha, não foi considerada defeito.

## Cobertura e interpretação

- 50 personagens; **1.161 regras distintas de entrada**, com 915 destinos
  nativos. Variantes de botão/direção podem compartilhar o mesmo golpe;
  esses números **não representam 1.161 golpes diferentes**. Há também
  normais de comando e alguns agarrões importados nessas tabelas.
- Entradas reais de pad no Snes9x headless, observando states, vida,
  captura/soltura, recuperação e avanço do relógio. Nenhum ataque foi
  iniciado escrevendo diretamente seu state na RAM.
- Padrão físico: Y=WP, X=SP, B=WK, A=SK, L=esquiva,
  L+trás/frente=esquivas direcionais, R=blowback.
- Retestes variaram distância, cadência, direção junto do botão final e
  poder disponível. Cargas foram medidas em **ticks do jogo**, pois uma
  chamada de emulação não equivale sempre a um tick de luta. Entradas
  repetidas receberam soltura entre os presses. Também houve retestes
  aéreos para os candidatos pertinentes e envio de complementos ligados
  na `TransTab`.
- Adversário base: Kyo, sem CPU. Contra-ataques receberam um soco do
  adversário. Os testes ajustam posição/vida/poder; testes aéreos também
  ajustam altura após um salto real. Não são uma partida jogada livremente.
- Resultado bruto consolidado: **904 entradas com dano e recuperação;
  211 com 0–2 HP para revisão; 34 sem alcançar o destino esperado;
  7 com flag de captura residual; 5 condicionais**. Os 211 incluem ações
  de suporte, fintas e deslocamentos; não são 211 defeitos confirmados.
- Nenhum caso foi classificado como relógio parado, recuperação excedida
  sem flag residual ou cura indevida do adversário nesta amostra.
  Isso não certifica todos os confrontos, lados, modos ou efeitos gráficos.

## Falha de captura confirmada — prioridade de estabilidade

Os dois personagens retornam ao state 0, mas `F_GRAB` do adversário fica
em 1. Um agarrão comum tentado depois falha. Repetindo a mesma situação e
limpando **somente essa flag, para diagnóstico**, o agarrão volta a capturar.
Não foi aplicada essa limpeza ao jogo.

- **Heidern:** Killing Bringer, states MUGEN **1400/1410**; 0 HP.
- **Takuma:** contra-ataque Mouko Burai Gan, **1700**, dois comandos; 42 HP,
  mas deixa a flag residual.
- **Daimon:** Nekko Gaeshi, **1400**; 0 HP.
- **Blue Mary:** contra-ataque **1500**; 95 HP, com flag residual.
- **Geese:** contra-ataque **1401**; 38 HP, com flag residual.

São cinco personagens e sete regras de entrada. O defeito é o estado
residual, inclusive nos golpes que causam dano.

## Preparações e capturas sem complemento ofensivo

Nestes exemplos o comando entrou, o dano foi 0–2 HP e a análise das
tabelas congeladas encontrou ausência da fase ofensiva ou do follow-up
de captura necessário. A implementação pode continuar adaptada: o ponto
é dar ao golpe um ataque/dano e uma finalização coerentes no motor nativo.
Os números abaixo são **states MUGEN**, não slots SNES.

- **Shingo — Kakehourin 3000/3010/MAX 3050:** 0 HP; preparação sem
  continuação ofensiva nativa. Os destinos 3001/3011/3051 não estão ligados.
- **Saisyu — Orochinagi 3000/3010/MAX 3050:** 0 HP; Kamukakari
  **1200/1210:** 0 HP; MAX Tsumugari **3150:** somente 1 HP.
- **Heidern — Final Bringer 3000/3010/MAX 3050:** 0 HP;
  Storm Bringer **1300:** captura e termina com 1 HP, sem 1310 ligado
  como fase do atacante; Neck Rolling **1200/1210:** 0 HP.
- **Rugal — Dead End Screamer 3100/3110/MAX 3150:** 0–1 HP; faltam
  fases do atacante como 3102/3152. God Press **1400/1410** e Gigantic
  Pressure **3000/3010** deram somente 2 HP: a captura não se completa
  com o impacto esperado. Dark Barrier 1300/1310 é tratado separadamente.
- **Leona — Rebel Spark 3100/3150:** 0 HP; Grateful Dead **3300:**
  captura e somente 1 HP; X-Caliber **1200/1201** e Ice Slasher
  **1400/1401:** 0 HP, sem ataque nativo alcançável.
- **Daimon — MAX Jigoku Gokuraku Otoshi 3050**, Arashi no Yama
  **3100**, Tenchi Gaeshi **1600**, Kirikabu Gaeshi **1300** e Chou
  Oosotogari **1700:** captura/entrada com somente 1 HP, sem as respectivas
  fases ofensivas completas. Ura Nage **1500/1510:** 0 HP.
- **Shermie — Flash 2200/2250:** captura com 1 HP, sem 2210/2260;
  Carnival **2150:** 1 HP, sem 2160. Clutch **1400/1450**, Shajitsu
  **7000/7050** e SDM Shukumei **8050:** 0 HP e sem rota ofensiva nativa.
- **King — Trap Shot 1400/1450:** captura com 1 HP, sem 1410;
  Mirage Kick **1300/1350:** inicia o movimento, mas não chega ao ataque.
- **Brian — American Supernova 3000/3050:** captura, percorre a cadeia
  disponível e termina com somente 1 HP.
- **Athena — Psychic Grasp 1070:** captura com 1 HP, sem complemento
  ofensivo independente. Refletor e teletransporte não entram nesta falha.
- **Mr. Big — Blaster Wave 3000/3010:** 0 HP, sem tiro/ataque nativo;
  a variante MAX 3050 acertou. Spinning Spear **3200/3210:** somente
  1 HP; Spinning Lancer **1300/1310:** 0 HP.
- **Chris — Hunting Air 1100/1150, Glider Stamp 1200/1250, Shooting
  Dancer Thrust 1400/1450, Kagami 7100/7150 e SDMs 2150, 2250,
  8150/8155:** entram na preparação, mas não têm uma fase ofensiva
  alcançável nas tabelas verificadas. Scramble Dash e transformação
  ficam fora desta conclusão.

## Inventário dos 50 personagens

`Sem impacto` significa 0–2 HP nas condições testadas. Quando há hitbox,
projétil ou condição especial, a causa ainda pode ser alcance, altura,
tempo ou contexto. `Entrada pendente` significa que os comandos testados
não alcançaram aquele destino; não prova sozinho que seja impossível
acioná-lo em qualquer contexto. Esta distinção evita desfazer adaptações.

1. **Iori:** sem rota ofensiva em **1501/1511, 3200/3210** (0 HP).
   Entradas pendentes **3050** e Kuzukaze **1400**. Nos retestes de 3050,
   outro super, slot 107, consumiu a entrada.
2. **Kyo:** 36/36 regras com dano e recuperação; nenhuma falha nova
   detectada nesta varredura.
3. **Shingo:** Kakehourin detalhado acima; MAX Burning Shingo **3150**
   também ficou em 0 HP, embora tenha ataque na tabela: revisar colisão/tempo.
4. **Rugal:** falhas detalhadas acima; Excursion **3200/3210/3250** sem
   impacto apesar de possuir ataque nativo. Entrada MAX **3050** pendente;
   surgiram outros especiais, inclusive Beads. **1300/1310** são refletores.
5. **Omega Rugal:** sem rota ofensiva nos candidatos **1020/1025, 1070,
   1085, 1090, 2400, 2600, 2700, 2800, 3000, 6000**; 0–1 HP.
   Rever a função de cada variante antes de escolher a adaptação.
   Entradas **2899/7200** pendentes. **2000/2002** são Dark Barrier:
   0 HP contra oponente parado não comprova falha de reflexão.
6. **Saisyu:** seis destinos com preparação/ataque incompleto, listados acima.
7. **Heidern:** Final/Storm Bringer e Neck Rolling incompletos; Killing
   Bringer deixa flag de captura, conforme prova específica.
8. **Takuma:** flag após **1700**; Ryuuko Ranbu **3105** não entrou em
   dois comandos, sendo substituído por outros ataques nos retestes.
9. **Clark:** Gatling Attack **1100/1110**, 0 HP e sem fase ofensiva nativa.
10. **Ralf:** **440/441** ficaram em 1/0 HP, apesar de ataque nativo.
    São entradas de normal de comando importadas nesta faixa; revisar
    colisão separadamente, sem contá-las como dois supers ausentes.
11. **Leona:** sete destinos incompletos, detalhados acima.
12. **Mature:** **1100, 1300/1320, 1420** sem impacto e sem rota
    ofensiva nativa. Inclui Metal Massacre B e Despair.
13. **Vice:** Withering Surface **3000/3100/3200**, 0 HP e sem rota
    ofensiva nativa; revisar a ligação da captura/finalização.
14. **Benimaru:** **1100/1110**, 0 HP nos contextos testados, mas há
    projétil nativo: revisão de trajetória/colisão, sem concluir falta de tiro.
15. **Daimon:** falhas detalhadas acima; **3000/3010/3160** também ficaram
    em 0–1 HP apesar de haver nós ofensivos na cadeia. **1200** requer
    revisão de captura antiaérea. **1100/1110** são evasões e **1010**
    é finta de Jiraishin; não exigir dano dessas ações.
16. **Terry:** 28/28 com dano e recuperação; nenhuma falha nova detectada.
17. **Andy:** 21/21 com dano e recuperação; nenhuma falha nova detectada.
18. **Joe:** entrada **1000** pendente, com outro especial consumindo
    o comando; **1410** sem impacto, mas possui ataque nativo.
19. **Ryo:** **1510, 2000/2010** sem impacto, com ataque nativo;
    revisar altura, alcance e sequência.
20. **Robert:** entradas de supers **3250/3260** pendentes; surgiram
    os ataques dos slots 66/68 em seu lugar.
21. **Yuri:** **431** sem impacto em duas regras; possui ataque nativo.
    Os destinos aéreos **58/59** acertaram no reteste de contexto.
22. **Athena:** Psychic Grasp incompleto; **1040/1050** são refletores,
    **1060/1065** teletransportes. Não classificados como ataques sem dano.
23. **Kensou:** 27 regras ofensivas acertaram; **2000/2050** são ações
    de comida/suporte. Dano zero dessas três entradas não é falha ofensiva.
24. **Chin:** captura **1950** termina com 1 HP e sem rota ofensiva;
    **1205** sem impacto, mas possui ataque. Entradas **1460/1461/1500**
    pendentes, inclusive após retestar os taps de D,D.
25. **King:** Mirage Kick e Trap Shot incompletos, detalhados acima.
26. **Mai:** **1000/1001/1010** sem impacto e sem rota ofensiva nativa;
    revisar a conversão das etapas/Helpers. **1043** sem impacto, com
    ataque nativo. Não inferir falta de complemento apenas pela animação.
27. **Chizuru:** 18 regras com dano; duas de contra-ataque condicionais.
    Não houve prova suficiente de falha nova nos contra-ataques.
28. **Kim:** **1200** termina em 1 HP sem rota ofensiva;
    supers **3100/3110/3120** sem impacto apesar de ataque nativo.
    Entradas **1000/1010, 1400/1410, 1500/1510** pendentes; as quatro
    primeiras têm combinação de postura/direção que precisa ser revista.
29. **Chang:** giro **1000/1010**, captura **1300** (1 HP, sem 1310),
    **1350** e hidden **3500** sem rota ofensiva completa. Confirmar
    quais fases devem ser comandos diretos e quais só continuação.
30. **Choi:** **1300/1310, 3050/3060** sem impacto e sem rota ofensiva;
    entrada **3000** pendente.
31. **Yashiro:** **1200/1210, 2000/2100, 3000/3010, 3500** sem rota
    ofensiva; 0–1 HP. Inclui Sledge Hammer e Million Bash Stream.
    Complementos opcionais de Jet Counter exigem decisão separada.
32. **Shermie:** Flash/Carnival e demais destinos detalhados acima.
    **2000** é transformação; dano zero não é defeito desse comando.
33. **Chris:** ataques incompletos detalhados acima. **1000/1050** são
    Scramble Dash e **2000** transformação; não exigir dano deles.
34. **Yamazaki:** Snake Arms **1000/1010/1020**, 0 HP e sem rota
    ofensiva ligada. Os estados de segurar/soltar precisam de adaptação
    funcional; não é necessário reproduzir todas as ramificações do MUGEN.
35. **Blue Mary:** flag residual após **1500**. Spider **1205** captura
    com somente 1 HP e sem complemento ofensivo; outro counter é condicional.
36. **Billy:** Power Charge **3100** entra, mas fica sem ataque nativo;
    entradas **1520, 1600/1610, 1800/1850** pendentes (seis regras).
    **1510** é fase de pouso, não um ataque independente. **3000/3020**
    são holds de agarrão importados como comandos nessa faixa, com 1 HP;
    não confundir esses IDs com supers ofensivos novos. Um counter é condicional.
37. **Lucky:** Death Bound **2900/3000**, 0 HP e sem ataque nativo;
    **2600** sem impacto, embora tenha ataque. Entradas **1050,
    3200/3300** pendentes, com colisões observadas com Shoot.
    **1000/1010** são Fast Break, deslocamento sem exigência de dano.
38. **Heavy D!:** entradas **1900/1950** pendentes, inclusive com soltura
    dos taps; **1250** sem impacto, mas possui ataque nativo.
39. **Brian:** American Supernova incompleto; supers novos da família
    **3300** acertaram nas regras verificadas.
40. **Geese:** flag residual em **1401**; **1300/1310** (Hishou
    Nichirinzan) sem impacto e sem fase ofensiva nativa. Entrada **1050**
    pendente, com outro ataque no lugar. Outro counter é condicional.
41. **Krauser:** **1210** (Kaiser Duel Sobat forte) sem impacto e sem
    rota ofensiva nativa, em duas regras; demais 23 entradas acertaram.
42. **Mr. Big:** Blaster Wave, Spinning Spear e Lancer detalhados acima.
43. **Eiji:** Tenmakyaku **1400/1410**, 0 HP e sem ataque nativo.
    **1200/1210** são refletores; **1500/1510**, teletransportes.
44. **Vega:** comandos de carga acertaram após medir o tempo corretamente.
    **1300** sem impacto apesar de ataque nativo: revisar interação
    aérea/mergulho. **1400/1410/1420/1430** são warps, sem exigência de dano.
45. **Ryu:** 16/16 com dano e recuperação; nenhuma falha nova detectada.
46. **Ken:** 16/16 com dano e recuperação; nenhuma falha nova detectada.
    O prolongamento opcional de chute **1330** não está ligado;
    isso sozinho não invalida os ataques adaptados que já acertam.
47. **Chun-Li:** Hyakuretsu Kyaku **1100** não entrou com os quatro
    presses da regra compilada; revisar reconhecimento durante o normal.
    Tenshin Enbu **1500** termina com 1 HP e sem continuação ofensiva nativa.
48. **Sakura:** 24/24 com dano e recuperação. Regressão específica passou:
    agarrão e posicionamento, Shinkuu Hadouken (72 HP), complemento do
    Otoshi (6 HP), Shun Goku Satsu (15 hits, 51 HP, blackout/finalização)
    e SGS no Practice sem congelar o rastreador de comandos.
49. **Kyo Nests:** 36/36 com dano e recuperação; cargas também retestadas.
50. **Kyo Ash:** 36/36 com dano e recuperação; cargas também retestadas.

## Evidência, reprodução e limites

- ROM existente, congelada em
  `build/specials_audit_20261106/4d757e64bdfc/` junto com MSU e tabelas.
  SHA-256 da ROM:
  `4d757e64bdfccbb715d94977f25cd9a754dbb0ad22b71cdc317ba70973ce7eea`.
- Essa ROM é anterior às correções de agarrões comuns registradas em
  [NORMAL_THROWS_FIX_2026-11-06.md](NORMAL_THROWS_FIX_2026-11-06.md).
  O fonte atualizado dos agarrões **não foi compilado**. Especial que
  reutilize slot de agarrão precisa de follow-up próprio; exemplos:
  Athena 1070 e Leona 3300. Não se deve reaproveitar cegamente o slot 75.
- [Resumo e casos por comando](audits/specials_supers_2026-11-06.json)
  guarda os resultados e hashes no projeto. O diretório local de evidência
  contém `final_results.json` com todas as tentativas,
  `native_offense_graph.json`, `source_followup_candidates.json` e
  `counter_leak_confirmation.json` com os testes pareados das flags.
- Scanner reutilizável: [audit_specials_headless.py](../tools/audit_specials_headless.py).
  Não inicia build. Exemplo, usando o snapshot existente:

```sh
python3 tools/audit_specials_headless.py \
  build/specials_audit_20261106/4d757e64bdfc \
  --confirm --out rerun.json
```

Os retestes desta auditoria foram executados em etapas; `--confirm` reúne
essas famílias de contexto para novas execuções. Pode produzir variações
de cadência nas primeiras tentativas; o JSON preserva as condições.

O cruzamento dos comandos sanitizados com os states ligados não apontou
outro destino numérico ausente no levantamento de fonte. Isso não garante
que um destino ligado execute as fases internas: essa é justamente a
falha encontrada em vários golpes acima. Ramificações opcionais do MUGEN
continuam sendo candidatas a adaptação, não obrigações de fidelidade.

Validação da ferramenta e das alterações anteriores: **301 testes de
unidade passaram**, além da regressão headless específica de Sakura.
Nesta etapa não houve build nem alteração de gameplay/assets.
