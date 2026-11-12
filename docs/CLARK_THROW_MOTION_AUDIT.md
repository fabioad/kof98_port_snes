# Auditoria do movimento das vítimas dos arremessos do Clark

> Documento de diagnóstico (fase 1 do `docs/PROMPT_ALINHAMENTO_ARREMESSOS_CLARK.md`).
> Medições feitas no ROM de `HEAD` (`e32aba8`), Snes9x headless, sem alterar
> código. A seção 6 lista o patch já implementado e a seção 7 as evidências.

## 1. Método e ferramentas

| Item | Valor |
|---|---|
| ROM base | `kof98-snes.sfc` de 09/11/2026 18:48 |
| sha256 do ROM base | `1729c29507a685178d6d2da814fdd95e8168ae8ffd8bcf6bfaadcef7aef6328a` |
| Core | `snes9x_libretro.so` (headless, `tools/calibration/headless.py`) |
| Trace por tick | `tools/trace_clark_throws_headless.py` (novo) |
| Captura de imagem | `tools/capture_clark_throws_headless.py` (novo) |
| Tabelas | `build/gen_fight/clark_spr.inc` (gerado por `tools/build_fight.py`) |
| Origem | `assets/characters/Clark-KOF98/Clark_SNES.cns`, `Clark.air` |
| Build | `make -f Makefile.pvsnes` (o `make` do `Makefile` raiz não fecha o
banco do `robert` em `HEAD`, falha pré-existente — ver §8) |

O trace registra, a cada tick: estado/frame/`x`/`y`/`facing` do Clark,
estado/frame/anima/`x`/`y`/`grab` da vítima, e o offset relativo
(`dx` = (vítima − atacante)·facing, `dy` = y_vítima − y_Clark, positivo = para
cima). Ele também marca saltos (> 24 px/tick), platôs (mesmo offset por > 12
ticks), troca de pose e release.

Vítima padrão: Kyo (`x` = 110/130, Clark em P1). A matriz P2/cantos/Choi/Daimon
está na §7.2.

## 2. Tabela de sintomas observados

Todos os números abaixo vêm de `build/clark_throw_trace/*.json` e das capturas
em `build/clark_throw_caps/before/`.

| Golpe | Evidência (tick) | Sintoma relatado |
|---|---|---|
| Ultra Argentine (super) | `t28–t412` a vítima fica no **frame 2 de 3** do anim segurado (`nfr=3`), que é o cel `5000,0` — **em pé** | fica "flutuando em pé" no ar |
| Ultra | `t46` `dy` 0→+77 num tick; `t353` `dy` +70→0 e `dx` −12→−32 | teleporte vertical de 70 px |
| Ultra | `t54–t412` `dy` = +80 **sem sair** (platô de 358 ticks) | "parado no mesmo Y" |
| Ultra | `t72, 133, 166, 227, 260, 323` platôs de 20–40 ticks em `dy=+80` | corpo colado no teto |
| Ultra | `t137` (−37,−32), `t143` (+5,+29), `t231` idem, `t237` idem | serrilhado de 30–37 px nas transições 111→103 e 104→105 |
| Ultra (release) | `t413` `y=10` → `t428` `y=39` → `t443` chão | a vítima "pula" 30 px **depois** do slam |
| Ultra (release) | `t415–t419`: `facing` do Clark inverte duas vezes; `x` da vítima 137→84 (−53 px num tick) | troca de lado / teleporte no fim |
| Running Three (fraco/forte/MAX) | `t0` `dx` −34, `t2` `dy` +67, platô `dy=+80` por 240 ticks | vítima "puxada" e depois parada no teto |
| Mount Tackle | `t10` `dx` −26; `t29` `dy` +70; `t65` `dy` −44 | solavanco de 70 px na "subida" |
| Super Argentine | `t37` `dx` −25; `t44` `dy` +26; `t117` `dx` −76 e release 3 ticks depois | teleporte horizontal de 76 px no arremesso |
| Frankensteiner | sem saltos (76 ticks presos), mas `dy` nunca sai de 0 | vítima "colada" no Clark |
| Todos | 1 único anim segurado para 6–7 fases do Ultra | pose não muda quando o Clark muda de fase |
| Todos | OAM da vítima sobe até a linha do HUD (captura `t340`) | "entra no HUD" |

