# Geese — quadros de vítima dos arremessos especiais faltando — 15/11/2026

Registro de investigação. **Nada foi alterado em código nem compilado.** O
diagnóstico saiu do `build/gen_fight/` já existente (gerado em 15/11 14:18),
do `Geese_SNES.cns` e do `Geese.air`.

## Resumo

Os dois arremessos especiais do Geese não são arremessos de fato na ROM:

- **Raimei Gouha Nage** (slot 107, state 1500)
- **Shinkuu Nage** (slot 108, state 1600)

Os dois ficaram ligados só ao state de **pré-arremesso** (o que contém o
HitDef) e não ao state de captura (1510 / 1610). Por isso a vítima nunca é
presa e nunca recebe os quadros de arremesso.

## Evidências

### 1. Slots 107/108 apontam para o state errado

`tools/build_fight.py:4631-4650`:

- `POST_CAL_REACTIVATED`: `(107, 1500, 1500)` e `(108, 1600, 1600)`.
- `hitdef_override` força golpe comum: `throw: 0`, `p2state: 0xFF`,
  `damage` 25/30, `fall: 1`. Ou seja, vira um soco que derruba, sem captura.
- `slice_damage` `{107: 25, 108: 30}` confirma o dano fixo por golpe.

No CNS (`Geese_SNES.cns`):

| Move | Pré (HitDef) | Captura/ataque | Estado da vítima |
|------|--------------|----------------|------------------|
| Raimei | 1500 (`p1stateno = 1510`) | 1510 (`TargetState 1515`, 9 `TargetBind`, `TargetLifeAdd` no elem 10) | 1515 → 826 (anim 5160) → 5690 |
| Shinkuu | 1600 (`p1stateno = 1610`) | 1610 (`TargetState 1615`, 5 `TargetBind`, `TargetLifeAdd` elem 5) | 1615 → 1616 (anim 5090) → 5690 |

O port nunca compila 1510/1610 nem 1515/1615.

### 2. Nada gerado para 107/108 em `build/gen_fight/geese_spr.inc`

- Existem `geeseAnim107` e `geeseAnim108`, mas só com as poses de pré
  (1500: 5 quadros; 1600: 6 quadros).
- **Não existem** `geeseBind107/108`, `geeseAct107/108` nem `geeseRev*` para
  esses slots (só 75, 99, 101, 103, 104). Compare com 103/104 (Rashomon), que
  têm Bind + Act completos.
- `geesePoseTab` tem só 7 poses (0-6), as dos arremessos normais.

### 3. Sprites de vítima ausentes em `geese_sprite_ids.json`

Quadros que as anims da vítima usam (`Geese.air`):

| Anim | Quadros (grupo,imagem) | Situação |
|------|------------------------|----------|
| 1515 (Raimei, vítima) | 5040,0 · 5012,20 · 5012,0 · 5012,10 · 5071,0 · 5071,10 · 5031,0 · 5011,10 | só **5040,0** existe; **faltam** 5012,0/10/20, 5071,0/10, 5031,0, 5011,10 |
| 1615 (Shinkuu, vítima) | 5000,0 · 5000,10 · 5032,0 · 5071,10 · 5012,20 | 5000,0 e 5000,10 existem; **faltam** 5032,0, 5071,10, 5012,20 |
| 825/826 (queda Raimei) | 5000,0 · 5012,* · 5002,* · 5031,0 · 5011,10 | mesmas faltas de 5012/5031/5011 |
| 1510 (atacante, Raimei) | 1500,0 a 1500,19 | **todos ausentes** (só aparece a pose 1500,20 nas anims de pré) |
| 1610 (atacante, Shinkuu) | 1400,5 · 820,0 a 820,12 | 1400,5 e 820,12 existem; 820,0 a 820,11 ausentes |

Ou seja: além de não ligar o state, o exportador também não incluiu os cels
dessas anims na tabela de sprites. Só entra o que alguma anim mapeada
referencia, e nenhuma referencia esses quadros.

### 4. O que já está certo (não mexer)

- Arremessos normais 74/75 (800/810/811/820): têm `geeseBind75`, `geeseAct75/77`
  e `geesePose0..6`. `test_throw_victim_pose_headless.py` cobre o Geese.
- Contra-ataques 99-102 (1410/1420): têm Bind/Act/Rev e usam a pose genérica
  5000 como vítima (decisão deliberada, `omit_anims: [100, 102]`).

## O que fazer depois (sugestão)

1. Mapear os states de captura: `POST_CAL_REACTIVATED` de 107/108 para
   **1510 / 1610** (anims 1510 / 1610), mantendo 1500/1600 como pré via
   `extra_trans`, como já é feito no DP (55/56).
2. Remover `hitdef_override` / `slice_damage` de 107/108 e deixar a captura
   dar o dano pelo `TargetLifeAdd` (Raimei: elem 10; Shinkuu: elem 5, com
   escala da barra de 200 pontos e `damage_scale 2.0`).
3. Declarar as binds das duas capturas (9 janelas em 1510, 5 em 1610) e a
   liberação: 1515 → 826 → 5690 e 1615 → 1616 → 5690, usando os runtime
   slots de vítima (S_VHELD 76 / S_VTHROW 77) e `TargetPose` com
   `geesePose7+` para 1515 e 1615.
4. Garantir que os cels listados na seção 3 entrem em `geese_sprite_ids.json`
   e no `geese.chr` (conferir orçamento de VRAM/banco do Geese, que já tem
   escala 0.81).
5. Teste headless novo parecido com `test_throw_victim_pose_headless.py`:
   Geese executa HCB+P/HCBx2 perto do oponente, vítima entra em 76, quadros
   avançam sem regredir e a liberação cai em 77 / queda.

## Observação sobre o lugar do trabalho

`tools/build_fight.py` e `tools/remaining_specials.py` já têm mudanças locais
não commitadas (Saisyu/Chang). Esta correção do Geese deve ir em commit
separado.
