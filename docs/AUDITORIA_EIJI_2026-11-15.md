# Auditoria do Eiji — correções (2026-11-15)

Escopo: comparar o fonte MUGEN (`assets/characters/Eiji-KOF98/Eiji-S.cns`, `Eiji-H.cns`, `Eiji.cmd`) com o que o port liga em `tools/build_fight.py`, medir o comportamento na ROM e corrigir o que estava errado.

Medições feitas por *headless* (Snes9x libretro) sobre a build de 15/11 15:08 (`kof98-snes.sfc`, sha256 `e6b2a65140cd08a5…`), com log de HP por tick. **Nenhuma ROM foi recompilada nesta rodada**: o código foi corrigido, mas os números pós-correção precisam de um novo build.

## 1. Mapa de slots

| Slot | Estado fonte | Golpe |
|---|---|---|
| 48/49 | 1300/1310 (dash → 1305 via slot 59) | Kotsu Hazaki |
| 50/51 | 1200/1210 | Ryuuei-jin |
| 52/53 | 1400/1410 (encadeado em 103–106/112) | Tenmakyaku |
| 54/55 | 1500/1510 | Kageutsushi (teleporte, sem ataque) |
| 56/57 | 1100/1110 | Kasumi-giri |
| 85/86/87 | 3000/3010/3020 | Zantetsuha / rápida / MAX |
| 107 | 1000 | Kikouhou |
| 108 | 1600 (clipe do 3100) | Mukuro Nui |
| 109/110 | 3100/3120 | Zantetsu Tourouken |
| 111 | 3200 | Yamikari |

## 2. Como o port calcula dano (para ler as tabelas)

- `damage_scale = 2.0` para o Eiji: tudo que vem do CNS é multiplicado por 2 na compilação. Confirmado nas normais: soco fraco fonte 7 → port 14, soco forte 11 → 22, chute fraco 4 → 8, chute forte 16 → 32.
- Especiais que já estavam certos seguem a mesma regra: 1305 fonte 20 → 40; 1100 fonte 17 → 34.
- Projéteis usam o byte de dano do `ProjTab`, **não** o `DamageTab`. Quando a expressão do fonte tem `ifelse(var(6),…)` o compilador não avalia e grava o *default* **14**. Era o caso do Kikouhou e dos três Zantetsuha.
- Slots 85–89 caem no sequencial de **5 contatos** do motor (`fight.asm`, `S_SUPPER`), então o byte do `ProjTab` é **dano por contato** (5 × valor = total).

## 3. Medição antes das correções

| Golpe | Fonte | Antes no port | Situação |
|---|---|---|---|
| 1000 Kikouhou | 20 (forte 25) | 14, 1 contato | default do compilador |
| 1600 Mukuro Nui | 11 (projétil) | **39** (14 + 25), 2 acertos | acerto duplo |
| 3100 Tourouken | 4+4+4+13 = 25 | 20, 1 acerto | fatia fixa |
| 3120 Tourouken forte | 6×4+14 = 38 | 30, 1 acerto | fatia fixa |
| 3200 Yamikari | 17×4 = 68 (agarrão) | 35, 1 acerto | vira golpe simples |
| 3000 Zantetsuha | 38 | 14 × 5 = 70 | default × 5 contatos |
| 3010 Zantetsuha forte | 48 | 14 × 5 = 70 | default × 5 contatos |
| 3020 MAX Zantetsuha | 2 × 40 = 80 | 14 × 5 = 70 | default × 5 contatos |
| 1201 Ryuuei | 16 (forte 19) | 22 | abaixo da escala |
| 1300/1310 Kotsu | 1305 = 20 | 40 | correto |
| 1100/1110 Kasumi-giri | 17 | 34 | correto |
| 1400/1410 Tenmakyaku | 12+12 | 22 (12+10) | ver §5 |

Os três Zantetsuha entregavam exatamente o mesmo dano, apesar de custos diferentes: 1000 para o 3000/3010 e 3000 para o 3020 fora do MAX.

## 4. Correções aplicadas (`tools/build_fight.py`)

1. **Kikouhou (107)**: `ProjTab` de 14 → **40** (fonte 20 × 2). O forte (fonte 25) compartilha a linha; ficou no valor fraco.
2. **Zantetsuha (85/86/87)**: dano por contato **15 / 19 / 32** → totais **75 / 95 / 160**, contra 38 / 48 / 80 da fonte × 2.
3. **Mukuro Nui (108)**: entrou em `PROJECTILE_EXCLUDE` — o estado disparava o projétil inferido *e* a fatia de espada. Agora é só a fatia, com dano **22** (fonte 11 × 2), em vez dos 39 de antes.
4. **Tourouken/Yamikari (109/110/111)**: `slice_damage` 20/30/35 → **50/76/136**; o override do 111 acompanha (35 → 136).
5. **Ryuuei (58 / estado 1201)**: dano 22 → **32** (fonte 16 × 2).

Nenhuma transição, comando ou animação mudou — só bytes de dano e a exclusão de um projétil inferido.

## 5. O que foi verificado e NÃO mudou