## 3. Origem × port, fase por fase

### 3.1 A pose da vítima não é a da origem

A origem troca a animação da vítima a cada `TargetState` do Clark, e usa
**cels próprios de arremesso** (grupos `5031/5032/5011/5012/5041`) com as
flags `H`/`V`:

| Estado da vítima (origem) | Action | Cels | Flags |
|---|---|---|---|
| 3020 (agarrão/1ª elevação) | 3020 | 5000,0 / 5010,0 / 5010,10 / 5031,40 / 5032,0 | `HV`, depois `V` no loop |
| 3021 (pausa no alto) | 3021 | 5031,30 / 5031,20 | `H` |
| 3022 (giro) | 3022 | 5011,10 / 5031,40 / 5032,0 / 5012,10 | `HV`, `V` |
| 3025 (2ª pausa) | 3025 | 5031,30 / 5031,20 | `H` |
| 3026 (slam) | 3026 | 5031,10/20 / 5011,20/10/0 / 5012,10 | `HV` |
| 3120 (Running Three) | 3120 | 5010,0 / 5041,0 / 5031,10 / 5011,20 | `V` e `H` |
| 3121 (queda do Running Three) | 3121 | 5012,10 | `V` |
| 815 (arremesso normal) | 815 | 5010,10 / 5000,0 / 5011,20 / 5031,10/30 | — |

No port, `VICTIM_STATE_IDS` mapeia **3020, 3021, 3022, 3025 e 3026 todos para o
sid 76**, e o sid 76 da vítima é uma pose compacta de 3 quadros
(`nfr=3`, medido no trace). Resultado: a vítima passa o Ultra inteiro no
quadro 2 — o cel `5000,0`, que é o **personagem em pé** — deslizando pelo ar.

Além disso, `AnimSetFrame`/`DrawCellsFar` só implementam a flag `H`
(`F_FLAGS` bit 0). A flag `V` (bit 1) é gerada na tabela
(`build_fight.py:11261`) e **ignorada** no desenho. Os cels de arremesso da
origem são desenhados de cabeça para baixo; sem o `V` o corpo é desenhado em
pé, e o eixo do sprite (pés) fica no ponto onde deveria estar a cabeça.

Isso explica a maior parte do "flutua": com a pose em pé, o corpo se estende
**para cima** a partir do eixo, e é por isso que o clamp de −80 foi necessário.
Com a pose da origem (corpo invertido/horizontal), o corpo fica **em volta** do
eixo e o clamp pode voltar a ser generoso.

### 3.2 A BindTab perde janelas compostas

`elem_window()` (`build_fight.py:6684`) converte a lista de triggers em **uma**
janela `[lo, hi]`. Quando a origem usa janelas disjuntas na mesma linha — caso
do Super Argentine:

```
value = 0,0   trigger1 = AnimElemtime(3)>=0 && <4 & AnimElemtime(8)>=0 && <9
                      & ... (7 pares)
```

o parser guarda só o primeiro par (`lo=2`, `hi=1`) e `canon_bind` descarta a
janela invertida. A `clarkBind101` emitida tem 6 linhas onde a origem tem 14:

```
101  0-0:(0,0) 1-1:(14,0) 3-3:(-11,0) 5-5:(4,-26) 27-27:(0,0)
```

Frames 6..26 ficam **sem linha de bind**: `ThrowBind` sai sem tocar na posição,
a vítima fica parada e salta quando a próxima linha casa. É o "desliza e
teleporta" do Super Argentine (`t117`: −76 px).

### 3.3 O clamp plano de −80

| Fonte (3010) | ×0,88 | Emitido |
|---|---|---|
| `40,0` | 35,0 | 35,0 |
| `32,0` | 28,0 | 28,0 |
| `36,-88` | 32,−77 | 32,−77 |
| `20,-112` | 18,−98 | **18,−80** |
| `8,-168` | 7,−148 | **7,−80** |

As três alturas da origem (77, 98, 148) viram (77, 80, 80): o arco de duas
elevações do Ultra colapsa e a vítima fica 358 ticks em `−80`.

O clamp existe para o corpo não invadir o HUD, mas o motivo real é a pose em pé
(§3.1). Ele é aplicado globalmente, então atinge os 53 personagens.

