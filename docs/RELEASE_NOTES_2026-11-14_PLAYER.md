# KOF '98 SNES — v1.2.0 (14/11/2026)

Esta é a maior atualização do port até agora: **os lutadores ficaram maiores**,
**a luta ficou mais rápida** e **dezenas de golpes que entravam na animação mas
não causavam dano agora acertam de verdade**.

---

## Destaques

- **Lutadores maiores.** O jogo agora usa a arte em **escala 1.0** como padrão
  (antes era 0.88). O elenco ocupa mais tela e os golpes ficam com o tamanho
  que você lembra do arcade, com poucos ajustes por personagem onde a arte
  original não caberia no SNES.
- **Luta mais rápida.** O combate saiu da casa dos ~46–54 fps para
  **~53–59 fps**, com os confrontos mais leves batendo **~60 fps**. Menos
  travadas, inputs mais responsivos, animação mais fluida.
- **Golpes que não machucavam agora machucam.** Uma auditoria interna testou
  os **940 golpes especiais e supers** do elenco: **907 acertam e causam dano**
  (eram 885), **33 são por design** (não são ataque) e **nenhum caso ficou em
  aberto**. Zero regressões.
- **Comandos não se engolem mais.** Vários supers deixaram de sair porque um
  golpe mais curto "roubava" o comando. Agora gancho, especial e super saem na
  hora certa.
- **HUD e menus no estilo arcade.** Placar com degradês, nomes em itálico,
  contador de POW dentro da caixa, banner grande de **ROUND X** no estilo do
  K.O. e os fundos animados do arcade nas telas de seleção.

---

## O que mudou para quem joga

### Lutadores e elenco

- Escala **1.0** por padrão em quase todo o elenco. Ajustes pontuais:
  Chang 0.80, Billy 0.85, Rugal 0.94, Omega Rugal 0.94, Sakura 0.95 e
  Chun-Li 0.99.
- Cache de sprites: quando o lutador só anda ou muda de lugar, a pose é
  reaproveitada e a luta não perde velocidade.
- **Mr. Big** ganhou a intro com as namoradas, como no original.
- Correções de tamanho/caixa que deixavam golpes passando por cima ou
  por baixo do oponente.

### Golpes, agarrões e supers

- **Agarrões que davam 0–1 de dano** agora aplicam o dano real:
  Billy (3000/3020 → 21/6), Ralf (440 → 34), Heidern (1400/1410 → 32),
  Daimon (1400 → 5), Duck King (2000/2300 → 42/52) e Yuki (1600 → 21).
- **Vítima não fica mais presa no chão** nos agarrões altos de Andy, Billy,
  Brian, Daimon, Krauser e Omega Rugal.
- **Golpes que entravam na animação e não causavam dano**, corrigidos:
  - **Eiji** 1200/1210 — o golpe de 1201/1202 agora conecta (22).
  - **Mai** 1043 — o mergulho de 1045 e o pouso de 1047 agora dão dano (18).
  - **Yuki** 1000 — o tiro do helper virou projétil de verdade (14);
    1300 Kaban Barrier virou caixa de corpo com dano (22).
  - **Ryo** 2000/2010 — Kohou aéreo sai na altura do tronco (14).
  - **Kasumi** 1200/1300/3100/3150 — os contra-ataques agarram e aplicam
    40/40/80/128 em vez de só aparar.
  - **Mary** 1520 — o contra baixo passou a aplicar o dano do slam (55).
- **Supers MAX que gastavam estoque e não faziam o serviço:**
  - **Iori** — MAX Ya Otome agora entra na versão completa e causa o dano da
    sequência (73).
  - **Rugal** — MAX Gigantic Pressure agora entra no Gigantic Pressure forte,
    que é o arremesso completo (43).
- **Prioridade de comandos** corrigida, para o golpe curto não roubar o
  comando do super: Ryuuko/Robert, Kasumi, Shermie e os supers aéreos do
  **Choi**.
- Ajustes de personagem: **Saisyu** (Orochinagi sai da meditação ao soltar o
  botão), **Shermie** (agarrão aéreo e custo de estoque correto), **Chin**
  (deslocamento do Flash Punch 2), **Ralf** (Ralf Kick forte no agarrão),
  **Omega Rugal** (dashes e rolamentos), **Yuki** (dashes FF/BB e o Kusanagi
  desenhando o Kyo), **Clark** (poses da vítima e sincronia do slam),
  **Mai**, **Yuri** e **Andy** (altura/encaixe do arremesso).
