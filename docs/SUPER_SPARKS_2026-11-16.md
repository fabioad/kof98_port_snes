# Sparks de super e MAX (16/11/2026)

O arcade troca o impacto conforme o golpe. Em `Kyo-N.cns` e nos demais
personagens da familia KOF98 o `HitDef` usa:

```
sparkno = s6001+ifelse(var(40),3,0)
```

`var(40)` e o MAX ativo. Os supers em `Kyo-S.cns` usam a familia
`s6002+ifelse(var(40),3,0)`. O resultado no SFF:

| Origem | Anim | Tamanho | Uso |
| --- | --- | --- | --- |
| `s6001` | 6001 | 25x32 | acerto normal (SparkHit) |
| `s6004` | 6004 | 22x28 | qualquer acerto durante o MAX (SparkMax) |
| `s6002` | 6002 | 31x36 | super normal (SparkSuper) |
| `s6005` | 6005 | 30x37 | super durante o MAX (o port reusa SparkSuper) |

## Como o motor escolhe

1. `EnterState` ja chama `SuperFxCheck` para o flash/escuro dos supers.
   O mesmo teste (`PowTab` delta <= -1000) marca `SUPERCHAIN` por lutador.
   A marca sobrevive aos estados de continuacao do super e cai quando o
   lutador entra num estado que nao e de ataque. A ativacao do MAX (96) e
   a carga manual (97) nao marcam a corrente.
2. `SparkPick` (banco 126) le `aofs`:
   - corrente de super -> `SparkSuper` (2);
   - senao, `F_MAX != 0` -> `SparkMax` (3);
   - senao -> `SparkHit` (0).
   Um super durante o MAX usa o `SparkSuper`, que e o desenho maior.
3. Projeteis guardam a origem nos bits 1-2 de `SPK_GRD` no disparo. Assim
   um Orochinagi que acerta depois do atacante sair do estado 85-89 ainda
   usa o spark de super. Projeteis refletidos limpam esses bits. (Os bits
   1-2 de `SPK_ATTR` ja sao a contagem de quique dos projeteis balisticos.)
4. `SpawnProjImpact` le os bits antes de liberar o slot do projetil e chama
   `SparkSpawnAt` com o indice escolhido.

## Atlas

`SparkAnimTab` ficou com a ordem fixa `Hit, Guard, Super, Max` (o motor
indexa por posicao; `SPARK_ANIM_*` em `fight.asm` documenta os indices).
Cada pagina OBJ tem 16 celulas de 16x16. Para caber os dois impactos novos
sem uma terceira pagina, o `SparkHit` passou de quatro para tres quadros
(2, 3 e 5 da anim 6001); o rabo esparso (quadro 7) foi removido. O atlas
fica em 15/16 celulas na pagina de impacto.

## Como conferir

```sh
python3 tools/build_fight.py
python3 tools/test_super_sparks_headless.py
```

O teste dispara um soco normal, repete com `F_MAX` ligado e executa o
QCFx2+X do Kyo; em cada caso compara o ponteiro do slot de spark com os
simbolos `SparkHit`, `SparkMax` e `SparkSuper`. Por fim, com Ryu, prende o
slot 0 e confere que o Shinkuu Hadouken no slot 1 tambem termina em
`SparkSuper`.

### Correcao: quadrados dourados apos o super

A primeira versao de `SpawnProjImpact` empilhava o indice do spark e depois o
slot, mas desempilhava na ordem inversa. Um projetil no slot 1 passava `20`
como indice de `SparkAnimTab` (ponteiro lixo, desenhado como blocos 16x16 da
pagina de sparks) e devolvia o indice como offset de slot. No slot 0 o
impacto virava sempre `SparkHit`. Agora o indice fica em A e so o slot vai
para a pilha.

O brilho/aura azul do MAX (ativação e supers durante o MAX) usa a
variante azul do `SuperFx` (seção 7 de `docs/SUPER_MOVES.md`), não os
sparks.
