# Guarda cancelável com golpe normal (03/11/2026)

## Comportamento

Segurar para trás é uma **pose de guarda**, não um estado comprometido. Se o
golpe do oponente não estiver acertando, um golpe normal (A/B/X/Y) agora
cancela a pose e sai normalmente. Se o golpe acertar, o defensor entra em
`S_GHIT` (blockstun) e o comportamento continua o de antes: não sai normal,
só os guard cancels existentes (Y+B = rolamento, X+A = blowback, gastando um
stock).

É o comportamento padrão dos jogos de luta: você pode sair da guarda e
atacar enquanto o oponente erra/termina o golpe; durante o blockstun você
fica preso no flinch.

## Implementação

Em `StGuard` (pose de guarda em pé) e `StCGuard` (agachado), depois do
`GCancelTry` e antes de `HoldsBack`, foi adicionada a checagem de borda dos
botões de ataque:

- `StGuard` → `StTryAttack` (tabela `CH_BUTTONS`, golpes em pé);
- `StCGuard` → `StTryCrouch` (tabela `CH_CBTN`, golpes agachados).

Como a checagem está **antes** do `HoldsBack`, ela só roda enquanto o
personagem ainda está na pose de defesa. O `S_GHIT` continua chamando apenas
o `GCancelTry`, então o blockstun não é cancelável por normal.

A ordem do `FightTick` ajuda: o primeiro `HitCheck` roda antes do
`TickFighter`. Se o golpe do oponente já está acertando, a vítima entra em
`S_GHIT` antes de o handler de guarda processar o botão — o bloqueio ganha.
Se o golpe ainda não acertou, a pose é cancelada e o normal sai.

## Verificação

Novo `tools/test_guard_normal_cancel_headless.py`:

- guarda em pé + A/B/X/Y → `S_SKICK`/`S_KICK`/`S_SPUNCH`/`S_PUNCH`;
- guarda agachada + A → golpe agachado (`S_CSKICK`/`S_CPUNCH`);
- `S_GHIT` + A → continua em `S_GHIT`, sem cancelar.

`test_guard_cancel_headless` (Y+B / X+A, um stock cada, luta continua) e
`test_projectile_guard_headless` continuam passando.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$5225`**
- layout MSU **`0xC276`**
- `.sfc` SHA-256 `392b39db…a49a63`
- `.msu` SHA-256 `471f5983…ce53dcb6` (inalterado)
