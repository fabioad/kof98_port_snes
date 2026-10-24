# Travamento no início do round — diagnóstico e correção (23/10/2026)

## Evidência dos savestates Mesen

Slots usados: `~/.config/Mesen2/SaveStates/kof98-snes_1.mss` (início da luta)
e `kof98-snes_2.mss` (travamento).

| Campo | Slot 1 (início) | Slot 2 (travado) |
|---|---|---|
| `cpu.pc` | `$C0:2097` (`WaitForVBlank`) | `$00:8004` (entrada da NMI) |
| `cpu.sp` | `$1FFA` | `$D87E` |
| `cpu.d` | `$1000` | `$0200` |
| `cpu.dbr` | `$7E` | `$00` |
| `gamestate` | `$01` | `$80` (inválido) |
| `huddirty` | `$04` | `$80` |
| `p1state/p2state` | `00/00` | `09/06` |
| WRAM `$1000-$1FFF` | estado normal | preenchida com `80 A5 09` repetido |

O slot 2 mostra a pilha fora da janela válida (`SP=$D87E`), a NMI sem
conseguir empilhar/retornar e a WRAM baixa coberta por frames de pilha
`80 A5 09`. O direct page do motor fica em `$1000`, então a primeira coisa
corrompida foi o próprio `gamestate`; depois disso, o reset condicional de
SP (que só rodava em `gs=1/2/4`) deixava de rodar e a NMI usava SP inválido.

## Causa

As limpezas de argumentos das chamadas de áudio usavam:

```asm
tsc
clc
adc #N
tcs
```

Isso depende de S estar exatamente onde o chamador espera. Quando um
`jsl`/retorno/rotina C deixava a pilha deslocada, o `tcs` propagava o
deslocamento. Com o tempo a pilha andava até a região do direct page; o
`pld` seguinte carregava D com lixo (`$09A5`), e a NMI empilhava
`phb/phd` (`80 A5 09`) repetidamente até lotar `$1000-$1FFF`.

## Correção

1. **Limpeza de argumentos sem `tsc/tcs`**: todos os pontos ativos foram
   trocados por `pla` (2 bytes por argumento), que é seguro mesmo se uma NMI
   entrar no meio.
   - `fight.asm`: `SfxPlay`, `SfxMusPlay`, `StageMusic`, `RoundVoice`;
   - `voice_queue.asm`: fila de voz e `spcPlaySoundV`;
   - `options.asm`: música do menu.
2. **Reset de SP incondicional** no topo do `MainLoop`, antes do
   `WaitForVBlank`: `S` volta a `$1FFF` mesmo se `gamestate` já estiver
   corrompido.
3. **Telemetria de pilha**: `TEL_SPFIX` / `TEL_SPLAST` registram quantas
   vezes o SP chegou fora da janela `$1C00-$1FFF` e o último valor inválido.

## Validação

- `python3 tools/probe_presentation.py --frames 900 --attacks --assert-clean`
  → **934 frames**, `end_gamestate=1`, P1/P2 em `state 0`, `sp_fixes=0`.
- Stress de 1.234 frames com três ataques: sem travamento, `sp_fixes=0`.
- `test_start_transition.py`: PASS single/versus.
- `test_stage8_music_headless.py`: PASS (música continua trocando).
- 139 testes unitários OK.
- `test_roster.py`: 24/26 (as duas falhas continuam sendo o harness dos Kyo
  ocultos).
- `verify pvsnes: OK`, checksum **`$4EEC`**.

O `test_fight_remote.py` ainda para no passo “mirrored B” porque espera
`state 7`; o layout de botões atual dispara `state 8` (strong kick). É um
descompasso do harness, não mais um travamento: o contador de frames avança
e o estado volta a `0`.

## Como inspecionar os slots

`tools/mss_read.py` lê `.mss` sem abrir o Mesen:

```sh
python3 tools/mss_read.py ~/.config/Mesen2/SaveStates/kof98-snes_2.mss
```
