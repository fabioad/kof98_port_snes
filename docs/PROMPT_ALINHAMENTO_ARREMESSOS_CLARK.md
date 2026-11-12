# Prompt — Alinhamento e movimento das vítimas dos arremessos do Clark

> **Como usar:** cole o bloco abaixo em um agente de código (Codex/Claude/etc.)
> com acesso a este repositório. O prompt pressupõe que o agente pode ler
> `src/engine/fight.asm`, `tools/build_fight.py`, os CNS/AIR do Clark e rodar
> build, testes headless e capturas no Snes9x.

---

## Papel

Você é engenheiro sênior de jogos de luta retrô, com experiência em 65816,
PVSnesLib, MUGEN e no motor deste port de **KOF98 para SNES**. Trabalhe de
forma investigativa: meça, compare com a origem MUGEN e com o jogo arcade,
e só depois altere código. Não presuma que a tabela gerada está correta.

## Missão

Diagnosticar e corrigir por que os **oponentes agarrados e arremessados pelo
Clark** se movem de forma estranha. O escopo cobre **agarrão normal,
especiais, super e MAX**, além do follow-up Flashing Elbow quando a vítima
estiver presa ou recém-lançada.

O problema não é só "posição errada": usuários relatam que a vítima
**desliza, flutua, teleporta, fica colada, muda de lado, troca de pose na
hora errada ou cai sem arco**. O entregável é a correção do movimento
(trajetória + pose + tempo + contato visual), não apenas um offset novo.

## Contexto do projeto

- Port de KOF98 (base MUGEN) para SNES, 65816, PVSnesLib.
- Tela 256×224; área de luta útil de `STAGE_L=24` a `STAGE_R=232`; chão em
  `GROUND_Y`; cerca de **190 px acima do chão**.
- Motor: `src/engine/fight.asm`. Gerador de dados: `tools/build_fight.py`.
  Dados do Clark: `assets/characters/Clark-KOF98/` (`Clark-H.cns` é a origem
  importada; `Clark_SNES.cns`/`.cmd` são a versão do port).
- A vítima presa **não tem física própria**: a cada tick o `ThrowBind`
  reescreve `F_X`/`F_Y` dela a partir da posição do atacante e de uma janela
  da `BindTab`. O movimento percebido é, portanto, uma função direta da
  tabela de offsets + da animação da vítima + da animação do Clark.
- O atacante pode ter `PosAdd`/`VelSet`/`PinVXUnlessVelSet` durante o
  arremesso; a vítima é arrastada junto.
- Estados de runtime relevantes: `S_TSEQ=75` (sequência de bind),
  `S_VHELD=76` (vítima presa), `S_VTHROW=77` (vítima lançada), `S_KNEE=60`
  (família 60–69, usada pelo Running Three), `S_EXT_GRAB=103` (follow-ups
  importados 103–116) e os slots de counter-grab 99–102.
- `ThrowBind` calcula:
  - `victim.x = attacker.x + facing * dx`;
  - `victim.y = attacker.y - dy` (o Y do motor cresce para cima; `dy`
    negativo no MUGEN significa "para cima");
  - `x` é limitado ao palco; `y` é limitado entre o chão e `MAX_AIR_Y=112`.
- A `BindTab` é indexada por **frame/elemento** (0-based) e usa linhas
  `{lo, hi, dx.s8, dy.s8}` terminadas em `$FF`. O gerador resolve as janelas
  com `canon_bind`, porque o MUGEN executa todos os `TargetBind` que casam e
  o **último vence**, enquanto o motor usa a primeira janela que casa.
- Os offsets são escalados pela `char_scale` do **atacante** (Clark está em
  **0.88** hoje) e o `dy` sofre um **clamp global em −80 px** antes de ser
  gravado em 8 bits.
- A vítima pode usar:
  - pose genérica sintética de 3 quadros (`65004`) para personagens de banco
    fixo, montada a partir de cels de hit (5000/5010);
  - pose "autoral" compactada em 3 cels (`65005`) para personagens MSU;
  - ou uma animação própria, dependendo do mapeamento.
- Vários estados de vítima da origem (`3020`, `3021`, `3022`, `3025`,
  `3026`) são mapeados para o **mesmo slot 76**. Ou seja, o port não troca
  de pose quando o Clark muda de fase do Ultra Argentine; ele mantém um
  único conjunto de poses e move o corpo pelo bind.

## Mapa dos arremessos do Clark

