# Auditoria Choi — especiais, supers e MAX (17/11/2026)

> **Atualização:** os quatro golpes ausentes e os supers incompletos foram
> corrigidos na mesma data; ver **Correções aplicadas** no fim deste arquivo.

Rodada focada no Choi para responder: **há golpe especial/super/MAX faltando
ou incompleto no port?** A resposta curta é **sim**: quatro golpes da fonte não
têm comando nem estado compilado, e quatro golpes implementados são
aproximações de um único impacto onde a fonte tem multi-hit/captura.

- ROM de referência: `kof98-snes.sfc` de 17/11 01:40, sha256
  `20c71ce86fb3aa37…` (commit `7383ccf` + árvore de trabalho, build de 01:40).
- Snapshot congelado: `build/audit_choi_20261117/` (ROM, MSU e `tables/` do
  mesmo build).
- Fonte: `assets/characters/choi-kofa/Choi.cmd`, `Choi_SNES.cns` e o cmd
  sintético `Choi_SNES.cmd`.
- Mapa compilado: `build/gen_fight/choi_remaining_specials.json`.
- Resultado bruto: `docs/audits/specials_choi_2026-11-17.json`.

## Resumo

- **4 golpes sem comando/estado:** 1210, 1610, 3110 e 3250.
- **4 golpes de 1 impacto** onde a fonte tem multi-hit/captura: 2400, 3000,
  3100 e 3200.
- **3 projéteis invisíveis** de 14 de dano que acertam a 120 px: 1100, 1600
  e 2400.
- **1 postura trocada:** o 3500 (Shakushi MAX2) está como golpe de chão, mas
  a fonte exige `statetype = A`.
- **18 estados distintos** compilados em 20 regras de comando; todas entram e
  acertam Kyo parado.

## Resultado do auditor automático

`tools/audit_specials_headless.py --chars choi --confirm`:

```text
choi 20 {'hit_and_recovered': 20}
```

As **20 regras de comando compiladas** entram no estado certo e acertam Kyo
parado. Portanto, o problema **não é input quebrado**. O auditor só enxerga
comandos que chegaram ao CmdTab; golpes que nunca receberam comando não
aparecem no relatório.

## Golpes da fonte sem comando/estado

Comparando os 22 estados especiais/supers que o `Choi.cmd` liga com o mapa
compilado, faltam quatro:

| Golpe | Estado fonte | Comando fonte | Situação no port |
|---|---:|---|---|
| Hishou Kuu Retsu Zan (forte, botão b) | 1210 | `~48$D,$U,b` | **sem comando e sem estado**; o 1200 aceita A+B e cobre só a versão fraco |
| Shissou Hishou Zan (forte, botão y) | 1610 | `~48$B,$F,y` | **sem comando e sem estado**; o 1600 só aceita A |
| Zan! En Getsu Rin (botão y) | 3110 | `~D,F,D,F,y` | **sem comando e sem estado**; o 3100 só aceita A |
| Houou Kyaku MAX | 3250 | `~D,F,D,F,c` | **sem comando e sem estado**; só o 3200 normal (custo 1000) existe |

Evidência direta: em `build/gen_fight/choi_remaining_specials.json` os values
de `moves` vão de 1000 a 3500, mas não há nenhuma entrada para 1210, 1610,
3110 ou 3250. O CmdTab gerado (`choiCmdTab` em `choi_spr.inc`) também não tem
linha para esses estados. Testes com os botões fortes (QCF2+B, HCB+B, QCB2+B,
QCB2+C) não entram nesses estados; caem em outros golpes ou não fazem nada.

### O que se perde

- **1210:** a versão forte do Hishou tem salto mais rápido (`VelSet -8,-7`
  contra `-6,-7`) e dano de acompanhamento diferente no estado 1110.
- **1610:** a versão forte do Shissou tem janela maior (`Time >= 32` contra
  `>= 24`) e dano maior no 1611 (`147/182` contra `133/154`).
- **3110:** a versão y do En Getsu Rin acrescenta o `sinadd` de PalFX e um
  `NotHitBy`; é a variante com invencibilidade extra.
- **3250:** é o Houou Kyaku MAX, custa 2000 de meter (`poweradd = -2000`) e
  tem a cadeia de agarrão/`targetstate 2236` própria. Na fonte ele divide o
  comando `~D,F,D,F,c` com o 3500 (Shakushi); o port ficou só com o 3500.

## Golpes implementados, mas incompletos

Além dos quatro ausentes, vários golpes existem apenas como **um impacto
único** ou com clipe emprestado. A tabela abaixo usa o dano medido no probe
(escala de 200 HP do port, não comparar com os 1500 da fonte).

### Especiais

