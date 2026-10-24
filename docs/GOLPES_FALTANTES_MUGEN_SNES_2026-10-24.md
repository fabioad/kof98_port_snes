# Golpes dos assets MUGEN que faltam no port SNES

Levantamento de 24/10/2026, sobre os arquivos locais e a ROM `kof98-snes.sfc` existente. Não altera a ROM nem os assets.

Foram encontrados **61 diretórios de personagens ativos nos assets**, dos quais **48 têm personagem-base no port e 13 estão fora do elenco**. O port também tem Kyo Nests e Kyo Ash, totalizando 50 entradas. Os quatro Kung Fu Man em `_excluded/` ficam fora desta lista por serem exemplos explicitamente excluídos.

## Como ler

- Os números entre parênteses são **states MUGEN**, não slots do motor SNES. Fraco/forte e MAX são agrupados quando pertencem ao mesmo golpe.
- **Falta** significa que o state de origem não tem mapeamento correspondente no elenco compilado, ou que seu comando não chegou à tabela compilada. Isso não significa que os sprites estejam ausentes do SFF.
- **Parcial/adaptado** significa que existe outra versão, fase ou substituição na ROM. Não trato uma versão MAX presente como prova de que a versão normal também existe, nem uma fase ativa importada como reprodução completa do golpe original.
- Incluí formas EX/Orochi e variações de outros anos quando elas existem nestes pacotes. A referência é o conteúdo dos assets, não somente a lista oficial do KOF '98.
- Nomes vêm dos CMD, comentários CNS e ReadMes locais. Alguns rótulos `_SNES.cmd` estão incorretos: nesses casos usei o CNS e mantive os IDs para conferência. Quando o nome não é seguro, preservei o rótulo do pacote.

## Personagens já presentes no SNES

### Iori

- **Supers:** MAX Ya Otome (3050); Ya Sakazuki fraco/forte e MAX (3100/3110/3150).
- **Parcial/adaptado:** Koto Tsuki In forte (1310) não tem state próprio; Tsumagushi usa as fases 1501/1511 em lugar dos inícios 1500/1510. Não são duas famílias inteiramente ausentes.

### Kyo — também vale para Kyo Nests e Kyo Ash

- **Especiais:** Koto Tsuki You (1400/1410).
- **Supers/variações:** Orochinagi normal/MAX (3000/3010/3050); Mushiki '96 (3100/3150); MAX Mushiki original (3250); versão '99 do 182 Shiki (3350).
- **Parcial:** ramificações da sequência Aragami/Dokugami sem state próprio: Nanase (1615), Yanosabi alternativo (1620), Migiri Ugachi (1625), Tsumi Yomi (1710). Kyuushou (1605) e Yanosabi (1610) têm mapeamento e não entram como ausentes.
- **Atenção:** a ROM liga 3550 no slot comentado como MAX Mushiki, mas o CNS identifica 3550 como **MAX Kamukura**. O comentário do gerador não comprova a presença do MAX Mushiki de origem.

### Shingo

- Não identifiquei uma família adicional ausente nas entradas especiais/supers examinadas. Isso não certifica todas as propriedades e ramificações do MUGEN.

### Rugal

- **Especiais:** Eye Beam / “目からビーム” (1700); Beads Destruction (1800).
- **Parcial:** Gravity Smash aéreo tem mapeamento para 1550, mas a variante forte 1560 não tem state próprio.

### Omega Rugal

- **Especiais:** Gravity Smash nas entradas 1050/1055; outras entradas de projétil 1010/1011 sem equivalência direta confirmada.
- **Parcial/variação:** comandos `RE2` (2310), `gravity` (7100) e `RE` (8000) não têm os respectivos inícios mapeados. Há outros supers e fases desse pacote ligados, inclusive 2300, 2400, 7000 e 8100; não significa ausência de todos os golpes dessas famílias.

### Saisyu

- **Supers:** MAX Orochinagi (3050); Tsumugari normal e MAX (3100/3110/3150).

### Heidern

- **Supers:** MAX Final Bringer (3050); Heidern End normal e MAX (3100/3110/3150).

### Takuma

