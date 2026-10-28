# Bola do Lucky: Death Bound diagonal (27/10/2026)

## Correção

A primeira versão no port fazia a bola aparecer **acima da tela e cair na
vertical**, modelando os helpers de "bola do céu" do pacote MUGEN. Isso
estava errado para o golpe de bola do Lucky: o **Death Bound** original sai
da mão dele e avança **em diagonal de cima para baixo** na direção do
oponente. A versão A vai mais alto, a C mais baixa.

Agora o projétil (sid 87, state 2100, comando BASKETBALL do port) usa:

- spawn na altura da mão/peito: **120 px acima do chão**;
- **4 px/tick** para frente;
- gravidade **11/16 px/tick²**, curvando a bola para baixo;
- dano **22**;
- se erra, toca o chão e quica para trás; TTL 90.

A captura headless mostra a bola saindo na altura do braço erguido do Lucky
e descendo em diagonal, em vez do orbe que aparecia no topo da tela.

## E o golpe de várias bolas caindo de cima?

Não existe uma chuva de bolas no moveset normal do Lucky.

- O **Death Shoot** (`D,D+P` no original) chama **uma** bola do alto/layup;
  os helpers 2101/2114/2115 da CNS são efeitos cosméticos, não projéteis
  independentes.
- O **Death Bound MAX/Desperation** pode gerar **3 rajadas diagonais**, mas
  isso não é uma chuva de bolas caindo.
- O port tem uma bola por shot; não há "várias bolas de cima".

## Comando

A tabela sintética do port liga o **DP+P** ao state 2099 (o "Shoot"/Death
Shoot do pacote MUGEN) e usa esse comando como BASKETBALL. O **QCF+P** do
port ainda executa o Fastbreak/DASH do pacote, enquanto no arcade o Death
Bound é `QCF+P`. O trajeto diagonal corrigido está no BASKETBALL/DP+P; se
for necessário bater o comando arcade exatamente, o próximo passo é remapear
`QCF+P` para este projétil.

## Validação

- `tools/test_lucky_basketball_headless.py`:
  - P1 acerta a vítima a ~60 px: **22 de dano**;
  - a bola sai na altura da mão (~120 px), anda para frente e desce;
  - no erro, toca o chão e quica para trás;
  - P2 espelhado: **22 de dano**.
- Teste unitário do perfil balístico (`height 120`, `gravity 11`,
  `drift 0`) e da linha gerada do ProjTab (`vx $0400`).
- **181 testes unitários** e demais testes headless: PASS.
- Build + `make verify`: OK.

## Hashes

- ROM `kof98-snes.sfc`: checksum **`$D092`**, SHA-256
  `1231375f…e45a1a27`.
- MSU `kof98-snes.msu`: SHA-256 `3e8945c3…868de386` (inalterado).
