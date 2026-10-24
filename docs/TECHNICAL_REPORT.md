# Relatório técnico — reconstrução nativa de IKEMEN GO para SNES

Data da auditoria: 2026-10-06

## Escopo e conclusão executiva

O conteúdo de referência foi auditado em `/run/media/fabio/Dados/Fabio/Ikemen_GO-dev-linux`. O diretório não será alterado. O projeto SNES fica em `/run/media/fabio/Dados/Fabio/Ikemen_GO-dev-snes` e já continha um protótipo anterior.

O pacote IKEMEN não é um jogo com roster amplo: ele contém Kung Fu Man em quatro bases de assets, das quais três aparecem no `select.def`. As variantes compartilham quase todo o conjunto de movimentos e arte, com diferenças de resolução, implementação de states e, no caso Z Axis, movimentação/projéteis no eixo Z.

A estratégia correta é uma reconstrução nativa e dirigida por dados. Os formatos DEF/SFF/AIR/CMD/CNS/ZSS/SND devem ser lidos apenas por ferramentas no PC. A ROM deve consumir tabelas binárias compactas, sem parser de texto, Go ou Lua.

Para o vertical slice, a escolha recomendada é:

- Player 1: `kfm_zss`, normalizado para o sistema nativo de states;
- Player 2: `kfm720`, redimensionado offline por redução inteira/nearest-neighbor e com os mesmos timings de gameplay;
- Stage: `stage0` (Training Room), por ser 2D, determinístico e adequado para validar câmera, tilemap e colisões;
- resolução: 256×224 NTSC, 60,0988 Hz;
- mapeamento inicial: Fast HiROM de 4 MiB;
- expansão para ExHiROM somente se o manifesto final convertido, após deduplicação, superar 4 MiB.

## 1. Estrutura encontrada

### Projeto IKEMEN de referência

- `chars/`: quatro diretórios de personagem.
- `stages/`: oito stages selecionáveis, dois deles baseados em modelos GLB 3D.
- `data/`: motif, HUD, fontes, efeitos comuns, AIR/CMD comuns, ZSS de sistemas e `select.def`.
- `sound/`: não contém a música `sound/kfm.mid` referenciada por `stages/kfm.def`; há apenas o placeholder `.keep`.
- `font/`, `video/`, `external/`, `lib/`, `save/`: runtime e conteúdo auxiliar do IKEMEN, não apropriados para inclusão direta na ROM.

### Projeto SNES existente

- `src/engine/fight.asm`: engine de luta 65816 monolítico.
- `src/snes/main.c`: wrapper C que apenas chama `FightMain`.
- `src/snes/fight_bridge.asm`: reservas de WRAM e inclusão do engine ASM.
- `tools/sff.py`: leitor SFF v1/v2 parcial e conversão 4bpp.
- `tools/build_fight.py`: conversor de personagens/stage para dados nativos.
- `tools/build_audio.py`: extrai SNDs IKEMEN, resample para 8 kHz e gera BRR/diretório SPC.
- `src/audio/spc.asm`: driver SPC700 nativo para SFX, separado do protótipo Neo Geo.
- `src/audio/neogeo_spc.asm` e ferramentas de áudio antigas: protótipo não originado no pacote IKEMEN auditado.
- dois caminhos de build: ExHiROM direto via WLA-DX e HiROM via PVSnesLib.

A cópia de `assets/` dentro do projeto SNES possui os mesmos hashes dos arquivos amostrados no projeto original. O desenvolvimento deve continuar usando essa cópia ou uma entrada configurável, nunca escrevendo no diretório `Ikemen_GO-dev-linux`.

## 2. Personagens encontrados

### `kfm`

- nome: Kung Fu Man;
- `localcoord`: 320×240;
- formatos: DEF, SFF v2, AIR, CMD, CNS, SND, storyboards DEF/SFF;
- SFF principal: 205.953 bytes, 281 sprites, 16 paletas;
- AIR: 117 actions;
- CMD: 37 definições de comando;
- CNS: 58 StateDefs, incluindo 47 HitDef/ReversalDef;
- vida: 1000; ataque/defesa: 100/100.

Este personagem existe como base de referência, mas não está diretamente listado em `[Characters]` do `select.def`.

### `kfm_zss`

- nome exibido: Kung Fu Man;
- `localcoord`: 320×240;
- selecionável;
- states em ZSS (`kfm.zss`, `hits.zss`, `command.zss`, `AI.zss`);
- SFF v2: 209.010 bytes, 282 sprites, 16 paletas;
- AIR: 118 actions;
- CMD: 37 comandos;
- 64 blocos StateDef nos arquivos ZSS, contando states negativos de comando/AI.

