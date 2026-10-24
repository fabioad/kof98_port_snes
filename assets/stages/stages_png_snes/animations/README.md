# Animações econômicas dos stages — definição para pvsneslib

Especificação baseada nos `.def` e `.sff` reais de `assets/stages`.
Há **8 animações**, cada uma com **2 ou 3 desenhos distintos**. O objetivo é
aplicar os movimentos futuramente aos cenários redesenhados de 512×224.
Os PNGs atuais, os stages MUGEN e a engine não foram alterados.

## Arquivos de uso

- `stage_animations.json`: definição principal; poses SFF, linhas do DEF,
  eixos, recortes, tempos, fases, trajetórias, regiões propostas e orçamento.
- `stage_anim_data.h`: as mesmas sequências em tabelas C.
- `stage_anim_clock.h` e `.c`: relógio independente de renderização,
  compatível com C89, sem ponto flutuante, alocação dinâmica ou chamadas de DMA.
- `selected/<id>/poses.png` e `preview.gif`: referências das poses escolhidas.
  São pixels do **MUGEN original**, alinhados pelos eixos; não são os gráficos
  finais de SNES nem uma demonstração sobre os fundos redesenhados.
- `source_inventory.json` e `references/`: material de inspeção original,
  incluindo poses descartadas. **Não incluir esses arquivos na ROM.**
- `inspect_sources.py` e `build_definitions.py`: reprodução da inspeção e
  das definições, usando o leitor SFF existente em `tools/sff.py`.

## Poses escolhidas

Todas as durações abaixo são ticks lógicos de 1/60 s. Um ciclo pode repetir
uma pose sem ocupar mais ROM: A–B–C–B tem quatro etapas e apenas três desenhos.
Os pares indicam `grupo,número` no SFF do stage correspondente.

1. **Japão, público do fundo:** ação 30; `30,0` e `30,4`;
   A por 36 ticks, B por 36. Ciclo de 1,2 s. Recortar as pessoas, não os carros.
2. **Japão, estudantes:** ação 45; `45,0` e `45,3`;
   30/30 ticks, ciclo de 1 s, início defasado em 15 ticks.
   Manter pés e posição da bolsa coerentes com os dois desenhos.
3. **Bazar, comerciante direito:** ação 20; `20,0` e `20,6`;
   42/18 ticks, ciclo de 1 s: repouso mais longo e gesto breve do braço.
4. **Bazar, espectador esquerdo:** ação 25; `25,0` e `25,5`;
   40/40 ticks, ciclo de 1,33 s, fase inicial de 20 ticks.
5. **Bazar, público central:** ação 30; `30,0` e `30,3`;
   36/36 ticks, ciclo de 1,2 s, fase inicial de 36 ticks.
   O recorte exclui o camelo; animar somente os gestos das pessoas.
6. **Coreia, homem do parapeito:** ação 35; `35,13` e `35,14`;
   24/24 ticks, ciclo de 0,8 s. Usar o gesto de observação.
   A entrada e saída do personagem no MUGEN foram omitidas.
7. **China, remador:** ação 15; `15,0`, `15,10`, `15,17`;
   A–B–C por 24/30/24 ticks, ciclo de 1,3 s. As poses representam alcance,
   puxada e recuperação. Os 20 desenhos originais ficam reduzidos a três.
   Não aplicar o balanço senoidal do piso do MUGEN: manter chão e pés estáveis.
8. **Coreia, gaivota:** ação 50; `50,0`, `50,1`, `50,2`;
   A–B–C–B, 9 ticks por etapa, ciclo de 0,6 s. Reusar esses três desenhos nas
   quatro passagens; usar H-flip para inverter o sentido. As ações originais
   40/45 têm três poses e 50/55 têm quatro; não é necessário guardar quatro atlases.

Esses tempos são uma proposta para SNES, não uma reprodução exata da velocidade
de todas as ações MUGEN. Os tempos originais permanecem no JSON para comparação.

## Estratégia de renderização

**Pessoas e remador: patches de BG1.** Manter chão, pernas imóveis, carros,
bancas e arquitetura na imagem estática. Redesenhar somente os tiles afetados
pelo movimento, já compostos com o fundo que fica atrás deles. Cada célula
animada deve ter seu próprio slot dinâmico: não deduplicar seu tile com uma
região estática, pois a troca animaria também o outro local.

