# KOF98 (Neo Geo / YM2610) — timbres e sound test para SNES

Extraído de `kof98.zip` (V-ROMs `242-v1..v4`, 16 MiB de ADPCM-A/B) e dos
registradores do YM2610 capturados pelo MAME enquanto o driver do jogo
toca cada uma das faixas.

- músicas capturadas: **42** (`data/kof98ym/scan.json`)
- timbres no SoundFont: **170** (100 percussão ADPCM-A, 0 FM, 70 melódicos ADPCM-B)
- sequências: **42** em `sequences/` (formato do `cps2conv`)

## Sound test

`kof98_neogeo_soundtest.sfc` — jukebox para SNES (PVSnesLib/SNESMOD).
75 músicas: as 42 faixas extraídas do Neo Geo + 33 MIDIs do projeto
(`kof98_port_snes/music`). Controles: **cima/baixo** escolhe, **esq/dir**
pagina, **A/START** toca, **B** para, **X/Y** volume.

## Como ouvir os timbres

- `samples_wav/` — um .wav por timbre (percussão, FM e melódicos).
- `kof98_ym2610.sf2` — SoundFont com o mesmo mapeamento do banco:
  **banco 0** = FM (0-59), **banco 1** = percussão ADPCM-A (0-99),
  **banco 2** = melódicos/pads ADPCM-B (0-99).
- `presets.json` — papel de cada timbre e quantas notas o driver tocou com ele.
- `previews/*.mp3` — prévias de 25 s renderizadas do .it (libopenmpt) para
  conferir a afinação/ritmo sem ligar o SNES.

## O que o jogo usa de verdade

No driver do KOF98 a **melodia é ADPCM-B** (monofônica) e a **percussão é
ADPCM-A**; o FM aparece em poucos trechos com patch fixo (jingle, stabs e
efeitos), sempre com a mesma frequência. É o mesmo desenho do arcade:
8 canais do SNESMOD = 6 de percussão + 1 de baixo + 1 de melodia.

## Percussão ADPCM-A (100)

