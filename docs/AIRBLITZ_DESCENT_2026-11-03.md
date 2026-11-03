# Air Blitz do Ralf — descida e pouso (03/11/2026)

## Sintoma

A descida do Air Blitz (state 455 / sid 54) estava muito lenta e o pouso
não tinha a rodada/backflip para trás que existe no CNS original.

## Causa da descida lenta

O CNS original faz, no elemento 4 da animação 455:

```cns
type = velset
trigger1 = AnimElem=4
x = 10
y = 15
```

O gerador convertia isso em duas linhas de ActTab por elemento
(`3,5,10` para x e `3,15,60` para y). No runtime, porém, a linha de
elemento do y não era aplicada: o rastreamento headless mostrava `F_VY = 0`
durante toda a descida, e o Ralf caía apenas com a gravidade
(`GRAV = 0.44 px/tick`). Por isso a descida parecia travada.

## Correção

`AirBlitzDive` (banco 50, janela baixa livre em `$0FD0`) é chamado por
`StSpecial` logo depois de `PinVXUnlessVelSet`. Quando `F_STATE == 54` e
`F_FRAME >= 3` (o frame do mergulho), ele aplica:

- `F_VX = 10 px/tick`
- `F_VY = 15 px/tick`

A descida agora percorre ~15 px por tick. O rastreamento mostra `F_Y`
caindo de ~25 px para ~9,5 px em um único tick, contra ~0.44 px/tick antes.

## Pouso com rodada para trás

O CNS original encadeia:

- 455 (mergulho) → 456 (pouso/backflip, com `posadd x=32` e depois
  `velset x=-3, y=-6` para o impulso para trás);
- 456 → 457 (levantar do pulo);
- 457 → 0 (idle).

O port pulava direto do 54 para o state 17 (pouso genérico), então a
rodada não aparecia. Foram adicionados:

```python
"anims": {56: 456, 57: 457, ...}
"moves": {56: 456, 57: 457, ...}
"extra_trans": [(54, 56, 1, 0), (56, 57, 1, 0), (57, 0, 0, 0), ...]
```

O rastreamento headless confirma a sequência `54 → 56 → 57 → 0`, com o
impulso para trás do 456 (sobe até ~38 px e cai) e o levantar do 457.

## Validaçao

- `test_super_fx_headless.py`: PASS.
- `test_ranbu_headless.py`: PASS.
- `test_msu_chr_visibility_headless.py`: PASS.
- `test_msu_voice_alignment_headless.py`: PASS.
- Trace do Air Blitz: descida em 15 px/tick e cadeia 54→56→57→0.

Build de teste em `build/ralf_airblitz_fix_20261103/`:

- ROM checksum **`$A1BA`**
- layout MSU **`0xC276`** (mudou por causa das animações 456/457;
  copie `.sfc` e `.msu` juntos)
- `.sfc` SHA-256 `f6226727…ae4e6c13`
- `.msu` SHA-256 `471f5983…ce53dcb6`