| Golpe | Estado | Sid | Dano medido | O que falta |
|---|---:|---:|---:|---|
| Hishou Kuu Retsu Zan (fraco) | 1200 | 110 | 20 | usa o clipe 1000; a fonte é um salto aéreo (1201/1203/1205) e o port fica parado |
| Senpuu Tobisaru Satotsu | 1100 | 109 | 20 | usa o clipe 1160; a fonte avança com `VelSet 9,-4` (1101) e o port fica em x=80 |
| Shissou Hishou Zan (fraco) | 1600 | 111 | 15 | usa o clipe 1000; a fonte avança ~8,5 px/tick e o port só anda ~24 px |
| Hien-sen, Kaiten, Hishou Kyaku, Tatsumaki | 1500/1510, 1300/1310, 1400/1410, 1000/1010 | 48/49, 50/51, 52/53, 107/108 | 20, 15, 18, 25/30 | nada estrutural; entram e acertam |

### Supers e MAX

| Golpe | Estado | Sid | Dano medido | O que falta |
|---|---:|---:|---:|---|
| Ultimate Storm | 2400 | 112 | 30 (1 impacto) | a fonte é um agarrão em cinco fases (2401→2402→2404→2405), com `targetbind`/`p2stateno` e final de 200; o port reusa o clipe 2901, não prende a vítima (`held=False`) e dá um único golpe |
| Shin! Chouzetsu Tatsumaki Shinkuu Zan | 3000 | 87 | 52 (1 impacto) | a fonte tem HitDef a cada 15 ticks, até 4 impactos, e captura em 3080; o port dá um impacto só |
| Zan! En Getsu Rin (fraco) | 3100 | 113 | 35 (1 impacto) | a fonte tem três HitDefs em 3190/3191/3192; o port reusa o clipe 1000 e dá um impacto |
| Houou Kyaku | 3200 | 114 | 30 (1 impacto) | a fonte tem a cadeia 3200→3201→3210, com `targetbind`/`TargetLifeAdd`; o port reusa o clipe 1010 e não prende a vítima |
| Shakushi (MAX2) | 3500 | 88 | 70 (5×14) | a execução funciona e o projétil é calibrado, mas a **postura está errada**: a linha do CmdTab é `posture 3` (S|C, chão) e a fonte exige `statetype = A` || Toppa fraco/forte (ar) | 3050/3060 | 85/86 | 40/44 | entram e acertam; são os supers aéreos |

A divergência de postura do 3500 vem do cmd sintético: `Choi_SNES.cmd`
declara `triggerall = statetype != A` para o `special_87`, enquanto o
`Choi.cmd` original exige `statetype = A`.

## Projéteis invisíveis extras em 1100, 1600 e 2400

`PROJECTILE_EXCLUDE["choi"]` em `tools/build_fight.py` é hoje `(50, 51, 86)`.
O comentário acima da tabela diz que Choi não tem projétil viajante no move
set, mas os sids novos `109` (1100), `111` (1600) e `112` (2400) não foram
incluídos na exclusão. O gerador transformou os HitDefs/dashes desses estados
em um tiro invisível de **14 de dano**.

Medição com o alvo a 120 px (a 24 px o golpe acerta pelo HitDef normal):

| Estado | x do atacante | Dano a 24 px | Dano a 120 px |
|---|---:|---:|---:|
| 1100 | 80 → 80 (parado) | 20 | **14** |
| 1600 | 81,9 → 105,9 (~24 px) | 15 | **14** |
| 2400 | 80 → 80 (parado) | 30 | **14** |

Ou seja, o golpe acerta a 120 px sem o corpo chegar lá. Isso é o mesmo falso
positivo que a lista de exclusão já corrige para 1300/1310/3060, mas os sids
109/111/112 ficaram de fora.

O projétil do **3500 não entra nessa lista**: ele é intencional/calibrado
(`vx 11`, 5 impactos de 14 = 70) e está documentado em
`AUDITORIA_PROJETEIS_2026-11-15.md`.

## Recomendações

1. **Adicionar os quatro golpes ausentes** ao `cmd_extra`/mapa de Choi:
   - 1210 em QCF2+B (reusar o clipe 1200 se não houver orçamento de arte);
   - 1610 em HCB+B (reusar o clipe 1600);
   - 3110 em QCB2+B (reusar o clipe 3100);
   - 3250 como MAX do Houou Kyaku, com custo 2000 e prioridade sobre 3200
     quando o meter permitir (ou QCB2+C).
   Depois rodar `test_category_d_batch3_headless.py` e o auditor com
   `--confirm`.
2. **Corrigir a postura do 3500** para `posture 4` (ar), como na fonte. Se o
   comando aéreo for engolido pelo 3050, ajustar a ordem/prioridade no CmdTab
   antes de testar.