É a melhor referência para o Player 1 porque representa a implementação IKEMEN moderna sem exigir eixo Z.

### `kfm720`

- nome: Kung Fu Man 720;
- `localcoord`: 1280×720;
- selecionável com `order=0`;
- SFF v2: 1.112.964 bytes, 281 sprites, 17 paletas;
- AIR: 117 actions;
- CMD: 37 comandos;
- CNS: os mesmos 58 StateDefs e 47 HitDef/ReversalDef da versão clássica, com ajustes de escala/coordenadas.

É apropriado para o Player 2 do vertical slice porque fornece uma variante visual distinta e pode ser reduzido offline. Não haverá scaling em runtime.

### `kfm_zaxis`

- nome: Kung Fu Man Z Axis;
- `localcoord`: 320×240;
- selecionável com `order=0`;
- SFF v2: 216.436 bytes, 280 sprites, 16 paletas;
- AIR: 122 actions;
- CMD: 39 comandos, adicionando `UU` e `DD` para movimento no eixo Z;
- 89 blocos StateDef nos ZSS;
- usa função `BoardProjectile`, múltiplos projéteis e `modifyProjectile` para paredes no eixo Z.

Esta variante requer adaptação. No engine SNES 2D inicial, o eixo Z será descartado. Em uma fase posterior, pode ser aproximado como três lanes discretas ou convertido para movimento vertical de profundidade sem scaling. Os projéteis de tábuas podem ser preservados em 2D.

## 3. Stages encontrados

- `stage0` — Training Room, 320×240, câmera horizontal ±125, ground 190, duas camadas normais tiled, SFF com 3 sprites. É o stage do vertical slice.
- `stage1` — Training Stage, 320×240, câmera ±125, três camadas normais tiled, SFF com 5 sprites.
- `kfm` — Mountainside Temple, 320×240, câmera ±150, ground 200, seis elementos visuais com normal/parallax/addalpha, SFF com 8 sprites. Referencia `sound/kfm.mid`, arquivo ausente no pacote.
- `stageZ` — Training Stage Z, 320×240, câmera ±165, zoom 0,75–1, SFF com 6 sprites; recursos de profundidade devem ser simplificados.
- `interactivestage` — Interactive Training Stage, 320×240, attached character, BGCtrl, transparência, reflexos, animações e elementos destrutíveis; SFF principal com 15 sprites e SFF/SND adicionais do attached character. Deve ser portado por último e com scripts pré-convertidos.
- `stage0-720` — Training Room HD, 1280×720, câmera ±500, normal/parallax, SFF com 3 sprites; requer redução offline.
- `stage3d` — Third Heights, 1280×720, modelo GLB de 12.102.424 bytes; SFF contém apenas portrait.
- `stage3d_outline` — variante de Third Heights, GLB de 12.112.576 bytes; SFF contém apenas portrait.

Os stages 3D não podem ser executados como GLB no SNES. A aproximação recomendada é pré-renderizar uma vista 2D em camadas, converter para tiles e usar parallax. Geometria 3D, FOV e zoom contínuo serão descartados.

## 4. Formatos utilizados

### Entrada de build no PC

- `.def`: metadados, referências, câmera, stage e motif.
- `.sff`: sprites/paletas; os arquivos auditados usam SFF v2.
- `.air`: actions, frames, offsets, flips, duração e caixas Clsn1/Clsn2.
- `.cmd`: comandos, janela de execução, buffer e regras de entrada de state.
- `.cns`: constantes, StateDefs e state controllers MUGEN.
- `.zss`: states e funções IKEMEN modernas.
- `.const`: constantes das variantes ZSS.
- `.snd`: bancos de samples MUGEN/IKEMEN.
- `.mid`: referência de BGM no stage KFM, ausente na origem; o `mario.mid` do protótipo SNES não pertence ao conteúdo auditado.
- `.glb`: stages 3D, apenas para pré-render/conversão offline.

### Saída nativa proposta

- tiles 4bpp SNES e paletas BGR555;
- tilemaps de 16 bits;
- metasprites com células 8×8/16×16 e índices já resolvidos;
- actions compactas com frame, duração, flags, caixas e eventos;
- states compactos com opcodes somente para controllers utilizados;
- tabela de comandos pré-compilada;
- amostras BRR e sequências de música/SFX para SPC700;
- manifesto por banco, com offsets de 24 bits e checksums de build.

