# Reativação de states e fechamento do build — 02/11/2026

## Estados religados

`POST_CAL_REACTIVATED` em `tools/build_fight.py` repõe, depois de
`apply_profile`, os comandos que apontavam para um `Statedef` sem `sid`.
São **27 personagens / 71 entradas de comando**.

| Personagem | State -> sid |
| --- | --- |
| Iori | 3050 -> 103 |
| Saisyu | 3050->87, 3100->88, 3110->89, 3150->66 |
| Heidern | 3050->87, 3100->88, 3110->89, 3150->66 |
| Takuma | 3020->87, 3220->58, 3100->88, 3120->89 |
| Clark | 1500->58, 1510->59, 3050->87, 3100->88, 3110->89, 3150->66 |
| Ralf | 510->87, 511->88, 520->89, 521->58, 550->59, 570->60, 512->61 |
| Leona | 3250->58, 3100->87, 3150->88, 3300->89 |
| Benimaru | 1300->60, 1310->61, 1600->62, 3050->87, 3100->89, 3150->88, 3300->66 |
| Daimon | 1400->63, 1600->59, 3050->87, 3100->89, 3150->88, 3160->60 |
| Terry | 3050 -> 87 |
| Andy | 3150 -> 87 |
| Ryo | 3050 -> 87 |
| Robert | 3120->87, 3250->88, 3260->89 |
| Athena | 3100->87, 4000->88 |
| King | 3500 -> 87 |
| Chizuru | 2200 -> 87 |
| Kim | 3120 -> 87 |
| Chang | 3500 -> 87 |
| Choi | 3000->87, 3500->88 |
| Yashiro | 3500 -> 87 |
| Shermie | 7000->60, 7050->61 |
| Chris | 7100->60, 7150->61 |
| Billy | 3100->62, 1800->64, 1850->66 |
| Lucky | 2900->88, 3000->89 |
| Mr. Big | 3000->87, 3010->88, 3250->89 |
| Eiji | 3020 -> 87 |
| Sakura | 3050 -> 87 |

Obs.: Takuma mantém apenas os quatro comandos; os states de
continuação 3221/3222/3022/3023/3001 foram deixados de fora para a tabela
caber nos 32 KiB do banco 83, que divide espaço com `ShingoChrN`.

## Layout / build

- `tools/asset_paths.py`: resolvedor case-insensitive usado por
  `build_fight.py`, `build_select.py` e `calibration/native.py`.
- `build_portraits`: paleta de 3 cores é preenchida quando o quantizador
  devolve menos de 3 cores.
- Alocador: mesas/metasprites, atlases de projétil e tabela de IA agora
  são empacotados numa única passada (`grab(all_sizes)`), com ordem
  embaralhada nos retries. O esquema antigo de “reservar depois” deixava
  um atlas de 4 KiB sem janela contígua.
- Novas janelas: tails após as ending stills nos bancos 118–125.
- Daimon: CHR agora streamado pelo MSU. A tabela cresceu e empurrava o
  blob ROM-residente para o banco 43, onde fica `EndData0`. As metades
  baixas 27–42 ficaram livres e foram devolvidas ao alocador.
- Saisyu e Clark: `SprData` separado em `_meta.inc`.
- Heidern: as quotes ES ficam imediatamente após a tabela, em offset
  dinâmico, em vez de `$A000` fixo.
- `Chizuru 87` e `Mr. Big 88/89` marcados como MAX/SDM.

## Verificação

```sh
python3 tools/build_fight.py
make pvsnes PVSNESLIB_HOME=/run/media/fabio/Dados/Fabio/pvsneslib-sdk-4.6
make pvsnes-verify PVSNESLIB_HOME=/run/media/fabio/Dados/Fabio/pvsneslib-sdk-4.6
python3 -m unittest tools.tests.test_reactivated_states
python3 -m unittest tools.tests.test_command_list tools.tests.test_counter_grab
python3 tools/test_command_list_headless.py
python3 tools/test_msu_chr_visibility_headless.py
```

Resultados:

- `build_fight.py`: OK.
- Link ROM: OK, 1.499.887 bytes livres de 8 MiB.
- `pvsnes-verify`: OK (Fast HiROM, checksum `$7AEB`).
- Testes unitários: OK.
- Command list headless: 6 PASS.
- MSU CHR visibility: 960 páginas / 57 poses, passed.

## Limites conhecidos

- Golpes cujo HitDef real está em Helper/Explod continuam aproximados.
- Supers MAX em slots especiais (`Iori 103`, `Saisyu/Heidern/Clark 66`)
  não recebem o desconto da janela MAX; usam o custo direto do `PowTab`.
- O `.msu` e a ROM mudaram; copie os dois juntos para o SD.

## Correção pós-build: MSU alinhado e Daimon no MSU

- Daimon passou a streamar CHR do MSU. Isso desloca os slices de todos os
  personagens seguintes; ROM antiga + MSU novo (ou vice-versa) faz os
  chars MSU lerem tiles errados, aparecerem por poucos quadros ou ficarem
  invisíveis.
- O arquivo `.msu` agora é preenchido até múltiplo de 512 bytes.
- Sempre copie **kof98-snes.sfc e kof98-snes.msu do mesmo build**.
- Layout MSU atual: `$F416`.

## Correção de travamento Clark × Ralf (02/11/2026)

Os states novos do Clark que não tinham a cadeia completa foram desativados
temporariamente:

- 1500/1510 (Super Argentine/Napalm) -> faltavam 1511/1520/5690;
- 3050 (MAX Ultra Argentine) -> faltava 3060 e a cadeia 3061-3067;
- 3100/3110/3150 (Running Three) -> faltavam 3105/3155/3120/3121/1201.

Entrar nesses states deixava o Clark preso na pose final, com o resto da
luta ainda rodando. O Ultra Argentine original (3000 -> 109-111) continua
ligado e é a versão estável. Os comandos ficam sem `sid` até as cadeias
completas serem importadas e testadas.

Build/verify: ROM checksum `$6B6B`, `make pvsnes-verify` OK.

## Correção de travamento/glitches do Ralf (02/11/2026)

Os states reativados do Ralf também dependiam de cadeias que o motor não
importa:

- 510/511 (Running Super) precisam do `ChangeState` para 512, que depende
  de `p2bodydist X`; sem ele o Ralf atravessa o oponente e não acerta;
- 512 (montaria) usa `p1stateno = 515` e a cadeia 515-518, que não estão
  ligadas;
- 520/521 (Ultra Vulcan) apontam para os victim states 80010/80011, que
  não existem no runtime; a animação roda, mas não causa dano;
- 550 (MAX V-Slasher) usa os victim states 80002/80018 e só registra
  parte dos hits;
- 570 (MAX Galactica) é baseado em Helpers, que o motor não suporta.

Como no Clark, os comandos foram desligados até a cadeia completa ser
importada e testada. O par estável 85/86 (Galactica Phantom fraco/forte)
continua ativo. A tabela de IA do Ralf deixa de listar os sids 87-89.

Build: `make pvsnes` e `make pvsnes-verify` OK.