Confirme os sids no mapa atual (`move_ids`, `clarkTargetTab`,
`clarkTransTab` e `build/gen_fight/clark_spr.inc`), pois o ROM diet já
remapou slots várias vezes.

| Classe | Golpe | Estados MUGEN | Slots/sids atuais (conferir) | Observações |
|---|---|---|---|---|
| Normal | Agarrão normal | 800 → 810; vítima 815/816/820/821 | 74 → 75; vítima 76 → 77 | `TargetBind` 8,0 → 0,0 → −16,0 → −32,0 → −48,0, depois sobe e arremessa |
| Especial | Mount Tackle | 1200/1210 | ver `clarkBind99` (estado 1210) | Segura, anda e desce a vítima; bind com vários patamares |
| Especial | Super Argentine | 1300/1310 | conferir no mapa | Agarrão e arremesso curto |
| Especial | Frankensteiner | 1400/1410 → 1420 | conferir no mapa | Fase aérea; release e queda |
| Especial | Napalm Stretch | 1500/1510 | conferir no mapa | Fase aérea |
| Super | Ultra Argentine | 3000/3010 → 3011 → … → 3016 | 85 → 109 → 110 → 111 → 103 → 104 → 105 → 106 | Vítimas 3020–3026 caem no slot 76; 4 danos e duas elevações |
| MAX | Ultra Argentine MAX | 3050 (reusa 3010–3016) | 87 → 109… | Mesma cadeia visual do super |
| Super | Running Three | 3100/3105/3110/3111 | 88 → 62 → 66 → 60 | Agarrão correndo; `VelSet` no atacante; vítima 3120/3121 |
| MAX | Running Three MAX | 3150/3155/3160 | 86 → 64 → 66 → 60 | Reusa o arremesso 3110/3111 |
| Follow-up | Flashing Elbow | 1600/1605/1606 | 112/113/114 | Não é grab, mas o release da vítima importa |

Fora do escopo direto: Vulcan Punch (1000/1010) e Gatling Attack (1100/1110)
são golpes de contato, não agarrões. Se algum deles iniciar um bind por
engano, registre como bug separado.

## Sintomas que precisam ser reproduzidos e classificados

Para cada golpe, verifique e documente:

1. A vítima desliza no chão ou no ar sem passar pelas poses intermediárias.
2. A vítima "teleporta" 40–80 px em um único frame.
3. A vítima fica parada/flutuando no mesmo Y por muitos frames (platô),
   especialmente em −80 px.
4. A vítima é arrastada junto com o Clark mesmo quando a animação dele não
   mostra deslocamento.
5. A vítima aparece na frente/atrás do Clark na hora errada (prioridade de
   sprite, clipping).
6. A vítima vira de lado na hora errada, ou fica de costas.
7. A vítima mantém pose de "hit" (bent-over) durante todo o arremesso, ou
   entra em loop de 3 poses enquanto o Clark executa 6 fases.
8. A vítima é solta cedo, cai reta, atravessa o cenário ou não é lançada.
9. A vítima treme 1 px ou alterna entre dois offsets vizinhos.
10. A vítima entra no HUD/topo da tela ou sai pela borda.
11. O Clark atravessa a vítima no canto, ou a vítima "descola" da mão dele.
12. O movimento muda entre P1 e P2, com/sem canto, ou conforme o tamanho do
    oponente (Choi/Daimon/Athena).
13. O agarrão quebra no meio (vítima liberada) porque o estado do atacante
    saiu da whitelist de `StVictimHeld`.
14. Após KO, tech/escape ou hitpause, a vítima fica presa ou cai de forma
    inconsistente.

## Desafios técnicos que explicam os sintomas

### 1. A vítima é um "boneco de posição", não um corpo com física

O `ThrowBind` reescreve a posição a cada tick. Não existe interpolação,
inércia ou colisão da vítima durante o hold. Qualquer frame sem linha de
bind, linha com janela errada ou transição de estado produz um salto seco.
O movimento só parece natural se a tabela tiver **um offset por frame de
animação** e se a animação da vítima acompanhar a fase.

**Investigar:** para cada frame do atacante, qual linha da `BindTab` casa;
se não casar nenhuma, o que o motor faz; se a vítima anda em passos de 1 px
ou em saltos.

### 2. A tabela é de 8 bits e comprimida

`dx`/`dy` são `s8` (→ −128..127), gravados como bytes. O offset é escalado
por 0.88 e depois limitado a `dy >= −80`. Isso significa:

- offsets altos da origem (por exemplo `−112` e `−168` no Ultra) **não
  cabem** e viram −80;
- o arco vertical é achatado: as duas elevações do Ultra podem ficar no
  mesmo Y;
- um offset de origem grande pode "dar a volta" se alguém remover o clamp
  sem mudar o formato.

**Investigar:** listar todos os `dy` de origem por fase e comparar com o
valor emitido. O platô em −80 é uma decisão de projeto (evitar sprite no
HUD), mas precisa ser reavaliado para o Ultra: talvez comprimir o arco de
forma não linear, reduzir a altura do Clark, ou usar um teto por golpe.

### 3. Janelas de frame, off-by-one e a regra "último vence"

A origem usa `AnimElemTime(N) >= 0 && AnimElemTime(M) < 0`,
`AnimElemTime(N) = 0`, `AnimElemNo(0) = N`, às vezes com espaço antes do
parêntese. O compilador já teve bugs nesses casos e gerou janelas
`0..254`, que prendem a vítima por segundos. O `canon_bind` resolve o
vencedor por frame, mas:

- `F_FRAME` é 0-based; `AnimElem` é 1-based;
- janelas inclusivas (`lo..hi`) podem manter um offset um frame a mais;
- uma linha larga no fim da tabela (ex.: `20,254`) pode segurar a vítima
  até o estado acabar;
- em MUGEN, todos os `TargetBind` casam e o último vence; no motor, a
  primeira janela que casa vence. O gerador precisa continuar honrando
  isso.

**Investigar:** gerar um dump "frame → linha vencedora → dx/dy" e comparar
com a origem. Procurar janelas que nunca são alcançadas, buracos e linhas
`0..254` suspeitas. Hoje há candidatos como `clarkBind66` com
`20,254,14,176` (−80) no fim.

### 4. Eixo do sprite ≠ ponto de contato

O bind posiciona o **eixo** (pés) da vítima, não as mãos/quadril/cabeça. A
pose segurada genérica tem o eixo nos pés; por isso a vítima pode ficar
"pendurada" acima da mão do Clark ou com o tronco dentro dele. Já existe um
ajuste manual desse tipo para o arremesso normal da King (`dy + 35`), o que
prova que o problema é real e que não há uma calibração automática por
personagem.

**Investigar:** para cada vítima, onde está o eixo da animação de hold e
qual ponto do corpo deveria coincidir com a mão do Clark. Medir o erro em
pixels nas três poses (início, meio, fim). Considere uma tabela de
calibração por personagem/golpe em vez de um hack no motor.

### 5. Escala do atacante vs. escala da vítima

Os offsets usam a escala do **Clark** (0.88), mas cada vítima tem sua
própria escala e seu próprio tamanho de sprite. O mesmo bind pode encaixar
no Kyo e flutuar no Daimon ou no Choi. O Ultra Argentine e o Running Three
têm as maiores amplitudes, então são os mais sensíveis.

**Investigar:** matriz com pelo menos 3 silhuetas (baixo/médio/alto) e
medir o erro de contato. Não use um único oponente como referência.

### 6. O clamp de −80 e o teto de 112 achatam o arco

A origem do Ultra chega a `−168`; o port corta em −80. O resultado é que a
"elevação" vira uma mudança horizontal, e as repetições do Ultra podem
parecer idênticas. O `MAX_AIR_Y=112` e o clamp de chão (`y >= 0`) também
alteram o release e o bounce.

**Investigar:** comparar a curva de Y da origem (240 px de palco) com a do
port (190 px). Propor um remapeamento que preserve a **leitura** do arco
(sobe → pausa → desce) e não apenas corte o topo. Meça o custo visual de
deixar o sprite entrar alguns pixels no HUD.

### 7. O atacante se move durante o arremesso

O Clark tem `PosAdd`/`VelSet` no normal throw, no Mount Tackle, no Running
Three e em fases do Ultra. Como a vítima é re-semeada a partir de
`attacker.x`, qualquer deslocamento do Clark a arrasta. Se o `VelSet` for
perdido (ex.: `PinVXUnlessVelSet` zera a velocidade), o Clark anda "no
lugar" e a vítima desliza sozinha; se o `PosAdd` for aplicado no frame
errado, a vítima teleporta junto.

**Investigar:** logar `attacker.x/vx`, `victim.x/vx`, `state`, `frame` e a
linha de bind a cada tick. Separar o movimento autoral do Clark do
movimento da vítima.