## 5. Funcionalidades realmente utilizadas

### Movimento e física

- idle, turn, crouch transitions, walk forward/back;
- run forward e hop backward;
- pulo baixo com toque em cima, pulo comum com cima mantido e pulo alto com baixo→cima/diagonal ou cima durante o dash para frente;
- gravidade 0,44, velocidades fracionárias e fricção;
- autoturn e limites de stage.

Constantes clássicas relevantes:

- walk forward: 2,4 px/tick;
- walk backward: 2,2 px/tick;
- run: 4,6 px/tick;
- jump neutral: -8,4 px/tick;
- pulo baixo: -6,5 px/tick; pulo alto: -10,5 px/tick;
- jump forward/back: 2,5/-2,55 px/tick;
- pulo alto diagonal: 1,5× a velocidade horizontal comum; durante dash: 4,6 px/tick para frente;
- liedown: 60 ticks.

### Ataques básicos

- standing: states 200, 210, 230 e 240;
- crouching: 400, 410, 430 e 440;
- aéreos: 600, 610, 630 e 640;
- throw: 800/810;
- light/strong chains e cancelamentos condicionados por `movecontact` e tempo;
- cancelamento especial/super: os normais fortes (`6, 8, 20, 22, 24, 26`)
  só abrem a janela depois de conectar (`F_HITDONE`) e a partir do elemento
  definido pelo bloco `[State -1, Combo]`/`var(1)` do CNS do personagem,
  limitado ao meio da animação quando a fonte não traz janela. O
  `CmdTryCancel` aceita apenas especiais (`48-66`) e supers (`85-89`), para
  um normal conectado não virar provocação, corrida ou agarre; os normais
  leves mantêm o cancelamento por contato anterior. A linha de abertura vem
  do word `CH_CANCELROW` do descritor, mas a tabela `CancelTab` mora no banco
  de dados do motor: o `CancelGate` corrige o banco do ponteiro antes de
  indexar. Sem isso o gate desreferenciava o ponteiro uma vez a mais e lia
  um byte do banco de tabelas do personagem, fechando a janela dos
  importados (Ryu, Ken, Sakura, Ryo e Robert) e abrindo-a por acaso nos
  personagens fixos.

Parâmetros básicos do KFM clássico que devem ser preservados:

- soco fraco: damage 23, active em AnimElem 3, hitpause 8/8, hitstun 11, pushback -4;
- soco forte: damage 57, active em AnimElem 3, hitpause 12/12, hitstun 16, pushback -5,5;
- chute fraco: damage 26, HitDef desde time 0, hitpause 12/12, hitstun 14, pushback -5;
- chute forte: damage 63, HitDef desde time 0, hitpause 12/12, hitstun 17, pushback -6;
- sweep: damage 72, low/trip, fall habilitado.

### Especiais, supers e defesa

- Kung Fu Palm: states 1000/1010/1020;
- Kung Fu Knee: 1050/1060/1070;
- Kung Fu Upper: 1100/1110/1120;
- Kung Fu Blow: 1200/1210/1220;
- active blocking alto/baixo/aéreo: 1300–1351;
- Kung Fu Zankou: 1400/1410/1420;
- Triple Kung Fu Palm: 3000;
- Smash Kung Fu Upper: 3050/3051;
- power checks de 330 e 1000;
- ReversalDef, invulnerabilidade temporária, SuperPause, hitpause, hit/guard sounds e efeitos.

### Sistema de comandos

- QCF, QCB, dragon-punch, double-QCF e double-QCB;
- double tap F/B; Z Axis também U/U e D/D;
- botão + direção, botões simultâneos, hold, release e janela de charge;
- default de 15 ticks e buffer de 1 tick; ZSS/Z Axis usam buffer de 3 ticks nos especiais.

### Colisões

- AIR clássico possui 449 declarações Clsn1/Clsn2 e 973 retângulos somente no KFM base;
- Clsn1 é hitbox e Clsn2 é hurtbox;
- caixas podem ser default por action ou substituídas por frame;
- pushbox também depende de `[Size]` e controllers `Width`, não da bounding box visual.

### HUD e rounds

- motif 1280×720 deve ser reinterpretado em 256×224;
- barras de vida, power, portraits/names, timer, combo/hit count, round/KO/win;
- `match.wins=2`, máximo de um draw game;
- a configuração visual do motif usa tempos zero em alguns displays, mas as regras de round são válidas.

