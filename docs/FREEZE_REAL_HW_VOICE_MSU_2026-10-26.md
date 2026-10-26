# Travamento raro Ralf × Clark no SD2SNES — diagnóstico e correção (26/10/2026)

## Sintoma

Em SNES real com SD2SNES MKII, muito raramente a luta Ralf × Clark trava:
os lutadores e o relógio param, a tela fica limpa (sem menu) e a música
continua. Esse quadro é um bloqueio da CPU, não um softlock de estado de
luta: `pausecnt`/`gamestate` continuariam contando e o menu apareceria.

## O que foi descartado

- ~1,5 milhão de frames de Ralf × Clark no Snes9x, em três modos
  (CPU × CPU, Ralf ocioso × Clark CPU e Ralf CPU × Clark ocioso), com
  detecção de parada do contador de frames e de pose congelada: nenhuma
  reprodução.
- 300 mil frames com entradas aleatórias nos dois lados, incluindo
  comandos HCF/QCB/QCF/DP, arremessos e golpes multi-hit: nenhuma
  reprodução.
- O MSU e a ROM são carregados corretamente no emulador; o travamento é
  dependente de timing de hardware/SD2SNES.

## Causas prováveis corrigidas

### 1. Leitura de voz MSU fora do alinhamento de 512 bytes

O carregador de CHR já alinha toda leitura do `.msu` a um setor de 512
bytes e traz prefixo + payload para `MsuStageBuf` antes de DMA para VRAM
(correção de 24/10). O fluxo de vozes, porém, ainda lia blocos de 512 bytes
em offsets arbitrários do arquivo. No SD2SNES o cache de dados é reabastecido
por setor; uma leitura assim pode começar no meio do setor e atravessar a
página de cache, deixando a CPU presa no loop de cópia do `MSU_DATA`.

Agora `MsuReadAlignedFar` (`src/snes/fight_bridge.asm`) lê qualquer amostra
de voz em blocos alinhados a 512 bytes, com prefixo descartado, usando
`MsuStageBuf`. `VQTF_chunk` (`src/engine/voice_queue.asm`) usa esse caminho e,
em caso de timeout do MSU, mantém o cursor e tenta de novo no frame seguinte.

A primeira versão dessa correção usava um segundo DMA MSU (canal 5) para
trazer a voz. No SD2SNES MKII os chars de MSU voltaram a aparecer com tiles
trocados: o DMA de voz e o DMA de CHR compartilham o mesmo caminho de cache.
A voz agora é copiada pela **CPU** (`MSU_DATA`), também a partir de setor
alinhado; o caminho de DMA do CHR ficou intocado. O teste de voz continua
comparando byte a byte com o `.msu`.

### 2. `spcLoadEffect` sem timeout durante uma voz ativa

`RoundVoice` e `FxDrainFar` desligam a NMI e chamam `spcLoadEffect`, cujos
handshakes de `APUIO1` não têm timeout na PVSnesLib 4.6. Se uma voz ainda
estiver sendo transmitida, a APU pode não responder e a CPU fica presa
(música continua). Agora:

- `FxDrainFar` só inicia a recarga pendente quando `digi_active` ($00015A)
  está zerado; caso contrário devolve e tenta no próximo frame.
- `RoundVoice` abandona o callout se a voz ainda estiver ativa, em vez de
  arriscar o handshake; a NMI e a pilha são restauradas normalmente.

## Vozes do Ralf

O gerador mapeia `PlaySnd` com amostra do `.snd` para o op7 (voz) apenas
nos estados que estão ligados a um sid. Depois da correção, o Ralf tem:

| Golpe | Sid/estado | Voz | Quando toca |
|---|---|---|---|
| Air Blitz | 54 / 455 | 4 | tempo 7 do estado |
| Arremesso básico | 75 / 301 | 0 | tempo 29 |
| Galactica Phantom fraco | 85 / 500 | 5 | elemento 51 |
| Galactica Phantom forte | 86 / 501 | 6 | tempo 123 |
| Pose de vitória | 90 / 181 | 1 | tempo 100 |

O Galactica fraco estava **sem voz** porque o `PlaySnd` original dispara no
elemento 52 de uma animação de 182 ticks. O gerador convertia vozes de
animações em loop para tempo de estado, mas o gatilho de ActTab só carrega
7 bits (0..127); a voz era descartada. `tools/build_fight.py` agora usa o
gatilho por elemento como fallback quando o tempo não cabe, então a voz do
Galactica fraco passou a tocar (confirmado no headless: voz índice 5,
3.375 bytes).

Vulcan Punch (400/401), Gatling (420/421), o grab (440/441) e os supers de
corrida não têm amostra de voz nos estados correspondentes do CNS original;
eles continuam silenciosos por falta de dado de origem, não por regressão
do port.

## Validação

- Build PVSnesLib + `make verify`: OK. O checksum final desta rodada,
  já incluindo as correções da esquiva do Clark e da California Romance
  do Mr. Big, é `$C102`.
- Novo teste `tools/test_msu_voice_alignment_headless.py`: transmite as 21
  vozes do Clark e compara byte a byte com o `.msu`, incluindo amostras
  ímpares e com vários blocos (até 3.375 bytes). PASS.
- `test_choi_throw_headless.py`, `test_ai_headless.py`, os testes de
  anti-aéreo/California Romance e o probe de apresentação: PASS.
- MSU atual: SHA-256
  `3e8945c3…868de386` (mudou depois que a California Romance do Mr. Big
  passou a usar uma amostra de voz).
- ROM: SHA-256 `d66ac5dc…c5fb77f7`, checksum `$C102`.

## Teste no console

Copie `kof98-snes.sfc` **e** `kof98-snes.msu` juntos para o SD (substitua
os dois). Se o travamento ainda aparecer, o próximo suspeito é o firmware
do SD2SNES; a documentação anterior recomenda 1.11.2 ou mais recente para
as correções de cache/dma do MSU.