- **Especiais:** Mouko Burai Gan (1400/1410); Koho (1600/1610); Ko'ou Ken da forma EX/ura (1050/1060).
- **Supers:** MAX Ryuuko Ranbu (3020); Shin Kishin Geki normal/MAX (3100/3120); Haoh Shikou Ken nas entradas 1500/1510 e 3200/3210/3220; Kyokugen Koho normal/MAX (3300/3320).
- **Correção de nomenclatura:** o `_SNES.cmd` chama 3020 de “Haoh Shikou Ken MAX” e 3100/3120 de “Ryuuko Ranbu”; os comentários dos states CNS identificam os golpes acima.

### Clark

- **Especial:** Super Argentine Backbreaker, início/fase de agarre (1500/1510); Flashing Elbow (1600).
- **Supers:** MAX Ultra Argentine Backbreaker (3050); Running Three normal/MAX (3100/3110/3150).
- **Correção de nomenclatura:** 1500/1510 aparecem como “Napalm Stretch” no `_SNES.cmd`, mas o CNS os identifica como Super Argentine Backbreaker. Os states 1400/1410 já estão ligados.

### Ralf

- **Especiais:** Gatling Attack (410/411); Ralf Kick (430/431); início terrestre ascendente do Kyuukouka Bakudan Punch (450/451). A fase de mergulho 455 já existe.
- **Supers:** Umanori Vulcan Punch (510/511); Galactica Phantom (520/521); MAX Baribari Vulcan Punch (550), MAX Umanori Vulcan Punch (560), MAX Galactica Phantom (570).
- Os comandos de super usam expressões como `510 + var(17)*50`; conferir apenas valores inteiros literais do CMD perderia esses golpes.

### Leona

- **Especiais:** Baltic Launcher de origem (1300/1305); Ice Slasher da forma Riot (1410/1411).
- **Supers:** Rebel Spark DM/SDM (3100/3150); SDM Gravity Storm (3250); Grateful Dead (3300).
- **Parcial:** há outros states que o gerador comenta como Baltic Launcher. Não equivalem automaticamente às entradas 1300/1305 do pacote.
- **Correção de nomenclatura:** 3250 aparece como “V-Slasher MAX” no CMD SNES, mas é identificado como SDM Gravity Storm no CNS.

### Mature

- **Especiais/versões do pacote:** Ebony Tears (1500/1501/1502); variantes C/Z de Death Row (1001/1002), Metal Massacre (1101/1102), Despair (1301/1302) e Sacrilege (1401/1402).
- **Super:** SDM Heaven's Gates (3100).
- **Parcial:** o port liga versões dessas quatro famílias em outros states; as variantes acima não devem ser contadas como quatro famílias totalmente ausentes. Os supers Nocturnal Rites 3500/3600 já foram mantidos.

### Vice

- Não identifiquei uma família adicional ausente nas entradas especiais/supers examinadas. Seus supers adicionais 3100/3200/3300/3400 estão ligados. States de guard cancel não foram contados como especiais.

### Benimaru

- **Especiais:** Iai Geri (1300/1310); Benimaru Collider (1600).
- **Supers:** MAX Raikouken (3050); Electro Trigger normal/MAX (3100/3150); Raiko Katategoma normal/MAX (3300/3350).

### Daimon

- **Especiais:** Nekko Gaeshi (1400); Tenchi Gaeshi (1600).
- **Supers:** MAX Jigoku Gokuraku Otoshi (3050); Arashi no Yama normal/MAX e fase de agarre (3100/3150/3160).
- Jiraishin já tem uma restauração adicional no port; não o contei como ausente.

### Terry

- **Especiais/variações:** Power Wave EX/ura (1050); Power Charge MOW (1550/1560); Fire Kick (1600); Double Kong (1700).
- **Supers:** MAX Power Geyser (3050); High Angle Geyser (3100); Buster Wolf normal/MAX (3200/3250).
- **Parcial:** Power Dunk MOW fraco (1450) não tem início próprio, enquanto o port tem Power Dunk em outros states, inclusive 1460.

### Andy

- **Especiais:** Gekiheki Haisui Shou normal/ura (1400/1450); Genei Shiranui (1500); Bakushin (1700).
- **Supers:** Chou Reppa Dan normal/MAX (3000/3010/3050); MAX Hishou Ryuusei Ken (3150); Dan Da Dan normal/MAX (3200/3210/3250).
- **Parcial:** Hishou Ken EX forte (1160); a entrada 1150 já foi restaurada.

