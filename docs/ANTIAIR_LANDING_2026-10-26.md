# Recuperação de anti-aéreos ao pousar (26/10/2026)

## Sintoma

Golpes anti-aéreos que sobem e depois caem — Choi (Hien Zan 1500/1510),
Athena (Phoenix Arrow 1020), entre outros — ficavam **parados no último
frame da animação** depois de tocar o chão. O último frame tem um hold de
255 ticks, então a recuperação parecia travada por vários segundos.

## Causa

O `trans_rules` de `tools/build_fight.py` converte `ChangeState` de pouso em
uma linha `kind=1` do TransTab (`Vel Y > 0 && Pos Y >= 0`). Se o estado alvo
não tem sid (por exemplo 1505 do Choi), ele já era redirecionado para
`S_LAND` (sid 17).

Dois detalhes impediam a linha de existir:

1. O `ChangeState` do Choi tem um guarda de janela:
   ```cns
   trigger1 = AnimElem = 5,> 0
   trigger1 = Vel Y > 0 && Pos Y >= 0
   ```
   O extrator não reconhecia `AnimElem = N,> 0` e marcava o controlador
   inteiro como não suportado, descartando a regra de pouso. O mesmo valia
   para `AnimElemTime(N) > 0`.
2. Alguns estados têm **mais de um sid** (versões alternativa/MAX ou ar/terra).
   O mapa `state_to_sid` é first-wins, então só o primeiro sid recebia a
   linha de pouso. A Athena, por exemplo, usa o sid 49 no chão e o 66 no ar
   para o estado 1020; o 66 ficava sem pouso.

Sem a linha de pouso, `TransAir` não encontrava nada, o estado continuava e
o `AnimTick` parava no frame de 255 ticks.

## Correção

- `AnimElem = N,> 0`, `AnimElem = N,>= 1` e `AnimElemTime(N) > 0` passaram a
  ser tratados como **guardas de janela**, não como regras. O `ChangeState`
  continua válido se houver um gatilho real (pouso, `AnimTime=0`, comando,
  `MoveHit` ou distância).
- `trans_rules` agora emite a linha para **todos os sids** que mapeiam o
  estado de origem, não só o primeiro. Isso cobre versões aéreas/MAX e
  slices.
- Estados de pouso sem sid continuam indo para `S_LAND` (sid 17), cuja
  animação 47 tem 4 ticks.

## Validação

Teste headless `tools/test_antiair_landing_headless.py`:

| Golpe | Estados | Recuperação em S_LAND |
|---|---|---|
| Choi 1500 fraco | `48 -> 17 -> 0` | **4 ticks** |
| Choi 1510 forte | `49 -> 17 -> 0` | **4 ticks** |
| Athena 1020 (chão) | `49 -> 17 -> 0` | **2 ticks** |

Teste estático `tools/tests/test_antiair_landing_rows.py`: percorre todos os
`build/gen_fight/*_spr.inc` e falha se algum golpe com velocidade vertical
negativa e hold de 255 ticks não tiver uma linha `kind=1` de pouso.

Ken (estado 1111, 20 ticks) e Sakura (estado 56, 17 ticks) usam poses de
pouso próprias e continuam com a recuperação prevista; o que foi eliminado
foi o hold de 255 ticks.

## Build

- ROM: checksum **`$DA94`**,
  SHA-256 `a1928fdd…240f2f88`.
- MSU: SHA-256 `3e8945c3…868de386` (inalterado nesta rodada).