- **Custo de barra está certo.** Medido com 3000 de barra: 3100 gasta 1000; 3120 e 3200 gastam 3000 (fora do MAX), como no fonte (`poweradd` + `PowerAdd` com `var(40) = 0`). O 3020 é detectado como MAX (`PowTab` −1000 dentro do MAX, 3000 fora). Única diferença conhecida: dentro do MAX, 3120/3200 não ganham o desconto de 1000 porque não foram marcados como `max_sids`. Só afeta a janela de MAX.
- **MAX Zantetsuha não perdeu o segundo projétil.** O motor entrega 5 contatos independentemente do número de helpers do fonte; o que estava errado era o dano por contato, agora corrigido.
- **Tenmakyaku (1400/1410)**: os dois hits (12+10) continuam. O fonte tem dois HitDefs de `12/var(23)` em 1402/1412 e `var(23)` é divisor de golpes; com o encadeamento por `air_box_patch_frames` o 10 pode ser compensação. Só mediria em jogo real.
- **Ryuuei forte com `tail_ticks` curto**: 1200 e 1210 dividem o slot 58 e a animação 1201; o `tail_ticks` é por animação, então separar o hold de 41 exigiria um slot novo. Fica como pendência.
- **Comandos**: mantidos. Comparação com o `Eiji.cmd` do fonte:

  | Golpe | Fonte | Port |
  |---|---|---|
  | 1300/1310 Kotsu (弱/強骨破斬り) | `~F,DF,D,DB,B,a/b` | igual (HCB) |
  | 1200/1210 Ryuuei (流影陣) | `~F,D,DF,x/y` | igual (DP) |
  | 1400/1410 Tenmakyaku (天馬脚) | `~B,D,DB,a/b` | igual (RDP) |
  | 1500/1510 Kageutsushi (影移し) | `~D,DF,F,a/b` | igual (QCF) |
  | 1100/1110 Kasumi-giri (霞み斬り) | `~D,DB,B,x/y` | igual (QCB) |
  | 1000 Kikouhou (気孔砲) | `~D,DF,F,x/y` | **QCF×2** |
  | 1600 Mukuro Nui (骸縫い) | `~D,DF,F,x/y` **no ar** | **DP no chão** |
  | 3000/3010/3020 Zantetsuha (斬鉄波) | `~D,DF,F,DF,D,DB,B,x/y/x+y` | igual |
  | 3100/3120 Tourouken (斬鉄蟷螂拳) | `~D,DF,F,DF,D,DB,B,a/b/a+b` | **QCB×2 + x/x+y** |
  | 3200 Yamikari (闇狩り) | `~F,DF,D,DB,B,F,DF,D,DB,B,x/y/x+y` | **HCB×2** |

  Mudar isso mexe em prioridade de comando e na lista de comandos do PRACTICE.
- **`char_scale`**: o build usa 1.0 (`build/gen_fight/build_profile.json`) porque é o perfil de escala cheia; o `0.81` do `newroster.py` é configuração legada e não entra no build.
- **`Eiji.air` vs `Eiji.air.orig`**: 2302 linhas de diferença (Clsn2 removidos nas poses 41/120/121/182, durações trocadas). Não foi tocado; precisa de conferência visual.

## 6. Teste novo

`tools/test_eiji_specials_headless.py` cobre os 13 golpes que não tinham teste nenhum (48–57 e 85–87). Rodado contra a build de 15/11 antes das correções:

```
1300/1310 Kotsu Hazaki      40/40
1200/1210 Ryuuei-jin        22/22
1400/1410 Tenmakyaku        22/22
1500/1510 Kageutsushi        0/0   (teleporte)
1100/1110 Kasumi-giri       34/34
3000/3010/3020 Zantetsuha   70/70/70
```

O teste valida o estado entrado e um piso de dano (não o valor exato), para não quebrar a cada ajuste de calibração.

## 7. Valores esperados no próximo build

| Golpe | Antes | Esperado |
|---|---|---|
| 1000 Kikouhou | 14 | 40 |
| 1600 Mukuro Nui | 39 | 22 |
| 3100 Tourouken | 20 | 50 |
| 3120 Tourouken forte | 30 | 76 |
| 3200 Yamikari | 35 | 136 |
| 3000 Zantetsuha | 70 | 75 |
| 3010 Zantetsuha forte | 70 | 95 |
| 3020 MAX Zantetsuha | 70 | 160 |
| 1200/1210 Ryuuei | 22 | 32 |

O 3020 é a maior mudança de comportamento: com 160 de dano ele passa a ser o super mais forte do elenco (acima do 140 do Kasumi e do 105 do Clark). Se ficar exagerado em jogo, baixar só o byte do `ProjTab` do slot 87 (cada ponto equivale a 5 de dano).

## 8. Pendências

1. Recompilar, rodar `tools/test_eiji_specials_headless.py` e repetir a varredura de especiais para confirmar a tabela da §7.
2. Decidir o comando do Kikouhou/Mukuro Nui/Tourouken/Yamikari (fonte vs. port).
3. Dar ao Ryuuei forte um slot próprio para o `tail_ticks` de 41.
4. Conferir `Eiji.air` contra `.orig` (hurtbox das poses 41/120/121/182).
5. Marcar 3120/3200 como `max_sids` se o desconto dentro do MAX for desejado.