Não colar os sprites originais diretamente sobre os PNGs novos. As pessoas já
estão desenhadas no fundo e as proporções mudaram. É necessário reconstruir a
área encoberta e adaptar as poses ao estilo e à paleta do cenário. As regiões
`target_region_xywh` são propostas de composição, em pixels do mundo 512×224;
não são coordenadas extraídas automaticamente dos novos desenhos. A região é
um limite de trabalho; o patch pode conter somente alguns tiles dessa região.

No Japão, as camadas originais 25, 30 e 45 se sobrepõem. Compor as partes
estáticas na ordem MUGEN e garantir um único dono para cada célula animada.
As duas regiões propostas no JSON são adjacentes, sem sobreposição. Se o
redesenho exigir sobreposição, unificar essas células em um único patch de
duas poses em vez de deixar dois atualizadores disputarem o mesmo tile.

**Gaivotas: OBJ 16×16.** Uma instância visível por vez; atlas e paleta
compartilhados. O perfil atual da engine usa OBJ 8×8/16×16, portanto 16×16 é o
tamanho grande. Não alterar OBSEL para acomodar o ambiente sem revisar os
lutadores. Um sprite consome uma entrada OAM e duas colunas de tiles de 8 pixels
na linha; a reserva final deve considerar também os lutadores e efeitos.

## Orçamento de gráficos

Os números são **tetos de produção para o redesenho futuro**, não tamanhos
medidos de arquivos `.chr` prontos. Cada tile SNES 4bpp ocupa 32 bytes.
Paletas BG existentes são compartilhadas, sem paleta adicional para pessoas.

- **Japão:** até 8 tiles alterados por animação, duas animações.
  1.024 bytes de poses na ROM e 32 tiles dinâmicos em VRAM, com dois buffers.
  Limitar a parte estática a 480 tiles: 480 + 32 = 512.
- **Bazar:** 4 + 4 + 8 tiles alterados. 1.024 bytes de poses na ROM;
  32 tiles dinâmicos em VRAM; parte estática até 480 tiles.
- **China:** remador redesenhado dentro de 32×48, até 24 tiles por pose.
  2.304 bytes para três poses na ROM, 48 tiles/1.536 bytes em dois buffers
  de VRAM. Parte estática até 464 tiles. Incluir o remo dentro desses limites.
- **Coreia:** homem com até 4 tiles alterados: 256 bytes de poses na ROM e
  8 tiles/256 bytes para dois buffers BG. Parte estática até 504 tiles.
  Gaivota: 12 tiles úteis/384 bytes de poses na ROM e 32 bytes de paleta OBJ.
  Reservar **704 bytes de VRAM OBJ**, incluindo lacunas de endereçamento.
  Total do ambiente animado: 640 bytes de desenhos na ROM e 960 bytes de
  reserva VRAM (BG + OBJ), mais a paleta de 32 bytes em CGRAM.

Os quatro cenários somam até **4.992 bytes de desenhos de animação na ROM**,
mais 32 bytes da paleta da gaivota, tabelas de células, sequências, código e
alinhamento do linker. Os buffers de VRAM são por fase carregada, não a soma
das quatro fases. Os PNGs finais atuais já usam 512 tiles: recompô-los com
essas reservas antes de ativar animações, sem acrescentar tiles além do teto.

### Organização da gaivota em VRAM

Os tiles inferiores de um OBJ 16×16 estão a **+16 índices**, não +2.
Para uma base OBJ reservada `N`, usar poses nas bases `N`, `N+2`, `N+4`;
cada uma usa offsets `{0,1,16,17}`. A faixa `N..N+21` contém 22 slots,
12 úteis e 10 livres. Reservá-la inteira evita sobrepor os lutadores.
Escolher N alinhado ao começo de uma linha do atlas e sem cruzar o banco OBJ.

Guardar somente os 12 tiles úteis na ROM: seis tiles da linha superior e
seis da inferior. Carregar os dois blocos de 192 bytes em endereços VRAM
separados por 256 words. As poses ficam residentes durante a fase;
animar trocando o índice OAM, sem DMA de gráficos a cada batida de asa.

## Troca de patches sem quadro parcialmente atualizado

1. Reservar dois conjuntos de slots por patch. O tilemap aponta para o ativo.
2. Preparar a pose desejada no buffer inativo. Limite proposto compartilhado
   por todas as animações: **256 bytes de gráficos por VBlank**.
3. Quando a cópia terminar, trocar as entradas do tilemap desse patch em um
   único VBlank; até 24 entradas/48 bytes por commit. Fazer no máximo um
   commit por VBlank. Células esparsas exigem tratar os endereços separadamente.
