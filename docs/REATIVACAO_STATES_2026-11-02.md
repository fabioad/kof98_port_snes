# Reativação de states e fechamento do build — 02/11/2026

## Estados religados

`POST_CAL_REACTIVATED` em `tools/build_fight.py` repõe, depois de
`apply_profile`, os comandos que apontavam para um `Statedef` sem `sid`.
São **27 personagens / 71 entradas de comando**.

| Personagem | State -> sid |
| --- | --- |
| Iori | 3050 -> 103 |
| Saisyu | 3050->87, 3100->88, 3110->89, 3150->66 |
| Heidern | 3050->87, 3100->88, 3110->89, 3150->66 |
| Takuma | 3020->87, 3220->58, 3100->88, 3120->89 |
| Clark | 1500->58, 1510->59, 3050->87, 3100->88, 3110->89, 3150->66 |
| Ralf | 510->87, 511->88, 520->89, 521->58, 550->59, 570->60, 512->61 |
| Leona | 3250->58, 3100->87, 3150->88, 3300->89 |
| Benimaru | 1300->60, 1310->61, 1600->62, 3050->87, 3100->89, 3150->88, 3300->66 |
| Daimon | 1400->63, 1600->59, 3050->87, 3100->89, 3150->88, 3160->60 |
| Terry | 3050 -> 87 |
| Andy | 3150 -> 87 |
| Ryo | 3050 -> 87 |
| Robert | 3120->87, 3250->88, 3260->89 |
| Athena | 3100->87, 4000->88 |
| King | 3500 -> 87 |
| Chizuru | 2200 -> 87 |
| Kim | 3120 -> 87 |
| Chang | 3500 -> 87 |
| Choi | 3000->87, 3500->88 |
| Yashiro | 3500 -> 87 |
| Shermie | 7000->60, 7050->61 |
| Chris | 7100->60, 7150->61 |
| Billy | 3100->62, 1800->64, 1850->66 |
| Lucky | 2900->88, 3000->89 |
| Mr. Big | 3000->87, 3010->88, 3250->89 |
| Eiji | 3020 -> 87 |
| Sakura | 3050 -> 87 |

Obs.: Takuma mantém apenas os quatro comandos; os states de
continuação 3221/3222/3022/3023/3001 foram deixados de fora para a tabela
caber nos 32 KiB do banco 83, que divide espaço com `ShingoChrN`.

## Layout / build

- `tools/asset_paths.py`: resolvedor case-insensitive usado por
  `build_fight.py`, `build_select.py` e `calibration/native.py`.
- `build_portraits`: paleta de 3 cores é preenchida quando o quantizador
  devolve menos de 3 cores.
- Alocador: mesas/metasprites, atlases de projétil e tabela de IA agora
  são empacotados numa única passada (`grab(all_sizes)`), com ordem
  embaralhada nos retries. O esquema antigo de “reservar depois” deixava
  um atlas de 4 KiB sem janela contígua.
- Novas janelas: tails após as ending stills nos bancos 118–125.
- Daimon: CHR agora streamado pelo MSU. A tabela cresceu e empurrava o
  blob ROM-residente para o banco 43, onde fica `EndData0`. As metades
  baixas 27–42 ficaram livres e foram devolvidas ao alocador.
- Saisyu e Clark: `SprData` separado em `_meta.inc`.
- Heidern: as quotes ES ficam imediatamente após a tabela, em offset
  dinâmico, em vez de `$A000` fixo.
- `Chizuru 87` e `Mr. Big 88/89` marcados como MAX/SDM.

## Verificação

```sh
python3 tools/build_fight.py
make pvsnes PVSNESLIB_HOME=/run/media/fabio/Dados/Fabio/pvsneslib-sdk-4.6
make pvsnes-verify PVSNESLIB_HOME=/run/media/fabio/Dados/Fabio/pvsneslib-sdk-4.6
python3 -m unittest tools.tests.test_reactivated_states
python3 -m unittest tools.tests.test_command_list tools.tests.test_counter_grab
python3 tools/test_command_list_headless.py
python3 tools/test_msu_chr_visibility_headless.py
```

Resultados:

- `build_fight.py`: OK.
- Link ROM: OK, 1.499.887 bytes livres de 8 MiB.
- `pvsnes-verify`: OK (Fast HiROM, checksum `$7AEB`).
- Testes unitários: OK.
- Command list headless: 6 PASS.
- MSU CHR visibility: 960 páginas / 57 poses, passed.

## Limites conhecidos

- Golpes cujo HitDef real está em Helper/Explod continuam aproximados.
- Supers MAX em slots especiais (`Iori 103`, `Saisyu/Heidern/Clark 66`)
  não recebem o desconto da janela MAX; usam o custo direto do `PowTab`.
- O `.msu` e a ROM mudaram; copie os dois juntos para o SD.

## Correção pós-build: MSU alinhado e Daimon no MSU

- Daimon passou a streamar CHR do MSU. Isso desloca os slices de todos os
  personagens seguintes; ROM antiga + MSU novo (ou vice-versa) faz os
  chars MSU lerem tiles errados, aparecerem por poucos quadros ou ficarem
  invisíveis.
- O arquivo `.msu` agora é preenchido até múltiplo de 512 bytes.
- Sempre copie **kof98-snes.sfc e kof98-snes.msu do mesmo build**.
- Layout MSU atual: `$F416`.

## Correção de travamento Clark × Ralf (02/11/2026)

Os states novos do Clark que não tinham a cadeia completa foram desativados
temporariamente:

- 1500/1510 (Super Argentine/Napalm) -> faltavam 1511/1520/5690;
- 3050 (MAX Ultra Argentine) -> faltava 3060 e a cadeia 3061-3067;
- 3100/3110/3150 (Running Three) -> faltavam 3105/3155/3120/3121/1201.

Entrar nesses states deixava o Clark preso na pose final, com o resto da
luta ainda rodando. O Ultra Argentine original (3000 -> 109-111) continua
ligado e é a versão estável. Os comandos ficam sem `sid` até as cadeias
completas serem importadas e testadas.

Build/verify: ROM checksum `$6B6B`, `make pvsnes-verify` OK.

## Reativação funcional dos golpes do Ralf (02/11/2026)

Os states do Ralf que estavam desligados foram religados usando as
cadeias que o motor já suporta. O objetivo foi golpe funcional e dano,
não fidelidade visual dos explods/palFX.

- 510/511 -> 512 (Running Super): a transição usa o gate de distância
  existente (`TransDistGate`, kind 4) no frame 7 com 70 px de centro.
  512 foi para o sid 103 e seu HitDef prende a vítima no slot 76.
- 512 -> 515 -> 516/517/518 (montaria): 515 foi para o sid 104 e usa o
  mesmo pipeline TargetBind/TargetState/TargetLifeAdd do Ultra Argentine
  do Clark. 516/517 usam o slot segurado (76) e 518 o arremessado (77).
  São 13 contatos de 2 pontos (~23 de dano).
- 520/521 (Ultra Vulcan): dash reduzido de 16/8/4 para 12/6/3 px/tick e
  o posadd de -16/+8/+8/+16 removido; o HitDef acerta por 80.
- 550 (MAX V-Slasher): a vítima fica presa em hitstun (sem launch) e os
  13 contatos usam o MoveHitReset existente; 4 pontos nos primeiros e 3
  nos últimos, ~49 de dano.
- 570 (MAX Galactica): sem Helper, virou um único golpe de 80 pontos no
  frame final. A parte visual do helper não existe.
- 85/86 (Galactica Phantom fraco/forte) continuam como antes.

Limites conhecidos: os victim states de queimadura 80010/80011 e
80002/80018 não foram portados; os efeitos de explod/palFX dos golpes
continuam ausentes. O dano e a sequência funcional estão no lugar.

Build/verify: checksum `$34A5`, layout MSU `0x01EE`. Copie `.sfc` e
`.msu` do mesmo build.

## Vulcan Punch com múltiplos hits (03/11/2026)

Ralf (states 400/401, sids 48/49) e Clark (states 1000/1010, sids 48/49)
agora acertam cinco contatos antes de derrubar:

