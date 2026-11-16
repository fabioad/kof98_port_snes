# Auditoria de especiais e supers — 2026-11-15

Nova rodada completa de `tools/audit_specials_headless.py --confirm` sobre o
roster inteiro, com ROM e tabelas do **mesmo build**. Fecha a lista de casos
que a auditoria de 12/11 ainda reportava (§ `AUDITORIA_ESPECIAIS_2026-11-12.md`).

- ROM de referência: `kof98-snes.sfc` de 15/11 16:17, sha256 `d9a7571d26c9…`
  (commit `50c174d` + alterações não commitadas na árvore).
- Snapshot congelado: `build/specials_recheck_20261115c/` (ROM, MSU,
  `tables/`, `shard0-7.json`).
- Repetido na build de 14:57 (`ccb5e32d…`,
  `build/specials_recheck_20261115b/`) com **resultado idêntico**, então os
  três casos abertos não vêm de uma build intermediária.

## Números

| | |
|---|---|
| Casos de comando auditados | 1.234 (53 entradas do roster) |
| `hit_and_recovered` | 1.193 |
| `by_design` | 36 |
| `conditional` | 2 |
| `no_impact_review` | **3** |

Nenhum `input_missed`: todo comando compilado encontra o seu estado.

## Casos abertos

### Por projeto (2) — Chizuru

| Estado | Golpe | Situação |
|---|---|---|
| 1004 | QCF fraco | Dano condicional a `p2movetype`, 28 no fonte |
| 1300 | RCB | Dano condicional à postura do oponente, 18 |

Já medidos com a condição certa em 12/11. A ferramenta testa contra um Kyo
parado, por isso continuam `conditional`. Não são regressão.

### Passa pelo adversário sem acertar (3) — **regressão**

Os três entram no estado, percorrem o cenário e não geram dano quando o alvo
está no caminho. Só conectam se o alvo estiver perto do **ponto de chegada**.

| Personagem | Golpe | Estado | Avanço medido (x) | Acerta | Não acerta |
|---|---|---|---|---|---|
| Saisyu | Kamukakari fraco | 1200 | 80 → 164 (84 px) | 18 a 80–140 px | 12–64 px |
| Saisyu | Kamukakari forte | 1210 | 80 → 185 (105 px) | 22 a 100–140 px | 12–80 px |
| Blue Mary | Spinfall (subindo) | 1160 | 86 → 218 (132 px) | 34 a 100–140 px | 12–80 px |

Medições com `distance` de 12 a 140 px a cada 4–20 px
(`/tmp`-style sweep, mesma ROM). O adversário em `distance = 24` fica em
x ≈ 104/110, ou seja, **dentro** do trajeto percorrido.

#### Por que apareceu agora

Na build de 13:38 esses três acertavam a 24 px porque o corpo **não se
movia**: `x` ficava parado em 80 (Saisyu) e 86 (Mary), com 18/22/34 de dano.
O movimento veio depois e expôs o problema:

- Saisyu: `c56aaae` (lunge com `LUNGES` em `tools/remaining_specials.py`) e
  `c3a2d8a` (Tsumugari avança 8 px por elemento);
- Mary: `b733bd8` (bit12 do `velset` no Spinfall).

A causa provável é a janela de acerto ficar nos quadros finais da animação
compilada, não durante o deslocamento. O golpe precisa de caixa ativa no
trajeto; aumentar a velocidade não resolve.

Nota sobre Mary: a correção não commitada em `tools/build_fight.py` (zerar a
velocidade de entrada e lançar um tick depois, para o hitbox do quadro 0 não
sair no ar) **já está** na build de 16:17 e não muda o resultado a 24 px.

Esses três foram deixados **sem** `CASE_SETUPS` de propósito: se ganharem uma
linha de distância longa, a ferramenta passa a reportar "acerta" e a regressão
some do relatório.

### Falso positivo corrigido — Benimaru 1110

`Kuuchuu Raikouken forte` (estado 1110) era reportado como sem impacto. O
golpe é o mesmo helper do fraco e acerta adversário **no ar**:

| Setup | Dano |
|---|---|
| pulo 48 px, alvo no ar, distância 48–64 px | 20 |
| pulo 24 px, alvo no ar, distância 24 px | 30 |
| qualquer setup com alvo parado no chão | 0 |

O `confirmation_setups` já tinha esse teste para o fraco (1100) e não tinha
para o forte. Adicionado:

```python
("benimaru", 1110): [_s(air_height=16, distance=48, opponent_air=True)],
```

Verificado: 1110 passa a `hit_and_recovered` com 20.

## Fora do alcance desta ferramenta (segue pendente)

A auditoria prova entrada de comando e impacto. Ela **não** mede arte,
efeitos nem helpers aproximados. Continuam em aberto, pelos documentos
anteriores:

- **Rugal** — Gravity Smash forte (1560) sem linha no port; no fonte o
  estado exige `Helper(99999),var(11) > 0`.
- **Omega Rugal** — 7200 (striker) sem estado equivalente; o comando RE usa
  o clipe do Gravity Smash.
