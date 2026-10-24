# Super moves e MAX

Este documento consolida os critérios usados pelo motor e as correções de
outubro/2026 para custo de meter, slots MAX e leitura da command list.

## 1. O que é um super

| Faixa de `sid` | Categoria |
| --- | --- |
| 48–66 | especiais |
| 67–84 | sistema, agarre, vítima |
| **85–89** | **supers** |
| 96 | ativação do MAX |
| 97 | carga manual de meter |

`IsSpecialState` e `CmdTryCancel` tratam 85–89 como supers. Um super só
entra se o comando estiver no buffer, a postura/distância bater e o
`PowTab[sid]` permitir o gasto.

O buffer de comandos aceita até **30 frames** (`CmdScanCap`). QCFx2 e
HCBx2 usam janelas de 25–30 frames; o limite antigo de 18 frames cortava a
primeira metade do movimento e deixava um DP/QCF especial comer o input.

## 2. Custo de meter

- O `PowTab[sid]` é um delta assinado aplicado no `EnterState`.
- Valores negativos são custos: `-1000` = 1 estoque, `-2000` = 2,
  `-3000` = 3.
- O gerador lê três fontes:
  1. `poweradd` no cabeçalho do `Statedef`;
  2. `type = PowerAdd` + `value = -N`;
  3. `poweradd = -N` em controllers como `SuperPause`.
- Todo super que tem comando custa pelo menos **1000**. Estados de
  continuação/finisher (Iori 3020/3210, Athena 3050, ...) não trazem custo
  próprio, mas o port pode entrar neles direto, então o gerador aplica o
  mínimo de um estoque.
- Casos com expressão (`-1000 - ((PrevStateNo = 1111) * 1000)`) continuam
  cobertos pelo mínimo de 1000; para valores exatos use `pow_override`.

## 3. MAX/SDM por personagem

O slot MAX **não é fixo**. O descritor carrega um byte `CH_MAXMASK`
(offset 91), com bit0 = sid 85 ... bit4 = sid 89. O matcher lê esse byte
em vez de presumir 88/89.

Convenção usual:

- 85/86 = primeiro super (fraco/forte)
- 87 = MAX/SDM do primeiro super
- 88/89 = segundo super (fraco/forte)

Exceções atuais (detectadas pelo nome do estado, pelo formato de custo SDM
do CNS ou por `MAX_SIDS_OVERRIDE`):

| Personagem | Slots MAX |
| --- | --- |
| Iori | 89 |
| Kyo / Kyo Nests / Kyo Ash | 87 |
| Shingo | 87 |
| Rugal | 87 |
| Omega Rugal | 88, 89 |
| Mature | 88 |
| Vice | 89 |
| Heavy D! | 86 |
| Lucky | 86 |
| Ryu | 88 |
| Chris | 85, 86 |
| Shermie | 85 |
| Geese / Joe / Ken / Krauser / Yamazaki | 87 |
| Vega | 87, 88 (quando ligados) |

Os demais 85/86/88/89 são supers normais.

## 4. MAX na prática

- **Y + B + X** no neutro, com ≥ 1000 de meter → estado 96.
- O MAX custa 1000 e arma `F_MAX = 240` ticks (~4 s a 60 fps).
- Durante o MAX: +25% de dano.
- Super MAX dentro do MAX paga o custo-base do `PowTab` (normalmente
  1000–3000).
- Super MAX fora do MAX é o **Quick SDM**: exige 3000 e gasta os três
  estoques.

### Correção do timer

`F_HOT` (offset 58) e `F_MAX` (59) são bytes vizinhos no descritor do
lutador. O `CmdTry` gravava `F_HOT` com um store de 16 bits; o byte alto
caía em `F_MAX` e zerava o MAX a cada direção/botão novo. Por isso o MAX
“expirava” assim que o jogador mexia no direcional. O store agora é de 8
bits, e o timer decrementa uma vez por frame (medido: 239 → 211 em 28
frames; 211 → 0 em 211 frames).

## 5. Ganho de meter

Acertos e defesas rendem 25% a mais:

| Evento | Antes | Agora |
| --- | --- | --- |
| acerto (atacante) | 60 | 75 |
| acerto (vítima) | 30 | 38 |
| defesa (atacante) | 25 | 31 |
| defesa (vítima) | 15 | 19 |
| projétil defendido (vítima) | 15 | 19 |
| projétil defendido (dono) | 25 | 31 |

A carga manual (`R+Y+B+X`, sid 97) continua em ~5/tick.

## 6. Como conferir

```sh
python3 tools/build_fight.py
python3 -m unittest tools.tests.test_command_list
python3 tools/test_super_meter_headless.py
python3 tools/test_cancel_headless.py
python3 tools/test_sf_cancel_headless.py
make pvsnes PVSNESLIB_HOME=/caminho/do/pvsneslib
```

`build/gen_fight/max_masks.inc` mostra a máscara final por personagem. A
command list usa a mesma máscara para escolher as tags `SUP` e `MAX`.