Também há uma colisão de janelas em `1210` (Mount): as linhas
`AnimElemtime(11)>=0 && <10` (`−12,−44`) e `AnimElemtime(11)=10` (`−4,−20`)
caem no mesmo frame 10 e a segunda vence — a descida de 44 px vira um degrau de
18 px de uma vez.

### 3.4 Expressões relativas à vítima não são avaliadas

`TargetBind pos = (Target,const(size.head.pos.x)) + 48,0` (Mount 1210,
Super Argentine 1310, Running Three 3110/3160 e Ultra 3010) não casa com o
regex de constantes; o gerador cai em `(0,0)`.

`size.head.pos.x` do Kyo é **4** (`Constants.cns`), então a origem pede
`dx = 52` e o port emite `0` → 52 px (46 px na escala 0,88) de erro no
primeiro frame do agarrão. É o `dx −26` do Mount em `t10` e a causa do
"descola da mão" ao agarrar. A distribuição no roster é −4..8 (mediana 4),
então um valor fixo de 4 mantém o erro ≤ 8 px em todos.

### 3.5 O Ultra e o Running Three são tratados como "arremesso para trás"

`SetThrowDirFar` (`fight.asm:23300`) marca `F_TFLAGS` bit 5 quando a direção
segurada no grab é "para trás". O comando do Ultra (`HCB`) **termina em
trás**, então todo grab HCB/HCF entra no caminho de back throw:

* Clark e a vítima são virados no grab;
* no release, `BackThrowReleaseFar` grava uma posição "na frente" adiada em 2
  ticks e `BackThrowLatchFar` a aplica depois — `t417`: 137 → 84 px num tick;
* o `facing` do Clark oscila (`t415` +1, `t419` −1).

### 3.6 O release sempre lança a vítima para cima

`ThrowRelease` (`menucore.asm:3048`) chama `LaunchVictim` para qualquer
término natural do bind, com `VY = −5,5 px/tick`. No Ultra o slam termina com
a vítima no chão (`y=5`) e ela é lançada 30 px para cima (`t413`→`t428`),
parecendo um ressalto sem motivo.

## 4. Autoral × artefato

| Comportamento | Classificação |
|---|---|
| Salto de 70 px em `3016` elem 7→8 (slam) | **autoral** (a origem desce de −80 para 0) — mas na origem vem junto com troca de pose; no port fica um teleporte |
| Curva 77→98→148 do Ultra | autoral; **achatada** pelo clamp |
| Platô de 22 ticks em `3011`/`3013` (`AnimElemtime(2)>=0` até o fim do estado) | autoral (a origem segura a vítima no alto durante o hitpause) |
| Pausa de 4 hits do Ultra | autoral |
| Vítima em pé no ar | **artefato** (pose errada + sem `V`) |
| Gaps de 20 frames na `BindTab` do 1310 | **artefato** (parser) |
| Teleporte de 53 px no release do Ultra | **artefato** (back throw falso) |
| Pulo de 30 px após o slam | **artefato** (release genérico) |
| `dx` 0 em vez de 52 no primeiro frame | **artefato** (expressão) |

## 5. Top 5 causas (ranqueadas por impacto visual)

1. **Pose única e vertical para todas as fases + flag `V` não renderizada.**
   `3020–3026/3120/3121 → sid 76` e o sid 76 é uma pose de 3 quadros em pé.
   O corpo aparece em pé, flutuando, e o eixo (pés) fica onde a origem põe a
   cabeça. Custo: a vítima nunca é erguida/virada/girada.
2. **`elem_window` colapsa janelas disjuntas** → linhas de bind perdidas
   (Super Argentine perde 8 de 14), frames sem bind, saltos de 40–76 px.
3. **Detecção de back throw dispara em comandos HCB/HCF** → virada dupla e
   teleporte adiado de 24–53 px no fim do Ultra/Running Three.
4. **Clamp plano de −80 + formato s8** → arco achatado, platôs de 20–350
   ticks, duas elevações idênticas.
5. **`(Target,const(size.head.pos.x))+48` avaliado como 0** → 46 px de erro
   no ponto de contato do primeiro frame; some a dependência do tamanho da
   vítima.

Menções honrosas: release que lança para cima depois de um slam (§3.6);
colisão de janelas no `1210` (§3.3).

