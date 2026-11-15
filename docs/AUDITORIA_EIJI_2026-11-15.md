# Auditoria do Eiji (2026-11-15)

Escopo: comparar o fonte MUGEN (`assets/characters/Eiji-KOF98/Eiji-S.cns`, `Eiji-H.cns`, `Eiji.cmd`) com o que o port liga em `tools/build_fight.py`, `tools/newroster.py` e `Eiji_SNES.cmd`.

**Nada foi compilado, rodado em ROM ou commitado nesta rodada.** Tudo abaixo vem da leitura do fonte e do resultado headless já existente (`build/specials_recheck_20261113/shard6.json`). Itens marcados "a confirmar" são inferências.

## 1. Mapa de slots

| Slot | Estado fonte | Golpe |
|---|---|---|
| 48/49 | 1300/1310 (dash → 1305 via slot 59) | Kotsu Hazaki |
| 50/51 | 1200/1210 | Ryuuei-jin |
| 52/53 | 1400/1410 (encadeado em 103–106/112) | Tenmakyaku |
| 54/55 | 1500/1510 | Kageutsushi (`by_design`, sem ataque) |
| 56/57 | 1100/1110 | Kasumi-giri |
| 85/86/87 | 3000/3010/3020 | Zantetsuha / rápida / MAX |
| 107 | 1000 | Kikouhou |
| 108 | 1600 (clipe do 3100) | Mukuro Nui |
| 109/110 | 3100/3120 | Zantetsu Tourouken |
| 111 | 3200 | Yamikari |

## 2. Resultado headless (dano no Kyo parado a 24 px; tudo `hit_and_recovered`)

1300/1310=40, 1200/1210=22, 1400/1410=22, 1100/1110=34, 3000/3010/3020=70 cada, 1000=14, 1600=14, 3100=20, 3120=30, 3200=35, 1500/1510=0 (by_design).
A auditoria só checa "acerta e recupera"; não compara com `meta.damage`.

## 3. Divergências de comando

- **Kikouhou (1000)**: fonte QCF+x/y; port QCF×2 (`KIKOUHOU`, `cmd_extra`, `QCF2`).
- **Mukuro Nui (1600)**: fonte QCF+x/y **no ar**; port DP+A/B no chão.
- **Zantetsu Tourouken (3100/3120)**: fonte usa botões a/b/a+b; port usa QCB×2 + x ou x+y (`ZANTETSU_W (0,1)`, MAX `(0,3)`).
- **Yamikari (3200)**: fonte x/y/x+y; port mapeia A/B com `HCB2`.
- Conferidos e iguais: Kotsu, Ryuuei, Tenmakyaku, Kageutsushi, Kasumi-giri, Zantetsuha (x/y/x+y).

## 4. Divergências funcionais

1. **Mukuro Nui**: fonte é aéreo e solta o helper 1610 (Projectile dano 11, `hitflag MAFD`, VelSet 6,6 diagonal). O port reaproveita o clipe de espada 3100 com override `active 7 / damage 25`. Medido 14 (esperado 25; `projectile=True`), ou seja, o dano vem de um projétil inferido, não do corte.
2. **Ryuuei rush (1200/1210)**: fonte tem `tail_ticks` 21 após 1200 e 41 após 1210; o port usa `_tweak("eiji","tail_ticks",{1201: 21})` para ambos, então o forte fica com hold curto. O helper 1200→1220 tem `HitOverride` de projéteis (→1221→helper 1225, Projectile 12/16), um contra-projétil que provavelmente não existe no port (a confirmar).
3. **MAX Zantetsuha (3020)**: fonte dispara dois projéteis (helpers 3025 e 3026, dano 40 cada, o segundo `Diagup`); o port mede 70, igual aos de tiro único. Provavelmente um projétil só (a confirmar).
4. **Supers de vários hits** reduzidos a uma fatia fixa por `slice_damage`: 3105 (3 janelas×4 + final 13), 3126 (4 janelas×6 + final 14), 3200 (TargetLifeAdd 17×4+, via 3210). Somar e comparar com 20/30/35.
5. **Tenmakyaku**: conexão depende de `air_box_patch_frames` em 1401/1411 (fonte sai por MoveContact). Hitdefs 104/112 usam dano 10 contra 12 do fonte.
6. **Custo de barra**: fonte gasta 1000 em 3000/3010 e 2000 (1000 em MAX) em 3020/3120/3200. Não verificado no port (`max_masks.inc`, `COMMAND_LIST`).

