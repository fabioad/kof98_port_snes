# Categoria A: comandos religados (04/11/2026)

## O que era

A varredura inicial comparava os `[State -1]` dos CMDs com `moves` +
`POST_CAL_REACTIVATED` e listava onze personagens com "comando sem state".
Essa varredura não contava o `POST_CAL_SUPERS`, que já restaurava nove
desses golpes depois do `apply_profile`. A auditoria funcional no headless
mostrou que o problema real era outro em cada grupo:

1. **Mai (2070)** — o comando terminava em `~z`. O parser tratava
   `~botão` como release não suportado e descartava a definição inteira;
   o golpe não tinha linha no `CmdTab`.
2. **Final `z` (Chin 1920 / Mai 2070)** — o pad roteia R para `y|b` e só
   acrescenta o token `z` enquanto R está segurado. O `CmdTry` é
   first-match-wins, então o super `y` (mesmo movimento) consumia o botão
   antes da regra `z`.
3. **Supers de agarrão (Mai, Yamazaki, Mary, Geese, Krauser)** — o state
   raiz entrava, mas o `p1stateno` que prende o adversário e aplica o dano
   não estava ligado. O golpe recuperava com 0–1 de dano.

## Correções

### Parser e matcher

- `~botão` no fim de um comando agora é tratado como o **press** do botão
  (o matcher nativo só modela press edges). `~direção` continua sendo
  release.
- Regras de mesmo tamanho cujo último elemento usa `z` vêm antes das
  regras `x`/`y`/`b`: o R do pad chega junto com `y|b`, então o `z` precisa
  ganhar o empate.

### Follow-ups de agarrão

Os states `p1stateno` foram religados na janela 103–111, que é a que o
`StVictimHeld` reconhece como agarrão (`S_EXT_GRAB..S_EXT_LAST`). Um slot
abaixo de 103 libera a vítima no tick seguinte.

| Personagem | Golpe | Follow-up | Dano medido |
|---|---|---|---|
| Mai | 2070 | 2071 (sid 103) | 31 |
| Yamazaki | 3150 MAX Drill | 3151 (sid 104) | 41 |
| Blue Mary | 3060 Super Dunk | 3065 (sid 104) | 33 |
| Blue Mary | 4000 Dynamite Dunk | 4011 (sid 105) | 31 |
| Geese | 3250 MAX Rashomon | 3260/3261 (103/104) | 26 |
| Krauser | 3220 MAX Gigantic Cyclone | 3221/3222 (103/104) | 31 |

Ajustes específicos:

- **Yamazaki 3000/3010** (Guillotine): o dano vem de `fvar(7)`, que o
  extrator não avalia; o HitDef foi fixado em 22 por contato.
- **Mary 3060**: o `animelemtime(6) > 0 && Vel Y + Pos Y >= 0` de whiff era
  lido como regra de pouso e disparava na entrada (o Y de tela é sempre
  >= 0), então o launcher nunca chegava ao box do elemento 9. A regra foi
  descartada (`trans_drop`) e o dash de 10 px/tick foi reduzido a 2 px/tick
  para encontrar a vítima a curta e média distância.
- **Mary 4000**: a saída 4010 → 4011 usa `Pos Y > 20`, que o parser de
  pouso não reconhece; a transição foi adicionada no fim da animação.
- **Mai 2071**: o `TargetLifeAdd` usa `ifelse(enemynear,gethitvar(...))` e
  o extrator o descarta; foi adicionada uma linha op3 explícita de -30.
- **Geese 3261**: o dano da origem (elemento 22) vinha um elemento depois
  do `TargetState` que solta a vítima (elemento 21). O hit de -25 foi
  movido para o elemento 18.
- **Krauser 3222**: o loop de dano usa `var(16)`/`Const(data.attack)` e o
  extrator não gera op3; foram adicionados três contatos de -10 e o
  TargetState final para S_VTHROW.

### Kyo Nests / Ash

As variantes são `deepcopy` do Kyo base feitas **antes** da reativação do
Orochinagi. Elas receberam as mesmas linhas do Kyo (`98/3000/1110` e
`60/3005/3026`) e um `air_synth` que clona a ação 1110 no slot 3026 (o AIR
das variantes não traz o clipe sintético do pacote base). Resultado: 55 de
dano, igual ao Kyo base.

## Verificação

Novo `tools/test_category_a_headless.py` cobre 16 comandos:

- Joe 3150 (71), Chin 1920 (55), Mai 2070 (31);
- Yamazaki 3150 (41), 3000 (22), 3010 (22);
- Mary 3060 (33), 4000 (31);
- Geese 3250 (26), Krauser 3070 (170 no barrage MAX), 3220 (31);
- Ken 3050 (24), Chun-Li 3300 (26);
- Kyo, Nests e Ash 3000 (55 cada).

Todos PASS. O teste confere o state esperado (raiz ou follow-up) e um
mínimo de dano no adversário com 200 HP.

Regressões que continuam PASS: `pytest -q tools/tests` (272 passed),
`test_ai_headless`, `test_msu_chr_visibility_headless` (960 páginas/56
poses), `test_super_stage_vram_headless`, `test_chizuru_dp_headless`,
`test_attract_demo_headless`, `test_team_*`, `test_single_campaign`,
`test_midfight_join`, `test_ralf_mount`, `test_counter_banner`,
`test_benimaru_antiair`, `test_chin_zake`, `test_mary_grab`,
`test_yamazaki_reversal` e `test_chunli_hyakuretsu`.

> `test_krauser_kaiser_wave_headless`, `test_geese_projectiles_headless`,
> `test_input_shortcuts_headless` e `test_command_list_headless` têm
> falhas que também ocorrem no par de entrega anterior (asserts de vx/
> input de 1 frame). Não foram usados como gate desta mudança.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$9C60`**
- layout MSU **`0x1135`**
- `.sfc` SHA-256 `187bc733…cf776`
- `.msu` SHA-256 `6d9ca6ba…f9528`

O `.msu` cresceu ~295 KiB porque os follow-ups trazem animações novas
(sobretudo o 3061 da Mary). Copie `.sfc` e `.msu` juntos.