- `hit_soft_resets` rearma o HitDef em cada uma das cinco janelas de
  ataque do CNS (Ralf 3/6/9/12/15 e 5/8/11/14/17; Clark 4/7/10/13/16 e
  3/5/7/9/11);
- `hitdef_override` mantém a vítima em hitstun (`fall = 0`, `gvx/gvy = 0`)
  até o quinto contato;
- `MoveHitFinisher` força o knockdown no quinto contato;
- `air_box_patch_frames` acrescenta uma caixa de corpo nas cinco janelas,
  porque a caixa final original não cobria todas as animações de hit e o
  quinto golpe passava por alguns personagens.

Dano medido no headless:

- Ralf: 4 + 4 + 4 + 4 + 3 = 19;
- Clark: 6 + 6 + 6 + 6 + 5 = 29.

Testado contra Heidern, Clark e Kyo, em pé e na guarda, a 20/40/70 px.
Build/verify: checksum `$22DE`, layout MSU `0x01EE`.

## Agarres de Ralf e Clark (03/11/2026)

Os especiais de agarre que só tocavam a animação foram ligados à cadeia de
bind/dano do motor:

- **Ralf Running Super** (510/511 -> 512 -> 515): a montaria já usava o
  pipeline do Ultra Argentine; agora o whiff corta o dash no frame 10 e a
  tentativa no frame 4.
- **Clark Mount Tackle** (HCF + X/Y): 1200 -> 1205 (sid 53) -> 1210
  (sid 99); 21 de dano e knockdown.
- **Clark Super Argentine** (HCF + A/B): 1300 -> 1305 (sid 55) -> 1310
  (sid 101); quatro contatos de 20, ~81 de dano.
- **Clark Frankensteiner** (DP + A/B): 1400/1410 -> 1420 (sid 107); 25
  de dano.
- **Clark Napalm Stretch** (DP + X/Y): 1500 (sid 58) -> 1510 (sid 108);
  20 de dano.

Detalhes técnicos:

- `S_EXT_GRAB` passou de 103 para 98; os slots 98/99/101/107/108 agora
  mantêm a vítima presa e o `ThrowBind` reposiciona o corpo.
- `StAirSpec` ganhou uma cauda em banco baixo (`StAirSpecTail`) para
  chamar `ThrowBind` sem estourar a janela de 32 KiB do banco Fight,
  preservando o `ClampX` dos especiais aéreos.
- Os estados de tentativa usam gate de distância kind 4 (corpo <= 8 px,
  convertido para 38 px de centro).
- Os comandos "strong" do CMD do Clark entram no estado de tentativa, não
  no estado de vítima segurada.
- `frame_cap` corta os primeiros frames dos roots/tentativas quando o
  agarre não conecta: Ralf 87/88/103, Clark 52/54/56/57/58.

Continuam desligados: Clark Running Three (3100/3110/3150) e o MAX 3050,
que ainda dependem das cadeias 3105/3155/3120/3121/1201 e 3060/3061-3067.

Build/verify: checksum `$40BE`, layout MSU `0x01EE`. Copie `.sfc` e `.msu`
do mesmo build.

Observação: o teste headless `test_sakura_antiair_headless` ainda acusa
30 de dano no Shou'ou Ken forte contra um orçamento de 26; é uma diferença
de calibração de dano da Sakura, não dos agarres.

## Correção do “um frame” nos chars (03/11/2026)

Os primeiros builds da cadeia de agarres adicionaram animações novas do
Clark (1205/1420) ao blob CHR, mudando o layout do MSU para `0xBDAF`.
No SNES real isso reintroduziu o sintoma de personagens presos em um
frame (o loader do SD2SNES é sensível ao layout/setor).

As tentativas 1205/1305 reutilizam agora o anim 1200 já existente, e o
follow-up do Frankensteiner (1420) reutiliza o anim 3011 do Ultra
Argentine. O conjunto de sprites do Clark voltou a 222 cels/16.608 tiles,
o layout do MSU voltou para `0x01EE` (o mesmo da build estável) e os
agarres continuam funcionais com dano e bind. A pose visual de alguns
follow-ups é reaproveitada; o dano e o knockdown são os mesmos.

Build/verify: checksum `$40BE`, layout MSU `0x01EE`.