### Joe

- **Supers:** Screw Upper forte (3010); Bakuretsu Hurricane Tiger Kakato (3100); Thunder Fire normal/potencial (3200/3250).
- **Especial:** Slash Kick forte (1310).
- O state 3150 foi restaurado após a calibração; não o incluí entre os cortes ainda vigentes.

### Ryo

- **Especiais/variações:** Ko'ou Ken EX/ura (1050); Koho EX/ura (1150/1160); Hien Shippuu Kyaku '95 (1250/1260); Kyokugenryuu Renbu Ken (1400); Ko'ou Ken aéreo (2000/2010); Ko'ou Geki (2100).
- **Supers:** MAX Haoh Shokou Ken (3050); Ryuuko Ranbu normal/MAX (3100/3110/3150); MAX Tenchi Haoh Ken (3250); super descartado/experimental `MAX没超必殺技` (3350).

### Robert

- **Especiais/variações:** Ryuugeki Ken EX/ura (1050); Hien Shippuu Kyaku e versão '95 (1250/1260); Kyokugenryuu Renbu Kyaku (1400); Sen'en Renbu Kyaku (1450).
- **Supers:** Haoh Shokou Ken normal/MAX (3000/3010/3020); MAX Ryuuko Ranbu (3120); Muei Shippuu Juudan Kyaku normal/MAX (3200/3210/3220); Muei Senpuu Juudan Kyaku normal/MAX (3250/3260/3270).
- **Comando ausente:** Ryuugeki Ken forte 1010 tem mapeamento no gerador, mas não aparece como entrada de comando na tabela compilada examinada.
- A entrada original que menciona 3050 não tem esse Statedef no CNS mesclado; não a contei como golpe adicional válido.

### Yuri

- **Supers MAX:** Haoh Shokou Ken (550); Ryuuko Ranbu (560), que substitui o super de chutes durante MAX no pacote original.
- Os supers normais 500/501 e 510/511 já existem; as fases 512/513/514 também estão ligadas.

### Athena

- **Supers:** Phoenix Fang Arrow curto/longo/duplo (2000/2020/2050); Super Shining Crystal Bit (4000).
- **Parcial:** a entrada 3100 também foi retirada do mapeamento; deve ser conferida com a sequência Crystal Bit antes de tratá-la como família independente. Crystal Bit e sua continuação 3000/3050 já estão ligados.

### Kensou

- **Especial:** Sen Shippo fraco/forte (1300/1330).
- **Versões normais dos supers:** Niku Man o Kuu (2000), Sen Ki Hakkei (2100), Chouryuu Renken (2200).
- **Parcial:** as versões SDM 2050/2150/2250 estão ligadas nos slots 48–53, classificados pelo motor como especiais. Portanto não são três famílias inteiramente ausentes, mas também não há equivalência fiel de custo/categoria com o MUGEN.

### Chin

- **Especiais do pacote:** Zake Attack (1000/1100), Fire Zake e sua variante (1203/1300), upper forte (1400).
- **Supers:** Super Long Walk Hell (1750); Hyper Long Walk Hell (2200).
- Há outros projéteis e variantes, inclusive 1900/1910/1920, já ligados; nomes genéricos do pacote não devem ser confundidos com ausência de todo ataque de fogo.

### King

- **Especial:** Mirage Dance (1500).
- **Supers:** MAX Illusion Dance (3200); Silent Flash normal/MAX (3300/3400); Surprise Rose super fraco/forte/MAX (3500/3600/3700); Rose “Dragooner” – 1954, MAX2 (3800).
- O port usa os states 3000/3100 como seu par de supers. Não se deve deduzir pelos rótulos do importador que todos os supers do pacote já estão presentes.

### Mai

- **Especiais:** Bachi (1038/1040); Toki Tsubute (1050); Hishou Ryuu'en Jin (1080/1082).
- **Super:** MAX2 (2030, nome do CMD).
- **Sem comando compilado:** Ryuu Enbu 1010 e Gekka Botan 2070 têm mapeamento, mas seus comandos não aparecem na CmdTab. Há outras fases de Enbu ligadas; não significa que toda a família esteja ausente.