## 5. Escala de dano (port vs. base do fonte)

| Golpe | Port | Fonte |
|---|---|---|
| Kikouhou | 14 | 20 |
| Kasumi-giri 1100 | 34 | 17 |
| Kotsu 1305 | 40 | 20 |
| Ryuuei 1201 | 22 | 16 |
| Zantetsuha 3005 | 70 | 38 |
| Tenmakyaku | 12+10 | 12+12 |

O 14 do Kikouhou parece o valor genérico de projétil (também usado em Yuki e Ryo). A escala não é uniforme; decidir se é intencional (balanceamento do port) ou resíduo.

## 6. Arte

`Eiji.air` difere de `Eiji.air.orig` (2302 linhas, alterado em 23/10): vários Clsn2 removidos nas poses 41/120/121/182 e durações trocadas. Risco de hurtbox ausente. **Não avaliado.**

## 7. Cobertura de teste

Apenas `tools/test_category_d_batch2_headless.py` (107–111) e `test_projectile_calibration.py:57` (projétil 3002). Sem teste para 48/49, 50/51, 52/53, 56/57, 85–87.

Observação: `newroster.py` ainda diz `char_scale: 0.81`, enquanto o build usa 1.0 (`char_scales.eiji`).

## 7b. Rodada de correção (2026-11-15): nenhum código alterado

Revisei cada item contra `build_fight.py` e decidi não editar código às cegas, porque nada pode ser compilado nem medido em ROM nesta rodada:

- **Tenmakyaku 104/112 (dano 10 vs 12)**: no fonte, 1402 e 1412 têm dois HitDefs de `12/var(23)` cada, e `var(23)` é divisor de hits. O 10 pode ser compensação deliberada do port. Mudar sem medir arrisca estourar a soma. Não alterado.
- **Ryuuei `tail_ticks` (21 vs 41)**: 1200 e 1210 compartilham o slot 58 e a animação de 1201. `tail_ticks` é por animação, então separar exige um slot novo para o forte (mudança estrutural). Não alterado.
- **MAX Zantetsuha (dois projéteis)**, **Mukuro Nui** e **supers com `slice_damage`**: dependem de medir hits na ROM.
- **Comandos (Kikouhou, Zantetsu, Yamikari)**: podem ser escolha de design para não colidir com outros inputs; decidir antes de trocar.
- **`char_scale: 0.81` em `newroster.py`**: todos os personagens têm esse valor, então é resíduo geral, não do Eiji. Não alterado.

Quando houver build disponível, aplicar na ordem da seção 8, medindo cada item no headless.

## 8. Recomendações (por prioridade)

1. Mukuro Nui: decidir entre fidelidade (aéreo + helper 1610) e manter o atalho; documentar o dano real (14 vs 25).
2. MAX Zantetsuha: verificar se há dois projéteis; senão ligar o segundo ou ajustar o dano.
3. Somar os hits das supers 3100/3120/3200 e calibrar `slice_damage`.
4. Corrigir `tail_ticks` do 1210 (41) separado do 1200 (21).
5. Revisar comandos de Zantetsu Tourouken e Yamikari contra o `Eiji.cmd` ou registrar como decisão de design.
6. Checar custo de barra no port.
7. Comparar `Eiji.air` com `.orig` quanto a hurtbox.
8. Adicionar testes headless para 48/49, 50/51, 52/53, 56/57 e 85–87, comparando com `meta.damage`.
