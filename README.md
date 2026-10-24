# KOF '98 SNES — um port de fã para Super Nintendo

**Português (Brasil)** · [English](#english)

---

## 🇧🇷 Português (Brasil)

### Uma carta de amor ao SNES

Há uns 30 anos, quando vi **Street Fighter Alpha 2** rodando no Super
Nintendo, fiquei boquiaberto. Na época, aquilo parecia impossível: personagens
grandes, animação fluida, efeitos, vozes... tudo em um console de 16 bits.
Aquele jogo me marcou e me mostrou uma coisa que nunca esqueci: **o SNES,
quando alguém se dedica de verdade, pode chegar a lugares que pareciam
inimagináveis.**

O tempo passou, mas a vontade de ver o SNES ser levado ao limite ficou. Este
port de **The King of Fighters '98** nasceu dessa obsessão: pegar um jogo de
luta enorme, cheio de sistemas, personagens e efeitos, e fazer tudo caber em
um hardware que muita gente já considerava "no limite" nos anos 90.

Não é um emulador, nem um wrapper, nem uma ROM oficial. É um motor de luta
próprio em **65816 + PVSnesLib**, com assets convertidos de pacotes MUGEN/KOF
'98, rodando de verdade no SNES (ou em um emulador compatível).

### O que você vai encontrar

- **50 entradas de lutador**, incluindo o elenco de KOF '98, convidados e
  formas ocultas.
- **10 cenários** convertidos para o SNES.
- **6 modos de jogo**, além da demonstração automática e das opções.
- Sistema de **power gauge**, MAX, supers, SDM e Quick SDM.
- **Chains, cancelamentos, especiais, supers, projéteis, agarrões,
  contra-ataques, bloqueio alto/baixo/aéreo, chip damage e blowback**.
- **IA com níveis de 1 a 9**, com personalidade própria por personagem.
- **Modo TREINO/PRACTICE** com command list, meter infinito e CPU parada.
- **Team Play 3 vs 3**, Survivor com final próprio e campanha Single Play.
- **Paletas espelhadas** para lutas entre o mesmo personagem.
- Música e efeitos via SPC700/SNESMOD; gráficos, vozes e extras podem ser
  streamados do arquivo MSU-1.

### Números do port

| Item | Valor |
| --- | --- |
| Lutadores | **50 entradas** (48 do elenco-base + Kyo Nests e Kyo Ash) |
| Cenários | **10** |
| Modos | **6**: Single Play, Single VS, Team Play, Team VS, Survivor e Practice |
| Rounds | Melhor de 3 (duas vitórias) |
| IA | Níveis **1 a 9** |
| Resolução | 256×224, padrão SNES |
| ROM | **8 MiB** (`kof98-snes.sfc`) |
| Dados MSU-1 | **~28 MB** opcionais (`kof98-snes.msu`) |

### Lutadores

O elenco reúne a família KOF '98 e alguns convidados especiais:

- **KOF '98:** Kyo, Iori, Shingo, Terry, Andy, Joe, Ryo, Robert, Yuri, Athena,
  Kensou, Chin, King, Mai, Chizuru, Kim, Chang, Choi, Yashiro, Shermie, Chris,
  Yamazaki, Blue Mary, Billy, Lucky, Heavy D!, Brian, Geese, Krauser, Mr. Big,
  Eiji, Saisyu, Heidern, Takuma, Clark, Ralf, Leona, Mature, Vice, Benimaru,
  Daimon, Rugal e Omega Rugal.
- **Convidados:** Ryu, Ken, Chun-Li, Sakura e Vega.
- **Variantes de Kyo:** Kyo Nests e Kyo Ash.

Formas ocultas:

- **Omega Rugal:** segure **L+R** na célula do Rugal.
- **Kyo Nests / Kyo Ash:** use **L** ou **R** na célula do Kyo.
- O Rugal normal depende do CHR streamado do MSU-1; sem o arquivo, a célula
  mostra Omega Rugal e o Rugal normal fica indisponível.

### Sistemas de jogo

- **Controles de 4 botões** com macros nos ombros: L = esquiva, R = blowback,
  L+R = taunt. Combinações de direção + botão reproduzem os comandos MUGEN
  (QCF, QCB, DP, HCF, HCB, charge, double motions etc.).
- **Chains e cancelamentos:** normais leves encadeiam; normais fortes abrem
  cancelamento para especiais e supers depois de conectar.
- **Power gauge e MAX:** ative o MAX com **Y+B+X** e gaste o medidor em supers,
  versões MAX/SDM e Quick SDM.
- **Defesa:** bloqueio alto, baixo e aéreo, chip damage, pushback, guard crush
  no blowback (CD), contra-ataques/reversals por personagem e agarrões.
- **Movimentação:** dash, backdash, pulo, esquiva parada (L), rolamento para
  frente/trás (L + direção) e blowback (R).
- **Combos e juggle:** contador de hits, decaimento de combo, projéteis,
  faíscas de impacto, tremor de tela e KO.
- **Modos de jogo:** campanha Single Play, versus local, Team Play 3v3,
  Team VS, Survivor e Practice.
- **Practice:** command list no menu de pausa, meter cheio, vida protegida,
  relógio parado e CPU idle para testar setups.
- **Attract demo:** após alguns segundos sem input, a ROM mostra uma luta
  CPU vs CPU e depois entra na abertura.
- **Opções e sound test:** ajustes de jogo e audição das faixas.
- **Paletas P2:** em espelho, o segundo jogador recebe a próxima paleta do
  pacote de origem.
- **IA:** perfis de zoner, rush, grappler e equilibrado; a agressividade,
  defesa, anti-aéreo, agarre e uso de super sobem com o nível.

### Com MSU-1

Com o arquivo `kof98-snes.msu` ao lado da ROM:

- Todas as **50 entradas** ficam disponíveis.
- Os tiles de personagem são streamados do MSU-1.
- As vozes streamadas e o final do Survivor (13 stills) funcionam.
- O attract demo pode sortear o roster completo.
- O jogo usa o arquivo para gráficos, vozes e extras; música e efeitos
  continuam saindo do SPC700/SNESMOD.

**Importante:** copie sempre `kof98-snes.sfc` e `kof98-snes.msu` do **mesmo
build**, com o mesmo nome-base, na mesma pasta. Use um emulador com suporte a
MSU-1. Se o `.msu` estiver ausente, antigo ou de outro build, a tela
**MSU-1 CHECK** (a primeira do jogo) mostra `UNAVAILABLE` ou os sprites podem
aparecer como blocos de tiles.

### Sem MSU-1

Sem o arquivo `.msu`, o jogo continua rodando, mas com o elenco residente na
ROM:

- **Kyo, Iori, Shingo, Terry, Benimaru, Daimon e Omega Rugal** (este por
  **L+R** na célula do Rugal).
- Esses personagens mantêm as vozes na ROM.
- Rugal normal, Kyo Nests/Kyo Ash e os convidados que dependem de CHR
  streamado ficam indisponíveis.
- O attract demo e o Survivor ficam restritos ao roster da ROM; o final do
  Survivor cai no final normal.
- Música, efeitos, HUD, cenários e o núcleo da luta continuam funcionando.

### Controles

| Botão | Ação |
| --- | --- |
| Direcional | Andar, agachar, pular |
| **Y** | Soco fraco |
| **X** | Soco forte |
| **B** | Chute fraco |
| **A** | Chute forte |
| **L** | Esquiva parada |
| **L + trás/frente** | Rolamento para trás/frente |
| **R** | Blowback (CD) |
| **L + R** | Taunt |
| **START** | Confirmar/avançar nos menus; no Single/Team Play, START no lado da CPU abre a seleção daquele lado |
| **SELECT** | Muda o nível da IA na seleção; durante a luta, abre o menu de pausa (CONTINUE / COMMAND LIST / EXIT) |

### Desculpas e compromisso

Se você encontrou um bug, um golpe que não saiu como deveria, uma voz
cortada, um efeito errado ou um comportamento estranho: **desculpe**. Este é
um projeto de fã, feito com muito carinho, mas ainda em evolução. Alguns
golpes secundários, versões MAX, variações e efeitos ainda estão em
adaptação, e não é um port 1:1 perfeito do original.

A ideia é continuar corrigindo e melhorando. Se algo quebrou, por favor
reporte com o personagem, o modo, o golpe e, se possível, uma gravação ou
save state. Os bugs serão corrigidos nas próximas versões.

### Agradecimentos

Este port não existiria sem os **mitos que extraíram os assets no passado**.
A lista aparece na tela **MSU-1 CHECK**, a primeira do jogo:

```text
THANKS FOR IKARUGA, ZELGADIS,
NEOGOUKI, OHGAKI, M.M.R.,
AHURON, LE@N, MDK, JUANXOC,
TESTP, JERZY, 119WAY,
FERVICANTE, KAMRANBERNSTEIN,
KOOPAKOOT, SANDER71113, EHNYD,
MOUSER, H", VICE, BRAZOMBIE,
GONZO-, JIN, J.LEE
```

Muito obrigado também à comunidade MUGEN, aos mantenedores do PVSnesLib e do
WLA-DX, à cena SNES/SPC700 e aos desenvolvedores de emuladores como Snes9x,
Mesen e bsnes, que tornam possível testar e preservar tudo isso.

Se eu esqueci alguém, me avise: o crédito é de vocês.

### Como compilar

Requisitos: PVSnesLib **4.6+**, WLA-DX (incluído no PVSnesLib) e Python 3.

```sh
make pvsnes PVSNESLIB_HOME=/caminho/para/pvsneslib
make pvsnes-verify PVSNESLIB_HOME=/caminho/para/pvsneslib
```

A saída é:

```text
kof98-snes.sfc   # ROM de 8 MiB
kof98-snes.msu   # dados opcionais (~28 MB)
```

Para jogar com o roster completo, mantenha os dois arquivos juntos. Para jogar
sem MSU-1, use apenas o `.sfc`.

### Por dentro

- `src/engine/fight.asm` — núcleo do motor de luta em 65816.
- `src/snes/fight_bridge.asm` — ponte ASM e mapa de memória do build PVSnesLib.
- `tools/build_fight.py` — converte SFF/AIR/CNS/CMD em tabelas compactas.
- `tools/build_stages.py` e `tools/build_audio.py` — cenários e áudio.
- `docs/` — documentação técnica, lista de golpes e relatórios de validação.

O build experimental standalone (`make`) gera `build/boot-*.sfc` com WLA-DX
puro. O build principal é o híbrido PVSnesLib.

O `.msu` é instalado por arquivo temporário + `rename`, nunca por `cp` direto
sobre o arquivo em uso. Se um emulador estiver aberto durante o build, ele
continua lendo o arquivo antigo até ser reaberto; feche e abra de novo para
pegar o build novo.

### Aviso legal

Projeto de fã, **não oficial e sem fins comerciais**. The King of Fighters,
SNK, Street Fighter, Capcom e todos os personagens, nomes, músicas e artes
pertencem aos seus respectivos detentores. Os assets foram convertidos a
partir de pacotes disponibilizados pela comunidade; todo o crédito aos autores
originais.

---

<a id="english"></a>
## 🇺🇸 English

### A love letter to the SNES

About 30 years ago, when I saw **Street Fighter Alpha 2** running on the Super
Nintendo, I was blown away. At the time, it looked impossible: large
characters, smooth animation, effects, voices... all on a 16-bit console. That
game left a mark on me and taught me something I never forgot: **the SNES,
when someone truly commits to it, can reach places that once seemed
unimaginable.**

Time passed, but the desire to see the SNES pushed to its limits stayed. This
port of **The King of Fighters '98** was born from that obsession: take a huge
fighting game full of systems, characters and effects, and make it fit on
hardware that many people already considered "maxed out" back in the 90s.

This is not an emulator, a wrapper or an official ROM. It is a custom fighting
engine written in **65816 + PVSnesLib**, with assets converted from
MUGEN/KOF '98 packages, running for real on the SNES (or a compatible
emulator).

