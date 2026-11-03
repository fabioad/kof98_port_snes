# Antiáreo do Benimaru (Super Inazuma) completo — 03/11/2026

## Sintoma

O antiáreo de chute do Benimaru (DP + botão, "Super Inazuma") parecia
incompleto: o personagem fazia só a pose inicial, não avançava e não
acertava. O RDP (Shinkuu Katategoma) continuava normal.

## Causa

No CNS do Benimaru o golpe é dividido em três estados:

- `1400`/`1410` — introdução de 3 quadros (pose + invencibilidade);
- `1401`/`1411` — o chute voador, com `VelSet (-0.75, -6)`, `PosAdd` e a
  HitDef que realmente acerta;
- `1402`/`1412` — aterrissagem, com `PosSet y=0`.

O importador só mapeou os estados de entrada (`1400`/`1410`) para os sids
54/55. O `ChangeState` para `1401`/`1411` foi descartado porque esses
estados não tinham sid de runtime. Resultado: o golpe tocava apenas a
introdução de 3 quadros, sem caixa de ataque e sem o salto.

## Correção

Foram adicionados quatro sids de follow-up ao Benimaru:

| sid | estado fonte | anim | função |
|---|---|---|---|
| 107 | 1401 | 1401 | chute fraco (ar) |
| 108 | 1411 | 1411 | chute forte (ar) |
| 109 | 1402 | 1402 | aterrissagem fraca |
| 110 | 1412 | 1412 | aterrissagem forte |

A cadeia é feita por `extra_trans`:

`54 → 107 → 109 → 0` (fraco)
`55 → 108 → 110 → 0` (forte)

Os sids 107/108 usam o handler `StAirSpec` (Physics + TransAir), então o
`VelSet`/`PosAdd` importados movem o chute no ar e a aterrissagem cai no
chão. Os sids 109/110 usam `StSpecial`; o `StateRet` aplica Physics/
TransAir até voltar para `S_STAND`.

## Verificação

Novo `tools/test_benimaru_antiair_headless.py`:

- DP fraco: estados `54 → 107 → 109`, 34 de dano, oponente derrubado;
- DP forte: estados `55 → 108 → 110`, 40 de dano, oponente derrubado;
- o golpe acerta um oponente no ar (antiáreo);
- não gera projétil e recupera para `S_STAND`.

Os outros comandos do Benimaru continuam iguais: Raikouken (QCF+P),
Handou Sandan (QCB+K), Iai Geri (QCF+K) e Shinkuu Katategoma (RDP+K).

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$E6E8`**
- layout MSU **`0xC276`**
- `.sfc` SHA-256 `fefca3f6…1907e6`
- `.msu` SHA-256 `471f5983…ce53dcb6` (inalterado)