### Chizuru

- **Super:** HSDM/MAX2 do pacote (2200, que invoca o helper `HSDM` 40001). O nome do CMD está com codificação inconsistente; mantive a identificação técnica.

### Kim

- **Supers:** Houou Kyaku normal/MAX (3000/3020); MAX Houou Tenbu Kyaku (3120); Houou Hiten Kyaku normal/MAX (3200/3210/3220).
- Houou Tenbu Kyaku normal 3100/3110 já está ligado.

### Chang

- **Especial:** Haki Kyaku (1400).
- **Supers:** Tekkyuu Dai Assatsu nível 2 (3400); Tekkyuu Dai Sekai (3500).

### Choi

- **Especiais:** Tatsumaki Shippuu Zan (1000/1010); Senpuu Hien Shitotsu (1100); Hishou Kuuretsu Zan (1200/1210); Shissou Hishou Zan (1600/1610).
- **Supers:** Ultimate Storm (2400); Shin! Chouzetsu Tatsumaki Shinkuu Zan na entrada normal (3000); Zan! En Getsu Rin (3100/3110); Houou Kyaku normal/MAX (3200/3250); Shakushi/MAX2 (3500).
- **Parcial:** há versões 3050/3060 de super ligadas. Elas não preservam todos os inícios e supers normais acima.

### Yashiro

- **Especiais Orochi:** Odoru Daichi (2200/2210); Kujiku Daichi (2300/2310).
- **Supers normais:** MAX Million Bash Stream (3020); Final Impact (3100/3120).
- **Supers Orochi:** Hoeru Daichi normal/MAX (3500/3510/3520); Araburu Daichi normal/MAX (3600/3620); Ankoku Jigoku Gokuraku Otoshi normal/MAX (3700/3720).
- A ROM já mistura especiais normais e Orochi (incluindo 2000/2100); isso não representa a importação completa das duas formas.

### Shermie

- **Especiais normais:** Axle Spin Kick (1000/1050), Shermie Shoot (1100/1150), Shermie Whip (1200/1250), Shermie Spiral (1300).
- **Especial Orochi:** Shajitsu no Odori (7000/7050); Raijin no Tsue aéreo (7100/7150).
- **Variações Orochi:** distâncias adicionais de Mugetsu no Raiun (7225/7250/7275); Yatanagi no Muchi forte (7350).
- **Supers:** Shermie Carnival normal (2100); Ankoku Raikouken normal/SDM (8100/8150); entrada própria de Shukumei, Gen'ei, Shinshi em 8000.
- **Parcial/adaptado:** a ROM liga Shukumei em 8050, Carnival em 2150 e Flash em 2200/2250. Os states 7200/7300 foram restaurados como entradas adicionais de projétil, mas não têm os comandos originais correspondentes na CmdTab examinada.

### Chris

- **Especiais normais:** Slide Touch (1300/1350), Direction Change (1500/1550), Shooting Dancer Step (1600/1650).
- **Especiais Orochi:** Taiyou o Iru Honoo (7000/7010), Kagami o Hofuru Honoo (7100/7150), Tsuki o Tsumu Honoo (7200/7250), Shishi o Kamu Honoo (7300/7350).
- **Versões normais dos supers:** Twister Drive (2100), Chain Slide Touch (2200), Daichi o Harau Gouka DM/SDM (8000/8050), Ankoku Orochinagi nos inícios DM (8100/8105).
- **Parcial:** Twister Drive 2150, Chain Slide Touch 2250 e Ankoku Orochinagi SDM 8150/8155 já estão ligados. Não são famílias inteiramente ausentes.

### Yamazaki

- **Especiais:** Bakudan Pachiki (1400); Todome (1600).
- **Super:** MAX Guillotine (3020).
- **Parcial:** Drill usa diretamente 3140 e a versão MAX 3150 restaurada; seu início normal 3100 não foi preservado como entrada própria. Guillotine normal 3000/3010 já voltou.

### Blue Mary