| banco:programa | papel | notas usadas no jogo | amostra |
|---|---|---|---|
| `1:0` | snare | 331 | a 00008a snare |
| `1:1` | snare | 1303 | a 00008c snare |
| `1:2` | snare | 644 | a 00008e snare |
| `1:3` | snare | 309 | a 000090 snare |
| `1:4` | snare | 168 | a 00009a snare |
| `1:5` | snare | 415 | a 00009c snare |
| `1:6` | snare | 160 | a 00009e snare |
| `1:7` | snare | 235 | a 0000a6 snare |
| `1:8` | snare | 126 | a 0000ba snare |
| `1:9` | snare | 105 | a 000391 snare |
| `1:10` | snare | 643 | a 00039d snare |
| `1:11` | snare | 80 | a 0003e5 snare |
| `1:12` | snare | 170 | a 0008b4 snare |
| `1:13` | snare | 204 | a 0009a6 snare |
| `1:14` | snare | 92 | a 000ac1 snare |
| `1:15` | snare | 223 | a 000e96 snare |
| `1:16` | snare | 84 | a 000ea6 snare |
| `1:17` | snare | 113 | a 000f8f snare |
| `1:18` | snare | 201 | a 001197 snare |
| `1:19` | snare | 707 | a 001998 snare |
| `1:20` | snare | 240 | a 001a93 snare |
| `1:21` | snare | 431 | a 001c9d snare |
| `1:22` | snare | 115 | a 001eb8 snare |
| `1:23` | snare | 176 | a 001ee5 snare |
| `1:24` | snare | 365 | a 0021ab snare |
| `1:25` | snare | 198 | a 0028aa snare |
| `1:26` | snare | 299 | a 002990 snare |
| `1:27` | snare | 174 | a 002b98 snare |
| `1:28` | snare | 264 | a 002ea6 snare |
| `1:29` | snare | 450 | a 002f9d snare |
| `1:30` | snare | 552 | a 003094 snare |
| `1:31` | snare | 1404 | a 003099 snare |
| `1:32` | snare | 84 | a 0030b4 snare |
| `1:33` | snare | 180 | a 00359d snare |
| `1:34` | snare | 84 | a 0036b0 snare |
| `1:35` | snare | 72 | a 0038b8 snare |
| `1:36` | snare | 700 | a 003aa6 snare |
| `1:37` | snare | 156 | a 003cba snare |
| `1:38` | snare | 3684 | a 003f9c snare |
| `1:39` | snare | 77 | a 004196 snare |
| `1:40` | snare | 250 | a 004496 snare |
| `1:41` | snare | 332 | a 004591 snare |
| `1:42` | snare | 113 | a 004996 snare |
| `1:43` | snare | 252 | a 0049aa snare |
| `1:44` | snare | 74 | a 004c8d snare |
| `1:45` | snare | 161 | a 004f8c snare |
| `1:46` | tom | 830 | a 00528e tom |
| `1:47` | tom | 270 | a 00568f tom |
| `1:48` | tom | 2880 | a 00579c tom |
| `1:49` | tom | 256 | a 0057aa tom |
| `1:50` | snare | 456 | a 005a98 tom |
| `1:51` | tom | 305 | a 005ba6 tom |
| `1:52` | snare | 271 | a 00609c snare |
| `1:53` | tom | 107 | a 00649b tom |
| `1:54` | snare | 3224 | a 00669c snare |
| `1:55` | snare | 89 | a 0066aa snare |
| `1:56` | snare | 738 | a 006791 snare |
| `1:57` | snare | 134 | a 0069ab snare |
| `1:58` | snare | 287 | a 006ea6 snare |
| `1:59` | snare | 440 | a 007414 snare |
| `1:60` | snare | 400 | a 007499 snare |
| `1:61` | snare | 816 | a 007591 snare |
| `1:62` | tom | 962 | a 00819c tom |
| `1:63` | tom | 808 | a 008391 tom |
| `1:64` | tom | 252 | a 008aa4 kick |
| `1:65` | tom | 532 | a 008cae tom |
| `1:66` | tom | 90 | a 008eab tom |
| `1:67` | tom | 899 | a 00908b kick |
| `1:68` | tom | 216 | a 0091ac tom |
| `1:69` | kick | 128 | a 0097aa kick |
| `1:70` | kick | 170 | a 009d95 kick |
| `1:71` | kick | 323 | a 00a08e kick |
| `1:72` | kick | 239 | a 00a096 kick |
| `1:73` | kick | 587 | a 00a09e kick |
| `1:74` | kick | 211 | a 00a38c kick |
| `1:75` | tom | 327 | a 00a38f tom |
| `1:76` | tom | 70 | a 00a998 tom |
| `1:77` | kick | 163 | a 00abaa kick |
| `1:78` | kick | 257 | a 00ad94 kick |
| `1:79` | kick | 642 | a 00b68a kick |
| `1:80` | kick | 128 | a 00ba95 kick |
| `1:81` | kick | 166 | a 00c898 kick |
| `1:82` | kick | 144 | a 00caaa kick |
| `1:83` | kick | 323 | a 00d196 kick |
| `1:84` | kick | 244 | a 00daab kick |
| `1:85` | kick | 71 | a 00dbb0 kick |
| `1:86` | kick | 112 | a 00de98 kick |
| `1:87` | kick | 91 | a 00e095 kick |
| `1:88` | kick | 490 | a 00e0ba kick |
| `1:89` | kick | 512 | a 00e2e9 kick |
| `1:90` | kick | 4716 | a 00e79c kick |
| `1:91` | kick | 403 | a 00e8a7 kick |
| `1:92` | kick | 76 | a 00ede3 kick |
| `1:93` | kick | 106 | a 00f0ba kick |
| `1:94` | kick | 5353 | a 00f19b kick |
| `1:95` | kick | 139 | a 00f1a3 kick |
| `1:96` | kick | 647 | a 00f38f kick |
| `1:97` | kick | 793 | a 00f48b kick |
| `1:98` | kick | 1021 | a 00f48d kick |
| `1:99` | kick | 516 | a 00f79b kick |

## FM (0)

| banco:programa | papel | notas usadas no jogo | amostra |
|---|---|---|---|