### What you will find

- **50 fighter entries**, including the KOF '98 cast, guest characters and
  hidden forms.
- **10 stages** converted for the SNES.
- **6 game modes**, plus the attract demo and options.
- **Power gauge**, MAX mode, supers, SDM and Quick SDM.
- **Chains, cancels, specials, supers, projectiles, throws, counters,
  high/low/air blocking, chip damage and blowback**.
- **AI levels 1 to 9**, with per-character personality.
- **PRACTICE mode** with a command list, infinite meter and an idle CPU.
- **3v3 Team Play**, Survivor with its own ending, and a Single Play campaign.
- **Mirror-match palettes** when both players pick the same fighter.
- Music and sound effects through SPC700/SNESMOD; graphics, voices and extras
  can be streamed from the MSU-1 file.

### Port numbers

| Item | Value |
| --- | --- |
| Fighters | **50 entries** (48 base roster + Kyo Nests and Kyo Ash) |
| Stages | **10** |
| Modes | **6**: Single Play, Single VS, Team Play, Team VS, Survivor and Practice |
| Rounds | Best of 3 (first to two wins) |
| AI | Levels **1 to 9** |
| Resolution | 256×224, standard SNES |
| ROM | **8 MiB** (`kof98-snes.sfc`) |
| MSU-1 data | **~28 MB** optional (`kof98-snes.msu`) |

