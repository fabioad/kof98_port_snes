# Veredito dos casos abertos da auditoria de especiais/supers

- ROM: `kof98-snes.sfc` de 12/11/2026 (commit `70438e6`)
- Snapshot da auditoria: `build/specials_recheck_20261112g`
- Ferramenta: `tools/audit_specials_headless.py --confirm` (8 shards, oponente Kyo parado a 24 px)

Este documento fecha, caso a caso, os 57 casos que a auditoria ainda reporta
como `no_impact_review` ou `conditional`. Nenhum deles é comando roubado ou
comando que não entra: em todos o estado **é atingido**. O que falta é dano, e
o motivo está classificado abaixo em três grupos.

Como reproduzir a triagem: a cadeia de estados do fonte vem de
`[Statedef N]` do `.cns` do personagem (HitDef, ReversalDef, TargetLifeAdd,
Projectile e ChangeState/TargetState). Um estado sem nenhum desses
controladores não é um ataque.

## Números

| | |
|---|---|
| Casos auditados | 941 |
| `hit_and_recovered` | 885 |
| `no_impact_review` | 47 |
| `conditional` | 9 |
| Casos distintos abertos | **57** |

Dos 57: **35 são por projeto**, **10 acertam fora do setup padrão** e **12
dependem de uma carga de dano que o port não tem**.

---

## Grupo 1 — Por projeto (não é ataque, ou o dano é condicional)

O estado não tem HitDef próprio (ou o dano só existe quando o oponente ataca).
Testar dano aqui não faz sentido.

| Personagem | Estado | O que é / evidência |
|---|---|---|
| Athena | 1040, 1050, 1060, 1065 | Sem controlador de ataque (cadeias 1040→1041, 1050→1051) |
| Vega | 1400, 1410, 1420, 1430 | Teleportes (`PosAdd` nos dois sentidos, sem ataque) |
| Rugal | 1300, 1310 | Dark Barrier: escudo, sem HitDef |
| Daimon | 1100, 1110 | Chou Ukemi (levantar rápido), sem ataque |
| Kasumi | 1200, 1300, 3100, 3150 | Posturas de contra-ataque (`ReversalDef`) |
| Geese | 1400 | Contra-ataque (`ReversalDef` + `TargetLifeAdd`) |
| Mary | 1520 | Contra-ataque (`ReversalDef`) |
| Billy | 1100 | Contra-ataque (`ReversalDef`; o dano mora em 1101) |
| Chin | 1460, 1461 | Janelas de espera do contra-ataque; o hit mora em 1400/1401 |
| Iori | 1400 | Kuzukaze: agarrão que derruba; o fonte não declara dano (só a queda) |
| Yuki | 1200 | Arremesso de posicionamento: HitDef sem `damage` e sem `TargetLifeAdd` |
| Chris | 1000, 1050, 2000 | Sem controlador de ataque (cadeias 1000→1010→1020 e 1050→1060→1070) |
| Eiji | 1500, 1510 | Sem controlador de ataque |
| Heavy D | 1250, 1900 | Sem controlador de ataque |
| Lucky | 1000, 1010 | Sem controlador de ataque (nem HitDef, nem projétil) |
| Shermie | 2000 | Sem controlador de ataque |
| Omega Rugal | 2000, 2002 | Sem controlador de ataque (cadeia 2000/2002→2001) |

## Grupo 2 — Acerta fora do setup padrão da auditoria

O golpe funciona; a auditoria testa a 24 px contra um Kyo parado com `hold=2`.
Medições feitas à parte (mesma ROM):

| Personagem | Estado | Medição |
|---|---|---|
| Joe | 1410 | 22 de dano a 100–130 px (é um chute voador longo) |
| Ryo | 1510 | 40 de dano a 100–130 px (corrida longa) |
| Yuri | 431 | 14 de dano a 100–130 px (corrida longa) |
| Yuri | 450 | 6 de dano no ápice do pulo (96 px) — fireball aéreo |
| Kim | 1200 | 14 de dano num pulo real; a auditoria força a altura e o takeoff sobrescreve |
| Billy | 3100 | 45 de dano com `hold=3` (a auditoria usa 2) |
| Lucky | 2600 | 22 de dano a 120 px |
| Chizuru | 1004 | 28 de dano com outro cadência; o fonte usa `ifelse(p2movetype = I/H, ...)` |
| Chizuru | 1300 | 18 de dano, mesma condição de postura do oponente |
| Heavy D | 1950 | **parcial**: 1 de 5 contatos (ver nota abaixo) |

Nota Heavy D 1950: o fonte declara `damage = 1,20` em cinco janelas
(elementos 3/8/13/19/24) — 5 de dano no total. O port acerta só a primeira:
a vítima é empurrada ~8 px e as janelas seguintes (tiques 131–181) erram.
Diferença real, mas de 1→5 de dano num golpe que o próprio fonte já define
como fraco; corrigir exige ajustar caixa/velocidade por janela.

## Grupo 3 — A carga de dano não existe no port

O estado é atingido e termina, mas o dano está num helper, projétil ou estado
seguinte que a conversão não trouxe (ou que não foi ligado ao runtime). Não é
comando quebrado; é conteúdo que falta.

| Personagem | Estado | O que falta |
|---|---|---|
| Benimaru | 1100 | Raikouken aéreo: o disparo está no helper 1105 (não ligado) |
| Daimon | 1010 | O `1010` do pacote só volta ao neutro; o trip do fraco vem do helper 1005 (o port emula só o fraco, no estado 48) |
| Eiji | 1200, 1210 | O HitDef está em 1201/1202 (não ligados) |
| Mai | 1043 | O HitDef está em 1045/1046/1047 (não ligados) |
| Kensou | 2000, 2050 | Só `TargetLifeAdd` (dano em vítima presa); sem agarrão ligado |
| Yuki | 1000, 1300 | `Projectile` por helper, sem linha no ProjTab |
| Ryo | 2000, 2010 | Projétil grande no helper 2020, sem linha no ProjTab |
| Omega Rugal | 7200 | Striker: helper 7201, sem equivalente no port |

Implementar esses casos é trabalho de conteúdo (ligar estado seguinte ou
compilar o projétil), não de comando. Ficam registrados aqui para não serem
reabertos como "regressão" a cada rodada.

---

## Como reavaliar

1. Congelar um snapshot (a ferramenta não pode ver um build em andamento):

   ```
   S=$PWD/build/specials_recheck_<data>
   mkdir -p $S/tables
   cp kof98-snes.sfc kof98-snes.msu $S/
   cp build/gen_fight/*_spr.inc build/gen_fight/*_remaining_specials.json $S/tables/
   ```

2. Rodar e comparar com esta rodada (`build/specials_recheck_20261112g`):

   ```
   cd tools
   python3 audit_specials_headless.py $S --confirm --out all.json
   ```

3. Qualquer caso novo em `input_missed` é comando roubado: investigar.
   `no_impact_review` novo: conferir se cai em um destes três grupos.