- **Especiais:** Straight Slicer (1600/1610); entrada 1050 sem nome confiável nos rótulos examinados.
- **Supers/inícios:** Super Dunk normal/MAX (3000/30000); Mary's Dynamite Swing nível 1 (3100); Splash Rose nível 1/2 (3300/3400); Mary's Typhoon (3800); versão `dynamite` 40000; Infinity Rose (50000).
- **Parcial:** há Super Dunk em 3060 e Goodnight em 4000 restaurados, além de outras fases de Mary. Não contar cada fase do Super Dunk como golpe diferente; a versão inicial/fiel normal ainda não foi preservada.

### Billy

- **Super:** Flaming Stick Spin normal/MAX (1800/1850/1860); entradas especiais de super em 1900/1910 (nome do pacote não legível com segurança); Super Stick Swing forte (2510); Chou HongRenSalgon forte (2600); MAX2 (6000).
- **Especial/variação:** Rapid Wave Cane forte (1610).
- **Variações do modo 2002:** 1102/1105/1111, 1305/1310/1315, 1580/1590, 1720 e 1791 não têm mapeamento próprio. São principalmente entradas de cancel/variante de golpes já parcialmente ligados.
- **Rótulo enganoso:** o state 3100, removido do slot 87, é **Power Charge**, não um super. Não o contei como golpe faltante.

### Lucky

- **Especiais/variantes:** Shoot 2/3/4 (2200/2300/2400), Finger Roll 1 (2500), Slam 1/2 e sua versão aérea (2700/2800/4700).
- **Supers:** Death Bound nas entradas 2900/3000; Finger Roll SDM (3100); Shoot Out normal/desperate (3400/3500).
- O basquete de Shoot 2099 → 2100 e os supers 3200/3300 já estão ligados; isso não cobre todas as trajetórias e supers do pacote.

### Heavy D!

- **Super adicional:** D. Shadow (2200, presente no CNS com custo de 1000, sem mapeamento no port).
- **Parcial/adaptado:** D. Magnum já existe via fase de disparo 2105, sem o início 2100 completo. D. Crazy e MAX D. Crazy 2000/2050 já estão ligados.

### Brian

- **Supers:** American Supernova nível 2 (3300), Galaxy Cyclone nível 2 (3400), Big Bang Tackle nível 2 (3500), American Final Tackle (3600).
- **Parcial/adaptado:** Galaxy Cyclone e Big Bang Tackle normais **já existem** pelas fases 3110/3210; o port pula os inícios 3100/3200. Não os contei como dois supers totalmente ausentes.

### Geese

- **Especiais:** Raimei Gouha Nage (1500); Shinkuu Nage (1600); contra-ataque baixo adicional 1402.
- **Supers:** Raging Storm fraco/forte (3000/3010); Deadly Rave nas entradas normal/MAX 3100/3110/3120 e na variante 3300.
- **Parcial:** Rashomon usa MAX 3250 restaurado, sem a entrada normal 3200. O port também liga 1050 em um slot de especial; não o confundir com importação fiel dos states 3000/3010 do Raging Storm.

### Krauser

- **Especiais:** Phoenix Throw (1600); Kaiser Claw (1700).
- **Supers:** Kaiser Inferno normal/MAX (3100/3150); Unlimited Desire normal/MAX (3300/3310/3320).
- **Parcial:** Gigantic Cyclone usa a versão MAX 3220 restaurada, sem a entrada normal 3200.

### Mr. Big

- **Especiais:** Crazy Drum (1100); Drum Shot (1500).
- **Supers:** Blaster Wave normal/MAX (3000/3010/3050); Rising Spear (3100); MAX do super descrito no CNS como `棒どつきスピニングちょっと対空` (3250).
- Os supers 3200/3210 já estão ligados; não devem ser confundidos com Blaster Wave.

### Eiji

- **Especiais:** Kikouhou (1000); Mukuro Nui (1600).
- **Supers:** MAX Zantetsuha (3020); Zantetsu Tourouken normal/MAX (3100/3120); Yamikari, exclusivo MAX (3200).
- Zantetsuha normal 3000/3010 já existe.

### Vega / M. Bison

- **Supers:** Final Psycho Crusher (3050); MAX Knee Press Nightmare (3150).
- Os teletransportes 1400/1410/1420/1430 já estão ligados.

### Ryu