### Fighters

The roster brings together the KOF '98 family and a few special guests:

- **KOF '98:** Kyo, Iori, Shingo, Terry, Andy, Joe, Ryo, Robert, Yuri, Athena,
  Kensou, Chin, King, Mai, Chizuru, Kim, Chang, Choi, Yashiro, Shermie, Chris,
  Yamazaki, Blue Mary, Billy, Lucky, Heavy D!, Brian, Geese, Krauser, Mr. Big,
  Eiji, Saisyu, Heidern, Takuma, Clark, Ralf, Leona, Mature, Vice, Benimaru,
  Daimon, Rugal and Omega Rugal.
- **Guests:** Ryu, Ken, Chun-Li, Sakura and Vega.
- **Kyo variants:** Kyo Nests and Kyo Ash.

Hidden forms:

- **Omega Rugal:** hold **L+R** on Rugal's cell.
- **Kyo Nests / Kyo Ash:** press **L** or **R** on Kyo's cell.
- Regular Rugal requires streamed MSU-1 CHR; without the data file the cell
  shows Omega Rugal and regular Rugal is unavailable.

### Game systems

- **Four-button controls** with shoulder macros: L = dodge, R = blowback,
  L+R = taunt. Direction + button combinations reproduce MUGEN commands
  (QCF, QCB, DP, HCF, HCB, charge, double motions, etc.).
