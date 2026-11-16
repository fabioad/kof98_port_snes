# Heavy D!: Shadow forte (D,D + Y), 15/11/2026

## Problema

O Shadow forte (estado 1950, sid 59) acertava **1 de 5 contatos** e o
primeiro já derrubava. O dano total ficava em 1 em vez dos 5 da fonte.

## Causa

O estado 1950 da fonte tem dois `HitDef`:

- o primeiro, redisparado nos `animelem` **3/8/13/19**, com
  `damage = 1,20`, `ground.velocity = 0` e **`air.fall = 1`**;
- o segundo, no `animelem` **24**, com `fall = 1` — o derrubão.

O extrator escolhe para o estado a linha do HitDef que derruba (o segundo)
e, além disso, o `air.fall = 1` do primeiro virava a flag `fall` da linha
única. Resultado: a tabela tinha uma linha só, com `fall = 1` e janela no
animelem 3, então **o primeiro contato derrubava** e os outros quatro não
podiam mais conectar (vítima em `S_DOWN`).

## Correção

Em `tools/build_fight.py`, no bloco `POST_CAL_TWEAKS` do Heavy D (aplicado
depois de `apply_profile`, então o perfil de calibração continua válido):

- o clipe AIR 1950 (35 quadros) foi dividido em dois sids:
  - **59** — elementos 1–23: os quatro contatos que prendem a vítima,
    sem knockdown, rearmados por `hit_resets` nos elementos 8/13/19
    (frames 7/12/18, `MoveHitReset` op18);
  - **62** — elemento 24 até o fim: o launcher (`fall = 1`) e a
    recuperação. Entra por `slice_hits` (HitDef 2) e volta ao neutro no
    fim (`62 -> 0`);
- `gvx`/`gvy` do sid 59 foram zerados porque o parser troca
  `ground.velocity = 0` por 1.5 px/tick, o que empurraria a vítima para
  fora da última janela;
- o sid 62 usa o segundo HitDef: `gvx = 4`, `gvy = -6.8`, `avx = 4`,
  `avy = -6.8`, como na fonte.

O gancho genérico de `POST_CAL_TWEAKS` agora também sincroniza a chave
`anims` com a cópia local usada para gerar a `AnimTab` (antes só o
`cfg` era atualizado, e um sid novo ficaria apontando para o clipe 47).

## Tabelas geradas

| sid | active | flags | dano | gvx/gvy |
|---:|---:|---|---:|---|
| 59 | 3 | `0x8220` (sem fall) | 1 | 0 / 0 |
| 62 | 1 | `0x8221` (fall) | 1 | 4.0 / −6.8 |

`TransTab`: `59 -> 62` (fim da animação) e `62 -> 0`.
`ActTab` do 59: op18 nos frames 7, 12 e 18.

## Limites conhecidos

- O swish autoral do elemento 24 (`PlaySnd 300,0`, linha de tempo exato 53)
  fica no primeiro slice e não toca no launcher. O contato continua com o
  som de impacto do HitDef. Recuperar esse cue exigiria linhas de PlaySnd
  cientes de slice, que nenhum outro golpe fatiado usa hoje.
- O contador de 5 contatos do motor não é usado aqui: o knockdown vem do
  `fall = 1` do próprio HitDef final.

## Validação

- `python3 -m unittest tools.tests.test_heavyd_brian_calibration` — os 12
  testes passam, incluindo `ShadowStrongTests` (configuração, tabelas e
  transições).
- ROM PRO de 15/11 23:28, sha256 `282a202291afe6b1…`; snapshot em
  `build/specials_recheck_20261115_heavyd/` (ROM, MSU e `heavyd_spr.inc` do
  mesmo build).
- `python3 audit_specials_headless.py <snapshot> --confirm --chars heavyd`:

| Estado | Antes | Agora |
|---|---|---|
| 1950 (Shadow forte) | `by_design`, 1 de dano | **`hit_and_recovered`, 5 de dano** |

  O personagem fecha 17 `hit_and_recovered` + 2 `by_design` (1900 é finta
  sem HitDef; 1250 não tem controlador de ataque), sem casos abertos.
- `BY_DESIGN` do estado 1950 foi removido de
  `tools/audit_specials_headless.py`; uma queda para 1 de dano volta a
  aparecer como `no_impact_review` em vez de ser mascarada.
