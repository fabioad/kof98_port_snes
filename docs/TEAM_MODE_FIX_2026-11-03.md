# Team Play / Team Versus — ROUND X e cores do stage (03/11/2026)

## ROUND X travado em 1

O intermission desenha `ROUND n` com `roundno`, mas o caminho de time
(`TeamRoundEnd`) nunca incrementava esse contador: ele sai pelo
`TeamSwap` em vez do melhor-de-3. Assim a segunda e a terceira luta
continuavam mostrando `ROUND 1`.

Correção em `TRE_continue`: antes de `nextflag = 1`, o contador passa a
ser `max(T_I1, T_I2) + 1`, onde `T_I1`/`T_I2` são os índices do membro
atual de cada lado. O primeiro combate (0/0) dá 1; o segundo (um lado em
1) dá 2; o terceiro (um lado em 2) dá 3. O mesmo valor alimenta a voz de
`ROUND n`.

## Cores do stage emaranhadas após a segunda luta

O `TeamSwap` reaproveita o stage e o CGRAM, mas pula o `PpuInit` do
`StartFight`. Se a luta anterior terminou com um super/MAX, o color math
genérico (`CGWSEL`/`CGADSUB`, estado em `SUPERFX`) podia ficar armado e
tingir o stage seguinte.

`StartFight` agora chama `ResetSuperFx` (banco 50, janela baixa) antes de
qualquer caminho, inclusive o `TeamSwap`:

```asm
SUPERFX = 0
SUPERFX_MODE = 0
CGWSEL = 0
CGADSUB = 0
```

Assim o próximo combate sempre começa com o color math desligado,
independentemente de como a luta anterior terminou.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$DC74`**
- layout MSU **`0xC276`**
- `.sfc` SHA-256 `81ed4c06…2e178282`
- `.msu` SHA-256 `471f5983…ce53dcb6`
