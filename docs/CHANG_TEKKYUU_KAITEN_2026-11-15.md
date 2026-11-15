# Chang: Tekkyuu Day-Kaiten (bola girando), 15/11/2026

## Problema

No giro da bola de ferro (QCF+X = estado 1000, QCF+Y = 1010):

- a bola não aparecia;
- o golpe quase nunca acertava.

## Causa

O ataque real da fonte é o Helper "Bola" (estado 1005), que o motor nativo
não executa. A animação do corpo (AIR 1000/1010) não tem Clsn1. Por isso
`tools/remaining_specials.py` colocava uma única caixa
`(-12,-100,70,0)` no penúltimo quadro, que é a pose de recuperação em pé
(`10,0`), durando no máximo 8 ticks. O golpe só acertava nessa janela.

## Correção

- `tools/remaining_specials.py`
  - `ball_spin_frames()` recorta o loop de giro (sprites 1000,0-3) em
    elementos de 3 ticks. A duração total do giro é a mesma de antes
    (quadros limitados a 8 ticks).
  - Cada elemento recebe duas caixas Clsn1, em unidades da fonte (escaladas
    por `char_scale` mais adiante no build):
    - uma caixa de ±36 em volta da posição da bola naquela fase da órbita
      (`BALL_ORBIT`, 6 pontos a cada 3 ticks, tirados da tabela
      `BindToParent` do helper, período de cerca de 18 ticks);
    - uma zona fixa no arco frontal, `(0,-125,105,-47)`, que cobre
      oponente em pé e agachado.
  - O `active` do HitDef passa a ser o primeiro elemento do giro. O acerto
    fica ativo durante todo o giro. Continua sendo um acerto só (dano 18 no
    1000 e 22 no 1010, com knockdown).
- `tools/build_fight.py`
  - Clipe novo `ChangBall` em `EXPLODS` (Chang.sff 1005,0 reduzido a 2/5,
    16x16, uma célula). `spark_sprite()` agora aceita escala `(num, den)`.
  - Depois do `repair_remaining_specials`, uma linha de ExpTab por fase da
    órbita e uma linha ActTab op14 por elemento do giro. Cada Explod dura
    3 ticks e posiciona a bola na órbita.

## Limites conhecidos

- A bola tem 16x16 px, menor que o tamanho original (cerca de 31 px com
  Chang a 0.80). O atlas de explods (`misc page`) estava em 15/16 células
  com a bola. Um bloco 2x2 estourou o pool
  (`spark: cell pool exceeds 16 slots`).
- A bola é desenhada sempre na frente do Chang. A metade traseira da órbita
  não passa por trás do corpo.
- Só há 2 slots de efeito. A bola pode ocupar o slot de uma faísca de hit.
- O golpe continua com um acerto só. O helper original acertava
  repetidamente, inclusive como dano de chip no bloqueio.
- A bola é um Explod parado no mundo por 3 ticks, então não acompanha o
  Chang se ele andar durante o giro.

## Validação

**Não validado em jogo.** O usuário pediu para não compilar.

- Uma compilação completa (`make -f Makefile.pvsnes`) passou pelo gerador do
  Chang e pelo atlas (`misc page 15/16`). Parou depois com
  `ValueError: missing close-normal data: mary`, em outro personagem. Não
  investiguei se esse erro já existia antes desta mudança.
- Ainda falta: gerar a ROM, rodar o golpe 1000/1010 no Snes9x headless
  (por exemplo com `tools/test_remaining_specials_headless.py --chars chang`)
  e olhar uma captura para ver a posição e o tamanho da bola.

## Arquivos para commitar

- `tools/remaining_specials.py`
- `tools/build_fight.py`
- `docs/CHANG_TEKKYUU_KAITEN_2026-11-15.md`
