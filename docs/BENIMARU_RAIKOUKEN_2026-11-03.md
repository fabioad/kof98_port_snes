# Raikouken forte do Benimaru — trajetória (03/11/2026)

## Como era

No CNS original, o Raikouken é um helper com o HitDef e um Explod 1002
com a bola elétrica:

- fraco (state 1000): helper em `pos = 78,-76`;
- forte (state 1010): helper em `pos = 61,-116` (mais alto e mais à
  frente, acompanhando a mão que sobe).

O helper em si é estático (state 1005, sem VelSet/Projectile); o port
aproxima o golpe com um projétil sintético. O `ProjTab` só carregava a
velocidade horizontal (`vx`), então **fraco e forte saíam na mesma altura
de torso e em linha reta** — o forte não acompanhava a mão levantada.

## Correção

`ProjVyFix` (banco 50, `$0E36`) é chamado pelo `ProjSpawn` no lugar do
`stz SPK_VY`. Para o **Raikouken forte de chão** (sid 49):

- spawn em `GROUND_Y - 96` (na altura da mão levantada, em vez do torso);
- `VY = -1 px/tick` (sobe levemente enquanto avança).

O fraco (sid 48) continua em `GROUND_Y - 40` com `VY = 0`. O ar forte
(sid 51) não foi alterado.

## Verificação headless

- Forte (X): a bola nasce em `y ≈ 93` e sobe ~1 px/tick (`93 → 29` em
  70 ticks).
- Fraco (Y): nasce em `y = 150` e mantém `VY = 0` (linha reta).

Build: `build/teamfix_benimaru_20261103/`, checksum **`$DC74`**, layout
**`0xC276`**. Copie `.sfc` e `.msu` juntos.
