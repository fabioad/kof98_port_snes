# KOF '98 SNES — versão 1.1.1 (07/11/2026)

Esta rodada fecha a apresentação dos agarrões e dá uma passada de arte na
seleção, no ORDER SELECT e no HUD. **A ROM não foi commitada**: o build está
em `kof98-snes.sfc` + `kof98-snes.msu` para validação.

## Agarrões (normal, especial e super)

- **Vítima segurada anima**: o slot de vítima presa agora usa um loop curto de
  três poses montado com os cels 5000/5010 que todo personagem já tem na ROM.
  Não houve aumento de CHR nem de sprites por personagem.
- **Voo do arremesso**: a vítima arremessada usa a pose aérea de hit (anim
  5030) em vez do quadro estático de queda (5050).
- **Lançamento fonte 816**: ao terminar um agarrão, a vítima recebe a
  velocidade do estado 816 do arcade/MUGEN (5,5 px/tick para cima e
  4,5 px/tick para longe, relativo à direção da vítima). Isso vale para
  agarrões normais, especiais e supers que soltam pelo `TargetState 77`.
- **Correção de altura**: o clamp de altura da vítima comparava um valor 8.8
  com um byte cru. O resultado prendia toda vítima a ~0,4 px do chão. Agora
  o limite de 112 px é aplicado em ponto fixo, então o arco de queda existe
  de verdade.
- **Canto**: a vítima arremessada quica na borda em vez de ficar colada nela,
  e o corpo deitado ganha 16 px de margem para não sair da tela.
- **Interrupção**: se o agarrador for acertado no meio do golpe, a vítima
  continua caindo pelo caminho antigo (sem ganhar o lançamento completo).

## Arremesso da Leona

- O estado de bind da Leona (`805`) usa um `anim = IfElse(...)`. O parser não
  resolvia a expressão e caía na arte de **idle**, então ela ficava parada
  enquanto a vítima se mexia nos binds.
- O build agora usa o ramo normal da expressão (`805`) e compacta a animação
  em três poses-chave da própria Leona. Ela volta a agachar, segurar e
  arremessar; os binds, dano e a vítima continuam iguais.
- Nenhum outro personagem foi alterado.

## Limpeza do Power Geyser

- O impacto final do pilar não cria mais o `SparkHit` branco genérico em cima
  da chama. O próprio pilar é o efeito; o spark extra deixava pontinhos
  claros ao redor da vítima.
- O `AfterImage` do estado 3000/3010 foi removido do build: o port não modela
  `AfterImageTime`, e o rastro de ghost ficava como sujeira clara depois do
  super. O pilar, dano, hitbox e câmera continuam iguais.
- No fim do pilar, o slot cosmético vizinho e os dois caches de página FX são
  limpos. Isso evita que a página de spark compartilhada seja desenhada por
  um frame com as células do pilar — os quadrados dourados intermitentes.

## Ajuste específico da King

- O agarrão normal da King usava os binds de torso do arcade (`-56/-60 px`),
  mas o port desenha a vítima com a pose genérica ancorada nos pés. O
  resultado era o oponente pendurado acima da cabeça dela, como se as mãos
  agarrando os pés.
- Apenas o estado normal de throw da King (`800/810`) foi ajustado: os binds
  desceram 35 px. Os agarrões especiais/supers dela e todos os outros
  personagens permanecem intactos.
- O levantamento final do arremesso foi mantido (só ficou mais baixo).

## Seleção de personagens

- O fundo continua sendo o frame do screenpack do arcade, com os ícones
  pequenos preservados (sem portraits grandes).
- A legenda herdada "STAGE SELECT" foi substituída por **PLAYER SELECT** na
  mesma faixa, com a fonte do jogo e fundo reconstruído a partir do gradiente
  original.
- O título é assado no BG1, então não consome espaço do banco de luta.

## ORDER SELECT

- Faixa de título com fundo próprio.
- Painéis com moldura azul (P1) e vermelha (P2), cabeçalhos coloridos e trilho
  inferior.
- Novas paletas 8/9 (azul/vermelho) carregadas junto das paletas de retrato;
  os retratos 24x24 e as posições de texto continuam iguais.
- Nenhum tile novo de HUD foi necessário: o preenchimento usa o glifo `"`
  (não usado) reservado como bloco sólido.

## HUD

