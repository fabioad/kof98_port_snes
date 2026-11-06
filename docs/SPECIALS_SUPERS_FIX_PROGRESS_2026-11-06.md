# Correções de especiais e supers — 06/11/2026

Escopo: exemplos confirmados na auditoria funcional de 06/11, com build e
reteste headless nesta mesma data.

## Aplicado no fonte: duração da captura em counters

Em `src/engine/fight.asm`, `AnimTick` mantém o último quadro das vítimas de
contra-ataque (slots 100/102), como já fazia para a vítima de agarrão comum
(76).

Antes, o fim da animação da vítima podia enviá-la ao neutro pelo caminho
genérico, sem limpar `F_GRAB`. Isso impedia `StVictimHeld` de executar
`VH_free` quando o atacante terminasse. O novo comportamento mantém a vítima
sob controle de `StVictimHeld`; a perda do vínculo segue a rotina de soltura
que limpa `F_GRAB` e `F_OWNER`.

## Aplicado nesta etapa: continuações e dano

`tools/build_fight.py` ganhou uma seção de correções tardias
(`POST_CAL_REACTIVATED`, `POST_CAL_TWEAKS`, `POST_CAL_TARGET_LIFE`,
`POST_CAL_ACT_OVERRIDE`, `POST_CAL_PROJS_FULL`) que roda depois de
`calibration.native.apply_profile`, sem invalidar os hashes existentes.

Foram corrigidos os 29 personagens da lista:

- **Animação/hitbox:** Iori 1501/1511/3200/3210, Omega 1020→1021, Leona
  3100→3102, Eiji 1400/1410→1401/1411, Krauser 1210→1211.
- **Continuação ofensiva:** Shingo Kakehourin, Saisyu Orochinagi, Clark
  Gatling, Mature Despair, Vice Withering, Choi/Yashiro/Chris, Yamazaki,
  Rugal Dead End Screamer, Daimon e Brian.
- **Capturas com fase do atacante:** Athena, Chin, King, Chang, Shermie,
  Blue Mary, Heidern e Mr. Big.
- **Projéteis/helpers:** Mai, Lucky, Mr. Big, Krauser e Saisyu.

Os values de dano foram ajustados para a escala de 200 HP do port; as
capturas usam `TargetLifeAdd` onde o MUGEN original dependia de um segundo
HitDef, que o motor nativo não aplica em vítima presa.

## Verificação

Build: `make -f Makefile.pvsnes` concluído. ROM verificada:
`43f5d0755b83fc78e2a9d0b93bf3ff15a663a1ac1e81045b4223c0b9394ad5ca`.

Reteste headless dos 29 states: todos terminaram acima de 1 HP de dano.
Relatório completo e JSON de resultados:

- `build/specials_fix_check_20261106/RELATORIO_CORRECOES.md`
- `build/specials_fix_check_20261106/visual_checks_fix.json`

## Separado para revisão

- **Geese:** o DP acerta; a pose de recuperação prolongada continua em
  revisão visual.
- **Billy:** conflito de comandos e o destino 3100 continuam separados.