### 8. Canto, borda e troca de lado

`AddXClamped` limita a vítima a `STAGE_L..STAGE_R`. No canto, o Clark pode
continuar andando e a vítima para na borda, gerando sobreposição. O
`MINTHROWSEP=24` e o `BackThrowReleaseFar`/`BackThrowLatchFar` tentam
corrigir o lado errado, mas a correção é adiada em 2 ticks justamente para
o bind não sobrescrever — o que pode produzir um "snap" visível.

**Investigar:** reproduzir em x=24, x=128 e x=232, P1 e P2, frente e costas.
Verificar se o snap de 2 ticks é perceptível e se o `Turn` autoral é
respeitado.

### 9. Virada (Turn), facing e back throw

Os `TargetBind` são relativos à direção do atacante. Um `Turn` no estado da
vítima, um `Turn` do atacante ou o flip do back throw mudam o sinal de `dx`.
Se o flip acontece um frame antes/depois da troca de pose, a vítima "pula"
para o outro lado.

**Investigar:** para cada `Turn` da origem, calcular o frame absoluto
(entrada do `TargetState` + `AnimElem − 1`) e conferir o frame em que o port
aplica. Verificar `SetThrowDirFar`, `SelfTurnFar` e o latch de side.

### 10. Release, herança de velocidade e queda

Ao sair de `S_VHELD` para `S_VTHROW`, a vítima recebe `THROWPUSH` (3 px/tick),
`THROWLIFTV` (−5.5 px/tick), `THROWPUSHV` (4.5 px/tick) e sofre
`THROWGRAV` (0.4 px/tick²). Se a origem define `VelSet`/`HitVelSet` e o
`ActTab` não aplica, a vítima cai reta ou desliza. Se o `TargetState` de
release não é mapeado para 77, ela pode ficar presa ou pousar "em pé".

**Investigar:** para cada arremesso, qual estado/vetor a vítima recebe no
release, se o arco é balístico, se o bounce de parede (`StVictimWall` →
`StVictimBounce`) dispara e se o ukemi funciona.

### 11. Pose genérica vs. coreografia

Este é o ponto mais visível. A origem tem estados de vítima distintos por
fase (`3020`, `3021`, `3022`, `3025`, `3026`), mas o port mapeia todos para
o slot 76. Além disso:

- personagens de banco fixo usam `65004`, um loop de 3 poses montado com
  cels de **hit** (5000/5010);
- personagens MSU usam `65005`, também compactado em 3 cels;
- o loop tem duração fixa (6–12 ticks) e não está sincronizado com a
  `BindTab`;
- o `authored_held` pega apenas o primeiro estado com mapeamento 76, então
  as poses das fases seguintes nunca aparecem.

O resultado é uma vítima em pose de "apanhando" que desliza pelo ar, em vez
de ser erguida, virada e arremessada.

**Investigar:** quantas poses a origem usa por fase; quais estão no AIR;
quanto CHR cada uma custa; se é viável mapear 2–3 poses por fase em vez de
um loop único. Para banco fixo, avaliar reuso de cels residentes sem
estourar OAM/CHR.

### 12. Compactação de animação, OAM e frame skipping

O port comprime animações para caber no banco e limita a vítima para não
estourar OAM. Isso remove quadros intermediários justamente nos arremessos
mais longos, o que transforma um arco suave em 2–3 saltos. O `DrawSparks` e
o pipeline de CHR também podem pular slots em condições específicas.

**Investigar:** comparar a contagem de frames da origem com a do port;
medir OAM em cada fase; verificar se o `AnimTick` avança ou repete quadro.

### 13. Pausas, superpause e hitpause

O Ultra/Running Three têm `SuperPause` e `Pause`; o bind é reposicionado
quando o jogo volta. Se a posição for calculada com frame/tempo defasado, a
vítima "congela" no lugar errado e retoma com um salto. O mesmo vale para
hitpause entre os 4 danos do Ultra.

**Investigar:** logar `pausecnt`, `F_STIME`, `F_FRAME` antes/depois de cada
pausa; garantir que o bind não avance durante o freeze.

### 14. Whitelist de `StVictimHeld`

A vítima só permanece presa se o estado do dono estiver em `S_TSEQ`,
`S_CGRAB_HI/LO`, 115, na família 60–69 ou em `S_EXT_GRAB` (109–114). Se uma
fase do Ultra/Running Three cair fora dessa faixa, `VH_free` solta a vítima
no meio do golpe. Isso explica quedas e "desaparecimentos" de pose.