## 6. Funcionalidades descartáveis ou aproximáveis

Podem ser descartadas no vertical slice:

- parser Go/Lua/ZSS/CNS em runtime;
- storyboards de intro/ending externos;
- menu completo, arcade paths, unlock Lua, modes Simul/Tag/Turns/Ratio;
- AI hints e AI ZSS avançada;
- ranking, training overlays, score, dizzy e guard-break globais;
- shaders, GLB, zoom contínuo, FOV 3D;
- reflexos alpha exatos, shear do HUD e palfx senoidal;
- attached characters e BGCtrl do interactive stage;
- suporte genérico a todos os state controllers MUGEN/IKEMEN.

Aproximações documentadas:

- Z Axis inicialmente colapsado para 2D;
- alpha de stages convertido para tiles já compostos ou color math fixo;
- 3D convertido para camadas 2D pré-renderizadas;
- sprites HD reduzidos offline sem bilinear/blur;
- caixas preservadas após transformação de coordenadas, com arredondamento conservador;
- samples/vozes selecionados conforme orçamento de ARAM.

## 7. Estimativa dos assets

### Origem relevante

- quatro SFFs principais de personagem: aproximadamente 1,74 MiB comprimidos no formato de origem;
- quatro AIRs: aproximadamente 193 KiB;
- CMD/CNS/ZSS/CONST de personagem: aproximadamente 410 KiB de texto;
- quatro SNDs de personagem: 76.631 bytes cada, mas são cópias equivalentes;
- SFFs dos oito stages: aproximadamente 326 KiB, sem contar GLB;
- dois GLBs: aproximadamente 23,1 MiB, não incluíveis diretamente;
- fight/common/system SND: aproximadamente 10,0 MiB no formato de origem;
- fight/fightfx/system SFF: aproximadamente 9,8 MiB, dominados pelo motif HD.

### Conversão estimada

O conversor atual gera, para apenas 12 actions do KFM:

- 73 sprites referenciados;
- 5.816 tiles 8×8 antes de cache/deduplicação global;
- 186.112 bytes de gráficos 4bpp;
- stage0: 229 tiles, 7.328 bytes, tilemap de 1.792 bytes;
- HUD provisório: 784 bytes de tiles.

Para o vertical slice, após deduplicação por tile e frames compartilhados:

- dois personagens: 0,45–0,90 MiB;
- stage e HUD: 32–96 KiB;
- animações/states/comandos/colisões: 64–160 KiB;
- áudio BRR e sequências: 128–512 KiB;
- código e tabelas: 128–256 KiB;
- total útil esperado: 1,0–2,0 MiB, cabendo confortavelmente em HiROM 4 MiB.

Para todo o conteúdo 2D auditado, com compartilhamento entre variantes KFM e sem duplicar os quatro SNDs, a estimativa é 2,5–3,8 MiB. Os stages 3D pré-renderizados e o motif completo podem elevar o total acima de 4 MiB. A decisão ExHiROM só será tomada a partir do relatório de tamanho gerado pelo pipeline final.

## 8. Riscos técnicos

### Críticos

- O build PVSnesLib atual não é reproduzível: `fight_bridge.asm` não encontra `fight.asm` porque o comando do `snes_rules` não recebe o include path esperado.
- O build direto gera ExHiROM de 8 MiB com título `SNES BOOT MARIO`, embora o conteúdo útil seja muito menor.
- A ROM direta usa música e samples de outro protótipo, não do IKEMEN auditado.
- A configuração OBJ atual é inválida: `OBSEL=$03` não seleciona a base onde os tiles são carregados; todas as células são marcadas como large (32×32), mas o conversor gera células 16×16.
- O layout de quatro tiles de cada célula 16×16 é linear; OBJ 16×16 do SNES espera stride apropriado na página de tiles.
- P2 usa offset de 128 tiles apesar de receber uma janela de 8 KiB, causando sobreposição lógica; uma janela de 8 KiB corresponde a 256 tiles 4bpp.
- A colisão atual usa a bounding box visual inteira do metasprite, ignorando Clsn1, Clsn2 e pushbox.
- Não há guard, hitstun/guardstun reais, pushbox entre jogadores, rounds best-of-three, comandos especiais ou efeitos do IKEMEN.

### Altos

