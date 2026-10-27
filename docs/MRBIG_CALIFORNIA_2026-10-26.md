# Mr. Big — California Romance (26/10/2026)

## Golpe

O movimento do Mr. Big que corre e termina com o anti-aéreo é a
**California Romance**:

- fraca: `MFD_df+x` → estado 1400 → 1401 → 1402;
- forte: `MFD_df+y` → estado 1410.

A animação forte (1410) tem quatro `HitDef`s, nos elementos 4, 6, 9 e 10.
A fraca distribui os golpes entre 1401 (um) e 1402 (dois), com um helper
1406 de ReversalDef no caminho.

## Defeito

O port só tinha os estados 1400 e 1410 ligados a sids. Os golpes da versão
fraca ficavam em 1401/1402, que **não estavam mapeados** — a animação rodava e
o Big não acertava nada. Na versão forte, o gerador guardava apenas o
primeiro `HitDef`; os outros três eram descartados. Além disso, o terceiro
contato tinha `fall=1`, e o motor nativo colocava a vítima direto em
`S_DOWN`, tornando-a imune ao quarto golpe.

## Correção

A California Romance agora usa quatro contatos, no mesmo esquema das
slices do anti-aéreo da Sakura:

| Sid | Animação | Contato | Dano |
|---|---|---|---|
| 52 | 1400 (startup fraco) | — | — |
| 59 | 1410, quadros 0–4 | 1º | 5 |
| 53 | 1410, quadros 0–4 | 1º (forte) | 6 |
| 56 | 1410, quadros 5–6 | 2º | 6 |
| 57 | 1410, quadros 7–8 | 3º | 7 |
| 58 | 1410, quadros 9–14 | 4º (launcher) | 7 |
| 60 | 1403 (pouso) | — | — |

- A fraca mantém o startup 1400 e entra na sequência 1410 pelo sid 59.
- A forte começa direto no sid 53.
- `slice_no_fall` remove o knockdown apenas do 3º contato (sid 57); o
  4º mantém `fall=1` e lança a vítima.
- `state_vel` mantém a corrida de 7 px/frame entre as slices.
- Totais: **25 HP na fraca** e **26 HP na forte**, próximos dos 26 HP do
  anti-aéreo da Sakura.

A cadeia gerada é:

```text
fraca:  52 -> 59 -> 56 -> 57 -> 58 -> 60 -> 0
forte:       53 -> 56 -> 57 -> 58 -> 60 -> 0
```

## Validação

Teste headless `tools/test_mrbig_california_headless.py`:

- fraca: estados `[52,59,56,57,58,60,0]`, **4 contatos**, **25 HP**;
- forte: estados `[53,56,57,58,60,0]`, **4 contatos**, **26 HP**;
- ambos terminam com os dois lutadores no estado 0.

Teste de tabelas `tools/tests/test_mrbig_california.py`: PASS.

## Build

- ROM: checksum **`$DA94`**,
  SHA-256 `a1928fdd…240f2f88`.
- MSU: SHA-256 `3e8945c3…868de386` — **mudou**, porque a nova sequência
  passou a usar uma amostra de voz do Big. Copie ROM e MSU juntos.