**Investigar:** mapear todos os estados do Clark que seguram a vítima e
conferir a whitelist. Estados novos ou remapeados (ex.: 3050 → 3010, 3150 →
3160) precisam estar cobertos.

### 15. Expressões relativas à vítima

O Running Three usa `TargetBind` com
`(Target,const(size.head.pos.x)) + 48`. O parser atual pode não avaliar
`const(size.head.pos.x)` e cair em 0, gerando um `dx` errado para vítimas
altas/baixas. O mesmo vale para offsets que dependem do `p2bodydist` ou do
tamanho do oponente.

**Investigar:** listar todos os `TargetBind` do Clark com expressões;
verificar o valor emitido e comparar com o esperado para 3 alturas.

### 16. Espelhamento P1/P2 e palette/prioridade

Os offsets são multiplicados pelo `facing`. Em P2, um sinal trocado produz
uma vítima do lado errado. A prioridade de sprite (`SprPriority` 4, −1, 2,
−2 na origem) também muda o desenho: em alguns frames a vítima deve passar
na frente, em outros atrás. Se a prioridade não é reproduzida, o contato
parece "atravessado".

**Investigar:** reproduzir os mesmos golpes com Clark em P1 e P2; comparar
a ordem de desenho de Clark e da vítima frame a frame.

## Protocolo de trabalho

1. **Baseline reproduzível**
   - Build atual: `make` e `make verify`.
   - Para cada golpe, entrar no treino/versus e capturar 2–3 s a 60 fps
     (não só um frame estático).
   - Logar por tick: `state`, `F_FRAME`, `x`, `y`, `vx`, `vy`, `facing`,
     `F_STAB`/`F_STIME`, linha de bind aplicada, `pausecnt`, OAM.
2. **Classificar cada descontinuidade**
   - É autoral (existe na origem/arcade) ou é artefato do port?
   - Comparar com o `TargetBind`/`TargetState`/`PosAdd`/`VelSet` da origem.
   - Se for autoral, documentar e não "suavizar".
3. **Matriz mínima**
   - Golpes: normal, Mount, Super Argentine, Frankensteiner, Napalm,
     Ultra (normal e MAX), Running Three (fraco, forte e MAX).
   - Lados: Clark P1 e P2.
   - Posições: centro, canto esquerdo, canto direito.
   - Vítimas: uma baixa (Choi), uma média (Kyo) e uma alta (Daimon).
   - Estados: normal, guardando, no ar (quando o golpe permitir).
4. **Hipóteses mensuráveis**
   - `clarkBind109` (Ultra): frames 3–5 ficam em −77/−80; o arco de duas
     elevações está achatado?
   - `clarkBind66` (Running Three): frame 1→2 salta ~67 px (0 → −67); é
     autoral ou falta pose intermediária?
   - `clarkBind66`: linha `20,254` mantém −80 até o fim; o estado dura
     quanto?
   - `clarkBind99` (Mount): frame 8→10 desce −76 → −62 → −18; a vítima
     acompanha a mão do Clark ou "escorrega"?
   - `clarkBind75` (normal): a vítima percorre 8 → 0 → −16 → −32 → −48 e
     depois sobe; há frame sem bind no meio?
   - Mapeamento 3020–3026 → 76: a pose nunca muda; comparar com a origem.
   - `TargetBind` com `(Target,const(size.head.pos.x))`: qual `dx` foi
     emitido?
   - Release: qual vetor a vítima recebe e qual estado (77?) ela entra?
5. **Correção**
   - Prefira corrigir no gerador (`tools/build_fight.py`) e nos dados.
   - Só mexa no motor (`fight.asm`) se a limitação for estrutural; explique
     o impacto em CPU/RAM/ROM.
   - Não aumente o clamp de −80 sem avaliar HUD, topo da tela, OAM e o
     tamanho dos sprites.
   - Se precisar de mais de 8 bits por offset, apresente um plano de
     migração (formato novo, compatibilidade, custo) antes de implementar.
6. **Prova visual**
   - Antes/depois em GIF/MP4 ou sequência de PNGs, com o mesmo input e a
     mesma posição inicial.
   - Marcar no vídeo os frames de teleporte/platô para revisão humana.

## Restrições

- Não quebrar os outros 49 personagens nem os arremessos normais já
  auditados.