- **Iori** ganhou o final explosivo do Ya Otome e ajustes de anti-aéreo;
  **Leona** teve o tempo do golpe de agarrão refeito.
- **Projéteis refletidos:** o reflexo do P1 estava usando o lutador errado no
  cálculo — corrigido.
- **CPU** não dá mais os "toquinhos" para trás e o timer de cancelamento
  funciona como deve.

### Velocidade e fluidez

- Parte do motor de desenho e da fila de vozes passou a rodar em **FastROM**,
  que era o gargalo de 41% das instruções da luta.
- A voz agora é copiada em blocos alinhados e roda na folga do quadro
  anterior, sem roubar tempo da luta.
- Resultado medido (2400 quadros, Snes9x headless):

  | confronto | antes | agora |
  |---|---|---|
  | Daimon vs King | 48,5 fps | **54,4 fps** |
  | Ryu vs Ken | 57,8 fps | **59,6 fps** |
  | demais pares | 46–58 fps | **53–59 fps** |

- Nenhum quadro perdido de OAM ou de stream de CHR nas medições.

### Visual

- **HUD arcade:** timer grande com degradê, nomes em itálico (P1 branco→azul,
  P2 laranja→vermelho), RUSH n HITS, COUNTER!!, GO!/K.O. em dourado e os
  números de estoque do POW azuis dentro da caixa creme.
- **Banner de ROUND X** grande, no mesmo estilo do K.O./GO!.
- **Correção da paleta corrompida** que trocava as cores da luta e do título
  de vez em quando.
- **Cenários reexportados** com três paletas por fase e tiles espelhados —
  acabou o efeito de blocos chapados em vários stages.
- **China Stage:** o deque do barco foi alinhado ao chão dos lutadores.
- **Telas de seleção, OPTIONS e MSU-1 CHECK** com o fundo animado do arcade
  (o "K.O.F." subindo) e artes de ORDER SELECT.
- **Título** com a arte do arcade "THE SNESFEST" em fundo vermelho, textos com
  contorno preto e PRESS piscando no lugar certo.
- **SOUND TEST:** nomes das faixas não vazam mais para a entrada seguinte.

### Áudio

- As **17 músicas** (10 de cenário + 7 de menu) foram reconvertidas do MIDI
  com o arranjo completo de 8 vozes do Final Fight Guy: mais corpo, bateria
  melhor e notas preservadas.
- O tema do **USA Yard** foi centralizado e ganhou uma faixa de comparação no
  SOUND TEST.

### Correções de modo de jogo

- **SURVIVOR com P2** segue as mesmas regras do P1 (melhor de 3 na abertura,
  HP do lado humano certo, bônus de especial e ending próprio).
- **Team Play:** HUD e lutadores voltam corretamente na troca de personagem.
- **Seleção de time:** o cursor avança para o próximo lutador.
- **Attract demo:** o idle do CPU vs CPU foi corrigido (não começa cedo nem
  trava).
- **Tela de título:** não aparece mais a faixa preta do HUD no meio do "98".
- **Loading da luta:** sem lixo de BG2/OBJ na entrada do cenário.
- **MSU-1 CHECK:** a pergunta YES/NO voltou a aparecer com o fundo animado
  atrás.
- **Sem `.msu`:** cursores aparecem no Terry e um aviso vermelho pisca
  avisando que faltam os dados.

---

## Como jogar

```text
kof98-snes.sfc   # ROM de 8 MiB
kof98-snes.msu   # dados MSU-1 (~58 MB)
```

Mantenha os dois arquivos juntos para jogar com o elenco completo e os
gráficos em escala 1.0. Sem o `.msu`, a ROM roda com o elenco reduzido e arte
menor.

Perfis alternativos, se precisar de mais desempenho no seu setup:

- **MID** (`kof98-snes-mid.sfc/.msu`) — arte HI 0.88, o antigo padrão.
- **OLD** (`kof98-snes-old.sfc/.msu`) — arte 0.81, o mais leve.

## Compatibilidade

- Testado em Snes9x (headless e janela) e em hardware com SD2SNES/FXPak.
- FastROM, MSU-1 e ExHiROM.
- 311 testes automatizados passando, mais as regressões de cada correção.