- streaming atual pode copiar dois frames, OAM completo e HUD completo no mesmo frame sem orçamento de VBlank;
- forced blank é ativado durante a apresentação, mascarando excesso de transferência com tela apagada;
- não há medição de sprites/slivers por scanline;
- não há validação de máximo de células por metasprite nem limite de 128 OAM entries;
- tool `sff.py` tem suporte parcial a truecolor PNG em SFF v2;
- o parser AIR atual ignora as caixas;
- o stage atual é achatado para uma única imagem 256×224, não preserva largura/câmera/parallax;
- o Makefile executa cada gerador múltiplas vezes ao usar `make -B`, pois múltiplas saídas não são agrupadas.

### Médios

- PVSnesLib adiciona runtime útil, mas o engine atual é praticamente todo ASM e não aproveita C de alto nível;
- WRAM reservada não tem mapa compartilhado gerado/verificado contra o runtime;
- o pacote original não inclui a BGM `sound/kfm.mid` referenciada pelo stage Mountainside Temple;
- stages 3D e Interactive Stage exigem conversão especial e aproximações.

## 9. Estratégia de conversão

### SFF → SNES

1. ler SFF v1/v2 no PC;
2. transformar coordenadas para 256×224 conforme `localcoord`;
3. reduzir sprites HD apenas por escala inteira/nearest-neighbor ou algoritmo pixel-art determinístico;
4. quantizar por personagem/paleta para 15 cores visíveis + transparência;
5. deduplicar tiles considerando flip H/V;
6. empacotar células OBJ com layout real do SNES;
7. escolher automaticamente 8×8/16×16 por frame e validar OAM/scanline;
8. gerar preview PNG e relatório de perdas.

### AIR → animação e colisões

1. preservar todas as durations e loopstart;
2. converter Clsn1/Clsn2 por frame, incluindo defaults;
3. normalizar retângulos e coordenadas após scaling;
4. gerar keyframes sem remover frames arbitrariamente;
5. anexar eventos de frame vindos de HitDef/PlaySnd/state;
6. validar que startup/active/recovery resultantes correspondem ao original.

### CMD → recognizer compacto

- histórico circular de 20–30 ticks por jogador;
- direções normalizadas em relação ao facing;
- símbolos press/hold/release/4-way/simultaneous;
- comprimento, janela e buffer pré-compilados;
- prioridade preservada pela ordem do CMD;
- mapeamento SNES: Y=x (soco fraco), X=y (soco forte), B=a (chute fraco), A=b (chute forte);
- ombros roteados por `PushHist`: L=c (esquiva parada), L+trás/L+frente = rolls, R=blowback (`y+b`), L+R=taunt (`s`).

### CNS/ZSS → state data

Não haverá compilador genérico de toda a linguagem. A ferramenta extrairá apenas:

- StateDef, anim, ctrl, velset, physics, poweradd;
- ChangeState/ChangeAnim;
- VelSet/VelAdd/PosAdd;
- HitDef/ReversalDef;
- PlaySnd/Explod;
- NotHitBy/HitBy;
- pausas e eventos simples;
- triggers limitados a time, animelem, animtime, ctrl, state type, command, movecontact, vida e power.

Expressões fora do subconjunto serão sinalizadas no build e convertidas manualmente para callbacks nativos quando necessário.

### Stage → tilemaps

- converter elementos separadamente, não rasterizar o stage inteiro;
- tiles 8×8 deduplicados e mapas 32×32/64×32;
- BG1 para plano principal, BG2 para parallax/elementos distantes, BG3 para HUD;
- câmera em coordenadas de mundo e scroll via registradores;
- animação por substituição de tile/mapa;
- color math apenas quando necessário;
- pre-render 2D para GLB.

### Áudio

- analisar SND e extrair samples no PC;
- converter WAV/PCM para BRR com loop validado;
- manter um driver SPC700 nativo com comandos de BGM e SFX;
- reservar 32–40 KiB de ARAM para driver/eco/sequência e 24–32 KiB para samples residentes;
- trocar bancos de voz/BGM entre rounds quando necessário;
- prioridade: impactos, vozes essenciais, instrumentos principais.

## 10. Arquitetura proposta

### Código 65816

- reset/NMI/IRQ e inicialização de PPU/APU;
- fila DMA e execução estrita em VBlank;
- upload de OAM/CGRAM/VRAM;
- montagem de metasprites e culling por scanline;
- primitivas AABB e fixed-point críticas;
- descompressão de tiles, se profiling justificar.

### Código C

- máquina de rounds e match;
- state machine dos lutadores;
- física e câmera em fixed-point;
- command recognizer;
- aplicação de HitDef, hitstun, guardstun, pushback e cancelamentos;
- gestão de animação, eventos, projéteis e efeitos;
- HUD e regras de KO/vitória.