- Manter o ABI das tabelas (`BindTab`, `ActTab`, `TargetTab`, etc.) sempre
  que possível; mudanças de formato exigem plano e testes de regressão.
- Respeitar o orçamento de CPU do 65816 e a meta de ~59–60 fps.
- Respeitar o orçamento de OAM/CHR; o ROM diet pode ter removido slots.
- Não usar hacks por personagem sem documentar e sem tornar o mecanismo
  reutilizável.
- Manter o texto de docs/release em português (pt-BR), como o restante do
  repositório.
- Se o comportamento da origem for ambíguo, compare com o arcade; a meta é
  **leitura visual no SNES**, não fidelidade pixel a pixel.

## Entregáveis

1. `docs/CLARK_THROW_MOTION_AUDIT.md` com:
   - tabela por golpe/fase: estado, frame, offset de origem, offset emitido,
     posição da vítima, pose, sintoma observado, causa raiz;
   - lista priorizada dos defeitos (top 5) com evidência (trace/vídeo);
   - o que é autoral e o que é artefato.
2. Patch em `tools/build_fight.py` e/ou `src/engine/fight.asm` e/ou dados do
   Clark.
3. Novo teste de regressão, por exemplo
   `tools/tests/test_clark_throw_motion.py`, verificando:
   - delta máximo de X/Y por frame (fora dos frames de snap autoral);
   - nenhum platô no clamp maior que N frames;
   - a vítima avança de pose nas transições de fase;
   - o release tem vetor não nulo e direção coerente com o facing;
   - a vítima não sai do palco nem entra no HUD;
   - P1/P2 e cantos produzem o mesmo resultado.
4. Capturas antes/depois (GIF/PNG) para pelo menos: Ultra normal, Ultra
   MAX, Running Three e agarrão normal, com Kyo e Daimon.
5. Atualização dos docs de release com o que mudou e os hashes do build.

## Critérios de aceite

- Em todos os golpes do escopo, a vítima:
  - mantém contato visual consistente com o Clark (erro ≤ 8 px no ponto de
    contato, nas três alturas testadas);
  - não apresenta teleporte não autoral (variação vertical > 24 px/frame
    fora de frames de snap documentados);
  - não fica mais de 3 frames no mesmo offset de clamp;
  - muda de pose quando o Clark muda de fase;
  - é lançada com arco balístico e pousa corretamente;
  - não fica presa, não atravessa o cenário e não entra no HUD.
- Funciona com Clark em P1 e P2, no centro e nos dois cantos.
- Não há regressão nos 50 arremessos normais nem nos testes existentes.
- `make`, `make verify`, `python3 -m unittest discover -s tools/tests` e
  `python3 tools/test_clark_chains_headless.py` passam.
- A captura de vídeo mostra o antes/depois no mesmo input.

## Comandos úteis

```bash
# build e verificação
make
make verify

# regressão específica do Clark
python3 tools/test_clark_chains_headless.py

# tabelas de bind e shadowing
python3 -m unittest tools.tests.test_clark_super_bind

# auditorias de arremesso
python3 tools/audit_throw_turn_headless.py
python3 tools/audit_release_throws_headless.py

# suíte completa
python3 -m unittest discover -s tools/tests

# captura de um par (índices do roster em test_roster.py)
python3 tools/capture_pair_headless.py <p1_idx> <p2_idx> /tmp/clark.png --frames 120
```

Ferramentas de apoio: `tools/calibration/headless.py` (Snes9x libretro),
`tools/export_snes_frames.py`, `tools/snap_frame.py`, `tools/test_roster.py`,
`tools/normal_throws.py` e o debugger do Mesen
(`tools/mesen_dbg.lua`).

## Formato da resposta

1. Comece com o **diagnóstico**, sem alterar código: tabela de sintomas,
   traces e as 5 causas mais prováveis, ranqueadas.
2. Se faltar informação, liste exatamente quais capturas/logs você precisa
   e por quê.
3. Depois proponha o patch mínimo, arquivo por arquivo, com o impacto em
   ROM/RAM/CPU/OAM.
4. Implemente, rode os testes e anexe a evidência visual.
5. Termine com um resumo em pt-BR do que mudou, o que ficou fora do escopo
   e os riscos restantes.

**Não entregue apenas "aumentei o clamp" ou "mudei o offset".** O objetivo é
fazer o corpo arremessado parecer que está sendo segurado, erguido, girado e
lançado — com trajetória contínua, pose coerente e contato crível em todas as
classes de arremesso do Clark.
