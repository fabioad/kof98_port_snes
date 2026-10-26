# Esquiva do Clark — direção e correção (26/10/2026)

## Comandos

| Comando | Sid | Estado MUGEN | Direção |
|---|---|---|---|
| `ESQ_F` (frente + L) | 95 | 700 | rola para a frente |
| `ESQ_B` (trás + L) | 94 | 710 | rola para trás |
| `ESQ_L` (L sozinho) | 69 | 720 | esquiva neutra, sem deslocamento |

## Defeito encontrado

Os estados 700/710 do Clark declaram a velocidade assim:

```cns
x = ifelse((PrevStateNo = 100 || var(16) = 1),7.5,5)   ; frente
x = ifelse(var(16) = 1,-7.5,-5)                       ; trás
```

O extrator de `build_fight.py` só aceitava `VelSet` com número no início.
Como a expressão começava com `ifelse`, as duas linhas eram descartadas.
O ActTab gerado tinha apenas as linhas de parada:

```asm
clarkAct95: .db 6,5,0,0   ; parar
            .db 7,5,0,0
```

Resultado: a animação da esquiva rodava, mas o Clark ficava **parado**
(tanto `ESQ_F` quanto `ESQ_B`). O Ralf não sofria disso porque seus estados
250/251 usam `4.75*ifelse(...)` e `-4.75`, que começam com número.

## Correção

`tools/build_fight.py` agora reconhece o padrão de esquiva do sistema:
quando a expressão é um `ifelse` com dois ramos numéricos e a condição cita
`PrevStateNo`/`var(16)`, usa o ramo **else** (esquiva normal). As linhas
passaram a ser:

```asm
clarkAct94: .db 2,5,251,0  ; -5 px/frame (trás)
            .db 3,5,251,0
clarkAct95: .db 2,5,5,0    ; +5 px/frame (frente)
            .db 3,5,5,0
```

A regra é restrita a esse padrão; expressões de salto (`sysvar`/`const`) e
de hit (`gethitvar`) continuam intocadas. O mesmo conserto vale para Andy,
Benimaru e Daimon, que usam o mesmo CNS de esquiva.

## Validação headless

Com o Clark no P1, a partir de x=120:

- `ESQ_F`: estado 95, deslocamento **+60,5 px** em 40 frames;
- `ESQ_B`: estado 94, deslocamento **-68,1 px** em 40 frames;
- `ESQ_L`: estado 69, deslocamento **0**;
- salto neutro: continua subindo na vertical (dx=0).

Novo teste `tools/tests/test_dodge_velocity_rows.py` verifica as linhas de
velocidade de Clark, Andy, Benimaru, Daimon e Ralf.

## IA

Para o Clark controlado pela CPU (`AI_evade`): a curta distância ele escolhe
**frente em 5/8** dos casos, **neutro em 2/8** e **trás em 1/8**; a partir de
80 px de distância escolhe sempre o rolamento para a frente. Ou seja, a IA
prefere atravessar o ataque, não recuar.

## Build

- ROM `kof98-snes.sfc`: checksum **`$C102`**,
  SHA-256 `d66ac5dc…c5fb77f7`.
- MSU atual (mudou com a voz da California Romance):
  SHA-256 `3e8945c3…868de386`.