- O HUD continua vindo do `fight.def`/`fight.sff` do arcade (barras, retratos,
  nomes, contador de POWER e relógio). A auditoria visual confirmou que a
  correção de agarrões não mexeu no layout.
- A barra de POWER já fica amarela quando o MAX está ativo; o comportamento
  foi preservado.

## Itens 1–6 desta rodada

### 1. Cels de vítima por personagem

- Personagens streamados pelo MSU-1 agora usam uma pose de **hold autoral**
  (a ação apontada pelo `ChangeAnim2` do victim state) em vez do loop
  genérico 5000/5010.
- A pose autoral é combinada com uma pose genérica para manter o loop curto
  e limitada a um cel novo por personagem, sem estourar os bancos.
- Personagens ROM-residentes continuam no loop genérico por orçamento.

### 2. Impacto dos agarrões

- Todo lançamento para `S_VTHROW` dispara um **SparkHit** no peito da vítima
  e o SFX `SFX_THROW`.
- Os `PlaySnd`/`Explod` autorais de cada agarrão continuam rodando; o FX
  compartilhado garante que nenhum agarrão fique mudo.

### 3. ORDER SELECT 32×32

- Retratos do ORDER SELECT subiram de 24×24 para **32×32** (4×4 tiles).
- O P2 usa os mesmos tiles do P1 no ORDER SELECT; não há segundo blob de
  retratos na ROM.
- O painel, as molduras azul/vermelha e os nomes foram ajustados ao novo
  tamanho.

### 4. HUD: MAX e rounds

- A palavra **MAX** pisca em dourado ao lado de cada contador de POWER
  enquanto o MAX está ativo.
- Os pips de round existentes foram preservados; o novo texto usa a banda
  `HUD_POWCNT`, sem aumentar o orçamento do HUD.

### 5. Seleção: moldura e cursor

- Molduras douradas estáticas foram assadas no BG1 em volta das placas de
  nome.
- O cursor ganhou um **glow de 1 px** gerado na própria arte do ringue,
  sem novos tiles de BG e sem código extra no banco de luta.

### 6. Throw tech

- A saída de throw tech agora toca `SFX_GUARD` e gera um **SparkGuard** na
  vítima, deixando o escape legível.
- A janela de escape existente (`ESCWIN`) foi mantida.

## Validação

- `python3 -m unittest discover -s tools/tests`: **311 testes OK**.
- `tools/test_back_throw_headless.py`: frente/trás/espelhado em 5 lutadores +
  Chizuru, exigindo lançamento aéreo de verdade.
- `tools/test_clark_chains_headless.py`: Ultra Argentine, Running Three e
  Flashing Elbow, 6 cadeias PASS.
- `tools/test_team_order_headless.py`: 17 PASS (ORDER SELECT, 32×32 e dois
  humanos).
- `tools/test_msu_chr_visibility_headless.py`: PASS após os cels novos.
- `tools/test_mary_grab_headless.py`, `test_mature_vice_grabs_headless.py`,
  `test_counter_grab_headless.py`, `test_choi_throw_headless.py`,
  `test_ralf_mount_headless.py`, `test_chizuru_fixes_headless.py`: PASS.
- `make -f Makefile.pvsnes verify`: **OK**, checksum **`$25BC`**.
- Capturas em `build/v111_ui/` (`select.png`, `order_select.png`,
  `fight_hud.png`, `fight_hud_max.png`, `throw_normal.png`).

## Build

- `kof98-snes.sfc` — SHA-256
  `53bda8bb5941d0a0e211feb6277ad49007e3bc1e3b2a61e9aa6cd6824b59cb19`
- `kof98-snes.msu` — SHA-256
  `72a6885eedfeb4c35284cbe8630a8f15eeef3d1b86f17683f38161dfb9ff38b9`

Copie ROM e MSU juntos.

## Próximos passos rápidos (o que ainda vale a pena)

1. **Cels autorais de vítima para os personagens ROM-residentes** (hoje só
   os streamados usam a pose autoral; Terry/Omega seguem no loop genérico).
2. **Som de impacto específico por personagem** em vez do `SFX_THROW`
   compartilhado.
3. **Retratos do ORDER SELECT também no HUD** ou variação de 32×32 no
   versus, se houver VRAM sobrando.
4. **Animação de throw tech** (pose dedicada) além do flinch + spark.
5. **Moldura dourada animada** na seleção usando a paleta CGRAM, sem tiles
   novos.