## Melódicos / pads ADPCM-B (70)

| banco:programa | papel | notas usadas no jogo | amostra |
|---|---|---|---|
| `2:0` | lead | 14 | b 0000c6 |
| `2:1` | bass | 211 | b 0000c8 |
| `2:2` | bass | 119 | b 0000ca |
| `2:3` | tom | 2 | b 0000cc |
| `2:4` | lead | 3 | b 0000ce |
| `2:5` | pad | 6 | b 0000d0 |
| `2:6` | snare | 14 | b 0000d2 |
| `2:7` | tom | 82 | b 0000d4 |
| `2:8` | tom | 66 | b 0000d6 |
| `2:9` | tom | 6 | b 0000d8 |
| `2:10` | tom | 8 | b 0000da |
| `2:11` | lead | 101 | b 0000dc |
| `2:12` | mel | 7 | b 0000de |
| `2:13` | bass | 603 | b 0000e0 |
| `2:14` | mel | 252 | b 0001d1 |
| `2:15` | tom | 2 | b 0009d2 |
| `2:16` | bass | 20 | b 000edb |
| `2:17` | pad | 20 | b 0010d3 |
| `2:18` | bass | 11 | b 0011d6 |
| `2:19` | bass | 51 | b 0017cf |
| `2:20` | bass | 755 | b 001ad4 |
| `2:21` | lead | 120 | b 0021d2 |
| `2:22` | lead | 409 | b 0022c7 |
| `2:23` | tom | 8 | b 0022cc |
| `2:24` | pad | 2 | b 0023d9 |
| `2:25` | bass | 32 | b 0024d7 |
| `2:26` | bass | 4 | b 0024d8 |
| `2:27` | tom | 2 | b 0025da |
| `2:28` | lead | 10 | b 0028d5 |
| `2:29` | bass | 816 | b 002acc |
| `2:30` | bass | 3 | b 002bdf |
| `2:31` | tom | 66 | b 0032c6 |
| `2:32` | lead | 73 | b 0032dd |
| `2:33` | bass | 16 | b 0039db |
| `2:34` | lead | 2038 | b 003ada |
| `2:35` | bass | 1 | b 0040ce |
| `2:36` | bass | 39 | b 0044c9 |
| `2:37` | lead | 24 | b 0047cb |
| `2:38` | bass | 3 | b 0047de |
| `2:39` | pad | 3 | b 0052df |
| `2:40` | bass | 108 | b 0053d9 |
| `2:41` | bass | 144 | b 0058cd |
| `2:42` | lead | 30 | b 005fd6 |
| `2:43` | bass | 2 | b 0062da |
| `2:44` | bass | 32 | b 0062db |
| `2:45` | bass | 4 | b 0068d8 |
| `2:46` | bass | 20 | b 006bcf |
| `2:47` | tom | 2 | b 0072d7 |
| `2:48` | tom | 47 | b 0074db |
| `2:49` | bass | 523 | b 0080d1 |
| `2:50` | bass | 2 | b 0081d7 |
| `2:51` | bass | 762 | b 0088d3 |
| `2:52` | bass | 24 | b 0088dc |
| `2:53` | lead | 52 | b 0088e0 |
| `2:54` | bass | 140 | b 008edd |
| `2:55` | tom | 2 | b 008fda |
| `2:56` | bass | 32 | b 0090d4 |
| `2:57` | tom | 2 | b 0091ca |
| `2:58` | bass | 804 | b 0095d5 |
| `2:59` | tom | 8 | b 0097db |
| `2:60` | tom | 1 | b 0098d8 |
| `2:61` | bass | 96 | b 009bd9 |
| `2:62` | tom | 4 | b 00a1df |
| `2:63` | tom | 2 | b 00a5da |
| `2:64` | tom | 6 | b 00afdb |
| `2:65` | mel | 148 | b 00b0d7 |
| `2:66` | tom | 8 | b 00beda |
| `2:67` | tom | 6 | b 00c7db |
| `2:68` | mel | 19 | b 00dfdb |
| `2:69` | tom | 40 | b 00e8d9 |

