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

## Char invisíveis no round 3

O `TeamSwap` reaproveitava o stage/CGRAM, mas não restaurava o contexto de
PPU do combate (OBSEL, bases de BG, paleta do stage). Depois do banner/
intermission da segunda luta, os atores do round 3 podiam ser desenhados
fora da página de OBJ correta e ficar invisíveis no console.

`TeamSwap` agora chama `TeamPpuSetup` (banco 50, `$0F9A`): `PpuInit`,
`LoadStaticGfx`, `CampStage` e `StagePick`. Isso restaura OBSEL/BG/stage
sem tocar em HP, meter ou posição do sobrevivente; o NMI fica desligado
durante a troca e é religado no fim. `test_team_swap_headless` continua
passando os 6 casos de posição/facing.

## Cores do stage depois da terceira luta (Team Versus)

Na luta final o combate pode terminar com um super/MAX, e a tela de
vencedor (`ShowTitle`/`DrawBanner`) **não roda `StartFight`**, então o
color math genérico podia continuar armado e o stage aparecia com parte
das cores faltando.

`ShowTitle` agora chama `ResetSuperFx` antes de montar o ROUND/banner:
zera `SUPERFX`, `SUPERFX_MODE`, `CGWSEL` e `CGADSUB` (e descarta a voz de
vencedor pendente). O reset que já existia no `StartFight` continua
cobrindo a próxima luta.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$EA8A`**
- layout MSU **`0xC276`**
- `.sfc` SHA-256 `09b27bd4…a5cfe406`
- `.msu` SHA-256 `471f5983…ce53dcb6`
