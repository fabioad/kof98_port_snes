# Travamento durante a luta — slots Mesen 1–4

Os originais foram preservados. Cópias e logs ficam em
`build/freeze_slots_20261023/`.

## Causas reproduzidas

Os slots 2 e 4 estavam executando `CancelGate` em `$F2:016C` e
`$F2:0135`, respectivamente. O replay do slot 2 na ROM anterior reproduziu
BRK. O trace mostra `LDX` em `$F2:0189` consumindo os bytes `56 20`
como `$2056`; `$20` era o opcode do `JSR CharPtr`. A rotina executava
com índices de 16 bits, mas o assembler emitia `LDX #boxp` em 8 bits.
`CancelGate` agora estabelece `REP #$30` e `.INDEX 16` explicitamente.

Depois dessa correção, os quatro replays alcançaram um segundo defeito:
BRK com endereço de retorno `$F2:860F`, dentro de `FlushHudLive`.
Essa rotina já usa índices de 16 bits, mas `CPX #(5*7).b` forçava um
argumento de um byte. O opcode do próximo desvio era consumido como
parte do argumento. A comparação agora usa `.w`.

Com ambos corrigidos, os slots 2 e 3 avançaram 1.800 frames. Os slots
1 e 4 então expuseram `ComboDraw`: o caminho de dois ou mais hits chama
`WriteStr`, que retorna com A=16, e seguia para `CD_done`, montado para
A=8. O argumento de `ORA #HUD_COMBO` consumia o opcode seguinte; o
trace termina executando dados de `MsuPalette` e BRK em `$8F:002A`.
`CD_done` agora restabelece A=8 explicitamente. A regressão headless de
combos passa a exercitar um segundo contato durante a tolerância do
contador e exigir que a luta continue avançando após desenhar `2 HITS`.

O teste geral de apresentação não detectava esse segundo problema;
os replays Mesen verificam a entrada no vetor BRK/COP/IRQ além do avanço
do contador de frames. O teste de cancel conectado falhava na ROM
anterior e passou após a correção de `CancelGate`.

## Build

`Makefile.pvsnes` agora inclui `cancel_gate.asm` nas dependências do
objeto do motor, para uma alteração nesse arquivo invalidar o build.

A geração completa encontrou cinco perfis de calibração desatualizados
(Athena, Chizuru, Mary, Lucky e Brian). Os arquivos atuais foram
reanalisados com `tools/calibrate.py --analyze`; os fingerprints de
entrada/configuração foram atualizados, preservando as listas de
correções já escolhidas pelo projeto. Nenhuma nova correção de combate
proposta pelo calibrador foi aplicada.

## Replay

`tools/test_mesen_cancel_freeze.lua` usa os caminhos absolutos
`KOF_STATE`, `KOF_SYMBOLS` e `KOF_LOG`. `KOF_RAW=1` permite reproduzir
a ROM anterior no PC original. Por padrão o replay reinicia em
`MainLoop`, com pilha e registradores de contexto restaurados, pois os
endereços de código podem mudar na recompilação. Isso é uma retomada
controlada dos dados salvos, não um carregamento intacto do estado antigo.
`KOF_RECOVERED` opcionalmente grava uma cópia após um replay aprovado.

Usar uma cópia da ROM sem `.sym` ao lado evita uma falha do próprio
Mesen na importação automática dos símbolos (`MemoryMappings::GetAbsoluteAddress`).
O script lê os símbolos explicitamente.

## Validação final

- Build completo sem personagens ignorados; `verify_pvsnes_rom.py`: OK,
  checksum `$5F20`.
- Quatro replays Mesen aprovados, 1.800 frames cada: slots 1/2/3/4
  avançaram o contador em 1.786/1.778/1.667/1.715 frames e passaram por
  `CancelGate` 278/689/234/302 vezes, sem BRK ou paralisação.
- Cópias `slot1_recuperado.mss` a `slot4_recuperado.mss` gravadas em
  `MainLoop`, com SP=`$1FFF`. O slot 3 já chegou à seleção após o round;
  os demais terminaram no estado de luta. Os originais foram comparados
  byte a byte com os backups e permanecem intactos.
- `test_cancel_headless.py`, `test_combo_reset_headless.py` (incluindo
  `2 HITS`), `test_round_timer_headless.py`: PASS.
- Stress de apresentação: 1.833 frames, `gs=1`, lutadores em idle e
  `sp_fixes=0`.
- A ROM e o MSU da raiz foram comparados byte a byte com os arquivos
  efetivamente testados; hashes em `validated_sha256.json` junto aos logs.
