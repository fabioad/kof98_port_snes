# Hishou Ken do Andy pelo QCB+P (27/10/2026)

## O que o original faz

O comando do jogador (baixo, baixo+trás, trás + soco = QCB+P) aponta para
os states **1100/1110** da CNS. Esses states criam o helper **1105**, que é
o Hishou Ken de curta distância: uma explosão de energia na palma, com
HitDef próprio e sem `Projectile` controller.

- `1100` (fraco): helper no `animelem 5`; dano 13 na escala de 100 HP.
- `1110` (forte): helper no `animelem 6`, depois de Andy dar um passo à
  frente (`velset x = 12`); dano 14.
- O Clsn1 do helper 1105 ocupa **x = 32..127** à frente do eixo de Andy, e
  o efeito dura ~19 ticks. A versão `QCF+c` (state 1150/helper 1155) é o
  Hishou Ken de trás, um projétil viajante.

O port só tinha ligado a versão de trás (`sid 58 = 1150`). Os sids 52/53
(states 1100/1110) não tinham linha no ProjTab, então o QCB+P tocava a
animação de arremesso, mas **não criava projétil nem hitbox**.

## Como ficou

- sids 52/53 agora têm linha no ProjTab:
  - `vx = 0` (a explosão é estacionária, como no helper);
  - dano **26/28** (13/14 × damage_scale 2);
  - guarda `MA` (`$A0`) e release nos frames 4/5 da animação dos states
    1100/1110;
- o byte de guarda leva no nibble baixo o código **10** = deslocamento de
  **80 px** à frente (centro do Clsn1 original 32..127);
- o código 8–15 também marca um golpe curto: o hitbox horizontal passa de
  24 para **48 px** de raio e o projétil dura **12 ticks** em vez dos 90
  normais. Com isso a borda perto fica em 80−48 = 32 px e a longe em
  80+48 = 128 px, praticamente o Clsn1 32..127 do original;
- no forte, Andy já avançou quando o helper nasce; como o deslocamento é
  relativo à posição atual, o alcance acompanha o passo (o teste confirma
  28 de dano);
- o `QCF+c` de trás continua sendo o projétil viajante de 4 px/tick e 14
  de dano.

### Sobre o visual

O orbe compilado do Ko'ou Ken da Yuri é reutilizado para as duas versões.
O atlas do helper 1105 (explosão de palma) não cabe nas janelas de banco
PVS que sobraram no ROM; compilá-lo junto com o clipe principal estourou
a alocação e tirou a janela de 12 KiB da própria Yuri. O trajeto, o alcance,
o tempo e o dano seguem o helper 1105; só o desenho é o orbe compartilhado.
Na falha, o orbe aparece a 80 px e some após 12 ticks; no acerto, o spark
de impacto o substitui, como em qualquer projétil.

## Validação

- Novo `tools/test_andy_hishouken_headless.py`:
  - P1 fraco: state 52, **26** de dano;
  - P1 forte: state 53, **28** de dano (com o passo à frente);
  - P1 errando: o orbe nasce a ~80 px, fica parado e expira sem acertar;
  - P2 (virado para a esquerda): queda/alcance espelhados, **26** de dano;
  - `QCF+c` de trás: state 58, projétil viajante, **14** de dano.
- `test_projectile_calibration`: linhas 52/53 (`$AA,41` / `$AA,49`) e o
  perfil/config gerados.
- **180 testes unitários** e os demais testes headless: PASS.
- Build PVSnesLib + `make verify`: OK.

## Hashes

- ROM `kof98-snes.sfc`: checksum **`$D092`**, SHA-256
  `1231375f…e45a1a27`.
- MSU `kof98-snes.msu`: SHA-256 `3e8945c3…868de386` (inalterado).