- **Especial:** Tatsumaki Senpuu Kyaku aéreo (1250).
- **Supers:** Shinkuu Tatsumaki Senpuu Kyaku normal/MAX (3100/3150).
- **Rótulo enganoso:** o slot 87 é comentado como super Tatsumaki no gerador, mas aponta para 3200, identificado pelo CNS como **Shin Shoryuken**. Por isso o Shinkuu Tatsumaki original continua na lista de faltantes.

### Ken

- **Especiais:** Tatsumaki Senpuu Kyaku aéreo (1250); Oosoto Mawashi Geri (1320).
- **Supers:** Shippuu Jinrai Kyaku normal/MAX (3100/3150); Shinryuuken (3200).
- **Parcial:** Shoryuu Reppa MAX 3050 foi restaurado; a entrada normal 3000 não está preservada como state próprio.

### Chun-Li

- **Especiais/variantes:** Kikouken novo/curto (1050); Spinning Bird Kick aéreo (1250).
- **Supers:** Kikou Shou (3000), Houyoku Sen (3100), Hazan Tenshou Kyaku (3200).
- O state 3300 restaurado é outra entrada do pacote e não comprova a presença desses três supers.

### Sakura

- **Especial:** Ouka Kyaku (1400).
- **Supers:** MAX Shinkuu Hadouken (3050); Haru Ichiban normal/MAX (3100/3150); Midare Zakura normal/MAX (3200/3250); Haru Goku Satsu (3300).

## Personagens dos assets que ainda estão inteiramente fora da ROM

Todos os especiais e supers abaixo faltam porque o personagem não tem entrada em `CHARS` nem tabelas de lutador no binário. Nomes abaixo seguem os documentos e states locais, inclusive golpes adicionais aos de KOF '98.

### Adelheid

- **Especiais:** G. Kicken, G. Drucken, G. Wand, G. Prinzessin, G. Kreis.
- **Supers:** G. Kronprinz e G. Schlagen, com versões DM/SDM.

### Bao

- **Especiais:** Psycho Ball frontal/longa/ascendente (900/920/945), Air Psycho Ball (1100), variantes aéreas 1001/1004, escudo (1900), entradas adicionais de movimento/ataque 1250/1400/1450/1500.
- **Supers:** Super Explocion (950), Hyper Psycho Ball / Psycho Ball Attack Max (3000), Ball Explosion (3350), Psycho Ball Gravity (3500).
- O pacote usa rótulos genéricos para parte dos especiais; os IDs são a referência para esses casos.

### Duck King

- **Especiais:** Head Spin Attack (1000), Flying Spin Attack (1100), Dancing Dive (1200), Break Storm (1300).
- **Supers/derivações de Duck Dance:** Break Spiral (2000), Duck Dance (2100), Diving Punisher (2110), Rolling Punisher (2120), Dancing Caliber (2130), Break Hurricane (2140), Super Pumping Machine (2150), Beat Rush (2200), High Bound Spiral (2300).

### Fighter

- **Especiais:** os ReadMes descrevem Open Fire/Duneblast, Firespout, Relentless Assault, Distortion Strike/Pit Raptor, Mirror Sheen e Piston Sledge.
- **Supers:** Dragonstorm, Galestrike, Tempest of Light, Shatterstorm e Savage Beating, incluindo SDM.
- O ReadMe reúne mais de um conjunto de movimentos. O CMD também nomeia Raging Storm, Baribari Vulcan Kick, Dragon Cannon e Kikou Shou MAX. Esses nomes divergentes devem ser reconciliados com o modo/forma do pacote antes da importação; não são uma contagem garantida de famílias independentes.

### Goenitz

- **Especiais:** Yonokaze (quatro posições), Wanhyou Tokobuse, Wanhyou Mametsu, Hyouga, Shin Aoi Hana: Seiran, Shin Koto Tsuki: Souga; entradas adicionais DP+chute 1600/1610.
- **Supers:** Yami Doukoku normal/MAX; Shin Yaotome: Mizuchi; Shin Yaotome: Jissou Koku.

### Haohmaru

- **Especiais:** Senpuu Retsuzan e seu falso projétil, Ougi Kogetsuzan, Ougi Resshinzan, Zankousen.
- **Supers:** Tenha Seiouzan; Hi Ougi Tenha Fuujinzan, com MAX; Hi Ougi Tenha Dankuu Retsuzan.

### John Crawley

