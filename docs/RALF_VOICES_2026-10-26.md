# Vozes do Ralf — Galactica Phantom fraco (26/10/2026)

## Mapa atual

O gerador mapeia `PlaySnd` com amostra do `.snd` para op7 (voz) apenas nos
estados ligados a um sid. Depois da correção, o Ralf tem:

| Golpe | Sid/estado | Voz | Quando toca |
|---|---|---|---|
| Air Blitz | 54 / 455 | 4 | tempo 7 do estado |
| Arremesso básico | 75 / 301 | 0 | tempo 29 |
| **Galactica Phantom fraco** | **85 / 500** | **5** | **elemento 51** |
| Galactica Phantom forte | 86 / 501 | 6 | tempo 123 |
| Pose de vitória | 90 / 181 | 1 | tempo 100 |

## Defeito

O Galactica fraco estava sem voz porque o `PlaySnd` original dispara no
elemento 52 de uma animação de 182 ticks. O gerador convertia vozes de
animações em loop para tempo de estado, mas o gatilho de ActTab só carrega
7 bits (0..127); a voz era descartada silenciosamente.

## Correção

`tools/build_fight.py` agora usa o gatilho por **elemento de animação**
como fallback quando o tempo calculado não cabe. `ralfAct85` passou a ter:

```asm
.db 51,7,45,0   ; elemento 51, op7 (voz), índice 5
```

Confirmado no headless: ao entrar no estado 85, o Ralf enfileira a voz
índice 5 (3.375 bytes) e o cache bate com o `.msu`.

Vulcan Punch (400/401), Gatling (420/421), o grab (440/441) e os supers de
corrida não têm amostra de voz nos estados correspondentes do CNS original;
eles continuam silenciosos por falta de dado de origem, não por regressão
do port.

## Validação

- `tools/tests/test_ralf_voice_rows.py`: PASS (garante as linhas de voz).
- `test_ai_headless.py`: PASS.
- ROM atual: checksum **`$C547`**,
  SHA-256 `c3e8c7d3…05c7cf35`.