- **Chains and cancels:** light normals chain; heavy normals open special and
  super cancels after connecting.
- **Power gauge and MAX:** activate MAX with **Y+B+X** and spend meter on
  supers, MAX/SDM versions and Quick SDM.
- **Defense:** high, low and air blocking, chip damage, pushback, blowback
  (CD) guard crush, character-specific counters/reversals and throws.
- **Movement:** dash, backdash, jump, standing dodge (L), forward/back roll
  (L + direction) and blowback (R).
- **Combos and juggles:** hit counter, combo decay, projectiles, impact
  sparks, screen shake and KO.
- **Game modes:** Single Play campaign, local versus, 3v3 Team Play, Team VS,
  Survivor and Practice.
- **Practice:** command list in the pause menu, full meter, protected health,
  frozen timer and idle CPU for testing setups.
- **Attract demo:** after a few seconds without input, the ROM plays a
  CPU vs CPU fight and then enters the opening.
- **Options and sound test:** game settings and music playback.
- **P2 palettes:** in a mirror match, the second player gets the next palette
  from the source package.
- **AI:** zoner, rush, grappler and balanced profiles; aggression, defense,
  anti-air, throw and super usage scale with the level.

### With MSU-1

With `kof98-snes.msu` next to the ROM:

- All **50 entries** are available.
- Character tiles are streamed from the MSU-1 file.
- Streamed voices and the 13-still Survivor ending work.
- The attract demo can pick from the full roster.
- The game uses the file for graphics, voices and extras; music and sound
  effects still come from the SPC700/SNESMOD.

**Important:** always copy `kof98-snes.sfc` and `kof98-snes.msu` from the
**same build**, with the same base name, in the same folder. Use an emulator
with MSU-1 support. If the `.msu` is missing, stale or from another build, the
**MSU-1 CHECK** screen (the first screen of the game) shows `UNAVAILABLE`, or
sprites may appear as tile blocks.