- **Chizuru** — sprite do clone, PalFX e AfterImage ausentes.
- ~~**Heavy D 1950** — 1 de 5 contatos~~ **corrigido**: o estado foi
  dividido em quatro contatos que prendem a vítima + o launcher
  ([HEAVYD_SHADOW_2026-11-15](HEAVYD_SHADOW_2026-11-15.md)).
- **Efeitos** (Explod/PalFX/AfterImage) e animações aproximadas (Ralf,
  Clark, Iori) não são medidos aqui.

## Casos claros ajustados — 22 entradas

Os 22 casos claros da lista de 15/11 foram corrigidos no build. A causa não
era uma só:

- o extrator estático lia `VelSet`/`VelAdd`/`VelMul` e `PosAdd` com
  `Time=a,b`, faixas de `AnimElem` ou fórmulas como zero, então a `PosTab`
  saía vazia;
- nos grabs importados (Daimon/Rugal) o comando entra no slot sintético
  103–114, não no root declarado na regra;
- em todos os casos de chão a `BodySep` mantém 24 px entre os eixos e
  desfazia qualquer avanço a curta distância, mesmo com a `PosTab` correta;
- uma `PosAdd` por elemento volta a disparar a cada loop da animação (Choi
  1600 e Yashiro 2200 acumulavam ~5× a distância da fonte).

A correção usa um passo limitado por tempo: `POST_CAL_VEL` em
`tools/build_fight.py` grava `ActTab op5` (velocidade), `op5 0` no fim da
janela ativa e `op23` (`StepInOn`). O `op23` liga `F_TFLAGS` bit4 e a
`BodySep` só cede para **esse** estado, enquanto houver velocidade
horizontal. Moves com VelSet que já andavam (Saisyu, Mary, Benimaru, Terry)
não foram marcados e mantiveram o comportamento anterior — conferido contra
a ROM de 16:17 com o mesmo audit.

Medição final (`build/specials_recheck_20261115d`, ROM e tabelas do mesmo
build; `dx = max(x)-min(x)` durante o golpe):

| Personagem | Estado(s) / sid(s) | dx final |
|---|---|---|
| Athena | 1080/1085 · 54/53 | 12 / 16 |
| Brian | 3210/3400 · 88/108 | 16 / 24 |
| Chizuru | 2200 · 87 | 12 |
| Choi | 1600 · 111 | 24 |
| Chun-Li | 1100 · 57 | 20 |
| Daimon | 1300/1500/1510/3000 · 53/54/55/85 | 12 em todos |
| Heavy D! | 1100/1150 · 50/51 | 12 / 12 |
| Iori | 3000 · 85 | 34 |
| Kim | 3100/3110/3120 · 85/86/87 | 15 / 34 / 34 |
| King | 1300/1350 · 54/55 | 16 / 16 |
| Kyo / Nests / Ash | 1800/1810 · 58/59 | 12 / 12 |
| Leona | 1200/1201/1400/1401 · 52/53/54/55 | −9 / −9 / −6 / −12 |
| Mai | 1038 · 107 | 9 |
| Mature | 1300 · 54 | 15 |
| Rugal | 1400/1410, 3000/3010, 3100/3110/3150, 3200/3210/3250 | 16; 16; 36; 16 |
| Shermie | 1300 · 109 | 20 |
| Shingo | 1000/3050/3150 · 48/87/52 | 8 / 20 / 34 |
| Takuma | 3100/3105 · 113/88 | 6 / 6 |
| Yamazaki | 3150 · 87 | 9 |
| Yashiro | 2200, 3000/3010, 3100 · 107/85/86/110 | 43; 34; 6 |
| Yuki | 1400/1500 · 52/53 | 16 / 20 |
| Chris | 7100/7150 · 60/61 | 6 / 6 |

Os valores maiores que o total da fonte (Iori/Kim/Yashiro) incluem o
recuo/avanço do próprio impacto; o eixo do atacante é medido até o fim da
recuperação. Daimon 3000 continua intermitente no probe a 24 px
(`input_missed` em uma das tentativas), mas a tentativa válida mede 12 px e
o comando entra; é o mesmo comportamento de antes, não uma regressão nova.

## Método — congele ROM e tabelas juntos

A primeira tentativa desta rodada usou a ROM de 13:38 com as tabelas de
14:57. As duas builds diferem em 113.468 bytes e o resultado não vale como
prova: os metadados de comando vêm das tabelas, o comportamento vem da ROM.

```sh
S=$PWD/build/specials_recheck_$(date +%Y%m%d%H%M)
mkdir -p $S/tables
cp kof98-snes.sfc kof98-snes.msu $S/
cp build/gen_fight/*_spr.inc build/gen_fight/*_remaining_specials.json $S/tables/
cd tools
python3 audit_specials_headless.py $S --confirm --chars <lista> --out shard0.json
```

Rodar em 8 shards leva ~2 min. Use `--out nome.json` relativo ao snapshot
(o caminho é juntado ao diretório do snapshot).