### Dados gerados

- `game_manifest.bin`: diretório de personagens/stages/bancos;
- `char_*.bin`: constants, commands, states, actions, caixas e referências de gráficos/áudio;
- `stage_*.bin`: câmera, camadas, tilemaps e animações;
- `gfx_*.bin`: tiles/paletas comprimidos ou banked;
- `audio_*.bin`: BRR e sequências;
- includes gerados apenas para símbolos de link, nunca grandes tabelas textuais desnecessárias.

## 11. Mapas preliminares

### ROM Fast HiROM, 4 MiB

Endereços são preliminares e deverão ser emitidos pelo linker/manifesto:

```text
C0:0000-C1:FFFF  reset, runtime C, engine 65816, tabelas globais
C2:0000-C3:FFFF  HUD, fonte, fight FX, dados de rounds
C4:0000-C7:FFFF  Player 1: lógica, animações, colisões, gráficos
C8:0000-CB:FFFF  Player 2: lógica, animações, colisões, gráficos
CC:0000-CD:FFFF  stage0, tilemaps, palettes e parallax
CE:0000-D1:FFFF  áudio SPC, BRR, sequências e vozes
D2:0000-DF:FFFF  reserva para especiais, efeitos e expansão do slice
E0:0000-FF:FFFF  expansão para demais personagens/stages dentro de 4 MiB
```

A alocação real deve ser compacta; não é necessário preencher bancos vazios com conteúdo duplicado. HiROM foi escolhido porque o slice estimado cabe em 4 MiB, facilita blobs maiores e evita o ExHiROM arbitrário de 8 MiB do protótipo.

### WRAM, 128 KiB

```text
7E:0000-1FFF  runtime C/PVSnesLib, stack e direct page reservados pelo linker
7E:2000-27FF  globals, round manager, câmera e fila DMA
7E:2800-2FFF  dois fighters, projéteis e efeitos
7E:3000-33FF  históricos de input e command matcher
7E:3400-3FFF  animação, colisão e scratch
7E:4000-421F  shadow OAM completo (544 bytes)
7E:4220-49FF  shadow do HUD/tilemap e dirty regions
7E:4A00-5FFF  stage state, filas de eventos e áudio
7E:6000-7FFF  staging de DMA/decompressão (8 KiB)
7F:0000-7FFF  cache de tiles/frame e buffers de conversão runtime
7F:8000-FFFF  reserva, debug e expansão
```

O mapa será formalizado em RAMSECTION/linker e verificado contra o `.sym`.

### VRAM, 64 KiB, offsets em bytes

```text
0000-1FFF  BG1 tiles do stage                  8 KiB
2000-37FF  BG2/parallax e stage dinâmico       6 KiB
3800-3FFF  HUD/fonte BG3                       2 KiB
4000-47FF  BG1 tilemap                         2 KiB
4800-4FFF  BG2 tilemap                         2 KiB
5000-57FF  BG3 HUD tilemap                     2 KiB
5800-5FFF  efeitos BG / reserva                 2 KiB
6000-AFFF  cache OBJ compartilhado            20 KiB
B000-D7FF  working set Player 1               10 KiB
D800-FFFF  working set Player 2               10 KiB
```

O layout OBJ final será alinhado às restrições de `OBSEL`. O cache será por tiles, não por frame bruto. Se um único frame exceder o working set, o conversor deverá reempacotar/deduplicar ou rejeitar o asset; nunca sobrescrever VRAM silenciosamente.

### CGRAM

```text
BG palette 0-3    stage principal/parallax
BG palette 4      HUD/fonte
BG palette 5-7    efeitos e reserva
OBJ palette 0     Player 1
OBJ palette 1     Player 2
OBJ palette 2-5   efeitos/projéteis/alternates
OBJ palette 6-7   reserva
```

### ARAM, 64 KiB

```text
0000-01FF  IPL/zero page/hardware
0200-1FFF  driver SPC700, stack e buffers
2000-2FFF  sequência BGM e estado de canais
3000-7FFF  samples BRR residentes
8000-BFFF  banco trocável de voz/SFX
C000-FFFF  echo buffer ou banco adicional, conforme configuração
```

O echo buffer poderá ser reduzido ou desabilitado para priorizar samples.

## 12. Toolchain recomendado

