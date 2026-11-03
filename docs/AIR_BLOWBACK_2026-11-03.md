# Blowback aéreo para todos os personagens (03/11/2026)

## Pergunta: reutilizar o quadro do golpe forte aéreo ou importar as animações?

Reutilizar o **golpe forte aéreo** (sid 24) é bem mais rápido e seguro:

- não adiciona AIR/estado/CHR por personagem;
- não muda o layout do `.msu` (que já causou travamentos quando mudou);
- é uma regra de comando + um flag de HitDef, comum a todos;
- o custo de runtime é praticamente o mesmo (uma animação já importada).

Importar as animações reais de air CD exigiria, por personagem: localizar o
estado/AIR no pacote, importar os sprites, acrescentar AnimTab/CHR, ajustar
HitDef/hitboxes e testar; além do risco de deslocar o layout MSU. É um
trabalho bem maior e não tem ganho de tempo de execução.

## Implementação

- `AirBlowTry` (banco 50, janela baixa `$0EA0`) é chamado no `StJump`:
  - se `R` foi pressionado no ar, entra no **sid 24** (golpe forte aéreo) e
    liga o latch `F_TFLAGS` bit 4;
  - senão, volta para o fluxo normal (air throw / comandos / golpe aéreo).
- `AirBlowForce` (mesma janela) é chamado no caminho de acerto: se o latch
  estiver ligado, força `scr5` bit 0, levando a vítima ao knockdown
  (`HO_kdown`).
- `EnterState` agora limpa o bit 4, então o latch não vaza para o próximo
  estado.
- O blowback de chão (`CD`/`R` no solo) continua usando o estado específico
  de cada personagem; nada mudou nele.

## Validação headless

Para Ralf, Kyo, Iori e Terry, no ar:

- **R (air blowback):** P1 entra no state 24 e a vítima vai para
  `10` (S_DOWN) → `18` (deitada), com dano.
- **X (golpe forte aéreo normal):** P1 também entra no state 24, mas a
  vítima vai para `9` (hitstun) → `0`, sem knockdown.

Também passaram `test_super_fx_headless`, `test_ranbu_headless`,
`test_msu_chr_visibility_headless` e `test_msu_voice_alignment_headless`.

## Build

`build/ralf_airblow_20261103/`

- checksum **`$C13C`**
- layout MSU **`0xC276`**
- `.sfc` SHA-256 `5e97cba2…08bdc3b`
- `.msu` SHA-256 `471f5983…ce53dcb6`

O `.msu` é o mesmo da build anterior do Air Blitz; copie `.sfc` e `.msu`
juntos.