### Without MSU-1

Without the `.msu` file, the game still runs, but with the ROM-resident
roster:

- **Kyo, Iori, Shingo, Terry, Benimaru, Daimon and Omega Rugal** (the latter
  via **L+R** on Rugal's cell).
- These characters keep their voices in the ROM.
- Regular Rugal, Kyo Nests/Kyo Ash and guests that depend on streamed CHR are
  unavailable.
- The attract demo and Survivor are restricted to the ROM roster; the
  Survivor ending falls back to the normal ending.
- Music, sound effects, HUD, stages and the core fight still work.

### Controls

| Button | Action |
| --- | --- |
| D-pad | Walk, crouch, jump |
| **Y** | Light punch |
| **X** | Strong punch |
| **B** | Light kick |
| **A** | Strong kick |
| **L** | Standing dodge |
| **L + back/forward** | Back/forward roll |
| **R** | Blowback (CD) |
| **L + R** | Taunt |
| **START** | Confirm/advance in menus; in Single/Team Play, START on the CPU side opens that side's character select |
| **SELECT** | Changes the AI level on the select screen; during a fight, opens the pause menu (CONTINUE / COMMAND LIST / EXIT) |

### Apologies and commitment

If you ran into a bug, a move that did not come out as expected, a cut voice,
a wrong effect or any strange behavior: **I am sorry**. This is a fan project
made with a lot of care, but it is still evolving. Some secondary moves, MAX
versions, variations and effects are still being adapted, and this is not a
perfect 1:1 port of the original.

The plan is to keep fixing and improving it. If something breaks, please
report the character, mode, move and, if possible, a recording or save state.
Bugs will be fixed in future updates.

### Credits

This port would not exist without the **legends who extracted the assets in
the past**. Their names are shown on the **MSU-1 CHECK** screen, the first
screen of the game:

```text
THANKS FOR IKARUGA, ZELGADIS,
NEOGOUKI, OHGAKI, M.M.R.,
AHURON, LE@N, MDK, JUANXOC,
TESTP, JERZY, 119WAY,
FERVICANTE, KAMRANBERNSTEIN,
KOOPAKOOT, SANDER71113, EHNYD,
MOUSER, H", VICE, BRAZOMBIE,
GONZO-, JIN, J.LEE
```

Thank you also to the MUGEN community, the PVSnesLib and WLA-DX maintainers,
the SNES/SPC700 scene, and the developers of emulators such as Snes9x, Mesen
and bsnes, who make it possible to test and preserve all of this.

If I forgot anyone, please let me know: the credit belongs to you.

### How to build

Requirements: PVSnesLib **4.6+**, WLA-DX (bundled with PVSnesLib) and
Python 3.

```sh
make pvsnes PVSNESLIB_HOME=/path/to/pvsneslib
make pvsnes-verify PVSNESLIB_HOME=/path/to/pvsneslib
```

Output:

```text
kof98-snes.sfc   # 8 MiB ROM
kof98-snes.msu   # optional data file (~28 MB)
```

To play with the full roster, keep both files together. To play without
MSU-1, use only the `.sfc`.

### Under the hood

- `src/engine/fight.asm` — the 65816 fighting engine core.
- `src/snes/fight_bridge.asm` — ASM bridge and memory map for the PVSnesLib
  build.
- `tools/build_fight.py` — converts SFF/AIR/CNS/CMD into compact tables.
- `tools/build_stages.py` and `tools/build_audio.py` — stages and audio.
- `docs/` — technical documentation, move lists and validation reports.

The standalone experimental build (`make`) produces `build/boot-*.sfc` with
plain WLA-DX. The main build is the PVSnesLib hybrid.

The `.msu` is installed through a temporary file + `rename`, never by a direct
`cp` over the file in use. If an emulator is open during the build, it keeps
reading the old file until reopened; close and reopen it to pick up the new
build.

### Legal notice

Fan project, **unofficial and non-commercial**. The King of Fighters, SNK,
Street Fighter, Capcom and all characters, names, music and artwork belong to
their respective rights holders. Assets were converted from packages shared
by the community; all credit goes to the original authors.