- PVSnesLib 4.6 ou mais recente, disponível em `/run/media/fabio/Dados/Fabio/pvsneslib/pvsneslib`;
- WLA-DX fornecido pelo PVSnesLib para C/ASM/link;
- Python 3.14.4 para conversores;
- Pillow já usado no protótipo, com quantização sem blur/interpolação bilinear;
- bsnes e Snes9x/libretro para validação automática;
- Mesen disponível em `/home/fabio/.local/bin/mesen` para validação adicional;
- testes Python para parsers/conversores;
- verificadores de header/checksum, mapa de memória, DMA budget, OAM e scanlines.

Recomendação: manter um único build Fast HiROM reproduzível. O build ExHiROM experimental deve deixar de ser o alvo padrão depois que o build HiROM for corrigido.

## 13. Plano incremental

### Fase 0 — baseline reproduzível

- corrigir includes e dependências do Makefile PVSnesLib;
- gerar uma única ROM HiROM de 4 MiB com título correto;
- remover dependência do áudio Mario/Neo Geo do alvo principal;
- criar smoke tests em bsnes, Mesen e Snes9x.

### Fase 1 — pipeline de assets correto

- completar parser SFF v2;
- parser AIR com Clsn1/Clsn2;
- quantização de 16 cores e deduplicação de tiles;
- packer OBJ válido e relatórios OAM/scanline/VRAM;
- conversão de `stage0` como tilemap/layers, com largura e câmera.

### Fase 2 — vertical slice de gameplay

- `kfm_zss` e `kfm720` como dois descriptors de personagem;
- idle, walk, crouch, jump e quatro ataques em pé;
- hitbox, hurtbox e pushbox por frame;
- damage, hitpause, hitstun, pushback, KO;
- HUD, best-of-three, round reset, vitória;
- dois controles humanos e fallback de dummy/AI simples.

### Fase 3 — fidelidade do slice

- ataques crouching/aéreos, throw e guard;
- comando buffer e especiais principais;
- sparks, sons, vozes e BGM válida;
- câmera horizontal e parallax;
- profiling de VBlank e estabilidade a 60 FPS.

### Fase 4 — expansão

- supers, reversals e projéteis;
- KFM Z Axis aproximado;
- Mountainside Temple, Stage1, StageZ e stage0-720;
- Interactive Stage simplificado;
- stages 3D pré-renderizados;
- seleção de personagem/stage e conteúdo restante.

## 14. Estado de validação da baseline em 2026-10-06

- `make pvsnes-verify`: falhou ao recompilar `fight_bridge.asm`, pois `fight.asm` não foi localizado.
- `make -B verify`: gerou e validou header/checksum de uma ROM Fast ExHiROM de 8 MiB, mas com warnings de velocidade conflitante e título `SNES BOOT MARIO`.
- o gerador foi executado repetidamente por causa da modelagem incorreta de múltiplas saídas no Makefile.
- bsnes/libretro executou 120 frames e gerou imagem apenas do stage, sem HUD ou lutadores.
- Snes9x/libretro não concluiu a execução limitada e precisou ser interrompido.
- não há evidência de funcionamento em hardware real.

Portanto, a primeira tarefa de implementação é corrigir o build e o subsistema gráfico OBJ antes de adicionar novos golpes ou personagens.

## 15. Estado do vertical slice após a correção da baseline

A baseline recomendada já foi corrigida e o slice atual usa `kfm` no Player 1 e `kfm720` no Player 2. O uso do `kfm` clássico em vez de `kfm_zss` foi uma escolha incremental: seus AIR/CNS/CMD já estão integrados ao pipeline nativo, enquanto os states ZSS exigem uma camada adicional de compilação de estado.

Implementado e validado:

- build único Fast HiROM de 4 MiB por `Makefile.pvsnes`, com `PVSNESLIB_HOME` configurável;
- engine 65816 em `src/engine/fight.asm`, sem runtime Go/Lua/IKEMEN;
- geração reproduzível de sprites, paletas, metasprites, AIR, CNS e CMD por personagem em `build/gen_fight/`;
- descriptors `CharKfm` e `CharKfm720` com sprites, caixas, animações, ataques, comandos, CHR, paleta e nome independentes;
- `kfm720` normalizado offline por escala 4× para o espaço 320×240;
- bancos separados para tabelas/gráficos de cada personagem e paletas OBJ separadas;
- shadow OAM contíguo com tabela baixa de 512 bytes e tabela alta em `OAMBUF+512`, eliminando bits aleatórios de tamanho/X alto;
- movimento, virada, caixas AIR espelhadas, quatro ataques básicos, dano CNS, hitstun, slide, knockback, KO e reinício de round;
- áudio SPC700 nativo com 12 clips BRR derivados de SNDs IKEMEN e comandos para Round/Fight, swishes, hits, landing e KO;
- teste determinístico em RetroArch/Snes9x por `tools/test_fight_remote.py`, usando controle remoto binário e `READ_CORE_RAM`.

