# Telemetria de apresentação + HUD parcial — 23/10/2026

## 1. O que foi implementado

### Telemetria no motor (`src/engine/fight.asm`)

Bloco em WRAM `$51B0..$51DF` (reservado em `fight_bridge.asm`), zerado no
início da luta e rezerável por software escrevendo `1` em `TEL_CTRL`.

| Campo | Conteúdo |
|---|---|
| `TEL_FRAMES` | frames apresentados |
| `TEL_DMA_P1/P2` | frames em que o lutador tinha upload pendente |
| `TEL_HUD_BYTES` | bytes totais de DMA de HUD (32 bits) |
| `TEL_HUD_FRAMES` | apresentações que chamaram `FlushHud` |
| `TEL_REQ_P1/P2` | `framecnt` do pedido de sprite atual |
| `TEL_AGE_SUM/MAX_P1/P2` | soma/máximo da idade do pedido em frames |
| `TEL_REQS_P1/P2` | pedidos de sprite aceitos |
| `TEL_DROP_P1/P2` | poses novas recusadas porque o upload anterior ainda corria |
| `TEL_CTRL` | escrita 1 = reset |
| `TEL_HP/POW/MAX` | caches usados pelo HUD para marcar bandas sujas |
| `TEL_SPFIX` | vezes em que S chegou fora da janela `$1C00-$1FFF` |
| `TEL_SPLAST` | último S inválido observado |

As constantes ficam em `assets/runtime_abi.json` e são geradas para o ASM por
`tools/runtime_abi.py`, então o probe Python lê exatamente os mesmos endereços.

O ponto de medição é `FightPresent`, antes de qualquer DMA. O pedido é
marcado em `ASF_q_new`; quando uma pose nova chega com upload em andamento,
`ASF_q_drop` incrementa o contador de descarte e mantém a pose anterior.

### HUD parcial (`FlushHud`)

`huddirty` passou de booleano para máscara:

| Bit | Banda | Linhas | Bytes |
|---|---|---|---|
| `$01` | nomes/pips | 1 | 64 |
| `$02` | vida + timer (topo) | 2 | 64 |
| `$04` | timer (baixo) | 2–3 | 128 |
| `$08` | linha 4 | 4 | 64 |
| `$10` | combo | 11 | 64 |
| `$20` | contadores de power | 22–23 | 128 |
| `$40` | barras de power | 25 | 64 |
| `$80` | HUD completo | todas | 2048 |

`FlushHud` envia **no máximo uma banda por apresentação**. A ordem da tabela
`HudBandTab` prioriza vida, depois power, contadores, timer e combo. A banda
só é limpa da máscara depois de escolhida; as demais ficam para os próximos
vblanks. Full flush continua existindo para pausa, banners, K.O., intro e
troca de membro.

`DrawBars` agora compara HP, power e `F_MAX` com caches e marca somente as
bandas que mudaram. `DrawTimer` marca `HUD_TIMER`; `ComboDraw` marca
`HUD_COMBO`; os eventos de setup/overlay marcam `HUD_FULL`.

## 2. Resultado medido

Probe: `python3 tools/probe_presentation.py` (VERSUS, P1 humano, P2 parado;
idle → walk → jump, 420 frames).

```
frames=428
P1 upload pendente = 67.3% dos frames
P2 upload pendente = 37.6%
idade média P1/P2 = 1.38 / 1.39 frames
idade máxima P1/P2 = 5 / 5 frames
pedidos P1/P2 = 82 / 48
poses descartadas P1/P2 = 4 / 0
HUD: 9 frames com DMA (1 full + 8 bandas), 3008 bytes no total
     ~7,0 bytes/frame em média
```

No caminho antigo, cada evento de HUD enviava 576 bytes (3 faixas fixas). Com
8 eventos de banda, seriam ~4,6 KB só de HUD ao vivo; agora são ~640 bytes
(64–128 por banda), além do full flush de setup.

### Achado importante: `DMACHUNK` estava em 256

O valor não commitado em `assets/runtime_abi.json` era `256`, enquanto o
`build_fight.py` e a documentação usavam `1280`. Com 256 B/vblank, uma pose de
2–3 KB levava 8–12 vblanks. A/B no mesmo cenário:

| `DMACHUNK` | idade média P1 | idade máx | poses descartadas |
|---|---|---|---|
| 256 | 8,48 frames | 21 | 63 |
| 1280 | 1,38 frames | 5 | 4 |

O valor foi alinhado para **1280**, que é o orçamento usado pelo build e o
limite documentado do caminho MSU/ROM. O HUD parcial reduz o DMA concorrente,
então o valor voltou a ser seguro.

## 3. Como rodar

```sh
python3 tools/probe_presentation.py              # idle/walk/jump
python3 tools/probe_presentation.py --attacks    # inclui 3 golpes B
```

`--attacks` ainda reproduz um **travamento pré-existente no hit-stop** (P1
state 8, P2 state 9, `framecnt` para). Ele ocorre também com HUD e telemetria
desligados, então não foi introduzido por este trabalho; é o próximo candidato
para a investigação de fluidez.

## 4. Correção do travamento de round

O probe `--attacks` reproduzia o travamento no hit-stop. Os savestates Mesen
mostraram S fora da janela (`$D87E`), NMI em `$00:8004` e a WRAM baixa
preenchida por frames `80 A5 09`. A causa era o cleanup de argumentos de
áudio com `tsc/adc/tcs`; foi trocado por `pla` e o SP passou a ser resetado
incondicionalmente no topo do `MainLoop`. Detalhes em
`docs/FREEZE_ROUND_2026-10-23.md`.

## 5. Observações de implementação

Testes: 139 unitários OK, incluindo `test_presentation_telemetry` e o guard
de `ASF_q_new` em `test_sprite_upload_queue`.

- O banco `Fight` está cheio (32768 bytes). A tabela compacta de bandas
  (7 bytes por entrada, offsets pré-calculados) e o laço com `inx` foram
  necessários para caber sem mover código para o banco 126.
- O laço de bandas usa `inx` sete vezes em vez de `txa/adc/tax`; a variante
  aritmética se mostrou instável quando o acumulador estava em 8/16 bits
  alternando no caminho de apresentação.
- `FlushHud` só roda se não houver upload de lutador pendente, evitando
  iniciar um segundo DMA no mesmo vblank.
- O teste estrutural `tools/tests/test_sprite_upload_queue.py` foi ajustado
  para aceitar o caminho `ASF_q_drop` (telemetria) e exigir que ele chegue a
  `ASF_q_wait`.
