# Yuki — Ai no Kusanagi: sprite do Kyo e recuperação (2026-11-09)

## Resumo

O super **Ai no Kusanagi Dai Koushin** da Yuki (sid 89, estado MUGEN 3350)
terminava com o hold de 255 ticks do anim 3300 — na prática, **~4 segundos
parada** depois do ataque. O Kyo que aparece no golpe (helper 3355, AIR 1903,
grupo 2001 do SFF da Yuki) também não era desenhado: o sid 89 usava o clipe
primário de projétil (a chama do Naku Ko).

A correção:

- anim 3300 com cauda limitada a 24 ticks (recuperação em **123 ticks**);
- clipe alternativo de ProjFx com o frame do Kyo (63×64, 12 tiles);
- sid 89 passa a selecionar esse clipe alternativo, mantendo velocidade,
  dano e guarda originais;
- contra **Kyo / Kyo Nests / Kyo Ash** o sprite é ocultado, mas o hitbox
  continua ativo (o super ainda acerta).

## Recuperação

- Antes: `F_STATE` ficava em 89 por **255+ ticks** (hold `t = 255` da última
  pose do AIR 3300). O estado só voltava a 0 depois de ~4,2 s.
- Agora: `tail_ticks: {13001: 6, 3300: 24}` em `tools/newroster.py`
  (mantido também em `tools/gen_char_cfg.py`). A última pose dura 24 ticks;
  medido em emulador: **recuperação no tick 123**, `F_STATE` volta a 0.

## Sprite do Kyo

- Origem: estado 3355 (`Kyo+Moto`) do CNS da Yuki, anim 1903 / grupo 2001.
- Como o motor nativo não tem corpos helper, o Kyo viaja no slot de projétil
  compartilhado (`SPARKS`), igual aos helpers da Kasumi.
- `tools/calibration/projectiles.py`:

  ```python
  "yuki": {
      "action": 1903,
      "frames": ((1, 255),),
      "sids": (89,),
      "release": 2,
      "squeeze_w": 64,
      "squeeze_h": 64,
  }
  ```

  - O frame 1903,1 (63×82) é comprimido para **63×64** e cabe na página de
    16 tiles do efeito (12 células não vazias).
  - O clipe alternativo é one-shot; o frame de **255 ticks** mantém o sprite
    até o tiro acertar ou expirar (TTL de 90 ticks).
  - O clipe primário (chama do AIR 1315) continua no sid 88 (MAX Naku Ko).
  - O ProjTab do sid 89 ganhou o bit2 (`present`) para selecionar o clipe
    alternativo: `00 0b 16 05 a0 1d`.

## Ocultar contra Kyo

- `SPK_GRD` bit1 = “sprite oculto” (bit livre: a guarda usa os bits 4-7,
  `ProjRadius` trata códigos <8 como o raio normal de 24 px e o offset de
  spawn já foi consumido em `ProjBallisticSetup`).
- Em `ProjSpawn`, quando o atacante é `CharYuki` no sid 89 e o oponente é
  `CharKyo`, `CharKyonests` ou `CharKyoash`, o bit é ligado.
- `DrawSparks` pula o desenho desse slot (somente quando `SPK_ATTR` bit7
  confirma que é projétil, para nunca esconder um spark cosmético que reutilize
  o slot); `TickSpark`/colisão continuam normais, então o dano e o hitbox não
  mudam.

Resultado medido:

| Oponente | Recuperação | Sprite do Kyo | OAM do helper | Dano |
|----------|-------------|---------------|---------------|------|
| Mai      | 123 ticks   | desenhado     | +32 bytes (12 células) | 200 → 90 |
| Kyo      | 123 ticks   | oculto        | 0             | 200 → 90 |
| Kyo Nests| 123 ticks   | oculto        | 0             | 200 → 90 |
| Kyo Ash  | 123 ticks   | oculto        | 0             | 200 → 90 |

## Arquivos alterados

- `src/engine/fight.asm`
  - `DrawSparks`: respeita o bit “sprite oculto”.
  - `ProjSpawn`: marca o Kyo do super como oculto contra as variantes de Kyo.
- `tools/calibration/projectiles.py`: clipe alternativo do Kyo para o sid 89.
- `tools/newroster.py` / `tools/gen_char_cfg.py`: `tail_ticks` do anim 3300.
- `tools/test_yuki_kusanagi_headless.py`: regressão nova (4 confrontos).

## Validação

```text
PASS vs mai: recovery=123, Kyo sprite drawn (+32 OAM bytes), super hits 200->90
PASS vs kyo: recovery=123, invisible Kyo, super still hits 200->90
PASS vs kyonests: recovery=123, invisible Kyo, super still hits 200->90
PASS vs kyoash: recovery=123, invisible Kyo, super still hits 200->90
PASS: Yuki Kusanagi helper art, mirror-Kyo suppression and recovery
```

- `python3 -m pytest tools/tests -q`: **312 passed, 5504 subtests passed**.
- Projéteis que compartilham a paleta de efeitos continuam OK:
  `test_terry_geyser_headless`, `test_yuri_projectile_anim_headless`,
  `test_geese_projectiles_headless`, `test_projectile_clash_headless`,
  `test_athena_specials_headless`.
- `make -f Makefile.pvsnes verify`: **OK**, checksum **`$252B`**.
- `test_projectile_render` continua com a falha antiga de expectativa
  (`attr $04` vs `$34`), já reproduzida no ROM baseline; não é regressão
  deste trabalho.

## Atualização (2026-11-12): contra Kyo o projétil volta a aparecer

- **Antes:** contra Kyo / Nests / Ash o corpo do helper era oculto
  (`SPK_GRD` bit1) para não duplicar o oponente — e o super ficava sem
  nenhum sprite visível.
- **Agora:** nesse confronto o sid 89 desenha o **clipe primário** (a chama
  do AIR 1315, o projétil de antes), visível, com velocidade, dano e guarda
  inalterados.  O clipe alternativo com o Kyo continua valendo para os
  demais oponentes.
- O bit1 de `SPK_GRD` e o teste de "oculto" no `DrawSparks` foram removidos.
- `tools/test_yuki_kusanagi_headless.py` confere os dois clipes (anims
  diferentes) e que o tiro continua acertando; capturas em
  `build/yuki_sheet_kyo.png` (chama) e `build/yuki_sheet_mai.png` (Kyo).