Validações observadas no teste atual:

- P1: descriptor `CharKfm`, banco de tabelas `$F8`;
- P2: descriptor `CharKfm720`, banco de tabelas `$EF`;
- `kfm720` seleciona a paleta OBJ 1 (`attr=$73`; os bits altos são flip horizontal);
- golpes do P1 causam `23/57/26/63` pontos de dano conforme CNS;
- golpe fraco do `kfm720` produz `hitstun=14` e `slide=12`, diferindo do `kfm`;
- KO zera HP, entra em `gamestate=2` e reinicia com HP `200/200`;
- o alvo `clean` foi corrigido removendo a dependência inexistente `cleanLogs`.

### Áudio SPC700 integrado

- `tools/build_audio.py` seleciona 12 eventos dos contêineres IKEMEN (`kfm.snd`, `common.snd` e `fight.snd`), resample para 8 kHz e gera `spc_brr.bin`, `spc_dir.bin`, `spc_ids.inc` e `spc_tables.inc` em `build/gen_audio/`.
- O banco gerado usa 25.254 bytes de BRR; o bloco SPC completo `spc_boot.bin` tem 28.836 bytes e ocupa ARAM `$0200-$72A3`, com diretório DSP em `$0F00` e samples a partir de `$1000`.
- `src/audio/spc.asm` é um driver SPC700 nativo, separado do protótipo Neo Geo/Mario. Ele usa as vozes 6/7 alternadamente e reconhece `APUIO0=2` como comando SFX com ID em `APUIO1`; `APUIO2` carrega um contador de sequência útil para depuração.
- O 65816 faz upload IPL em `AudioInit`, com timeouts em todas as esperas. `SfxPlay` também limita espera por porta livre/ack; se a APU não responder, `audiordy` permanece zero e o loop de luta continua.
- Eventos conectados: Round/Fight no início do round, swish por estado de ataque, HitDef hit sound por força (`5,0`, `5,1`, `5,2`), landing e KO.
- Validação Snes9x/RetroArch: `audiordy=1`, sequência inicial `2` e último SFX `10` (Fight); landing produz ID `8`; os quatro ataques incrementam a sequência em 2 e terminam nos IDs `4/6/5/6`; KO observa ID `11`; restart volta a `10` após Round/Fight.
- ROM final da rodada: `fighting-engine.sfc`, 4 MiB, checksum `$B391`, SHA-256 `bad7db4a79d2e6c83ab760bb235f0a7a0440895d5749aa7366077dc9b4c4e305`.

### Compatibilidade observada nesta rodada

- RetroArch/Snes9x: suíte completa `tools/test_fight_remote.py --launch` passou com movimentação, paleta P2, colisões AIR ativas somente nos frames corretos, dano `23/57/26/63`, IA KFM720, áudio, KO e restart.
- bsnes standalone v115: `fighting-engine.sfc` carregou e renderizou os dois lutadores no stage a aproximadamente `60 FPS`, com os metasprites compostos corretamente; evidência em `build/bsnes_oamhi_final.png`.
- Mesen GUI: a ROM carregou e renderizou a luta a `60 FPS`; evidência em `build/mesen_audio.png`. Uma leitura Lua com `emu.memType.snesWorkRam` observou `gamestate=1`, `oamtop=$00A4`, P1 `x=$5000/hp=200` e P2 `x=$9200/hp=200`.
- O modo `--testrunner` desta instalação local do Mesen segfaulta antes de executar até mesmo `emu.stop(0)` (exit `139`), então a validação Mesen usou a GUI + script carregado pela linha de comando, não o runner headless.

Restrições conhecidas do slice atual:

- apenas estados básicos e ataques em pé estão compilados para a ROM;
- há SFX nativo, mas ainda não há BGM IKEMEN nem todas as vozes/efeitos do conteúdo original;
- os SNDs multi-megabyte continuam fora da ROM: apenas os 12 clips priorizados foram convertidos;
- seleção de personagem, câmera lateral e conteúdo além do `stage0` ainda não foram integrados;
- ainda não há validação em console real.