- **Especiais:** Mega Smash, Flying Attack, Spiral Leg Bomber, Over Drive Kick e versão Guard Break, Fireblast.
- **Supers:** Mega Smasher e Atomic Smash, com versões SDM.

### Kasumi

- **Especiais:** Kasane Ate terrestre/aéreo, Taikuu Kasane Ate, Hakuzan Toh, Messhin Mutou, Sassho Inshu, Tatsumaki Souda, Rai Houkou, Senkou Nagashi.
- **Supers:** Chou Kasane Ate e Shingan Kazura Otoshi, com versões MAX.

### Kyoko

- **Especiais:** Doku Gami e sequência, Oni Yaki, 75 Shiki Kai, R.E.D. Kick, Nie Togi (nome do ReadMe).
- **Supers:** Mu Shiki e 182 Shiki, com versões MAX.

### Orochi

- **Especiais:** Lightning nas quatro posições (1020–1023), Reflection (1041/10411/13111 e 1045), ataques `Poder` (1051/1052).
- **Supers:** Mu Ni Kaerou e variações simples/duplas (2000/2100 e entradas alternativas 10000/10450/11000/11001), Soul Extraction simples/dupla (2200/2300), golpe `or` (20000, nome do CMD).
- O DEF escreve `cmd/`, mas o diretório real é `CMD/`; os comandos foram conferidos no arquivo efetivamente existente. Parte dos números altos é de variação/continuação, não necessariamente outro golpe.

### Rock Howard

- **Especiais:** Reppuken (1000), Double Reppuken (1050), Hard Edge (1100/1150), Rising Tackle (1200/1250), Rage Run Dunk/Shift (1300/1350), Crack Counter alto/baixo (1400/1450), Shinkuu Nage (1500).
- **Supers:** Raging Storm (2000/2500), Shine Knuckle (2100/2600), Deadly Rave Neo (3000), Thunder Break LDM (33300).

### Sagat

- **Especiais:** Tiger Shot alto/baixo, Tiger Uppercut, Tiger Knee/Crush, conforme comandos e states do pacote.
- **Supers:** Tiger Cannon e Ground Tiger Cannon (3000/3050), Tiger Raid (3100 e variantes), Tiger Genocide normal/MAX (3200/3250), Angry Charge (3300), Tiger Storm MAX2 (3400).

### Lee Pai Long

- **Especiais:** ataques de garra alto/baixo (1050/1051/1060/1061), Hyakuretsu Ken (1100), Hyakuretsu Kyaku (1200/1250), Hien Mouko (1300), ataque de cotovelo `華中走肘撃` (1350), Hien Hekikake e derivação de parede (1400/1430), `華中猛腕脚` (1500).
- **Supers:** `華中飛猿爪` (2000/2050 e EX 2250), `真空空転爪` e variantes EX/ranbu (2100/2150/2200), `飛翔旋風撃` (2300), super adicional 3600 sem nome seguro no cabeçalho.
- Preservei os nomes japoneses onde a romanização não estava documentada com segurança.

## Limites e evidência da comparação

1. Fontes principais: `tools/build_fight.py`, `tools/newroster.py`, os CMD/CNS originais e `_SNES`, ReadMes locais e `build/gen_fight/*_spr.inc`.
2. As tabelas **CmdTab dos 48 personagens-base foram lidas também do binário**, usando os endereços de `kof98-snes.symfull`. Os conjuntos de slots conferem com os arquivos gerados em **48 de 48** personagens.
3. Os supers de `POST_CAL_SUPERS` foram considerados presentes quando restaurados. A lista não replica cegamente os comentários antigos de corte por orçamento de ROM.
4. O levantamento é estático. Não executei cada golpe no emulador e não certifico equivalência de dano, invulnerabilidade, helpers, agarrões, ramificações ou efeitos. Um golpe ligado pode continuar incompleto; os casos conhecidos de substituição estão assinalados.
5. Não somei states para anunciar um total de golpes: fraco/forte, versões MAX, fases de ataque, variantes de modo e helpers fariam essa soma superestimar o número de famílias.

ROM examinada: 8.388.608 bytes; SHA-256 `7562ae1cf20d39bea13528a03819921f4a0cf5220543b2a6e0d38d343739c991`.