## 6. Informação que ainda falta

* **Referência visual do arcade/MUGEN**: não há runtime MUGEN nesta máquina.
  A referência usada é o CNS/AIR da origem + a geometria dos cels do SFF
  (§7.1). Se houver vídeo do golpe no arcade, ele fecha a discussão sobre a
  altura máxima aceitável.
* **Ponto exato da mão do Clark** por frame da animação dele: hoje é inferido
  do bind. Medir exigiria caixas de "mão" na animação de bind.
* **Orçamento de OAM por fase**: o contador `RT_OAMDROP` existe; falta rodar o
  perfil `PERF_VERIFY` nas fases novas para provar que o pico continua ≤ 128
  sprites. Fica como verificação no teste headless (§7.3).
* **Choi**: o SFF está em `assets/characters/choi-kofa/` (o nome do roster é
  `choi`); a matriz de 3 alturas usa Choi/Kyo/Daimon.

## 7. Correção

### 7.1 Poses da vítima a partir da origem

A pose é gerada **da própria AIR do Clark** (`3020, 3021, 3022, 3025, 3026,
3120, 3121`) e emitida por personagem como um *pose anim* compacto, usando os
cels equivalentes que já existem no SFF de cada vítima (grupos comuns
`5000/5010/5031/5032/5011/5012/5040/5041`, ligados por *link* no SFF, portanto
sem CHR novo). As flags `H`/`V` e os `xoff/yoff` são preservados.

Escolha de pose por fase (e altura máxima) segue a métrica de extensão acima
do eixo de cada cel: com o corpo **abaixo** do eixo o bind pode subir mais; com
o corpo acima, o teto desce. É esse número que substitui o −80 fixo.

### 7.2 Patch por arquivo, com impacto

| Arquivo | Mudança | Custo |
|---|---|---|
| `tools/build_fight.py` | `elem_window` devolve **todas** as janelas; poses da vítima por fase (`PoseTab`) a partir da AIR do Clark; op `TargetPose` na `ActTab` no frame do `TargetState`; teto de `dy` por pose em vez de −80; `const(size.head.pos.x)` = 4 | +~450 B/personagem de dados (~24 KB no total), +2 B no descritor |
| `src/engine/fast_paths.asm` | `V` flip no `DrawCellsFar`/`DCF_verify` (máscara de Y e bit 7 do attr em `scr5`) | ~40 B de ROM, 0 RAM, ~6 ciclos/cel (≈0,3% de frame) |
| `src/engine/fight.asm` | flag `V` do frame no `draw` do lutador; op 21 `TargetPose`; back throw só no arremesso normal (sid 74/75); release não lança se a vítima já está no chão | ~120 B de ROM, +2 B de descritor, 0 RAM, ~30 ciclos por release |
| `src/engine/fight.asm` | `CH_POSETAB` no descritor | +2 B por personagem |

Nada muda no formato da `BindTab` (linhas de 4 bytes: `lo, hi, dx.s8, dy.s8`
seguidas de `$FF`): o teto passa a vir da pose, não de um clamp global, então
`dy` continua cabendo em `s8` (mínimo usado: −112, o mesmo `MAX_AIR_Y` que o
motor já aplica).

### 7.3 Teste e evidências

* `tools/tests/test_clark_throw_motion.py` — valida as tabelas geradas
  (continuidade, teto por pose, pose por fase, release, expressão).
* `tools/trace_clark_throws_headless.py` antes/depois no mesmo input.
* `tools/capture_clark_throws_headless.py` antes/depois (PNG + folha).

## 8. Observações de infraestrutura

* O `make` do `Makefile` raiz **já falha em `HEAD`**:
  `ValueError: ('meta', 'robert'): no free PVS bank window for 24101 bytes`
  (perfil 0,81 com mapa de bancos fixo). O build oficial é
  `make -f Makefile.pvsnes`; ele passa e gera `kof98-snes.sfc`.
* `make -f Makefile.pvsnes` **não rastreia** as variáveis de ambiente
  `KOF_CHAR_SCALE`/`KOF_SCALE_CAPS`; trocar de perfil sem `touch
  tools/build_fight.py` reaproveita `.chr` do outro perfil e o montador
  segfaulta. Vale registrar como bug separado.
