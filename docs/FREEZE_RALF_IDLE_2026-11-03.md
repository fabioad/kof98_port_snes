# Travamento do Ralf no idle — leitura MSU cruzando página de 8 KiB (03/11/2026)

## Sintoma

No SNES real com SD2SNES, o Ralf fica preso no quadro de guarda do idle
(o mesmo do print enviado), sempre no mesmo ponto. O resto da luta pode
continuar rodando — inclusive a música — mas o sprite não volta a animar.
Como o quadro exibido é o último que foi commitado antes da falha, o
sintoma parece um golpe específico; na prática o Ralf estava voltando ao
idle depois de uma queda.

## Diagnóstico

O upload de CHR do MSU-1 (`SprDmaP`/`SD_msu`) alinha o seek em setores de
512 bytes, mas o payload de 1.280 bytes ainda podia atravessar o fim de uma
página de cache de 8 KiB do SD2SNES. A leitura encenada (`prefixo +
payload`) terminava depois da página; o barramento/DMA do MSU ficava
esperando a troca de página e a CPU travava, enquanto o áudio (que roda no
SPC/APU) seguia.

O caso reproduzido é o sprite 6 do `ralfAnim0` (idle), enfileirado logo
depois da pose de guarda:

```text
anim 0: 1(8t) -> 5(7t) -> 2(8t) -> 1(7t) -> 6(7t) -> 3(8t) ...
```

O primeiro chunk do sprite 6 tem o payload em `$2FBF80`; o seek alinhado
é `$2FBE00`, então prefixo 384 + payload 1.280 = 1.664 bytes terminam em
`$2FC480` — 1.152 bytes além do fim da página de 8 KiB (`$2FC000`). O
último sprite exibido antes da falha é o 1 (pose de guarda do print). Os
sprites 3 e 9 do mesmo idle também cruzavam a página, e 55 dos 299
metasprites do Ralf tinham pelo menos um chunk assim. Por isso a falha era
determinística por quadro e sensível a mudanças no layout do `.msu`.

## Correção

`MsuChrPageClamp` (banco 127, cauda livre depois do `StageData`; no build
standalone, depois do `KyoData`) encurta o payload daquele vblank para
terminar exatamente no fim da página de 8 KiB. O cursor do upload
(`F_DMAPOS`) avança pelo mesmo `scr3`, então o vblank seguinte continua
na página seguinte, sem perder nenhum tile.

- `src/engine/fight.asm`: `SD_msu` chama `jsl MsuChrPageClamp` logo após
  calcular o seek alinhado e o prefixo.
- `src/snes/fight_bridge.asm`: nova seção `MsuChrPageClamp`, com a conta
  `0x2000 - (seek & $1FFF) - prefixo`.
- O clamp vale para todo CHR streamado por MSU, não só o Ralf.

Efeito colateral: um sprite que cruzava a página passa a precisar de um
vblank extra. O relógio da animação não muda; no máximo a telemetria
`TEL_DROP` acusa uma pose coalescida a mais nesses casos.

## Validação

- `python3 -m unittest tools.tests.test_msu_chr_page_clamp`: 4 PASS
  (o chunk do idle do Ralf cruzava a página; com o clamp todos os 299
  metasprites ficam dentro de uma página e cobrem exatamente o `dmalen`).
- `tools/test_super_fx_headless.py`: PASS.
- `tools/test_ranbu_headless.py`: Ryo/Robert/Sakura PASS.
- Build PVSnesLib: checksum **`$B2F7`**, layout MSU **`0x01EE`**,
  `make pvsnes-verify` OK.
- ROM de teste em `build/ralf_idle_fix_20261103/` (copiar `.sfc` **e**
  `.msu` juntos).
  - `kof98-snes.sfc`: SHA-256 `00305214…f361bf`
  - `kof98-snes.msu`: SHA-256 `0f997227…d2295b`

## Se ainda travar

O próximo suspeito é o caminho de voz (`MsuReadAlignedFar`), que já lê em
blocos de 512 bytes alinhados e, portanto, não cruza a página de 8 KiB.
Se o sintoma mudar de quadro, vale instrumentar `TEL_DROP_P1`/`TEL_DMA_P1`
e conferir se o layout do `.msu` no SD é o mesmo do ROM (`0x01EE`).
