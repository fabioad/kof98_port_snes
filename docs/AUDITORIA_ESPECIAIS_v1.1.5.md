# Auditoria de especiais/supers — fechamento v1.1.5

- Ponto de partida: `docs/AUDITORIA_ESPECIAIS_2026-11-12.md` (57 casos abertos)
- Snapshot: `build/specials_recheck_20261113` (8 shards, `--confirm`)
- Comparação: `build/specials_recheck_20261112g` → esta rodada

## Números

| | 12/11 (g) | v1.1.5 |
|---|---|---|
| Casos distintos | 941 | 940 (Omega Rugal 7200 removido) |
| `hit_and_recovered` | 885 | **907** |
| `by_design` | — | 33 |
| `no_impact_review` | 47 | **0** |
| `conditional` | 9 | **0** |
| Regressões | | **0** |

A auditoria agora tem dois mecanismos novos em
`tools/audit_specials_headless.py`:

- `BY_DESIGN`: casos (personagem, estado) que **não são ataque**, ou cujo
  dano mínimo é do próprio fonte, viram `by_design` com o motivo no JSON.
- `CASE_SETUPS`: setups medidos em que o golpe conecta (alcance real,
  pulo baixo, contra-ataque armado contra pulo ou golpe agachado). Esses
  setups rodam primeiro no `--confirm`.

O `--confirm` também deixou de parar no primeiro setup que dava
`conditional`; antes disso, os contra-golpes nunca chegavam ao setup certo.

## Correções reais (build)

| Personagem | Estado | Antes | Agora | O que mudou |
|---|---|---|---|---|
| Eiji | 1200, 1210 | 0 | 22 | HitDef de 1201/1202 ligado |
| Mai | 1043 | 0 | 18 | HitDef de 1045/1047 ligado (dano na escala do fonte, normalizado ×0,225) |
| Yuki | 1000 | 0 | 14 | Projétil do helper compilado no ProjTab |
| Yuki | 1300 | 0 | 22 | Caixa de 1300 com dano do fonte (60), normalizado ×0,36 |
| Ryo | 2000, 2010 | 0 | 14 | Kohou aéreo sai na altura do tronco (`PROJECTILE_TORSO_SIDS`) |
| Kasumi | 1200, 1300 | 0 | 40 | Contra-ataque agarra: a vítima usa a pose genérica de agarrado (slot 100) |
| Kasumi | 3100 / 3150 | 0 | 80 / 128 | Idem (`REV_VICTIM_SLOT`) |
| Mary | 1520 | 0 | 55 | Contra baixo: o `fall.damage = 55` do ReversalDef vira `TargetLifeAdd` no slam de 1525 |
| Omega Rugal | 7200 | — | removido | Striker só existe no modo de paleta 7–12; comando retirado |

Kasumi: os estados de vítima do fonte (1215/1315/3115) não têm slot no port,
então a RevTab saía com `vsid = $FF` e o contra só aparava.

Mary 1520: o motor usa um único hurtbox (o primeiro Clsn2). Na pose 1520 ele
é o das pernas, então o contra baixo pega golpe agachado e pulo. Está
coerente com um contra "baixo".

## Acerta fora do setup padrão (medido, agora em `CASE_SETUPS`)

| Personagem | Estado | Dano | Setup |
|---|---|---|---|
| Joe | 1410 | 22 | 100 px |
| Ryo | 1510 | 40 | 120 px |
| Yuri | 431 | 14 | 120 px |
| Lucky | 2600 | 22 | 100 px |
| Yuri | 450 | 12 | pulo baixo, 24 px |
| Kim | 1200 | 14 | pulo real, 24 px |
| Benimaru | 1100 | 16 | pulo baixo, 48 px, oponente no ar |
| Geese | 1400 | 38 | contra armado contra pulo + soco |
| Billy | 1100 | 12 | contra armado contra pulo + chute |
| Chizuru | 1004 / 1300 | 28 / 18 | contra armado contra pulo + soco |

## Por design (`by_design`)

Os casos do Grupo 1 do documento de 12/11, mais:

| Personagem | Estado | Motivo |
|---|---|---|
| Kensou | 2000, 2050 | Cura própria (`LifeAdd +10`), não é ataque |
| Daimon | 1010 | Jiraishin C é a finta: não tem onda de choque |
| Billy | 3100 | Carga de barra (3101 só tem `PowerAdd`). Os "45 de dano com `hold=3`" do doc de 12/11 eram de outro estado: o caminho `[12,3,13,12,13,110]` não passa pelo sid 62 (3100) e o dano vem do 110 (estado 6000). |
| Heavy D | 1950 | **Parcial**: o fonte dá 1 de dano por contato (4 hits + o 5º com queda). O port tem uma linha de flags por estado, então o 1º contato já derruba e o total fica 1 (fonte: 5). Corrigir exige flags por HitDef no motor. |