3. **Excluir os sids 109/111/112** de `PROJECTILE_EXCLUDE["choi"]` para remover
   o tiro invisível de 14. Se o 1600 ficar curto demais, o passo correto é
   aumentar o `POST_CAL_VEL`/step-in, não manter o projétil.
4. **Decidir o escopo dos supers simplificados** (2400, 3000, 3100, 3200).
   Se forem mantidos como aproximação, registrar isso no doc de release; se
   forem completados, usar `TargetLifeAdd`/`targetbind` como já foi feito em
   Heavy D, Clark, Daimon e Mary.
5. **Cobrir os casos no teste**: adicionar 1210/1610/3110/3250 ao
   `test_category_d_batch3_headless.py` e um caso que garanta que
   1100/1600/2400 **não** acertam a 120 px.

## Como reproduzir

```sh
S=build/audit_choi_20261117
mkdir -p $S/tables
cp kof98-snes.sfc kof98-snes.msu $S/
cp build/gen_fight/*_spr.inc build/gen_fight/*_remaining_specials.json $S/tables/
cd tools
python3 audit_specials_headless.py ../$S --chars choi --confirm --out choi.json
```

O snapshot usado nesta auditoria está em `build/audit_choi_20261117/`
(ROM sha256 `20c71ce86fb3aa37…`, MSU `7f9f3363eaecfa9b…`).

---

# Correções aplicadas (17/11/2026)

Os quatro golpes ausentes foram ligados e os quatro supers de impacto único
foram refeitos. O que mudou em `tools/build_fight.py`:

| Item | Correção |
|---|---|
| 1210 Hishou Kuu Retsu Zan forte | sid 115, QCF2+C, dano 22 |
| 1610 Shissou Hishou Zan forte | sid 116, HCB+C, dano 18 |
| 3110 Zan! En Getsu Rin (y) | sid 117, QCB2+C, 3 contatos |
| 3250 Houou Kyaku MAX | sid 118, QCB2+Z, custo 2000, agarrão multi-contato |
| 3500 Shakushi MAX2 | agora `posture 4` (aéreo), como a fonte; projétil calibrado mantido |
| 1100 / 1200 / 1210 / 1600 / 1610 | passam a avançar (`POST_CAL_VEL`) em vez de ficar parados |
| 3000 Shin! Chouzetsu... | 4 contatos (`hit_resets`) em vez de 1 |
| 3100 / 3110 En Getsu Rin | 3 contatos em vez de 1 |
| 2400 Ultimate Storm | agarrão real: 2404 (5 contatos) + 2405 (lançador), `held=True` |
| 3200 Houou Kyaku | agarrão real: 3201 -> 3210 -> 3211, `TargetLifeAdd` por contato |
| 3250 Houou Kyaku MAX | agarrão real: 3251 -> 3260 -> 3261, dano maior |
| projéteis invisíveis | sids 109/111/112/116 incluídos em `PROJECTILE_EXCLUDE["choi"]`; o 3500 continua intencional |

Comandos novos (o port não usa a notação MUGEN original; são botões SNES):

- 1210: QCF2 + C
- 1610: HCB + C
- 3110: QCB2 + C
- 3250: QCB2 + Z

## Verificação

```text
tools/audit_specials_headless.py --chars choi --confirm
choi 24 {'hit_and_recovered': 24}

tools/test_choi_specials_headless.py
PASS Choi specials: 22 moves
```

O teste novo cobre os 18 estados distintos, incluindo os golpes aéreos
(1400/1410, 3050/3060, 3500), os três agarrões (2400, 3200, 3250) e os
multi-hits (3000, 3100, 3110). Também passam:

```text
tools/test_choi_throw_headless.py      PASS
tools/test_antiair_landing_headless.py PASS Choi weak/strong Hien Zan
```

`tools/test_category_d_batch3_headless.py` continua vermelho no **Chin 1400
Upper strong** (`states [0, 3, 13, 21]`). O mesmo caso falha na ROM anterior à
correção (`build/audit_choi_20261117/kof98-snes.sfc`), então não é regressão
desta rodada.

## Build final

O build final foi feito com o HEAD atual (`17bd6d6`), incluindo as alterações
do Mr. Karate, e linkou sem ajustes temporários:

```text
make -f Makefile.pvsnes PVSNESLIB_HOME=/run/media/fabio/Dados/Fabio/pvsneslib-sdk-4.6
Build finished successfully!
```

Resultado bruto pós-correção:
`docs/audits/specials_choi_2026-11-17_fixed.json` (o de antes:
`docs/audits/specials_choi_2026-11-17_pre_fix.json`).