4. Se faltar tempo após lutadores/HUD, adiar o ambiente mantendo a pose atual.
   Não mostrar o buffer incompleto. Manter separados `desired_pose`,
   `uploading_pose` e `displayed_pose`; não redirecionar uma cópia pela metade.

O teto incremental é até 256 bytes de gráficos + 48 bytes de mapa no VBlank
de commit, além das tarefas já existentes. Isso é uma política conservadora,
não uma medição de folga no jogo real. O remador leva até três VBlanks para
preparar 768 bytes; programar a cópia antes do instante de apresentação.
Se houver atraso, a duração exibida poderá aumentar, sem afetar a luta.

O mapa 512×224 usa dois planos de 32×32. Para uma célula `(tx,ty)`, com
`tx=0..63`, o índice word é `(tx/32)*1024 + ty*32 + tx%32`.
Endereço de tile em VRAM: `chr_base_words + tile_index*16`.
Não confundir bytes de transferência com endereços VRAM em words.

## Voo e câmera

As quatro trajetórias propostas estão no JSON. Cada uma dura 352 ticks;
inícios em 0, 360, 720 e 1.080; repetição em 1.440 ticks (24 s).
Começar em x=-16 ou x=512 e mover ±1,5 px/tick, com ±0,25 px/tick em y.
Isso permite no máximo uma instância ativa, mantendo o céu pouco carregado.

Usar posição e velocidade **signed 16-bit Q12.4**: multiplicar a coordenada
inicial por 16 e somar `velocity_q4` a cada tick lógico. Sem seno ou float.
Posições desse percurso cabem no intervalo. Em PAL atualizar também o
movimento pelo mesmo relógio lógico de 60 Hz, não apenas as poses.
Subtrair `camera_x` apenas ao desenhar: `screen_x = world_x - camera_x`.
Ocultar quando o retângulo sair da tela; não converter x negativo para u8.
O parallax proposto é 1,0 para acompanhar o panorama; o MUGEN usa 1,1.

O MUGEN desenha essas gaivotas na camada 1, à frente dos jogadores. Para
interferir menos na luta, recomenda-se colocá-las atrás dos lutadores no
futuro projeto. A prioridade BG/OBJ e a ordem OAM precisam ser configuradas
em conjunto; um número de prioridade isolado não resolve sobreposição OBJ.

## Integração futura em pvsneslib

Incluir `stage_anim_data.h`, compilar `stage_anim_clock.c` e manter um
`StageAnimState` por clip ativo. Inicializar ao entrar na fase; chamar
`stage_anim_video_tick()` uma vez por frame com 50 ou 60 Hz. O retorno indica
mudança da pose desejada. O upload inicial da pose é obrigatório mesmo sem
esse retorno; o relógio não gerencia DMA, mapa, OAM nem arquivos de arte.

Usar `dmaCopyVram()` somente na janela apropriada, com endereço em words e
tamanho em bytes. Para a gaivota, usar `oamSet()`/`oamSetGfxOffset()` após
carregar o atlas. O argumento `id` é o índice OAM multiplicado por 4.
Reservar a entrada, paleta e faixa VRAM junto ao alocador dos lutadores;
nenhum endereço ou índice livre foi presumido nesta definição.

Referências oficiais consultadas:
[sprites e OAM](https://alekmaul.github.io/pvsneslib/sprite_8h.html) e
[DMA](https://alekmaul.github.io/pvsneslib/dma_8h.html).
Os protótipos também foram conferidos no SDK local em `/tmp/pvsneslib-sdk`.

## Validação e limites

As poses selecionadas existem nos SFF e aparecem nas ações indicadas.
Os eixos variáveis do remador e da gaivota foram respeitados nas prévias.
Os testes do relógio cobrem limites de quadros, volta do ciclo, pausa e a
mesma duração em 50/60 Hz. Compilação de teste: C89, warnings como erros.

Não foram produzidos `.chr`, paletas finais ou poses redesenhadas nesta
etapa. Não houve integração, compilação de ROM ou teste no emulador/SNES.
As posições propostas e os tetos de tiles dependem da adaptação artística.
Se excedidos, reduzir a região animada ou simplificar as poses; não usar
automaticamente mais memória que a reserva.

Para reproduzir:

```sh
python3 -B animations/inspect_sources.py
python3 -B animations/build_definitions.py
cc -std=c89 -pedantic -Wall -Wextra -Werror animations/stage_anim_clock.c animations/test_clock.c -o /tmp/kof98-stage-animation-clock-test
/tmp/kof98-stage-animation-clock-test
```
